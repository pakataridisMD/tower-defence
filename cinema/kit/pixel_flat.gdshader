shader_type canvas_item;
// Smooth pixel-art sampling for painted plates without a normal map (lights still add, flat-on).
void fragment() {
	vec2 sz = 1.0 / TEXTURE_PIXEL_SIZE;
	vec2 uv = UV * sz;
	vec2 seam = floor(uv + 0.5);
	vec2 d = fwidth(uv);
	uv = seam + clamp((uv - seam) / max(d, vec2(1e-4)), -0.5, 0.5);
	COLOR = texture(TEXTURE, uv / sz) * COLOR;
}
