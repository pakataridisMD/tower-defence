"""Render whole story films on the Mac, shot by shot, then cut each film with its voice lines.

    python3 render_story.py --blender /Applications/Blender.app/Contents/MacOS/Blender --renders DIR --root VOICE_ROOT \
        [--films ember_intro storm_intro ...] [--samples 16] [--res 67] [--sprites]

--sprites: the chosen look (the game's pixel characters as cards in the 3D sets) and every film; use a new --renders folder.

Runs one Blender job at a time (Cycles GPU), so it never doubles up on the Mac's memory. Every shot renders into
<renders>/<film>_<n>/ and is resumable: run the same command again after a stop and finished frames are skipped.
After a film's shots are all done it is cut to <renders>/films/<film>.mp4 (cut.py, 1280 wide). Progress goes to
<renders>/story_progress.txt. Shots made from other renders (reuse/montage in story/reuse.json) are skipped here and
filled in by cut.py from the trailer renders (--trailer).

PAUSING FOR OTHER WORK (the user's rule, Nov 13: the films always give way to any other job on the Mac).
The run is paused while ~/.cinema_render_pause/ holds any file. Each job that needs the Mac adds its own file and
removes it when done, so several jobs can overlap; the run resumes once the folder is empty again:

    python3 render_story.py --pause ci-1234 [--wait 120]   # stop Blender now, wait until its GPU memory is free
    python3 render_story.py --resume ci-1234                # let the films carry on
    python3 render_story.py --status                        # rendering <film> <shot> / paused / idle / stopped

or from a shell without this script: mkdir -p ~/.cinema_render_pause && touch ~/.cinema_render_pause/ci-1234, wait
until ~/.cinema_render_state reads "paused" (or "idle"), and rm the file afterwards. A pause stops Blender at once
(only the frame it was drawing is lost; frames are written under a temporary name and renamed when whole) and the
shot carries on from its last finished frame when the run resumes."""
import json, os, signal, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = json.load(open(os.path.join(HERE, "story", "voice.json")))
REUSE = json.load(open(os.path.join(HERE, "story", "reuse.json")))
PAUSE_DIR = os.path.expanduser("~/.cinema_render_pause")
STATE = os.path.expanduser("~/.cinema_render_state")
# The films without a character that still needs fixing (Orrok, Ourra, Ignar, Brannoc, Vael-Orrun): safe to render now.
READY = ["ember_intro", "storm_intro", "nature_intro", "void_intro", "earth_intro",
         "storm_herald", "nature_herald", "void_herald", "earth_herald",
         "storm_warden", "nature_warden", "void_warden", "water_warden"]
# --sprites (the chosen look, Nov 13): every film, the lands first in play order, then the main story
LANDS = [l + "_" + p for l in ("ember", "storm", "nature", "water", "earth", "void") for p in ("intro", "herald", "warden")]
MAIN = ["prologue", "regents_counsel", "night_of_falling_stars", "long_night", "lumen_gate", "convergence_intro", "crossroads",
        "capital_prelude", "dawn", "heart_falls", "assault_intro", "the_turning", "the_high_king", "the_truth", "the_hush",
        "solenne_falls", "epilogue"]


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


# ------------------------------------------------------------------ pause / resume
def pausers():
    try:
        return sorted(f for f in os.listdir(PAUSE_DIR) if not f.startswith("."))
    except FileNotFoundError:
        return []


def set_state(text):
    tmp = STATE + ".tmp"; open(tmp, "w").write(text + "\n"); os.replace(tmp, STATE)


def get_state():
    try:
        return open(STATE).read().strip()
    except FileNotFoundError:
        return "stopped"


def wait_while_paused(renders):
    if not pausers():
        return
    log(renders, "paused for: %s" % ", ".join(pausers())); set_state("paused")
    while pausers():
        time.sleep(5)
    log(renders, "resumed")


