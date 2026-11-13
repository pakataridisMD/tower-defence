"""The cast as 3D pixel art: each character rebuilt in cubes from their game sprite (art/story/characters/<id>/),
same colours and features, cut into rigid parts on pivots (hips, torso, head, two arms, two legs, a mouth, eyes,
a carried item) so they can act in big, snappy poses.

    rig = fennick(); pose(rig, t, arm_l=(fwd, out), head=(nod, tilt, turn), ...)   # see pose() below

Cells are voxkit.V metres. The figure faces -Y; its right side is -X."""
import math
import bpy
from mathutils import Vector
from voxkit import Part, rgb, V

SKIN = rgb("#eab896"); SKIN_D = rgb("#c98e6e")
WHITE = rgb("#ece6da"); WHITE_D = rgb("#c9c2b4")
EYE = rgb("#241a1a"); MOUTH = rgb("#3a1414")


def _empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    e.empty_display_size = 0.05
    if parent:
        e.parent = parent
    e.location = loc
    return e


def _attach(ob, parent, loc_cells):
    ob.parent = parent; ob.location = tuple(c * V for c in loc_cells)
    return ob


def _eyes(head, xs, z, y, name, col=EYE, h=2, w=2):
    """Two eyes as their own small object (so they can blink and widen), on the face at front y."""
    p = Part()
    for x in xs:
        p.box(x, 0, 0, x + w, 1, h, col)
        p.put(x + (1 if x > 0 else w - 2), -1, h - 1, rgb("#fff4e0"))   # a glint, so the eyes look alive
    o = p.mesh(name, origin=(0, 0, h / 2.0))
    _attach(o, head, (0, y - 0.6, z + h / 2.0))
    return o


def _mouth(head, x0, x1, z, y, name):
    p = Part(); p.box(x0, 0, -1, x1, 1, 1, MOUTH)
    o = p.mesh(name, origin=(0, 0, 0)); _attach(o, head, (0, y - 0.7, z))
    o.scale.z = 0.25
    return o


def _limb(name, w, d, length, top, bottom, bottom_rows, cuff=None, seed=3):
    """An arm or a leg hanging down from its pivot (origin at the top centre)."""
    p = Part(seed)
    x0 = -w // 2; y0 = -d // 2
    p.box(x0, y0, -length, x0 + w, y0 + d, 0, lambda x, y, z: bottom if z < -length + bottom_rows else (cuff if cuff and z < -length + bottom_rows + 1 else top))
    return p, x0, y0


def _rig(name, parts, hip_h, shoulder_z, shoulder_x, neck_z, leg_x):
    root = _empty("rig_" + name)
    hips = _empty(name + "_hips", root, (0, 0, hip_h * V))
    rig = dict(root=root, hips=hips, name=name)
    rig["torso"] = _attach(parts["torso"], hips, (0, 0, 0))
    rig["head"] = _attach(parts["head"], rig["torso"], (0, 0, neck_z))
    rig["arm_r"] = _attach(parts["arm_r"], rig["torso"], (-shoulder_x, 0, shoulder_z))
    rig["arm_l"] = _attach(parts["arm_l"], rig["torso"], (shoulder_x, 0, shoulder_z))
    rig["leg_r"] = _attach(parts["leg_r"], hips, (-leg_x, 0, 0))
    rig["leg_l"] = _attach(parts["leg_l"], hips, (leg_x, 0, 0))
    return rig


