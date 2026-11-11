#!/usr/bin/env python3
"""Audition ElevenLabs voices for the narrator (Queen Ysolde).

Finds deep, mature female narrator voices (your own library plus the public
Voice Library), has each perform the same acted test lines with v3 emotion
tags, and writes one MP3 per voice to OUT_DIR plus voices.json.

    python3 tools/voice/audition_elevenlabs.py OUT_DIR [--max 6]

Then set NARRATOR_VOICE_ID (or the regal_el preset's voice_id) to the winner.
"""
import argparse
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import elevenlabs_tts as el  # noqa: E402

TEST = ("[ominous, low voice] His name was Vael-Orrun. Where he walked, the elements did not mix. "
        "[gasps] [shocked] They stopped. "
        "[sad, voice breaking] And Oswin fell. His lantern went out. "
        "[shouting] Hold the road!")

ap = argparse.ArgumentParser()
ap.add_argument("out", type=Path)
ap.add_argument("--max", type=int, default=6)
args = ap.parse_args()
args.out.mkdir(parents=True, exist_ok=True)

candidates = []
for v in el.api_get("/voices").get("voices", []):
    labels = v.get("labels") or {}
    if labels.get("gender") == "female":
        brit = labels.get("accent") == "british"
        candidates.append({"voice_id": v["voice_id"], "name": v["name"], "source": "my voices",
                           "labels": labels, "score": 2 if brit else -1})
query = urllib.parse.urlencode({"gender": "female", "age": "middle_aged", "use_cases": "narrative_story",
                                "language": "en", "page_size": 30, "sort": "trending"})
shared = el.api_get(f"/shared-voices?{query}").get("voices", [])
for v in shared:
    desc = (v.get("description") or "").lower() + " " + (v.get("name") or "").lower()
    score = sum(w in desc for w in ("deep", "british", "regal", "queen", "epic", "narrat", "warm", "mature", "cinematic"))
    candidates.append({"voice_id": v["voice_id"], "name": v["name"], "source": "voice library",
                       "public_owner_id": v.get("public_owner_id"), "score": score,
                       "accent": v.get("accent"), "description": v.get("description")})
candidates.sort(key=lambda c: -c.get("score", 0))
picked = candidates[:args.max]
for c in picked:
    if c["source"] == "voice library":  # a library voice must be added before use
        try:
            el.api_post_json(f"/voices/add/{c['public_owner_id']}/{c['voice_id']}", {"new_name": c["name"]})
        except SystemExit as e:
            print("skip", c["name"], e)
            continue
    mp3 = el.tts(TEST, c["voice_id"])
    slug = "".join(ch if ch.isalnum() else "_" for ch in c["name"])[:40]
    (args.out / f"{slug}.mp3").write_bytes(mp3)
    c["file"] = f"{slug}.mp3"
    print(c["name"], "->", c["file"])
(args.out / "voices.json").write_text(json.dumps(picked, indent=1))
