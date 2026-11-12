"""Turns the road sketches in gen_campaign.py into the big, winding maps the game plays on.

The sketches are drawn on the old 24 x 15 grid as straight roads that turn at right angles. Each
map is grown to GRID (about three times the area), its corners are nudged, every long straight is
bent into curves, and most maps get spawn holes: pits in the open ground where part of the horde
climbs out and joins the road partway along. The result for each lane is

  waypoints  the control points, in cells (the first and last are still the road's two ends)
  curve      the road's centre line, densely sampled, in cells (floats)

Both go into the map's .tres. The game walks enemies along `curve` and blocks the cells it passes
over; tools/art/gen_game_art.py paints the road from the same points, so the two always agree.

Everything here is deterministic: the same sketch and stage id always give the same map.
"""
from __future__ import annotations

import contextlib
import math
import random
import zlib

SKETCH = (24, 15)
GRID = (42, 26)

# How far a road may be from another road (centre to centre, in cells) after it has been bent, so
# there is always room to build between two roads.
CLEARANCE = 3.2
# Biggest sideways bend of a curve, in cells.
MAX_BEND = 6.0
# Largest radius a corner is rounded to, in cells.
CORNER_RADIUS = 4.5
# A road end inside the grid is a spawn hole; holes keep this far from any other road.
HOLE_CLEARANCE = 4.5


def _seed(*parts) -> int:
    return zlib.crc32("|".join(str(p) for p in parts).encode())


# ------------------------------------------------------------------------------------ geometry
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _mul(a, k):
    return (a[0] * k, a[1] * k)


def _len(a):
    return math.hypot(a[0], a[1])


def _norm(a):
    d = _len(a) or 1.0
    return (a[0] / d, a[1] / d)


def _dist_point_segment(p, a, b):
    v = _sub(b, a)
    ll = v[0] * v[0] + v[1] * v[1]
    if ll < 1e-12:
        return _len(_sub(p, a))
    t = max(0.0, min(1.0, ((p[0] - a[0]) * v[0] + (p[1] - a[1]) * v[1]) / ll))
    return _len(_sub(p, _add(a, _mul(v, t))))


def _segments(lanes):
    """Every distinct segment of every lane, as (a, b) with a <= b so shared ones appear once."""
    seen = {}
    for lane in lanes:
        for a, b in zip(lane[:-1], lane[1:]):
            key = (min(a, b), max(a, b))
            seen[key] = True
    return list(seen.keys())


def _inside(p, grid, margin=0.0):
    return margin <= p[0] <= grid[0] - 1 - margin and margin <= p[1] <= grid[1] - 1 - margin


# ------------------------------------------------------------------------------------ scaling
# Inside the board, a sketch is stretched so its roads reach this close to the edges.
MARGIN = 3
# Columns kept free of road at the right edge of the board, for the final assault's citadel. Set it
# with reserve_right() around the calls that build and scale that one map.
_RIGHT_RESERVE = 0


@contextlib.contextmanager
def reserve_right(columns):
    """Builds and scales maps whose roads keep `columns` cells at the right edge free."""
    global _RIGHT_RESERVE
    old = _RIGHT_RESERVE
    _RIGHT_RESERVE = columns
    try:
        yield
    finally:
        _RIGHT_RESERVE = old


def _scale_axis(v, src, dst, span=None, reserve=0):
    if v < 0:
        return -1
    if v >= src:
        return dst
    plain = (v + 0.5) * dst / src - 0.5
    if span is not None:
        lo, hi = span
        plain_lo, plain_hi = (lo + 0.5) * dst / src - 0.5, (hi + 0.5) * dst / src - 0.5
        new_lo, new_hi = min(MARGIN, plain_lo), max(dst - 1 - MARGIN - reserve, plain_hi if not reserve else 0)
        if hi > lo:
            plain = new_lo + (plain - plain_lo) * (new_hi - new_lo) / (plain_hi - plain_lo)
    return int(round(plain))


def _spans(lanes):
    """The range of inside coordinates a sketch uses, per axis."""
    spans = []
    for axis, size in ((0, SKETCH[0]), (1, SKETCH[1])):
        values = [p[axis] for lane in lanes for p in lane if 0 <= p[axis] < size]
        spans.append((min(values), max(values)) if values else None)
    return spans


