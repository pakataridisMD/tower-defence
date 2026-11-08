"""Turn high-resolution renders into hi-bit pixel art.

This is the "3D to pixel art" technique (used by games such as Dead Cells): render the model large,
then shrink it by a whole factor, snap every pixel to one shared palette, harden the edges and add
a selective outline. The result reads like hand-placed pixels with consistent lighting, in the
spirit of Graveyard Keeper, Romestead and Emberville.

Only numpy is needed, so this runs inside Blender, with the bpy module, or with plain Python.
All arrays are float RGBA in [0, 1], straight (not premultiplied) alpha, top row first.
"""

from __future__ import annotations

import numpy as np

# --- Colour maths (sRGB <-> OKLab) -------------------------------------------------------------


def srgb_to_linear(c: np.ndarray) -> np.ndarray:
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c: np.ndarray) -> np.ndarray:
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])


def srgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    lms = srgb_to_linear(rgb) @ _M1.T
    return np.cbrt(lms) @ _M2.T


def oklab_to_srgb(lab: np.ndarray) -> np.ndarray:
    lms = (lab @ np.linalg.inv(_M2).T) ** 3
    return linear_to_srgb(lms @ np.linalg.inv(_M1).T)


# --- The shared palette -----------------------------------------------------------------------

#: (name, hue in degrees, peak chroma). Each becomes a ramp from deep shadow to highlight.
RAMPS = [
    ("stone", 60.0, 0.025),     # warm greys for stone and wood shadows
    ("slate", 250.0, 0.035),    # cool greys for slate and metal
    ("earth", 55.0, 0.07),      # browns
    ("bronze", 62.0, 0.12),     # bronze, copper, gold
    ("ember", 40.0, 0.19),      # fire orange
    ("blood", 25.0, 0.17),      # reds
    ("sun", 95.0, 0.16),        # yellows and fire cores
    ("moss", 135.0, 0.12),      # greens
    ("sea", 200.0, 0.1),        # teals
    ("storm", 255.0, 0.16),     # deep blues
    ("ice", 235.0, 0.13),       # bright sky blues for storm crystals and sparks
    ("arcane", 305.0, 0.14),    # purples for Void
]
RAMP_STEPS = 7
#: Shadows lean towards this hue, highlights towards the one below: the classic pixel-art hue shift.
SHADOW_HUE = 285.0
LIGHT_HUE = 70.0
HUE_SHIFT = 0.18


def _lerp_hue(a: float, b: float, t: float) -> float:
    delta = ((b - a + 180.0) % 360.0) - 180.0
    return a + delta * t


def build_palette() -> np.ndarray:
    """A shared palette of hue-shifted ramps plus near-black and near-white, as sRGB (n, 3)."""
    colours = [(0.06, 0.05, 0.08), (0.96, 0.94, 0.88)]
    for _name, hue, chroma in RAMPS:
        for step in range(RAMP_STEPS):
            t = step / (RAMP_STEPS - 1)
            lightness = 0.2 + 0.74 * t
            # Chroma peaks in the middle of the ramp and fades at the ends.
            c = chroma * (0.45 + 0.55 * np.sin(np.pi * (0.15 + 0.7 * t)))
            if t < 0.5:
                h = _lerp_hue(hue, SHADOW_HUE, HUE_SHIFT * (0.5 - t) * 2)
            else:
                h = _lerp_hue(hue, LIGHT_HUE, HUE_SHIFT * (t - 0.5) * 2)
            rad = np.radians(h)
            lab = np.array([lightness, c * np.cos(rad), c * np.sin(rad)])
            colours.append(tuple(np.clip(oklab_to_srgb(lab), 0.0, 1.0)))
    return np.array(colours, dtype=np.float64)


PALETTE = build_palette()
_PALETTE_LAB = srgb_to_oklab(PALETTE)


def quantise(rgb: np.ndarray) -> np.ndarray:
    """Snap each colour to the nearest palette entry in OKLab (perceptual) space."""
    flat = rgb.reshape(-1, 3).astype(np.float64)
    lab = srgb_to_oklab(flat)
    # A touch more saturation before snapping, for the warm, rich look of hand-made pixel art.
    lab[:, 1:] *= SATURATION
    palette_lab = _PALETTE_LAB
    palette = PALETTE
    # Weight lightness a little more than hue so shading steps stay where the light put them.
    weights = np.array([1.4, 1.0, 1.0])
    dist = (((lab[:, None, :] - palette_lab[None, :, :]) * weights) ** 2).sum(axis=2)
    return palette[np.argmin(dist, axis=1)].reshape(rgb.shape)


SATURATION = 1.3

# --- Shrinking and cleaning up ------------------------------------------------------------------

#: Below this alpha a shrunk pixel is empty or shadow; above it the pixel is solid.
SOLID_ALPHA = 0.5
#: Pixels between this and SOLID_ALPHA become the flat shadow colour.
SHADOW_ALPHA = 0.14
SHADOW_COLOUR = (0.06, 0.05, 0.1)
SHADOW_OPACITY = 0.26
#: Bright, semi-transparent pixels (flame tips, sparks) stay solid instead of turning to shadow.
GLOW_LUMA = 0.55
OUTLINE_COLOUR = (0.1, 0.065, 0.07)


