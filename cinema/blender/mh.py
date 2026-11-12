"""Real human bodies for our heroes, from the CC0 MakeHuman HM08 base mesh (data shipped with MPFB 2, CC0).

We only read MakeHuman's data files (base.obj, morph targets, the game_engine rig and its weights) with our own code.
A body is morphed (gender, muscle, weight, height, plus any detail targets), put from MakeHuman's A-pose into the
KayKit T-pose, and handed back with the joint positions the KayKit rig is then fitted to, so every stand-in animation
still drives it.

    body, eyes, joints = mh.body(height=2.15, gender=0.0, muscle=0.8, weight=0.45, targets={"nose/...": 0.5})
"""
import bpy, bmesh, gzip, json, math, os
from mathutils import Vector, Matrix

DATA = os.environ.get("MH_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "mh")
if not os.path.isdir(os.path.join(DATA, "3dobjs")):
    DATA = "/home/user/mpfb2/src/mpfb/data"

_OBJ = None


def _obj():
    """base.obj -> (verts in MakeHuman space, {group: [faces]})"""
    global _OBJ
    if _OBJ:
        return _OBJ
    verts, uvs, groups, guv, g = [], [], {}, {}, None
    with open(os.path.join(DATA, "3dobjs", "base.obj")) as f:
        for line in f:
            if line.startswith("v "):
                verts.append(tuple(float(t) for t in line.split()[1:4]))
            elif line.startswith("vt "):
                uvs.append(tuple(float(t) for t in line.split()[1:3]))
            elif line.startswith("g "):
                g = line.split()[1]
            elif line.startswith("f "):
                toks = line.split()[1:]
                groups.setdefault(g, []).append([int(t.split("/")[0]) - 1 for t in toks])
                guv.setdefault(g, []).append([int(t.split("/")[1]) - 1 if "/" in t else 0 for t in toks])
    _OBJ = (verts, groups, uvs, guv)
    return _OBJ


def _target(rel):
    path = os.path.join(DATA, "targets", rel if rel.endswith(".gz") else rel + ".target.gz")
    out = []
    with gzip.open(path, "rt") as f:
        for line in f:
            p = line.split()
            if len(p) == 4 and not line.startswith("#"):
                out.append((int(p[0]), float(p[1]), float(p[2]), float(p[3])))
    return out


def _lerp_pairs(v, names):
    """MakeHuman's macro weights: v in 0..1 between min/average/max."""
    lo, mid, hi = names
    if v < 0.5:
        return {lo: 1 - v * 2, mid: v * 2}
    return {mid: 1 - (v - 0.5) * 2, hi: (v - 0.5) * 2}


def macro_targets(gender=0.5, muscle=0.5, weight=0.5, height=0.5, proportions=1.0, race="caucasian"):
    """The macro modifier targets and weights for a young adult, as MakeHuman mixes them."""
    t = {}
    genders = {"female": 1 - gender, "male": gender}
    musc = _lerp_pairs(muscle, ("minmuscle", "averagemuscle", "maxmuscle"))
    wei = _lerp_pairs(weight, ("minweight", "averageweight", "maxweight"))
    hei = {"minheight": max(0.0, 1 - height * 2), "maxheight": max(0.0, height * 2 - 1)}
    for g, gw in genders.items():
        if gw <= 0:
            continue
        t["macrodetails/%s-%s-young" % (race, g)] = gw
        for m, mw in musc.items():
            for w, ww in wei.items():
                k = gw * mw * ww
                if k <= 0:
                    continue
                t["macrodetails/universal-%s-young-%s-%s" % (g, m, w)] = k
                for hname, hw in hei.items():
                    if hw > 0:
                        t["macrodetails/height/%s-young-%s-%s-%s" % (g, m, w, hname)] = k * hw
                if proportions > 0:
                    t["macrodetails/proportions/%s-young-%s-%s-idealproportions" % (g, m, w)] = k * proportions
    return t


def mask(name):
    """A MakeHuman UV mask image (lips, eyelids, face, ears...) as a Blender image."""
    path = os.path.join(DATA, "textures", "mpfb_%s.jpg" % name)
    im = bpy.data.images.load(path, check_existing=True); im.colorspace_settings.name = "Non-Color"
    return im


def _groups_json():
    return json.load(open(os.path.join(DATA, "mesh_metadata", "basemesh_vertex_groups.json")))


def _expand(spec):
    """Vertex group entries are [start, end] ranges or single ints."""
    out = []
    for e in spec:
        if isinstance(e, list):
            out.extend(range(e[0], e[1] + 1))
        else:
            out.append(e)
    return out


def _to_blender(p, s):
    return Vector((p[0] * s, -p[2] * s, p[1] * s))


def body(name="mh_body", height=2.15, gender=0.5, muscle=0.5, weight=0.5, tall=0.5, proportions=1.0,
         targets=None, helpers=("helper-l-eye", "helper-r-eye")):
    """Build a morphed, T-posed body mesh. Returns (body, extras, joints): `extras` are helper meshes (eyes...),
    `joints` maps MakeHuman joint names to Blender positions in the T-pose."""
    verts, faces, uvs, guv = _obj()
    co = [list(v) for v in verts]
    tw = macro_targets(gender, muscle, weight, tall, proportions)
    tw.update(targets or {})
    for rel, w in tw.items():
        if not w:
            continue
        for i, dx, dy, dz in _target(rel):
            c = co[i]; c[0] += dx * w; c[1] += dy * w; c[2] += dz * w
    vg = _groups_json()
    # joints: mean of each joint cube
    raw_j = {}
    for gname, spec in vg.items():
        if gname.startswith("joint-"):
            idx = _expand(spec)
            n = len(idx)
            raw_j[gname[6:]] = [sum(co[i][k] for i in idx) / n for k in range(3)]
    # scale: ground to head top (highest body vertex) becomes `height`
    body_idx = sorted({i for f in faces["body"] for i in f})
    top = max(co[i][1] for i in body_idx)
    ground = raw_j["ground"][1]
    s = height / (top - ground)
    off = Vector((0, 0, -ground * s))

    def B(p):
        return _to_blender(p, s) + off

    def make(gname, oname):
        fl = faces[gname]
        used = sorted({i for f in fl for i in f})
        remap = {o: n for n, o in enumerate(used)}
        me = bpy.data.meshes.new(oname)
        me.from_pydata([B(co[i]) for i in used], [], [[remap[i] for i in f] for f in fl])
        uvl = me.uv_layers.new(name="UVMap")
        k = 0
        for fu in guv[gname]:
            for t in fu:
                uvl.data[k].uv = uvs[t]; k += 1
        me.update()
        o = bpy.data.objects.new(oname, me); bpy.context.scene.collection.objects.link(o)
        for p in me.polygons:
            p.use_smooth = True
        o["mh_index"] = used[:]  # original base-mesh index of each vertex
        return o, remap

    bo, remap = make("body", name)
    extras = [make(h, h)[0] for h in helpers if h in faces]
    joints = {k: B(v) for k, v in raw_j.items()}
    _weights(bo, remap)
    for e in extras:  # helpers (eyes) ride on the head
        pass
    _t_pose(bo, extras, joints)
    return bo, extras, joints


def _weights(o, remap):
    """MakeHuman game_engine weights as vertex groups on `o` (named like the game_engine bones)."""
    w = json.load(open(os.path.join(DATA, "rigs", "standard", "weights.game_engine.json")))["weights"]
    for bone, pairs in w.items():
        g = None
        for i, val in pairs:
            n = remap.get(i)
            if n is None:
                continue
            if g is None:
                g = o.vertex_groups.new(name=bone)
            g.add([n], val, "REPLACE")


ARM = ("clavicle", "upperarm", "lowerarm", "hand")


def _t_pose(o, extras, J):
    """Swing each arm up about the shoulder (and straighten the elbow and wrist) so the arm lies along X, like the
    KayKit rest pose. Done directly on vertices with the arm weights, so no rig is needed."""
    me = o.data
    gi = {g.index: g.name for g in o.vertex_groups}
    for side, sx in (("l", 1), ("r", -1)):
        sh, el, wr = J[side + "-shoulder"], J[side + "-elbow"], J[side + "-hand"]
        # rotation 1: whole arm about the shoulder so the elbow is level with the shoulder and straight out on X
        def rot_to_x(a, b):
            d = (b - a); d.y = d.y  # keep
            target = Vector((sx, 0, 0)) * d.length
            q = d.rotation_difference(target)
            return q.to_matrix().to_4x4()
        R1 = rot_to_x(sh, el)
        el1 = sh + (R1 @ (el - sh).to_4d()).to_3d() if False else sh + R1.to_3x3() @ (el - sh)
        wr1 = sh + R1.to_3x3() @ (wr - sh)
        R2 = rot_to_x(el1, wr1).to_3x3()
        wr2 = el1 + R2 @ (wr1 - el1)
        # per-vertex: blend by the arm weights (upperarm+lowerarm+hand+fingers get R1; lowerarm+hand get R2 on top)
        names_arm = {b + "_" + side for b in ("upperarm", "lowerarm", "hand")} | {
            f + "_0%d_" % k + side for f in ("thumb", "index", "middle", "ring", "pinky") for k in (1, 2, 3)}
        names_fore = {b + "_" + side for b in ("lowerarm", "hand")} | {
            f + "_0%d_" % k + side for f in ("thumb", "index", "middle", "ring", "pinky") for k in (1, 2, 3)}
        R1_3 = R1.to_3x3()
        for v in me.vertices:
            wa = sum(g.weight for g in v.groups if gi[g.group] in names_arm)
            wf = sum(g.weight for g in v.groups if gi[g.group] in names_fore)
            wc = sum(g.weight for g in v.groups if gi[g.group] == "clavicle_" + side)
            if wa <= 0 and wc <= 0:
                continue
            p = v.co.copy()
            a = min(1.0, wa + wc * 0.35)
            q1 = Matrix.Identity(3).lerp(R1_3, a) if False else None
            # slerp-style blend via quaternion
            qq = R1_3.to_quaternion()
            p1 = sh + Matrix.Identity(3).to_quaternion().slerp(qq, a).to_matrix() @ (p - sh)
            if wf > 0:
                p1 = el1 + Matrix.Identity(3).to_quaternion().slerp(R2.to_quaternion(), min(1.0, wf)).to_matrix() @ (p1 - el1)
            v.co = p1
        J[side + "-elbow"] = el1
        J[side + "-hand"] = wr2
        for k in list(J):
            if k.startswith(side + "-finger"):
                J[k] = el1 + R2 @ (sh + R1_3 @ (J[k] - sh) - el1)
    me.update()
