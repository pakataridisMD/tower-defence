#!/usr/bin/env bash
# Export a double-clickable macOS app (universal: Apple Silicon + Intel) of the game.
#
#   tools/build/export_macos.sh [godot-binary]
#
# Needs Godot 4.7.2 and its export templates installed (Editor > Manage Export Templates, or unzip
# templates/macos.zip and templates/version.txt from the .tpz into
# ~/.local/share/godot/export_templates/4.7.2.stable on Linux,
# ~/Library/Application Support/Godot/export_templates/4.7.2.stable on macOS).
# Writes builds/macos/Tower Defence 2D.zip. The app is ad-hoc signed, not notarized.
set -euo pipefail
cd "$(dirname "$0")/../.."
GODOT="${1:-godot}"
mkdir -p builds/macos
"$GODOT" --headless --import
"$GODOT" --headless --export-release "macOS" "builds/macos/Tower Defence 2D.zip" 2>&1 | tee builds/macos/export.log
if grep -E "^ERROR: (Cannot export|Project export)" builds/macos/export.log; then exit 1; fi
ls -la builds/macos
