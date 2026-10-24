"""
Act IV (Novel Ch. 12 & 17 - The Mirror of Erised & The Philosopher's Stone):
The towering Golden Arch of the Mirror of Erised framing the levitating Blood-Crimson
Philosopher's Stone core, surrounded by spinning sacred alchemical transmutation rings.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.blender_rig.scene_builder import StudioPalette, StudioScene


def build_shot(scene: StudioScene) -> None:
    scene.title = "ACT IV - THE MIRROR OF ERISED & THE STONE"
    scene.subtitle = "Novel Ch. 12 & 17  |  I Show Not Your Face But Your Hearts Desire"
    scene.setup_three_point_lighting(
        energy_scale=1.5,
        key_color=StudioPalette.CRIMSON,
        fill_color=StudioPalette.GOLD,
        rim_color=StudioPalette.CYAN,
    )
    scene.create_orbit_camera(
        radius=10.6,
        elevation_deg=22.0,
        start_angle_deg=-22.0,
        end_angle_deg=28.0,
        target=(0.0, 0.0, 0.7),
    )

    # 0. Imported 3D Assets: Young Seeker Figure & Sculpted Golden Guardian Dragon
    scene.import_glb_asset(
        name="YoungSeekerBeforeMirror",
        filename="Xbot.glb",
        location=(-2.25, -0.95, -1.45),
        target_height=2.55,
        rotation_euler=(0.0, 0.0, math.radians(35.0)),
        override_color=StudioPalette.CYAN,
        emission_strength=1.8,
    )
    scene.import_glb_asset(
        name="ChamberGuardianDragon",
        filename="DragonAttenuation.glb",
        location=(2.35, -0.45, -1.45),
        target_height=2.5,
        rotation_euler=(0.0, 0.0, math.radians(-35.0)),
        override_color=StudioPalette.GOLD,
        emission_strength=2.0,
        animate_turntable_rev=0.2,
    )

    # 1. Ornate Golden Arch of the Mirror of Erised
    mirror_pts = [
        (-1.65, 0.0, -1.45),
        (-1.65, 0.0, 1.65),
        (0.0, 0.0, 2.85),
        (1.65, 0.0, 1.65),
        (1.65, 0.0, -1.45),
        (-1.65, 0.0, -1.45),
    ]
    scene.add_polyline_curve(
        name="MirrorOfErisedGoldenFrame",
        points=mirror_pts,
        color=StudioPalette.GOLD,
        bevel_radius=0.085,
        emission_strength=3.8,
    )

    # 2. The Blood-Red Philosopher's Stone Core + Sacred Alchemical Triangle & Rings
    scene.add_sphere(
        name="PhilosophersStoneCrimsonCore",
        location=(0.0, 0.0, 0.65),
        radius=0.42,
        color=StudioPalette.CRIMSON,
        emission_strength=8.0,
    )

    # Sacred Alchemical Triangle surrounding the Stone
    tri_r = 1.45
    tri_pts = [
        (0.0, 0.0, 0.65 + tri_r),
        (-tri_r * math.cos(math.radians(30.0)), 0.0, 0.65 - tri_r * math.sin(math.radians(30.0))),
        (tri_r * math.cos(math.radians(30.0)), 0.0, 0.65 - tri_r * math.sin(math.radians(30.0))),
        (0.0, 0.0, 0.65 + tri_r),
    ]
    scene.add_polyline_curve(
        name="AlchemicalTriangle",
        points=tri_pts,
        color=StudioPalette.CYAN,
        bevel_radius=0.04,
        emission_strength=4.2,
    )

    # 3. Spinning Gyroscopic Transmutation Rings
    scene.add_torus(
        name="AlchemyRingOuter",
        location=(0.0, 0.0, 0.65),
        major_radius=2.15,
        minor_radius=0.045,
        rotation_euler=(math.radians(65.0), math.radians(20.0), 0.0),
        color=StudioPalette.GOLD,
        emission_strength=3.2,
        animate_spin_axis=2,
        spin_revolutions=0.8,
    )
    scene.add_torus(
        name="AlchemyRingInner",
        location=(0.0, 0.0, 0.65),
        major_radius=1.15,
        minor_radius=0.038,
        rotation_euler=(math.radians(25.0), math.radians(70.0), 0.0),
        color=StudioPalette.AMBER,
        emission_strength=4.0,
        animate_spin_axis=1,
        spin_revolutions=1.0,
    )

    # 4. Rising Golden Phoenix / Spell Harmonic Lissajous Crown
    scene.add_parametric_curve(
        name="PhoenixHarmonicCrown",
        func=lambda t: (
            2.6 * math.sin(2.0 * t),
            1.4 * math.cos(3.0 * t),
            0.65 + 1.1 * math.sin(3.0 * t),
        ),
        t_min=0.0,
        t_max=2.0 * math.pi,
        steps=320,
        color=StudioPalette.AMBER,
        bevel_radius=0.03,
        emission_strength=3.2,
    )


if __name__ == "__main__":
    StudioScene.run_cli(build_shot)
