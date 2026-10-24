---
name: story-to-storyboard
description: >-
  Transforms an educational topic or concept into a structured visual storytelling script
  and deterministic storyboard.json manifest. Use when planning a new YouTube episode,
  designing lateral and in-depth educational explorations, or breaking a script into
  Blender, Three.js/Remotion, and Manim shots.
---

# Story-to-Storyboard Skill (Lateral + Deep-Dive Architecture)

Use this skill whenever the user wants to plan a new episode, explore a topic, or convert a rough idea into a multi-engine production pipeline inside `episodes/<NNN-slug>/`.

## 1. Dual-Axis Educational Framework

To make educational videos both intellectually faithful and visually captivating, structure every episode across two axes:
1. **Lateral Hook & Connections (`"mode": "lateral"`)**:
   - Shows *where this concept lives in the wider universe* (historical origin, cross-disciplinary bridges, surprising real-world systems).
   - **Recommended Engines**: `r3f-remotion` (3D spatial canvas, typography, shader transitions) or `blender` (physical metaphors & dioramas).
2. **In-Depth First Principles (`"mode": "deep-dive"`)**:
   - Deconstructs the exact mathematical, physical, or algorithmic mechanism without hand-waving.
   - **Recommended Engines**: `manim` (equations, coordinate transforms, proofs) combined with `blender` (3D cutaway mechanics, volumetric fields) or `r3f-remotion` (custom GLSL simulations).

## 2. Step-by-Step Procedure

1. **Scaffold the Episode Directory**:
   ```bash
   python3 -m packages.pipeline_cli.studio init-episode <NNN-slug> --title "<Episode Title>"
   ```
2. **Draft `episodes/<NNN-slug>/story/script.md`**:
   - Write the narrative in synchronized 2-column blocks: `[Timecode / Shot ID | Visual & Camera Direction | Voiceover Narration]`.
   - Explicitly annotate each section with `[LATERAL]` or `[DEEP-DIVE]`.
3. **Generate `episodes/<NNN-slug>/story/storyboard.json`**:
   - Define each shot with:
     - `id`: e.g., `"shot_01_hook"`
     - `mode`: `"lateral"` or `"deep-dive"`
     - `engine`: `"blender"` | `"r3f-remotion"` | `"manim"`
     - `entry`: Relative path to the shot script in `shots/`
     - `duration_sec`: Exact duration in seconds
     - `fps`: `60` (default)
     - `seed`: Integer seed for deterministic procedural generation
     - `keyframe_checks`: Array of normalized timestamps (`[0.1, 0.5, 0.9]`) and visual assertions describing what must be visible in the frame.
4. **Validate the Manifest**:
   ```bash
   python3 -m packages.pipeline_cli.studio status <NNN-slug>
   ```
