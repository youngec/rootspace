#version 330 core

uniform sampler2D active_tex;

smooth in vec2 frag_tex_uv;
smooth in vec3 frag_color_rgb;

out vec4 fragColor;

void main() {
    // fragColor = texture(active_tex, frag_tex_uv);
    fragColor = texture(active_tex, frag_tex_uv) + vec4(frag_color_rgb, 1.0);
}
