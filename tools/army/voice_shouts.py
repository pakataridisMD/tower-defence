#!/usr/bin/env python3
"""Records the army's battle shouts (data/army/shouts.json) with ElevenLabs v3.

Heroes speak with their cinematic voice from tools/voice/cast.json, so Tamsin on the battlefield is the Tamsin of the
cutscenes. Troop voices come from tools/army/voices.json (voice -> Voice Library id and owner); `--find` searches the
public Voice Library for each troop voice's casting note and writes the best match there to review.

Each line is mastered for the battlefield: close and dry with only a little air (outdoors, not a hall), tight
compression so it cuts through the battle, the hero's own style layers (Aurath's two voices, Orrok's depth), loudness
-16 LUFS, silence trimmed. Written to assets/audio/army/<voice or hero>/<line id>.ogg.

ElevenLabs replies are cached in tools/voice/cache/, so running it again only pays for new or changed lines.

usage:
  python3 tools/army/voice_shouts.py --cost                 characters to record (one credit each on v3)
  python3 tools/army/voice_shouts.py --find                 pick troop voices from the Voice Library
  python3 tools/army/voice_shouts.py [names...] [--force]   record (all, or only these voices/heroes)

Auth: the network secret for api.elevenlabs.io, or ELEVENLABS_API_KEY (see tools/voice/elevenlabs_tts.py).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "voice"))
import elevenlabs_tts as el  # noqa: E402
import narrate  # noqa: E402

SHOUTS = ROOT / "data" / "army" / "shouts.json"
VOICES = Path(__file__).resolve().parent / "voices.json"
OUT = ROOT / "assets" / "audio" / "army"
LUFS = -16.0
# Every shout is shouted: v3 reads the leading tag; lines with no tag of their own get this one.
DEFAULT_TAG = "[shouting]"
CALM_KINDS = {"death"}

# Search words for each troop voice in the public Voice Library (see shouts.py VOICES for the casting notes).
FIND = {
    "line": {"gender": "male", "age": "middle_aged", "words": ["gruff", "soldier", "sergeant", "british", "battle", "rough"]},
    "wall": {"gender": "female", "age": "young", "words": ["strong", "fierce", "soldier", "warrior", "british", "tough"]},
    "stone": {"gender": "male", "age": "old", "words": ["deep", "gravel", "dwarf", "rough", "old", "scottish"]},
    "veil": {"gender": "male", "age": "middle_aged", "words": ["cold", "calm", "quiet", "menac", "dark", "assassin"]},
    "order": {"gender": "female", "age": "middle_aged", "words": ["warm", "calm", "priest", "gentle", "steady", "british"]},
    "gale": {"gender": "female", "age": "young", "words": ["wild", "energetic", "fierce", "rider", "warrior", "loud"]},
}
# Troop voices that borrow a cast voice instead of a library pick.
FROM_CAST = {"crew": "fennick"}


def load() -> dict:
    return json.loads(SHOUTS.read_text(encoding="utf-8"))


def all_lines(data: dict) -> list[tuple[str, str, dict]]:
    """(voice or hero, kind, line) for every line."""
    out = []
    for table in ("lines", "champions"):
        for who, kinds in data[table].items():
            for kind, entries in kinds.items():
                out += [(who, kind, e) for e in entries]
    return out


def voice_ids() -> dict[str, dict]:
    """voice or hero -> {voice_id, style}."""
    cast = narrate.cast()
    picked = json.loads(VOICES.read_text(encoding="utf-8")) if VOICES.exists() else {}
    out = {hero: {"voice_id": role["voice_id"], "style": role.get("style", "mortal")} for hero, role in cast.items()}
    for voice, hero in FROM_CAST.items():
        if hero in cast:
            out[voice] = {"voice_id": cast[hero]["voice_id"], "style": "mortal"}
    for voice, spec in picked.items():
        if not voice.startswith("_"):
            out[voice] = {"voice_id": spec["voice_id"], "style": spec.get("style", "mortal")}
    return out


def spoken(text: str, kind: str) -> str:
    """The text sent to v3: its own tag, or a shout tag; names respelled the way the cinematics do."""
    respell = narrate.respellings()
    for name, said in respell.items():
        text = text.replace(name, said)
    if text.lstrip().startswith("[") or kind in CALM_KINDS:
        return text
    return f"{DEFAULT_TAG} {text}"


def master(samples: np.ndarray, sr: int, style: str, out: Path) -> float:
    preset = narrate.STYLES.get(style, {})
    chain = ["highpass=f=90", "lowshelf=f=180:g=1.5", "equalizer=f=2800:t=q:w=1.4:g=2.5",
             "equalizer=f=5500:t=q:w=2:g=-2", "lowpass=f=12500",
             "acompressor=threshold=-24dB:ratio=3.5:attack=4:release=120:makeup=2",
             "alimiter=limit=0.9:attack=2:release=40", "apad=pad_dur=0.25", f"loudnorm=I={LUFS}:TP=-1:LRA=6",
             "aresample=44100"]
    if preset.get("semitones"):
        chain.insert(0, f"rubberband=pitch={2 ** (preset['semitones'] / 12):.4f}:formant=preserved")
    graph = ",".join(chain)
    layers = preset.get("layers") or []
    if layers:
        names = [f"l{i}" for i in range(len(layers))]
        graph = (f"[0:a]asplit={len(layers) + 1}[dry]{''.join(f'[{n}s]' for n in names)};"
                 + "".join(f"[{n}s]rubberband=pitch={r}:formant=shifted,volume={g}[{n}];" for n, (r, g) in zip(names, layers))
                 + f"[dry]{''.join(f'[{n}]' for n in names)}amix=inputs={len(layers) + 1}:normalize=0,{graph}")
    with tempfile.TemporaryDirectory() as tmp:
        raw, done = Path(tmp) / "raw.wav", Path(tmp) / "m.wav"
        # Outdoors: a short, light room only, so the voice sits in the battle and not in a hall.
        sf.write(raw, narrate._room(samples, sr, rt60=0.45, wet=0.05 + 0.5 * preset.get("room", 0.0) * 0.3), sr, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw), "-filter_complex" if layers else "-af", graph,
                        "-ac", "1", str(done)], check=True)
        narrate._level(done, LUFS)
        x, sr = sf.read(done)
        loud = np.where(np.abs(x) > 0.004)[0]
        if len(loud):
            x = x[max(0, loud[0] - int(0.02 * sr)): loud[-1] + int(0.12 * sr)]
        sf.write(done, x, sr, subtype="FLOAT")
        narrate._write_ogg(done, out)
    return sf.info(out).duration


def record(names: list[str], force: bool) -> None:
    data = load()
    ids = voice_ids()
    missing = sorted({who for who, _, _ in all_lines(data) if who not in ids})
    if missing:
        print("No voice yet for:", ", ".join(missing), "- run --find first, or add them to", VOICES)
    durations = {}
    for who, kind, entry in all_lines(data):
        if names and who not in names or who not in ids:
            continue
        out = OUT / who / f"{entry['id']}.ogg"
        if out.exists() and not force:
            durations[entry["id"]] = sf.info(out).duration
            continue
        mp3 = el.tts(spoken(entry["text"], kind), ids[who]["voice_id"], stability=0.0)
        samples, sr = el.decode(mp3)
        durations[entry["id"]] = round(master(samples, sr, ids[who]["style"], out), 2)
        print(f"{entry['id']:28s} {durations[entry['id']]:5.2f}s  {entry['text']}")
    (OUT / "durations.json").write_text(json.dumps(dict(sorted(durations.items())), indent=1) + "\n")


def find() -> None:
    picked = json.loads(VOICES.read_text(encoding="utf-8")) if VOICES.exists() else {}
    for voice, spec in FIND.items():
        query = urllib.parse.urlencode({"gender": spec["gender"], "age": spec["age"], "language": "en",
                                        "page_size": 60, "sort": "trending"})
        shared = el.api_get(f"/shared-voices?{query}").get("voices", [])
        taken = {p.get("voice_id") for k, p in picked.items() if k != voice}
        best, best_score = None, -1
        for v in shared:
            if v["voice_id"] in taken:
                continue
            desc = ((v.get("description") or "") + " " + (v.get("name") or "")).lower()
            score = sum(w in desc for w in spec["words"])
            if score > best_score:
                best, best_score = v, score
        if best is None:
            continue
        el.api_post_json(f"/voices/add/{best['public_owner_id']}/{best['voice_id']}", {"new_name": f"army {voice}: {best['name']}"})
        picked[voice] = {"voice": best["name"], "voice_id": best["voice_id"], "owner": best.get("public_owner_id"),
                         "style": "mortal", "why": (best.get("description") or "")[:160]}
        print(voice, "->", best["name"], "|", (best.get("description") or "")[:100])
    picked["_about"] = "Troop voices for the army's shouts (tools/army/voice_shouts.py). Heroes use tools/voice/cast.json."
    VOICES.write_text(json.dumps(dict(sorted(picked.items())), indent=1) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--cost", action="store_true")
    ap.add_argument("--find", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.cost:
        lines = all_lines(load())
        chars = sum(len(spoken(e["text"], k)) for who, k, e in lines if not a.names or who in a.names)
        print(f"{len(lines)} lines, about {chars} characters (credits on eleven_v3)")
        return
    if a.find:
        find()
        return
    record(a.names, a.force)


if __name__ == "__main__":
    main()