# ------------------------------------------------------------------ Fennick
def fennick():
    """Fennick the tower-designer: old, round, bald, a big white beard and bushy brows, white shirt under a brown
    waistcoat, dark trousers, a gold-topped staff (as in his sprite)."""
    VEST = rgb("#7a4a2c"); VEST_D = rgb("#5e3620"); GOLD = rgb("#d8a848"); TROUS = rgb("#4a3a34"); BOOT = rgb("#2c221e")
    parts = {}
    # torso: z 0..18 above the hips, round belly
    t = Part(11)
    def torso_col(x, y, z):
        if z < 2:
            return rgb("#3a2a22")                      # belt
        if abs(x + 0.5) <= 2.0 and y < 0:
            return WHITE if (z % 4) else GOLD if abs(x + 0.5) < 1 else WHITE   # shirt front, gold buttons
        return VEST if z > 3 else VEST_D
    t.box(-9, -5, 0, 9, 5, 18, torso_col)
    t.ell(0, -3.5, 7, 8.5, 4.5, 7.5, torso_col)         # belly
    t.box(-10, -5, 13, 10, 5, 18, lambda x, y, z: WHITE if abs(x) >= 9 else torso_col(x, y, z))   # shirt shoulders
    parts["torso"] = t.mesh("fennick_torso", origin=(0, 0, 0))
    # head: z 0..15 above the neck
    h = Part(12)
    h.box(-7, -6, 0, 7, 7, 14, SKIN)
    h.box(-6, -5, 14, 6, 6, 15, rgb("#f2c8a8"))         # the bald crown, catching light
    for sx in (-1, 1):                                  # ears
        h.box(7 if sx > 0 else -8, -1, 5, 8 if sx > 0 else -7, 2, 9, SKIN_D)
    h.box(-1, -7, 6, 1, -6, 9, rgb("#e09a80"))          # nose
    h.ell(0, -6.5, 3.0, 6.5, 2.6, 5.0, WHITE)           # beard over the jaw ...
    h.ell(0, -7.0, -2.0, 5.0, 2.6, 4.5, WHITE)          # ... spilling onto the chest
    h.box(-5, -8, 4, 5, -7, 6, WHITE_D)                 # moustache
    h.box(-6, -7, 10, -1, -6, 12, WHITE); h.box(1, -7, 10, 6, -6, 12, WHITE)   # bushy brows
    h.box(-7, -2, 4, -6, 6, 10, WHITE_D); h.box(6, -2, 4, 7, 6, 10, WHITE_D)    # white hair at the sides
    h.box(-7, 6, 3, 7, 7, 9, WHITE_D)
    parts["head"] = h.mesh("fennick_head", origin=(0, 0, 0))
    # arms: white sleeves, skin hands
    for side in ("r", "l"):
        p, _, _ = _limb("arm", 5, 5, 16, WHITE, SKIN, 4, cuff=WHITE_D, seed=13 if side == "r" else 14)
        parts["arm_" + side] = p.mesh("fennick_arm_" + side, origin=(0, 0, 0))
    for side in ("r", "l"):
        p = Part(15 if side == "r" else 16)
        p.box(-3, -3, -16, 3, 3, 0, lambda x, y, z: BOOT if z < -12 else TROUS)
        p.box(-3, -5, -16, 3, -3, -13, BOOT)            # boot toes
        parts["leg_" + side] = p.mesh("fennick_leg_" + side, origin=(0, 0, 0))
    rig = _rig("fennick", parts, hip_h=16, shoulder_z=16, shoulder_x=11.5, neck_z=18, leg_x=4)
    rig["eyes"] = _eyes(rig["head"], (-5, 2), 8, -6, "fennick_eyes", h=2, w=3)
    rig["mouth"] = _mouth(rig["head"], -2, 2, 3, -9, "fennick_mouth")
    # the staff in his right hand: gold, with an amber stone that can flare
    s = Part(17)
    s.line((0, 0, -26), (0, 0, 22), 1.0, GOLD)
    s.ell(0.5, 0.5, 24, 2.6, 2.6, 2.8, rgb("#ffb040"), glow=1.0)
    s.box(-2, -2, 20, 3, 3, 21, GOLD)
    rig["item"] = _attach(s.mesh("fennick_staff", origin=(0, 0, 0), glow_strength=1.2), rig["arm_r"], (0, -3, -14))
    rig["height"] = 49 * V
    return rig


