// The iron bomb: a lit sphere of pitted black iron with a riveted band and a neck for the fuse.
// It is lit by a cold rim from behind and by the burning fuse (light_pos, in UV space).
shader_type canvas_item;
#include "res://scripts/ui/splash/noise.gdshaderinc"

uniform vec2 light_pos = vec2(0.6, 0.0);
uniform float light_power = 0.0;
uniform float heat = 0.0; // glows from inside just before it bursts

const float R = 0.74;
const vec2 C = vec2(0.0, 0.16);

vec3 shade(vec3 n, vec3 albedo, float rough, vec3 frag, float metal) {
	vec3 v = vec3(0.0, 0.0, 1.0);
	// cold moonlight from the upper left
	vec3 l1 = normalize(vec3(-0.6, 0.7, 0.55));
	vec3 col = albedo * (0.05 + 0.35 * max(dot(n, l1), 0.0)) * vec3(0.55, 0.62, 0.8);
	vec3 h1 = normalize(l1 + v);
	col += vec3(0.35, 0.42, 0.6) * pow(max(dot(n, h1), 0.0), mix(60.0, 8.0, rough)) * metal;
	// warm point light from the fuse
	vec3 lp = vec3(light_pos * 2.0 - 1.0, 0.55);
	lp.y = -lp.y;
	vec3 l2 = normalize(lp - frag);
	float fall = light_power / (1.0 + 2.5 * dot(lp - frag, lp - frag));
	col += albedo * max(dot(n, l2), 0.0) * vec3(1.0, 0.55, 0.2) * 2.2 * fall;
	vec3 h2 = normalize(l2 + v);
	col += vec3(1.0, 0.6, 0.25) * pow(max(dot(n, h2), 0.0), mix(90.0, 10.0, rough)) * fall * 1.6 * metal;
	// rim from behind
	float rim = pow(1.0 - max(n.z, 0.0), 3.0);
	col += vec3(0.25, 0.3, 0.42) * rim * 0.5;
	return col;
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	vec2 c = p - C;
	float d = length(c);
	float body = 1.0 - smoothstep(R - 0.008, R + 0.004, d);
	// the neck: a short iron collar on top
	float neck_w = 0.16;
	float neck_top = C.y - R - 0.12;
	float neck = smoothstep(neck_w, neck_w - 0.01, abs(p.x)) * smoothstep(neck_top, neck_top + 0.01, p.y)
			* (1.0 - step(C.y - R + 0.1, p.y));
	vec3 col = vec3(0.0);
	float alpha = 0.0;
	if (body > 0.0) {
		vec2 q = c / R;
		float z = sqrt(max(1.0 - dot(q, q), 0.0));
		vec3 n = normalize(vec3(q.x, -q.y, z));
		vec3 frag = vec3(c.x, -c.y, z * R);
		// pitted, hammered iron
		vec2 sp = vec2(atan(n.x, n.z), n.y) * 3.0;
		float pits = splash_fbm(sp * 4.0);
		float rust = smoothstep(0.55, 0.8, splash_fbm(sp * 2.0 + 7.0));
		vec3 albedo = mix(vec3(0.11, 0.105, 0.115), vec3(0.2, 0.09, 0.05), rust * 0.6) * (0.75 + 0.5 * pits);
		float rough = 0.35 + 0.4 * rust;
		// a raised band round the middle, with rivets
		float lat = n.y + 0.12;
		float band = smoothstep(0.075, 0.065, abs(lat));
		if (band > 0.0) {
			n = normalize(n + vec3(0.0, -sign(lat) * smoothstep(0.04, 0.075, abs(lat)) * 0.6, 0.0));
			albedo = vec3(0.16, 0.15, 0.16) * (0.8 + 0.4 * pits);
			rough = 0.25;
			float lon = atan(n.x, n.z) * 6.0;
			float rivet = smoothstep(0.035, 0.02, length(vec2(fract(lon / 3.14159 * 2.0) - 0.5, lat * 6.0) * vec2(0.5, 1.0)));
			albedo += vec3(0.12) * rivet;
		}
		// as the fuse reaches the powder, fissures split the iron and glow from inside
		float vein = abs(splash_fbm(sp * 2.6 + 3.0) - 0.5);
		float spread = splash_fbm(sp * 1.3 - 5.0);
		float open = smoothstep(spread - 0.1, spread + 0.25, heat * 1.15);
		float crack = smoothstep(0.03 * open, 0.0, vein) * open;
		col = shade(n, albedo, rough, frag, 1.0);
		vec3 molten = mix(vec3(1.0, 0.3, 0.05), vec3(1.0, 0.85, 0.5), smoothstep(0.004, 0.0, vein));
		col = mix(col, molten * 1.6, crack);
		col += vec3(0.9, 0.25, 0.04) * smoothstep(0.08, 0.0, vein) * open * 0.35;
		col += vec3(1.0, 0.4, 0.1) * pow(heat, 4.0) * 0.5 * (0.6 + 0.4 * pits);
		alpha = body;
	}
	if (neck > 0.0 && body < 1.0) {
		float x = p.x / neck_w;
		vec3 n = normalize(vec3(x, 0.15, sqrt(max(1.0 - x * x, 0.0))));
		vec3 frag = vec3(p.x, -p.y, 0.2);
		float lip = step(p.y, neck_top + 0.05);
		vec3 albedo = vec3(0.13, 0.12, 0.13) * (1.0 + 0.4 * lip);
		vec3 nc = shade(n, albedo, 0.3, frag, 1.0);
		col = mix(nc, col, body);
		alpha = max(alpha, neck);
	}
	COLOR = vec4(col, alpha);
}
