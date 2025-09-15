# ui/cube_widget.py
from kivy.uix.widget import Widget
from kivy.graphics import *
from kivy.clock import Clock
from kivy.graphics.opengl import *
from kivy.config import Config
from math import sin, cos, radians
from cube.cube import Cube
from config.cube_defaults import SCALE

Config.set('graphics', 'depthbuffer', 1)


class CubeWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cube = Cube()
        self.rotation_x = 25
        self.rotation_y = 30
        self.camera_distance = 10.0  # distance from origin along -Z
        self.scale = SCALE
        self.rotating_slices = []  # ← list of (axis, index) tuples
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        # Enable culling
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)  # discard back faces
        glFrontFace(GL_CW)  # front faces are counter-clockwise

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

    # --- Projection (camera at origin looking +Z) ---
    def project_vertex(self, vertex):
        x, y, z = vertex
        z += self.camera_distance  # push cube in front of camera
        if z <= 0:
            return None
        f = 4.0  # focal length
        x_proj = (x / z) * f * self.scale + self.center_x
        y_proj = (y / z) * f * self.scale + self.center_y
        return x_proj, y_proj

    # --- Normals ---
    def calculate_face_normal(self, verts3d):
        p1, p2, p3 = verts3d[:3]
        v1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
        v2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])
        return (
            v1[1] * v2[2] - v1[2] * v2[1],
            v1[2] * v2[0] - v1[0] * v2[2],
            v1[0] * v2[1] - v1[1] * v2[0],
        )

    def is_face_visible(self, normal):
        # Camera looks down +Z, so visible faces have normals pointing toward -Z
        view_dir = (0, 0, 1)
        dot = sum(n * v for n, v in zip(normal, view_dir))
        return dot < 0

    # --- Drawing ---
    # --- Drawing ---
    def draw_cube(self):
        self.canvas.clear()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        with self.canvas:
            faces_to_draw = []

            # --- Gather faces to draw ---
            for piece in self.cube:
                px, py, pz = piece.position
                offset = (px - 1, py - 1, pz - 1)

                for face in piece.faces.values():
                    # --- Skip hidden internal faces unless slice is rotating ---
                    if not self.is_face_exposed(piece, face) and not self.is_slice_rotating(piece):
                        continue

                    # Offset + rotate vertices
                    verts3d = [(vx, vy, vz)
                               for vx, vy, vz in face.vertices]
                    verts3d = [self.rotate_vertex(v, self.rotation_x, self.rotation_y) for v in verts3d]

                    # Project vertices to 2D
                    verts2d = [self.project_vertex(v) for v in verts3d]
                    if any(v is None for v in verts2d):
                        continue

                    # Average Z for sorting
                    avg_z = sum(v[2] for v in verts3d) / len(verts3d)
                    faces_to_draw.append((avg_z, verts2d, face.colour))

            # Sort far → near for correct overlay
            faces_to_draw.sort(key=lambda f: f[0])

            # --- Draw faces and borders ---
            for _, verts2d, color in faces_to_draw:
                # Draw main face
                Color(*color)
                Quad(points=(
                    verts2d[0][0], verts2d[0][1],
                    verts2d[1][0], verts2d[1][1],
                    verts2d[2][0], verts2d[2][1],
                    verts2d[3][0], verts2d[3][1],
                ))

                # Draw border only if external face
                face_color = tuple(color)  # convert NumPy array to tuple
                if face_color[:3] != (0, 0, 0):  # compare only RGB
                    self.draw_face_border(verts2d, border_color=(0, 0, 0, 1), border_width=1)

    def draw_face_border(self, verts2d, border_color=(0, 0, 0, 1), border_width=1.0):
        Color(*border_color)
        inset_pixels = 2  # desired inset in screen pixels
        inset = inset_pixels #* self.scale  # compensate for zoom

        for i in range(4):
            p1 = verts2d[i]
            p2 = verts2d[(i + 1) % 4]

            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            length = (dx ** 2 + dy ** 2) ** 0.5
            if length == 0:
                continue
            nx, ny = dx / length, dy / length

            start = (p1[0] + nx * inset, p1[1] + ny * inset)
            end = (p2[0] - nx * inset, p2[1] - ny * inset)

            Line(points=[start[0], start[1], end[0], end[1]], width=border_width)

    def update_cube(self, dt):
        self.rotation_x += 1
        self.rotation_y += 1
        self.draw_cube()

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
            if axis == 'x' and px == index: return True
            if axis == 'y' and py == index: return True
            if axis == 'z' and pz == index: return True
        return False
