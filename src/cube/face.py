import numpy as np
class Face:
    def __init__(self, piece, face, colour):
        self.piece = piece
        self.colour = colour
        self.face = face
        self.vertices = self.get_vertices()
        self.centre = self.get_centre()
        self.normal = self.get_normal()

    def get_vertices(self):
        vertices = self.piece.vertices
        face_vertices = {
            "front": [vertices[0], vertices[1], vertices[2], vertices[3]],
            "back": [vertices[4], vertices[5], vertices[6], vertices[7]],
            "left": [vertices[0], vertices[4], vertices[7], vertices[3]],
            "right": [vertices[1], vertices[5], vertices[6], vertices[2]],
            "up": [vertices[3], vertices[2], vertices[6], vertices[7]],
            "down": [vertices[0], vertices[1], vertices[5], vertices[4]]
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

