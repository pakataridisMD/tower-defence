"""Cut a story cinematic from rendered shots plus its voice lines (and optional music).

    python3 cut.py --film ember_warden --renders /path/renders --out film.mp4 [--step 6] [--music path.ogg]

Shot n's frames are in <renders>/<film>_<n>/f####.png (every --step-th frame for an animatic). Each shot is as long as
film.py made it (its voice line plus pad); its voice line starts 0.25 s in."""
import json, os, subprocess, sys, glob, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
VOICE = json.load(open(os.path.join(HERE, "story", "voice.json")))


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    film = arg("--film"); renders = arg("--renders"); out = arg("--out"); step = int(arg("--step", "1"))
    music = arg("--music"); fps = 24
    tmp = tempfile.mkdtemp()
    parts = []
    n = 1
    while os.path.isdir(os.path.join(renders, "%s_%d" % (film, n))):
        d = os.path.join(renders, "%s_%d" % (film, n))
        frames = sorted(glob.glob(os.path.join(d, "f*.png")))
        dur = len(frames) * step / fps
        line = VOICE.get(film, {}).get("%02d" % n)
        clip = os.path.join(tmp, "s%02d.mp4" % n)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "%f" % (fps / step), "-pattern_type", "glob", "-i", os.path.join(d, "f*.png")]
        if line:
            cmd += ["-i", os.path.join(REPO, line["file"]), "-filter_complex",
                    "[1:a]adelay=250|250,apad,atrim=0:%f[a];[0:v]fps=%d,pad=ceil(iw/2)*2:ceil(ih/2)*2[v]" % (dur, fps),
                    "-map", "[v]", "-map", "[a]"]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex",
                    "[0:v]fps=%d,pad=ceil(iw/2)*2:ceil(ih/2)*2[v]" % fps, "-map", "[v]", "-map", "1:a", "-shortest"]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-ar", "44100", "-ac", "2", "-t", "%f" % dur, clip]
        subprocess.run(cmd, check=True)
        parts.append(clip); n += 1
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join("file '%s'\n" % p for p in parts))
    joined = os.path.join(tmp, "joined.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], check=True)
    if music:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", joined, "-stream_loop", "-1", "-i", music, "-filter_complex",
                        "[1:a]volume=0.35[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]", "-map", "0:v", "-map", "[a]",
                        "-c:v", "copy", "-c:a", "aac", out], check=True)
    else:
        os.replace(joined, out)
    print("cut", out, len(parts), "shots")


if __name__ == "__main__":
    main()
