#!/usr/bin/env bash
# Fetch the CC0 orchestral samples the music renderer plays (about 5 GB).
# Versilian Studios Chamber Orchestra 2, Community Edition: CC0 1.0 (public domain),
# free for any use, including commercial games, with no attribution required.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$here/.samples"
cd "$here/.samples"
if [ ! -d VSCO-2-CE ]; then
  git clone --depth 1 https://github.com/sgossner/VSCO-2-CE.git
fi
git -C VSCO-2-CE checkout -q 440300901dfe9275fd84e0b7763af1f8443ae62e 2>/dev/null || true
# Choir, celesta and tubular bells come from FluidR3_GM (MIT licence), played by FluidSynth.
if ! command -v fluidsynth >/dev/null || [ ! -f /usr/share/sounds/sf2/FluidR3_GM.sf2 ]; then
  echo "Also install: sudo apt-get install fluidsynth fluid-soundfont-gm"
fi
