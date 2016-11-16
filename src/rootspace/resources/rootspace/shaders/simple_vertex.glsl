#version 330 core

layout(location = 0) in vec4 vert_pos;
layout(location = 1) in vec4 vert_col;

uniform mat4 mvp_matrix;

smooth out vec4 color;

void main() {
    gl_Position = mvp_matrix * vert_pos;
    color = vert_col;
}
