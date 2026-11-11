"""The list of every sound effect: its recipe, how many variations to render and how the game plays it."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass
class Spec:
    name: str
    group: str
    recipe: Callable[[np.random.Generator, int], np.ndarray]
    variants: int = 1
    # Loudness target for rendering (momentary max, LUFS-like). The game can trim further with volume_db.
    loud: float = -20.0
    bus: str = "Sfx"
    volume_db: float = 0.0
    # Played at a board position (panned) or straight to the speakers.
    positional: bool = True
    # How many copies may sound at once, and the shortest time between two starts (seconds).
    max_voices: int = 4
    min_gap: float = 0.0
    pitch_jitter: float = 0.0
    # Higher wins when every player is busy.
    priority: int = 1
    # Ducks the music bus by this many dB for duck_time seconds when played.
    duck_db: float = 0.0
    duck_time: float = 0.0
    description: str = ""
    tags: list[str] = field(default_factory=list)


SOUNDS: dict[str, Spec] = {}


def sound(name: str, group: str, **kwargs):
    def deco(fn):
        register(name, group, fn, **kwargs)
        return fn
    return deco


def register(name: str, group: str, recipe, **kwargs) -> Spec:
    if name in SOUNDS:
        raise ValueError(f"duplicate sound {name}")
    spec = Spec(name=name, group=group, recipe=recipe, **kwargs)
    SOUNDS[name] = spec
    return spec
