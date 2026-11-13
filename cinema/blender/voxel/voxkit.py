"""3D pixel art: the game's characters and sets built from coloured cubes ("voxels"), one cube about one sprite pixel.

A Part is a sparse grid of coloured cells, drawn with simple solids (box, ellipsoid, cylinder, line) in cell units,
z up, the figure facing -Y (toward a camera in front). part.mesh(name, size) turns it into one Blender object with
only the outer faces, flat colours (a face-corner colour attribute) and its glowing cells on a second, emissive
material. Each cell's colour is jittered a little, as a pixel artist dithers, so flat areas read as pixel art."""
import math, random
import numpy as np
import bpy

V = 0.03   # metres per cell for the cast (a 1.5 m figure is 50 cells tall)


def rgb(h, k=1.0):
    """'#a0522d' or (r, g, b) 0-255 -> linear-ish 0-1 floats (Blender colour attributes are linear)."""
    if isinstance(h, str):
        h = h.lstrip("#"); h = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(min(1.0, (c / 255.0 * k)) ** 2.2 for c in h)


class Part:
    def __init__(self, seed=1):
        self.cells = {}          # (x, y, z) -> (colour, glow)
        self.rng = random.Random(seed)

    def put(self, x, y, z, col, glow=0.0):
        self.cells[(int(x), int(y), int(z))] = (col, glow)

    def clear(self, x, y, z):
        self.cells.pop((int(x), int(y), int(z)), None)

    def box(self, x0, y0, z0, x1, y1, z1, col, glow=0.0, where=None):
        """Fill the cells x0..x1-1 etc. `col` may be a function (x, y, z) -> colour or None (skip)."""
        for x in range(int(x0), int(x1)):
            for y in range(int(y0), int(y1)):
                for z in range(int(z0), int(z1)):
                    if where and not where(x, y, z):
                        continue
                    c = col(x, y, z) if callable(col) else col
                    if c is not None:
                        self.put(x, y, z, c, glow)

    def ell(self, cx, cy, cz, rx, ry, rz, col, glow=0.0, where=None):
        """An ellipsoid centred at (cx, cy, cz) (cell centres at +0.5)."""
        for x in range(int(cx - rx - 1), int(cx + rx + 1)):
            for y in range(int(cy - ry - 1), int(cy + ry + 1)):
                for z in range(int(cz - rz - 1), int(cz + rz + 1)):
                    d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 + ((z + 0.5 - cz) / rz) ** 2
                    if d <= 1.0 and (not where or where(x, y, z)):
                        c = col(x, y, z) if callable(col) else col
                        if c is not None:
                            self.put(x, y, z, c, glow)

    def cyl(self, cx, cy, z0, z1, r, col, glow=0.0, ry=None):
        ry = ry or r
        for x in range(int(cx - r - 1), int(cx + r + 1)):
            for y in range(int(cy - ry - 1), int(cy + ry + 1)):
                if ((x + 0.5 - cx) / r) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    for z in range(int(z0), int(z1)):
                        c = col(x, y, z) if callable(col) else col
                        if c is not None:
                            self.put(x, y, z, c, glow)

    def line(self, a, b, r, col, glow=0.0):
        """A rod of radius r cells from a to b."""
        a = np.array(a, float); b = np.array(b, float); n = int(np.linalg.norm(b - a) * 2) + 1
        for t in np.linspace(0, 1, n):
            p = a + (b - a) * t
            for dx in range(-int(r) - 1, int(r) + 2):
                for dy in range(-int(r) - 1, int(r) + 2):
                    for dz in range(-int(r) - 1, int(r) + 2):
                        if dx * dx + dy * dy + dz * dz <= r * r + 0.25:
                            self.put(math.floor(p[0] + dx), math.floor(p[1] + dy), math.floor(p[2] + dz), col, glow)

    def paint(self, fn):
        """Recolour every cell: fn(x, y, z, colour) -> colour (or (colour, glow))."""
        for k, (c, g) in list(self.cells.items()):
            r = fn(*k, c)
            if r is not None:
                self.cells[k] = r if (isinstance(r, tuple) and len(r) == 2 and isinstance(r[0], tuple)) else (r, g)

    def front(self, y=None):
        """The y of the front-most cell (the face), or of the front-most cell in column x,z when used via front_at."""
        return min(k[1] for k in self.cells)

    def front_at(self, x, z):
        ys = [k[1] for k in self.cells if k[0] == x and k[2] == z]
        return min(ys) if ys else None

    def decal(self, x, z, col, glow=0.0, depth=0):
        """Paint the front-most cell of column (x, z) (a pixel on the face), optionally pushing `depth` cells in."""
        y = self.front_at(x, z)
        if y is None:
            return
        for d in range(depth + 1):
            if (x, y + d, z) in self.cells:
                self.cells[(x, y + d, z)] = (col, glow)

    # ---------------------------------------------------------------- mesh
    def mesh(self, name, size=V, origin=(0, 0, 0), jitter=0.05, glow_strength=6.0):
        """One object with the outer faces of all cells; origin (in cells) becomes the object's origin (its pivot)."""
        keys = list(self.cells)
        occ = set(keys)
        verts, faces, cols, mats = [], [], [], []
        ox, oy, oz = origin
        dirs = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
                ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
                ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
                ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
                ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
                ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)])]
        shade = {(0, 0, 1): 1.0, (0, 0, -1): 0.8, (1, 0, 0): 0.94, (-1, 0, 0): 0.94, (0, 1, 0): 0.9, (0, -1, 0): 0.97}
        for k in keys:
            col, glow = self.cells[k]
            j = 1.0 + self.rng.uniform(-jitter, jitter)
            for (dx, dy, dz), quad in dirs:
                if (k[0] + dx, k[1] + dy, k[2] + dz) in occ:
                    continue
                i = len(verts)
                for (qx, qy, qz) in quad:
                    verts.append(((k[0] + qx - ox) * size, (k[1] + qy - oy) * size, (k[2] + qz - oz) * size))
                faces.append((i, i + 1, i + 2, i + 3))
                s = shade[(dx, dy, dz)] * j
                c = tuple(min(1.0, ch * s) for ch in col)
                cols.append(c + (1.0,))
                mats.append(1 if glow > 0 else 0)
        me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
        attr = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        data = np.repeat(np.array(cols, dtype=np.float32), 4, axis=0).ravel()
        attr.data.foreach_set("color", data)
        me.polygons.foreach_set("material_index", np.array(mats, dtype=np.int32))
        me.polygons.foreach_set("use_smooth", np.zeros(len(faces), dtype=bool))
        me.materials.append(vox_material(False)); me.materials.append(vox_material(True, glow_strength))
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        if OUTLINE:
            outline(ob, OUTLINE * size / V)
        return ob


