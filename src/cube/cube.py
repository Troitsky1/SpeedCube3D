import numpy as np
from .slice import Slice
from .piece import Piece
from utils import quaternion_rotation, rotate_slice_indices
from typing import List, Iterator
from config.cube_defaults import DEFAULT_SIZE, DEFAULT_FACE_COLORS


class Cube:
    DEFAULT_SIZE = DEFAULT_SIZE
    DEFAULT_FACE_COLORS = DEFAULT_FACE_COLORS

    def __init__(self, size: float = DEFAULT_SIZE, init_colours: dict = DEFAULT_FACE_COLORS):
        self.size = size
        self.init_colours = init_colours

        self.vertices = np.array([
            [-size, -size, -size],
            [size, -size, -size],
            [size,  size, -size],
            [-size,  size, -size],
            [-size, -size,  size],
            [size, -size,  size],
            [size,  size,  size],
            [-size,  size,  size],
        ])

        self.normals = {
            "front": np.array([0, 0, 1]),
            "back":  np.array([0, 0, -1]),
            "left":  np.array([-1, 0, 0]),
            "right": np.array([1, 0, 0]),
            "up":    np.array([0, 1, 0]),
            "down":  np.array([0, -1, 0]),
        }

        self.slices = self.make_slices()
        self.pieces = self.get_pieces()
        self.centres = self.get_centres()

    def __iter__(self) -> Iterator[Piece]:
        """Yield every Piece in the cube (flattened from the 3D list)."""
        for plane in self.pieces:  # x dimension
            for row in plane:  # y dimension
                for piece in row:  # z dimension
                    yield piece

    # -----------------
    # Cube construction
    # -----------------
    def make_slices(self):
        return {
            "x_slices": [Slice("x", i, self) for i in range(3)],
            "y_slices": [Slice("y", i, self) for i in range(3)],
            "z_slices": [Slice("z", i, self) for i in range(3)],
        }

    def get_pieces(self) -> List[List[List["Piece"]]]:
        # Build the cube directly with Piece objects
        pieces: List[List[List["Piece"]]] = [
            [
                [
                    Piece((x, y, z), self)
                    for z in range(3)
                ]
                for y in range(3)
            ]
            for x in range(3)
        ]

        # Register each piece into its slices
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    piece = pieces[x][y][z]

                    # X slice
                    self.slices["x_slices"][x].add_piece(piece)
                    piece.assign_slice(self.slices["x_slices"][x])

                    # Y slice
                    self.slices["y_slices"][y].add_piece(piece)
                    piece.assign_slice(self.slices["y_slices"][y])

                    # Z slice
                    self.slices["z_slices"][z].add_piece(piece)
                    piece.assign_slice(self.slices["z_slices"][z])

        return pieces

    def get_centres(self):
        return {key: normal * self.size for key, normal in self.normals.items()}

    # -----------------
    # Cube operations
    # -----------------
    def update_state(self, rotated_slice, cw_ccw=True):
        """
        Rotate a slice of the cube and update the cube's internal state.

        Args:
            rotated_slice (Slice): The slice object to rotate.
            cw_ccw (bool): True for clockwise, False for counter-clockwise.
        """
        # Map slice axis to rotation vector
        axis_map = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1)}
        axis_vector = axis_map[rotated_slice.axis]

        # Determine rotation angle
        angle = np.pi / 2  # 90 degrees per move
        if not cw_ccw:
            angle = -angle

        # 1. Rotate vertices for pieces in this slice
        for piece in rotated_slice.pieces:
            piece.vertices = quaternion_rotation(piece.vertices, axis_vector, angle)

            # Update each face geometry
            for face in piece.faces.values():
                face.vertices = face.get_vertices()
                face.centre = face.get_centre()
                face.normal = face.get_normal()

        # 2. Reorder piece positions using the utility function
        old_positions = [piece.position for piece in rotated_slice.pieces]
        mapping = rotate_slice_indices(rotated_slice.axis, cw_ccw)

        for new_idx, piece in zip(mapping, rotated_slice.pieces):
            piece.position = old_positions[new_idx]

        # 3. Update slice memberships
        for axis, slices in self.slices.items():
            for s in slices:
                s.pieces = []

        for x in range(3):
            for y in range(3):
                for z in range(3):
                    piece = self.pieces[x][y][z]
                    self.slices['x_slices'][x].add_piece(piece)
                    piece.assign_slice(self.slices['x_slices'][x])
                    self.slices['y_slices'][y].add_piece(piece)
                    piece.assign_slice(self.slices['y_slices'][y])
                    self.slices['z_slices'][z].add_piece(piece)
                    piece.assign_slice(self.slices['z_slices'][z])

    def is_solved(self) -> bool:
        """Check if cube is in solved state (returns True/False only)."""
        expected_colors = {
            "left":  self.pieces[0][1][1].faces["left"].colour,
            "right": self.pieces[2][1][1].faces["right"].colour,
            "up":    self.pieces[1][2][1].faces["up"].colour,
            "down":  self.pieces[1][0][1].faces["down"].colour,
            "front": self.pieces[1][1][2].faces["front"].colour,
            "back":  self.pieces[1][1][0].faces["back"].colour,
        }

        for x in range(3):
            for y in range(3):
                for z in range(3):
                    piece = self.pieces[x][y][z]
                    for face_name, face in piece.faces.items():
                        if face.colour == (0, 0, 0):
                            continue
                        if face.colour != expected_colors[face_name]:
                            return False
        return True
