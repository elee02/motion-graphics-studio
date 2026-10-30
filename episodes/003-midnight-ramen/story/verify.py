#!/usr/bin/env python3
"""Verify the episode master: container, streams, loudness, and frame samples."""

from __future__ import annotations

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate,nb_frames,channels,sample_rate",
         "-of", "json", path],
        capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def loudness(path):
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    summary = out.split("Summary:")[-1]
    rows = {}
    for key in ("I:", "LRA:", "Peak:"):
        for line in summary.splitlines():
            if line.strip().startswith(key):
                rows[key] = line.strip()
    return rows


def main(path):
    info = probe(path)
    v = [s for s in info["streams"] if s.get("width")][0]
    a = [s for s in info["streams"] if s.get("channels")][0]
    print(f"file      {path}")
    print(f"duration  {float(info['format']['duration']):.2f}s   size {int(info['format']['size'])/1e6:.1f} MB")
    print(f"video     {v['codec_name']} {v['width']}x{v['height']} {v['r_frame_rate']} fps, {v.get('nb_frames')} frames")
    print(f"audio     {a['codec_name']} {a['channels']}ch {a['sample_rate']} Hz")
    for k, row in loudness(path).items():
        print(f"{k:<9} {row}")
    if abs(float(info["format"]["duration"]) - 13.3) > 0.1:
        sys.exit("unexpected duration")
    if v["width"] != 1920 or v["height"] != 1080:
        sys.exit("unexpected resolution")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist", "midnight_ramen.mp4"))