def scale_point(p, grid=GRID, spans=(None, None)):
    return (_scale_axis(p[0], SKETCH[0], grid[0], spans[0], _RIGHT_RESERVE),
            _scale_axis(p[1], SKETCH[1], grid[1], spans[1]))


def scale_lanes(lanes, grid=GRID, spans=None):
    spans = spans or _spans(lanes)
    return [[scale_point(p, grid, spans) for p in lane] for lane in lanes]


def _jitter(lanes, grid, seed, fixed):
    """Nudges every inside turning point by up to a cell, the same way in every lane it appears in."""
    moved = {}
    for lane in lanes:
        for p in lane[1:-1]:
            if p in moved or p in fixed or not _inside(p, grid, 2):
                continue
            rng = random.Random(_seed(seed, "jitter", p))
            moved[p] = (p[0] + rng.choice((-1, 0, 0, 1)), p[1] + rng.choice((-1, 0, 0, 1)))
    return [[moved.get(p, p) for p in lane] for lane in lanes]


def _on_segment(p, a, b):
    if p == a or p == b:
        return False
    if (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) != 0:
        return False
    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def merge_overlaps(lanes):
    """Where a lane joins another partway along a straight, gives the other lane a turning point
    there too, so the stretch they share is one segment and bends as one road."""
    changed = True
    while changed:
        changed = False
        points = {p for lane in lanes for p in lane}
        for p in points:
            for lane in lanes:
                for a, b in zip(lane[:-1], lane[1:]):
                    if _on_segment(p, a, b):
                        lanes = _split(lanes, a, b, p)
                        changed = True
                        break
                if changed:
                    break
            if changed:
                break
    return lanes


# ------------------------------------------------------------------------------------ spawn holes
def _length(lane):
    return sum(_len(_sub(b, a)) for a, b in zip(lane[:-1], lane[1:]))


def _split(lanes, a, b, j):
    """Puts j between a and b in every lane that walks from a to b, so lanes keep sharing the road."""
    out = []
    for lane in lanes:
        new = [lane[0]]
        for p, q in zip(lane[:-1], lane[1:]):
            if (p, q) == (a, b):
                new.append(j)
            elif (p, q) == (b, a):
                new.append(j)
            new.append(q)
        out.append(new)
    return out


def add_holes(lanes, count, grid, seed, spans=((0.15, 0.4), (0.35, 0.55))):
    """Adds `count` spawn holes, each a short road from a pit in the open ground to a point partway
    along the main road (lane 0). Returns the lanes with each hole's lane appended."""
    rng = random.Random(_seed(seed, "holes"))
    holes = []
    for h in range(count):
        lo, hi = spans[min(h, len(spans) - 1)]
        main = lanes[0]
        total = _length(main)
        segs = _segments(lanes)
        options = []
        walked = 0.0
        for a, b in zip(main[:-1], main[1:]):
            seg = _len(_sub(b, a))
            d = _norm(_sub(b, a))
            for s in range(3, int(seg) - 2, 2):
                if not lo <= (walked + s) / total <= hi:
                    continue
                j = (round(a[0] + d[0] * s), round(a[1] + d[1] * s))
                if not _inside(j, grid, 1) or _dist_point_segment(j, a, b) > 0.75:
                    continue
                for hx in range(3, grid[0] - 3, 2):
                    for hy in range(3, grid[1] - 3, 2):
                        hole = (hx, hy)
                        reach = _len(_sub(hole, j))
                        if not 6.0 <= reach <= 13.0:
                            continue
                        way = _norm(_sub(j, hole))
                        # Meets the road across it, not along it.
                        if abs(way[0] * d[0] + way[1] * d[1]) > 0.72:
                            continue
                        near = min(_dist_point_segment(hole, p, q) for p, q in segs)
                        if near < HOLE_CLEARANCE or any(_len(_sub(hole, o)) < 10 for o in holes):
                            continue
                        clear = True
                        t = 0.0
                        while clear and t < reach - 3.0:
                            probe = _add(hole, _mul(way, t))
                            clear = all(_dist_point_segment(probe, p, q) >= CLEARANCE + 0.3 for p, q in segs)
                            t += 1.0
                        if clear:
                            options.append((near + rng.random() * 2.0, a, b, j, hole))
            walked += seg
        if not options:
            continue
        options.sort(key=lambda o: -o[0])
        # One of the roomiest few, so maps differ.
        _, a, b, j, hole = options[rng.randrange(min(8, len(options)))]
        lanes = _split(lanes, a, b, j)
        main = lanes[0]
        k = main.index(j)
        lanes = lanes + [[hole] + main[k:]]
        holes.append(hole)
    return lanes


