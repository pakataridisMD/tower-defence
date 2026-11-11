"""The story cast: one entry per character, with materials, outfit, body and portrait framing.

Names and looks are placeholders until the lore is written; ids are stable so files can be swapped.
"""
from __future__ import annotations

import math

import numpy as np

from rig import Body, v
from sdf import Material, box, cone, ellipsoid, glow_mat, make_ramp, mat, rot_y, rot_z, sphere


def eye(col="2a2030"):
    return Material(make_ramp(col, 4), flat=1.0, rim=0)


def glow_eye(col):
    return glow_mat(col, flat=1.0)


CAST: dict[str, dict] = {}


def character(cid, **kw):
    CAST[cid] = kw
    return kw


# Oswin, the Grey Lantern: falls in the prologue (CIN-00), returns as the White Lantern (CIN-23).
character(
    "oswin_grey",
    title="Oswin, the Grey Lantern",
    role="Mentor. Falls at the Crack in the prologue; returns at dawn in the finale.",
    element="none",
    body=dict(height=1.85, bulk=0.92),
    mats=dict(
        skin=mat("c99a7c"),
        cloth=mat("7a7a7e", tex=0.08, tex_freq=50, tex_axis="y"),
        cloth2=mat("4a4a52"),
        hat=mat("6e6e74", tex=0.06, tex_freq=40, tex_axis="x"),
        band=mat("4a3a30"),
        cape=mat("5e5a5a", tex=0.08, tex_freq=40, tex_axis="y"),
        leather=mat("5a3a28"),
        belt=mat("4a3020"),
        metal=mat("c08a4a", spec=1.0),
        brass=mat("c8923e", spec=1.0),
        eye=eye(),
        hair=mat("dcd8d0", tex=0.18, tex_freq=220, tex_axis="y"),
        shaft=mat("6e4c35", tex=0.1, tex_freq=120, tex_axis="y"),
        lamp=glow_mat("ffc860"),
    ),
    spec=dict(hair="hair", beard="hair", beard_len=1.25, brows="hair", cape="cape", hat="hat", hat_band="band",
              robe=True, belt="belt", buckle="metal", wide_sleeves=True,
              weapon=dict(type="lantern_staff", shaft="shaft", gem="lamp", frame="brass")),
    portrait=dict(center=(0.02, 1.5, 0.0), scale=135, yaw=-1.15, pitch=0.12, bg=("1e1a22", "6a5040", "ffc860")),
    portrait_weapon=True,
    portrait_pose=dict(arm_n=(0.25, 0.6, 1.0), arm_f=(-0.05, 0.18, 0.25)),
    rim=(255, 200, 120),
)

character(
    "oswin_white",
    title="Oswin, the White Lantern",
    role="Oswin returned (CIN-23 onward). No hat; robes glow at the hems; the lantern burns white.",
    element="all",
    body=dict(height=1.9, bulk=0.95),
    mats=dict(
        skin=mat("dcb89e"),
        cloth=mat("e4dccc", tex=0.08, tex_freq=50, tex_axis="y", spread=0.75),
        cloth2=mat("c8c0b0"),
        hem=glow_mat("fff4d0"),
        cape=mat("d8cdb4", tex=0.08, tex_freq=40, tex_axis="y", spread=0.75),
        leather=mat("8a6a4a"),
        belt=mat("d8b060", spec=1.0),
        metal=mat("e8c060", spec=1.0),
        brass=mat("f0d070", spec=1.0),
        eye=glow_eye("fff0b0"),
        hair=mat("f6f4f0", tex=0.14, tex_freq=220, tex_axis="y", spread=0.42),
        shaft=mat("e6dcc4", tex=0.08, tex_freq=120, tex_axis="y"),
        lamp=glow_mat("ffffff"),
        s_fire=glow_mat("ff7a3a"), s_storm=glow_mat("9ad0ff"), s_nature=glow_mat("9ae04a"),
        s_water=glow_mat("4ad0d0"), s_earth=glow_mat("e8a030"), s_void=glow_mat("c070ff"),
    ),
    spec=dict(hair="hair", long_hair=True, beard="hair", beard_len=1.35, brows="hair", cape="cape", robe=True,
              belt="belt", buckle="metal", wide_sleeves=True, hem="hem",
              weapon=dict(type="lantern_staff", shaft="shaft", gem="lamp", frame="brass"),
              motes=[(0.1, 0.25, 0.45, 0.02, "s_fire"), (-0.3, 0.45, -0.35, 0.017, "s_storm"),
                     (0.2, -0.25, 0.42, 0.015, "s_nature"), (-0.25, 0.75, 0.3, 0.016, "s_water"),
                     (0.15, 0.05, -0.45, 0.014, "s_earth"), (-0.4, -0.1, 0.3, 0.015, "s_void")]),
    portrait=dict(center=(0.02, 1.5, 0.0), scale=135, yaw=-1.15, pitch=0.12, bg=("2a2a30", "a89870", "fff4d0")),
    portrait_weapon=True,
    portrait_pose=dict(arm_n=(0.25, 0.6, 1.0), arm_f=(-0.05, 0.18, 0.25)),
    rim=(255, 246, 210),
)

# Cassivane Dral, the Ashen Regent. Fatherly Lord Marshal before the midpoint.
_cass_common = dict(torso="enamel", armour="enamel", pauldron="steel", greaves=True, legs="cloth2", boots="steel",
                    sleeve="cloth2", forearm="steel", hands="steel", cape="cape", hair="hair", beard="hair",
                    beard_len=0.12, brows="hair", belt="belt", buckle="gold", locket="gold", gorget="steel", trim="gold",
                    collar="cape",
                    weapon=dict(type="sword", blade="blade", guard="gold", grip="leather"))
