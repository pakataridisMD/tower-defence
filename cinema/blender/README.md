# Blender cinematic tests

3D look tests for the cutscenes and trailers (the user chose our own 3D in Blender on 2026-11-12). Design only.

- `gate_test.py`: "The Black Gate" layout test (canyon, colossal gate, lantern column, Tamsin stand-in).
  `blender -b -P cinema/blender/gate_test.py -- OUT_DIR --frames 1 150 --res 100 --samples 64`
  or `python gate_test.py -- ...` with the `bpy` module (pip install bpy==5.2.3, Python 3.13).
- Characters are CC0 stand-ins from KayKit (Kay Lousberg), cloned to `KAYKIT` (default /home/user/assets3d):
  KayKit-Character-Pack-Adventures-1.0 and KayKit-Character-Pack-Skeletons-1.0 on GitHub.
- `ph/`: CC0 scanned rocks, textures and HDRIs from Poly Haven (polyhaven.com), used when present.
