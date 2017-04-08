#version 330 core

layout(location = 0) in vec3 vert_xyz;
layout(location = 2) in vec2 tex_uv;

uniform mat4 mvp_matrix;

smooth out vec2 tex_coords;

void main() {
    gl_Position = mvp_matrix * vec4(vert_xyz, 1.0);
    tex_coords = tex_uv;
}

