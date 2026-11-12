shader_type canvas_item;
render_mode unshaded;
uniform float t = 0.0;
uniform float flash = 0.0;
uniform vec2 glow_pos = vec2(0.47, 0.25);
uniform vec4 glow_col : source_color = vec4(0.30, 0.16, 0.55, 1.0);
uniform vec4 top : source_color = vec4(0.008, 0.008, 0.025, 1.0);
uniform vec4 mid : source_color = vec4(0.035, 0.04, 0.09, 1.0);
uniform vec4 low : source_color = vec4(0.13, 0.12, 0.22, 1.0);
float h(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
void fragment() {
	float y = UV.y;
	vec3 c = mix(top.rgb, mid.rgb, smoothstep(0.0, 0.55, y));
	c = mix(c, low.rgb, smoothstep(0.5, 1.0, y));
	// glow around the rift (upper right)
	vec2 r = (UV - glow_pos) * vec2(1.4, 3.0);
	c += glow_col.rgb * exp(-dot(r, r) * 1.8) * 0.55;
	vec2 g = floor(UV * vec2(800.0, 500.0));
	float s = h(g);
	float tw = 0.6 + 0.4 * sin(t * (2.0 + 6.0 * h(g + 3.1)) + 30.0 * h(g + 7.7));
	float star = step(0.9965, s) * tw * (1.0 - smoothstep(0.45, 0.85, y));
	c += vec3(0.9, 0.85, 1.0) * star;
	c += vec3(0.45, 0.42, 0.75) * flash;
	COLOR = vec4(c, 1.0);
}
