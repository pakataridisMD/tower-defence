#!/usr/bin/env python3
"""Voices for the story cinematics: the narrator and every speaking character.

Reads data/story/cinematics/<id>.json and writes one Ogg Vorbis file per shot to
assets/story/voice/<id>/<NN>.ogg (NN = 01, 02, ...), which the cinematic player
picks up. Shots without "text" are skipped.

The narrator (Queen Ysolde) is the ElevenLabs v3 voice Elariel (preset regal_el).
Every other speaker gets their own ElevenLabs voice from cast.json, placed with a
style (Heralds sound hollowed, Wardens elemental, Vael-Orrun vast). Each sentence
is acted from direction.json. Kokoro-82M (Apache-2.0, run locally) remains as a
free offline fallback (presets regal, warm, elder, whisper, hush).

Setup (once):
    python3 -m venv .venv-voice
    .venv-voice/bin/pip install kokoro-onnx soundfile
    tools/voice/fetch_model.sh          # ~350 MB into tools/voice/model/ (git-ignored)

Use:
    .venv-voice/bin/python tools/voice/narrate.py                 # every cinematic
    .venv-voice/bin/python tools/voice/narrate.py opening         # one cinematic
    .venv-voice/bin/python tools/voice/narrate.py --text "Line" --out line.ogg
    .venv-voice/bin/python tools/voice/narrate.py --preset elder opening
    .venv-voice/bin/python tools/voice/narrate.py --speakers cast     # only the characters

Needs ffmpeg with the rubberband filter on PATH.
"""
from __future__ import annotations

import argparse
import json
import re
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path(__file__).resolve().parent / "model"
CINEMATICS = ROOT / "data" / "story" / "cinematics"
VOICE_OUT = ROOT / "assets" / "story" / "voice"

# Voice = weighted blend of Kokoro voice styles + delivery + mastering.
# Optional keys: "semitones" (pitch shift; sounds robotic, avoid), "room" (hall wetness, default 0.16),
# "rt60" (hall length in seconds, default 1.1), "master": "trailer" (close, dry, punchy),
# "sentence_gap" / "para_gap" (pause lengths in seconds).
PRESETS = {
    # Low, calm, storybook-ancient. Kore is the lowest Kokoro female voice;
    # a little Nicole adds breath and intimacy.
    "elder": {
        "voices": {"af_kore": 0.7, "af_nicole": 0.3},
        "lang": "en-us", "speed": 0.88,
    },
    # Breathier, closer to the mic: for quiet or sad beats.
    "whisper": {
        "voices": {"af_nicole": 1.0},
        "lang": "en-us", "speed": 0.9, "room": 0.1,
    },
    # The narrator (chosen by Doctor Paris, 2026-11-11): British, crisp, regal.
    "regal": {
        "voices": {"bf_emma": 0.6, "af_kore": 0.4},
        "lang": "en-gb", "speed": 0.8, "room": 0.07, "rt60": 0.9, "master": "trailer",
        "sentence_gap": 0.75, "para_gap": 1.6,  # slow and dramatic (Doctor Paris, 2026-11-11)
    },
    # ElevenLabs v3: real acting from emotion tags (Doctor Paris chose it, 2026-11-11).
    # voice_id is filled in from the voice audition (tools/voice/audition_elevenlabs.py).
    "regal_el": {
        "engine": "elevenlabs",
        "voice_id": os.environ.get("NARRATOR_VOICE_ID", "ksryVoNAGZT8GxWCTiVm"),  # Elariel (Voice Library), picked by Doctor Paris
        "stability": 0.0, "para_gap": 1.2, "room": 0.05, "rt60": 0.9, "master": "trailer",
    },
    # Free offline fallback for the Hush (the cast voices it with ElevenLabs):
    # flat and slow, then layered an octave down and a fifth up.
    "hush": {
        "voices": {"af_nicole": 0.5, "bf_isabella": 0.5}, "lang": "en-us", "speed": 0.78,
        "sentence_gap": 0.9, "para_gap": 1.4, "room": 0.0, "master": "hush",
    },
    # Warmer and more British, same cinematic hall: the other finalist.
    "warm": {
        "voices": {"bf_emma": 0.8, "af_kore": 0.2},
        "lang": "en-gb", "speed": 0.82, "room": 0.07, "rt60": 0.9, "master": "trailer",
        "sentence_gap": 0.75, "para_gap": 1.6,
    },
}

