# ui/cube_widget.py
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.clock import Clock
from kivy.graphics.opengl import *
from kivy.config import Config
import numpy as np

from cube.cube import Cube
from config.cube_defaults import SCALE
from utils.camera import Camera
from utils.ray_casting import pick_face_and_vectors
from utils.face_picking import intersect_with_plane
Config.set('graphics', 'depthbuffer', 1)


class CubeWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cube = Cube()
        self.scale = SCALE
        self.rotating_slices = []
        self.background_clicked = True #***************REPLACE WITH CHECKER FUNCTION******************
        self.last_intersection = None
        self.active_quadrants = None
        self.active_normal = None
        self.rotation_vec = None
        self.active_centre = None
        # Camera starts on +Z looking at origin
        self.camera = Camera(
            position=(0, 0, 16),
            target=(0, 0, 0),
            up=(0, 1, 0),
            fov=45.0,
            aspect=self.width / max(1, self.height),
            near=0.1,
            far=100.0
        )
        self.camera.aspect = self.width / max(1, self.height)
        self.debug_vectors: list[tuple[np.ndarray, np.ndarray, tuple[float, float, float, float]]] = []
        self.cube_canvas = InstructionGroup()
        self.debug_canvas = InstructionGroup()
        self.canvas.add(self.cube_canvas)
        self.canvas.add(self.debug_canvas)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CW)

        Clock.schedule_interval(self.update_cube, 1 / 60)

    # -------------------
    # Rendering
    # -------------------
    def draw_cube(self):
        self.cube_canvas.clear()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        faces_to_draw = []

        for piece in self.cube:
            for face in piece.faces.values():
                # Skip hidden faces unless slice is rotating
                if not self.is_face_exposed(piece, face) and not self.is_slice_rotating(piece):
                    continue

                verts3d = face.vertices
                verts2d, avg_depth = self.camera.world_to_screen(
                    verts3d, self.width, self.height
                )
                if verts2d is None:
                    continue

                faces_to_draw.append((avg_depth, verts2d, face.colour))

        # sort far → near
        faces_to_draw.sort(key=lambda f: f[0], reverse=True)

        for _, verts2d, color in faces_to_draw:
            '''
            self.cube_canvas.add(Color(*color))
            self.cube_canvas.add(Quad(points=[
                verts2d[0][0], verts2d[0][1],
                verts2d[1][0], verts2d[1][1],
                verts2d[2][0], verts2d[2][1],
                verts2d[3][0], verts2d[3][1],
            ]))
            '''
            # Draw black outline for non-internal faces
            if tuple(color[:3]) != (0, 0, 0):
                self.draw_face_border(verts2d)

        #debugging
        for start3d, end3d, color in self.debug_vectors:
            self.draw_debug_vector(start3d, end3d, color)

    def draw_face_border(self, verts2d, border_color=(0, 0, 0, 1), border_width=1.0):
        self.cube_canvas.add(Color(*border_color))
        for i in range(4):
            p1 = verts2d[i]
            p2 = verts2d[(i + 1) % 4]
            self.cube_canvas.add(Line(points=[p1[0], p1[1], p2[0], p2[1]], width=border_width))

    # -------------------
    # Animation
    # -------------------
    def update_cube(self, dt):
        """Orbit camera around cube instead of rotating cube."""
        #self.camera.orbit(dx=30*dt, dy=30*dt)
        self.draw_cube()

    # -------------------
    # Helpers
    # -------------------
    def is_face_exposed(self, piece, face):
        px, py, pz = piece.position
        if face.axis == 'x':
            return (face.direction == -1 and px == 0) or (face.direction == +1 and px == 2)
        elif face.axis == 'y':
            return (face.direction == -1 and py == 0) or (face.direction == +1 and py == 2)
        elif face.axis == 'z':
            return (face.direction == -1 and pz == 0) or (face.direction == +1 and pz == 2)
        return False

    def is_slice_rotating(self, piece):
        px, py, pz = piece.position
        for axis, index in self.rotating_slices:
            if axis == 'x' and px == index:
                return True
            if axis == 'y' and py == index:
                return True
            if axis == 'z' and pz == index:
                return True
        return False

    def on_touch_down(self, touch):
        result = pick_face_and_vectors(self.cube, self.camera, touch.x, touch.y, self.width, self.height)
        if result:
            self.background_clicked = False
            self.last_intersection = result["intersection"]
            self.active_quadrants = result["quadrants"]
            self.active_centre = result["face_center"]
            self.active_normal = result["face_normal"]
            self.clear_debug_vectors()
            self.add_debug_vector(result["ray"][0], result["intersection"], (1, 0, 0, 1))
            for q in result["quadrants"]:
                self.add_debug_vector(result["intersection"], q, (0, 0, 1, 1))

        else:
            self.background_clicked = True

    def on_touch_up(self, touch):
        self.background_clicked = False
        self.last_intersection = None
        self.active_quadrants = None
        self.active_centre = None
        self.active_normal = None

    def on_touch_move(self, touch):
        self.debug_canvas.clear()
        if not self.background_clicked:
            ray_origin, ray_dir = self.camera.get_ray(touch.x, touch.y, self.width, self.height)
            new_intersection = intersect_with_plane(ray_origin, ray_dir, self.active_centre, self.active_normal)
            motion_vec = new_intersection - self.last_intersection

            # find best matching cardinal
            dots = [np.dot(motion_vec, c) for c in self.active_quadrants]
            best_idx = int(np.argmax(dots))
            self.rotation_vec = self.active_quadrants[best_idx]

            self.clear_debug_vectors()
            self.add_debug_vector(self.last_intersection, new_intersection, (0, 1, 0, 1))  # motion vector
            for q in self.active_quadrants:
                if np.allclose(q, self.rotation_vec) == 0:
                    colour = (1, 0, 0, 1)
                else:
                    colour = (0, 0, 1, 1)
                self.add_debug_vector(self.last_intersection, q, colour)
        else:
            dx = touch.dx
            dy = - touch.dy
            self.camera.orbit(dx, dy)
            self.draw_cube()

    def draw_vector(self, start_3d, end_3d, color=(1, 0, 0, 1), width=1.0):
        start_2d, _ = self.camera.world_to_screen([start_3d], self.width, self.height)
        end_2d, _ = self.camera.world_to_screen([end_3d], self.width, self.height)

        if start_2d and end_2d:
            s = start_2d[0]
            e = end_2d[0]
            Color(*color)
            Line(points=[s[0], s[1], e[0], e[1]], width=width)

    def draw_debug_vector(self, start_3d, end_3d, color=(1, 0, 0, 1), width=1.0):
        start_2d, _ = self.camera.world_to_screen([start_3d], self.width, self.height)
        end_2d, _ = self.camera.world_to_screen([end_3d], self.width, self.height)

        if start_2d and end_2d:
            s = start_2d[0]
            e = end_2d[0]
            self.debug_canvas.add(Color(*color))
            self.debug_canvas.add(Line(points=[s[0], s[1], e[0], e[1]], width=width))

    def add_debug_vector(self, start, end, color=(1, 0, 0, 1)):
        start = np.array(start, dtype=float)
        end = np.array(end, dtype=float)
        self.debug_vectors.append((start, end, color))

    def clear_debug_vectors(self):
        self.debug_vectors.clear()
        self.debug_canvas.clear()

    def on_size(self, *args):
        # Keep camera aspect in sync with widget dimensions
        self.camera.aspect = self.width / max(1, self.height)