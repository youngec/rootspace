# -*- coding: utf-8 -*-

# Also check out http://www.lfd.uci.edu/~gohlke/code/transformations.py.html

import math
import ctypes
import glfw
import numpy
import OpenGL.GL as GL
from OpenGL.GL.shaders import compileProgram, compileShader


def mat4x4_identity():
    return numpy.eye(4, dtype=numpy.float)


def mat4x4_rotation_z(angle):
    sin = math.sin(angle)
    cos = math.cos(angle)
    return numpy.array((
            (cos, -sin, 0, 0),
            (sin, cos, 0, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 1)
        ),
        dtype=numpy.float
    )


def mat4x4_ortho(l, r, b, t, n, f):
    return numpy.array((
            (2 / (r - l), 0, 0, 0),
            (0, 2 / (t - b), 0, 0),
            (0, 0, -2 / (f - n), 0),
            (0, 0, 0, 1)
        ),
        dtype=numpy.float
    )


def main():
    # Initialize the library
    if not glfw.init():
        return

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(640, 480, "Hello World", None, None)
    if not window:
        glfw.terminate()
        return

    # Make the window's context current
    glfw.make_context_current(window)
    glfw.swap_interval(1)

    # Define the vertices
    vertex_pos = [
        -0.6, -0.4, 1.0, 0.0, 0.0,
        0.6, -0.4, 0.0, 1.0, 0.0,
        0, 0.6, 0.0, 0.0, 1.0
    ]
    num_vertices = 3

    # Define the shaders
    vertex_shader = """uniform mat4 MVP;
    attribute vec3 vCol;
    attribute vec2 vPos;
    varying vec3 color;
    void main() {
        gl_Position = MVP * vec4(vPos, 0.0, 1.0);
        color = vCol;
    }
    """

    fragment_shader = """varying vec3 color;
    void main() {
        gl_FragColor = vec4(color, 1.0);
    }
    """

    # Initialize the vertex buffer
    vbo_pos = GL.glGenBuffers(1)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_pos)
    array_type = (GL.GLfloat * len(vertex_pos))
    GL.glBufferData(
        GL.GL_ARRAY_BUFFER, len(vertex_pos) * ctypes.sizeof(GL.GLfloat),
        array_type(*vertex_pos),
        GL.GL_STATIC_DRAW
    )
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

    # Initialize the shaders
    shader_program = compileProgram(
        compileShader(vertex_shader, GL.GL_VERTEX_SHADER),
        compileShader(fragment_shader, GL.GL_FRAGMENT_SHADER)
    )

    # Get the shader parameter locations
    mvp_loc = GL.glGetUniformLocation(shader_program, "MVP")
    vpos_loc = GL.glGetAttribLocation(shader_program, "vPos")
    vcol_loc = GL.glGetAttribLocation(shader_program, "vCol")

    # Bind the vertex array
    GL.glEnableVertexAttribArray(vpos_loc)
    GL.glVertexAttribPointer(vpos_loc, 2, GL.GL_FLOAT, False,
        ctypes.sizeof(GL.GLfloat) * 5, 0
    )
    GL.glEnableVertexAttribArray(vcol_loc)
    GL.glVertexAttribPointer(vcol_loc, 3, GL.GL_FLOAT, False,
        ctypes.sizeof(GL.GLfloat) * 5, ctypes.sizeof(GL.GLfloat) * 2
    )

    # Set the clear color
    GL.glClearColor(0.0, 0.0, 0.0, 0.0)

    # Loop until the user closes the window
    while not glfw.window_should_close(window):
        width, height = glfw.get_framebuffer_size(window)
        ratio = width / height

        # Calculate the model-view-projection matrix
        m = mat4x4_identity()
        v = mat4x4_rotation_z(glfw.get_time())
        p = mat4x4_ortho(-ratio, ratio, -1, 1, 1, -1)
        mvp = p @ v @ m

        # Update the viewport size
        GL.glViewport(0, 0, width, height)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # Bind the programs and buffers
        GL.glUseProgram(shader_program)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo_pos)
        GL.glEnableVertexAttribArray(vpos_loc)
        GL.glEnableVertexAttribArray(vcol_loc)

        GL.glUniformMatrix4fv(mvp_loc, 1, False, mvp)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, num_vertices)

        # Unbind the programs and buffers
        GL.glDisableVertexAttribArray(vcol_loc)
        GL.glDisableVertexAttribArray(vpos_loc)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glUseProgram(0)

        # Swap front and back buffers
        glfw.swap_buffers(window)

        # Poll for and process events
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()
