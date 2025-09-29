import numpy as np

def intersect_with_plane(ray_origin, ray_dir, plane_point, plane_normal):
    """
    Return the intersection of a ray with a plane.
    Does not check bounds, so intersection can lie anywhere on the plane.
    """
    denom = np.dot(plane_normal, ray_dir)
    if np.isclose(denom, 0):
        return None  # ray parallel to plane
    t = np.dot(plane_normal, plane_point - ray_origin) / denom
    if t <= 0:
        return None  # behind camera
    return ray_origin + t * ray_dir