character(
    "cassivane",
    title="Cassivane Dral, Lord Marshal",
    role="The Regent before the midpoint: calm, fatherly, always holding a gold locket.",
    element="fire",
    body=dict(height=1.95, bulk=1.12, shoulder=0.24, chest_depth=1.05),
    mats=dict(
        skin=mat("c08c70"),
        cloth=mat("8a2a2a"),
        cloth2=mat("3a3038"),
        enamel=mat("a8282a", spec=1.0, spread=0.55),
        steel=mat("a8acb8", spec=1.0),
        cape=mat("9a2224", tex=0.07, tex_freq=36, tex_axis="y"),
        leather=mat("3a2a26"),
        belt=mat("3a2a26"),
        gold=mat("e0b040", spec=1.0),
        blade=mat("c8ccd8", spec=1.0),
        eye=eye("3a3040"),
        hair=mat("8a8a90", tex=0.15, tex_freq=200, tex_axis="x"),
    ),
    spec=dict(_cass_common),
    portrait=dict(center=(0.02, 1.6, 0.0), scale=128, yaw=-1.1, pitch=0.1, bg=("1e1216", "6a2020", "e0b040")),
    portrait_pose=dict(arm_n=(0.45, 0.05, 1.9), arm_f=(0.05, 0.18, 0.25)),
    portrait_spec=dict(locket_hand="n"),
    rim=(255, 190, 120),
)

character(
    "cassivane_ashen",
    title="Cassivane Dral, the Ashen Regent",
    role="After the midpoint: armour burned like paper, Heartstone shards from his shoulders, eyes grey.",
    element="void",
    body=dict(height=1.95, bulk=1.12, shoulder=0.24, chest_depth=1.05),
    mats=dict(
        skin=mat("8a8288"),
        cloth=mat("2a2228"),
        cloth2=mat("221c22"),
        enamel=mat("2e2626", spec=0.5, tex=0.22, tex_freq=140),
        steel=mat("4a4448", spec=0.6, tex=0.18, tex_freq=140),
        cape=mat("2a2224", tex=0.12, tex_freq=36, tex_axis="y"),
        leather=mat("221a1a"),
        belt=mat("221a1a"),
        gold=mat("d0a040", spec=1.0),
        blade=mat("5a5060", spec=1.0),
        eye=glow_eye("d8d8e0"),
        hair=mat("b8b4b8", tex=0.15, tex_freq=200, tex_axis="x"),
        shard_a=glow_mat("ff7a3a"), shard_b=glow_mat("c070ff"), shard_c=glow_mat("9ad0ff"),
        ash=glow_mat("ff9a50"),
    ),
    spec=dict(_cass_common, cape_tatter=True,
              shards=[(0.0, 0.05, 0.08, -0.06, 0.24, 0.045, "shard_a"), (-0.05, 0.02, 0.06, -0.16, 0.16, 0.035, "shard_b"),
                      (0.0, 0.05, -0.08, -0.04, 0.22, 0.04, "shard_c"), (-0.06, 0.0, -0.06, -0.15, 0.14, 0.03, "shard_b")],
              motes=[(-0.2, 0.5, 0.1, 0.012, "ash"), (-0.35, 0.3, -0.1, 0.01, "ash"), (-0.15, 0.75, 0.0, 0.009, "ash")]),
    portrait=dict(center=(0.02, 1.62, 0.0), scale=120, yaw=-1.1, pitch=0.1, bg=("101014", "3a2a3a", "c070ff")),
    portrait_pose=dict(arm_n=(0.45, 0.05, 1.9), arm_f=(0.05, 0.18, 0.25)),
    portrait_spec=dict(locket_hand="n"),
    rim=(210, 160, 255),
)


# Queen Ysolde of Solenne, the narrator.
character(
    "ysolde",
    title="Queen Ysolde of Solenne",
    role="Narrator and ally. White and gold gown, six-point silver circlet, a single long dark braid.",
    element="all",
    body=dict(height=1.7, bulk=0.78, shoulder=0.19, head_r=0.122),
    mats=dict(
        skin=mat("d8b096"), cloth=mat("ece4d4", tex=0.06, tex_freq=50, tex_axis="y", spread=0.7),
        cloth2=mat("c8b890"), gold=mat("e0b040", spec=1.0), silver=mat("d0d4e0", spec=1.0),
        mail=mat("b8a8c8", spec=0.8, tex=0.25, tex_freq=160), leather=mat("8a6a4a"), belt=mat("e0b040", spec=1.0),
        hair=mat("3a2a2c", tex=0.2, tex_freq=200, tex_axis="y", spread=0.35), eye=eye("2a2030"),
        cape=mat("d8ccb0", tex=0.06, tex_freq=40, tex_axis="y"),
    ),
    spec=dict(hair="hair", long_hair=True, brows="hair", robe=True, belt="belt", buckle="gold", collar="mail",
              circlet6="silver", sleeve="cloth", wide_sleeves=True, gorget="mail", jaw=0.72),
    portrait=dict(center=(0.03, 1.5, 0.0), scale=165, yaw=-1.2, pitch=0.08, bg=("141018", "6a5a3a", "fff0c0")),
    portrait_pose=dict(arm_n=(0.45, 0.1, 1.4), arm_f=(0.45, 0.1, 1.4)),
    rim=(255, 236, 190),
)

def _blindfold(J, p, b):
    hr = J["head_r"]
    return [ellipsoid(J["head"] + v(hr * 0.1, hr * 0.02, 0), (hr * 1.08, hr * 0.24, hr * 1.0), "blindfold", layer=8),
            ellipsoid(J["head"] + v(hr * 1.06, hr * 0.02, 0), (hr * 0.05, hr * 0.06, hr * 0.5), "gold", layer=9)]


