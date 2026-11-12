shader_type canvas_item;
render_mode unshaded, blend_add;
uniform float t = 0.0;
uniform float speed = 6.0;
uniform float density = 0.25;
uniform vec4 tint : source_color = vec4(0.5, 0.4, 0.8, 1.0);
uniform float scale = 3.0;
float h(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f*f*(3.0-2.0*f);
	return mix(mix(h(i), h(i+vec2(1,0)), f.x), mix(h(i+vec2(0,1)), h(i+vec2(1,1)), f.x), f.y); }
float fbm(vec2 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 5; i++){ s += a * n(p); p *= 2.03; a *= 0.5; } return s; }
void fragment() {
	vec2 p = UV * vec2(scale * 2.5, scale);
	p.x += t * speed * 0.01;
	float f = fbm(p + vec2(0.0, t * 0.02));
	float band = smoothstep(0.0, 0.45, UV.y) * (1.0 - smoothstep(0.6, 1.0, UV.y));
	float a = smoothstep(0.35, 0.85, f) * band * density;
	COLOR = vec4(tint.rgb * a, a);
}