# ------------------------------------------------------------------ Tamsin
def tamsin():
    """Tamsin the lamplighter: young, red hair tied back, a blue tunic with a pale front, dark blue trousers, a long
    lantern pole with a burning lantern (as in her sprite)."""
    BLUE = rgb("#4a6c9c"); BLUE_D = rgb("#36527a"); PALE = rgb("#d6dce6"); TROUS = rgb("#3a4866"); BOOT = rgb("#3a2a22")
    HAIR = rgb("#c8603c"); HAIR_D = rgb("#9c4428"); WOOD = rgb("#6a4a30"); FLAME = rgb("#ffb050")
    skin = rgb("#f0c4a4")
    parts = {}
    t = Part(21)
    def torso_col(x, y, z):
        if 2 <= z < 4:
            return rgb("#5a3a26")
        if y < 0 and abs(x + 0.5) < 3.5 and z > 6:
            return PALE
        return BLUE if z > 1 else BLUE_D
    t.box(-7, -4, 0, 7, 4, 17, torso_col)
    t.box(-8, -5, -4, 8, 5, 4, lambda x, y, z: BLUE_D if z < 0 else torso_col(x, y, z))   # tunic skirt
    parts["torso"] = t.mesh("tamsin_torso", origin=(0, 0, 0))
    h = Part(22)
    h.box(-6, -5, 0, 6, 6, 13, skin)
    h.box(-1, -6, 5, 1, -5, 7, rgb("#e8a88c"))          # nose
    h.box(-7, -5, 9, 7, 7, 15, HAIR)                    # hair cap
    h.box(-7, -6, 10, 7, -5, 13, lambda x, y, z: HAIR_D if (x % 4 == 0 and z == 10) else HAIR)   # fringe
    h.box(-7, -4, -1, -6, 4, 4, HAIR); h.box(6, -4, -1, 7, 4, 4, HAIR)                         # hair over the ears
    h.box(-7, -2, 3, -6, 7, 11, HAIR); h.box(6, -2, 3, 7, 7, 11, HAIR)
    h.box(-6, 6, 2, 6, 7, 11, HAIR)
    h.ell(0, 9, 7, 2.6, 3.0, 4.5, HAIR_D)               # the tie at the back
    h.box(-5, -6, 3, -3, -5, 4, rgb("#e89a8a")); h.box(3, -6, 3, 5, -5, 4, rgb("#e89a8a"))   # cheeks
    parts["head"] = h.mesh("tamsin_head", origin=(0, 0, 0))
    for side in ("r", "l"):
        p, _, _ = _limb("arm", 4, 4, 16, BLUE, skin, 3, cuff=PALE, seed=23 if side == "r" else 24)
        parts["arm_" + side] = p.mesh("tamsin_arm_" + side, origin=(0, 0, 0))
    for side in ("r", "l"):
        p = Part(25 if side == "r" else 26)
        p.box(-2, -3, -20, 3, 3, 0, lambda x, y, z: BOOT if z < -15 else TROUS)
        p.box(-2, -5, -20, 3, -3, -17, BOOT)
        parts["leg_" + side] = p.mesh("tamsin_leg_" + side, origin=(0, 0, 0))
    rig = _rig("tamsin", parts, hip_h=20, shoulder_z=15, shoulder_x=9, neck_z=17, leg_x=3)
    rig["eyes"] = _eyes(rig["head"], (-4, 2), 6, -5, "tamsin_eyes", h=2, w=2)
    rig["mouth"] = _mouth(rig["head"], -1, 2, 2, -5, "tamsin_mouth")
    # the lantern pole, held upright in her left hand, the lantern hanging from a hook at the top
    s = Part(27)
    s.line((0, 0, -20), (0, 0, 60), 0.8, WOOD)
    s.line((0, 0, 60), (0, -6, 62), 0.6, rgb("#3a3a40"))
    s.box(-2, -9, 50, 3, -4, 57, lambda x, y, z: rgb("#3a3a40") if z in (50, 56) or x in (-2, 2) and z % 2 else FLAME, glow=0.0)
    s.paint(lambda x, y, z, c: (c, 1.0) if c == FLAME else None)
    rig["item"] = _attach(s.mesh("tamsin_pole", origin=(0, 0, 0), glow_strength=10.0), rig["arm_l"], (0, -3, -14))
    lamp = bpy.data.lights.new("tamsin_lantern", "POINT"); lamp.energy = 25; lamp.color = (1.0, 0.7, 0.35); lamp.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("tamsin_lantern", lamp); bpy.context.scene.collection.objects.link(lo)
    lo.parent = rig["item"]; lo.location = (0, -6.5 * V, 53 * V)
    rig["height"] = 52 * V
    return rig


# ------------------------------------------------------------------ acting
def _k(o, path, frame):
    o.keyframe_insert(path, frame=frame)


def pose(rig, frame, loc=None, face=None, squash=None, lean=None, head=None, arm_r=None, arm_l=None, leg_r=None, leg_l=None,
         eyes=None, mouth=None, item=None):
    """Key one pose at `frame`. Angles in degrees.
    loc (x, y, z) of the feet; face: turn about Z (0 = facing the camera at -Y); squash: (width, height) scale;
    lean (fwd, side) of the hips; head (nod down, tilt, turn); arm_* (forward, out[, twist]); leg_* (forward, out);
    eyes: open 0..1.3; mouth: open 0..1."""
    r = rig
    if loc is not None:
        r["root"].location = loc; _k(r["root"], "location", frame)
    if face is not None:
        r["root"].rotation_euler.z = math.radians(face); _k(r["root"], "rotation_euler", frame)
    if squash is not None:
        w, h = squash; r["root"].scale = (w, w, h); _k(r["root"], "scale", frame)
    if lean is not None:
        f, s = lean; r["hips"].rotation_euler = (math.radians(-f), math.radians(s), 0); _k(r["hips"], "rotation_euler", frame)
    if head is not None:
        n, t, tu = head; r["head"].rotation_euler = (math.radians(n), math.radians(t), math.radians(tu)); _k(r["head"], "rotation_euler", frame)
    for key, val, sgn in (("arm_r", arm_r, 1), ("arm_l", arm_l, -1), ("leg_r", leg_r, 1), ("leg_l", leg_l, -1)):
        if val is not None:
            f, o = val[0], val[1]; tw = val[2] if len(val) > 2 else 0
            r[key].rotation_euler = (math.radians(-f), math.radians(o * sgn), math.radians(tw * sgn)); _k(r[key], "rotation_euler", frame)
    if eyes is not None:
        r["eyes"].scale = (1, 1, max(0.08, eyes)); _k(r["eyes"], "scale", frame)
    if mouth is not None:
        r["mouth"].scale = (1, 1, 0.25 + 1.1 * mouth); _k(r["mouth"], "scale", frame)
    if item is not None:
        r["item"].rotation_euler = tuple(math.radians(a) for a in item); _k(r["item"], "rotation_euler", frame)


def objects(rig):
    return [v for v in rig.values() if isinstance(v, bpy.types.Object)]
