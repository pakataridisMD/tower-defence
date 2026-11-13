"""Cut a story cinematic from rendered shots plus its voice lines (and optional music).

    python3 cut.py --film ember_warden --renders /path/renders --out film.mp4 [--step 6] [--music path.ogg] [--trailer dir]

Shot n's frames are in <renders>/<film>_<n>/f####.png (every --step-th frame for an animatic). Each shot is as long as
film.py made it (its voice line plus pad); its voice line starts 0.25 s in. Shots listed in story/reuse.json come from
the trailer renders (--trailer, frames in <dir>/<name>/) or are a montage of other films' shots, cut to the line's length."""
import json, os, subprocess, sys, glob, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
VOICE = json.load(open(os.path.join(HERE, "story", "voice.json")))
REUSE = json.load(open(os.path.join(HERE, "story", "reuse.json")))


def srt(text, dur, path, speaker):
    """Captions for a line not voiced yet: its sentences shown one after another, timed by length."""
    import re
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+|\n\n|\s/\s", text) if p.strip()]
    total = sum(len(p) for p in parts) or 1; t = 0.25; out = []
    for i, p in enumerate(parts):
        d = (dur - 0.5) * len(p) / total
        f = lambda x: "%02d:%02d:%02d,%03d" % (x // 3600, x % 3600 // 60, x % 60, (x - int(x)) * 1000)
        who = "" if speaker == "narrator" else speaker.replace("_", " ").title() + ": "
        out.append("%d\n%s --> %s\n%s%s\n" % (i + 1, f(t), f(t + d), who if i == 0 else "", p)); t += d
    open(path, "w").write("\n".join(out))


def frames_for(film, n, renders, trailer, step, fps):
    """The frame files for shot n (and the step they were rendered at), or None when the shot doesn't exist."""
    d = os.path.join(renders, "%s_%d" % (film, n))
    if os.path.isdir(d):
        return sorted(glob.glob(os.path.join(d, "f[0-9][0-9][0-9][0-9].png"))), step
    r = REUSE.get(film, {}).get(str(n))
    if isinstance(r, str) and trailer:
        fs = sorted(glob.glob(os.path.join(trailer, r, "f[0-9][0-9][0-9][0-9].png")))
        return (fs, 1) if fs else None
    if isinstance(r, list):
        line = VOICE.get(film, {}).get("%02d" % n)
        total = int(((line["duration"] + 0.4) if line else 6.0) * fps / step)
        share = max(1, total // len(r)); out = []
        for name in r:
            fs = sorted(glob.glob(os.path.join(renders, name, "f[0-9][0-9][0-9][0-9].png")))
            mid = len(fs) // 2
            out += fs[max(0, mid - share // 2):max(0, mid - share // 2) + share]
        return (out, step) if out else None
    return None


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    film = arg("--film"); renders = arg("--renders"); out = arg("--out"); step = int(arg("--step", "1"))
    music = arg("--music"); fps = 24
    tmp = tempfile.mkdtemp()
    parts = []
    trailer = arg("--trailer"); width = int(arg("--width", "1280"))   # every shot scaled to one size so they join
    last = max([int(k) for k in VOICE.get(film, {})] + [int(k) for k in REUSE.get(film, {})] + [0])
    for n in range(1, last + 1):
        got = frames_for(film, n, renders, trailer, step, fps)
        if not got:
            print("missing shot", n, "- skipped"); continue
        frames, st = got
        seq = os.path.join(tmp, "seq%02d" % n); os.makedirs(seq)
        for i, f in enumerate(frames):   # one numbered sequence per shot, whatever folders it came from
            os.symlink(f, os.path.join(seq, "f%05d.png" % i))
        dur = len(frames) * st / fps
        line = VOICE.get(film, {}).get("%02d" % n)
        clip = os.path.join(tmp, "s%02d.mp4" % n)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "%f" % (fps / st), "-i", os.path.join(seq, "f%05d.png")]
        if line and not line.get("file"):   # rewritten line, not re-voiced yet: show it as captions over silence
            sub = os.path.join(tmp, "s%02d.srt" % n); srt(line["text"], dur, sub, line["speaker"])
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex",
                    "[0:v]fps=%d,scale=%d:-2,subtitles=%s:force_style='FontName=DejaVu Sans,FontSize=16,Outline=1,MarginV=18'[v]" % (fps, width, sub),
                    "-map", "[v]", "-map", "1:a"]
        elif line:
            cmd += ["-i", os.path.join(arg("--root", REPO), line["file"]), "-filter_complex",
                    "[1:a]adelay=250|250,apad,atrim=0:%f[a];[0:v]fps=%d,scale=%d:-2[v]" % (dur, fps, width),
                    "-map", "[v]", "-map", "[a]"]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex",
                    "[0:v]fps=%d,scale=%d:-2[v]" % (fps, width), "-map", "[v]", "-map", "1:a", "-shortest"]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-ar", "44100", "-ac", "2", "-t", "%f" % dur, clip]
        subprocess.run(cmd, check=True)
        parts.append(clip)
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
