# utils/camera.py
import numpy as np
from math import radians, tan

class Camera:
    def __init__(self, position, target, up=(0, 1, 0), fov=60.0, aspect=1.0, near=0.1, far=100.0):
        self.position = np.array(position, dtype=float)
        self.target = np.array(target, dtype=float)
        self.up = np.array(up, dtype=float)
        self.fov = fov
        self.aspect = aspect
        self.near = near
        self.far = far

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = np.array(value, dtype=float)

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = np.array(value, dtype=float)

    @property
    def direction(self):
        """Forward direction (normalized)"""
        d = self.target - self.position
        return d / np.linalg.norm(d)

    @property
    def right(self):
        """Right vector from camera basis"""
        return np.cross(self.direction, self.up) / np.linalg.norm(np.cross(self.direction, self.up))

    @property
    def true_up(self):
        """Recomputed up vector (orthogonalized)"""
        return np.cross(self.right, self.direction)

    def get_ray(self, screen_x, screen_y, screen_w, screen_h):
        """
        Convert screen pixel coords into a ray in world space.
        Returns (ray_origin, ray_dir).
        """
        # Normalize screen coords to [-1, 1]
        nx = (2.0 * screen_x / screen_w) - 1.0
        ny = 1.0 - (2.0 * screen_y / screen_h)

        # Projection math
        tan_fov = tan(radians(self.fov) / 2.0)
        px = nx * tan_fov * self.aspect
        py = ny * tan_fov

        ray_dir = (
            self.direction
            + px * self.right
            + py * self.true_up
        )
        ray_dir /= np.linalg.norm(ray_dir)

        return self.position, ray_dir

    # utils/camera.py (inside Camera class)

    import numpy as np

    def world_to_screen(self, vertices, width, height):
        """
        Project a list of 3D vertices from world space into 2D screen space.

        Args:
            vertices: list of np.ndarray, shape (3,)

        Returns:
            (verts_2d, avg_depth) or (None, None) if projection fails
            :param vertices:
            :param height:
            :param width:
        """
        # Build camera basis
        f = self.direction
        r = self.right
        u = self.true_up

        # View matrix (look-at)
        T = np.identity(4)
        T[:3, 3] = -self.position
        R = np.identity(4)
        R[:3, :3] = np.vstack([r, u, -f])  # camera axes

        view_matrix = R @ T

        # Projection matrix (perspective)
        fov_rad = np.radians(self.fov)
        f_n = 1.0 / np.tan(fov_rad / 2)
        z_near, z_far = self.near, self.far

        proj_matrix = np.zeros((4, 4))
        proj_matrix[0, 0] = f_n / self.aspect
        proj_matrix[1, 1] = f_n
        proj_matrix[2, 2] = (z_far + z_near) / (z_near - z_far)
        proj_matrix[2, 3] = (2 * z_far * z_near) / (z_near - z_far)
        proj_matrix[3, 2] = -1.0

        # Transform vertices
        verts_2d = []
        depths = []

        for v in vertices:
            v_h = np.array([v[0], v[1], v[2], 1.0])
            v_view = view_matrix @ v_h
            v_clip = proj_matrix @ v_view

            if v_clip[3] == 0:
                return None, None

            # Perspective divide → normalized device coords
            v_ndc = v_clip[:3] / v_clip[3]

            # Cull if outside clip volume
            if np.any(np.abs(v_ndc) > 1):
                return None, None

            # Convert to screen space (assuming top-left origin)
            x_screen = (v_ndc[0] + 1) * 0.5 * self.aspect * 2 * width  # adjust 400→widget size
            y_screen = (1 - (v_ndc[1] + 1) * 0.5) * height
            verts_2d.append((x_screen, y_screen))
            depths.append(v_view[2])

        avg_depth = np.mean(depths)
        return verts_2d, avg_depth