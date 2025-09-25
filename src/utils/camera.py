# utils/camera.py
import numpy as np
from math import radians, tan, cos, sin
from config.cube_defaults import SCALE

class Camera:
    def __init__(self, position, target, up=(0, 1, 0),
                 fov=60.0, aspect=1.0, near=0.1, far=100.0):
        self._position = np.array(position, dtype=float)
        self._target = np.array(target, dtype=float)
        self.up = np.array(up, dtype=float)
        self.fov = fov
        self.aspect = aspect
        self.near = near
        self.far = far

        # orbit state
        self.radius = np.linalg.norm(self._position - self._target)
        self.yaw = 0.0    # horizontal angle (deg)
        self.pitch = 0.0  # vertical angle (deg)

    # --- Properties ---
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
        d = self.target - self.position
        return d / np.linalg.norm(d)

    @property
    def right(self):
        return np.cross(self.direction, self.up) / np.linalg.norm(np.cross(self.direction, self.up))

    @property
    def true_up(self):
        return np.cross(self.right, self.direction)

    # --- Camera motion ---
    def update_position_from_angles(self):
        """Recompute position from yaw, pitch, and radius."""
        rad_yaw = - radians(self.yaw)
        rad_pitch = - radians(self.pitch)

        x = self.radius * cos(rad_pitch) * sin(rad_yaw)
        y = self.radius * sin(rad_pitch)
        z = self.radius * cos(rad_pitch) * cos(rad_yaw)

        self._position = self.target + np.array([x, y, z])

    def orbit(self, dx, dy, sensitivity=0.3):
        """
        Orbit camera around target by dx, dy (pixels or normalized units).
        dx → changes yaw
        dy → changes pitch
        """
        self.yaw = (self.yaw + dx * sensitivity) % 360.0
        self.pitch = max(-90.0, min(90.0, self.pitch + dy * sensitivity))
        self.update_position_from_angles()

    def set_angles(self, yaw, pitch):
        """
        Directly set yaw/pitch, with clamping and wrapping.
        """
        self.yaw = yaw % 360.0
        self.pitch = max(-90.0, min(90.0, pitch))
        self.update_position_from_angles()

    # --- Ray casting ---
    def get_ray(self, screen_x, screen_y, screen_w, screen_h):
        nx = (2.0 * screen_x / screen_w) - 1.0
        ny = 1.0 - (2.0 * screen_y / screen_h)

        tan_fov = tan(radians(self.fov) / 2.0)
        px = nx * tan_fov * self.aspect
        py = ny * tan_fov

        ray_dir = (self.direction + px * self.right + py * self.true_up)
        ray_dir /= np.linalg.norm(ray_dir)

        return self.position, ray_dir

    # --- Projection ---
    def world_to_screen(self, vertices, width, height, scale=SCALE):
        f = self.direction
        r = self.right
        u = self.true_up

        # View matrix
        T = np.identity(4)
        T[:3, 3] = -self.position
        R = np.identity(4)
        R[:3, :3] = np.vstack([r, u, -f])
        view_matrix = R @ T

        # --- Keep your width dependency ---
        cube_width = scale
        cube_height = cube_width * (height / width)

        # --- Perspective projection matrix ---
        fov_rad = np.radians(self.fov)
        f_n = 1.0 / np.tan(fov_rad / 2.0)
        z_near, z_far = self.near, self.far

        proj_matrix = np.zeros((4, 4))
        proj_matrix[0, 0] = f_n / (width / height)  # aspect ratio correction
        proj_matrix[1, 1] = f_n
        proj_matrix[2, 2] = (z_far + z_near) / (z_near - z_far)
        proj_matrix[2, 3] = (2 * z_far * z_near) / (z_near - z_far)
        proj_matrix[3, 2] = -1.0

        verts_2d, depths = [], []
        for v in vertices:
            v_h = np.array([*v, 1.0])
            v_view = view_matrix @ v_h
            v_clip = proj_matrix @ v_view

            if v_clip[3] == 0:
                continue

            # perspective divide
            v_ndc = v_clip[:3] / v_clip[3]

            # Cull if outside clip volume
            if np.any(np.abs(v_ndc) > 1):
                continue

            # screen mapping (unchanged)
            x_screen = (v_ndc[0] + 1) * 0.5 * width
            y_screen = (1 - (v_ndc[1] + 1) * 0.5) * height
            verts_2d.append((x_screen, y_screen))
            depths.append(v_view[2])

        return verts_2d, np.mean(depths) if depths else (None, None)