# ------------------------------------------------------------------------------------ curves
def _side_room(base, n, own, segs, grid, limit=12.0):
    """How far a point can move along n before it comes within CLEARANCE of another road (or nearer
    than it already is, for the roads that meet its own at a corner) or within a cell and a half
    of the edge of the board."""
    others = [(p, q, min(CLEARANCE + 0.6, _dist_point_segment(base, p, q) * 0.9)) for p, q in segs if (p, q) != own]
    t = 0.0
    while t < limit:
        probe = _add(base, _mul(n, t + 0.5))
        if not _inside(probe, grid, 1.5):
            return t
        for p, q, keep in others:
            if _dist_point_segment(probe, p, q) < keep:
                return t
        t += 0.5
    return t


def _bend(lanes, grid, seed, scale, calm, flip=frozenset()):
    """Adds sideways control points along each long straight, so it winds into the free ground
    beside it. Shared straights bend the same way in every lane. `scale` shrinks the bends of the
    segments in it (retries); `calm` holds points no bend may come near (buildings of the base)."""
    segs = _segments(lanes)
    plans = {}
    for key in segs:
        a, b = key
        seg = _len(_sub(b, a))
        rng = random.Random(_seed(seed, "bend", key))
        k = scale.get(key, 1.0)
        if seg < 5 or k <= 0.05 or any(_dist_point_segment(c, a, b) < 3.0 for c in calm):
            plans[key] = []
            continue
        d = _norm(_sub(b, a))
        n = (-d[1], d[0])
        mid = _add(a, _mul(d, seg * 0.5))
        plus, minus = _side_room(mid, n, key, segs, grid), _side_room(mid, _mul(n, -1), key, segs, grid)
        roomy = 1 if plus >= minus else -1
        turn = -1 if key in flip else 1
        style = rng.random()
        if seg >= 12 and max(plus, minus) >= 5 and style < 0.3:
            fractions, signs, taper = [0.22, 0.78], [roomy, roomy], 1.1  # a wide detour out to one side
        elif seg >= 7 and (style < 0.55 or min(plus, minus) < 2.5):
            fractions, signs, taper = [0.5], [roomy], 1.0  # one long bow
        else:
            count = max(2, round(seg / rng.uniform(4.5, 7.0)))  # a snake, swinging both ways
            first = rng.choice((-1, 1))
            fractions = [(i + 0.5) / count for i in range(count)]
            signs = [first * (1 if i % 2 == 0 else -1) for i in range(count)]
            taper = 0.7
        points = []
        for f, sign in zip(fractions, signs):
            base = _add(a, _mul(d, seg * f))
            sign *= turn
            room = _side_room(base, _mul(n, sign), key, segs, grid)
            ends = min(seg * f, seg * (1 - f))
            amp = min(MAX_BEND, room * 0.85, ends * taper) * rng.uniform(0.75, 1.0) * k
            if amp >= 0.8:
                off = _add(base, _mul(n, sign * amp))
                points.append((round(off[0], 2), round(off[1], 2)))
        plans[key] = points
    out = []
    for lane in lanes:
        new = [lane[0]]
        for p, q in zip(lane[:-1], lane[1:]):
            key = (min(p, q), max(p, q))
            mids = plans.get(key, [])
            new += mids if key[0] == p else list(reversed(mids))
            new.append(q)
        out.append(new)
    return out


