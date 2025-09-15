import numpy as np

SCALE = 100
DEFAULT_SIZE = 3  # 3x3x3 cube\
DEFAULT_FACE_COLORS = {
    'up': np.array([1, 1, 1, 1], dtype=np.float32),       # White
    'down': np.array([1, 1, 0, 1], dtype=np.float32),     # Yellow
    'front': np.array([0, 0, 1, 1], dtype=np.float32),    # Blue
    'back': np.array([0, 1, 0, 1], dtype=np.float32),     # Green
    'left': np.array([1, 0, 0, 1], dtype=np.float32),     # Red
    'right': np.array([1, 0.5, 0, 1], dtype=np.float32),  # Orange
}
