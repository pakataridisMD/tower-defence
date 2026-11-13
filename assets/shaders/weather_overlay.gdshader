shader_type canvas_item;
render_mode unshaded;
// The weather over the whole battle view, drawn on top of the board (under the HUD) so it can always be
// seen, however far the camera is zoomed out: sheets of rain, falling snow, drifting ash with live
// embers, blowing dust, rolling fog, and a darkening or frosting of the edges of the view.
//
// Everything is snapped to a grid of big square pixels so it sits with the pixel art of the game.
// The world-space particles of WeatherArt still fall on the map underneath; this is the near layer.

// 0 clear, 1 rain, 2 storm, 3 snow, 4 blizzard, 5 ash, 6 dust (Weather.Kind).
uniform int kind = 0;
uniform float intensity : hint_range(0.0, 1.0) = 0.0;
// Wind: x across the screen (sign is the direction), y unused; length is how hard it blows.
uniform vec2 wind = vec2(1.0, 0.0);
// Lightning flash, 0 to 1.
uniform float flash = 0.0;
// Size of the rectangle in canvas pixels, and the size of one weather pixel.
uniform vec2 rect_size = vec2(1560.0, 984.0);
uniform float px = 3.0;
// Time in seconds (set by the script so captures can hold it still).
uniform float t = 0.0;
// Void ash is purple with violet embers instead of grey with orange ones.
uniform bool void_land = false;

float hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

float fbm(vec2 p) {
	float v = 0.0;
	float a = 0.5;
	for (int i = 0; i < 4; i++) {
		v += a * noise(p);
		p = p * 2.03 + vec2(17.1, 9.2);
		a *= 0.5;
	}
	return v;
}

// Premultiplied "over": lays a colour with alpha on top of what is there.
void over(inout vec4 acc, vec3 c, float a) {
	a = clamp(a, 0.0, 1.0);
	acc.rgb = c * a + acc.rgb * (1.0 - a);
	acc.a = a + acc.a * (1.0 - a);
}

// Straight streaks falling along a slant (rain, or with x and y swapped, blowing grit). Returns how
// lit this pixel is (0 to 1, brighter at the leading end).
float streaks(vec2 p, vec2 cell, float speed, float len, float slant, float seed, float density) {
	vec2 q = p;
	q.x -= floor(q.y * slant);
	q.y -= floor(t * speed);
	vec2 id = floor(q / cell);
	vec2 f = q - id * cell;
	if (hash(id + seed) > density) {
		return 0.0;
	}
	float x0 = floor(hash(id + seed + 3.1) * cell.x);
	float y0 = floor(hash(id + seed + 7.7) * max(1.0, cell.y - len));
	if (f.x != x0 || f.y < y0 || f.y > y0 + len) {
		return 0.0;
	}
	return 0.35 + 0.65 * (f.y - y0) / len;
}

// Flakes drifting down in cells, each wobbling side to side. `size` is 1 or 2 weather pixels.
float flakes(vec2 p, float cell, vec2 vel, float size, float seed, float density, float wobble) {
	vec2 q = p - floor(vel * t);
	vec2 id = floor(q / cell);
	vec2 f = q - id * cell;
	float r = hash(id + seed);
	if (r > density) {
		return 0.0;
	}
	vec2 at = floor(vec2(hash(id + seed + 1.7), hash(id + seed + 5.3)) * (cell - size));
	at.x += floor(sin(t * (1.1 + r) + r * 31.0) * wobble);
	vec2 d = f - at;
	if (d.x < 0.0 || d.y < 0.0 || d.x >= size || d.y >= size) {
		return 0.0;
	}
	// A 3x3 flake is a little cross; a 2x2 one has one dim corner, so neither reads as a block.
	if (size > 2.5) {
		bool corner = (d.x == 0.0 || d.x == 2.0) && (d.y == 0.0 || d.y == 2.0);
		return corner ? 0.0 : 1.0;
	}
	return (size > 1.5 && d.x + d.y > 1.5) ? 0.55 : 1.0;
}

