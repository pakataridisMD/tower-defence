"""A simple humanoid rig and the parts that dress it.

`Body` turns a pose (joint angles) into joint positions; `build()` dresses those joints with SDF
primitives according to a character spec (robe or armour, hood or helm, beard, cape, weapon...).
Animations are just functions from a frame number to a pose, so every character gets the same set:
idle, walk, attack, cast, hurt, death.

A character faces +x. z is its left side (towards the camera at yaw 0) and -z its right side.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from sdf import Prim, box, cone, ellipsoid, rot_x, rot_y, rot_z, sphere


def v(*a):
    return np.array(a, np.float32)


@dataclass
class Pose:
    bob: float = 0.0            # whole body up/down
    lean: float = 0.0           # spine lean forward (radians)
    twist: float = 0.0          # shoulders turn about y
    head: float = 0.0           # head nod forward
    head_turn: float = 0.0
    # arms: (shoulder forward swing, shoulder outward raise, elbow bend) radians
    arm_n: tuple = (0.1, 0.12, 0.3)   # near arm (left, +z)
    arm_f: tuple = (-0.1, 0.12, 0.3)  # far arm (right, -z)
    # legs: (hip forward swing, knee bend)
    leg_n: tuple = (0.0, 0.0)
    leg_f: tuple = (0.0, 0.0)
    cape: float = 0.0           # cape flare backwards
    fall: float = 0.0           # 0..1 collapse for death: tips the whole body backwards
    weapon: float = 0.0         # extra weapon rotation in the hand
    glow: float = 0.0           # 0..1 spell charge (bigger hand/weapon glow)
    sink: float = 0.0           # 0..1 dissolve into the ground (death of spirits)


@dataclass
class Body:
    height: float = 1.8
    head_r: float = 0.13
    shoulder: float = 0.22
    hip_w: float = 0.11
    bulk: float = 1.0           # limb thickness multiplier
    head_scale: float = 1.0     # chibi factor for small sprites
    chest_depth: float = 1.0


def joints(b: Body, p: Pose) -> dict:
    H = b.height
    leg = H * 0.47
    thigh, shin = leg * 0.5, leg * 0.5
    torso = H * 0.30
    J = {}

    def limb(root, ang_fwd, bend, l1, l2, side_out=0.0, down=True):
        # swing forward in the x-y plane, outward along z
        d1 = v(math.sin(ang_fwd), -math.cos(ang_fwd), 0)
        d1 = d1 + v(0, 0, side_out)
        d1 /= np.linalg.norm(d1)
        k = root + d1 * l1
        a2 = ang_fwd + bend if down else ang_fwd - bend
        d2 = v(math.sin(a2), -math.cos(a2), 0) + v(0, 0, side_out * 0.5)
        d2 /= np.linalg.norm(d2)
        return k, k + d2 * l2

    pelvis = v(0, leg + p.bob, 0)
    J["pelvis"] = pelvis
    for name, side, (sw, kn) in (("n", 1, p.leg_n), ("f", -1, p.leg_f)):
        hip = pelvis + v(0, 0, side * b.hip_w)
        knee, foot = limb(hip, sw, -kn, thigh, shin)
        J["hip_" + name], J["knee_" + name], J["foot_" + name] = hip, knee, foot
    lean = p.lean
    up = v(math.sin(lean), math.cos(lean), 0)
    chest = pelvis + up * torso * 0.66
    neck = pelvis + up * torso
    J["chest"], J["neck"] = chest, neck
    tw = rot_y(p.twist)
    for name, side, (sw, out, el) in (("n", 1, p.arm_n), ("f", -1, p.arm_f)):
        sh = neck + tw @ v(-0.01, -0.085, side * b.shoulder)
        upper, fore = H * 0.17, H * 0.16
        d1 = v(math.sin(sw) * math.cos(out), -math.cos(sw) * math.cos(out), side * math.sin(out))
        el_p = sh + d1 * upper
        a2 = sw + el
        d2 = v(math.sin(a2) * math.cos(out * 0.5), -math.cos(a2) * math.cos(out * 0.5), side * math.sin(out * 0.5))
        hand = el_p + d2 * fore
        J["sh_" + name], J["el_" + name], J["hand_" + name] = sh, el_p, hand
        J["fore_dir_" + name] = d2
    hr = b.head_r * b.head_scale
    hd = up * (hr * 1.05) + v(math.sin(p.head) * hr * 0.3, 0, 0)
    J["head"] = neck + hd + v(0, hr * 0.15, 0)
    J["head_r"] = hr
    J["up"] = up
    return J


def transform(prims: list[Prim], M: np.ndarray, pivot: np.ndarray, shift: np.ndarray) -> list[Prim]:
    """Rotate primitives about a pivot (used for the death fall) and move them."""
    out = []
    for p in prims:
        a = list(p.a)
        if p.kind == "sphere":
            a[0] = (M @ (a[0] - pivot)) + pivot + shift
        elif p.kind in ("ellip", "box"):
            idx_rot = 2 if p.kind == "ellip" else 3
            a[0] = (M @ (a[0] - pivot)) + pivot + shift
            a[idx_rot] = M if a[idx_rot] is None else M @ a[idx_rot]
        elif p.kind == "rcone":
            a[0] = (M @ (a[0] - pivot)) + pivot + shift
            a[1] = (M @ (a[1] - pivot)) + pivot + shift
        out.append(Prim(p.kind, tuple(a), p.mat, p.k, p.sub, p.disp, p.layer))
    return out


# ---------------------------------------------------------------- dressing
def build(spec: dict, b: Body, p: Pose) -> list[Prim]:
    J = joints(b, p)
    P: list[Prim] = []
    s = spec
    bulk = b.bulk
    hr = J["head_r"]
    skin = s.get("skin_mat", "skin")
    cloth = s.get("cloth", "cloth")
    cloth2 = s.get("cloth2", "cloth2")
    armour = s.get("armour")          # material name or None
    robe = s.get("robe", False)

    # ---- cape behind (its own layer so it doesn't melt into the body)
    if s.get("cape"):
        sh_c = (J["sh_n"] + J["sh_f"]) / 2
        top = sh_c + v(-0.09, 0.0, 0)
        flare = 0.12 + 0.35 * p.cape
        bot = v(J["pelvis"][0] - flare, 0.05 + 0.2 * p.cape, 0)
        mid = (top + bot) / 2
        d = bot - top
        ang = math.atan2(d[0], -d[1])
        half_len = float(np.linalg.norm(d)) / 2
        P.append(box(mid, (0.025, half_len, 0.2 * bulk), s["cape"], round_=0.02, rot=rot_z(ang), k=0.0, layer=1,
                     disp=(0.025, 24.0, "y", 3)))
        P.append(box(bot + v(0, 0.08, 0), (0.03, 0.08, 0.26 * bulk), s["cape"], round_=0.025, rot=rot_z(ang), k=0.08,
                     layer=1, disp=(0.025, 24.0, "y", 3)))
        if s.get("cape_tatter"):
            for i, dz in enumerate((-0.18, 0.0, 0.18)):
                P.append(cone(bot + v(0, 0, dz), bot + v(-0.05 - 0.1 * p.cape, -0.1 - 0.04 * i, dz * 1.2),
                              0.04, 0.01, s["cape"], k=0.04, layer=1))

    # ---- legs
    for side in (() if s.get("no_legs") else ("f", "n")):
        hip, knee, foot = J["hip_" + side], J["knee_" + side], J["foot_" + side]
        leg_mat = s.get("legs", cloth2)
        P.append(cone(hip, knee, 0.075 * bulk, 0.058 * bulk, leg_mat, k=0.03))
        P.append(cone(knee, foot + v(0, 0.04, 0), 0.058 * bulk, 0.045 * bulk, s.get("boots", "leather"), k=0.02))
        P.append(ellipsoid(foot + v(0.04, 0.035, 0), (0.08 * bulk, 0.04, 0.05 * bulk), s.get("boots", "leather"), k=0.02))
        if armour and s.get("greaves"):
            P.append(sphere(knee + v(0.03, 0, 0), 0.06 * bulk, armour, k=0.01))

    # ---- torso
    pel, chest, neck, up = J["pelvis"], J["chest"], J["neck"], J["up"]
    torso_mat = s.get("torso", cloth)
    P.append(ellipsoid(pel + up * 0.02, (0.13 * bulk, 0.11, 0.15 * bulk), torso_mat, k=0.04))
    P.append(ellipsoid(chest, (0.14 * bulk * b.chest_depth, 0.2, 0.18 * bulk), torso_mat, k=0.08,
                       disp=(0.006, 30.0, "y", 5)))
    # trapezius / shoulder mass so the arms grow out of the body instead of standing beside it
    P.append(cone(J["sh_f"] + v(0, 0.02, 0.03), J["sh_n"] + v(0, 0.02, -0.03), 0.075 * bulk, 0.075 * bulk, torso_mat, k=0.07))
    P.append(cone(chest, neck + up * 0.04, 0.05, 0.05, skin, k=0.03))
    if s.get("belt"):
        P.append(ellipsoid(pel + up * 0.09, (0.135 * bulk, 0.028, 0.158 * bulk), s["belt"], k=0.0, layer=2))
        P.append(sphere(pel + up * 0.09 + v(0.12 * bulk, 0, 0.0), 0.03, s.get("buckle", "metal"), layer=2))
    if robe:
        # a skirt that widens to the ground; legs show only at the hem when walking
        hem_y = 0.06
        sway = (J["foot_n"][0] + J["foot_f"][0]) * 0.25
        P.append(cone(pel + up * 0.05, v(pel[0] + sway, hem_y + 0.08, 0), 0.15 * bulk, 0.25 * bulk, s.get("robe_mat", cloth),
                      k=0.06, disp=(0.018, 26.0, "y", 7)))
        if s.get("hem"):
            P.append(cone(v(pel[0] + sway, hem_y + 0.075, 0), v(pel[0] + sway, hem_y + 0.045, 0), 0.255 * bulk,
                          0.262 * bulk, s["hem"], layer=2, disp=(0.018, 26.0, "y", 7)))
    if armour:
        P.append(ellipsoid(chest + v(0.035, 0.02, 0), (0.135 * bulk, 0.15, 0.175 * bulk), armour, k=0.0, layer=2))
        if s.get("gorget"):
            P.append(cone(neck - up * 0.04, neck + up * 0.05, 0.085 * bulk, 0.06, s["gorget"], layer=2))
        if s.get("trim"):
            P.append(cone(chest + v(0.13 * bulk, 0.12, 0), chest + v(0.14 * bulk, -0.15, 0), 0.012, 0.012, s["trim"], layer=2))
        if s.get("collar"):
            P.append(cone((J["sh_n"] + J["sh_f"]) / 2 + v(-0.05, 0.02, 0) - v(0, 0, 0.17), (J["sh_n"] + J["sh_f"]) / 2 +
                          v(-0.05, 0.02, 0) + v(0, 0, 0.17), 0.05, 0.05, s["collar"], layer=2, disp=(0.01, 50, "", 17)))
        if s.get("rune"):
            P.append(ellipsoid(chest + v(0.16 * bulk, 0.02, 0), (0.02, 0.05, 0.03), s["rune"], layer=2))
    if s.get("tabard"):
        P.append(box(pel + up * 0.02 + v(0.10 * bulk, -0.16, 0), (0.02, 0.17, 0.08), s["tabard"], round_=0.015,
                     layer=2, rot=rot_z(-0.08 - p.lean)))

    # ---- arms (far arm first so the near one sits in front)
    for side in ("f", "n"):
        sh, el, hand = J["sh_" + side], J["el_" + side], J["hand_" + side]
        sleeve = s.get("sleeve", cloth)
        P.append(cone(sh, el, 0.062 * bulk, 0.05 * bulk, sleeve, k=0.05))
        P.append(cone(el, hand, 0.05 * bulk, 0.04 * bulk, s.get("forearm", sleeve), k=0.02))
        if s.get("wide_sleeves"):
            d = J["fore_dir_" + side]
            P.append(cone(el + d * 0.02, el + d * 0.15, 0.055, 0.085, sleeve, k=0.03, disp=(0.01, 30, "y", 9)))
        P.append(sphere(hand, 0.045 * bulk, s.get("hands", skin), k=0.015))
        if armour:
            pm = s.get("pauldron", armour)
            sd = 1 if side == "n" else -1
            P.append(ellipsoid(sh + v(-0.005, 0.03, sd * 0.02), (0.085 * bulk, 0.055, 0.085 * bulk), pm, k=0.0, layer=2,
                               rot=rot_x(-sd * 0.35)))
            P.append(ellipsoid(sh + v(-0.005, -0.025, sd * 0.045), (0.075 * bulk, 0.045, 0.07 * bulk), pm, k=0.0, layer=2,
                               rot=rot_x(-sd * 0.55)))
            if s.get("trim"):
                P.append(ellipsoid(sh + v(-0.005, 0.0, sd * 0.06), (0.08 * bulk, 0.012, 0.06 * bulk), s["trim"], layer=2,
                                   rot=rot_x(-sd * 0.55)))
            if s.get("spikes"):
                P.append(cone(sh + v(-0.01, 0.06, 0), sh + v(-0.06, 0.2, 0), 0.03, 0.004, s["spikes"], layer=2))

    # ---- head
    head = J["head"]
    hrot = rot_y(p.head_turn) @ rot_z(-p.head)
    jaw = s.get("jaw", 1.0)
    P.append(ellipsoid(head, (hr * 0.98, hr * 1.08, hr * 0.86), skin, k=0.02))
    face = head + hrot @ v(hr * 0.86, -hr * 0.05, 0)
    if s.get("face", True):
        # nose, brow, cheeks, jaw
        P.append(cone(face + hrot @ v(-0.01, hr * 0.12, 0), face + hrot @ v(hr * 0.22, -hr * 0.22, 0), hr * 0.07,
                      hr * 0.10, skin, k=hr * 0.08))
        P.append(ellipsoid(head + hrot @ v(hr * 0.2, -hr * 0.55, 0), (hr * 0.68 * jaw, hr * 0.42, hr * 0.64 * jaw), skin,
                           k=hr * 0.25))
        P.append(sphere(head + hrot @ v(hr * 0.62, -hr * 0.82, 0), hr * 0.2 * (0.6 + 0.4 * jaw), skin, k=hr * 0.18))
        for side in (1, -1):
            P.append(sphere(face + hrot @ v(-hr * 0.12, hr * 0.12, side * hr * 0.36), hr * 0.17, skin, sub=True,
                            k=hr * 0.08))
            eye_mat = s.get("eyes", "eye")
            P.append(sphere(face + hrot @ v(-hr * 0.2, hr * 0.12, side * hr * 0.36), hr * 0.12, eye_mat, layer=3))
    if s.get("hair"):
        P.append(ellipsoid(head + hrot @ v(-hr * 0.15, hr * 0.25, 0), (hr * 0.95, hr * 0.92, hr * 1.0), s["hair"],
                           k=0.0, layer=4, disp=(hr * 0.06, 90.0 / max(hr, 0.05) * 0.13, "x", 11)))
        if s.get("long_hair"):
            P.append(cone(head + hrot @ v(-hr * 0.4, 0, 0), head + v(-hr * 0.7, -hr * 2.4, 0), hr * 0.9, hr * 0.55,
                          s["hair"], k=hr * 0.3, layer=4, disp=(hr * 0.05, 70, "y", 12)))
    if s.get("beard"):
        L = s.get("beard_len", 1.0)
        P.append(cone(head + hrot @ v(hr * 0.5, -hr * 0.62, 0), head + hrot @ v(hr * 0.8, -hr * (1.25 + 1.2 * L), 0),
                      hr * 0.55, hr * 0.1, s["beard"], k=hr * 0.25, layer=4, disp=(hr * 0.05, 140, "y", 13)))
        for side in (1, -1):  # moustache
            P.append(cone(face + hrot @ v(hr * 0.12, -hr * 0.36, side * hr * 0.05),
                          face + hrot @ v(-hr * 0.05, -hr * 0.62, side * hr * 0.42), hr * 0.11, hr * 0.06, s["beard"],
                          layer=4, k=hr * 0.05))
    if s.get("brows"):
        for side in (1, -1):
            P.append(ellipsoid(face + hrot @ v(hr * 0.02, hr * 0.33, side * hr * 0.38), (hr * 0.12, hr * 0.06, hr * 0.24),
                               s["brows"], layer=4, rot=rot_x(side * 0.3)))
    if s.get("hood"):
        P.append(ellipsoid(head + hrot @ v(-hr * 0.22, hr * 0.15, 0), (hr * 1.2, hr * 1.28, hr * 1.18), s["hood"], k=0.0,
                           layer=5, disp=(hr * 0.04, 40, "y", 14)))
        P.append(ellipsoid(head + hrot @ v(hr * 1.05, -hr * 0.3, 0), (hr * 1.15, hr * 1.3, hr * 1.02), s["hood"],
                           sub=True, layer=5, k=hr * 0.12))
        # the hood's cowl drapes onto the shoulders
        P.append(cone(head + hrot @ v(-hr * 0.75, -hr * 0.3, 0), (J["sh_n"] + J["sh_f"]) / 2 + v(-0.11, -0.02, 0),
                      hr * 0.8, hr * 1.25, s["hood"], k=hr * 0.3, layer=5, disp=(hr * 0.05, 40, "y", 15)))
        P.append(cone(head + hrot @ v(-hr * 0.9, hr * 0.7, 0), head + hrot @ v(-hr * 1.9, -hr * 0.2, 0), hr * 0.45,
                      hr * 0.12, s["hood"], k=hr * 0.3, layer=5))
    if s.get("helm"):
        m = s["helm"]
        P.append(ellipsoid(head + hrot @ v(-hr * 0.05, hr * 0.12, 0), (hr * 1.15, hr * 1.2, hr * 1.1), m, k=0.0, layer=5))
        # visor slit
        P.append(box(head + hrot @ v(hr * 1.05, hr * 0.12, 0), (hr * 0.3, hr * 0.09, hr * 0.7), m, sub=True, layer=5,
                     rot=hrot))
        if s.get("helm_glow"):
            P.append(box(head + hrot @ v(hr * 0.86, hr * 0.12, 0), (hr * 0.08, hr * 0.06, hr * 0.55), s["helm_glow"],
                         layer=6, rot=hrot))
        P.append(cone(head + hrot @ v(hr * 0.8, -hr * 0.4, 0), head + hrot @ v(hr * 0.9, -hr * 1.2, 0), hr * 0.35,
                      hr * 0.12, m, layer=5, k=hr * 0.2))
    if s.get("hat"):
        m = s["hat"]
        tilt = rot_z(-0.12) @ hrot
        P.append(ellipsoid(head + hrot @ v(hr * 0.05, hr * 0.62, 0), (hr * 2.0, hr * 0.13, hr * 1.9), m, layer=6,
                           rot=tilt, disp=(hr * 0.04, 30, "x", 16)))
        P.append(ellipsoid(head + hrot @ v(-hr * 0.1, hr * 1.0, 0), (hr * 1.02, hr * 0.62, hr * 0.98), m, layer=6, k=hr * 0.2,
                           rot=tilt))
        P.append(ellipsoid(head + hrot @ v(-hr * 0.2, hr * 1.38, 0), (hr * 0.8, hr * 0.45, hr * 0.78), m, layer=6, k=hr * 0.25,
                           rot=tilt))
        P.append(ellipsoid(head + hrot @ v(-hr * 0.15, hr * 1.55, 0), (hr * 0.5, hr * 0.15, hr * 0.7), m, layer=6, sub=True,
                           k=hr * 0.15, rot=tilt))
        if s.get("hat_band"):
            P.append(ellipsoid(head + hrot @ v(-hr * 0.1, hr * 0.78, 0), (hr * 1.06, hr * 0.13, hr * 1.02), s["hat_band"],
                               layer=6, rot=tilt))
    if s.get("horns"):
        m = s["horns"]
        for side in (1, -1):
            base = head + hrot @ v(-hr * 0.1, hr * 0.8, side * hr * 0.65)
            mid = base + hrot @ v(-hr * 0.5, hr * 0.9, side * hr * 0.6)
            tip = mid + hrot @ v(-hr * 0.9, hr * 0.5, side * hr * 0.1)
            P.append(cone(base, mid, hr * 0.28, hr * 0.17, m, layer=7, k=hr * 0.05))
            P.append(cone(mid, tip, hr * 0.17, hr * 0.03, m, layer=7, k=hr * 0.08))
    if s.get("crown"):
        m = s["crown"]
        for i in range(7):
            a = -math.pi * 0.85 + i * (math.pi * 1.7 / 6)
            base = head + hrot @ v(math.cos(a) * hr * 0.95 - hr * 0.1, hr * 0.85, math.sin(a) * hr * 0.95)
            P.append(cone(base, base + v(0, hr * (0.55 if i % 2 else 0.85), 0), hr * 0.12, hr * 0.02, m, layer=7))
        P.append(cone(head + hrot @ v(-hr * 0.1, hr * 0.82, -hr), head + hrot @ v(-hr * 0.1, hr * 0.82, hr), hr * 0.12,
                      hr * 0.12, m, layer=7))
    if s.get("circlet6"):
        m = s["circlet6"]
        P.append(ellipsoid(head + hrot @ v(-hr * 0.08, hr * 0.62, 0), (hr * 1.0, hr * 0.06, hr * 0.92), m, layer=7,
                           rot=rot_z(-0.25) @ hrot))
        for i in range(6):
            a = -math.pi * 0.7 + i * (math.pi * 1.4 / 5)
            base = head + hrot @ v(math.cos(a) * hr * 0.98 - hr * 0.08, hr * 0.62 - math.cos(a) * hr * 0.2, math.sin(a) * hr * 0.92)
            P.append(cone(base, base + hrot @ v(-0.1 * hr, hr * 0.3, 0), hr * 0.06, hr * 0.01, m, layer=7))
    if s.get("circlet"):
        P.append(ellipsoid(head + hrot @ v(hr * 0.9, hr * 0.5, 0), (hr * 0.1, hr * 0.12, hr * 0.12), s["circlet"], layer=8))

    # ---- weapon in the near hand (drawn last, own layer)
    w = s.get("weapon")
    if w:
        hand = J["hand_n"]
        d = J["fore_dir_n"]
        ang = math.atan2(d[0], -d[1]) + p.weapon
        wd = v(math.sin(ang), -math.cos(ang), 0)   # along the forearm
        wtype = w["type"]
        if wtype == "staff":
            # held upright-ish, tilted a little with the arm
            tilt = 0.15 + p.weapon
            dirv = v(math.sin(tilt), math.cos(tilt), 0)
            top = hand + dirv * w.get("above", 0.75)
            bot = hand - dirv * w.get("below", 0.85)
            P.append(cone(bot, top, 0.022, 0.03, w["shaft"], layer=9))
            if w.get("head") == "crook":
                c1 = top + v(0.06, 0.08, 0)
                P.append(cone(top, c1, 0.032, 0.03, w["shaft"], layer=9, k=0.02))
                P.append(cone(c1, c1 + v(0.06, -0.06, 0), 0.03, 0.022, w["shaft"], layer=9, k=0.02))
                P.append(sphere(top + v(0.055, 0.0, 0), 0.055 + 0.03 * p.glow, w["gem"], layer=10))
            else:
                P.append(sphere(top + dirv * 0.06, 0.06 + 0.035 * p.glow, w["gem"], layer=10))
                for i in range(4):
                    a = i * math.pi / 2 + 0.4
                    P.append(cone(top - dirv * 0.02, top + dirv * 0.13 + v(math.cos(a) * 0.06, 0, math.sin(a) * 0.06),
                                  0.014, 0.006, w["shaft"], layer=9))
        elif wtype == "lantern_staff":
            tilt = 0.12 + p.weapon
            dirv = v(math.sin(tilt), math.cos(tilt), 0)
            top = hand + dirv * 0.78
            bot = hand - dirv * 0.9
            P.append(cone(bot, top, 0.022, 0.028, w["shaft"], layer=9))
            c1 = top + v(0.07, 0.07, 0)
            c2 = c1 + v(0.09, -0.03, 0)
            P.append(cone(top, c1, 0.028, 0.025, w["shaft"], layer=9, k=0.02))
            P.append(cone(c1, c2, 0.025, 0.02, w["shaft"], layer=9, k=0.02))
            swing = -0.04 * math.sin(p.lean * 6 + p.bob * 40)
            lamp = c2 + v(swing, -0.2, 0)
            P.append(cone(c2, lamp + v(0, 0.08, 0), 0.007, 0.007, w["frame"], layer=9))
            P.append(cone(lamp + v(0, 0.075, 0), lamp + v(0, 0.1, 0), 0.05, 0.02, w["frame"], layer=9))
            P.append(cone(lamp - v(0, 0.075, 0), lamp - v(0, 0.065, 0), 0.055, 0.055, w["frame"], layer=9))
            for i in range(4):
                a = i * math.pi / 2 + math.pi / 4
                off = v(math.cos(a) * 0.045, 0, math.sin(a) * 0.045)
                P.append(cone(lamp + off - v(0, 0.07, 0), lamp + off + v(0, 0.075, 0), 0.008, 0.008, w["frame"], layer=9))
            P.append(ellipsoid(lamp, (0.038 + 0.015 * p.glow, 0.06 + 0.015 * p.glow, 0.038 + 0.015 * p.glow), w["gem"], layer=10))
        elif wtype in ("sword", "greatsword"):
            L = 0.75 if wtype == "sword" else 1.15
            Wd = 0.035 if wtype == "sword" else 0.055
            grip_end = hand - wd * 0.08
            guard = hand + wd * 0.06
            tip = guard + wd * L
            P.append(cone(grip_end, guard, 0.02, 0.02, w.get("grip", "leather"), layer=9))
            side = np.cross(wd, v(0, 0, 1))
            P.append(cone(guard + v(0, 0, 0.1), guard - v(0, 0, 0.1), 0.022, 0.022, w["guard"], layer=9))
            P.append(cone(guard, tip, Wd, 0.008, w["blade"], layer=10))
            if w.get("glow_edge"):
                P.append(cone(guard + wd * 0.1, tip - wd * 0.05, Wd * 0.35, 0.004, w["glow_edge"], layer=11))
            del side
        elif wtype == "scythe":
            top = hand + v(0.1, 0.85, 0)
            P.append(cone(hand - v(0.08, 0.7, 0), top, 0.022, 0.022, w["shaft"], layer=9))
            for i in range(6):
                t0, t1 = i / 6, (i + 1) / 6
                a0 = top + v(-0.55 * t0, -0.1 * math.sin(t0 * 3.1) - 0.05 * t0, 0)
                a1 = top + v(-0.55 * t1, -0.1 * math.sin(t1 * 3.1) - 0.05 * t1, 0)
                P.append(cone(a0, a1, 0.05 * (1 - t0) + 0.01, 0.05 * (1 - t1) + 0.008, w["blade"], layer=10, k=0.02))
        elif wtype == "orb":
            P.append(sphere(hand + v(0.05, 0.1, 0), 0.07 + 0.04 * p.glow, w["gem"], layer=10))
        elif wtype == "lantern":
            P.append(cone(hand, hand - v(0, 0.12, 0), 0.008, 0.008, "metal", layer=9))
            P.append(box(hand - v(0, 0.22, 0), (0.05, 0.07, 0.05), w["frame"], round_=0.01, layer=9))
            P.append(sphere(hand - v(0, 0.22, 0), 0.042 + 0.02 * p.glow, w["gem"], layer=10))
    if s.get("off_hand"):
        w2 = s["off_hand"]
        hand = J["hand_f"]
        if w2["type"] == "shield":
            P.append(ellipsoid(hand + v(0.08, 0.05, -0.04), (0.04, 0.24, 0.18), w2["mat"], layer=9))
            P.append(sphere(hand + v(0.12, 0.05, -0.04), 0.05, w2.get("boss", "metal"), layer=9, k=0.01))
        elif w2["type"] == "flame":
            P.append(sphere(hand + v(0.04, 0.08, 0), 0.06 + 0.05 * p.glow, w2["mat"], layer=10))

    if s.get("locket"):
        hand = J["hand_" + s.get("locket_hand", "f")]
        P.append(ellipsoid(hand + v(0.04, 0.035, 0.02), (0.03, 0.038, 0.014), s["locket"], layer=9))
        P.append(cone(hand + v(0.04, 0.07, 0.02), hand + v(0.0, -0.08, 0.03), 0.004, 0.004, s["locket"], layer=9))
    for (ox, oy, oz, a, b, r, m) in s.get("shards", []):
        base = J["sh_" + ("n" if oz > 0 else "f")] + v(ox, oy, 0)
        P.append(cone(base, base + v(a, b, oz * 0.6), r, r * 0.15, m, layer=13))
    # ---- aura motes for spirits / bosses (fixed by spec)
    for (ox, oy, oz, r, m) in s.get("motes", []):
        P.append(sphere(J["chest"] + v(ox, oy, oz), r, m, layer=12))

    # ---- character-specific parts (thunderbird, water column, thorns...)
    if s.get("extra"):
        P += s["extra"](J, p, b)

    # ---- death: tip backwards about the feet and sink
    if p.fall > 0 or p.sink > 0:
        pivot = v((J["foot_n"][0] + J["foot_f"][0]) / 2 - 0.2, 0, 0)
        M = rot_z(p.fall * 1.45)
        P = transform(P, M, pivot, v(-0.05 * p.fall, -p.fall * 0.05 - p.sink * 0.6, 0))
    return P


# ---------------------------------------------------------------- animations
def anim_idle(i, n=4):
    t = i / n * 2 * math.pi
    return Pose(bob=0.008 * math.sin(t), head=0.03 * math.sin(t + 1), arm_n=(0.2, 0.15, 0.55 + 0.05 * math.sin(t)),
                arm_f=(-0.05, 0.15, 0.3), cape=0.05 + 0.04 * math.sin(t), glow=0.3 + 0.2 * math.sin(t))


def anim_walk(i, n=6):
    t = i / n * 2 * math.pi
    s = math.sin(t)
    return Pose(bob=0.025 * abs(math.cos(t)) - 0.01, lean=0.08,
                leg_n=(0.42 * s, 0.35 * max(0, -math.cos(t + 0.6)) + 0.1), leg_f=(-0.42 * s, 0.35 * max(0, math.cos(t + 0.6)) + 0.1),
                arm_n=(0.2 - 0.15 * s, 0.12, 0.55), arm_f=(0.35 * s, 0.12, 0.3), cape=0.25 + 0.08 * s, glow=0.3)


def anim_attack(i, n=6):
    # wind up, strike, follow through, recover
    keys = [(-1.3, 1.2, -0.1), (-2.2, 1.5, -0.15), (-2.5, 0.6, -0.12), (0.9, 0.2, 0.2), (1.1, 0.25, 0.25), (0.4, 0.5, 0.05)]
    sw, el, lean = keys[i % len(keys)]
    return Pose(lean=lean, arm_n=(sw, 0.2, el), arm_f=(-0.3, 0.15, 0.4), leg_n=(0.3, 0.1), leg_f=(-0.25, 0.15),
                cape=0.2 + 0.1 * (i in (3, 4)), weapon=0.0)


def anim_cast(i, n=6):
    g = [0.2, 0.5, 0.8, 1.0, 1.0, 0.5][i % 6]
    raise_ = [0.6, 1.2, 1.9, 2.3, 2.3, 1.2][i % 6]
    return Pose(lean=-0.05, arm_n=(raise_, 0.25, 0.2), arm_f=(raise_ * 0.6, 0.35, 0.5), head=-0.15 * g,
                cape=0.15 + 0.2 * g, glow=g, leg_n=(0.15, 0.05), leg_f=(-0.15, 0.05))


def anim_hurt(i, n=2):
    return Pose(lean=-0.25 - 0.1 * i, head=-0.2, arm_n=(0.6, 0.4, 0.9), arm_f=(0.5, 0.4, 0.9), leg_n=(0.2, 0.2),
                leg_f=(-0.3, 0.1), cape=0.3)


def anim_death(i, n=6):
    f = [0.0, 0.12, 0.35, 0.65, 0.9, 1.0][i % 6]
    return Pose(lean=-0.3 * f, head=-0.3 * f, arm_n=(0.6 + f, 0.5, 0.6), arm_f=(0.8 + f, 0.5, 0.6),
                leg_n=(0.3 * f, 0.4 * f), leg_f=(0.1, 0.6 * f), fall=f * 0.95, cape=0.1)


ANIMS = {"idle": (anim_idle, 4), "walk": (anim_walk, 6), "attack": (anim_attack, 6), "cast": (anim_cast, 6),
         "hurt": (anim_hurt, 2), "death": (anim_death, 6)}