# Speaker ids voiced by the narrator. Queen Ysolde is the narrator, so her
# in-scene lines use the same voice.
NARRATOR_SPEAKERS = {"narrator", "ysolde"}
# Every other speaking character has their own ElevenLabs voice in cast.json.
CAST_FILE = Path(__file__).resolve().parent / "cast.json"

# How a character's voice is placed and treated, on top of the narrator's ElevenLabs preset.
# "layers": extra copies of the voice at [pitch ratio, gain] under the dry voice;
# "fx": an ffmpeg filter chain run before mastering.
STYLES = {
    "mortal": {},                                               # close and dry, like the narrator
    "seer": {"room": 0.1, "rt60": 1.6},                         # a little cold air around her
    "warden": {"room": 0.14, "rt60": 1.8},                      # elemental: a bigger, older space
    "herald": {"room": 0.1, "rt60": 1.4,                        # hollowed: thin chorus, scooped mids
               "fx": "chorus=0.7:0.9:35|52:0.3|0.25:0.3|0.45:1.6|2.1,equalizer=f=900:t=q:w=1.5:g=-3"},
    "sovereign": {"room": 0.2, "rt60": 2.6, "layers": [[0.5, 0.3]]},   # Vael-Orrun: dark hall, sub-octave shadow
    "twin": {"room": 0.14, "rt60": 1.8, "layers": [[0.5, 0.8]]},       # Aurath speaks in two voices at once
    "titan": {"room": 0.14, "rt60": 2.0, "semitones": -2},             # Orrok: stone giant
    # The hidden god. Every word must land: the clean take stays on top at full level,
    # with only a faint octave below and a short, light room. No echo, no lowpass.
    "hush": {"room": 0.06, "rt60": 1.0, "layers": [[0.5, 0.2]], "lufs": -16.0},
}


def cast() -> dict[str, dict]:
    if not CAST_FILE.exists():
        return {}
    return json.loads(CAST_FILE.read_text(encoding="utf-8")).get("speakers", {})


def speaker_preset(speaker: str, narrator: str = "regal_el") -> dict | None:
    """The preset that voices a speaker, or None if they stay as subtitles."""
    if speaker in NARRATOR_SPEAKERS:
        return PRESETS[narrator]
    role = cast().get(speaker)
    if not role:
        return None
    return {**PRESETS["regal_el"], **STYLES[role.get("style", "mortal")], "voice_id": role["voice_id"]}

_kokoro = None


def kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        onnx, voices = MODEL_DIR / "kokoro-v1.0.onnx", MODEL_DIR / "voices-v1.0.bin"
        if not onnx.exists():
            sys.exit(f"Model missing: run tools/voice/fetch_model.sh (looked in {MODEL_DIR})")
        _kokoro = Kokoro(str(onnx), str(voices))
    return _kokoro


def style(preset: dict):
    k = kokoro()
    mix = None
    for name, weight in preset["voices"].items():
        s = k.get_voice_style(name) * weight
        mix = s if mix is None else mix + s
    return mix


SENTENCE_GAP = 0.32   # seconds between sentences
PARAGRAPH_GAP = 0.9   # seconds for a blank line in the text


def _trim(x: np.ndarray, sr: int, floor: float = 0.004) -> np.ndarray:
    """Cut the model's own leading/trailing silence so our pauses are exact."""
    loud = np.flatnonzero(np.abs(x) > floor)
    if loud.size == 0:
        return x[:0]
    pad = int(sr * 0.03)
    return x[max(0, loud[0] - pad): loud[-1] + pad]


DIRECTION_FILE = Path(__file__).resolve().parent / "direction.json"


def direction_for(cid: str | None) -> dict[str, dict]:
    """sentence text -> emotion settings, from tools/voice/direction.json."""
    if not cid or not DIRECTION_FILE.exists():
        return {}
    doc = json.loads(DIRECTION_FILE.read_text(encoding="utf-8"))
    emotions = doc.get("emotions", {})
    for name, settings in emotions.items():
        EMOTION_NAMES[id(settings)] = name
    return {line: emotions[name] for line, name in doc.get("lines", {}).get(cid, {}).items()
            if name in emotions}