// A flake with a dark pixel under it, so it shows on pale ground as well as on dark: lays both.
void flake_layer(inout vec4 acc, vec2 p, float cell, vec2 vel, float size, float seed, float density,
		float wobble, vec3 c, float a, vec3 shade, float shade_a) {
	float lit = flakes(p, cell, vel, size, seed, density, wobble);
	float under = flakes(p - vec2(1.0, 1.0), cell, vel, size, seed, density, wobble);
	over(acc, shade, under * (1.0 - lit) * shade_a);
	over(acc, c, lit * a);
}

void fragment() {
	vec2 canvas = UV * rect_size;
	vec2 p = floor(canvas / px);
	// Distance from the middle of the view, for the edges.
	vec2 q = UV - 0.5;
	float edge = smoothstep(0.28, 0.78, length(q * vec2(1.0, 1.28)));
	float k = intensity;
	float w = clamp(length(wind), 0.3, 3.0) * sign(wind.x == 0.0 ? 1.0 : wind.x);
	vec4 acc = vec4(0.0);

	if (kind == 1 || kind == 2) {
		bool storm = kind == 2;
		// Dark wet sky over everything, darker at the edges.
		over(acc, vec3(0.05, 0.07, 0.12), k * ((storm ? 0.2 : 0.1) + edge * (storm ? 0.5 : 0.32)));
		// Rolling mist low over the ground.
		float mist = fbm(p * 0.02 + vec2(t * 0.08 * w, t * 0.02));
		over(acc, vec3(0.62, 0.68, 0.78), k * smoothstep(0.5, 0.85, mist) * (storm ? 0.16 : 0.1));
		float slant = (storm ? 0.42 : 0.24) * w;
		float dense = storm ? 1.0 : 0.7;
		float far = streaks(p, vec2(9.0, 30.0), storm ? 150.0 : 120.0, 5.0, slant, 1.0, 0.75 * dense * k);
		float mid = streaks(p, vec2(13.0, 44.0), storm ? 210.0 : 170.0, 8.0, slant, 11.0, 0.7 * dense * k);
		float near = streaks(p, vec2(19.0, 64.0), storm ? 290.0 : 240.0, 12.0, slant, 23.0, 0.6 * dense * k);
		over(acc, vec3(0.62, 0.7, 0.84), far * 0.3 * k);
		over(acc, vec3(0.72, 0.79, 0.92), mid * 0.48 * k);
		over(acc, vec3(0.86, 0.91, 1.0), near * 0.7 * k);
	} else if (kind == 3 || kind == 4) {
		bool blizzard = kind == 4;
		// A heavy grey-blue overcast dims the land so the white snow stands out against it, frost creeps
		// in from the edges, and in a blizzard a white-out haze rolls over everything.
		over(acc, vec3(0.16, 0.2, 0.3), k * (blizzard ? 0.26 : 0.2));
		over(acc, vec3(0.86, 0.92, 1.0), k * edge * (blizzard ? 0.55 : 0.3));
		float fog = fbm(p * 0.018 + vec2(-t * 0.35 * w, t * 0.04));
		over(acc, vec3(0.9, 0.94, 1.0), k * (blizzard ? 0.08 + 0.3 * smoothstep(0.35, 0.8, fog) : 0.1 * smoothstep(0.5, 0.85, fog)));
		vec2 drift = vec2((blizzard ? 70.0 : 10.0) * w, blizzard ? 55.0 : 22.0);
		float d = blizzard ? 1.0 : 0.85;
		vec3 shade = vec3(0.2, 0.26, 0.38);
		flake_layer(acc, p, 10.0, drift * 0.6, 1.0, 3.0, d * k, 2.0, vec3(0.9, 0.94, 1.0), 0.75 * k, shade, 0.35 * k);
		flake_layer(acc, p, 15.0, drift * 0.85, 2.0, 13.0, d * 0.85 * k, 3.0, vec3(0.97, 0.98, 1.0), 0.95 * k, shade, 0.5 * k);
		flake_layer(acc, p, 26.0, drift * 1.2, 3.0, 29.0, d * 0.75 * k, 4.0, vec3(1.0), k, shade, 0.55 * k);
		if (blizzard) {
			// Snow driven flat by the wind.
			float gust = streaks(p.yx, vec2(16.0, 50.0), 260.0 * abs(w), 7.0, 0.0, 41.0, 0.5 * k);
			over(acc, vec3(1.0), gust * 0.6 * k);
		}
	} else if (kind == 5) {
		// Smoke-dark sky glowing from below, then ash flakes and live embers rising through them.
		vec3 smoke = void_land ? vec3(0.08, 0.03, 0.12) : vec3(0.1, 0.05, 0.03);
		vec3 glow = void_land ? vec3(0.7, 0.36, 1.0) : vec3(1.0, 0.45, 0.12);
		over(acc, smoke, k * (0.2 + edge * 0.5));
		float haze = fbm(p * 0.015 + vec2(t * 0.05 * w, -t * 0.03));
		over(acc, mix(smoke, glow, 0.3), k * smoothstep(0.45, 0.85, haze) * 0.25);
		// Firelight from below the bottom edge.
		over(acc, glow, k * smoothstep(0.5, 1.0, UV.y) * 0.16);
		vec3 ash = void_land ? vec3(0.78, 0.68, 0.92) : vec3(0.8, 0.77, 0.74);
		vec3 soot = void_land ? vec3(0.06, 0.02, 0.1) : vec3(0.08, 0.05, 0.04);
		flake_layer(acc, p, 10.0, vec2(8.0 * w, 9.0), 1.0, 5.0, 0.85 * k, 3.0, ash * 0.85, 0.75 * k, soot, 0.4 * k);
		flake_layer(acc, p, 16.0, vec2(12.0 * w, 14.0), 2.0, 17.0, 0.8 * k, 4.0, ash, 0.9 * k, soot, 0.5 * k);
		flake_layer(acc, p, 28.0, vec2(16.0 * w, 18.0), 3.0, 19.0, 0.6 * k, 5.0, ash, 0.9 * k, soot, 0.5 * k);
		float e = flakes(p, 17.0, vec2(6.0 * w, -18.0), 1.0, 37.0, 0.6 * k, 5.0);
		float e2 = flakes(p, 31.0, vec2(9.0 * w, -26.0), 2.0, 43.0, 0.5 * k, 6.0);
		float flicker = 0.65 + 0.35 * sin(t * 9.0 + hash(floor(p / 17.0)) * 40.0);
		over(acc, glow * 1.5, e * flicker * k);
		over(acc, mix(glow, vec3(1.0, 0.9, 0.6), 0.5) * 1.3, e2 * k);
	} else if (kind == 6) {
		// A brown-out: thick moving dust clouds, the far side of the view lost in haze, grit streaking past.
		vec3 sand = vec3(0.72, 0.52, 0.3);
		over(acc, vec3(0.3, 0.18, 0.08), k * edge * 0.5);
		float cloud = fbm(p * vec2(0.012, 0.03) + vec2(-t * 0.6 * w, t * 0.03));
		float cloud2 = fbm(p * vec2(0.03, 0.06) + vec2(-t * 1.4 * w, 3.0));
		over(acc, sand, k * (0.14 + 0.36 * smoothstep(0.35, 0.8, cloud)));
		over(acc, sand * 1.15, k * 0.18 * smoothstep(0.55, 0.85, cloud2));
		float grit = streaks(p.yx * vec2(1.0, sign(w)), vec2(9.0, 60.0), 330.0 * abs(w), 6.0, 0.06, 51.0, 0.55 * k);
		float grit2 = streaks(p.yx * vec2(1.0, sign(w)), vec2(13.0, 80.0), 420.0 * abs(w), 10.0, 0.04, 61.0, 0.4 * k);
		over(acc, vec3(0.86, 0.7, 0.48), grit * 0.6 * k);
		over(acc, vec3(0.95, 0.82, 0.6), grit2 * 0.75 * k);
	}

	// Lightning lights up the whole view for an instant.
	over(acc, vec3(0.85, 0.9, 1.0), flash * 0.45);
	COLOR = vec4(acc.a > 0.0001 ? acc.rgb / acc.a : vec3(0.0), acc.a);
}
