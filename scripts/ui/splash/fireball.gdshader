// The blast: a turbulent ball of fire that bursts out, cools from white through orange and red,
// and breaks up into rags. Drawn additively over the smoke. progress runs 0 to 1 over the blast.
shader_type canvas_item;
render_mode blend_add;
#include "res://scripts/ui/splash/noise.gdshaderinc"

uniform float progress = 0.0;
uniform float seed = 3.0;

vec3 ramp(float t) {
	t = clamp(t, 0.0, 1.0);
	vec3 c = mix(vec3(0.0), vec3(0.45, 0.05, 0.02), smoothstep(0.0, 0.25, t));
	c = mix(c, vec3(1.0, 0.32, 0.05), smoothstep(0.2, 0.5, t));
	c = mix(c, vec3(1.0, 0.72, 0.28), smoothstep(0.45, 0.75, t));
	c = mix(c, vec3(1.0, 0.97, 0.88), smoothstep(0.78, 1.0, t));
	return c;
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float d = length(p);
	vec2 dir = p / max(d, 0.0001);
	float ang = atan(p.y, p.x);
	float grow = 1.0 - pow(1.0 - clamp(progress * 2.4, 0.0, 1.0), 3.0);
	float radius = mix(0.05, 0.62, grow) + progress * 0.14;
	// lobes round the rim, so the ball is never a clean circle
	vec2 rim = vec2(cos(ang), sin(ang)) * 1.6 + vec2(seed, progress * 0.6);
	float lobes = splash_fbm(rim * 1.4) * 1.25 + splash_fbm(rim * 4.0) * 0.35;
	// billows rolling outward inside
	vec2 q = p * 3.2 - dir * progress * 3.5 + vec2(seed * 1.7);
	vec2 warp = vec2(splash_fbm(q * 1.3 + 4.0), splash_fbm(q * 1.3 - 2.0));
	float n = splash_fbm(q + warp * 1.8);
	float edge = radius * (0.5 + 0.75 * lobes) * (0.9 + 0.25 * n);
	float soft = 0.08 + 0.25 * edge;
	float inside = 1.0 - smoothstep(edge - soft, edge + soft * 0.3, d);
	float core = 1.0 - smoothstep(0.0, max(edge * 0.95, 0.001), d);
	float cool = smoothstep(0.04, 0.85, progress);
	float temp = (core * 0.8 + n * 0.55) * (1.0 - cool * 0.8) - smoothstep(0.5, 1.0, progress) * 0.35;
	// holes open as the fire tears apart into rags
	float holes = smoothstep(0.25 + progress * 0.6, 0.5 + progress * 0.45, n + core * 0.25);
	float a = inside * mix(1.0, holes, smoothstep(0.15, 0.65, progress)) * (1.0 - smoothstep(0.32, 0.72, progress));
	COLOR = vec4(ramp(temp) * a * 1.5, 1.0);
}