def speak(text: str, preset: dict, direction: dict | None = None) -> tuple[np.ndarray, int]:
    """Raw speech, one sentence at a time with natural breaths between them.
    A blank line in the text becomes a longer, dramatic pause. Each sentence can
    be acted with an emotion from direction.json (speed, voice, loudness, pause)."""
    k, voice = kokoro(), style(preset)
    direction = direction or {}
    out, sr = [], 24000
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    for pi, para in enumerate(paras):
        sentences = [x for x in re.split(r"(?<=[.!?])\s+", " ".join(para.split())) if x]
        for si, sentence in enumerate(sentences):
            emo = direction.get(sentence, {})
            said = sentence[:-1] + "!" if emo.get("exclaim") and sentence.endswith(".") else sentence
            v = style({"voices": emo["voices"]}) if "voices" in emo else voice
            samples, sr = k.create(said, voice=v, speed=preset["speed"] * emo.get("speed", 1.0),
                                   lang=preset["lang"])
            if emo.get("pause") and out:
                out.append(np.zeros(int(sr * emo["pause"]), dtype=np.float32))
            out.append(_trim(samples, sr) * 10 ** (emo.get("gain", 0) / 20))
            last_in_para = si == len(sentences) - 1
            if not (last_in_para and pi == len(paras) - 1):
                gap = (preset.get("para_gap", PARAGRAPH_GAP) if last_in_para
                       else preset.get("sentence_gap", SENTENCE_GAP))
                out.append(np.zeros(int(sr * gap), dtype=np.float32))
    return np.concatenate(out).astype(np.float32), sr


EMOTION_NAMES: dict[int, str] = {}  # id(emotion settings) -> emotion name, for ElevenLabs tags


def speak_elevenlabs(text: str, preset: dict, direction: dict | None = None) -> tuple[np.ndarray, int]:
    """Same text handling as speak(), voiced by ElevenLabs v3 with emotion tags.
    One request per paragraph; blank lines become pauses of para_gap seconds."""
    import elevenlabs_tts as el
    direction = direction or {}
    out, sr = [], 44100
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    for pi, para in enumerate(paras):
        sentences = [x for x in re.split(r"(?<=[.!?])\s+", " ".join(para.split())) if x]
        emotions = [EMOTION_NAMES.get(id(direction[x])) if x in direction else None for x in sentences]
        audio, sr = el.decode(el.tts(el.tagged(sentences, emotions), preset["voice_id"],
                                     preset.get("stability", 0.0)))
        out.append(_trim(audio, sr))
        if pi < len(paras) - 1:
            out.append(np.zeros(int(sr * preset.get("para_gap", PARAGRAPH_GAP)), dtype=np.float32))
    return np.concatenate(out).astype(np.float32), sr


def _room(x: np.ndarray, sr: int, rt60: float = 1.1, wet: float = 0.16) -> np.ndarray:
    """A soft, dark hall: convolution with decaying filtered noise. Unlike a
    few discrete echoes, this has no metallic ring."""
    rng = np.random.default_rng(7)
    n = int(sr * rt60 * 1.2)
    t = np.arange(n) / sr
    ir = rng.standard_normal(n) * np.exp(-6.91 * t / rt60)
    ir = np.convolve(ir, np.ones(12) / 12, mode="same")    # darken the tail
    ir = np.concatenate([np.zeros(int(sr * 0.025)), ir])   # 25 ms pre-delay
    ir /= np.sqrt(np.sum(ir ** 2))
    size = len(x) + len(ir) - 1
    nfft = 1 << (size - 1).bit_length()
    tail = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:size]
    dry = np.concatenate([x, np.zeros(len(ir) - 1)])
    y = dry + wet * tail * (np.max(np.abs(x)) / (np.max(np.abs(tail)) + 1e-9))
    # Faint, dark room tone so pauses aren't digital dead air.
    tone = np.convolve(rng.standard_normal(len(y)), np.ones(40) / 40, mode="same")
    return y + tone * np.max(np.abs(x)) * 10 ** (-58 / 20) / (np.std(tone) + 1e-9)


