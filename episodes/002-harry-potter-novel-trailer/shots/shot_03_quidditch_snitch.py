"""
Act III (Novel Ch. 11 - Quidditch):
Three towering Golden Goal Hoops, a central winged Golden Snitch with silver filigree wings,
and high-velocity Crimson (Gryffindor) & Emerald (Slytherin) broomstick slipstreams.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.blender_rig.scene_builder import StudioPalette, StudioScene


def build_shot(scene: StudioScene) -> None:
    scene.title = "ACT III - AERIAL KINEMATICS OF QUIDDITCH"
    scene.subtitle = "Novel Ch. 11  |  Three Golden Goal Hoops & The Winged Golden Snitch"
    scene.setup_three_point_lighting(
        energy_scale=1.4,
        key_color=StudioPalette.GOLD,
        fill_color=StudioPalette.CRIMSON,
        rim_color=StudioPalette.EMERALD,
    )
    scene.create_orbit_camera(
        radius=11.0,
        elevation_deg=24.0,
        start_angle_deg=15.0,
        end_angle_deg=55.0,
        target=(0.0, 0.0, 0.5),
    )

    # 1. Three Towering Golden Quidditch Goal Hoops + Masts
    hoop_configs = [
        ("LeftHoop", (-2.3, 0.8, 0.9), 1.8),
        ("CenterHoop", (0.0, 1.2, 1.45), 2.35),
        ("RightHoop", (2.3, 0.8, 0.9), 1.8),
    ]
    for h_name, (hx, hy, hz), mast_h in hoop_configs:
        scene.add_torus(
            name=h_name,
            location=(hx, hy, hz),
            major_radius=0.72,
            minor_radius=0.055,
            rotation_euler=(math.radians(90.0), 0.0, 0.0),
            color=StudioPalette.GOLD,
            emission_strength=3.5,
        )
        scene.add_cylinder(
            name=f"{h_name}_Mast",
            location=(hx, hy, hz - 0.72 - mast_h * 0.5),
            radius=0.04,
            depth=mast_h,
            color=StudioPalette.GOLD,
            emission_strength=2.0,
        )

    # 2. Central Golden Snitch Sphere + Swept Silver Filigree Wings
    scene.add_sphere(
        name="GoldenSnitchCore",
        location=(0.0, -0.8, 0.65),
        radius=0.28,
        color=StudioPalette.GOLD,
        emission_strength=6.5,
    )
    for wing_sign, wing_name in [(-1.0, "SnitchWingLeft"), (1.0, "SnitchWingRight")]:
        scene.add_parametric_curve(
            name=wing_name,
            func=lambda t, s=wing_sign: (
                s * (0.28 + 1.45 * t),
                -0.8 - 0.35 * math.sin(t * math.pi),
                0.65 + 0.65 * math.sin(t * math.pi * 1.2) + 0.15 * math.cos(6.0 * t),
            ),
            t_min=0.0,
            t_max=1.0,
            steps=120,
            color=StudioPalette.SILVER,
            bevel_radius=0.035,
            emission_strength=4.5,
        )

    # 3. High-Speed Helical Broomstick Slipstreams (Crimson Gryffindor vs. Emerald Slytherin)
    scene.add_parametric_curve(
        name="GryffindorCrimsonSlipstream",
        func=lambda t: (
            t,
            0.95 * math.cos(1.65 * t),
            0.55 + 0.85 * math.sin(1.65 * t),
        ),
        t_min=-3.8,
        t_max=3.8,
        steps=320,
        color=StudioPalette.CRIMSON,
        bevel_radius=0.055,
        emission_strength=4.8,
    )
    scene.add_parametric_curve(
        name="SlytherinEmeraldSlipstream",
        func=lambda t: (
            t,
            -0.95 * math.cos(1.65 * t),
            0.55 - 0.85 * math.sin(1.65 * t),
        ),
        t_min=-3.8,
        t_max=3.8,
        steps=320,
        color=StudioPalette.EMERALD,
        bevel_radius=0.055,
        emission_strength=4.8,
    )


if __name__ == "__main__":
    StudioScene.run_cli(build_shot)
