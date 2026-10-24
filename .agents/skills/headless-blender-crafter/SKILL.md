---
name: headless-blender-crafter
description: >-
  Guides procedural 3D modeling, shader node construction, camera rigging, and headless
  rendering in Blender using Python (bpy) without storing binary .blend files in Git.
  Use when creating or modifying 3D shots (`engine: "blender"`), procedural geometries,
  lighting setups, or PBR/volumetric materials.
---

# Headless Blender Crafter (`bpy` Code-as-Scene)

Use this skill when authoring or debugging procedural 3D scenes in `episodes/<slug>/shots/*.py` or extending `packages/blender_rig/`.

## 1. Zero-Binary `.blend` Rules

- **Never save `.blend` files into Git-tracked folders.** Always build the scene programmatically starting from `packages.blender_rig.scene_builder.reset_scene()`.
- If you need to inspect or cache a generated `.blend` file locally for debugging, output it to `episodes/<slug>/renders/debug/<shot_id>.blend` (which is git-ignored).

## 2. Standard Shot Structure

Every Blender shot script in `episodes/<slug>/shots/` should use `packages.blender_rig`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.blender_rig.scene_builder import StudioScene, StudioPalette

def build_shot(scene: StudioScene):
    # 1. Camera & Studio Lighting
    scene.setup_three_point_lighting(energy_scale=1.2)
    cam = scene.create_orbit_camera(
        radius=7.5, elevation_deg=25.0, start_angle_deg=0.0, end_angle_deg=90.0
    )

    # 2. Procedural Geometry & Materials
    mat_primary = scene.create_emission_glass_material(
        name="WaveMaterial", color=StudioPalette.CYAN, strength=2.5
    )
    scene.create_parametric_wave_surface(name="HarmonicSurface", material=mat_primary)

if __name__ == "__main__":
    StudioScene.run_cli(build_shot)
```

## 3. Multimodal Preview & Verification Workflow

Before rendering a full animation, **always** render and inspect keyframe PNGs:

1. **Render a single keyframe preview** (fast EEVEE/Workbench or low-sample Cycles):
   ```bash
   python3 -m packages.pipeline_cli.studio preview <episode-slug> --shot <shot_id> --frame 30
   ```
2. **Inspect the PNG via `read_file`**:
   Call `read_file` on `episodes/<episode-slug>/renders/previews/<shot_id>_f0030.png` to check framing, exposure, shadows, and clipping.
3. **Adjust camera focal length, orbit radius, or shader nodes** based on visual inspection before full render.
