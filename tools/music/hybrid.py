"""Hybrid film-score sounds that sit under and around the sampled orchestra.

Synth instruments (used as track instruments, so they are written in the score like any part):
  syn_pulse  a tight, filtered saw pluck for 8th/16th-note ostinatos
  syn_pad    a wide, detuned saw pad with a slow attack
  syn_sub    a sine sub bass
  syn_bass   a driven, detuned low saw that "blats" on the attack (doubles low brass)

Drum ensembles (used as percussion kinds in Section.hits):
  taiko      several big drums at once: bass drum + log drum + tumba samples and a synth boom
  epic       taiko plus a long low boom and a stick crack, for downbeats
  toms       a higher drum ensemble for fills
  snare      a tight snare stack for rhythm
  tick       a clock tick

All synthesis is our own code; drum samples are VSCO 2 CE (CC0).
"""
from __future__ import annotations

import functools

import numpy as np
from scipy import signal

import orchestra as orc
from orchestra import SR

SYNTHS = {"syn_pulse", "syn_pad", "syn_sub", "syn_bass"}
DRUMS = {"taiko", "epic", "toms", "snare", "tick"}


def _hz(p: float) -> float:
    return 440.0 * 2 ** ((p - 69) / 12)


@functools.lru_cache(maxsize=None)
def _sos(kind: str, fc: float, order: int = 2):
    return signal.butter(order, min(0.99, fc / (SR / 2)), kind, output="sos")


def _saws(f: float, n: int, detune_cents: float, length: int, rng) -> np.ndarray:
    t = np.arange(length) / SR
    out = np.zeros((length, 2), np.float32)
    for k in range(n):
        c = (k - (n - 1) / 2) / max(1, (n - 1) / 2) * detune_cents
        ph = rng.uniform(0, 2 * np.pi)
        w = signal.sawtooth(2 * np.pi * f * 2 ** (c / 1200) * t + ph).astype(np.float32)
        pan = (k / max(1, n - 1)) * 2 - 1 if n > 1 else 0.0
        out[:, 0] += w * np.cos((pan * 0.8 + 1) * np.pi / 4)
        out[:, 1] += w * np.sin((pan * 0.8 + 1) * np.pi / 4)
    return out / n


def _env(length: int, attack: float, dur: float, release: float) -> np.ndarray:
    t = np.arange(length) / SR
    a = np.minimum(1.0, t / max(attack, 1e-3))
    r = np.clip(1 - (t - dur) / max(release, 1e-3), 0, 1)
    return (a * r).astype(np.float32)


def synth_note(kind: str, pitch: float, vel: int, dur: float, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    f = _hz(pitch)
    v = vel / 127
    if kind == "syn_pulse":
        rel = 0.06
        n = int((dur + rel) * SR)
        x = _saws(f, 3, 9, n, rng)
        t = np.arange(n) / SR
        e = np.exp(-t / 0.07)[:, None]
        dark = signal.sosfilt(_sos("low", 260 + f), x, axis=0)
        bright = signal.sosfilt(_sos("low", 900 + 3500 * v), x, axis=0)
        y = dark * (1 - e) + bright * e
        amp = (0.35 + 0.65 * np.exp(-t / 0.18)) * _env(n, 0.003, dur, rel)
        return (y * amp[:, None] * (0.4 + 0.6 * v)).astype(np.float32)
    if kind == "syn_pad":
        rel = 1.6
        n = int((dur + rel) * SR)
        x = _saws(f, 7, 18, n, rng) + 0.5 * _saws(f / 2, 3, 10, n, rng)
        y = signal.sosfilt(_sos("low", 1100 + 900 * v, 4), x, axis=0)
        y = signal.sosfilt(_sos("high", 60), y, axis=0)
        t = np.arange(n) / SR
        lfo = 1 + 0.08 * np.sin(2 * np.pi * 0.23 * t + rng.uniform(0, 6))
        amp = _env(n, min(1.2, dur * 0.4), dur, rel) * lfo
        return (y * amp[:, None] * (0.3 + 0.7 * v) * 1.6).astype(np.float32)
    if kind == "syn_sub":
        rel = 0.35
        n = int((dur + rel) * SR)
        t = np.arange(n) / SR
        y = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t)
        y = np.tanh(1.3 * y) * _env(n, 0.02, dur, rel) * (0.4 + 0.6 * v)
        return np.stack([y, y], axis=1).astype(np.float32)
    if kind == "syn_bass":
        rel = 0.5
        n = int((dur + rel) * SR)
        t = np.arange(n) / SR
        x = _saws(f, 4, 14, n, rng)
        x = np.tanh(x * 2.6)
        e = np.exp(-t / 0.35)[:, None]
        dark = signal.sosfilt(_sos("low", 380), x, axis=0)
        bright = signal.sosfilt(_sos("low", 2200 * (0.5 + v)), x, axis=0)
        y = dark * (1 - e) + bright * e
        sub = np.sin(2 * np.pi * f / 2 * t)[:, None] * 0.6
        amp = _env(n, 0.03, dur, rel)
        return ((y + sub) * amp[:, None] * (0.4 + 0.6 * v)).astype(np.float32)
    raise KeyError(kind)


