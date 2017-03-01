#version 330 core

layout(location = 0) in vec3 vert_xyz;
layout(location = 1) in vec3 color_rgb;

uniform mat4 mvp_matrix;

smooth out vec4 frag_color;

void main() {
    gl_Position = mvp_matrix * vec4(vert_xyz, 1.0);
    frag_color = vec4(color_rgb, 1.0);
}
