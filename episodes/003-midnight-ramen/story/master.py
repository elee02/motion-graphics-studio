#!/usr/bin/env python3
"""Assemble the episode 003 master: cards + shot + score -> dist/midnight_ramen.mp4"""

from __future__ import annotations

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # episodes/003-midnight-ramen
FRAMES = os.path.join(ROOT, "renders", "frames")
CARDS = os.path.join(ROOT, "renders", "cards")
SCORE = os.path.join(ROOT, "renders", "score.wav")
DIST = os.path.join(ROOT, "dist")
BUILD = os.path.join(ROOT, "renders", "build")

TITLE_IN, TITLE_LEN = 1.4, 2.1
SCENE_LEN = 10.0
XFADE = 0.7
END_LEN = 2.6
TOTAL = TITLE_LEN + SCENE_LEN + END_LEN - 2 * XFADE


def run(cmd):
    print("$", " ".join(cmd[:6]), "..." if len(cmd) > 6 else "")
    subprocess.run(cmd, check=True)


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate,codec_name",
         "-of", "json", path],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


def main():
    missing = [f for f in range(1, 241) if not os.path.exists(os.path.join(FRAMES, f"frame_{f:04d}.png"))]
    if missing:
        sys.exit(f"missing {len(missing)} frames (first: {missing[:3]}) - render still running?")
    os.makedirs(DIST, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)

    scene = os.path.join(BUILD, "scene.mp4")
    title = os.path.join(BUILD, "title.mp4")
    end = os.path.join(BUILD, "end.mp4")
    master = os.path.join(DIST, "midnight_ramen.mp4")

    run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(FRAMES, "frame_%04d.png"),
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", scene])
    for png, out, dur in ((os.path.join(CARDS, "title.png"), title, TITLE_LEN),
                          (os.path.join(CARDS, "end.png"), end, END_LEN)):
        run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", f"{dur:.3f}", "-framerate", "24", "-i", png,
             "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", out])

    graph = (
        f"[0:v][1:v]xfade=transition=fadeblack:duration={XFADE}:offset={TITLE_IN}[v1];"
        f"[v1][2:v]xfade=transition=fadeblack:duration={XFADE}:offset={TITLE_LEN + SCENE_LEN - 2 * XFADE:.3f}[v2];"
        f"[v2]fade=t=in:st=0:d=0.55,fade=t=out:st={TOTAL - 0.9:.3f}:d=0.9[v3];"
        f"[3:a]loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.7,afade=t=out:st={TOTAL - 1.0:.3f}:d=1.0[a]"
    )
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", title, "-i", scene, "-i", end, "-i", SCORE,
         "-filter_complex", graph, "-map", "[v3]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", master])

    thumb = os.path.join(DIST, "thumbnail.png")
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "6.4", "-i", master, "-frames:v", "1", thumb])

    info = probe(master)
    dur = float(info["format"]["duration"])
    stream = info["streams"][0]
    print(f"[MASTER] {master}")
    print(f"[MASTER] {stream['width']}x{stream['height']} {stream['r_frame_rate']}fps {dur:.2f}s "
          f"video={info['streams'][0]['codec_name']} audio={info['streams'][1]['codec_name']}")


if __name__ == "__main__":
    main()
