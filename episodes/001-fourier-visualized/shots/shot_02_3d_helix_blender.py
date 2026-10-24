"""
Shot 02 (Headless Blender / bpy): 3D Complex Euler Helix & Orthogonal Wave Projections.
Constructs a 3D complex exponential spiral exp(i * omega * t) in cyan, alongside its
real (cosine) projection on the floor plane and imaginary (sine) projection on the back wall.
Zero binary .blend files required!
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.blender_rig.scene_builder import StudioPalette, StudioScene


def build_euler_helix_shot(scene: StudioScene) -> None:
    scene.title = "2. 3D Intuition: Complex Euler Helix exp(i*omega*t)"
    scene.subtitle = "DEEP-DIVE 3D  |  Headless Blender Procedural Rig"

    scene.setup_three_point_lighting(energy_scale=1.25)
    scene.create_orbit_camera(
        radius=10.8,
        elevation_deg=28.0,
        start_angle_deg=22.0,
        end_angle_deg=58.0,
    )

    freq = 2.2
    radius = 1.05

    # 1. Primary 3D Complex Helix: (t, r*cos(w*t), r*sin(w*t))
    scene.add_parametric_curve(
        name="ComplexEulerHelix",
        func=lambda t: (t, radius * math.cos(freq * t), radius * math.sin(freq * t)),
        t_min=-3.2,
        t_max=3.2,
        steps=360,
        color=StudioPalette.CYAN,
        bevel_radius=0.055,
        emission_strength=4.0,
    )

    # 2. Orthogonal Floor Shadow: Real Projection cos(w*t) at z = -1.45
    scene.add_parametric_curve(
        name="RealCosineProjection",
        func=lambda t: (t, radius * math.cos(freq * t), -1.45),
        t_min=-3.2,
        t_max=3.2,
        steps=300,
        color=StudioPalette.AMBER,
        bevel_radius=0.035,
        emission_strength=2.8,
    )

    # 3. Orthogonal Wall Shadow: Imaginary Projection sin(w*t) at y = 2.2
    scene.add_parametric_curve(
        name="ImaginarySineProjection",
        func=lambda t: (t, 2.2, radius * math.sin(freq * t)),
        t_min=-3.2,
        t_max=3.2,
        steps=300,
        color=StudioPalette.VIOLET,
        bevel_radius=0.035,
        emission_strength=2.8,
    )


if __name__ == "__main__":
    StudioScene.run_cli(build_euler_helix_shot)
