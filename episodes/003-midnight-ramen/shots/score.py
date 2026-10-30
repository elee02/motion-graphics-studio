#!/usr/bin/env python3
"""
Episode 003 score — procedural rain, warm pad, music box and two foley hits.
Deterministic (no randomness beyond a fixed seed); no samples on disk.

    .venv/bin/python episodes/003-midnight-ramen/shots/score.py --output score.wav --duration 13.3
"""

from __future__ import annotations

import argparse
import wave

import numpy as np
from scipy import signal

SR = 48000
RNG = np.random.default_rng(3)


def env_adsr(n: int, attack: float, release: float, sr: int = SR) -> np.ndarray:
    a = max(1, int(attack * sr))
    r = max(1, int(release * sr))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a) ** 2
    e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def bandpass(x: np.ndarray, lo: float, hi: float, order: int = 3) -> np.ndarray:
    sos = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band", output="sos")
    return signal.sosfilt(sos, x)


def lowpass(x: np.ndarray, cutoff: float, order: int = 3) -> np.ndarray:
    sos = signal.butter(order, cutoff / (SR / 2), btype="low", output="sos")
    return signal.sosfilt(sos, x)


def place(buf: np.ndarray, sig: np.ndarray, at_sec: float, gain: float = 1.0, pan: float = 0.0):
    start = int(at_sec * SR)
    end = min(buf.shape[1], start + len(sig))
    if end <= start:
        return
    chunk = sig[: end - start] * gain
    left = np.sqrt(0.5 * (1.0 - pan))
    right = np.sqrt(0.5 * (1.0 + pan))
    buf[0, start:end] += chunk * left * 1.414
    buf[1, start:end] += chunk * right * 1.414


def make_reverb_ir(seconds: float = 0.75) -> np.ndarray:
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = RNG.standard_normal(n) * np.exp(-t / 0.16)
    ir = lowpass(ir, 5200.0)
    ir[: int(0.012 * SR)] *= np.linspace(0.2, 1.0, int(0.012 * SR))
    ir /= np.sqrt(np.sum(ir**2)) + 1e-9
    return ir


def add_reverb(stereo: np.ndarray, wet: float = 0.22) -> np.ndarray:
    ir = make_reverb_ir()
    out = np.copy(stereo)
    for ch in range(2):
        conv = signal.fftconvolve(stereo[ch], ir, mode="full")[: stereo.shape[1]]
        out[ch] += conv * wet * 0.5
    return out


def rain_bed(duration: float) -> np.ndarray:
    n = int(duration * SR)
    out = np.zeros((2, n))
    for ch in range(2):
        white = RNG.standard_normal(n)
        body = bandpass(white, 380.0, 7200.0)
        hiss = bandpass(RNG.standard_normal(n), 1600.0, 5200.0)
        slow = lowpass(np.abs(RNG.standard_normal(n)), 0.7)
        slow = 0.75 + 0.25 * (slow / (np.max(slow) + 1e-9))
        out[ch] = body * 0.85 + hiss * 0.10
        out[ch] *= slow
        out[ch] *= env_adsr(n, 0.8, min(1.6, duration * 0.2))
    return out / (np.max(np.abs(out)) + 1e-9)


def city_rumble(duration: float) -> np.ndarray:
    n = int(duration * SR)
    brown = np.cumsum(RNG.standard_normal(n))
    brown = lowpass(brown, 110.0, order=2)
    brown /= np.max(np.abs(brown)) + 1e-9
    return np.vstack([brown, np.roll(brown, 137)])


def pad_chord(buf: np.ndarray, freqs, at: float, length: float, gain: float):
    n = int(length * SR)
    t = np.arange(n) / SR
    e = env_adsr(n, 0.95, 1.25)
    for i, f in enumerate(freqs):
        voice = np.zeros(n)
        for detune, amp in ((-0.18, 0.55), (0.0, 1.0), (0.16, 0.5)):
            phase = RNG.uniform(0, 2 * np.pi)
            voice += amp * np.sin(2 * np.pi * (f + detune) * t + phase)
        voice += 0.18 * np.sin(2 * np.pi * f * 2 * t)
        voice += 0.07 * np.sin(2 * np.pi * f * 3 * t)
        pan = (i / max(1, len(freqs) - 1)) * 1.2 - 0.6
        place(buf, voice * e, at, gain / len(freqs), pan=pan)


