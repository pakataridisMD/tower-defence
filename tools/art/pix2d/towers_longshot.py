"""The long-range towers in the hand-drawn style. Imported by towers.py, which registers them in TOWERS.

They shoot across most of the map, so they read as lookouts: taller and slimmer than a base tower, with the weapon
at the very top (a copper lance, a great bow, a rack of flare tubes) instead of a big glowing heart.
"""
from __future__ import annotations

import numpy as np

from kit import INK, Sprite, hexc, ramp
from creatures import STONE, STONE_D, IRON, GOLD
from towers import (BARK, BARK_D, BASALT, BOLT, CLOTH_R, COPPER, FIRE, LEAF, LEAF_D, SAP, SLATE, block, course_wall,
                    plinth, meta_for, tower)

THATCH = ramp("8a7a3e", spread=0.5)
ROPE = ramp("9a8460", spread=0.4)


@tower
def storm_skyneedle():
    """Skyneedle: a very tall, thin slate needle wound with copper, a copper lance on top crackling at the tip."""
    s = Sprite(34, 118)
    cx, bottom = 16, 114
    plinth(s, cx, bottom, 26, 5, SLATE, seed=601)
    course_wall(s, cx, bottom - 5, 14, 7, 62, SLATE, row_h=6, seed=602, moss_rows=1)
    top = bottom - 67
    # copper bands winding up the shaft, narrower as it rises
    for k, y in enumerate(range(bottom - 15, top + 4, -12)):
        w = 7.0 - (bottom - 5 - y) / 62 * 3.5
        s.part(s.rect(cx - w, y - 2, cx + w + 1, y), COPPER, flat=True)
        s.px(cx - w + 1, y - 1, COPPER[4])
        s.line(cx - w, y, cx + w, y - 3 if k % 2 else y + 1, COPPER[1])
    # a glowing slit window halfway up
    s.fill(s.rect(cx - 1, bottom - 40, cx + 1, bottom - 32), INK)
    s.fill(s.rect(cx - 1, bottom - 39, cx + 1, bottom - 34), BOLT[2], glow=True)
    # collar and pointed cap
    block(s, cx - 6, top - 4, cx + 6, top + 1, SLATE, depth=2, seed=603)
    s.part(s.poly([(cx - 5, top - 4), (cx + 6, top - 4), (cx + 1, top - 11)]), SLATE, flat=True)
    s.line(cx + 1, top - 11, cx - 4, top - 5, SLATE[4])
    # the lance: a long copper rod with three coil rings and a needle tip
    s.part(s.rect(cx, top - 34, cx + 2, top - 10), COPPER, flat=True)
    for k in range(3):
        y = top - 15 - k * 6
        r = 4 - k
        s.line(cx - r, y, cx + 1 + r + 1, y - 1, COPPER[3])
        s.line(cx - r, y + 1, cx + 1 + r + 1, y, COPPER[1])
    s.line(cx + 1, top - 40, cx + 1, top - 34, COPPER[4])
    # crackling tip: a blue crystal star held by the last ring
    tip = top - 43
    s.fill(s.poly([(cx + 1, tip - 6), (cx + 4, tip), (cx + 1, tip + 5), (cx - 2, tip)]), BOLT[2], glow=True)
    s.fill(s.poly([(cx + 1, tip - 6), (cx + 4, tip), (cx + 1, tip + 1)]), BOLT[3], glow=True)
    s.px(cx + 1, tip - 1, BOLT[4], glow=True)
    s.px(cx + 1, tip, BOLT[4], glow=True)
    s.ink()
    s.pxs([(cx - 3, tip - 1), (cx - 4, tip + 1), (cx + 5, tip - 2), (cx + 6, tip), (cx + 1, tip - 6), (cx - 2, top - 24),
           (cx + 5, top - 28)], BOLT[4], glow=True)
    return s, meta_for(s, "storm", tip, energy=0.9, rng=95, height=60)


