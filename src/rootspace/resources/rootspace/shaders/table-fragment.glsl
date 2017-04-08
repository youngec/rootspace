#version 330 core

uniform sampler2D active_tex;

smooth in vec2 tex_coords;

out vec4 frag_color_out;

void main() {
    frag_color_out = texture(active_tex, tex_coords);
}

