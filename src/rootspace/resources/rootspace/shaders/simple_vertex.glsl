#version 330 core

layout(location = 0) in vec3 vert_xyz;
layout(location = 1) in vec2 col_rg;

uniform mat4 mvp_matrix;

smooth out vec4 color;

void main() {
    gl_Position = mvp_matrix * vec4(vert_xyz, 1.0);
    color = vec4(col_rg, 0.0, 1.0);
}
