"""The game's own pixel-art sprites standing in a lit 3D set, with real camera moves (an "HD-2D" look test).

    blender -b -P tests/hd2d_test.py -- OUT --shot walk|talk --sprites DIR [--frames A B] [--res 33] [--samples 16]

DIR holds art/story/characters/<name>/<anim>_<k>.png (+ _n normal map, + _glow) as on main. Each sprite is a flat card
that turns to face the camera, lit by the set's lights through its normal map, its glow as emission, pixels kept hard."""
import sys, os, math, glob, shutil, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy
from mathutils import Vector
import cine3d as C, sets, wardens as W

SPR = C.opt("--sprites", "/tmp/sprites")
TMP = tempfile.mkdtemp()


def _seq(name, anim, kind, hold):
    """Copy an animation's frames as one numbered sequence, each frame repeated `hold` times (8 fps art at 24 fps)."""
    src = os.path.join(SPR, "art", "story", "characters", name)
    suf = "" if kind == "c" else "_" + kind
    frames = sorted(glob.glob(os.path.join(src, "%s_[0-9]%s.png" % (anim, suf))),
                    key=lambda p: int(os.path.basename(p).split("_")[1].split(".")[0]))
    if not frames:
        return None, 0
    d = os.path.join(TMP, "%s_%s_%s" % (name, anim, kind)); os.makedirs(d, exist_ok=True)
    n = 0
    for fr in frames:
        for _ in range(hold):
            n += 1; shutil.copy(fr, os.path.join(d, "f%04d.png" % n))
    img = bpy.data.images.load(os.path.join(d, "f0001.png")); img["px"] = tuple(img.size); img.source = "SEQUENCE"
    if kind != "c":
        img.colorspace_settings.name = "Non-Color" if kind == "n" else "sRGB"
    return img, n


def _tex(nt, img, n, offset):
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = "Closest"
    u = t.image_user; u.frame_duration = n; u.frame_start = 1; u.frame_offset = offset; u.use_cyclic = True; u.use_auto_refresh = True
    return t


def sprite(name, anim, loc, height=1.75, flip=False, fps=8, phase=0, glow=3.0, walk=None):
    """A sprite card standing at `loc`, `height` metres tall (the drawn figure), facing the camera."""
    hold = max(1, round(24 / fps))
    col, n = _seq(name, anim, "c", hold); nrm, _ = _seq(name, anim, "n", hold); glw, _ = _seq(name, anim, "glow", hold)
    w_px, h_px = col["px"]
    bbox_h = h_px * 0.88   # the drawn figure fills most of the canvas height
    hm = height * h_px / bbox_h; wm = hm * w_px / h_px
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    o = bpy.context.object; o.name = "sprite_" + name
    for v in o.data.vertices:   # stand it up, feet at the origin
        v.co = Vector((v.co.x * wm * (-1 if flip else 1), 0, (v.co.y + 0.5) * hm))
    o.location = loc
    m = bpy.data.materials.new("spr_" + name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.8
    tc = _tex(nt, col, n, phase); nt.links.new(tc.outputs["Color"], b.inputs["Base Color"]); nt.links.new(tc.outputs["Alpha"], b.inputs["Alpha"])
    if nrm:
        tn = _tex(nt, nrm, n, phase); nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.8
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if glw:
        tg = _tex(nt, glw, n, phase); nt.links.new(tg.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = glow
    o.data.materials.append(m)
    o.visible_shadow = True
    cam = C.sc.camera
    tr = o.constraints.new("LOCKED_TRACK"); tr.target = cam; tr.lock_axis = "LOCK_Z"; tr.track_axis = "TRACK_NEGATIVE_Y"
    if walk:   # (speed m/s, direction): slide along the ground while the walk cycle plays
        sp, d = walk
        o.keyframe_insert("location", frame=1)
        o.location = Vector(loc) + Vector(d).normalized() * sp * C.sc.frame_end / 24
        o.keyframe_insert("location", frame=C.sc.frame_end)
        for fc in (o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
    return o


shot = C.opt("--shot", "talk")
C.setup(4.0)
S = sets.ember()
hm = S["marks"]["hero"]
cam = C.camera(40 if shot == "walk" else 50, 3.0 if shot == "walk" else 2.2, 8.0)
if shot == "walk":   # Ashwick running down the street of forges toward a low camera that drifts back
    C.key_cam(cam, [(0, (hm.x + 2.2, hm.y - 6.0, 0.8), (88, 0, 18)), (4, (hm.x + 1.6, hm.y - 7.2, 0.7), (89, 0, 12))])
    sprite("herald_ashwick", "walk", (hm.x, hm.y + 6, hm.z), 1.6, glow=1.5, walk=(1.3, (0, -1, 0)))
    sets.ash_fall()
else:                # Fennick by the cart, Tamsin behind waving the carts through; a slow push in
    C.key_cam(cam, [(0, (hm.x + 1.4, hm.y - 4.6, 1.5), (86, 0, 14)), (4, (hm.x + 0.9, hm.y - 3.6, 1.45), (86, 0, 10))])
    sprite("fennick", "idle", (hm.x + 0.4, hm.y, hm.z), 1.5, flip=True)
    sprite("tamsin", "walk", (hm.x - 1.8, hm.y + 2.6, hm.z), 1.65, phase=4, walk=(0.5, (1, -0.3, 0)))
# a soft warm key riding with the camera, so the flat cards read in the night set (as the game lights its sprites)
L = C.light("AREA", (0, 0, 0), (0, 0, 0), 120, (1.0, 0.82, 0.62), 2.0, "sprite_key"); L.parent = cam; L.location = (1.2, 0.8, 0.6)
C.sc.view_settings.exposure = 0.6
C.render(default_res=33, default_samples=16)