def master(wav_in: Path, ogg_out: Path, preset: dict) -> None:
    filters = []
    if preset.get("semitones"):  # pitch shifting adds a robotic edge; avoid if possible
        filters.append(f"rubberband=pitch={2 ** (preset['semitones'] / 12):.4f}:formant=preserved")
    if preset.get("master") == "hush":
        with tempfile.TemporaryDirectory() as tmp:
            mastered = Path(tmp) / "m.wav"
            graph = ("[0:a]asplit=3[a][b][c];"
                     "[a]rubberband=pitch=0.5:formant=shifted,volume=0.9[lo];"
                     "[b]volume=0.35[mid];"
                     "[c]rubberband=pitch=1.5:formant=shifted,highpass=f=1500,volume=0.25[hi];"
                     "[lo][mid][hi]amix=inputs=3:normalize=0,aecho=0.6:0.7:400|900:0.25|0.15,"
                     "lowpass=f=6000,apad=pad_dur=2,loudnorm=I=-19:TP=-2,aresample=44100")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav_in), "-filter_complex", graph,
                            "-ac", "1", str(mastered)], check=True)
            _write_ogg(mastered, ogg_out)
        return
    if preset.get("master") == "trailer":
        # Movie-trailer narrator: close and dry, big chest, forward and clear,
        # tightly compressed so every word cuts through loud music.
        filters += [
            "highpass=f=75",
            "lowshelf=f=140:g=3.5",               # chest
            "equalizer=f=350:t=q:w=1.2:g=-2",     # less boxiness/mud
            "equalizer=f=3000:t=q:w=1.4:g=3",     # presence: intelligibility
            "highshelf=f=9000:g=2",               # air
            "deesser=i=0.4",
            "acompressor=threshold=-24dB:ratio=2.5:attack=8:release=160:makeup=2",  # keep acted dynamics
            "alimiter=limit=0.89:attack=2:release=50",
            "apad=pad_dur=0.6",
            f"loudnorm=I={preset.get('lufs', -15.0)}:TP=-1:LRA=7",
            "aresample=44100",
        ]
    else:
        filters += [
            "highpass=f=70",
            "lowshelf=f=200:g=2",                # warmth
            "equalizer=f=5500:t=q:w=2:g=-2.5",    # tame the synthetic fizz/sibilance
            "lowpass=f=12500",                    # remove vocoder hiss above the voice
            "acompressor=threshold=-22dB:ratio=2:attack=20:release=250",
            "apad=pad_dur=0.6",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "aresample=44100",
        ]
    if preset.get("fx"):
        filters.insert(0, preset["fx"])
    layers = preset.get("layers") or []
    graph = ",".join(filters)
    if layers:  # extra pitched copies under the dry voice, then the usual chain
        names = [f"l{i}" for i in range(len(layers))]
        graph = (f"[0:a]asplit={len(layers) + 1}[dry]{''.join(f'[{n}s]' for n in names)};"
                 + "".join(f"[{n}s]rubberband=pitch={ratio}:formant=shifted,volume={gain}[{n}];"
                           for n, (ratio, gain) in zip(names, layers))
                 + f"[dry]{''.join(f'[{n}]' for n in names)}amix=inputs={len(layers) + 1}:normalize=0,{graph}")
    with tempfile.TemporaryDirectory() as tmp:
        x, sr = sf.read(wav_in)
        roomy = Path(tmp) / "room.wav"
        sf.write(roomy, _room(x, sr, rt60=preset.get("rt60", 1.1), wet=preset.get("room", 0.16)),
                 sr, subtype="FLOAT")
        mastered = Path(tmp) / "m.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(roomy),
                        "-filter_complex" if layers else "-af", graph, "-ac", "1", str(mastered)], check=True)
        if preset.get("master") == "trailer":
            _level(mastered, preset.get("lufs", -15.0))
        _write_ogg(mastered, ogg_out)


def _loudness(wav: Path) -> float:
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    found = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
    return float(found[-1]) if found else float("nan")


