from __future__ import annotations  # allows using "Piece" as a string
from typing import TYPE_CHECKING, Dict
import numpy as np

from .face import Face

if TYPE_CHECKING:
    from .slice import Slice


class Piece:
    def __init__(self, position, cube):
        self.position = position
        self.cube = cube
        self.colours = self.assign_colours()
        self.vertices = self.get_vertices(self.cube)
        self.faces = self.get_faces()
        self.slices = []

    def assign_slice(self, slice_to_add: "Slice"):
        self.slices.append(slice_to_add)

    def get_vertices(self, cube):
        x = self.position[0]
        y = self.position[1]
        z = self.position[2]

        cube_max = np.max(np.stack(cube.vertices), axis=0)
        cube_min = np.min(np.stack(cube.vertices), axis=0)

        increment_x = (cube_max[0] - cube_min[0]) / 3
        increment_y = (cube_max[1] - cube_min[1]) / 3
        increment_z = (cube_max[2] - cube_min[2]) / 3

        # Calculate min and max coordinates for the piece
        min_x = cube_min[0] + increment_x * x
        max_x = cube_min[0] + increment_x * (x + 1)
        min_y = cube_min[1] + increment_y * y
        max_y = cube_min[1] + increment_y * (y + 1)
        min_z = cube_min[2] + increment_z * z
        max_z = cube_min[2] + increment_z * (z + 1)

        # Define vertices in clockwise order from front to back
        vertices = [
            # Front face in clockwise order
            (min_x, min_y, max_z),  # Bottom-left front
            (max_x, min_y, max_z),  # Bottom-right front
            (max_x, max_y, max_z),  # Top-right front
            (min_x, max_y, max_z),  # Top-left front

            # Back face in clockwise order
            (min_x, min_y, min_z),  # Bottom-left back
            (max_x, min_y, min_z),  # Bottom-right back
            (max_x, max_y, min_z),  # Top-right back
            (min_x, max_y, min_z)  # Top-left back
        ]

        return vertices

    def get_faces(self) -> Dict[str, Face]:
        faces = {}
        for face_name in self.colours:
            faces[face_name] = Face(self, face_name, self.colours[face_name],)
        return faces

    def assign_colours(self):
        (x, y, z) = self.position
        colors = {
            'left': (0, 0, 0),
            'right': (0, 0, 0),
            'down': (0, 0, 0),
            'up': (0, 0, 0),
            'back': (0, 0, 0),
            'front': (0, 0, 0)
        }

        # Assign the appropriate color if the face is on the outside
        if x == 0:
            colors['left'] = self.cube.init_colours['left']
        if x == 2:
            colors['right'] = self.cube.init_colours['right']
        if y == 0:
            colors['down'] = self.cube.init_colours['down']
        if y == 2:
            colors['up'] = self.cube.init_colours['up']
        if z == 0:
            colors['back'] = self.cube.init_colours['back']
        if z == 2:
            colors['front'] = self.cube.init_colours['front']

        return colors
