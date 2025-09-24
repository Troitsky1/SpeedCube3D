# ui/cube_widget.py
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.clock import Clock
from kivy.graphics.opengl import *
from kivy.config import Config
import numpy as np

from cube.cube import Cube
from config.cube_defaults import SCALE
from utils.ray_casting import screen_to_world_ray, pick_closest_visible_face, vector_from_face_center_to_ray
from utils.camera import Camera
from ui.debug import draw_debug_vectors

Config.set('graphics', 'depthbuffer', 1)


def normalize(v):
    return v / np.linalg.norm(v) if np.linalg.norm(v) > 1e-8 else v


class CubeWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cube = Cube()
        self.scale = SCALE
        self.rotating_slice = None

        # State for interaction
        self.selected_face = None
        self.face_center = None
        self.face_normal = None
        self.corner_vectors = None

        # Camera: looking at origin from Z+
        self.camera = Camera(
            position=(0, 0, 6),
            target=(0, 0, 0),
            up=(0, 1, 0),
            fov=60.0,
            aspect=self.width / self.height
        )

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CW)

        Clock.schedule_interval(self.update_cube, 1 / 60)

    # --- Visibility ---
    def is_face_visible(self, normal, face_center):
        view_vec = np.array(face_center) - np.array(self.camera.position)
        return np.dot(normal, view_vec) < 0

    def is_piece_in_rotating_slice(self, piece) -> bool:
        return (
            hasattr(self, "rotating_slice")
            and self.rotating_slice is not None
            and piece.position in self.rotating_slice.positions
        )

    # --- Drawing ---
    def draw_cube(self):
        self.canvas.clear()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        with self.canvas:
            faces_to_draw = []

            for piece in self.cube:
                for face in piece.faces.values():
                    if not self.is_face_visible(face.normal, face.centre):
                        continue

                    verts_world = [np.array(v) for v in face.vertices]
                    verts_screen, depth = self.camera.world_to_screen(verts_world, self.width, self.height)
                    if verts_screen is None:
                        continue

                    faces_to_draw.append((depth, verts_screen, face.colour))

            faces_to_draw.sort(key=lambda f: f[0])  # sort far → near

            for _, verts2d, color in faces_to_draw:
                Color(*color)
                Quad(points=(
                    verts2d[0][0], verts2d[0][1],
                    verts2d[1][0], verts2d[1][1],
                    verts2d[2][0], verts2d[2][1],
                    verts2d[3][0], verts2d[3][1],
                ))
                if tuple(color[:3]) != (0, 0, 0):
                    self.draw_face_border(verts2d)

    def draw_face_border(self, verts2d, border_color=(0, 0, 0, 1), border_width=1.0):
        Color(*border_color)
        for i in range(4):
            p1 = verts2d[i]
            p2 = verts2d[(i + 1) % 4]
            Line(points=[p1[0], p1[1], p2[0], p2[1]], width=border_width)

    # --- Animation ---
    def update_cube(self, dt):
        # Example: orbit camera slowly around Y axis
        angle = np.radians(20 * dt)
        x, y, z = self.camera.position
        x_new = x * np.cos(angle) - z * np.sin(angle)
        z_new = x * np.sin(angle) + z * np.cos(angle)
        self.camera.position = (x_new, y, z_new)
        self.draw_cube()

    # --- Touch ---
    def on_touch_down(self, touch):
        ray_dir = screen_to_world_ray(
            touch.x, touch.y,
            self.width, self.height,
            np.array(self.camera.position),
            self.camera.direction,
            self.camera.up,
            self.camera.fov,
            self.camera.position-(0,0,0)
        )

        result = pick_closest_visible_face(self.cube, np.array(self.camera.position), ray_dir)
        if result is None:
            return
        face_center, face_normal, piece, face = result

        # Store interaction state
        self.selected_face = face
        self.face_center = face_center
        self.face_normal = face_normal
        self.corner_vectors = [corner - face_center for corner in face.vertices]

        # Initial debug draw (optional)
        intersection = vector_from_face_center_to_ray(face_center, face_normal, self.camera.position, ray_dir)
        if intersection is not None:
            c_to_p = intersection - face_center
            draw_debug_vectors(self, self.camera.position, ray_dir, face_center, face_normal, c_to_p, self.corner_vectors)

    def on_touch_move(self, touch):
        if self.selected_face is None:
            return

        ray_dir = screen_to_world_ray(
            touch.x, touch.y,
            self.width, self.height,
            np.array(self.camera.position),
            self.camera.direction,
            self.camera.up,
            self.camera.fov,
            1.0
        )

        c_to_p = vector_from_face_center_to_ray(self.face_center, self.face_normal, self.camera.position, ray_dir)
        if c_to_p is None:
            return

        # Find closest two corner vectors
        c_to_p_n = normalize(c_to_p)
        dots = [np.dot(c_to_p_n, normalize(v)) for v in self.corner_vectors]
        idx1, idx2 = np.argsort([-d for d in dots])[:2]  # pick two with highest dot product
        v1, v2 = self.corner_vectors[idx1], self.corner_vectors[idx2]

        # Compute bisector vector
        bisector = normalize(v1 + v2)

        # Debug draw (optional)
        draw_debug_vectors(self, self.camera.position, ray_dir, self.face_center, self.face_normal, c_to_p, self.corner_vectors)
        with self.canvas:
            Color(0, 1, 1)  # cyan for bisector
            Line(points=[*self.face_center, *(self.face_center + bisector)], width=2)