character(
    "ysolde_blind",
    title="Queen Ysolde, after the Night of Falling Stars",
    role="Blinded by the falling Sunstone: gold-embroidered black cloth over her eyes, braid cut short, a grey soldier's "
         "cloak, Fennick's brass measuring rod as a staff.",
    element="all",
    body=dict(height=1.7, bulk=0.78, shoulder=0.19, head_r=0.122),
    mats=dict(CAST["ysolde"]["mats"], cape=mat("6a6a70", tex=0.08, tex_freq=40, tex_axis="y"), blindfold=mat("1a1418"),
              rod=mat("c8923e", spec=1.0), tip=mat("e8c060", spec=1.0)),
    spec=dict(hair="hair", brows="hair", robe=True, belt="belt", buckle="gold", collar="cape", cape="cape",
              circlet6="silver", sleeve="cloth", wide_sleeves=True, jaw=0.72, extra=_blindfold,
              weapon=dict(type="staff", shaft="rod", gem="tip", above=0.7, below=0.85)),
    portrait=dict(center=(0.03, 1.47, 0.0), scale=140, yaw=-1.2, pitch=0.08, bg=("101014", "4a4a5a", "fff0c0")),
    rim=(255, 236, 190),
)


character(
    "tamsin",
    title="Tamsin Reed, Captain of the Lanternguard",
    role="Starting hero. Dented half-plate over a faded blue tabard, a war-lantern on a pole she uses as a spear.",
    element="none",
    body=dict(height=1.62, bulk=0.95, head_r=0.12),
    mats=dict(
        skin=mat("d0a080"), cloth=mat("3e5a86", tex=0.08, tex_freq=40, tex_axis="y"), cloth2=mat("3a3a44"),
        steel=mat("9ca0ac", spec=1.0, tex=0.06, tex_freq=90), leather=mat("4a3424"), belt=mat("4a3424"),
        gold=mat("e0b040", spec=1.0), hair=mat("b8502a", tex=0.18, tex_freq=200, tex_axis="x"), eye=eye(),
        shaft=mat("5a4030", tex=0.1, tex_freq=120, tex_axis="y"), brass=mat("c8923e", spec=1.0), lamp=glow_mat("ffd070"),
    ),
    spec=dict(hair="hair", brows="hair", jaw=0.85, torso="steel", armour="steel", pauldron="steel", tabard="cloth", legs="cloth2",
              boots="leather", sleeve="cloth", forearm="steel", hands="leather", belt="belt", buckle="gold", trim="gold",
              weapon=dict(type="lantern_staff", shaft="shaft", gem="lamp", frame="brass")),
    portrait=dict(center=(0.03, 1.38, 0.0), scale=160, yaw=-1.15, pitch=0.1, bg=("101420", "2e4a7a", "ffd070")),
    portrait_weapon=True,
    portrait_pose=dict(arm_n=(0.25, 0.6, 1.0)),
    rim=(255, 220, 150),
)


# Master Tobias Fennick, Chief Tower-Wright. Briefings for stages 1-12; dies holding the Dawn Gate.
def _fennick_parts(J, p, b):
    hr = J["head_r"]
    out = []
    for s in (1, -1):  # magnifying spectacles pushed up on the head
        c = J["head"] + v(hr * 0.45, hr * 0.85, s * hr * 0.35)
        out.append(ellipsoid(c, (hr * 0.08, hr * 0.3, hr * 0.3), "brass", layer=7, rot=rot_z(-0.6)))
        out.append(ellipsoid(c + v(hr * 0.05, hr * 0.04, 0), (hr * 0.06, hr * 0.22, hr * 0.22), "lens", layer=8, rot=rot_z(-0.6)))
        # huge white side-whiskers
        out.append(ellipsoid(J["head"] + v(hr * 0.35, -hr * 0.45, s * hr * 0.78), (hr * 0.4, hr * 0.55, hr * 0.32), "whisker",
                             layer=4, k=hr * 0.1, disp=(hr * 0.06, 120, "y", 51)))
    for k in range(4):  # brass buttons on the waistcoat
        out.append(sphere(J["chest"] + v(0.15 * b.bulk, 0.1 - k * 0.07, 0), 0.016, "brass", layer=3))
    out.append(ellipsoid(J["pelvis"] + v(0.0, 0.1, 0), (0.15 * b.bulk, 0.035, 0.18 * b.bulk), "belt", layer=3))
    for k in range(5):  # chalk and calipers in the tool belt
        a = -1.0 + k * 0.5
        base = J["pelvis"] + v(math.cos(a) * 0.16 * b.bulk, 0.12, math.sin(a) * 0.18 * b.bulk)
        out.append(cone(base, base + v(0, 0.07, 0), 0.012, 0.01, "chalk" if k % 2 else "brass", layer=3))
    return out


character(
    "fennick",
    title="Master Tobias Fennick, Chief Tower-Wright",
    role="Briefings for stages 1-12. Dies holding the Dawn Gate on the Night of Falling Stars.",
    element="none",
    body=dict(height=1.5, bulk=1.35, head_r=0.13, chest_depth=1.25),
    mats=dict(
        skin=mat("d88a70"), cloth=mat("e8e0cc", tex=0.06, tex_freq=50, tex_axis="y"), cloth2=mat("4a3a30"),
        vest=mat("6a3a28", tex=0.08, tex_freq=60), leather=mat("3a2a20"), belt=mat("5a3a24"), brass=mat("d8a040", spec=1.0),
        lens=mat("a8d8e8", spec=1.0), whisker=mat("ece8e0", tex=0.2, tex_freq=200, tex_axis="y"), chalk=mat("f0f0e8"),
        eye=eye(), hair=mat("ece8e0"), metal=mat("d8a040", spec=1.0), rod=mat("c8923e", spec=1.0), tip=mat("e8c060", spec=1.0),
    ),
    spec=dict(torso="vest", sleeve="cloth", forearm="cloth", legs="cloth2", brows="whisker", extra=_fennick_parts,
              weapon=dict(type="staff", shaft="rod", gem="tip", above=0.45, below=0.5)),
    portrait=dict(center=(0.03, 1.2, 0.0), scale=135, yaw=-1.15, pitch=0.1, bg=("1a1410", "6a4a2a", "ffd070")),
    rim=(255, 210, 150),
)

