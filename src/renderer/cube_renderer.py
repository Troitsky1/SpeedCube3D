# renderer/cube_renderer.py
from kivy.uix.widget import Widget
from kivy.graphics import Mesh, Color
import numpy as np
from cube.cube import Cube
from cube.piece import Piece
from cube.face import Face


class CubeRenderer(Widget):
    def __init__(self, cube: Cube, **kwargs):
        super().__init__(**kwargs)
        self.cube = cube
        self.piece_meshes = {}  # Map piece -> Kivy Mesh
        self.init_meshes()

    def init_meshes(self):
        """Create a Mesh for each piece and face."""
        for piece in self.cube:
            self.piece_meshes[piece] = []
            for face in piece.faces.values():
                mesh = Mesh(vertices=face.vertices.flatten(), indices=face.indices, mode='triangles')
                self.piece_meshes[piece].append(mesh)

    def update(self):
        """Update all piece positions based on cube state."""
        for piece, meshes in self.piece_meshes.items():
            for i, face in enumerate(piece.faces.values()):
                meshes[i].vertices = face.vertices.flatten()
