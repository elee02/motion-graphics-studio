"""
Shot 03 (Manim Mathematical Explainer): Odd-Harmonic Epicycle Square Wave Synthesis.
Visualizes how rotating phasors of frequencies 1w, 3w, 5w, 7w sum to a square wave.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.manim_lib.studio_theme import StudioMathScene


def build_epicycle_shot(scene: StudioMathScene) -> None:
    scene.title = "3. Formal Mechanics: Fourier Epicycle Convergence"
    scene.equation_label = "DEEP-DIVE MATH  |  f(t) = (4/pi) [ sin(wt) + (1/3)sin(3wt) + (1/5)sin(5wt) + (1/7)sin(7wt) ]"
    scene.add_odd_harmonic_epicycles(count=4)


if __name__ == "__main__":
    StudioMathScene.run_cli(build_epicycle_shot)