# A Lanternguard soldier, hollowed (grey empty eyes) on the Night of Falling Stars.
character(
    "lanternguard_hollow",
    title="Hollowed Lanternguard",
    role="Solenne's guards whose eyes went grey: they open the east gate.",
    element="none",
    body=dict(height=1.75, bulk=1.0),
    mats=dict(
        skin=mat("a8a0a0"), cloth=mat("3e5a86", tex=0.08, tex_freq=40, tex_axis="y"), cloth2=mat("2e3038"),
        steel=mat("8a8e9a", spec=1.0, tex=0.06, tex_freq=90), leather=mat("3a2a20"), belt=mat("3a2a20"),
        gold=mat("c8a040", spec=1.0), eye=glow_eye("dcdce6"), visor=glow_mat("dcdce6"),
        shaft=mat("4a3a2a"), blade=mat("b8bcc8", spec=1.0),
    ),
    spec=dict(torso="steel", armour="steel", pauldron="steel", tabard="cloth", legs="cloth2", boots="leather",
              sleeve="cloth", forearm="steel", hands="leather", belt="belt", buckle="gold", helm="steel", helm_glow="visor",
              weapon=dict(type="staff", shaft="shaft", gem="blade", above=0.9, below=0.8)),
    portrait=dict(center=(0.03, 1.5, 0.0), scale=150, yaw=-1.15, pitch=0.1, bg=("101420", "2e3a5a", "dcdce6")),
    rim=(200, 210, 240),
)


# Nyxara of the Hollow, Void Warden: a starfield where her face should be, a black train of slow stars.
def _nyxara_parts(J, p, b):
    out = []
    hr = J["head_r"]
    out.append(ellipsoid(J["head"] + v(hr * 0.55, -hr * 0.05, 0), (hr * 0.5, hr * 0.85, hr * 0.7), "starface", layer=3))
    rs = np.random.default_rng(62)
    for k in range(9):
        out.append(sphere(J["head"] + v(hr * 1.0, rs.uniform(-0.6, 0.6) * hr, rs.uniform(-0.45, 0.45) * hr),
                          hr * rs.uniform(0.04, 0.08), "star", layer=15))
    # long train behind her
    out.append(cone(J["pelvis"] + v(-0.1, 0.0, 0), v(J["pelvis"][0] - 0.9 - 0.3 * p.cape, 0.04, 0), 0.22, 0.35, "train",
                    layer=1, disp=(0.02, 18, "y", 61)))
    rng = np.random.default_rng(61)
    for k in range(10):
        t = rng.random()
        out.append(sphere(v(J["pelvis"][0] - 0.1 - 0.85 * t, 0.06 + 0.4 * (1 - t) * rng.random(), rng.uniform(-0.25, 0.25)),
                          0.012, "star", layer=14))
    # the broken iron crown in her far hand
    hand = J["hand_f"]
    for k in range(5):
        a = k * 1.1
        out.append(cone(hand + v(math.cos(a) * 0.07, 0.0, math.sin(a) * 0.07),
                        hand + v(math.cos(a) * 0.07, 0.05 + 0.03 * (k % 2), math.sin(a) * 0.07), 0.012, 0.004, "iron", layer=9))
    out.append(ellipsoid(hand + v(0, -0.005, 0), (0.075, 0.012, 0.075), "iron", layer=9))
    return out


character(
    "nyxara",
    title="Nyxara of the Hollow",
    role="Void Warden. Freed after the Hollow King; walks beside Oswin at dawn.",
    element="void",
    body=dict(height=2.5, bulk=0.82, shoulder=0.2, head_r=0.13),
    mats=dict(
        skin=mat("2a2440", spread=0.35), cloth=mat("1e1834", tex=0.12, tex_freq=40, tex_axis="y", spread=0.35),
        cloth2=mat("100c1a", spread=0.3), leather=mat("100c1a", spread=0.3),
        train=mat("161226", tex=0.12, tex_freq=30, tex_axis="y", spread=0.35), starface=Material(make_ramp("0c0a1e", 4, 0.3), flat=1.0, rim=0),
        star=glow_mat("e8e0ff"), iron=mat("5a5660", spec=0.8), eye=glow_eye("e8e0ff"), hair=mat("1a1428"),
    ),
    spec=dict(robe=True, wide_sleeves=True, hood="cloth", face=False, extra=_nyxara_parts, crown=None,
              motes=[(0.2, 0.6, 0.1, 0.012, "star"), (-0.3, 0.3, -0.1, 0.01, "star"), (0.1, 0.9, -0.2, 0.011, "star"),
                     (0.4, 0.2, 0.2, 0.009, "star")]),
    portrait=dict(center=(0.03, 2.1, 0.0), scale=120, yaw=-1.15, pitch=0.1, bg=("06040e", "2a1a4a", "c8a8ff")),
    sprite_scale=28.0, frame=(80, 96), frame_cy=1.3,
    rim=(200, 170, 255),
)


def _ilyra_parts(J, p, b):
    hand = J["hand_n"]
    out = [cone(J["neck"] + v(0.12, -0.02, 0), hand + v(0.0, -0.04, 0), 0.004, 0.004, "brass", layer=9)]
    c = hand + v(0.03, -0.1, 0)
    out.append(ellipsoid(c, (0.012, 0.06, 0.06), "brass", layer=9))
    out.append(ellipsoid(c, (0.014, 0.045, 0.045), "astro", sub=True, layer=9))
    out.append(cone(c + v(0, 0.05, -0.04), c + v(0, -0.05, 0.04), 0.006, 0.006, "brass", layer=9))
    out.append(sphere(c, 0.012, "spark", layer=10))
    return out


