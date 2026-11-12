#!/bin/sh
# Fetch the CC0 MakeHuman data (base mesh, morph targets, game_engine weights, UV masks) that mh.py reads.
# Only data is used; MPFB's own add-on code is never run. Pinned to a known commit. Result: cinema/blender/mh/
set -e
here=$(cd "$(dirname "$0")" && pwd)
rev=6ff1eb358f6c1959ced77e79e6dd2406d9a71f49
tmp="$here/.mpfb2"
if [ ! -d "$tmp/.git" ]; then
  git clone --filter=blob:none --no-checkout https://github.com/makehumancommunity/mpfb2.git "$tmp"
fi
cd "$tmp"
git sparse-checkout set src/mpfb/data/3dobjs src/mpfb/data/mesh_metadata src/mpfb/data/targets \
  src/mpfb/data/rigs/standard src/mpfb/data/textures
git checkout -q "$rev"
rm -rf "$here/mh" && mkdir -p "$here/mh"
cp -R src/mpfb/data/3dobjs src/mpfb/data/mesh_metadata src/mpfb/data/targets src/mpfb/data/textures "$here/mh/"
mkdir -p "$here/mh/rigs/standard" && cp src/mpfb/data/rigs/standard/weights.game_engine.json "$here/mh/rigs/standard/"
cp LICENSE.ASSETS.md "$here/mh/"
echo "MakeHuman data ready in $here/mh"