@tower
def nature_eyrie():
    """Eyrie: a timber lookout on four stilts over stone footings, a leaf-thatched roof and a great bow at the rail."""
    s = Sprite(48, 106)
    cx, bottom = 23, 102
    # stone footings and four leaning stilts with cross bracing
    for x in (cx - 14, cx + 9):
        block(s, x, bottom - 6, x + 6, bottom, STONE_D, depth=2, seed=610 + x, moss=3)
    deck = bottom - 58
    legs = [(cx - 11, cx - 7), (cx + 12, cx + 8)]
    for (x0, x1) in legs:
        s.part(s.poly([(x0 - 2, bottom - 5), (x0 + 1, bottom - 5), (x1 + 1, deck), (x1 - 2, deck)]), BARK, flat=True)
    for k in range(3):                                         # X braces
        y0 = bottom - 8 - k * 16
        y1 = y0 - 15
        s.line(cx - 10 + k, y0, cx + 9 - k, y1, BARK_D[2])
        s.line(cx + 10 - k, y0, cx - 9 + k, y1, BARK_D[1])
        s.line(cx - 10 + k, y1 + 1, cx + 10 - k, y1 + 1, BARK_D[3])
    # a ladder up the middle
    s.line(cx - 2, bottom - 4, cx - 1, deck, ROPE[2])
    s.line(cx + 2, bottom - 4, cx + 1, deck, ROPE[2])
    for y in range(bottom - 8, deck, 5):
        s.line(cx - 2, y, cx + 2, y, ROPE[3])
    # the deck: planks seen from the front, a low rail
    s.part(s.rect(cx - 15, deck - 3, cx + 16, deck + 1), BARK_D, flat=True)
    for x in range(int(cx - 14), int(cx + 16), 4):
        s.px(x, deck - 1, BARK_D[0])
    s.part(s.rect(cx - 14, deck - 11, cx + 15, deck - 3), BARK, flat=True)
    for x in range(int(cx - 13), int(cx + 15), 3):
        s.line(x, deck - 10, x, deck - 4, BARK[1] if x % 2 else BARK[3])
    s.line(cx - 14, deck - 11, cx + 15, deck - 11, BARK[4])
    # corner posts and the leaf-thatched roof
    roof = deck - 30
    for x in (cx - 14, cx + 13):
        s.part(s.rect(x, roof + 4, x + 2, deck - 3), BARK_D, flat=True)
    s.part(s.poly([(cx - 20, roof + 6), (cx + 21, roof + 6), (cx + 13, roof - 4), (cx + 1, roof - 14), (cx - 12, roof - 4)]),
           THATCH, bias=0.05)
    rng = np.random.default_rng(611)
    for _ in range(22):                                        # leaves woven into the thatch
        x, y = int(rng.integers(cx - 17, cx + 19)), int(rng.integers(roof - 10, roof + 6))
        if s.a[y, x]:
            s.px(x, y, LEAF[3] if y < roof - 2 else LEAF_D[2])
    s.line(cx - 20, roof + 6, cx + 21, roof + 6, THATCH[1])
    # a green pennant on a pole above the roof
    s.line(cx + 1, roof - 14, cx + 1, roof - 24, BARK_D[3])
    s.fill(s.poly([(cx + 2, roof - 24), (cx + 10, roof - 21), (cx + 2, roof - 18)]), LEAF[3])
    # the great bow on the rail, drawn and aimed out to the right, a glowing green arrowhead
    by = deck - 18
    s.line(cx + 6, by - 9, cx + 10, by, BARK_D[3])
    s.line(cx + 10, by, cx + 6, by + 9, BARK_D[3])
    s.line(cx + 7, by - 9, cx + 11, by, BARK[4])
    s.line(cx + 11, by, cx + 7, by + 9, BARK[4])
    s.line(cx + 6, by - 9, cx - 2, by, ROPE[4])                 # string pulled back
    s.line(cx - 2, by, cx + 6, by + 9, ROPE[4])
    s.line(cx - 2, by, cx + 15, by, BARK[3])                    # the arrow
    s.part(s.rect(cx + 1, by + 1, cx + 5, by + 4), IRON, flat=True)   # an iron mount under it
    s.fill(s.poly([(cx + 15, by - 2), (cx + 19, by), (cx + 15, by + 2)]), SAP[3], glow=True)
    s.ink()
    s.pxs([(cx + 20, by - 1), (cx + 21, by + 1), (cx + 18, by - 3)], SAP[4], glow=True)
    return s, meta_for(s, "nature", by, muzzle_x=17, light_y=by, energy=0.7, rng=85, height=50)


