#version 330 core

uniform sampler2D active_tex;

smooth in vec2 frag_tex_uv;

out vec4 fragColor;

void main() {
    fragColor = texture(active_tex, frag_tex_uv);
}
