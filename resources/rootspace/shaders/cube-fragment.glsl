#version 330 core

smooth in vec3 frag_color;

out vec4 frag_color_out;

void main() {
    frag_color_out = vec4(frag_color, 1.0);
}
