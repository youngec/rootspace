#version 330 core

uniform sampler2D active_tex;

smooth in vec2 frag_tex;
smooth in vec4 frag_color;

out vec4 frag_color_out;

void main() {
    // frag_color_out = texture(active_tex, frag_tex);
    frag_color_out = texture(active_tex, frag_tex) + frag_color;
}
