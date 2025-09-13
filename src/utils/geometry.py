from math import sin, cos, radians

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