def round_corners(points, radius=CORNER_RADIUS):
    """Rounds every corner of a polyline with a quadratic curve and returns the sampled line."""
    out = [points[0]]
    for i in range(1, len(points) - 1):
        a, v, b = points[i - 1], points[i], points[i + 1]
        la, lb = _len(_sub(a, v)), _len(_sub(b, v))
        if la < 1e-6 or lb < 1e-6:
            continue
        da, db = _norm(_sub(a, v)), _norm(_sub(b, v))
        turn = math.pi - math.acos(max(-1.0, min(1.0, da[0] * db[0] + da[1] * db[1])))
        if turn < 0.02:
            out.append(v)
            continue
        r = min(radius, la * 0.5, lb * 0.5)
        p0, p2 = _add(v, _mul(da, r)), _add(v, _mul(db, r))
        steps = max(3, int(math.ceil(turn / (math.pi / 14) * max(1.0, r / 2.0))))
        for s in range(steps + 1):
            t = s / steps
            u = 1 - t
            out.append((u * u * p0[0] + 2 * u * t * v[0] + t * t * p2[0],
                        u * u * p0[1] + 2 * u * t * v[1] + t * t * p2[1]))
    out.append(points[-1])
    clean = [out[0]]
    for p in out[1:]:
        if _len(_sub(p, clean[-1])) > 0.05:
            clean.append(p)
    if clean[-1] != points[-1]:
        clean[-1] = points[-1]
    return [(round(x, 3), round(y, 3)) for x, y in clean]


def _resample(curve, step=0.5):
    """Points every `step` cells along a curve, each with how far along the lane it is."""
    out = [(curve[0], 0.0)]
    walked = 0.0
    carry = 0.0
    for a, b in zip(curve[:-1], curve[1:]):
        seg = _len(_sub(b, a))
        t = step - carry
        while t <= seg:
            out.append((_add(a, _mul(_sub(b, a), t / seg)), walked + t))
            t += step
        carry = seg - (t - step)
        walked += seg
    return out


def _too_close(curves, bases, grid, end_keep=2.0):
    """Places where a bent road comes nearer than CLEARANCE to another stretch of road that was not
    already that near before bending (roads that join or cross on purpose are allowed). Returns the
    base segments involved, and whether any road leaves the board."""
    segs_by_lane = []
    for b in bases:
        walked, segs = 0.0, []
        for p, q in zip(b[:-1], b[1:]):
            segs.append((p, q, walked))
            walked += _len(_sub(q, p))
        segs_by_lane.append(segs)

    def project(lane, p):
        """The nearest point on the lane's unbent road, its segment, and how far along it is."""
        best = None
        for a, b, start in segs_by_lane[lane]:
            c = _closest_on((a, b), p)
            dist = _len(_sub(c, p))
            if best is None or dist < best[0]:
                best = (dist, c, (a, b), start + _len(_sub(c, a)))
        return best[1], best[2], best[3]

    cache = {}

    def on_lane(lane, q):
        """How far along a lane's curve q lies, or None when q is not on that lane's road."""
        key = (lane, q)
        if key not in cache:
            cache[key] = None
            walked = 0.0
            curve = curves[lane]
            for a, b in zip(curve[:-1], curve[1:]):
                if _dist_point_segment(q, a, b) < 0.05:
                    cache[key] = walked + _len(_sub(_closest_on((a, b), q), a))
                    break
                walked += _len(_sub(b, a))
        return cache[key]

    samples = []
    for lane, curve in enumerate(curves):
        pts = _resample(curve)
        total = pts[-1][1]
        for p, s in pts:
            c, seg, along = project(lane, p)
            samples.append((lane, p, s, total, c, seg, along))
    bad = set()
    off_board = False
    for la, p, s, total, _c, seg, _a in samples:
        if end_keep < s < total - end_keep and not _inside(p, grid, -0.2):
            off_board = True
            bad.add((seg, seg))
    for i in range(len(samples)):
        la, p, s, _t, pc, pseg, palong = samples[i]
        for j in range(i + 1, len(samples)):
            lb, q, t, _t2, qc, qseg, qalong = samples[j]
            if abs(p[0] - q[0]) >= CLEARANCE or abs(p[1] - q[1]) >= CLEARANCE:
                continue
            if la == lb and abs(s - t) < CLEARANCE * 2.2:
                continue
            if _len(_sub(p, q)) >= CLEARANCE - 0.4:
                continue
            if la != lb:
                # Lanes that share a road: judge the pair as two points of one lane.
                on = on_lane(la, q)
                if on is not None:
                    lb, t = la, on
                    qc, qseg, qalong = project(la, q)
                    if abs(s - t) < CLEARANCE * 2.2:
                        continue
            if _len(_sub(pc, qc)) < CLEARANCE + 0.5 and (la != lb or abs(palong - qalong) > CLEARANCE * 3):
                continue  # these roads were this close before bending: a crossing or a join
            bad.add((pseg, qseg))
    return bad, off_board