character(
    "ilyra",
    title="Ilyra the Unbroken",
    role="Cassivane's daughter. Found as a captive at the crossroads; white hair, a broken astrolabe on a chain.",
    element="void+storm",
    body=dict(height=1.62, bulk=0.72, shoulder=0.18, head_r=0.12),
    mats=dict(
        skin=mat("d8c0b8"), cloth=mat("1e2a4a", tex=0.12, tex_freq=50, tex_axis="y"), cloth2=mat("161e30"),
        leather=mat("2a2228"), belt=mat("2a2228"), metal=mat("8a8aa0", spec=1.0), brass=mat("c8a050", spec=1.0),
        astro=mat("c8a050"), spark=glow_mat("c8e0ff"), hair=mat("eceaf0", tex=0.2, tex_freq=200, tex_axis="y", spread=0.4),
        eye=eye("3a3a5a"), veins=glow_mat("9ad0ff"),
    ),
    spec=dict(hair="hair", long_hair=True, brows="hair", jaw=0.7, robe=True, cape="cloth", cape_tatter=True,
              belt="belt", buckle="metal", sleeve="skin", forearm="skin", extra=_ilyra_parts),
    portrait=dict(center=(0.03, 1.42, 0.0), scale=165, yaw=-1.15, pitch=0.1, bg=("0a0c1a", "2a2a5a", "9ad0ff")),
    rim=(170, 200, 255),
)

character(
    "corvin",
    title="Corvin the Uncrowned, Ranger-King of the Rift",
    role="Void hero. Hooded ranger, silver hair, a curved black-glass blade that shows stars.",
    element="void",
    body=dict(height=1.88, bulk=0.9),
    mats=dict(
        skin=mat("c09478"), cloth=mat("2a2236", tex=0.1, tex_freq=40, tex_axis="y", spread=0.4), cloth2=mat("2a2434", spread=0.4),
        hood=mat("342a48", tex=0.1, tex_freq=40, tex_axis="y", spread=0.4),
        cape=mat("342a48", tex=0.1, tex_freq=40, tex_axis="y", spread=0.4),
        leather=mat("3a2a24"), belt=mat("3a2a24"), metal=mat("a8a8c0", spec=1.0), hair=mat("c8c8d4", tex=0.18, tex_freq=200),
        eye=eye(), blade=mat("100c1a", spec=1.0, tex=0.0), edge=glow_mat("c8b0ff"), guard=mat("6a6080", spec=1.0),
    ),
    spec=dict(hair="hair", brows="hair", hood="hood", cape="cape", belt="belt", buckle="metal",
              torso="cloth", sleeve="cloth", legs="cloth2", boots="leather",
              weapon=dict(type="sword", blade="blade", guard="guard", glow_edge="edge", grip="leather")),
    portrait=dict(center=(0.03, 1.6, 0.0), scale=150, yaw=-1.15, pitch=0.1, bg=("08060e", "2a1a3a", "c8b0ff")),
    portrait_spec=dict(hood=None, collar="hood"),
    rim=(200, 170, 255),
)


# ---------------------------------------------------------------- the six Heralds (stage-2 bosses)
# Shared motif: faces intact but eyes (and mouths) empty grey light; outlines leak grey dust.
HERALD_EYE = glow_eye("dcdce6")
DUST = glow_mat("b8b8c4")


def _dust(n=5, spread=0.5, seed=0):
    rng = np.random.default_rng(seed)
    return [(float(rng.uniform(-spread, spread * 0.4)), float(rng.uniform(-0.2, spread * 1.4)), float(rng.uniform(-0.3, 0.3)),
             float(rng.uniform(0.008, 0.016)), "dust") for _ in range(n)]


def _open_mouth(J, p, b):
    hr = J["head_r"]
    face = J["head"] + v(hr * 0.9, -hr * 0.62, 0)
    return [ellipsoid(face, (hr * 0.1, hr * 0.13, hr * 0.13), "mouth", layer=3)]


def _ourra_column(J, p, b):
    """The 4 m column of black seawater that walks with her, with fish and drowned lanterns inside."""
    out = []
    base = v(J["pelvis"][0] * 0.5, 0.0, 0)
    out.append(cone(base + v(0, 0.05, 0), base + v(0, 2.45, 0), 0.62, 0.48, "seawater", layer=100,
                    disp=(0.04, 9.0, "y", 21)))
    out.append(ellipsoid(base + v(0, 2.5, 0), (0.5, 0.18, 0.5), "foam", layer=100, disp=(0.03, 14.0, "", 22)))
    t = p.bob * 30 + p.lean
    for i, (a, y, r) in enumerate(((0.3, 0.6, 0.4), (2.2, 1.3, 0.45), (4.1, 1.9, 0.38), (5.3, 0.9, 0.42))):
        a += t * 0.5
        c = base + v(math.cos(a) * r, y, math.sin(a) * r)
        out.append(ellipsoid(c, (0.07, 0.03, 0.03), "fish", layer=14, rot=rot_y(-a)))
        out.append(cone(c - rot_y(-a) @ v(0.07, 0, 0), c - rot_y(-a) @ v(0.12, 0, 0), 0.006, 0.025, "fish", layer=14))
    for i, (a, y) in enumerate(((1.2, 1.6), (3.6, 0.5), (5.0, 2.1))):
        c = base + v(math.cos(a + t * 0.3) * 0.36, y, math.sin(a + t * 0.3) * 0.36)
        out.append(box(c, (0.03, 0.045, 0.03), "bronze", round_=0.008, layer=14))
        out.append(sphere(c, 0.022, "drowned_light", layer=15))
    return out + _open_mouth(J, p, b)


