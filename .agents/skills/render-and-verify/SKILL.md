---
name: render-and-verify
description: >-
  Executes the content-addressed incremental build pipeline, renders keyframe previews,
  performs multimodal visual quality checks, and masters the final YouTube MP4 via FFmpeg.
  Use when previewing shots, verifying visual faithfulness, checking cache status, or
  assembling an episode.
---

# Render, Multimodal Verification & Mastering Skill

Use this skill to orchestrate shot previews, incremental caching, visual inspection, and final FFmpeg mastering via `packages/pipeline_cli/studio.py`.

## 1. Incremental Content-Addressed Caching

Why re-render a 5-minute 3D scene if only one shot changed?
`studio.py` computes a SHA-256 hash over:
1. The shot's source file (`shots/shot_XX.py` or `.tsx`)
2. Any imported shaders in `packages/shaders/`
3. The shot's parameters in `story/storyboard.json` (duration, fps, resolution, seed)

Cached renders are stored in `episodes/<slug>/renders/cache/<shot_id>_<sha256[:12]>.mp4`.

## 2. Multimodal Quality Assurance Loop

For every shot in `storyboard.json`:
1. **Generate Keyframe Previews**:
   ```bash
   python3 -m packages.pipeline_cli.studio preview <episode-slug> --shot <shot_id>
   ```
2. **Inspect with `read_file`**:
   Read the generated `.png` keyframes in `episodes/<episode-slug>/renders/previews/`.
   Check against the shot's `keyframe_checks` in `storyboard.json`:
   - Is the primary subject centered and well-lit?
   - Are text labels legible against the background?
   - Do colors match the studio palette?
3. **Render Full Shots & Master Episode**:
   ```bash
   python3 -m packages.pipeline_cli.studio build <episode-slug>
   ```
   This renders any uncached shots, concatenates them cleanly, normalizes audio to `-14 LUFS` (YouTube standard), and outputs `episodes/<episode-slug>/dist/<episode-slug>_master.mp4` + YouTube chapters.