def _closest_on(seg, p):
    a, b = seg
    v = _sub(b, a)
    ll = v[0] * v[0] + v[1] * v[1]
    if ll < 1e-12:
        return a
    t = max(0.0, min(1.0, ((p[0] - a[0]) * v[0] + (p[1] - a[1]) * v[1]) / ll))
    return _add(a, _mul(v, t))


# ------------------------------------------------------------------------------------ a whole map
def build(stage_id, sketch_lanes, holes=0, grid=GRID, fixed_cells=(), jitter=True):
    """The finished roads of one map: a list of (waypoints, curve, is_hole) per lane, lane 0 first.
    Hole lanes come after the sketch's own lanes."""
    seed = _seed(stage_id)
    spans = _spans(sketch_lanes)
    fixed = {scale_point(c, grid, spans) for c in fixed_cells}
    lanes = merge_overlaps(scale_lanes(sketch_lanes, grid, spans))
    if jitter:
        lanes = _jitter(lanes, grid, seed, fixed)
    if holes:
        lanes = add_holes(lanes, holes, grid, seed)
    scale = {}

    def norm(seg):
        return (min(seg), max(seg))

    for _ in range(16):
        bent = _bend(lanes, grid, seed, scale, fixed)
        curves = [round_corners(lane) for lane in bent]
        bad, _off = _too_close(curves, lanes, grid)
        if not bad:
            break
        for a, b in bad:
            a, b = norm(a), norm(b)
            # Two bends that crowd each other: the shorter straight gives way, so long straights
            # (the ones that most need a bend) keep theirs.
            la, lb = _len(_sub(a[1], a[0])), _len(_sub(b[1], b[0]))
            short, long_ = (a, b) if la < lb else (b, a)
            if a == b or abs(la - lb) < 0.5:
                shrink = {a, b}
            elif scale.get(short, 1.0) > 0.1:
                shrink = {short}
            else:
                shrink = {long_}
            for key in shrink:
                scale[key] = scale.get(key, 1.0) * 0.6
    else:
        for a, b in bad:
            scale[norm(a)] = scale[norm(b)] = 0.0
        bent = _bend(lanes, grid, seed, scale, fixed)
        curves = [round_corners(lane) for lane in bent]
    waypoints = [[(int(round(x)), int(round(y))) for x, y in lane] for lane in bent]
    for w, lane in zip(waypoints, bent):
        w[0], w[-1] = lane[0], lane[-1]
    return [(w, c, i >= len(sketch_lanes)) for i, (w, c) in enumerate(zip(waypoints, curves))]


def scale_cell(cell, sketch_lanes, grid=GRID):
    """Where a cell of a sketch lands on the finished map (the same stretch its roads get)."""
    return scale_point(cell, grid, _spans(sketch_lanes))


def scale_column(column, sketch_lanes, grid=GRID):
    if column < 0:
        return column
    return _scale_axis(column, SKETCH[0], grid[0], _spans(sketch_lanes)[0], _RIGHT_RESERVE)


def describe(roads, grid=GRID) -> str:
    """A text picture of a map, for checking by eye: # road, O hole, . ground."""
    rows = [["." for _ in range(grid[0])] for _ in range(grid[1])]
    for _, curve, _hole in roads:
        for p, _s in _resample(curve, 0.25):
            x, y = int(math.floor(p[0] + 0.5)), int(math.floor(p[1] + 0.5))
            if 0 <= x < grid[0] and 0 <= y < grid[1]:
                rows[y][x] = "#"
    for waypoints, _, hole in roads:
        x, y = waypoints[0]
        if hole:
            rows[y][x] = "O"
    return "\n".join("".join(r) for r in rows)
