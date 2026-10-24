"""
Act II (Novel Ch. 7 - The Sorting Hat):
The Great Hall of Hogwarts — Gothic pointed cathedral arches framing dozens of levitating
wax candles with glowing golden flames beneath an enchanted starry night ceiling vortex.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.blender_rig.scene_builder import StudioPalette, StudioScene


def build_shot(scene: StudioScene) -> None:
    scene.title = "ACT II - THE GREAT HALL OF HOGWARTS"
    scene.subtitle = "Novel Ch. 7  |  A Thousand Floating Candles & The Enchanted Ceiling"
    scene.setup_three_point_lighting(
        energy_scale=1.2,
        key_color=StudioPalette.GOLD,
        fill_color=StudioPalette.VIOLET,
        rim_color=StudioPalette.CYAN,
    )
    scene.create_orbit_camera(
        radius=11.2,
        elevation_deg=18.0,
        start_angle_deg=-18.0,
        end_angle_deg=24.0,
        target=(0.0, 0.0, 0.8),
    )

    # 0. Imported 3D Assets: Twin Snowy Owl / Messenger Birds Soaring Through the Great Hall
    scene.import_glb_asset(
        name="HedwigMessengerBirdMain",
        filename="Parrot.glb",
        location=(-0.65, -0.85, 0.75),
        target_height=1.75,
        rotation_euler=(math.radians(12.0), 0.0, math.radians(25.0)),
        override_color=StudioPalette.WHITE,
        emission_strength=2.2,
    )
    scene.import_glb_asset(
        name="MessengerBirdCompanion",
        filename="Parrot.glb",
        location=(1.25, 0.55, 1.35),
        target_height=1.35,
        rotation_euler=(math.radians(-8.0), 0.0, math.radians(-30.0)),
        override_color=StudioPalette.GOLD,
        emission_strength=2.4,
    )

    # 1. Gothic Pointed Cathedral Arches Framing the Great Hall Nave
    for idx, y_pos in enumerate([-2.4, 0.0, 2.4]):
        scene.add_parametric_curve(
            name=f"GothicArchLeft_{idx}",
            func=lambda t, yp=y_pos: (-3.2 + 3.2 * math.sin(t), yp, -1.5 + 4.2 * math.sin(t)),
            t_min=0.0,
            t_max=math.pi * 0.5,
            steps=80,
            color=StudioPalette.VIOLET,
            bevel_radius=0.055,
            emission_strength=2.2,
        )
        scene.add_parametric_curve(
            name=f"GothicArchRight_{idx}",
            func=lambda t, yp=y_pos: (3.2 - 3.2 * math.sin(t), yp, -1.5 + 4.2 * math.sin(t)),
            t_min=0.0,
            t_max=math.pi * 0.5,
            steps=80,
            color=StudioPalette.VIOLET,
            bevel_radius=0.055,
            emission_strength=2.2,
        )

    # 2. 28 Levitating Candles (White Wax Cylinders + Glowing Gold Flame Orbs)
    for c_idx in range(28):
        row = c_idx // 7
        col = c_idx % 7
        cx = -2.4 + col * 0.8 + (0.2 if row % 2 else -0.2)
        cy = -2.2 + row * 1.45
        cz = 0.15 + 0.65 * math.sin(c_idx * 1.3) + (row % 2) * 0.45

        scene.add_cylinder(
            name=f"CandleWax_{c_idx:02d}",
            location=(cx, cy, cz),
            radius=0.045,
            depth=0.52,
            color=StudioPalette.WHITE,
            emission_strength=1.4,
        )
        scene.add_sphere(
            name=f"CandleFlame_{c_idx:02d}",
            location=(cx, cy, cz + 0.34),
            radius=0.075,
            color=StudioPalette.GOLD if c_idx % 3 != 0 else StudioPalette.AMBER,
            emission_strength=6.8,
        )

    # 3. Enchanted Starry Ceiling Galaxy Spiral Overhead (z = 2.5)
    scene.add_parametric_curve(
        name="EnchantedCeilingSpiral",
        func=lambda t: (
            0.38 * t * math.cos(2.4 * t),
            0.38 * t * math.sin(2.4 * t),
            2.45 + 0.15 * math.sin(t),
        ),
        t_min=0.5,
        t_max=7.5,
        steps=260,
        color=StudioPalette.CYAN,
        bevel_radius=0.025,
        emission_strength=3.5,
    )


if __name__ == "__main__":
    StudioScene.run_cli(build_shot)
