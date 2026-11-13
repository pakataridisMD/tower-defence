"""Test clip for the new film look: the game in 3D pixel art, acted big and snappy (stop-motion on twos).
Fennick (Ember intro, line 03) introduces himself by his cart in the Ember street; Tamsin waves carts through behind.

    blender -b -P voxel/vox_test.py -- OUT [--frames A B] [--res 67] [--samples 16] --no-mblur
    (from cinema/blender; the voice file: --voice PATH/03.ogg, default /tmp/claude-0/vox/03.ogg)"""
import os, sys, math, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import numpy as np
import bpy
import cine3d as C
import voxkit as VK
import cast_vox as K
import set_vox as S

A0 = 0.6            # the voice starts here
LENGTH = 14.4
C.setup(LENGTH)
F = lambda t: int(round(t * 24)) + 1

marks = S.ember_street()
fen = K.fennick(); tam = K.tamsin()


# ------------------------------------------------------------------ Fennick's acting
def P(t, **kw):
    K.pose(fen, F(t), **kw)


bx, by, bz = marks["fennick"]
idle = dict(arm_r=(12, 8), arm_l=(4, 10), leg_r=(0, 0), leg_l=(0, 0), lean=(0, 0), head=(0, 0, 0), squash=(1, 1), eyes=1.0)
P(0.0, loc=(bx, by, bz), face=70, **dict(idle, head=(28, 0, 0), arm_l=(55, 10), lean=(10, 0)))
P(0.3, face=70, head=(30, 0, 0), arm_l=(55, 12))
P(0.4, squash=(1.08, 0.9), head=(10, 0, -20), eyes=1.35, arm_l=(30, 30))                       # hears us
P(0.55, loc=(bx, by, bz + 0.13), squash=(0.92, 1.12), face=25, arm_l=(20, 50), arm_r=(20, 30), leg_r=(20, 5), leg_l=(-15, 5))
P(0.72, loc=(bx, by, bz), squash=(1.14, 0.86), face=0, leg_r=(0, 0), leg_l=(0, 0), arm_l=(10, 40))
P(0.85, squash=(0.97, 1.04), head=(0, 0, 0), eyes=1.0)
P(1.0, squash=(1.03, 1.0), lean=(-8, 0), arm_l=(80, 0, 50), head=(-10, 8, 0), arm_r=(12, 8))     # "I'm Fennick." hand on chest
P(1.5, lean=(-6, 0), head=(-8, -6, 0), arm_l=(78, 0, 52))
P(1.9, face=30, lean=(4, 0), arm_l=(70, 0, -60), head=(0, 0, 25))                                    # "I design ..."
P(2.5, face=25, loc=(bx, by, bz + 0.04), squash=(0.95, 1.08), arm_r=(150, 15), head=(-18, 0, 15), arm_l=(40, 50))   # "... the towers"
P(3.2, face=20, loc=(bx, by, bz), squash=(1, 1), arm_r=(140, 12), head=(-12, 0, 10))
P(3.45, face=0, arm_r=(12, 8), squash=(1.05, 0.95))
P(3.6, lean=(15, 0), arm_l=(92, 4), head=(6, 0, 0), eyes=1.2, squash=(1, 1))                   # "you build them": at us
P(3.9, lean=(19, 0), arm_l=(98, 0))
P(4.4, lean=(2, 0), arm_l=(12, 12), head=(0, 4, 0), eyes=1.0)
P(4.9, arm_l=(5, 25), arm_r=(10, 20), squash=(1.06, 0.94))                                      # wind up ...
flick = [(160, 30, 130, 25), (135, 45, 155, 15), (165, 20, 128, 35), (138, 50, 160, 20), (162, 28, 132, 30)]
for i, (al, ao, ar, ro) in enumerate(flick):                                                     # "... made of fire": flames
    P(5.05 + i * 0.27, arm_l=(al, ao), arm_r=(ar, ro), eyes=1.35, squash=(1.0, 1.05 if i % 2 else 0.97), head=(-6, 6 if i % 2 else -6, 0))
P(6.45, arm_l=(60, 15), arm_r=(15, 10), squash=(1, 1), head=(0, 0, 0), eyes=1.1)
for i in range(4):                                                                               # "so fire won't hurt them": no, no
    P(6.6 + i * 0.25, head=(0, 0, 22 if i % 2 else -22), arm_l=(100, 0, 25 if i % 2 else -25))
P(7.7, head=(0, 8, 0), arm_l=(30, 15, 0), eyes=0.55)                                             # knowing look
P(8.35, squash=(1.1, 0.88), arm_r=(65, 10), arm_l=(-25, 25), eyes=0.9, lean=(8, 0))             # wind up ...
P(8.75, loc=(bx, by, bz + 0.12), squash=(0.9, 1.16), arm_r=(-12, 5), arm_l=(172, 18), eyes=1.35, lean=(-6, 0), head=(-12, 0, 0))  # "Water will!"
P(8.95, loc=(bx, by, bz), squash=(1.14, 0.86))
P(9.15, squash=(1.0, 1.0))
P(9.7, arm_l=(165, 20), head=(-10, 4, 0))
P(9.95, loc=(bx, by - 0.22, bz), lean=(24, 0), head=(12, 12, 0), eyes=0.65, arm_l=(82, 2), arm_r=(15, 8))   # "And you, child,"
P(11.3, lean=(26, 0), head=(14, 14, 0), arm_l=(86, 0))
P(11.85, lean=(6, 0), head=(0, 0, 0), eyes=1.0, arm_l=(12, 14))
for i, t in enumerate((12.0, 12.5, 13.0)):                                                       # "will place it where I tell you": taps
    P(t, arm_r=(32, 6), head=(-4, 0, 0), squash=(1, 1.02))
    P(t + 0.16, arm_r=(6, 6), head=(12, 0, 0), squash=(1.05, 0.95))
