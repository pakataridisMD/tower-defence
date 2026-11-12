#!/bin/bash
# Render a film in parallel chunks with Movie Maker, then join, add bloom and mux the audio.
# usage: cinema/render.sh OUT.mp4 AUDIO [CINE] [chunk boundaries in seconds...]
# Needs GODOT (path to a Godot 4.7 binary). In a headless Linux box it runs under xvfb-run.
set -e
OUT="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; AUDIO="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"; export CINE=${3:-seven_crowns}; shift 3 || true
CUTS=("$@"); [ ${#CUTS[@]} -eq 0 ] && CUTS=(0 14.4 24 36 51 62 78)
GODOT=${GODOT:-godot}; JOBS=${JOBS:-4}
cd "$(dirname "$0")"
W=$(mktemp -d)
run() { # $1 index $2 t0 $3 t1
  mkdir -p $W/$1
  local cmd=("$GODOT" --path . --write-movie $W/$1/f.png --fixed-fps 30 --resolution 1920x1080)
  if [ -z "$DISPLAY" ] && command -v xvfb-run >/dev/null; then
    T0=$2 T1=$3 xvfb-run -a -s "-screen 0 1920x1080x24" "${cmd[0]}" --rendering-driver opengl3 "${cmd[@]:1}" > $W/$1.log 2>&1
  else
    T0=$2 T1=$3 "${cmd[@]}" > $W/$1.log 2>&1
  fi
}
for ((i = 0; i < ${#CUTS[@]} - 1; i++)); do
  run $(printf %02d $i) ${CUTS[$i]} ${CUTS[$((i + 1))]} &
  while [ $(jobs -r | wc -l) -ge $JOBS ]; do sleep 2; done
done
wait
: > $W/list.txt
for d in $(ls -d $W/[0-9][0-9] | sort); do
  for f in $(ls $d/f*.png | sort); do echo "file '$f'" >> $W/list.txt; done
done
ffmpeg -loglevel error -y -r 30 -f concat -safe 0 -i $W/list.txt -i "$AUDIO" -filter_complex \
  "[0:v]settb=1/30,setpts=N,format=gbrp,split[a][b];[b]curves=all='0/0 0.6/0 1/1',gblur=sigma=16[g];[a][g]blend=all_mode=screen:all_opacity=0.45,format=yuv420p[v]" \
  -map "[v]" -map 1:a -r 30 -c:v libx264 -preset slow -crf 19 -c:a aac -b:a 256k -shortest -movflags +faststart "$OUT"
echo "frames: $(wc -l < $W/list.txt)  ->  $OUT"
rm -rf $W
