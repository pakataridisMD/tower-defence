"""Draw the horde's power animations and bring in its death animations, in the hand-drawn 2D style.

Each kind of the rank and file has a power (EnemyData.power) and a strip of frames that shows it:

  grunt (skeleton)   rise     its death played backwards: the bones knit and it stands again
  runner (ghost)     phase    it thins out into the air (played forwards to vanish, backwards to return)
  brute (orc)        war_cry  head thrown back, axe and fist raised, a roar
  mender (elf)       mend     the bow raised to the sky to call the healing down
  splitter (golem)   harden   it hunkers down into a heap of stone (held while it is stone)
  warded (dwarf)     block    the hammer snaps up across its face to take a blow
  warden (dragon)    breath   neck coiled back, then fire

The frames are drawn by the pix2d kit on the story art branch (tools/art/pix2d: kit.py, creatures.py,
anim.py), from the same shapes as the walk, so they line up with it frame for frame. Death strips
are copied from that branch's art/pix2d/anim for every hand-drawn enemy in the game.

Writes assets/art/game/drawn/<id>_power.png, <id>_death.png (and their _n normal maps) and adds
"power" and "death" to drawn.json. Then run:
  python3 tools/art/gen_game_art.py --enemies && godot --headless --import

Usage:  python3 tools/art/gen_enemy_powers.py [git ref]   (default origin/claude/project-thread-b06oys)
        add --gif <path> for a preview of every power.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
REF = ARGS[0] if ARGS and not ARGS[0].endswith(".gif") else "origin/claude/project-thread-b06oys"
DRAWN = "assets/art/game/drawn"

# game id -> (art id, power, frames per second, frame the power holds on while it lasts or -1)
POWERS = {
    "grunt": ("skeleton", "rise", 10, -1),
    "runner": ("ghost", "phase", 12, 5),
    "brute": ("orc", "war_cry", 10, -1),
    "mender": ("elf", "mend", 10, -1),
    "splitter": ("golem", "harden", 12, 5),
    "warded": ("dwarf", "block", 16, -1),
    "warden": ("dragon", "breath", 12, -1),
}


def show(path: str) -> bytes:
    return subprocess.run(["git", "show", f"{REF}:{path}"], capture_output=True, check=True).stdout


def load_kit():
    """Unpack the pix2d drawing code from the art branch and import it."""
    tmp = tempfile.mkdtemp(prefix="pix2d_")
    names = subprocess.run(["git", "ls-tree", "--name-only", REF, "tools/art/pix2d/"],
                           capture_output=True, text=True, check=True).stdout.split()
    for path in names:
        if path.endswith(".py"):
            with open(os.path.join(tmp, os.path.basename(path)), "wb") as fh:
                fh.write(show(path))
    sys.path.insert(0, tmp)
    import anim  # noqa: E402
    import creatures  # noqa: E402
    return anim, creatures


def ease(t: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))


def blend(a: dict, b: dict, t: float) -> dict:
    """A pose part way from a to b (t 0..1)."""
    out = {}
    for key in set(a) | set(b):
        va, vb = a.get(key, (0, 0, 0)), b.get(key, (0, 0, 0))
        out[key] = tuple(x + (y - x) * t for x, y in zip(va, vb))
    return out


ROAR = {"weapon": (-1.15, 0, 0), "hand_w": (-0.4, 0, 0), "arm_f": (-2.3, 0, 0), "fore_f": (-0.5, 0, 0),
        "head": (-0.4, 0, 0), "body": (-0.08, 0, -1), "leg_n": (-0.22, 0, 0), "leg_f": (0.22, 0, 0)}
MEND = {"weapon": (-1.85, 0, -2), "arm_f": (-1.9, 0, 0), "head": (-0.4, 0, 0), "body": (-0.06, 0, -1), "cloak": (0.15, 0, 0),
        "hair": (0.2, 0, 0)}
HUNKER = {"body": (0, 0, 5), "head": (0.1, 0, 3), "leg_n": (-0.35, 0, 0), "shin_n": (0.7, 0, 0), "leg_f": (-0.35, 0, 0),
          "shin_f": (0.7, 0, 0), "weapon": (0.25, 0, 2), "hand_w": (-0.4, 0, 0), "arm_f": (0.35, 0, 2), "fore_f": (-0.6, 0, 0)}
GUARD = {"weapon": (-1.4, 0, 0), "hand_w": (1.6, 0, 0), "body": (0, 0, 2), "head": (0.12, 0, 1), "leg_n": (-0.25, 0, 0),
         "shin_n": (0.35, 0, 0), "leg_f": (0.15, 0, 0), "beard": (0.2, 0, 0)}


def poses(power: str) -> list[dict]:
    if power == "war_cry":     # gather, throw the head back and roar (shaking), let it out
        t = [0.0, 0.35, 0.75, 1.0, 1.0, 1.0, 1.0, 0.45]
        shake = [0, 0, 0, 0, 1, -1, 1, 0]
        return [{**blend({}, ROAR, ease(x)), "_all": (0, s, 0)} for x, s in zip(t, shake)]
    if power == "mend":        # raise the bow to the sky, hold it while the light comes, lower it
        t = [0.0, 0.3, 0.65, 0.9, 1.0, 1.0, 1.0, 0.5]
        lift = [0, 0, 0, -1, -1, -2, -1, 0]
        return [{**blend({}, MEND, ease(x)), "_all": (0, 0, d)} for x, d in zip(t, lift)]
    if power == "harden":      # sink down into a heap of stone; the last frame is held
        return [blend({}, HUNKER, ease(i / 5)) for i in range(6)]
    if power == "block":       # snap the hammer up across the face, take the blow, settle
        t = [0.0, 0.7, 1.0, 1.0, 0.6, 0.2]
        knock = [0, 0, -2, -1, 0, 0]
        return [{**blend({}, GUARD, ease(x)), "_all": (0, k, 0)} for x, k in zip(t, knock)]
    raise ValueError(power)


def phase_frames(anim, name):
    """The ghost thins into the air: more of it goes clear each frame, what is left turns pale."""
    base = anim.frames(name, "idle")
    out = []
    rng = np.random.default_rng(11)
    noise = rng.random(np.asarray(base[0][0]).shape[:2])
    for i, gone in enumerate([0.0, 0.18, 0.36, 0.52, 0.66, 0.78]):
        im = np.asarray(base[i % len(base)][0]).copy()
        nm = np.asarray(base[i % len(base)][1]).copy()
        keep = noise >= gone
        im[~keep, 3] = 0
        nm[~keep, 3] = 0
        pale = im[..., :3].astype(float)
        pale = pale + (np.array([200, 235, 240]) - pale) * (0.12 * i)
        im[..., :3] = np.clip(pale, 0, 255).astype(np.uint8)
        im[..., 3] = (im[..., 3] * (1.0 - 0.08 * i)).astype(np.uint8)
        out.append((Image.fromarray(im), Image.fromarray(nm)))
    return out


def power_frames(anim, creatures, name, power):
    if power == "rise":
        return [(f[0], f[1]) for f in reversed(anim.frames(name, "death"))]
    if power == "phase":
        return phase_frames(anim, name)
    if power == "breath":
        return [(f[0], f[1]) for f in anim.frames(name, "attack")]
    pad = anim.PADS.get(name, anim.PAD)
    out = []
    for p in poses(power):
        s = creatures.CREATURES[name](p, pad)
        out.append((Image.fromarray(np.asarray(s.image()).copy()), Image.fromarray(np.asarray(s.normal_image()).copy())))
    return out


def strip(ims):
    w, h = ims[0].size
    o = Image.new("RGBA", (w * len(ims), h), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        o.paste(im, (i * w, 0))
    return o


def main() -> None:
    anim, creatures = load_kit()
    drawn_path = os.path.join(DRAWN, "drawn.json")
    drawn = json.load(open(drawn_path))
    art_anim = json.loads(show("art/pix2d/anim/anim.json"))
    previews = {}
    for gid, (name, power, fps, hold) in POWERS.items():
        if gid not in drawn:
            continue
        frames = power_frames(anim, creatures, name, power)
        w, h = drawn[gid]["frame"]
        assert frames[0][0].size == (w, h), f"{gid}: power frames {frames[0][0].size} differ from the walk {w}x{h}"
        strip([f[0] for f in frames]).save(os.path.join(DRAWN, f"{gid}_power.png"))
        strip([f[1] for f in frames]).save(os.path.join(DRAWN, f"{gid}_power_n.png"))
        drawn[gid]["anims"]["power"] = {"frames": len(frames), "fps": fps, "loop": False, "hold": hold, "power": power}
        previews[gid] = [f[0] for f in frames]
        print(gid, power, len(frames), "frames")
    # Every hand-drawn enemy dies as its art does.
    deaths = 0
    for gid, info in drawn.items():
        src = info.get("source", gid)
        if src not in art_anim or "death" not in art_anim[src]["anims"]:
            continue
        for suffix in ("", "_n"):
            with open(os.path.join(DRAWN, f"{gid}_death{suffix}.png"), "wb") as fh:
                fh.write(show(f"art/pix2d/anim/{src}_death{suffix}.png"))
        info["anims"]["death"] = art_anim[src]["anims"]["death"]
        deaths += 1
    json.dump(drawn, open(drawn_path, "w"), indent=1, sort_keys=True)
    print("death strips:", deaths)
    if "--gif" in sys.argv:
        preview(previews, sys.argv[sys.argv.index("--gif") + 1])


def preview(previews, path, zoom=3):
    """Every power side by side, each looping on its own count."""
    names = list(previews)
    crop = {}
    for n in names:
        boxes = [im.getbbox() for im in previews[n] if im.getbbox()]
        crop[n] = (min(b[0] for b in boxes) - 4, min(b[1] for b in boxes) - 4, max(b[2] for b in boxes) + 4, max(b[3] for b in boxes) + 2)
    W = sum(c[2] - c[0] for c in crop.values())
    H = max(c[3] - c[1] for c in crop.values())
    out = []
    for i in range(24):
        im = Image.new("RGBA", (W, H), (44, 52, 40, 255))
        x = 0
        for n in names:
            fr = previews[n]
            f = fr[min(i, len(fr) - 1)] if i < len(fr) + 8 else fr[0]
            c = crop[n]
            part = f.crop(c)
            im.alpha_composite(part, (x, H - part.height))
            x += c[2] - c[0]
        out.append(im.convert("RGB").resize((W * zoom, H * zoom), Image.NEAREST))
    out[0].save(path, save_all=True, append_images=out[1:], duration=90, loop=0)
    print(path)


if __name__ == "__main__":
    main()
