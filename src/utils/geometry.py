from math import sin, cos, radians
import numpy as np


def rotate_vertex(vertex, angle_x, angle_y):
    x, y, z = vertex
    cos_x, sin_x = cos(radians(angle_x)), sin(radians(angle_x))
    y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x
    cos_y, sin_y = cos(radians(angle_y)), sin(radians(angle_y))
    x, z = x * cos_y + z * sin_y, -x * sin_y + z * cos_y
    return x, y, z


def project_vertex(vertex):
    perspective_factor = 3
    x, y, z = vertex
    z = max(z, -perspective_factor + 0.001)
    x /= (perspective_factor - z)
    y /= (perspective_factor - z)
    return x, y


def calculate_face_center(face, vertices):
    x = sum(vertices[i][0] for i in face) / len(face)
    y = sum(vertices[i][1] for i in face) / len(face)
    z = sum(vertices[i][2] for i in face) / len(face)
    return x, y, z


def calculate_normal(face, vertices):
    p1, p2, p3 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
    v1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
    v2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])
    normal = (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0],
    )
    return normal


def is_face_visible(normal):
    view_direction = (0, 0, -1)
    dot_product = sum(n * v for n, v in zip(normal, view_direction))
    return dot_product < 0


def quaternion_rotation(vertices, axis, angle):
    """
    Rotate a set of 3D vertices using a quaternion.

    Args:
        vertices (list[tuple[float, float, float]] | np.ndarray):
            Vertices to rotate (Nx3 array or list of 3D tuples).
        axis (tuple[float, float, float]):
            Axis of rotation (x, y, z).
        angle (float):
            Angle of rotation in radians.

    Returns:
        np.ndarray: Rotated vertices (Nx3).
    """
    vertices = np.array(vertices, dtype=float)
    axis = np.array(axis, dtype=float)
    axis = axis / np.linalg.norm(axis)

    # Build quaternion (q = [w, x, y, z])
    half_angle = angle / 2
    w = np.cos(half_angle)
    x, y, z = axis * np.sin(half_angle)
    q = np.array([w, x, y, z])

    # Conjugate of quaternion
    q_conj = np.array([w, -x, -y, -z])

    def quat_mult(q1, q2):
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        return np.array([
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2
        ])

    rotated = []
    for v in vertices:
        v_quat = np.array([0, *v])  # Represent vertex as quaternion
        v_rot = quat_mult(quat_mult(q, v_quat), q_conj)
        rotated.append(v_rot[1:])  # Drop scalar part
    return np.array(rotated)


def rotate_slice_indices(axis: str, clockwise: bool = True) -> list[int]:
    """
    Returns a mapping of old indices to new indices for a 3x3 slice rotation.

    Args:
        axis (str): One of 'x', 'y', or 'z'.
        clockwise (bool): True for clockwise rotation, False for counter-clockwise.

    Returns:
        list[int]: New index mapping for rotated slice pieces.
    """
    # Standard 3x3 rotation mapping (flattened slice)
    cw_mapping = [6, 3, 0, 7, 4, 1, 8, 5, 2]
    ccw_mapping = [2, 5, 8, 1, 4, 7, 0, 3, 6]

    return cw_mapping if clockwise else ccw_mapping
