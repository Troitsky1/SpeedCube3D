# renderer/camera_controller.py
import numpy as np
from utils.ray_casting import get_camera_position


class CameraController:
    def __init__(self, rot_x=30, rot_y=45, distance=10.0):
        self.rot_x = rot_x
        self.rot_y = rot_y
        self.distance = distance

    @property
    def position(self):
        return get_camera_position(self.rot_x, self.rot_y, self.distance)

    @property
    def direction(self):
        pos = self.position
        return -pos / np.linalg.norm(pos)