_MATS = {}
OUTLINE = 0.010   # metres: the dark pixel-art outline around every part (0 = none)


def outline(ob, width):
    """A dark rim like the game sprites' outlines: an inverted shell that only shows from behind (inverted hull)."""
    if "vox_outline" not in _MATS:
        m = bpy.data.materials.new("vox_outline"); m.use_nodes = True; nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial"); geo = nt.nodes.new("ShaderNodeNewGeometry")
        mix = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.02, 0.012, 0.01, 1); em.inputs["Strength"].default_value = 1.0
        lp = nt.nodes.new("ShaderNodeLightPath"); inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0; nt.links.new(lp.outputs["Is Camera Ray"], inv.inputs[1])
        mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"   # only the camera sees the rim: light passes it
        nt.links.new(geo.outputs["Backfacing"], mx.inputs[0]); nt.links.new(inv.outputs[0], mx.inputs[1])
        nt.links.new(mx.outputs[0], mix.inputs[0]); nt.links.new(em.outputs[0], mix.inputs[1]); nt.links.new(tr.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
        _MATS["vox_outline"] = m
    ob.data.materials.append(_MATS["vox_outline"])
    sm = ob.modifiers.new("outline", "SOLIDIFY"); sm.thickness = width; sm.offset = 1.0; sm.use_flip_normals = True
    sm.use_rim = False; sm.material_offset = len(ob.data.materials) - 1


def vox_material(glow, strength=6.0):
    key = (glow, strength)
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new("vox_glow_%g" % strength if glow else "vox"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_name = "Col"; a.attribute_type = "GEOMETRY"
    nt.links.new(a.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.75
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.25
    if glow:
        nt.links.new(a.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = strength
    _MATS[key] = m
    return m


def image_plane(name, path, width_m, loc=(0, 0, 0), glow_path=None, glow=3.0, crop=None):
    """A flat ground plane carrying one of the game's own pixel images, hard pixels (Closest)."""
    img = bpy.data.images.load(path)
    w, h = img.size
    hm = width_m * h / w
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = (width_m, hm, 1)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = "Closest"
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.9
    if glow_path:
        g = nt.nodes.new("ShaderNodeTexImage"); g.image = bpy.data.images.load(glow_path); g.interpolation = "Closest"
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1.0
        nt.links.new(g.outputs["Color"], mul.inputs[6]); mul.inputs[7].default_value = (1.0, 0.42, 0.12, 1)   # ember orange
        nt.links.new(mul.outputs[2], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = glow
    o.data.materials.append(m)
    return o


def stepped(objs, step=2):
    """Animate on twos (or `step`s), like stop-motion: every animated channel holds each pose for `step` frames."""
    for o in objs:
        ad = o.animation_data
        if not ad or not ad.action:
            continue
        for fc in _fcurves(ad.action):
            m = fc.modifiers.new("STEPPED"); m.frame_step = step


def _fcurves(action):
    if hasattr(action, "fcurves") and len(action.fcurves):
        return list(action.fcurves)
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out += list(bag.fcurves)
    return out
