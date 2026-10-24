"""
Procedural Cinematic Trailer Score Synthesizer (`synth_trailer_audio.py`).
Generates a 48kHz stereo WAV soundtrack synchronized to the 4 acts of the novel trailer:
1. Nocturnal Celesta / Bell minor waltz arpeggio in E minor (magical music-box timbre).
2. Deep Cinematic Trailer "BRAAAM" sub-bass & brass impacts on every act transition (0s, 4s, 8s, 12s).
3. Shimmering harmonic spell riser culminating in the Act IV Philosopher's Stone chord.
"""

from __future__ import annotations

import argparse
import wave
from pathlib import Path

import numpy as np


def midi_to_freq(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def synthesize_trailer_score(output_wav: Path, duration_sec: float = 16.0, sr: int = 48000) -> None:
    total_samples = int(sr * duration_sec)
    t = np.linspace(0.0, duration_sec, total_samples, endpoint=False)

    left = np.zeros(total_samples, dtype=np.float64)
    right = np.zeros(total_samples, dtype=np.float64)

    # --- 1. Enchanted Celesta / Bell Minor Motif (E minor / harmonic minor) ---
    # Classic nocturnal wizarding interval sequence (B4, E5, G5, F#5, E5, B5, A5, F#5...)
    motif_notes = [
        (0.25, 71, 0.75),  # B4
        (1.00, 76, 1.10),  # E5
        (2.10, 79, 0.45),  # G5
        (2.55, 78, 0.55),  # F#5
        (3.10, 76, 0.90),  # E5
        (4.25, 83, 0.70),  # B5 (Act II start)
        (4.95, 81, 1.35),  # A5
        (6.30, 78, 1.40),  # F#5
        (8.25, 76, 0.90),  # E5 (Act III start)
        (9.15, 79, 0.45),  # G5
        (9.60, 78, 0.55),  # F#5
        (10.15, 75, 1.10), # D#5 (mysterious chromatic tension)
        (11.25, 77, 0.75), # F5
        (12.25, 71, 1.20), # B4 (Act IV start)
        (13.45, 76, 2.30), # E5 (Final resonant hold)
    ]

    for start_t, midi_n, note_dur in motif_notes:
        if start_t >= duration_sec:
            continue
        f0 = midi_to_freq(midi_n)
        idx0 = int(start_t * sr)
        idx1 = min(total_samples, idx0 + int((note_dur + 1.2) * sr))
        nt = t[idx0:idx1] - start_t

        # Celesta bell timbre: fundamental + 2nd + 3rd + inharmonic 4.2x chime overtone
        env = np.exp(-nt * 2.4) * (1.0 - np.exp(-nt * 85.0))
        bell = (
            0.60 * np.sin(2.0 * np.pi * f0 * nt)
            + 0.25 * np.sin(2.0 * np.pi * (2.0 * f0) * nt) * np.exp(-nt * 4.0)
            + 0.12 * np.sin(2.0 * np.pi * (3.0 * f0) * nt) * np.exp(-nt * 6.0)
            + 0.08 * np.sin(2.0 * np.pi * (4.18 * f0) * nt) * np.exp(-nt * 11.0)
        ) * env

        pan = 0.5 + 0.28 * np.sin(start_t * 1.7)
        left[idx0:idx1] += bell * pan * 0.34
        right[idx0:idx1] += bell * (1.0 - pan) * 0.34

        # Stereo echo delay (280ms) for cavernous Great Hall reverb feel
        delay_samples = int(0.28 * sr)
        if idx0 + delay_samples < total_samples:
            d_end = min(total_samples, idx1 + delay_samples)
            seg_len = d_end - (idx0 + delay_samples)
            left[idx0 + delay_samples : d_end] += bell[:seg_len] * 0.14
            right[idx0 + delay_samples : d_end] += bell[:seg_len] * 0.18

    # --- 2. Deep Trailer "BRAAAM" Sub-Bass & Brass Hits at Each Act (0s, 4s, 8s, 12s) ---
    act_hits = [
        (0.0, 40),   # E1 (Act I)
        (4.0, 36),   # C1 (Act II)
        (8.0, 33),   # A0 (Act III)
        (12.0, 40),  # E1 + E2 (Act IV Climax)
    ]
    for hit_t, bass_midi in act_hits:
        if hit_t >= duration_sec:
            continue
        f_bass = midi_to_freq(bass_midi)
        idx0 = int(hit_t * sr)
        idx1 = min(total_samples, idx0 + int(3.6 * sr))
        bt = t[idx0:idx1] - hit_t

        env_hit = np.exp(-bt * 0.95) * (1.0 - np.exp(-bt * 35.0))
        # Rich saw-like brass harmonics + sub-bass sine
        braaam = (
            0.55 * np.sin(2.0 * np.pi * f_bass * bt)
            + 0.30 * np.sin(2.0 * np.pi * (2.0 * f_bass) * bt + 0.3 * np.sin(2.0 * np.pi * f_bass * bt))
            + 0.18 * np.sin(2.0 * np.pi * (3.0 * f_bass) * bt)
            + 0.10 * np.sin(2.0 * np.pi * (4.0 * f_bass) * bt)
        ) * env_hit * 0.48

        left[idx0:idx1] += braaam
        right[idx0:idx1] += braaam

    # --- 3. Shimmering Magical Riser & Pad Across Entire Trailer ---
    pad_freqs = [midi_to_freq(52), midi_to_freq(55), midi_to_freq(59), midi_to_freq(64)]  # E3 minor chord
    riser_env = np.clip(t / duration_sec, 0.15, 1.0) * np.exp(-np.maximum(0.0, t - (duration_sec - 1.2)) * 2.5)
    for pf in pad_freqs:
        shimmer = 0.06 * np.sin(2.0 * np.pi * pf * t + 0.25 * np.sin(2.0 * np.pi * 0.4 * t)) * riser_env
        left += shimmer
        right += shimmer

    # Master soft-limiter & fade-out
    fade_out = np.ones(total_samples)
    fade_len = int(0.8 * sr)
    if fade_len < total_samples:
        fade_out[-fade_len:] = np.linspace(1.0, 0.0, fade_len)

    stereo = np.stack([left * fade_out, right * fade_out], axis=-1)
    peak = np.max(np.abs(stereo)) or 1.0
    stereo = np.tanh(stereo / peak * 1.35) * 0.88
    pcm16 = (stereo * 32767.0).astype(np.int16)

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16.tobytes())


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthesize Harry Potter Novel Trailer Score")
    parser.add_argument("--output", required=True, help="Output WAV path")
    parser.add_argument("--duration", type=float, default=16.0)
    args = parser.parse_args()
    synthesize_trailer_score(Path(args.output).resolve(), duration_sec=args.duration)


if __name__ == "__main__":
    main()
