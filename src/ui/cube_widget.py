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

Config.set('graphics', 'depthbuffer', 1)


class CubeWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cube = Cube()
        self.scale = SCALE
        self.rotating_slices = []
        self.background_clicked = True #***************REPLACE WITH CHECKER FUNCTION******************

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
        self.canvas.clear()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        with self.canvas:
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
                Color(*color)
                Quad(points=[
                    verts2d[0][0], verts2d[0][1],
                    verts2d[1][0], verts2d[1][1],
                    verts2d[2][0], verts2d[2][1],
                    verts2d[3][0], verts2d[3][1],
                ])

                # Draw black outline for non-internal faces
                if tuple(color[:3]) != (0, 0, 0):
                    self.draw_face_border(verts2d)

    def draw_face_border(self, verts2d, border_color=(0, 0, 0, 1), border_width=1.0):
        Color(*border_color)
        for i in range(4):
            p1 = verts2d[i]
            p2 = verts2d[(i + 1) % 4]
            Line(points=[p1[0], p1[1], p2[0], p2[1]], width=border_width)

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

    def on_touch_move(self, touch):
        if self.background_clicked:  # you’ll add this condition
            dx = touch.dx
            dy = - touch.dy
            self.camera.orbit(dx, dy)
            self.draw_cube()