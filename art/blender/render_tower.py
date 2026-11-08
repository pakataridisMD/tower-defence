"""Render a tower to a Godot-ready sprite sheet.

Usage (either works):
    blender -b -P art/blender/render_tower.py -- fire_brazier [options]
    python art/blender/render_tower.py fire_brazier [options]      # needs `pip install bpy`

Options:
    --style pixel|hd pixel (default): hi-bit pixel art, 64 px frames drawn at 2x with sharp pixels.
                     hd: smooth 256 px frames drawn at half size.
    --directions N   aim directions to render (default 16)
    --frames N       animation frames per direction (default: the tower's own setting)
    --samples N      Cycles samples per frame (default 32 for pixel, 64 for hd)
    --out DIR        output folder (default assets/sprites/towers/<id>)
    --preview PATH   render one frame to PATH (plus PATH_board.png on the board colour)
    --no-outline     skip the outline pass

The sheet has one row per direction and one column per animation frame. Row d shows the tower
aiming at screen angle d * 360 / directions degrees, Godot style (0 = right, clockwise).
A JSON file next to it tells the game the frame size, the anchor pixel and the timing.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "towers"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import kit  # noqa: E402
import pixelate  # noqa: E402

#: Pixel style: render at this size, then shrink by PIXEL_FACTOR to 64 px frames.
RENDER_SIZE = 256
PIXEL_FACTOR = 4

OUTLINE_COLOR = (0.035, 0.03, 0.045)
OUTLINE_RADIUS = 2.0
OUTLINE_OPACITY = 0.9
#: The game board colour (BoardView.GROUND, #243042) as 8-bit sRGB fractions.
BOARD_COLOR = (0x24 / 255, 0x30 / 255, 0x42 / 255)


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tower")
    parser.add_argument("--directions", type=int, default=16)
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--style", choices=("pixel", "hd"), default="pixel")
    parser.add_argument("--samples", type=int, default=0)
    parser.add_argument("--out", default="")
    parser.add_argument("--preview", default="")
    parser.add_argument("--preview-angle", type=float, default=35.0,
                        help="screen angle in degrees for the preview")
    parser.add_argument("--no-outline", action="store_true")
    return parser.parse_args(argv)


def load_png(path: str) -> np.ndarray:
    """Load an 8-bit PNG as a float array, top row first, shape (h, w, 4)."""
    image = bpy.data.images.load(path, check_existing=False)
    w, h = image.size
    pixels = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    bpy.data.images.remove(image)
    return pixels.reshape(h, w, 4)[::-1].copy()


def save_png(array: np.ndarray, path: str, raw: bool = False) -> None:
    h, w, _ = array.shape
    image = bpy.data.images.new(os.path.basename(path), width=w, height=h, alpha=True)
    image.colorspace_settings.name = "Non-Color" if raw else "sRGB"
    image.alpha_mode = "STRAIGHT"
    image.pixels.foreach_set(np.ascontiguousarray(array[::-1], dtype=np.float32).ravel())
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


def add_outline(frame: np.ndarray, radius: float) -> np.ndarray:
    """Draw a thin dark outline around the solid parts of the sprite.

    Soft shadows and faint flame tips stay below the threshold, so only the tower body is traced.
    The outline sits underneath the sprite, so it only shows outside the silhouette.
    """
    alpha = frame[..., 3]
    solid = np.clip((alpha - 0.55) / 0.3, 0.0, 1.0)
    grown = solid.copy()
    r = int(math.ceil(radius))
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            dist = math.hypot(dx, dy)
            if dist == 0 or dist > radius + 0.5:
                continue
            weight = min(1.0, radius + 0.5 - dist)
            shifted = np.roll(np.roll(solid, dy, axis=0), dx, axis=1) * weight
            np.maximum(grown, shifted, out=grown)
    under_alpha = grown * OUTLINE_OPACITY
    over_alpha = alpha
    out_alpha = over_alpha + under_alpha * (1.0 - over_alpha)
    out = np.empty_like(frame)
    safe = np.where(out_alpha > 1e-6, out_alpha, 1.0)
    for c in range(3):
        out[..., c] = (frame[..., c] * over_alpha + OUTLINE_COLOR[c] * under_alpha * (1.0 - over_alpha)) / safe
    out[..., 3] = out_alpha
    return out


def composite_on_board(frame: np.ndarray) -> np.ndarray:
    """Preview helper: the sprite over the game's board colour, to judge contrast."""
    board = np.array(BOARD_COLOR, dtype=np.float32)
    alpha = frame[..., 3:4]
    out = np.ones_like(frame)
    out[..., :3] = frame[..., :3] * alpha + board * (1.0 - alpha)
    return out


def build_scene(tower_id: str, settings: kit.RenderSettings):
    scene = kit.reset_scene()
    kit.setup_render(scene, settings)
    kit.setup_camera(scene)
    kit.setup_lighting(scene)
    kit.add_shadow_catcher(scene)
    module = importlib.import_module(tower_id)
    rig = module.build(scene)
    return scene, rig