def music_box(buf: np.ndarray, freq: float, at: float, gain: float, pan: float = 0.0):
    length = 1.5
    n = int(length * SR)
    t = np.arange(n) / SR
    e = np.exp(-t * 3.4) * (1 - np.exp(-t * 220))
    tone = (
        np.sin(2 * np.pi * freq * t)
        + 0.35 * np.sin(2 * np.pi * freq * 2.01 * t)
        + 0.16 * np.sin(2 * np.pi * freq * 3.02 * t)
        + 0.06 * np.sin(2 * np.pi * freq * 4.10 * t)
    )
    place(buf, tone * e, at, gain, pan=pan)


def clink(buf: np.ndarray, at: float, base: float, gain: float, pan: float):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    e = np.exp(-t * 16)
    tone = np.sin(2 * np.pi * base * t) + 0.6 * np.sin(2 * np.pi * base * 1.47 * t)
    place(buf, tone * e, at, gain, pan=pan)
    click = RNG.standard_normal(int(0.004 * SR)) * np.exp(-np.arange(int(0.004 * SR)) / (0.0012 * SR))
    place(buf, click, at, gain * 0.8, pan=pan)


def build(duration: float) -> np.ndarray:
    n = int(duration * SR)
    music = np.zeros((2, n))
    foley = np.zeros((2, n))

    # --- pad: four warm chords, overlapping -----------------------------------
    chords = [
        [130.81, 164.81, 196.00, 246.94, 293.66],  # Cmaj9
        [110.00, 130.81, 164.81, 196.00, 246.94],  # Am9
        [87.31, 110.00, 130.81, 164.81, 196.00],   # Fmaj9
        [98.00, 123.47, 146.83, 164.81, 220.00],   # G6/9
    ]
    starts = [1.15, 3.35, 5.55, 7.75]
    for chord, at in zip(chords, starts):
        pad_chord(music, chord, at, 3.0, 0.30)
    pad_chord(music, chords[0], 9.75, 3.4, 0.22)  # resolve back home

    # --- music box melody ----------------------------------------------------
    for at, freq, pan in (
        (3.55, 659.25, 0.25),
        (5.75, 783.99, -0.2),
        (7.65, 987.77, 0.3),
        (9.90, 880.00, -0.15),
        (11.55, 659.25, 0.1),
    ):
        music_box(music, freq, at, 0.15, pan=pan)

    # --- foley ---------------------------------------------------------------
    hiss = bandpass(RNG.standard_normal(int(2.6 * SR)), 1800.0, 5600.0)
    hiss *= np.hanning(len(hiss)) ** 1.5
    place(foley, hiss, 3.1, 0.05, pan=-0.15)
    hiss2 = bandpass(RNG.standard_normal(int(1.4 * SR)), 2200.0, 6000.0)
    hiss2 *= np.hanning(len(hiss2)) ** 1.5
    place(foley, hiss2, 8.5, 0.035, pan=0.2)
    clink(foley, 7.02, 1860.0, 0.11, pan=0.35)
    clink(foley, 7.08, 2480.0, 0.05, pan=0.3)
    clink(foley, 9.36, 246.0, 0.10, pan=-0.3)

    wet = add_reverb(music + foley * 0.8, wet=0.26)

    rain = rain_bed(duration)
    rumble = city_rumble(duration)

    mix = np.zeros((2, n))
    mix += rain * 0.50
    mix += rumble * 0.12
    mix += wet * 0.95

    fade = int(0.9 * SR)
    mix[:, :fade] *= np.linspace(0, 1, fade) ** 1.5
    tail = int(1.6 * SR)
    mix[:, -tail:] *= np.linspace(1, 0, tail) ** 1.2

    peak = np.max(np.abs(mix)) + 1e-9
    mix *= 0.89 / peak
    return mix


def write_wav(path: str, stereo: np.ndarray):
    pcm = np.clip(stereo.T, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--duration", type=float, default=13.3)
    args = ap.parse_args()
    mix = build(args.duration)
    write_wav(args.output, mix)
    rms = 20 * np.log10(np.sqrt(np.mean(mix**2)) + 1e-9)
    print(f"[SCORE] {args.output}  {args.duration:.2f}s  rms={rms:.1f} dBFS  peak={20*np.log10(np.max(np.abs(mix))):.1f} dBFS")


if __name__ == "__main__":
    main()