# ------------------------------------------------------------------ drum ensembles

def _place(buf: np.ndarray, y: np.ndarray, at: int, gain: float, pan: float):
    y = y.mean(1) if y.ndim == 2 else y
    g = np.array([np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)]) * np.sqrt(2) * gain
    e = min(len(buf), at + len(y))
    buf[at:e] += y[: e - at, None] * g


def _boom(f0: float, f1: float, decay: float, n: int) -> np.ndarray:
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.045)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / decay) * np.minimum(1, t / 0.002)
    return np.tanh(1.6 * y).astype(np.float32)


def drum(kind: str, vel: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed * 31 + 7)
    v = vel / 127
    n = int(3.0 * SR)
    buf = np.zeros((n, 2), np.float32)
    if kind in ("taiko", "epic"):
        # three or four players, a few ms apart, across the stage
        players = 4 if kind == "epic" else 3
        for p in range(players):
            at = int(rng.uniform(0, 0.014) * SR)
            pan = (p / (players - 1)) * 1.4 - 0.7
            _place(buf, orc.render_perc("bd", vel, seed=seed + p), at, 0.8, pan)
            _place(buf, orc.render_perc("logdrum", vel, seed=seed + p), at, 0.45, -pan)
            _place(buf, orc.render_perc("tumba", vel, seed=seed + p), at + 40, 0.35, pan * 0.5)
        boom = _boom(120, 48 if kind == "taiko" else 36, 0.35 if kind == "taiko" else 0.9, n)
        _place(buf, boom, 0, 0.9 if kind == "taiko" else 1.3, 0.0)
        if kind == "epic":
            crack = rng.standard_normal(n).astype(np.float32) * np.exp(-np.arange(n) / SR / 0.03)
            crack = signal.sosfilt(_sos("high", 1200), crack)
            _place(buf, crack, 0, 0.25, 0.0)
    elif kind == "toms":
        for p in range(3):
            at = int(rng.uniform(0, 0.012) * SR)
            pan = p * 0.6 - 0.6
            _place(buf, orc.render_perc("tumba", vel, seed=seed + p), at, 0.7, pan)
            _place(buf, orc.render_perc("tenor", vel, seed=seed + p), at, 0.5, -pan)
        _place(buf, _boom(220, 110, 0.18, n), 0, 0.5, 0.0)
    elif kind == "snare":
        for p in range(2):
            at = int(rng.uniform(0, 0.006) * SR)
            _place(buf, orc.render_perc("snare", vel, seed=seed + p), at, 0.7, p * 0.6 - 0.3)
    elif kind == "tick":
        t = np.arange(int(0.08 * SR)) / SR
        y = rng.standard_normal(len(t)) * np.exp(-t / 0.004)
        y = signal.sosfilt(_sos("high", 3000), y)
        _place(buf, y.astype(np.float32), 0, 0.6, rng.uniform(-0.2, 0.2))
    else:
        raise KeyError(kind)
    buf *= 0.35 + 0.65 * v
    idx = np.nonzero(np.abs(buf).max(1) > 1e-4)[0]
    return buf[: idx[-1] + 1] if len(idx) else buf[:1]
