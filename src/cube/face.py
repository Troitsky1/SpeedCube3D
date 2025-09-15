from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from config.cube_defaults import FACE_AXES

if TYPE_CHECKING:
    from .piece import Piece


class Face:
    def __init__(self, piece: "Piece", face, colour):
        self.axis, self.direction = FACE_AXES[face]
        self.piece = piece
        self.colour = colour
        self.face = face
        self.vertices = np.array(self.get_vertices(), dtype=np.float32)
        self.indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
        self.centre = self.get_centre()
        self.normal = self.get_normal()

        # Apply small offset to internal black faces
        self.apply_internal_offset()

    def get_vertices(self):
        vertices = self.piece.vertices
        face_vertices = {
            "front": [vertices[0], vertices[1], vertices[2], vertices[3]],  # CCW from outside z+
            "back": [vertices[5], vertices[4], vertices[7], vertices[6]],  # CCW from outside z-
            "left": [vertices[4], vertices[0], vertices[3], vertices[7]],  # CCW from outside x-
            "right": [vertices[1], vertices[5], vertices[6], vertices[2]],  # CCW from outside x+
            "up": [vertices[3], vertices[2], vertices[6], vertices[7]],  # CCW from outside y+
            "down": [vertices[4], vertices[5], vertices[1], vertices[0]],  # CCW from outside y-
        }
        return face_vertices[self.face]

    def get_centre(self):
        center_x = sum(vertex[0] for vertex in self.vertices) / 4
        center_y = sum(vertex[1] for vertex in self.vertices) / 4
        center_z = sum(vertex[2] for vertex in self.vertices) / 4
        return center_x, center_y, center_z

    def get_normal(self):
        vertices = self.vertices
        a = np.subtract(vertices[1], vertices[0])
        b = np.subtract(vertices[2], vertices[0])
        normal = np.cross(a, b)
        norm_mag = np.linalg.norm(normal)
        if norm_mag != 0:
            normal = normal / norm_mag
        if self.face in ['left', 'back', 'down']:
            normal *= -1
        return normal

    def apply_internal_offset(self, epsilon=0.001):
        """
        Slightly offsets internal black faces along their normal to prevent z-fighting.
        Called once at initialization.
        """
        if np.allclose(self.colour[:3], (0, 0, 0)):  # only offset black faces
            self.vertices = np.array([v + epsilon * self.normal for v in self.vertices], dtype=np.float32)
            # recalc center after offset
            self.centre = self.get_centre()
