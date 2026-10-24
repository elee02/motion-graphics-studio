"""
Studio Manim Theme & Deterministic Mathematical Renderer.
Ensures consistent colors, safe 16:9 margins, and supports both Manim Community Edition
and a built-in deterministic Fourier/Vector preview renderer.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Tuple


class ManimPalette:
    BG_HEX = "#0B0F19"
    CYAN_HEX = "#00E5FF"
    AMBER_HEX = "#FFB000"
    VIOLET_HEX = "#9D4EDD"
    EMERALD_HEX = "#10B981"
    WHITE_HEX = "#F8FAFC"


@dataclass
class EpicycleTerm:
    freq: int
    amplitude: float
    phase: float
    color_rgb: Tuple[int, int, int]


@dataclass
class StudioMathScene:
    """Declarative mathematical explainer scene (Manim + built-in high-precision rasterizer)."""
    title: str = "Fourier Series Convergence"
    equation_label: str = "f(t) = (4/pi) * sum_{k=1,3,5...} (1/k) sin(k * omega * t)"
    fps: int = 60
    duration_sec: float = 5.0
    width: int = 1920
    height: int = 1080
    epicycles: List[EpicycleTerm] = field(default_factory=list)

    @property
    def total_frames(self) -> int:
        return max(1, int(round(self.fps * self.duration_sec)))

    def add_odd_harmonic_epicycles(self, count: int = 4) -> None:
        palette = [
            (0, 229, 255),    # Cyan (1st harmonic)
            (255, 176, 0),    # Amber (3rd harmonic)
            (157, 78, 221),   # Violet (5th harmonic)
            (16, 185, 129),   # Emerald (7th harmonic)
        ]
        for idx in range(count):
            k = 2 * idx + 1
            amp = (4.0 / math.pi) * (1.0 / k)
            self.epicycles.append(
                EpicycleTerm(
                    freq=k,
                    amplitude=amp,
                    phase=0.0,
                    color_rgb=palette[idx % len(palette)],
                )
            )

    def render_frame_png(self, frame: int, output_png: Path) -> None:
        """Renders a crisp 1080p mathematical epicycle + waveform diagram for frame N."""
        pw, ph = 1280, 720
        buf = bytearray(pw * ph * 3)

        # Deep obsidian background with subtle coordinate grid
        for y in range(ph):
            for x in range(pw):
                idx = (y * pw + x) * 3
                if x % 80 == 0 or y % 80 == 0:
                    buf[idx : idx + 3] = b"\x16\x1f\x33"
                else:
                    buf[idx : idx + 3] = b"\x0b\x0f\x19"

        def plot(px: int, py: int, rgb: Tuple[int, int, int], rad: int = 1) -> None:
            for dy in range(-rad, rad + 1):
                yy = py + dy
                if yy < 0 or yy >= ph:
                    continue
                for dx in range(-rad, rad + 1):
                    xx = px + dx
                    if xx < 0 or xx >= pw:
                        continue
                    if dx * dx + dy * dy <= rad * rad:
                        i = (yy * pw + xx) * 3
                        buf[i] = rgb[0]
                        buf[i + 1] = rgb[1]
                        buf[i + 2] = rgb[2]

        def line(x0: int, y0: int, x1: int, y1: int, rgb: Tuple[int, int, int], rad: int = 1) -> None:
            steps = max(abs(x1 - x0), abs(y1 - y0), 1)
            for s in range(steps + 1):
                t = s / steps
                plot(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), rgb, rad)

        def circle(cx: int, cy: int, r: int, rgb: Tuple[int, int, int]) -> None:
            steps = max(72, int(r * 4))
            for s in range(steps):
                ang = 2.0 * math.pi * (s / steps)
                plot(int(cx + r * math.cos(ang)), int(cy + r * math.sin(ang)), rgb, 1)

        # Epicycle center on the left, waveform trace on the right
        cx, cy = 320, 400
        scale = 135.0
        t_norm = (frame - 1) / max(1, self.total_frames - 1)
        omega_t = t_norm * 2.0 * math.pi * 1.5

        cur_x, cur_y = float(cx), float(cy)
        for term in self.epicycles:
            r_px = int(term.amplitude * scale)
            circle(int(cur_x), int(cur_y), r_px, (55, 80, 115))
            ang = term.freq * omega_t + term.phase
            nxt_x = cur_x + term.amplitude * scale * math.cos(ang)
            nxt_y = cur_y - term.amplitude * scale * math.sin(ang)
            line(int(cur_x), int(cur_y), int(nxt_x), int(nxt_y), term.color_rgb, 2)
            plot(int(nxt_x), int(nxt_y), (255, 255, 255), 3)
            cur_x, cur_y = nxt_x, nxt_y

        # Horizontal projection line from epicycle tip to waveform start
        wave_start_x = 580
        line(int(cur_x), int(cur_y), wave_start_x, int(cur_y), (255, 176, 0), 1)
        plot(wave_start_x, int(cur_y), (255, 176, 0), 4)

        # Draw synthesized square-wave approximation trace
        wave_width = 580
        prev_wx, prev_wy = None, None
        for wx_offset in range(wave_width):
            sample_t = omega_t - (wx_offset / wave_width) * (2.0 * math.pi * 1.5)
            val = 0.0
            for term in self.epicycles:
                val += term.amplitude * math.sin(term.freq * sample_t + term.phase)
            wx = wave_start_x + wx_offset
            wy = int(cy - val * scale)
            if prev_wx is not None and prev_wy is not None:
                line(prev_wx, prev_wy, wx, wy, (0, 229, 255), 2)
            prev_wx, prev_wy = wx, wy

        output_png.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".ppm", delete=False) as tmp:
            ppm_path = Path(tmp.name)
            tmp.write(f"P6\n{pw} {ph}\n255\n".encode("ascii"))
            tmp.write(buf)

        try:
            safe_title = self.title.replace(":", "\\:")
            safe_eq = self.equation_label.replace(":", "\\:")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(ppm_path),
                    "-vf",
                    (
                        f"scale={self.width}:{self.height}:flags=lanczos,"
                        f"drawbox=x=48:y=36:w=1280:h=105:color=0x0B0F19@0.78:t=fill,"
                        f"drawtext=text='{safe_title}':fontcolor=white:fontsize=38:x=68:y=52,"
                        f"drawtext=text='{safe_eq}':fontcolor=0xFFB000:fontsize=24:x=68:y=102"
                    ),
                    str(output_png),
                ],
                check=True,
            )
        finally:
            ppm_path.unlink(missing_ok=True)

    @classmethod
    def run_cli(cls, builder_fn: Callable[["StudioMathScene"], None]) -> None:
        parser = argparse.ArgumentParser(description="Studio Manim Mathematical Scene")
        parser.add_argument("--output", required=True, help="Output PNG or MP4 path")
        parser.add_argument("--frame", type=int, default=None, help="Single preview frame")
        parser.add_argument("--fps", type=int, default=60)
        parser.add_argument("--duration", type=float, default=5.0)
        parser.add_argument("--width", type=int, default=1920)
        parser.add_argument("--height", type=int, default=1080)
        parser.add_argument("--seed", type=int, default=42)
        args = parser.parse_args()

        scene = cls(fps=args.fps, duration_sec=args.duration, width=args.width, height=args.height)
        builder_fn(scene)
        out_path = Path(args.output).resolve()

        if out_path.suffix.lower() == ".png":
            target_frame = args.frame if args.frame is not None else max(1, scene.total_frames // 2)
            scene.render_frame_png(target_frame, out_path)
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                preview_fps = min(scene.fps, 24)
                num_f = max(1, int(scene.duration_sec * preview_fps))
                for f_idx in range(1, num_f + 1):
                    mapped_f = int(1 + (f_idx - 1) * (scene.total_frames - 1) / max(1, num_f - 1))
                    scene.render_frame_png(mapped_f, tmp_path / f"f_{f_idx:04d}.png")
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-loglevel",
                        "error",
                        "-framerate",
                        str(preview_fps),
                        "-i",
                        str(tmp_path / "f_%04d.png"),
                        "-r",
                        str(scene.fps),
                        "-c:v",
                        "libx264",
                        "-pix_fmt",
                        "yuv420p",
                        str(out_path),
                    ],
                    check=True,
                )
