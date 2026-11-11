#!/usr/bin/env bash
# Downloads the Kokoro-82M ONNX model (Apache-2.0) used by narrate.py.
set -euo pipefail
dir="$(cd "$(dirname "$0")" && pwd)/model"
mkdir -p "$dir"
base=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -f "$dir/$f" ] || curl -fL -o "$dir/$f" "$base/$f"
done
echo "Model ready in $dir"
