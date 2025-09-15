from __future__ import annotations  # allows using "Piece" as a string
from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from .piece import Piece  # only for type checking, not runtime


class Face:
    def __init__(self, piece: "Piece", face, colour):
        self.piece = piece
        self.colour = colour
        self.face = face
        self.vertices = np.array(self.get_vertices(),  dtype=np.float32)
        self.indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
        self.centre = self.get_centre()
        self.normal = self.get_normal()

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
        # Sum up each coordinate
        center_x = sum(vertex[0] for vertex in self.vertices) / 4
        center_y = sum(vertex[1] for vertex in self.vertices) / 4
        center_z = sum(vertex[2] for vertex in self.vertices) / 4

        # Return the center as a tuple
        return center_x, center_y, center_z

    def get_normal(self):
        vertices = self.vertices

        a = np.subtract(vertices[1], vertices[0])  # Vector from V1 to V2
        b = np.subtract(vertices[2], vertices[0])  # Vector from V1 to V3

        # Calculate the cross product of A and B
        normal = np.cross(a, b)

        # Optional: Normalize the normal vector to make it a unit vector
        normal_magnitude = np.linalg.norm(normal)
        if normal_magnitude != 0:
            normal = normal / normal_magnitude
        if self.face in ['left', 'back', 'down']:
            normal *= -1
        return normal