P(13.6, lean=(-6, 0), head=(-8, -9, 0), arm_l=(35, 55), squash=(1, 1), eyes=1.0)               # pleased with himself
P(LENGTH, lean=(-6, 0), head=(-8, -10, 0))
for t in (2.15, 6.35, 10.2, 13.9):                                                               # blinks
    P(t, eyes=1.0); P(t + 0.05, eyes=0.08); P(t + 0.14, eyes=1.0)

# lip flap from the voice itself: mouth open with the loudness, held on twos
voice = C.opt("--voice", "/tmp/claude-0/vox/03.ogg")
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", voice, "-ac", "1", "-ar", "8000", "-f", "f32le", "-"], capture_output=True).stdout
a = np.frombuffer(pcm, dtype=np.float32)
step = 8000 // 12
for i in range(int((LENGTH - A0) * 12)):
    seg = a[i * step:(i + 1) * step]
    rms = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0
    K.pose(fen, F(A0 + i / 12.0), mouth=min(1.0, max(0.0, (rms - 0.01) * 9)))

# the staff stone flares blue on "Water will"
blue = C.light("POINT", (0, 0, 0), (0, 0, 0), 0, (0.35, 0.65, 1.0), 0.05, "water_flash")
blue.parent = fen["item"]; blue.location = (0, 0, 24 * VK.V)
for t, e in ((8.6, 0), (8.8, 260), (9.6, 120), (10.2, 0)):
    blue.data.energy = e; blue.data.keyframe_insert("energy", frame=F(t))

# ------------------------------------------------------------------ Tamsin behind, waving the carts through
tx, ty, tz = marks["tamsin"]
K.pose(tam, 1, loc=(tx, ty, tz), face=-25, arm_l=(25, 8), arm_r=(150, 40), head=(0, 0, 0), squash=(1, 1), eyes=1.0, mouth=0.2)
t = 0.0; i = 0
while t < LENGTH:
    up = i % 2 == 0
    startle = 8.75 <= t < 9.6
    K.pose(tam, F(t), arm_r=(170 if startle else (150 if up else 128), 20 if startle else (45 if up else 72)),
           squash=(1.0, 1.04 if up else 0.97), loc=(tx, ty, tz + (0.1 if startle and up else 0.0)),
           leg_r=(12 if up else -8, 0), leg_l=(-8 if up else 12, 0), head=(0, 8 if up else -8, -10), eyes=1.35 if startle else 1.0,
           mouth=0.8 if startle else (0.5 if up else 0.2))
    t += 0.42; i += 1

VK.stepped(K.objects(fen) + K.objects(tam), step=2)

# ------------------------------------------------------------------ camera: lively, close, wide lens
cam = C.camera(30)
look = bpy.data.objects.new("look", None); C.sc.collection.objects.link(look)
tr = cam.constraints.new("TRACK_TO"); tr.target = look; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
shots = [(0.0, (1.7, -3.7, 1.25), (0.5, 0.7, 0.75)), (0.9, (1.4, -3.3, 1.2), (0.4, 0.4, 0.8)),
         (1.25, (0.75, -2.25, 1.1), (0.2, 0.0, 1.05)), (1.9, (1.0, -2.4, 1.05), (0.5, 0.2, 1.0)),
         (2.7, (1.2, -2.5, 0.9), (0.6, 0.2, 1.35)), (3.45, (0.5, -1.85, 1.05), (0.2, 0.0, 1.05)),
         (4.6, (0.6, -2.0, 1.05), (0.2, 0.0, 1.05)), (5.0, (0.9, -2.9, 1.0), (0.2, 0.0, 1.05)),
         (8.1, (0.7, -2.6, 0.95), (0.2, 0.0, 1.05)), (8.55, (0.95, -2.1, 0.42), (0.2, 0.0, 1.2)),
         (9.6, (0.85, -2.0, 0.45), (0.2, 0.0, 1.2)), (9.95, (0.42, -1.6, 1.12), (0.2, -0.2, 1.02)),
         (11.6, (0.4, -1.5, 1.12), (0.2, -0.2, 1.02)), (12.1, (0.9, -2.6, 1.15), (0.3, 0.2, 0.95)),
         (LENGTH, (1.9, -4.2, 1.45), (0.3, 0.6, 0.8))]
for t, p, l in shots:
    cam.location = p; cam.keyframe_insert("location", frame=F(t))
    look.location = l; look.keyframe_insert("location", frame=F(t))
cam.data.dof.use_dof = True; cam.data.dof.focus_object = fen["head"]; cam.data.dof.aperture_fstop = 4.0

# light: low ember sun from the right, a warm fill from the camera side, so the figures always read
C.light("SUN", (0, 0, 10), (52, 0, 128), 2.6, (1.0, 0.72, 0.5), 0.08, "ember_sun")
fill = C.light("AREA", (0, 0, 0), (0, 0, 0), 120, (1.0, 0.86, 0.72), 2.5, "fill"); fill.parent = cam; fill.location = (-0.8, 0.6, 0.4)
rim = C.light("SPOT", (-1.5, 3.0, 2.6), (0, 0, 0), 300, (1.0, 0.45, 0.2), 0.3, "rim")
rt = rim.constraints.new("TRACK_TO"); rt.target = fen["head"]; rt.track_axis = "TRACK_NEGATIVE_Z"; rt.up_axis = "UP_Y"
C.sc.view_settings.exposure = 0.0
C.render(default_res=67, default_samples=16)