character(
    "herald_ourra",
    title="Saltmother Ourra, the Drowned Herald",
    role="Water Herald. Boss of Ember 2 (Cinder Steps).",
    element="water",
    body=dict(height=1.7, bulk=0.9),
    mats=dict(
        skin=mat("8aa0a0"), cloth=mat("2a6a6e", tex=0.1, tex_freq=40, tex_axis="y"), cloth2=mat("1e3a40"),
        hood=mat("2a6a6e", tex=0.1, tex_freq=40, tex_axis="y"), cape=mat("1e4a50", tex=0.1, tex_freq=40, tex_axis="y"),
        leather=mat("2a2a2a"), belt=mat("6a5a3a"), metal=mat("8a7040", spec=1.0), eye=HERALD_EYE, mouth=HERALD_EYE,
        hair=mat("9aa4a8", tex=0.22, tex_freq=200, tex_axis="y"), dust=DUST,
        seawater=mat("16303e", spec=1.0, tex=0.15, tex_freq=12, tex_axis="y", spread=0.5), foam=mat("a8d8e0", spread=0.4),
        fish=mat("8ab0b8", spec=1.0), bronze=mat("8a6a3a", spec=1.0), drowned_light=glow_mat("6ae0d0"),
    ),
    spec=dict(hair="hair", long_hair=True, brows="hair", robe=True, cape="cape", cape_tatter=True, wide_sleeves=True,
              belt="belt", buckle="metal", extra=_ourra_column, motes=_dust(5, 0.5, 1), collar="cape"),
    portrait=dict(center=(0.04, 1.42, 0.0), scale=150, yaw=-1.15, pitch=0.1, bg=("06141a", "1e4a50", "6ae0d0")),
    portrait_spec=dict(extra=_open_mouth),
    portrait_pose=dict(arm_n=(0.9, 0.3, 0.9), arm_f=(0.7, 0.3, 1.0)),
    frame=(104, 128), frame_cy=1.3, sprite_scale=36.0,
    rim=(120, 230, 220),
)


def _gorrath_parts(J, p, b):
    out = []
    ch = J["chest"]
    # the square hole in his chest, and the carved stone where his heart was
    out.append(box(ch + v(0.2, 0.0, 0.04), (0.16, 0.1, 0.1), "rock", sub=True, layer=2, round_=0.01))
    out.append(box(ch + v(0.2, 0.0, 0.04), (0.16, 0.1, 0.1), "rock", sub=True, layer=0, round_=0.01))
    out.append(box(ch + v(0.08, 0.0, 0.04), (0.05, 0.05, 0.05), "heartstone", round_=0.01, layer=14,
                   rot=rot_y(0.6) @ rot_z(0.5)))
    for i in range(5):  # boulder knuckles and growths on the shoulders
        a = i * 1.3
        out.append(sphere(J["sh_n" if i % 2 else "sh_f"] + v(-0.05 + 0.03 * math.cos(a), 0.06 + 0.02 * i % 3, 0.03 * math.sin(a)),
                          0.05, "rock", k=0.03))
    return out + _open_mouth(J, p, b)


character(
    "herald_gorrath",
    title="Gorrath the Quarried, the Stone Herald",
    role="Earth Herald. Boss of Storm 2 (Galeback Ridge). Breaks into walking boulders.",
    element="earth",
    body=dict(height=2.3, bulk=1.6, shoulder=0.3, chest_depth=1.15, head_r=0.12),
    mats=dict(
        skin=mat("6e6258", tex=0.18, tex_freq=60), rock=mat("6e5e4e", tex=0.22, tex_freq=55),
        armour=mat("5e4636", spec=0.4, tex=0.22, tex_freq=55), cloth=mat("5a4a3a"), cloth2=mat("4a3e34", tex=0.15, tex_freq=60),
        leather=mat("4a3e34", tex=0.15, tex_freq=60), belt=mat("3a2e24"), metal=mat("a07040", spec=1.0),
        eye=HERALD_EYE, mouth=HERALD_EYE, dust=DUST, heartstone=mat("a89a88", tex=0.2, tex_freq=90),
    ),
    spec=dict(torso="rock", armour="armour", pauldron="armour", greaves=True, legs="rock", boots="rock", sleeve="rock",
              forearm="armour", hands="rock", helm=None, belt="belt", buckle="metal", brows="rock",
              extra=_gorrath_parts, motes=_dust(6, 0.6, 2),
              weapon=dict(type="greatsword", blade="rock", guard="armour", grip="leather")),
    portrait=dict(center=(0.06, 1.95, 0.0), scale=120, yaw=-1.0, pitch=0.1, bg=("140e0a", "5a3a22", "e8a030")),
    frame=(96, 112), frame_cy=1.15, sprite_scale=38.0,
    rim=(255, 190, 110),
)


def _vesper_parts(J, p, b):
    out = _open_mouth(J, p, b)
    hr = J["head_r"]
    # a long mourning veil from the crown down the back
    out.append(cone(J["head"] + v(-hr * 0.6, hr * 0.5, 0), v(J["pelvis"][0] - 0.4 - 0.2 * p.cape, 0.2, 0), hr * 1.0, 0.3,
                    "veil", layer=1, disp=(0.03, 18, "y", 31)))
    rng = np.random.default_rng(5)
    for i in range(7):  # the ghost choir
        a = i / 7 * 2 * math.pi + p.bob * 25
        c = J["chest"] + v(-0.2 + 0.45 * math.cos(a), 0.1 + 0.35 * math.sin(a * 1.7) + 0.2 * rng.random(), 0.45 * math.sin(a))
        out.append(sphere(c, 0.022 + 0.008 * (i % 3), "ghost", layer=15))
    return out


