---
name: manim-math-explainer
description: >-
  Guides authoring mathematical, geometric, and algorithmic animations using Manim
  Community Edition (`packages/manim_lib/`). Use when creating equations, vector fields,
  coordinate transformations, or step-by-step formal proofs (`engine: "manim"`).
---

# Manim Mathematical Explainer Skill

Use this skill when creating `engine: "manim"` shots in `episodes/<slug>/shots/*.py`.

## 1. Studio Theme Consistency

Always subclass `StudioManimScene` from `packages.manim_lib.studio_theme` instead of raw `manim.Scene`. This guarantees:
- Unified studio background (`#0B0F19` deep obsidian) matching Blender and Three.js shots.
- Consistent accent colors (`CYAN`, `AMBER`, `VIOLET`, `EMERALD`) for variables across engines.
- Safe 16:9 YouTube title/caption margins so labels never collide with subtitles.

## 2. Visual Faithfulness Guidelines

- **Color-Code Mathematical Terms**: If a frequency $\omega$ is colored `StudioPalette.CYAN` in the equation, the corresponding rotating phasor or 3D wave in Blender/Three.js MUST also use `StudioPalette.CYAN`.
- **Save Last Frame for Inspection**:
  Run Manim with `-s -ql` first to generate a keyframe PNG, then call `read_file` on the output image to confirm zero LaTeX overlap or clipping before rendering at `-qh` (1080p60) or `-qk` (4K60).
