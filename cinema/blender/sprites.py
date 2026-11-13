"""The game's own pixel-art characters in the 3D story sets (the look chosen on Nov 13: "game sprites in 3D").

Every cast member that has sprites in art/story/characters/<name>/ (anim_K.png, anim_K_n.png normal map, anim_K_glow.png)
becomes a flat card that turns to face the camera, lit by the set through its normal map, its glow as emission, pixels
kept hard. The card hangs under an empty that stands in for the rig, so walks (C.march), rises and mounts still work.
Characters without sprites (the mortal monarchs, the Keeper, Seraphel) stay 3D bodies until they are drawn."""
import os, glob, math, shutil, tempfile
import bpy
from mathutils import Vector
import cine3d as C, hero

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "art", "story", "characters")
TMP = tempfile.mkdtemp(prefix="sprites_")
ALIAS = {"ashwick": "herald_ashwick", "briar": "herald_briar", "gorrath": "herald_gorrath", "ourra": "herald_ourra",
         "vesper": "herald_vesper", "vholt": "herald_vholt", "broodmother": "elder_broodmother",
         "cassivane_ash": "cassivane_ashen", "oswin": "oswin_grey"}
FPS = 8   # the sprite animations are drawn for 8 frames a second


def folder(who):
    name = ALIAS.get(who, who)
    d = os.path.join(C.opt("--sprite-root", ROOT), name)
    return d if os.path.isdir(d) else None


def anim_for(action):
    """The 3D action a shot asks for, as one of the sprite animations: (anim, plays once)."""
    if action.startswith("Death"):
        return "death", True
    if action.startswith(("Walking", "Running")):
        return "walk", False
    if action.startswith(("Interact", "Use_Item", "PickUp", "Spellcast", "Cheer", "Throw")):
        return "cast", False
    if "Attack" in action:
        return "attack", False
    return "idle", False   # Idle, 2H_Melee_Idle, Blocking, sitting (no sitting sprites yet)


def _frames(d, anim, suffix):
    pat = os.path.join(d, "%s_[0-9]*%s.png" % (anim, suffix))
    out = [p for p in glob.glob(pat) if os.path.basename(p)[len(anim) + 1:-4 - len(suffix)].isdigit()]
    return sorted(out, key=lambda p: int(os.path.basename(p)[len(anim) + 1:-4 - len(suffix)]))


def _seq(d, who, anim, suffix, hold, colour):
    """One numbered image sequence from the animation's frames, each held `hold` film frames (8 fps art at 24 fps)."""
    fr = _frames(d, anim, suffix)
    if not fr:
        return None, 0
    out = os.path.join(TMP, "%s_%s%s" % (who, anim, suffix)); os.makedirs(out, exist_ok=True)
    n = 0
    for p in fr:
        for _ in range(hold):
            n += 1; shutil.copy(p, os.path.join(out, "f%04d.png" % n))
    img = bpy.data.images.load(os.path.join(out, "f0001.png"))
    px = tuple(img.size)
    if not colour:
        img.colorspace_settings.name = "Non-Color" if suffix == "_n" else "sRGB"
    img["px"] = px
    if colour:   # the drawn figure's height in pixels (rows with any alpha), for sizing the card
        import numpy as np
        a = np.empty(px[0] * px[1] * 4, dtype=np.float32); img.pixels.foreach_get(a)
        rows = np.where(a.reshape(px[1], px[0], 4)[:, :, 3].max(axis=1) > 0.1)[0]
        img["fig"] = (int(rows.min()), int(rows.max()) + 1) if len(rows) else (0, px[1])
    img.source = "SEQUENCE"
    return img, n


def _tex(nt, img, n, start, once):
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = "Closest"
    u = t.image_user; u.frame_duration = n; u.frame_start = start; u.use_cyclic = not once; u.use_auto_refresh = True
    return t


def card(who, action, loc, face_deg, opt=None):
    """Build `who` as a sprite card at `loc`; returns the empty that stands in for the rig, or None (no sprites)."""
    opt = opt or {}
    d = folder(who)
    if not d:
        return None
    anim, once = anim_for(action)
    if not _frames(d, anim, ""):
        anim, once = "idle", False
    hold = max(1, round(C.FPS / FPS))
    col, n = _seq(d, who, anim, "", hold, True)
    nrm, _ = _seq(d, who, anim, "_n", hold, False)
    glw, _ = _seq(d, who, anim, "_glow", hold, False)
    start = 1
    if once:   # deaths play once from `at` and hold the last drawing; a *_Pose death is already lying there
        start = int(round(C.sec(opt.get("at", 0.0)))) if not action.endswith("_Pose") else 1 - n
    phase = int(opt.get("phase", 0.0) * n)
    w_px, h_px = col["px"]; f0, f1 = col["fig"]
    props = hero.HUMANS.get(who, ({"height": 1.75}, None))[0]
    height = props.get("height", 1.75) * hero.SCALE.get(who, 1.0)
    per_px = height / max(1, f1 - f0)   # metres per art pixel, so the drawn figure stands `height` tall
    wm, hm = w_px * per_px, h_px * per_px
    foot = (h_px - f1) * per_px          # empty canvas under the feet
    root = bpy.data.objects.new("rig_" + who, None); C.sc.collection.objects.link(root)
    root.location = loc; root.rotation_euler.z = math.radians(face_deg)
    root["sprite"] = True
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.object; o.name = "sprite_" + who
    fwd = Vector((math.sin(math.radians(face_deg)), -math.cos(math.radians(face_deg)), 0))
    flip = -1 if fwd.x > 0.25 else 1   # the drawings face screen-left; mirror a figure turned to the right
    for v in o.data.vertices:   # stand the card up, the drawn feet on the ground
        v.co = Vector((v.co.x * wm * flip, 0, (v.co.y + 0.5) * hm - foot))
    o.parent = root; o.location = (0, 0, 0)
    m = bpy.data.materials.new("spr_" + who); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.85
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.2
    tc = _tex(nt, col, n, start - phase, once)
    nt.links.new(tc.outputs["Color"], b.inputs["Base Color"]); nt.links.new(tc.outputs["Alpha"], b.inputs["Alpha"])
    if nrm:
        tn = _tex(nt, nrm, n, start - phase, once); nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.8
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if glw:
        tg = _tex(nt, glw, n, start - phase, once); nt.links.new(tg.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = 2.0
    o.data.materials.append(m)
    o["face_camera"] = True
    if "scale" in opt:
        root.scale = (opt["scale"],) * 3
    return root


def face_camera(cam):
    """Turn every card to the camera (about its own up axis), once the shot's camera exists."""
    for o in C.sc.objects:
        if o.get("face_camera"):
            tr = o.constraints.new("LOCKED_TRACK"); tr.target = cam; tr.lock_axis = "LOCK_Z"; tr.track_axis = "TRACK_NEGATIVE_Y"


def key_light(cam, energy=90):
    """A soft warm key riding with the camera, so the flat cards read in night sets (the game lights its sprites)."""
    L = C.light("AREA", (0, 0, 0), (0, 0, 0), energy, (1.0, 0.84, 0.66), 2.0, "sprite_key")
    L.parent = cam; L.location = (1.2, 0.8, 0.6)
    return L
