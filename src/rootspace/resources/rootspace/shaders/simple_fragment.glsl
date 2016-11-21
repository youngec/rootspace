#version 330 core

uniform sampler2D tex;

smooth in vec2 frag_tex_uv;

out vec4 fragColor;

void main() {
    fragColor = texture(tex, frag_tex_uv);
}
