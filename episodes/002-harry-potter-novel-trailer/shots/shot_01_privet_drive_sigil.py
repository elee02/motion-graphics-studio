"""
Act I (Novel Ch. 1 - The Boy Who Lived):
Dumbledore's Silver Put-Outer (Deluminator) drawing twelve golden streetlamp orbs of
Privet Drive into a spinning astronomical armillary sphere around the Lightning Bolt Scar sigil.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.blender_rig.scene_builder import StudioPalette, StudioScene


def build_shot(scene: StudioScene) -> None:
    scene.title = "ACT I - THE BOY WHO LIVED"
    scene.subtitle = "Novel Ch. 1  |  Twelve Streetlamps of Privet Drive & The Lightning Scar"
    scene.setup_three_point_lighting(
        energy_scale=1.35,
        key_color=StudioPalette.GOLD,
        fill_color=StudioPalette.CYAN,
        rim_color=StudioPalette.VIOLET,
    )
    scene.create_orbit_camera(
        radius=10.5,
        elevation_deg=22.0,
        start_angle_deg=-25.0,
        end_angle_deg=35.0,
        target=(0.0, 0.0, 0.4),
    )

    # 1. Central 3D Jagged Lightning Bolt Sigil (Amber-Gold high emission)
    bolt_pts = [
        (0.45, 0.0, 2.35),
        (-0.25, 0.0, 0.75),
        (0.30, 0.0, 0.75),
        (-0.45, 0.0, -1.05),
    ]
    scene.add_polyline_curve(
        name="LightningScarSigil",
        points=bolt_pts,
        color=StudioPalette.GOLD,
        bevel_radius=0.11,
        emission_strength=7.5,
    )

    # 2. Concentric Spinning Astronomical Deluminator Armillary Rings
    scene.add_torus(
        name="DeluminatorOuterRing",
        location=(0.0, 0.0, 0.55),
        major_radius=2.35,
        minor_radius=0.055,
        rotation_euler=(math.radians(55.0), math.radians(15.0), 0.0),
        color=StudioPalette.SILVER,
        emission_strength=1.8,
        animate_spin_axis=2,
        spin_revolutions=0.6,
    )
    scene.add_torus(
        name="DeluminatorInnerRing",
        location=(0.0, 0.0, 0.55),
        major_radius=1.75,
        minor_radius=0.045,
        rotation_euler=(math.radians(-40.0), math.radians(35.0), 0.0),
        color=StudioPalette.GOLD,
        emission_strength=3.2,
        animate_spin_axis=0,
        spin_revolutions=0.75,
    )

    # 3. Twelve Streetlamp Light-Orbs Spiraling Inward Along Twin Filaments
    for k in range(12):
        angle = (2.0 * math.pi * k) / 12.0
        dist = 2.6 + 1.4 * (k % 3) * 0.45
        ox = dist * math.cos(angle)
        oy = dist * math.sin(angle)
        oz = -0.6 + 0.22 * k
        scene.add_sphere(
            name=f"PrivetLampOrb_{k:02d}",
            location=(ox, oy, oz),
            radius=0.14,
            color=StudioPalette.AMBER if k % 2 == 0 else StudioPalette.CYAN,
            emission_strength=5.5,
        )

    #Twin light-absorption vortex streams
    scene.add_parametric_curve(
        name="PutOuterLightStreamA",
        func=lambda t: (
            (3.6 - 0.45 * t) * math.cos(1.8 * t),
            (3.6 - 0.45 * t) * math.sin(1.8 * t),
            -1.1 + 0.38 * t,
        ),
        t_min=0.0,
        t_max=6.5,
        steps=240,
        color=StudioPalette.AMBER,
        bevel_radius=0.032,
        emission_strength=3.8,
    )
    scene.add_parametric_curve(
        name="PutOuterLightStreamB",
        func=lambda t: (
            -(3.6 - 0.45 * t) * math.cos(1.8 * t),
            -(3.6 - 0.45 * t) * math.sin(1.8 * t),
            -1.1 + 0.38 * t,
        ),
        t_min=0.0,
        t_max=6.5,
        steps=240,
        color=StudioPalette.CYAN,
        bevel_radius=0.028,
        emission_strength=3.2,
    )


if __name__ == "__main__":
    StudioScene.run_cli(build_shot)
