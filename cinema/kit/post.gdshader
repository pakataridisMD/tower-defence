shader_type canvas_item;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform float t = 0.0;
uniform float impact = 0.0;   // 1 = inverted impact frame
uniform float aberr = 0.0;
uniform float fade = 0.0;     // 1 = black
float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 dir = (uv - 0.5);
	float ab = aberr * 0.006;
	vec3 c;
	c.r = texture(screen_tex, uv + dir * ab).r;
	c.g = texture(screen_tex, uv).g;
	c.b = texture(screen_tex, uv - dir * ab).b;
	// grade: lift shadows to violet, warm highlights
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(c, c * vec3(1.05, 0.98, 1.08) + vec3(0.012, 0.0, 0.025), 0.8);
	c = pow(c, vec3(0.95));
	// vignette
	float v = smoothstep(0.95, 0.35, length(dir * vec2(1.0, 1.25)));
	c *= mix(0.55, 1.0, v);
	// grain
	float g = h(uv * 1000.0 + fract(t * 23.17)) - 0.5;
	c += g * 0.045;
	// impact frame: hard two-tone inversion
	if (impact > 0.5) {
		float k = step(0.42, l);
		c = mix(vec3(0.96, 0.92, 1.0), vec3(0.08, 0.0, 0.14), k);
	}
	c *= (1.0 - fade);
	COLOR = vec4(c, 1.0);
}
