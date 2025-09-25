# utils/camera.py
import numpy as np
from math import radians, tan, cos, sin
from config.cube_defaults import SCALE

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

    def world_to_screen(self, vertices, width, height, scale=SCALE):
        """
        Orthographic projection where cube size follows window width,
        and cube height is derived from cube width to keep proportions square.
        """
        # Build camera basis
        f = self.direction
        r = self.right
        u = self.true_up

        # View matrix
        T = np.identity(4)
        T[:3, 3] = -self.position
        R = np.identity(4)
        R[:3, :3] = np.vstack([r, u, -f])
        view_matrix = R @ T

        # Cube width scales with window width, height derived to stay square
        cube_width = scale
        cube_height = cube_width * (height / width)

        left, right = -cube_width, cube_width
        bottom, top = -cube_height, cube_height
        near, far = self.near, self.far

        proj_matrix = np.identity(4)
        proj_matrix[0, 0] = 2.0 / (right - left)
        proj_matrix[1, 1] = 2.0 / (top - bottom)
        proj_matrix[2, 2] = -2.0 / (far - near)
        proj_matrix[0, 3] = -(right + left) / (right - left)
        proj_matrix[1, 3] = -(top + bottom) / (top - bottom)
        proj_matrix[2, 3] = -(far + near) / (far - near)

        verts_2d, depths = [], []
        for v in vertices:
            v_h = np.array([*v, 1.0])
            v_view = view_matrix @ v_h
            v_clip = proj_matrix @ v_view

            v_ndc = v_clip[:3]

            # Convert to screen space
            x_screen = (v_ndc[0] + 1) * 0.5 * width
            y_screen = (1 - (v_ndc[1] + 1) * 0.5) * height
            verts_2d.append((x_screen, y_screen))
            depths.append(v_view[2])

        return verts_2d, np.mean(depths)

    # utils/camera.py (inside Camera)

    def orbit(self, dx, dy, sensitivity=0.3):
        """
        Orbit camera around target by dx, dy (in pixels or normalized units).
        dx -> rotation around world Y axis (left/right drag)
        dy -> rotation around camera's local X axis (up/down drag)
        """
        # Convert drag to angles
        angle_y = radians(dx * sensitivity)  # horizontal → yaw
        angle_x = radians(dy * sensitivity)  # vertical → pitch

        # Relative vector (camera position wrt target)
        rel = self.position - self.target
        x, y, z = rel

        # --- yaw (around world Y) ---
        cos_y, sin_y = cos(angle_y), sin(angle_y)
        xz_x = x * cos_y - z * sin_y
        xz_z = x * sin_y + z * cos_y
        x, z = xz_x, xz_z

        # --- pitch (around camera's local X axis) ---
        cos_x, sin_x = cos(angle_x), sin(angle_x)
        yz_y = y * cos_x - z * sin_x
        yz_z = y * sin_x + z * cos_x
        y, z = yz_y, yz_z

        # Update camera position
        self.position = self.target + np.array([x, y, z])
