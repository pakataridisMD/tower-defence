"""Cut the 3D story trailer from the rendered shot clips, the prologue voice lines and the prologue score.

    python3 cut_trailer.py --shots DIR --out trailer.mp4 [--root REPO_OR_ASSET_ROOT] [--width 1280]

DIR holds s01_rift.mp4 ... s09_queen.mp4 (the Mac's preview encodes). Voice files come from
<root>/assets/story/voice/prologue/NN.ogg and the music from <root>/assets/story/music/prologue.ogg.
The edit (shot order, speed, which voice line starts when and which part of it plays) is the PLAN below."""
import os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# (shot clip, speed): 0.8 plays a shot slower, so it lasts longer.
SHOTS = [("s01_rift", 1.0), ("s02_gate_shut", 1.0), ("s03_gate_opens", 1.0), ("s04_towers", 1.0), ("s05_oswin", 1.0),
         ("s06_fall", 1.0), ("s07_unbound", 1.0), ("s08_hold", 0.8), ("s09_queen", 1.0)]
# (voice line, start in the trailer, from, to): seconds; `to` None = to the end of the line.
VOICE = [("03", 0.5, 0, None),       # the six monarchs drove him down the Rift...
         ("07", 14.6, 0, None),      # this spring somebody unlocked the Black Gate
         ("08", 24.9, 0, None),      # Oswin turned the light of all his towers on it
         ("09", 40.3, 0, None),      # then the ground gave way, and he fell through
         ("10", 50.2, 0, None),      # six armies... each Herald went home
         ("12", 70.4, 0, 7.6),       # I am Ysolde, Queen of Solenne. You are a Spirewright...
         ("12", 79.5, 15.9, None)]   # Hold the road to each town. Kill its Herald. Free its Warden. Hold the road.
TITLE_SECONDS = 20.0                 # black title card after the last shot, under the last words
MUSIC_FROM = 0.0                     # where in the prologue score the trailer starts


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def run(cmd):
    subprocess.run(cmd, check=True)


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


def main():
    shots = arg("--shots"); out = arg("--out"); root = arg("--root", REPO); width = int(arg("--width", "1280"))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tmp = tempfile.mkdtemp(); parts = []
    for name, speed in SHOTS:   # every shot to one size and rate, speed applied
        p = os.path.join(tmp, name + ".mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(shots, name + ".mp4"), "-an", "-vf",
             "setpts=%f*PTS,fps=24,scale=%d:-2,setsar=1" % (1 / speed, width), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", p])
        parts.append(p)
    height = int(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=height",
                                          "-of", "csv=p=0", parts[0]]))
    # the title card: black, the title fades in at 6 s, then the credit line at 9 s. The text layers are PNGs from
    # title/make_title_pngs.py, so this works with an ffmpeg built without drawtext (the Mac's Homebrew one).
    title_dir = os.path.join(HERE, "title")
    card = os.path.join(tmp, "card.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=%dx%d:r=24:d=%f" % (width, height, TITLE_SECONDS),
         "-loop", "1", "-framerate", "24", "-i", os.path.join(title_dir, "title.png"),
         "-loop", "1", "-framerate", "24", "-i", os.path.join(title_dir, "credit.png"), "-filter_complex",
         "[1:v]scale=%d:%d,format=rgba,fade=t=in:st=6:d=1.5:alpha=1[t];[2:v]scale=%d:%d,format=rgba,fade=t=in:st=9:d=1.5:alpha=1[c];"
         "[0:v][t]overlay=shortest=1[a];[a][c]overlay=shortest=1,format=yuv420p" % (width, height, width, height),
         "-t", "%f" % TITLE_SECONDS, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", card])
    parts.append(card)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join("file '%s'\n" % p for p in parts))
    video = os.path.join(tmp, "video.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])
    total = dur(video)
    # the sound: the score under everything (ducked a little), the voice lines laid on top at their times
    ins = ["-i", video, "-ss", str(MUSIC_FROM), "-i", os.path.join(root, "assets", "story", "music", "prologue.ogg")]
    filt = ["[1:a]atrim=0:%f,afade=t=in:d=1.5,afade=t=out:st=%f:d=4,volume=0.42[m]" % (total, total - 4)]
    mix = ["[m]"]
    for i, (line, at, a, b) in enumerate(VOICE):
        ins += ["-i", os.path.join(root, "assets", "story", "voice", "prologue", line + ".ogg")]
        trim = "atrim=%f%s,asetpts=PTS-STARTPTS" % (a, (":%f" % b) if b else "")
        filt.append("[%d:a]%s,adelay=%d|%d[v%d]" % (i + 2, trim, at * 1000, at * 1000, i))
        mix.append("[v%d]" % i)
    filt.append("%samix=inputs=%d:duration=first:normalize=0,alimiter=limit=0.95[a]" % ("".join(mix), len(mix)))
    run(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[a]",
                                                         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", "%f" % total, out])
    print("trailer", out, "%.1f s" % total)


if __name__ == "__main__":
    main()