def _level(wav: Path, target: float, ceiling: float = 0.89) -> None:
    """loudnorm misses on very short lines ("We remember."): correct the integrated
    loudness to target, then keep the peaks under the ceiling (about -1 dBFS)."""
    x, sr = sf.read(wav)
    off = target - _loudness(wav)
    if np.isfinite(off) and abs(off) > 0.5:
        x = x * 10 ** (off / 20)
    peak = np.max(np.abs(x)) if len(x) else 0.0
    if peak > ceiling:  # soft knee: squash only what pokes above the ceiling
        over = np.abs(x) > ceiling * 0.9
        knee = ceiling * 0.9
        x[over] = np.sign(x[over]) * (knee + (ceiling - knee) * np.tanh((np.abs(x[over]) - knee) / (ceiling - knee)))
    sf.write(wav, x, sr, subtype="FLOAT")


def _write_ogg(wav: Path, ogg_out: Path) -> None:
    data, sr = sf.read(wav)
    ogg_out.parent.mkdir(parents=True, exist_ok=True)
    # libsndfile's Vorbis encoder can crash on one huge write: feed it in blocks.
    with sf.SoundFile(ogg_out, "w", sr, 1, format="OGG", subtype="VORBIS") as f:
        for i in range(0, len(data), 8192):
            f.write(data[i:i + 8192].astype(np.float32))


def render(text: str, out: Path, preset: dict, direction: dict | None = None) -> float:
    if preset.get("engine") == "elevenlabs":
        samples, sr = speak_elevenlabs(text, preset, direction)
    else:
        samples, sr = speak(text, preset, direction)
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.wav"
        sf.write(raw, samples, sr)
        master(raw, out, preset)
    return sf.info(out).duration


def shots_of(doc) -> list[dict]:
    if isinstance(doc, list):
        return [s for s in doc if isinstance(s, dict)]
    for key in ("shots", "lines", "beats"):
        if isinstance(doc.get(key), list):
            return doc[key]
    return []


def narrate_cinematic(path: Path, preset_name: str, out_root: Path = VOICE_OUT,
                      speakers: set[str] | None = None) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    cid = doc.get("id", path.stem) if isinstance(doc, dict) else path.stem
    out_dir = out_root / cid
    direction = direction_for(cid)
    for n, shot in enumerate(shots_of(doc), start=1):
        text = (shot.get("text") or "").strip()
        if not text or shot.get("voice") is False:
            continue
        speaker = shot.get("speaker", "narrator")
        if speakers and speaker not in speakers:
            continue
        preset = PRESETS[shot["voice_preset"]] if "voice_preset" in shot else speaker_preset(speaker, preset_name)
        if preset is None:
            continue  # characters without a voice in cast.json stay as subtitles
        out = out_dir / f"{n:02d}.ogg"
        secs = render(text, out, preset, direction)
        print(f"{out}  {secs:5.1f}s")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cinematics", nargs="*", help="cinematic ids (default: all)")
    ap.add_argument("--preset", default="regal_el", choices=sorted(PRESETS))
    ap.add_argument("--text", help="speak this text instead of cinematics")
    ap.add_argument("--out", type=Path, help="output .ogg for --text, or output root for cinematics")
    ap.add_argument("--scripts", type=Path, default=CINEMATICS, help="folder of cinematic .json files")
    ap.add_argument("--speakers", help="comma-separated speaker ids to render (default: all); 'cast' = everyone but the narrator")
    args = ap.parse_args()
    speakers = None
    if args.speakers:
        speakers = set(cast()) if args.speakers == "cast" else set(args.speakers.split(","))

    if args.text:
        out = args.out or Path("narration.ogg")
        print(f"{out}  {render(args.text.replace('\\n', '\n'), out, PRESETS[args.preset]):.1f}s")
        return
    files = sorted(args.scripts.glob("*.json"))
    if args.cinematics:
        files = [args.scripts / f"{c}.json" for c in args.cinematics]
    if not files:
        sys.exit(f"No cinematics found in {args.scripts}")
    for f in files:
        narrate_cinematic(f, args.preset, args.out or VOICE_OUT, speakers)


if __name__ == "__main__":
    main()