def shrink(frame: np.ndarray, factor: int) -> np.ndarray:
    """Average `factor` x `factor` blocks, weighting colour by alpha so edges do not go dark."""
    h, w, _ = frame.shape
    blocks = frame[: h - h % factor, : w - w % factor].reshape(h // factor, factor, w // factor, factor, 4)
    alpha = blocks[..., 3]
    weight = alpha.sum(axis=(1, 3))
    colour = (blocks[..., :3] * alpha[..., None]).sum(axis=(1, 3))
    out = np.zeros((h // factor, w // factor, 4))
    safe = np.where(weight > 1e-6, weight, 1.0)
    out[..., :3] = colour / safe[..., None]
    out[..., 3] = alpha.mean(axis=(1, 3))
    return out


def _neighbours(mask: np.ndarray) -> np.ndarray:
    """True where a pixel touches `mask` on one of its four sides."""
    grown = np.zeros_like(mask)
    grown[1:] |= mask[:-1]
    grown[:-1] |= mask[1:]
    grown[:, 1:] |= mask[:, :-1]
    grown[:, :-1] |= mask[:, 1:]
    return grown


def _neighbour_average(frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Average colour of each pixel's four neighbours that are inside `mask`."""
    total = np.zeros(frame.shape[:2] + (3,))
    count = np.zeros(frame.shape[:2])
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        total += np.roll(np.roll(frame[..., :3] * mask[..., None], dy, axis=0), dx, axis=1)
        count += np.roll(np.roll(mask, dy, axis=0), dx, axis=1)
    return total / np.maximum(count, 1)[..., None]


def pixelate(frame: np.ndarray, factor: int, outline: bool = True) -> np.ndarray:
    small = shrink(frame, factor)
    alpha = small[..., 3]
    luma = small[..., :3] @ np.array([0.2126, 0.7152, 0.0722])
    solid = (alpha >= SOLID_ALPHA) | ((alpha >= 0.25) & (luma >= GLOW_LUMA))
    shadow = ~solid & (alpha >= SHADOW_ALPHA)
    out = np.zeros_like(small)
    out[solid, :3] = quantise(small[solid, :3])
    out[solid, 3] = 1.0
    if outline:
        edge = ~solid & _neighbours(solid)
        # A single warm near-black, like a hand-drawn ink line. Glowing parts get a deep ember edge
        # instead, so fire and crystals keep a soft halo rather than a hard black ring.
        out[edge, :3] = OUTLINE_COLOUR
        glowing = solid & (luma >= GLOW_LUMA)
        glow_edge = edge & _neighbours(glowing)
        if glow_edge.any():
            out[glow_edge, :3] = quantise(_neighbour_average(out, glowing)[glow_edge] * 0.45)
        out[edge, 3] = 1.0
        solid = solid | edge
        shadow &= ~edge
    out[shadow, :3] = SHADOW_COLOUR
    out[shadow, 3] = SHADOW_OPACITY
    return out


FLAT_NORMAL = (0.5, 0.5, 1.0)


def pixelate_normals(normals: np.ndarray, colour_frame: np.ndarray, factor: int) -> np.ndarray:
    """Shrink a normal-pass render to match `colour_frame` (the output of `pixelate`).

    Normals are averaged per block and renormalised. Pixels the colour frame drew but the normal
    pass did not (outlines, glows, shadows) get a flat normal facing the viewer.
    """
    small = shrink(normals, factor)
    vectors = small[..., :3] * 2.0 - 1.0
    length = np.linalg.norm(vectors, axis=2, keepdims=True)
    vectors = vectors / np.maximum(length, 1e-6)
    out = np.zeros_like(small)
    out[..., :3] = vectors * 0.5 + 0.5
    has_normal = small[..., 3] >= 0.5
    out[~has_normal, :3] = FLAT_NORMAL
    out[..., 3] = (colour_frame[..., 3] > 0).astype(out.dtype)
    out[out[..., 3] == 0, :3] = FLAT_NORMAL
    return out


def palette_swatch(scale: int = 12) -> np.ndarray:
    """The palette as an image: one row per ramp. Handy to eyeball or to load into Aseprite."""
    rows = [PALETTE[:2]] + [PALETTE[2 + i * RAMP_STEPS: 2 + (i + 1) * RAMP_STEPS] for i in range(len(RAMPS))]
    width = max(len(r) for r in rows)
    image = np.zeros((len(rows) * scale, width * scale, 4))
    for y, row in enumerate(rows):
        for x, colour in enumerate(row):
            image[y * scale:(y + 1) * scale, x * scale:(x + 1) * scale, :3] = colour
            image[y * scale:(y + 1) * scale, x * scale:(x + 1) * scale, 3] = 1.0
    return image
