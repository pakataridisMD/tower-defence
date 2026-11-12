// A ring of bent air racing out from the blast. center is in screen UV, radius and width in
// screen heights.
shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform vec2 center = vec2(0.5, 0.5);
uniform float radius = 0.0;
uniform float width = 0.08;
uniform float strength = 0.0;
uniform float aspect = 1.7778;

void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 rel = (uv - center) * vec2(aspect, 1.0);
	float d = length(rel);
	float x = (d - radius) / width;
	float wave = exp(-x * x * 4.0) * sign(x) * -1.0 + exp(-x * x * 4.0);
	vec2 dir = rel / max(d, 0.0001);
	vec2 offset = dir / vec2(aspect, 1.0) * wave * strength * 0.035;
	vec3 col = texture(screen_tex, uv - offset).rgb;
	col += vec3(1.0, 0.7, 0.4) * exp(-x * x * 6.0) * strength * 0.06;
	COLOR = vec4(col, 1.0);
}
