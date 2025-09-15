from __future__ import annotations  # allows using "Piece" as a string
from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from .piece import Piece  # only for type checking, not runtime
    from .cube import Cube


class Slice:
    def __init__(self, axis, index, cube: "Cube"):
        """
        Initializes a Slice object.

        Parameters:
        axis (str): The axis this slice is on ('x', 'y', or 'z').
        index (int): The index on the axis where the slice is located (0, 1, or 2).
        """
        self.cube = cube
        self.axis = axis
        self.index = index
        self.pieces = []  # Holds the 9 pieces in this slice
        self.normal = self.set_normal()

    def add_piece(self, piece: "Piece"):
        """
        Adds a Piece object to the slice.

        Parameters:
        piece (Piece): The piece to add to this slice.
        """
        if len(self.pieces) < 9:
            self.pieces.append(piece)
        else:
            raise ValueError("A slice can only contain 9 pieces.")

    def get_positions(self):
        """
        Returns a list of positions of all pieces in this slice.
        """
        return [piece.position for piece in self.pieces]

    def __repr__(self):
        """
        Representation of the Slice object, showing the axis, index, and piece positions.
        """
        return f"Slice(axis={self.axis}, index={self.index})"

    def set_normal(self):
        normal = None
        if self.axis == 'x':
            normal = np.array([1, 0, 0])
        elif self.axis == 'y':
            normal = np.array([0, 1, 0])
        elif self.axis == 'z':
            normal = np.array([0, 0, 1])

        return normal
