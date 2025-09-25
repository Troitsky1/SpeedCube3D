import numpy as np

SCALE = 10
DEFAULT_SIZE = 3  # 3x3x3 cube\
DEFAULT_FACE_COLORS = {
    'up': np.array([1, 1, 1, 1], dtype=np.float32),       # White
    'down': np.array([1, 1, 0, 1], dtype=np.float32),     # Yellow
    'front': np.array([0, 0, 1, 1], dtype=np.float32),    # Blue
    'back': np.array([0, 1, 0, 1], dtype=np.float32),     # Green
    'left': np.array([1, 0, 0, 1], dtype=np.float32),     # Red
    'right': np.array([1, 0.5, 0, 1], dtype=np.float32),  # Orange
}
FACE_AXES = {
    'left':  ('x', -1),
    'right': ('x', +1),
    'down':  ('y', -1),
    'up':    ('y', +1),
    'back':  ('z', -1),
    'front': ('z', +1),
}
