"""Render whole story films on the Mac, shot by shot, then cut each film with its voice lines.

    python3 render_story.py --blender /Applications/Blender.app/Contents/MacOS/Blender --renders DIR --root VOICE_ROOT \
        [--films ember_intro storm_intro ...] [--samples 16] [--res 67]

Runs one Blender job at a time (Cycles GPU), so it never doubles up on the Mac's memory. Every shot renders into
<renders>/<film>_<n>/ and is resumable: run the same command again after a stop and finished frames are skipped.
After a film's shots are all done it is cut to <renders>/films/<film>.mp4 (cut.py, 1280 wide). Progress goes to
<renders>/story_progress.txt. Shots made from other renders (reuse/montage in story/reuse.json) are skipped here and
filled in by cut.py from the trailer renders (--trailer)."""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = json.load(open(os.path.join(HERE, "story", "voice.json")))
REUSE = json.load(open(os.path.join(HERE, "story", "reuse.json")))
# The films without a character that still needs fixing (Orrok, Ourra, Ignar, Brannoc, Vael-Orrun): safe to render now.
READY = ["ember_intro", "storm_intro", "nature_intro", "void_intro", "earth_intro",
         "storm_herald", "nature_herald", "void_herald", "earth_herald",
         "storm_warden", "nature_warden", "void_warden", "water_warden"]


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def args_list(name):
    if name not in sys.argv:
        return None
    out = []
    for a in sys.argv[sys.argv.index(name) + 1:]:
        if a.startswith("--"):
            break
        out.append(a)
    return out


def log(renders, text):
    line = "%s %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), text)
    print(line, flush=True)
    open(os.path.join(renders, "story_progress.txt"), "a").write(line + "\n")


def main():
    blender = arg("--blender", "blender"); renders = os.path.abspath(arg("--renders")); root = arg("--root")
    films = args_list("--films") or READY
    samples = arg("--samples", "16"); res = arg("--res", "67")
    os.makedirs(os.path.join(renders, "films"), exist_ok=True)
    for film in films:
        lines = sorted(VOICE.get(film, {}))
        reused = REUSE.get(film, {})
        for n in range(1, len(lines) + 1):
            if "%02d" % n in reused or str(n) in reused:
                continue
            out = os.path.join(renders, "%s_%d" % (film, n))
            if os.path.exists(os.path.join(out, "DONE")):
                continue
            log(renders, "start %s %d" % (film, n)); t0 = time.time()
            r = subprocess.run([blender, "-b", "-P", os.path.join(HERE, "film.py"), "--", out, "--film", film, "--shot", str(n),
                                "--res", res, "--samples", samples, "--gpu"],
                               stdout=open(out + ".log", "w"), stderr=subprocess.STDOUT)
            frames = len([f for f in os.listdir(out) if f.endswith(".png")]) if os.path.isdir(out) else 0
            if r.returncode == 0 and frames:
                open(os.path.join(out, "DONE"), "w").write("%d frames\n" % frames)
                log(renders, "done %s %d: %d frames in %.0f min" % (film, n, frames, (time.time() - t0) / 60))
            else:
                log(renders, "FAILED %s %d (exit %d, %d frames); see %s.log" % (film, n, r.returncode, frames, out))
        cut = [sys.executable, os.path.join(HERE, "cut.py"), "--film", film, "--renders", renders, "--width", "1280",
               "--out", os.path.join(renders, "films", film + ".mp4")] + (["--root", root] if root else [])
        if arg("--trailer"):
            cut += ["--trailer", arg("--trailer")]
        r = subprocess.run(cut)
        log(renders, ("cut %s" if r.returncode == 0 else "CUT FAILED %s") % film)
    log(renders, "ALL_DONE")


if __name__ == "__main__":
    main()