def render_frame(scene, rig: kit.TowerRig, screen_angle: float, phase: float, path: str,
                 normal_path: str = "", normal_material=None) -> None:
    rig.head.rotation_euler.z = kit.world_yaw_for_screen_angle(screen_angle)
    rig.animate(phase)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if normal_path:
        with kit.NormalPass(scene, normal_material):
            scene.render.filepath = normal_path
            bpy.ops.render.render(write_still=True)


def finish_frame(frame: np.ndarray, args: argparse.Namespace) -> np.ndarray:
    if args.style == "pixel":
        return pixelate.pixelate(frame, PIXEL_FACTOR, outline=not args.no_outline)
    if args.no_outline:
        return frame
    return add_outline(frame, OUTLINE_RADIUS)


def main() -> None:
    args = parse_args()
    pixel = args.style == "pixel"
    kit.FLAT = pixel
    samples = args.samples or (32 if pixel else 64)
    settings = kit.RenderSettings(size=RENDER_SIZE, samples=samples)
    scene, rig = build_scene(args.tower, settings)

    if args.preview:
        path = os.path.abspath(args.preview)
        render_frame(scene, rig, math.radians(args.preview_angle), 0.0, path)
        frame = finish_frame(load_png(path), args)
        if pixel:
            # Blow the pixels up 8x so they can be judged by eye.
            frame = frame.repeat(8, axis=0).repeat(8, axis=1)
        save_png(np.clip(frame, 0, 1), path)
        board_path = os.path.splitext(path)[0] + "_board.png"
        save_png(composite_on_board(frame), board_path)
        print(f"Preview written to {path} and {board_path}")
        return

    frames = args.frames or rig.frames
    out_dir = os.path.abspath(args.out or os.path.join(REPO, "assets", "sprites", "towers", rig.id))
    os.makedirs(out_dir, exist_ok=True)
    factor = PIXEL_FACTOR if pixel else 1
    size = RENDER_SIZE // factor
    sheet = np.zeros((args.directions * size, frames * size, 4), dtype=np.float32)
    # Normal maps let Godot's 2D lights (torches, fire towers, day and night) shade the sprites.
    normal_sheet = np.zeros_like(sheet) if pixel else None
    normal_material = kit.normal_override_material() if pixel else None
    started = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        for d in range(args.directions):
            angle = math.tau * d / args.directions
            for f in range(frames):
                path = os.path.join(tmp, f"d{d:02d}_f{f:02d}.png")
                normal_path = os.path.join(tmp, f"d{d:02d}_f{f:02d}_n.png") if pixel else ""
                render_frame(scene, rig, angle, f / frames, path, normal_path, normal_material)
                cell = (slice(d * size, (d + 1) * size), slice(f * size, (f + 1) * size))
                sheet[cell] = finish_frame(load_png(path), args)
                if pixel:
                    normal_sheet[cell] = pixelate.pixelate_normals(load_png(normal_path), sheet[cell], PIXEL_FACTOR)
            print(f"Direction {d + 1}/{args.directions} done ({time.time() - started:.0f} s)", flush=True)

    sheet_path = os.path.join(out_dir, f"{rig.id}.png")
    save_png(np.clip(sheet, 0.0, 1.0), sheet_path)
    if normal_sheet is not None:
        save_png(np.clip(normal_sheet, 0.0, 1.0), os.path.join(out_dir, f"{rig.id}_n.png"), raw=True)
    anchor_x, anchor_y = kit.anchor_pixel(settings)
    meta = {
        "id": rig.id,
        "sheet": f"{rig.id}.png",
        "normal_sheet": f"{rig.id}_n.png" if pixel else "",
        "style": args.style,
        "frame_size": [size, size],
        "directions": args.directions,
        "frames": frames,
        "fps": rig.fps,
        # Whole pixels, so pixel art lands on the pixel grid.
        "anchor": [round(anchor_x / factor), round(anchor_y / factor)],
        # One board cell is 64 screen pixels and a frame spans FRAME_CELLS cells.
        "display_scale": kit.FRAME_CELLS * 64 / size,
        "filter": "nearest" if pixel else "linear",
        "layout": "rows are directions (row d aims at screen angle d * TAU / directions, 0 = right, "
                  "clockwise); columns are animation frames",
        "camera": {"elevation_degrees": kit.CAMERA_ELEVATION, "frame_cells": kit.FRAME_CELLS},
    }
    with open(os.path.join(out_dir, f"{rig.id}.json"), "w") as handle:
        json.dump(meta, handle, indent=2)
        handle.write("\n")
    print(f"Sheet written to {sheet_path} in {time.time() - started:.0f} s", flush=True)


if __name__ == "__main__":
    main()