@tower
def fire_flare_battery():
    """Flare Battery: a square basalt bastion with a red banner, an iron rack of flare tubes glowing on top."""
    s = Sprite(46, 96)
    cx, bottom = 22, 92
    plinth(s, cx, bottom, 36, 6, BASALT, seed=620)
    course_wall(s, cx, bottom - 6, 28, 24, 40, STONE_D, row_h=6, seed=621, moss_rows=1)
    top = bottom - 46
    for k, (a, b) in enumerate([(cx - 15, cx - 8), (cx - 5, cx + 2), (cx + 5, cx + 12)]):   # crenels
        block(s, a, top - 6, b, top - 1, STONE, depth=2, side=(k == 2), seed=622 + k)
    block(s, cx - 15, top - 1, cx + 13, top + 2, STONE, depth=0, seed=625)
    # two glowing loopholes and a red banner with a gold flare sigil
    for x in (cx - 9, cx + 6):
        s.fill(s.rect(x, bottom - 30, x + 2, bottom - 22), INK)
        s.fill(s.rect(x, bottom - 28, x + 2, bottom - 24), FIRE[2], glow=True)
    s.part(s.poly([(cx - 4, top + 2), (cx + 3, top + 2), (cx + 3, top + 20), (cx - 0.5, top + 16), (cx - 4, top + 20)]),
           CLOTH_R, flat=True)
    s.pxs([(cx - 1, top + 6), (cx - 1, top + 7), (cx - 2, top + 8), (cx, top + 8), (cx - 1, top + 9), (cx - 1, top + 11)], GOLD[3])
    # the rack: an iron frame holding four tubes angled up and out
    base = top - 7
    s.part(s.rect(cx - 12, base - 4, cx + 11, base), IRON, flat=True)
    s.line(cx - 12, base - 4, cx + 11, base - 4, IRON[4])
    mouths = []
    for k in range(4):
        x = cx - 9 + k * 6
        lean = 3 + k
        h = 18 + (k % 2) * 4
        s.part(s.poly([(x - 2, base - 4), (x + 2, base - 4), (x + 2 + lean, base - 4 - h), (x - 2 + lean, base - 4 - h)]),
               IRON, flat=True)
        s.line(x - 2, base - 4, x - 2 + lean, base - 4 - h, IRON[4])
        mx, my = x + lean, base - 4 - h
        s.fill(s.ellipse(mx, my, 2.6, 1.6), FIRE[2], glow=True)
        s.fill(s.ellipse(mx, my - 1, 1.6, 1.4), FIRE[3], glow=True)
        s.px(mx, my - 1, FIRE[4], glow=True)
        mouths.append((mx, my))
        s.line(x - 1, base - 9, x + 3, base - 10, COPPER[2])    # a copper strap on each
    s.ink()
    # sparks and a thin trail rising from the tubes
    for (mx, my) in mouths:
        s.pxs([(mx + 1, my - 3), (mx + 2, my - 6)], FIRE[3], glow=True)
    s.pxs([(cx - 4, top - 38), (cx + 8, top - 42), (cx + 14, top - 36)], FIRE[4], glow=True)
    mx, my = mouths[2]
    return s, meta_for(s, "fire", my, muzzle_x=mx - s.w // 2, light_y=my + 4, energy=1.0, rng=110, height=52)
