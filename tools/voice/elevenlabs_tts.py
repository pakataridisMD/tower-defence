"""ElevenLabs v3 engine for narrate.py (--engine elevenlabs).

v3 acts from inline audio tags such as [shouting], [crying] or [gasps], so each
sentence's emotion from direction.json becomes a tag in front of it. One request
per paragraph keeps the delivery connected; narrate.py adds the pauses between
paragraphs and does the mastering.

Auth: the cloud environment injects the key for api.elevenlabs.io as a network
secret (header xi-api-key). Locally, set ELEVENLABS_API_KEY instead.

Every response is cached in tools/voice/cache/ (git-ignored) by a hash of the text,
voice and settings, so re-mastering or re-mixing never spends credits twice.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

API = "https://api.elevenlabs.io/v1"
CACHE = Path(__file__).resolve().parent / "cache"

# direction.json emotion -> v3 audio tag(s) placed before the sentence.
TAGS = {
    "calm": "",
    "awe": "[in awe, softly]",
    "dread": "[ominous, low voice]",
    "shock": "[gasps] [shocked]",
    "anger": "[angry]",
    "passion": "[passionately]",
    "pride": "[proudly]",
    "grief": "[sad, voice breaking]",
    "command": "[shouting]",
    "tender": "[softly, tenderly]",
    "bitter": "[bitterly]",
    "hope": "[hopeful]",
    "triumph": "[triumphant]",
    "whisper": "[whispers]",
    "desperate": "[desperate, voice cracking]",
    "wry": "[dry, wry]",
    # Character voices (cast.json).
    "menace": "[menacing, quietly]",
    "weary": "[tired, slowly]",
    "warm": "[warmly]",
    "cold": "[coldly]",
    "hollow": "[distant, empty]",
    "gruff": "[gruffly]",
    "fierce": "[fiercely]",
}


def _headers() -> dict:
    h = {"Content-Type": "application/json", "Accept": "audio/mpeg"}
    if os.environ.get("ELEVENLABS_API_KEY"):
        h["xi-api-key"] = os.environ["ELEVENLABS_API_KEY"]
    return h


def api_get(path: str) -> dict:
    req = urllib.request.Request(API + path, headers={**_headers(), "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def tts(text: str, voice_id: str, stability: float = 0.0, model: str = "eleven_v3") -> bytes:
    """MP3 bytes for text, cached on disk."""
    body = {"text": text, "model_id": model, "voice_settings": {"stability": stability}}
    key = hashlib.sha256(json.dumps([voice_id, body], sort_keys=True).encode()).hexdigest()[:24]
    cached = CACHE / f"{key}.mp3"
    if cached.exists():
        return cached.read_bytes()
    req = urllib.request.Request(f"{API}/text-to-speech/{voice_id}?output_format=mp3_44100_128",
                                 data=json.dumps(body).encode(), headers=_headers(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            audio = r.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ElevenLabs {e.code}: {e.read()[:400]!r}")
    CACHE.mkdir(exist_ok=True)
    cached.write_bytes(audio)
    return audio


def decode(mp3: bytes) -> tuple[np.ndarray, int]:
    with tempfile.TemporaryDirectory() as tmp:
        src, wav = Path(tmp) / "a.mp3", Path(tmp) / "a.wav"
        src.write_bytes(mp3)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-ac", "1", str(wav)], check=True)
        x, sr = sf.read(wav, dtype="float32")
    return x, sr


def tagged(sentences: list[str], emotions: list[str | None]) -> str:
    parts = []
    for s, e in zip(sentences, emotions):
        tag = TAGS.get(e or "calm", "")
        if e in ("command", "triumph", "desperate", "fierce") and s.endswith("."):
            s = s[:-1] + "!"
        parts.append(f"{tag} {s}".strip())
    return " ".join(parts)


def api_post_json(path: str, body: dict) -> dict:
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(),
                                 headers={**_headers(), "Accept": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ElevenLabs {e.code}: {e.read()[:300]!r}")
