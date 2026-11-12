#!/bin/bash
# Render a film in parallel chunks with Movie Maker, then join, add bloom and the sound.
# usage: cinema/render.sh OUT.mp4 AUDIO [CINE] [chunk boundaries in seconds...]
#   AUDIO is a finished mix, or "auto" to build one from the film's own cues (music + voice lines).
#   OUT.ogv makes a Theora film for the game (assets/story/video/<id>.ogv) plus <id>.json with the shot start
#   times, so the game's player draws the subtitles; the film itself is rendered without them.
#   Cutscenes: SCENE=earth_herald cinema/render.sh out.mp4 auto cutscene   (STORY_ROOT=<checkout> for another branch)
# Needs GODOT (path to a Godot 4.7 binary) and ffmpeg. In a headless Linux box it runs under xvfb-run.
set -e
OUT="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
AUDIO=$2
[ "$AUDIO" != auto ] && AUDIO="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
export CINE=${3:-seven_crowns}; shift 3 || true
CUTS=("$@")
GODOT=${GODOT:-godot}; JOBS=${JOBS:-4}
cd "$(dirname "$0")"
W=$(mktemp -d)
case $OUT in *.ogv) export SUBS=0 ;; esac

# The film's length and sound cues.
CUES_OUT=$W/cues.tsv "$GODOT" --headless --path . --quit-after 600 > $W/cues.log 2>&1 || true
touch $W/cues.tsv
LEN=$(awk -F'\t' '$1 == "length" { print $3 }' $W/cues.tsv)
[ -z "$LEN" ] && { cat $W/cues.log; echo "could not read the film's length"; exit 1; }

if [ ${#CUTS[@]} -eq 0 ]; then
  if [ "$CINE" = seven_crowns ]; then
    CUTS=(0 14.4 24 36 51 62 78)
  else # equal chunks, on 0.1 s steps so every boundary is a whole frame
    CUTS=($(awk -v l=$LEN -v n=$JOBS 'BEGIN { for (i = 0; i < n; i++) printf "%.1f ", int(l * i / n * 10) / 10; print l }'))
  fi
fi

if [ "$AUDIO" = auto ]; then
  args=(); filt=""; nv=0; music=""
  while IFS=$'\t' read -r kind file start; do
    case $kind in
      music) music=$file ;;
      voice)
        args+=(-i "$file")
        ms=$(awk -v s=$start 'BEGIN { printf "%d", s * 1000 }')
        filt+="[$nv:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=$ms|$ms[v$nv];"
        nv=$((nv + 1)) ;;
    esac
  done < $W/cues.tsv
  fade=$(awk -v l=$LEN 'BEGIN { print l - 1.5 }')
  if [ $nv -gt 0 ]; then
    for ((i = 0; i < nv; i++)); do filt+="[v$i]"; done
    filt+="amix=inputs=$nv:normalize=0:duration=longest,apad[vo];"
  else
    filt+="anullsrc=r=48000:cl=stereo[vo];"
  fi
  if [ -n "$music" ]; then
    args+=(-i "$music")
    # The music sits under the lines and ducks about 7 dB while someone speaks.
    filt+="[vo]asplit[vo1][key];[$nv:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=-3dB,apad[m];"
    filt+="[m][key]sidechaincompress=threshold=0.02:ratio=4:attack=60:release=600:makeup=1[md];"
    filt+="[md][vo1]amix=inputs=2:normalize=0:duration=first,"
  else
    filt+="[vo]"
  fi
  filt+="atrim=0:$LEN,afade=t=out:st=$fade:d=1.5,alimiter=limit=0.95[out]"
  ffmpeg -loglevel error -y "${args[@]}" -filter_complex "$filt" -map "[out]" -c:a pcm_s16le $W/mix.wav
  AUDIO=$W/mix.wav
fi

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
grep -h "SCRIPT ERROR\|^ERROR" $W/[0-9][0-9].log | sort | uniq -c | head -20 || true
: > $W/list.txt
for d in $(ls -d $W/[0-9][0-9] | sort); do
  for f in $(ls $d/f*.png | sort); do echo "file '$f'" >> $W/list.txt; done
done
BLOOM="[0:v]settb=1/30,setpts=N,format=gbrp,split[a][b];[b]curves=all='0/0 0.6/0 1/1',gblur=sigma=16[g];[a][g]blend=all_mode=screen:all_opacity=0.45,format=yuv420p[v]"
case $OUT in
  *.ogv)
    ffmpeg -loglevel error -y -r 30 -f concat -safe 0 -i $W/list.txt -i "$AUDIO" -filter_complex "$BLOOM" \
      -map "[v]" -map 1:a -r 30 -c:v libtheora -b:v 5M -c:a libvorbis -q:a 6 -shortest "$OUT"
    awk -F'\t' 'BEGIN { printf "{\"shots\": [" } $1 == "shot" { printf "%s%.2f", n++ ? ", " : "", $3 } END { print "]}" }' \
      $W/cues.tsv > "${OUT%.ogv}.json" ;;
  *)
    ffmpeg -loglevel error -y -r 30 -f concat -safe 0 -i $W/list.txt -i "$AUDIO" -filter_complex "$BLOOM" \
      -map "[v]" -map 1:a -r 30 -c:v libx264 -preset slow -crf 19 -c:a aac -b:a 256k -shortest -movflags +faststart "$OUT" ;;
esac
echo "frames: $(wc -l < $W/list.txt)  ->  $OUT"
[ -n "$KEEP" ] && echo "kept $W" || rm -rf $W
