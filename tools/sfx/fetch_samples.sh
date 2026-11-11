#!/usr/bin/env bash
# Fetch the recordings the sound recipes are built from (about 2.5 GB), into tools/sfx/.samples.
#
# * VSCO 2 Community Edition (Versilian Studios): CC0 1.0, free for any use including commercial games.
#   Only the folders the recipes use are checked out, at a pinned commit so renders stay the same.
# * Kokoro-82M text to speech (Apache-2.0) from the kokoro-onnx GitHub releases: the bosses' voices.
# * FluidR3_GM sound font (MIT): the sampled choir, played by FluidSynth (system package).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
dest="$here/.samples"
mkdir -p "$dest"
touch "$dest/.gdignore"
commit=440300901dfe9275fd84e0b7763af1f8443ae62e

if [ ! -e "$dest/vsco/LICENSE" ]; then
  rm -rf "$dest/vsco"
  git clone --filter=blob:none --no-checkout https://github.com/sgossner/VSCO-2-CE.git "$dest/vsco"
  git -C "$dest/vsco" sparse-checkout set --no-cone \
    /LICENSE /Readme.txt '/Brass/' '/Strings/' '/Percussion/' '/VSCO 1 Percussion/' '/Miscellania Raw/'
  git -C "$dest/vsco" checkout -q "$commit"
fi

if [ ! -f "$dest/kokoro/kokoro-v1.0.onnx" ]; then
  mkdir -p "$dest/kokoro"
  base=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
  curl -fL -o "$dest/kokoro/kokoro-v1.0.onnx" "$base/kokoro-v1.0.onnx"
  curl -fL -o "$dest/kokoro/voices-v1.0.bin" "$base/voices-v1.0.bin"
fi

python3 -c "import kokoro_onnx" 2>/dev/null || echo "Also run: pip install kokoro-onnx numpy scipy soundfile"
if ! command -v fluidsynth >/dev/null || [ ! -f /usr/share/sounds/sf2/FluidR3_GM.sf2 ]; then
  echo "Also install: sudo apt-get install fluidsynth fluid-soundfont-gm ffmpeg"
fi
ffmpeg -hide_banner -filters 2>/dev/null | grep -q rubberband || echo "ffmpeg needs the rubberband filter (librubberband)"
echo "Samples ready in $dest"