def stop(p):
    """Stop a Blender job (and anything it started) at once; give it 20 s to exit, then kill it."""
    for sig, wait in ((signal.SIGTERM, 20), (signal.SIGKILL, 10)):
        try:
            os.killpg(p.pid, sig)
        except ProcessLookupError:
            return
        try:
            p.wait(wait); return
        except subprocess.TimeoutExpired:
            continue


def run_shot(cmd, logfile, renders):
    """Run one shot's Blender job, stopping it whenever something asks the Mac to pause and rerunning it after
    (it resumes from its last finished frame). Returns the exit code of the run that finished."""
    while True:
        wait_while_paused(renders)
        p = subprocess.Popen(cmd, stdout=open(logfile, "a"), stderr=subprocess.STDOUT, start_new_session=True)
        while p.poll() is None:
            if pausers():
                stop(p)
                break
            time.sleep(2)
        else:
            return p.returncode


def pause_cli():
    name = arg("--pause"); os.makedirs(PAUSE_DIR, exist_ok=True)
    open(os.path.join(PAUSE_DIR, name), "w").write("%s pid %d\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), os.getppid()))
    limit = float(arg("--wait", "120")); t0 = time.time()
    while get_state().split()[0] == "rendering" and time.time() - t0 < limit:   # until Blender has let go of the GPU
        time.sleep(1)
    print("films:", get_state())


def main():
    if "--pause" in sys.argv:
        return pause_cli()
    if "--resume" in sys.argv:
        try:
            os.remove(os.path.join(PAUSE_DIR, arg("--resume")))
        except FileNotFoundError:
            pass
        print("still paused for: %s" % ", ".join(pausers()) if pausers() else "films resume")
        return
    if "--status" in sys.argv:
        print(get_state() + ("  (paused for: %s)" % ", ".join(pausers()) if pausers() else ""))
        return
    blender = arg("--blender", "blender"); renders = os.path.abspath(arg("--renders")); root = arg("--root")
    sprite_look = "--sprites" in sys.argv
    films = args_list("--films") or (LANDS + MAIN if sprite_look else READY)
    samples = arg("--samples", "16"); res = arg("--res", "67")
    os.makedirs(os.path.join(renders, "films"), exist_ok=True)
    try:
        for film in films:
            lines = sorted(VOICE.get(film, {}))
            reused = REUSE.get(film, {})
            for n in range(1, len(lines) + 1):
                if "%02d" % n in reused or str(n) in reused:
                    continue
                out = os.path.join(renders, "%s_%d" % (film, n))
                if os.path.exists(os.path.join(out, "DONE")):
                    continue
                wait_while_paused(renders)
                log(renders, "start %s %d" % (film, n)); t0 = time.time()
                set_state("rendering %s %d" % (film, n))
                code = run_shot([blender, "-b", "-P", os.path.join(HERE, "film.py"), "--", out, "--film", film, "--shot", str(n),
                                 "--res", res, "--samples", samples, "--gpu"] + (["--sprites"] if sprite_look else []),
                                out + ".log", renders)
                set_state("idle")
                frames = len([f for f in os.listdir(out) if f.endswith(".png") and not f.endswith(".part.png")]) if os.path.isdir(out) else 0
                if code == 0 and frames:
                    open(os.path.join(out, "DONE"), "w").write("%d frames\n" % frames)
                    log(renders, "done %s %d: %d frames in %.0f min" % (film, n, frames, (time.time() - t0) / 60))
                else:
                    log(renders, "FAILED %s %d (exit %d, %d frames); see %s.log" % (film, n, code, frames, out))
            wait_while_paused(renders)
            set_state("idle")
            cut = [sys.executable, os.path.join(HERE, "cut.py"), "--film", film, "--renders", renders, "--width", "1280",
                   "--out", os.path.join(renders, "films", film + ".mp4")] + (["--root", root] if root else [])
            if arg("--trailer"):
                cut += ["--trailer", arg("--trailer")]
            r = subprocess.run(cut)
            log(renders, ("cut %s" if r.returncode == 0 else "CUT FAILED %s") % film)
        log(renders, "ALL_DONE")
    finally:
        set_state("stopped")


if __name__ == "__main__":
    main()
