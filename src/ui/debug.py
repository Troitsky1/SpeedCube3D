# ui/debug.py
from kivy.graphics import Color, Line
import numpy as np


def draw_debug_vectors(widget, ray_origin, ray_dir,
                       face_center, face_normal,
                       vec_cp, quadrant_vectors,
                       ray_length=10.0, scale=1.0):
    """
    Draw debug vectors for ray casting and face bisectors.

    Args:
        widget: Kivy widget with a canvas (e.g., CubeWidget).
        ray_origin: np.ndarray, starting point of the ray.
        ray_dir: np.ndarray, direction of the ray.
        face_center: np.ndarray, center of the selected face.
        face_normal: np.ndarray, normal of the selected face.
        vec_cp: np.ndarray, vector from face center -> intersection point.
        quadrant_vectors: list of np.ndarray, the 4 bisectors from face center.
        ray_length: float, how far to draw the ray.
        scale: float, multiplier for bisector vector length.
    """

    with widget.canvas:
        # Ray in red
        Color(1, 0, 0)
        ray_end = ray_origin + ray_dir * ray_length
        Line(points=[*ray_origin, *ray_end], width=1)

        # Face normal in blue
        Color(0, 0, 1)
        normal_end = face_center + face_normal * (np.linalg.norm(vec_cp) * 0.5)
        Line(points=[*face_center, *normal_end], width=1)

        # Vector from center -> intersection point in green
        Color(0, 1, 0)
        cp_end = face_center + vec_cp
        Line(points=[*face_center, *cp_end], width=1)

        # Bisectors in yellow
        Color(1, 1, 0)
        for qv in quadrant_vectors:
            bis_end = face_center + qv * (scale * np.linalg.norm(vec_cp))
            Line(points=[*face_center, *bis_end], width=1)
