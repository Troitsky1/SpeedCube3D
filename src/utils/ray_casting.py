from __future__ import annotations
import numpy as np
from typing import Tuple, Optional, List
from cube.cube import Cube
from cube.piece import Piece
from cube.face import Face
from cube.slice import Slice  # forward reference for type hints


# --------------------------
# Camera / Ray Utilities
# --------------------------

def get_camera_position(rot_x: float, rot_y: float, radius: float = 10.0) -> np.ndarray:
    """
    Compute camera position in world coordinates based on rotation angles.
    """
    theta = -np.radians(rot_y)
    phi = np.radians(rot_x)

    x = radius * np.cos(phi) * np.sin(theta)
    y = radius * np.sin(phi)
    z = radius * np.cos(phi) * np.cos(theta)
    return np.array([x, y, z])


def screen_to_world_ray(
    mouse_x: float,
    mouse_y: float,
    screen_width: float,
    screen_height: float,
    camera_pos: np.ndarray,
    camera_dir: np.ndarray,
    camera_up: np.ndarray,
    camera_fov: float,
    camera_distance: float,
) -> np.ndarray:
    """
    Convert screen coordinates to a world-space ray.
    Returns the normalized ray direction.
    """
    ndc_x = (2 * mouse_x) / screen_width - 1
    ndc_y = 1 - (2 * mouse_y) / screen_height

    aspect_ratio = screen_width / screen_height
    near_plane_height = 2 * np.tan(np.radians(camera_fov / 2)) * camera_distance
    near_plane_width = near_plane_height * aspect_ratio

    camera_right = np.cross(camera_up, camera_dir)
    camera_right /= np.linalg.norm(camera_right)

    offset_x = (ndc_x * near_plane_width / 2) * camera_right
    offset_y = (ndc_y * near_plane_height / 2) * camera_up

    point_on_near_plane = camera_pos + camera_dir * camera_distance + offset_x + offset_y
    ray_direction = point_on_near_plane - camera_pos
    ray_direction /= np.linalg.norm(ray_direction)

    return ray_direction


# --------------------------
# Face Picking Utilities
# --------------------------

def vector_from_face_center_to_ray(
    face_center: np.ndarray,
    face_normal: np.ndarray,
    ray_origin: np.ndarray,
    ray_dir: np.ndarray
) -> Optional[np.ndarray]:
    """
    Project a ray onto a plane defined by the face center and normal.
    Returns the vector from the face center to the intersection point.
    """
    ray_dir = ray_dir / np.linalg.norm(ray_dir)
    face_normal = face_normal / np.linalg.norm(face_normal)

    denom = np.dot(face_normal, ray_dir)
    if np.isclose(denom, 0):
        return None

    t = np.dot(face_normal, face_center - ray_origin) / denom
    intersection = ray_origin + t * ray_dir
    return intersection - face_center


def pick_closest_visible_face(
    cube: Cube,
    ray_origin: np.ndarray,
    ray_dir: np.ndarray
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[Piece], Optional[Face]]:
    """
    Return the closest visible face along a ray.
    """
    camera_dir = -ray_origin / np.linalg.norm(ray_origin)
    closest_face: Optional[Face] = None
    closest_piece: Optional[Piece] = None
    shortest_distance: float = float('inf')
    face_center_out: Optional[np.ndarray] = None
    face_normal_out: Optional[np.ndarray] = None

    for piece in cube:  # Uses Cube.__iter__
        for face in piece.faces.values():
            # Only consider faces pointing toward the camera
            if np.dot(face.normal, camera_dir) <= 0:
                continue
            if face.colour == (0.0, 0.0, 0.0):
                continue

            vec_to_ray = vector_from_face_center_to_ray(face.centre, face.normal, ray_origin, ray_dir)
            if vec_to_ray is None:
                continue

            distance = np.linalg.norm(vec_to_ray)
            if float(distance) < shortest_distance:
                shortest_distance = float(distance)
                closest_face = face
                closest_piece = piece
                face_center_out = face.centre
                face_normal_out = face.normal

    return face_center_out, face_normal_out, closest_piece, closest_face


def calculate_face_plane_vectors(normal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Given a face normal, return orthonormal right and up vectors.
    """
    normal = normal / np.linalg.norm(normal)
    if np.allclose(normal, [0, 1, 0]) or np.allclose(normal, [0, -1, 0]):
        arbitrary = np.array([0, 0, 1])
    else:
        arbitrary = np.array([0, 1, 0])

    right = np.cross(normal, arbitrary)
    right /= np.linalg.norm(right)
    up = np.cross(right, normal)
    up /= np.linalg.norm(up)
    return right, up


def calculate_offset_vectors(normal: np.ndarray, right: np.ndarray, up: np.ndarray) -> List[np.ndarray]:
    """
    Generate four vectors at 90-degree intervals around the face normal for quadrant checks.
    """
    first_vec = (right + up) / np.sqrt(2)
    first_vec /= np.linalg.norm(first_vec)

    def rotate_90_in_plane(vec: np.ndarray, normal: np.ndarray) -> np.ndarray:
        return np.cross(normal, vec)

    vectors: List[np.ndarray] = [first_vec]
    for _ in range(3):
        vectors.append(rotate_90_in_plane(vectors[-1], normal))
    return vectors


def find_bisector_vector(origin: np.ndarray, point: np.ndarray, quadrant_vectors: List[np.ndarray]) -> np.ndarray:
    """
    Determine the bisector vector between the quadrant vectors closest to the target point.
    """
    point_vec = point - origin
    point_dir = point_vec / np.linalg.norm(point_vec)
    angles = [np.arccos(np.clip(np.dot(point_dir, qv) / np.linalg.norm(qv), -1, 1)) for qv in quadrant_vectors]
    idx1, idx2 = sorted(range(len(angles)), key=lambda i: angles[i])[:2]
    qv1, qv2 = quadrant_vectors[idx1], quadrant_vectors[idx2]
    bisector = (qv1 + qv2) / np.linalg.norm(qv1 + qv2)
    return bisector * np.linalg.norm(point_vec)


def find_slice_to_rotate_and_direction(
    bisector_vector: np.ndarray,
    bisector_normal: np.ndarray,
    cube: Cube,
    piece: Piece
) -> Tuple[bool, Optional[np.ndarray], Optional[Slice]]:
    """
    Determine which slice to rotate and rotation direction.
    Returns: (cw, rotation_normal, selected_slice)
    """
    cw: bool = True
    rotation_normal: Optional[np.ndarray] = None
    selected_slice: Optional[Slice] = None
    face_name_safe: Optional[str] = None  # Initialize to avoid "unreachable" usage

    # Iterate over piece faces and cube normals to find rotation normal
    for face in piece.faces.values():
        if face.colour == (0.0, 0.0, 0.0):
            continue

        for face_name, normal in cube.normals.items():
            face_name_safe = face_name  # Store last iterated face_name safely
            if np.allclose(bisector_normal, normal) or np.allclose(bisector_normal, -normal):
                continue
            else:
                rotation_normal = normal
                for maybe_slice in piece.slices:
                    if np.allclose(np.cross(maybe_slice.normal, rotation_normal), [0, 0, 0]):
                        selected_slice = maybe_slice

    # Only calculate dot product if we found a rotation normal and a valid face_name
    if rotation_normal is not None and face_name_safe is not None:
        cross_prod = np.cross(bisector_vector, cube.centres[face_name_safe])
        dot_prod = np.dot(rotation_normal, cross_prod)
        if dot_prod > 0:
            cw = False

    return cw, rotation_normal, selected_slice