character(
    "herald_vesper",
    title="The Pale Vesper, the Hollow Herald",
    role="Void Herald. Boss of Nature 2 (Rootway). Sings; a choir of ghost-lights follows.",
    element="void",
    body=dict(height=2.25, bulk=0.75, shoulder=0.19),
    mats=dict(
        skin=mat("c8b8c8"), cloth=mat("4a4652", tex=0.1, tex_freq=40, tex_axis="y"), cloth2=mat("3a3640"),
        hood=mat("4e4a58", tex=0.1, tex_freq=40, tex_axis="y"), veil=mat("9a96a4", tex=0.1, tex_freq=30, tex_axis="y"),
        leather=mat("3a3640"), belt=mat("3a3640"), metal=mat("8a80a0", spec=1.0), eye=HERALD_EYE, mouth=HERALD_EYE,
        dust=DUST, ghost=glow_mat("c8a8ff"), hair=mat("3a3640"),
    ),
    spec=dict(hood="hood", robe=True, wide_sleeves=True, belt="belt", buckle="metal", extra=_vesper_parts, jaw=0.75,
              motes=_dust(5, 0.5, 3)),
    portrait=dict(center=(0.04, 1.86, 0.0), scale=125, yaw=-1.05, pitch=0.12, bg=("100c18", "3a2a5a", "c8a8ff")),
    portrait_pose=dict(arm_n=(1.4, 0.35, 0.7), arm_f=(1.2, 0.35, 0.8), head=-0.25),
    frame=(88, 112), frame_cy=1.18, sprite_scale=36.0,
    rim=(200, 170, 255),
)


def _ashwick_parts(J, p, b):
    out = []
    # the messenger's satchel, still on his shoulder
    sh = J["sh_f"]
    out.append(cone(sh + v(0.02, 0.03, 0), J["pelvis"] + v(0.0, 0.05, 0.16), 0.012, 0.012, "strap", layer=2))
    out.append(box(J["pelvis"] + v(-0.02, 0.02, 0.17), (0.08, 0.065, 0.03), "satchel", round_=0.02, layer=2))
    # flame streaming behind like a cape
    for i in range(6):
        t = i / 5
        c = J["neck"] + v(-0.12 - 0.5 * t - 0.25 * p.cape, -0.1 - 0.35 * t + 0.05 * math.sin(i * 2 + p.bob * 40), 0.12 * math.sin(i * 1.7))
        out.append(sphere(c, 0.11 * (1 - t * 0.7), "flame" if i < 3 else "flame2", layer=16))
    hr = J["head_r"]
    for i in range(7):
        a = -1.3 + i * 0.43
        base = J["head"] + v(-hr * 0.2 + math.cos(a) * hr * 0.3, hr * 0.6, math.sin(a) * hr * 0.75)
        out.append(cone(base, base + v(-hr * (0.6 + 0.3 * (i % 2)) - 0.1 * p.cape, hr * (0.8 + 0.4 * (i % 3 == 1)), 0),
                        hr * 0.32, hr * 0.04, "flame" if i % 2 else "flame2", layer=16))
    for i in range(6):  # ember cracks across the skin
        a = i * 1.1
        out.append(cone(J["chest"] + v(0.12, 0.1 - i * 0.04, 0.12 * math.sin(a)), J["chest"] + v(0.13, 0.06 - i * 0.04,
                        0.12 * math.sin(a) + 0.05), 0.008, 0.008, "crack", layer=3))
    return out + _open_mouth(J, p, b)


character(
    "herald_ashwick",
    title="Ashwick the Kindled, the Flame Herald",
    role="Fire Herald. Boss of Water 2 (Saltmarsh Bends). A messenger boy of white-hot embers.",
    element="fire",
    body=dict(height=1.5, bulk=0.85, head_r=0.125),
    mats=dict(
        skin=mat("3a2420", tex=0.3, tex_freq=70), cloth=glow_mat("e86a2a", tex=0.25, tex_freq=60),
        cloth2=mat("3a1a14", tex=0.25, tex_freq=70), leather=mat("2a1410", tex=0.2, tex_freq=70),
        hair=glow_mat("fff0b0", tex=0.3, tex_freq=150, tex_axis="y"), eye=HERALD_EYE, mouth=HERALD_EYE, dust=DUST,
        strap=mat("5a3a24"), satchel=mat("6a4a2a", tex=0.1, tex_freq=50), flame=glow_mat("ffa040"), flame2=glow_mat("e85a20"),
        belt=mat("3a2014"), metal=mat("c08a4a", spec=1.0), crack=glow_mat("fff0b0"),
    ),
    spec=dict(torso="cloth2", sleeve="cloth2", forearm="cloth", hands="cloth", legs="cloth2", boots="cloth",
              extra=_ashwick_parts,
              motes=_dust(4, 0.4, 4)),
    portrait=dict(center=(0.02, 1.25, 0.0), scale=150, yaw=-1.1, pitch=0.1, bg=("1a0a06", "6a2a10", "ffb060")),
    sprite_scale=36.0,
    rim=(255, 220, 160),
)


def _vholt_parts(J, p, b):
    """Rides a thunderbird of black cloud: body under him, wings out, white-hot eyes."""
    out = []
    flap = math.sin(p.bob * 60 + p.lean * 4) * 0.35
    body_c = J["pelvis"] + v(0.0, -0.25, 0)
    out.append(ellipsoid(body_c, (0.55, 0.26, 0.3), "stormcloud", k=0.0, layer=20, disp=(0.04, 14, "", 41)))
    head = body_c + v(0.62, 0.25, 0)
    out.append(cone(body_c + v(0.35, 0.05, 0), head, 0.2, 0.13, "stormcloud", k=0.1, layer=20, disp=(0.03, 16, "", 42)))
    out.append(cone(head + v(0.08, 0.0, 0), head + v(0.3, -0.08, 0), 0.06, 0.01, "beak", layer=20, k=0.02))
    for s in (1, -1):
        out.append(sphere(head + v(0.06, 0.04, s * 0.09), 0.03, "boltlight", layer=21))
        root = body_c + v(0.05, 0.12, s * 0.22)
        tip = root + v(-0.45, 0.35 + flap * s * 0 + flap, s * 0.85)
        out.append(cone(root, tip, 0.18, 0.04, "stormcloud", layer=20, k=0.08, disp=(0.04, 14, "", 43)))
        out.append(cone(tip, tip + v(-0.35, -0.15, s * 0.25), 0.05, 0.01, "stormcloud", layer=20, k=0.05))
    out.append(cone(body_c - v(0.45, 0, 0), body_c - v(0.95, 0.1, 0), 0.18, 0.05, "stormcloud", layer=20, k=0.1,
                    disp=(0.04, 14, "", 44)))
    out.append(cone(body_c + v(0.1, -0.2, 0), body_c + v(0.25, -0.62, 0), 0.04, 0.02, "boltlight", layer=21))
    # lightning crown
    hr = J["head_r"]
    for i in range(5):
        a = -1.2 + i * 0.6
        base = J["head"] + v(math.cos(a) * hr * 0.6, hr * 0.85, math.sin(a) * hr * 0.9)
        out.append(cone(base, base + v(0.01, hr * (0.7 + 0.3 * (i % 2)), 0), hr * 0.12, hr * 0.03, "boltlight", layer=22))
    return out + _open_mouth(J, p, b)


