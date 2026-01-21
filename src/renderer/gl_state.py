
# src/renderer/gl_state.py

from kivy.graphics.opengl import (
    glClear, glEnable, glDisable, glDepthFunc, glCullFace, glFrontFace,
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST, GL_CULL_FACE,
    GL_LESS, GL_LEQUAL,
    GL_BACK, GL_CW, GL_CCW,
)

# --- Buffer clears ---
def clear_color_depth(*_):
    """Clear color + depth buffers during the active GL draw pass."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

# --- Depth test toggles ---
def depth_on(*_):
    glEnable(GL_DEPTH_TEST)

def depth_off(*_):
    glDisable(GL_DEPTH_TEST)

# --- Depth compare modes ---
def depth_less(*_):
    glDepthFunc(GL_LESS)

def depth_lequal(*_):
    glDepthFunc(GL_LEQUAL)

# --- Face culling toggles (optional) ---
def cull_on(*_):
    glEnable(GL_CULL_FACE)

def cull_off(*_):
    glDisable(GL_CULL_FACE)

def cull_back(*_):
    glCullFace(GL_BACK)

def front_face_cw(*_):
    glFrontFace(GL_CW)

def front_face_ccw(*_):
    glFrontFace(GL_CCW)
