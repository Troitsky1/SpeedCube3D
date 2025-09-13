from kivy.uix.widget import Widget
from kivy.graphics import Color, Quad, PushMatrix, PopMatrix, Translate, Scale
from kivy.clock import Clock
from kivy.graphics.opengl import glEnable, glDepthFunc, glClear, GL_DEPTH_TEST, GL_LESS, GL_DEPTH_BUFFER_BIT
from kivy.config import Config

from utils import rotate_vertex, project_vertex, calculate_face_center, calculate_normal, is_face_visible

# Enable depth buffer for proper 3D rendering
Config.set('graphics', 'depthbuffer', 1)


class CubeWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rotation_angle_x = 0
        self.rotation_angle_y = 0

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        Clock.schedule_interval(self.update_cube, 1 / 60)

    def draw_cube(self):
        self.canvas.clear()
        glClear(GL_DEPTH_BUFFER_BIT)

        with self.canvas:
            PushMatrix()
            Translate(self.center_x, self.center_y, 0)
            Scale(200, 200, 200)

            # Cube vertices
            vertices = [
                (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),  # Back
                (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),      # Front
            ]

            # Faces
            faces = [
                (0, 1, 2, 3),  # Back
                (4, 5, 6, 7),  # Front
                (0, 4, 7, 3),  # Left
                (2, 6, 5, 1),  # Right
                (3, 7, 6, 2),  # Top
                (0, 1, 5, 4),  # Bottom
            ]

            colors = [
                (1, 0, 0, 1),  # Red
                (0, 1, 0, 1),  # Green
                (0, 0, 1, 1),  # Blue
                (1, 1, 0, 1),  # Yellow
                (1, 0, 1, 1),  # Magenta
                (0, 1, 1, 1),  # Cyan
            ]

            # Rotate vertices
            rotated_vertices = [
                rotate_vertex(v, self.rotation_angle_x, self.rotation_angle_y) for v in vertices
            ]

            # Sort faces by depth
            face_depths = [
                (calculate_face_center(face, rotated_vertices)[2], face, colors[idx])
                for idx, face in enumerate(faces)
            ]
            face_depths.sort(reverse=True, key=lambda f: f[0])

            for _, face, color in face_depths:
                normal = calculate_normal(face, rotated_vertices)
                if is_face_visible(normal):
                    Color(*color)
                    points = []
                    for idx in face:
                        x, y = project_vertex(rotated_vertices[idx])
                        points.extend([x, y])
                    Quad(points=points)

            PopMatrix()

    def update_cube(self, dt):
        self.rotation_angle_x += 1
        self.rotation_angle_y += 1
        self.draw_cube()
