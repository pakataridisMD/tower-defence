shader_type canvas_item;
// Smooth pixel-art sampling: crisp texels at any (non-integer) scale, no shimmer while the camera moves.
void fragment() {
	vec2 sz = 1.0 / TEXTURE_PIXEL_SIZE;
	vec2 uv = UV * sz;
	vec2 seam = floor(uv + 0.5);
	vec2 d = fwidth(uv);
	uv = seam + clamp((uv - seam) / max(d, vec2(1e-4)), -0.5, 0.5);
	uv /= sz;
	COLOR = texture(TEXTURE, uv) * COLOR;
	NORMAL_MAP = texture(NORMAL_TEXTURE, uv).rgb;
}
