#version 330 core

layout(location = 0) in vec3 vert_xyz;
layout(location = 1) in vec2 tex_uv;
layout(location = 2) in vec4 color_rgb;

uniform mat4 mvp_matrix;

smooth out vec2 frag_tex;
smooth out vec4 frag_color;

void main() {
    gl_Position = mvp_matrix * vec4(vert_xyz, 1.0);
    frag_color = color_rgb;
    frag_tex = tex_uv;
}
