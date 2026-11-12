// The studio name, forged: it burns in from the middle out with a glowing edge, white hot at first,
// cooling through orange to dark gold-bronze iron, with cracks that glow while it is hot.
// text_size is the label's size in pixels.
shader_type canvas_item;
#include "res://scripts/ui/splash/noise.gdshaderinc"

uniform float heat = 1.0;
uniform float reveal = 0.0;
uniform vec2 text_size = vec2(1000.0, 300.0);

varying vec2 local;

void vertex() {
	local = VERTEX;
}

vec3 hot(float t) {
	vec3 c = mix(vec3(0.5, 0.08, 0.02), vec3(1.0, 0.42, 0.08), smoothstep(0.0, 0.4, t));
	c = mix(c, vec3(1.0, 0.82, 0.45), smoothstep(0.4, 0.75, t));
	return mix(c, vec3(1.0, 0.98, 0.92), smoothstep(0.75, 1.0, t));
}

void fragment() {
	vec2 uv = local / text_size;
	float a = COLOR.a;
	float n = splash_fbm(uv * vec2(9.0, 3.0) + 2.0);
	// burn in from the centre outward
	float from_mid = abs(uv.x - 0.5) * 2.0;
	float front = reveal * 1.35 - from_mid - (n - 0.5) * 0.35;
	float shown = smoothstep(0.0, 0.04, front);
	float edge = smoothstep(0.12, 0.0, front) * shown;
	// cooled metal: bronze-gold, light at the top, dark at the foot, hammered
	float g = clamp(uv.y, 0.0, 1.0);
	vec3 cold = mix(vec3(0.93, 0.74, 0.38), vec3(0.36, 0.2, 0.09), smoothstep(0.15, 0.95, g));
	cold *= 0.8 + 0.35 * splash_fbm(uv * vec2(40.0, 12.0));
	float t = clamp(heat * (0.85 + 0.3 * n), 0.0, 1.0);
	vec3 col = mix(cold, hot(t), smoothstep(0.0, 0.55, heat));
	// glowing cracks
	float crack = smoothstep(0.035, 0.0, abs(splash_fbm(uv * vec2(14.0, 5.0) + 11.0) - 0.5));
	col += hot(0.6) * crack * smoothstep(0.05, 0.6, heat) * 0.9;
	col += hot(1.0) * edge * 2.0;
	// the outline stays dark ink, tinted by heat
	vec3 base = COLOR.rgb;
	float is_outline = step(base.r + base.g + base.b, 0.6);
	col = mix(col, base + hot(0.4) * heat * 0.5, is_outline);
	COLOR = vec4(col, a * shown);
}