character(
    "herald_vholt",
    title="Vholt Stormcrown, the Sky Herald",
    role="Storm Herald. Boss of Earth 2 (Canyon Switchbacks). Rides a thunderbird of black cloud.",
    element="storm",
    body=dict(height=1.8, bulk=1.1),
    mats=dict(
        skin=mat("a08a78"), cloth=mat("4a5a7a", tex=0.08, tex_freq=40, tex_axis="y"), cloth2=mat("2e3648"),
        cape=mat("3a4a6a", tex=0.08, tex_freq=40, tex_axis="y"), leather=mat("3a2e2a"), belt=mat("3a2e2a"),
        metal=mat("9aa0b8", spec=1.0), hair=mat("d0d4dc", tex=0.18, tex_freq=200, tex_axis="y"), eye=HERALD_EYE,
        mouth=HERALD_EYE, dust=DUST, stormcloud=mat("2a2a38", tex=0.18, tex_freq=22, spread=0.5),
        beak=mat("4a4a5a", spec=1.0), boltlight=glow_mat("f0f4ff"), spear=mat("6a5a4a"), tip=glow_mat("e8f0ff"),
    ),
    spec=dict(hair="hair", long_hair=True, beard="hair", beard_len=0.6, brows="hair", cape="cape", belt="belt",
              buckle="metal", extra=_vholt_parts, motes=_dust(4, 0.5, 6),
              weapon=dict(type="staff", shaft="spear", gem="tip", above=0.9, below=0.6)),
    pose_override=dict(leg_n=(1.25, 1.4), leg_f=(1.25, 1.4), bob=0.18),
    portrait=dict(center=(0.04, 1.62, 0.0), scale=118, yaw=-1.1, pitch=0.12, bg=("0c1018", "2e3a5a", "e8f0ff")),
    frame=(128, 112), frame_cy=1.0, sprite_scale=34.0,
    rim=(210, 225, 255),
)


def _briar_parts(J, p, b):
    out = []
    rng = np.random.default_rng(9)
    # thorns sticking out of the whole silhouette
    anchors = [J["chest"], J["pelvis"], J["sh_n"], J["sh_f"], J["head"], J["el_n"], J["el_f"], J["knee_n"], J["knee_f"]]
    for i in range(34):
        a = anchors[i % len(anchors)]
        d = rng.normal(size=3)
        d[0] = abs(d[0]) * -0.6 + d[0] * 0.4
        d /= np.linalg.norm(d)
        base = a + d * 0.07
        out.append(cone(base, base + d * rng.uniform(0.12, 0.24), 0.026, 0.002, "thorn", layer=0, k=0.01))
    for i in range(9):  # white flowers that bloom grey
        a = anchors[(i * 3) % len(anchors)]
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        out.append(sphere(a + d * 0.12 + v(0.03, 0.03, 0), 0.036, "flower", layer=14))
        out.append(sphere(a + d * 0.12 + v(0.045, 0.035, 0), 0.01, "dust", layer=15))
    # healer's satchel
    out.append(box(J["pelvis"] + v(0.0, 0.0, 0.2), (0.08, 0.07, 0.035), "satchel", round_=0.02, layer=2))
    out.append(cone(J["sh_f"] + v(0.0, 0.02, 0), J["pelvis"] + v(0.0, 0.06, 0.2), 0.012, 0.012, "satchel", layer=2))
    return out + _open_mouth(J, p, b)


character(
    "herald_briar",
    title="Mother Briar, the Thorn Herald",
    role="Nature Herald. Boss of Void 2 (Fractured Steps). A thicket of black thorns shaped like a hunched old woman.",
    element="nature",
    body=dict(height=1.6, bulk=1.05),
    mats=dict(
        skin=mat("8a8478", tex=0.2, tex_freq=80, tex_axis="y"), cloth=mat("3a2e34", tex=0.35, tex_freq=70, tex_axis="y"),
        cloth2=mat("2e2428", tex=0.35, tex_freq=70, tex_axis="y"), hood=mat("3a2e34", tex=0.35, tex_freq=60, tex_axis="y"),
        thorn=mat("5a4a54", spec=0.5), leather=mat("1e181e"), belt=mat("3a2e24"), metal=mat("8a8a7a"),
        eye=HERALD_EYE, mouth=HERALD_EYE, dust=DUST, flower=mat("c8c8c4", spread=0.4), satchel=mat("6a5a40"),
    ),
    spec=dict(hood="hood", robe=True, wide_sleeves=True, extra=_briar_parts, motes=_dust(5, 0.5, 7)),
    pose_override=dict(lean=0.45, head=0.2),
    portrait=dict(center=(0.2, 1.22, 0.0), scale=165, yaw=-1.1, pitch=0.12, bg=("0a0e0a", "2a3a22", "c8c8c4")),
    portrait_pose=dict(lean=0.45, head=0.1, arm_n=(0.9, 0.3, 1.2), arm_f=(0.7, 0.3, 1.1)),
    sprite_scale=34.0,
    rim=(200, 230, 170),
)


def body_of(cid, head_scale=1.0) -> Body:
    b = dict(CAST[cid]["body"])
    return Body(head_scale=head_scale, **b)
