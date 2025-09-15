# ui/cube_widget.py
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.clock import Clock
from kivy.graphics.opengl import (
    glEnable, glDepthFunc, glClear,
    GL_DEPTH_TEST, GL_LESS, GL_DEPTH_BUFFER_BIT
)
from kivy.config import Config
from math import sin, cos, radians
from cube.cube import Cube
from config.cube_defaults import SCALE
Config.set('graphics', 'depthbuffer', 1)


class CubeWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cube = Cube()  # your Cube class
        self.rotation_x = 25
        self.rotation_y = 30
        self.camera_distance = 12.0  # push cube away from camera
        self.scale = SCALE

        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        Clock.schedule_interval(self.update_cube, 1 / 60)

    # --- Rotation ---
    def rotate_vertex(self, vertex, angle_x, angle_y):
        x, y, z = vertex

        # rotate around X axis
        cos_x, sin_x = cos(radians(angle_x)), sin(radians(angle_x))
        y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x

        # rotate around Y axis
        cos_y, sin_y = cos(radians(angle_y)), sin(radians(angle_y))
        x, z = x * cos_y + z * sin_y, -x * sin_y + z * cos_y

        return x, y, z

    # --- Projection ---
    def project_vertex(self, vertex):
        x, y, z = vertex
        z += self.camera_distance  # push cube forward
        if z <= 0.1:
            return None
        f = 3.0  # perspective factor
        x_proj = x / (f - z)
        y_proj = y / (f - z)
        return x_proj, y_proj

    # --- Normals ---
    def calculate_face_normal(self, face_vertices):
        p1, p2, p3 = face_vertices[:3]
        v1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
        v2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])
        normal = (
            v1[1] * v2[2] - v1[2] * v2[1],
            v1[2] * v2[0] - v1[0] * v2[2],
            v1[0] * v2[1] - v1[1] * v2[0],
        )
        return normal

    def is_face_visible(self, normal):
        # camera looks down -Z axis
        view_dir = (0, 0, -1)
        dot = sum(n * v for n, v in zip(normal, view_dir))
        return dot > 0  # flip sign

    # --- Drawing ---
    def draw_cube(self):
        self.canvas.clear()
        glClear(GL_DEPTH_BUFFER_BIT)

        with self.canvas:
            PushMatrix()
            Translate(self.center_x, self.center_y, 0)
            Scale(self.scale, self.scale, self.scale)

            faces_to_draw = []

            for piece in self.cube:
                # shift pieces so cube is centered at origin
                px, py, pz = piece.position  # e.g. (0,1,2)
                offset = (px - 1, py - 1, pz - 1)

                for face in piece.faces.values():
                    # apply piece offset
                    verts = [(vx + offset[0], vy + offset[1], vz + offset[2])
                             for vx, vy, vz in face.vertices]

                    # rotate into camera space
                    rotated = [self.rotate_vertex(v, self.rotation_x, self.rotation_y) for v in verts]

                    # --- back-face culling (keep only faces facing camera) ---
                    normal = self.calculate_face_normal(rotated)
                    if not self.is_face_visible(normal):
                        continue

                    # --- winding order fix ---
                    # If the normal points away from camera, reverse vertex order
                    # (you can flip <0 vs >0 depending on your handedness)
                    if normal[2] > 0:
                        rotated.reverse()
                    # --------------------------------------------------------

                    # project to 2D
                    projected = [self.project_vertex(v) for v in rotated]
                    if any(p is None for p in projected):
                        continue

                    # compute average depth for painter’s sort
                    avg_z = sum(v[2] for v in rotated) / len(rotated)
                    faces_to_draw.append((avg_z, projected, face.colour))

            # sort far → near
            faces_to_draw.sort(reverse=True, key=lambda f: f[0])

            # draw quads
            for _, verts2d, color in faces_to_draw:
                Color(*color)
                Quad(points=(verts2d[0][0], verts2d[0][1],
                             verts2d[1][0], verts2d[1][1],
                             verts2d[2][0], verts2d[2][1],
                             verts2d[3][0], verts2d[3][1]))
            PopMatrix()

    def update_cube(self, dt):
        self.rotation_x += 1
        self.rotation_y += 1
        self.draw_cube()
