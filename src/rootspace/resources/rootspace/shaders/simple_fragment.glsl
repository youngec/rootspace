#version 330 core

smooth in vec4 frag_color;

out vec4 frag_color_out;

void main() {
    frag_color_out = frag_color;
}
