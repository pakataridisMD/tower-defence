// Film finish over the whole splash: a heavy vignette and a little moving grain.
shader_type canvas_item;
#include "res://scripts/ui/splash/noise.gdshaderinc"

uniform float grain = 0.06;
uniform float darkness = 0.9;

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float v = smoothstep(0.45, 1.5, length(p * vec2(1.0, 0.8))) * darkness;
	float g = splash_hash(floor(UV * vec2(960.0, 540.0)) + fract(TIME * 7.3) * 31.0) - 0.5;
	float ga = abs(g) * grain * 2.0;
	float a = ga + v * (1.0 - ga);
	vec3 c = vec3(step(0.0, g)) * ga / max(a, 0.0001);
	COLOR = vec4(c, a);
}
