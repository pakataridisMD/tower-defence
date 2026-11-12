shader_type canvas_item;
render_mode unshaded;
// Post-processing over the board only (the HUD sits on a higher layer): a soft bloom around bright and
// glowing pixels, a gentle film grade (cool shadows, warm lights, a touch more contrast and colour) and a
// vignette that pulls the eye to the middle of the view.

uniform sampler2D screen_texture : hint_screen_texture, filter_linear;
uniform float bloom_strength = 0.38;
uniform float bloom_threshold = 0.7;
uniform float bloom_radius = 7.0;
uniform float contrast = 1.07;
uniform float saturation = 1.1;
uniform vec3 shadow_tint = vec3(0.92, 0.97, 1.08);
uniform vec3 light_tint = vec3(1.05, 1.0, 0.93);
uniform float vignette = 0.32;

vec3 bright(vec2 uv) {
	vec3 c = texture(screen_texture, uv).rgb;
	float l = max(c.r, max(c.g, c.b));
	return c * smoothstep(bloom_threshold, 1.0, l);
}

void fragment() {
	vec2 px = SCREEN_PIXEL_SIZE;
	vec3 base = texture(screen_texture, SCREEN_UV).rgb;
	// Bloom: two rings of taps, the outer one weaker.
	vec3 glow = vec3(0.0);
	for (int i = 0; i < 8; i++) {
		float a = float(i) * 0.785398 + 0.39;
		vec2 d = vec2(cos(a), sin(a));
		glow += bright(SCREEN_UV + d * px * bloom_radius) * 0.09;
		glow += bright(SCREEN_UV + d * px * bloom_radius * 2.3) * 0.045;
	}
	vec3 c = base + glow * bloom_strength;
	// Grade.
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(vec3(l), c, saturation);
	c = (c - 0.5) * contrast + 0.5;
	c *= mix(shadow_tint, light_tint, smoothstep(0.15, 0.7, l));
	// Vignette over this rectangle.
	vec2 q = UV - 0.5;
	float v = 1.0 - vignette * smoothstep(0.25, 0.75, length(q * vec2(1.0, 1.25)));
	COLOR = vec4(clamp(c * v, 0.0, 1.0), 1.0);
}
