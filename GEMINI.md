# Motion Graphics Studio — Workspace Rules (`GEMINI.md`)

You are operating inside a **Code-as-Scene Educational Motion Graphics Monorepo** built for Antigravity IDE and Gemini Pro. Every visual asset, 3D model, shader, mathematical animation, and composite video is generated deterministically from source code.

## 1. Core Architectural Principle: Zero-Binary Git ("Code-as-Scene")

- **Never commit heavy media or binary 3D files to Git**: `.mp4`, `.mov`, `.png` frame sequences, `.blend`, `.glb`, `.wav`, and `.exr` files are strictly git-ignored.
- **Everything is Procedural & Reproducible**:
  - **Blender (`bpy`)**: Write Python scripts that construct meshes, Geometry Nodes, Shader Nodes, lighting, and camera animation from scratch using `packages/blender_rig/`. Never rely on manual edits inside a binary `.blend` file that aren't captured in Python.
  - **Three.js / React Three Fiber + Remotion (`packages/web-stage/`)**: All animations MUST be strictly frame-deterministic (`useCurrentFrame()` and `useVideoConfig()`). Never use `useFrame((state, delta) => ...)` with real-time clocks or `Math.random()` without a deterministic seed.
  - **Shaders (`packages/shaders/`)**: Store reusable GLSL vertex/fragment shaders (`.vert`, `.frag`, `.glsl`) in `packages/shaders/` and import them across both Three.js and Blender/compositor pipelines.
  - **Manim (`packages/manim_lib/`)**: Keep mathematical derivations and graph explanations modular and styled with `packages/manim_lib/studio_theme.py`.

## 2. Multimodal Visual Verification Loop (Crucial for Faithfulness)

Whenever you write or modify a 3D scene, shader, or motion graphics shot:
1. **Render a Keyframe Preview First**: Before rendering a full 60fps video sequence, run the CLI in `--preview-frame <N>` mode (or render keyframe timestamps: start, midpoint, climax) to `episodes/<id>/renders/previews/`.
2. **Visually Inspect with `read_file`**: Always call `read_file` on the generated `.png` preview frame (or low-res `.mp4` proxy) so you can visually verify:
   - Camera framing & composition (ensure subjects are not clipped or off-screen).
   - Lighting contrast, materials, and readability of 3D labels/typography.
   - Mathematical and physical accuracy of the visual metaphor.
3. **Iterate Before Full Render**: Fix any framing, shader artifact, or overlap issues in code and re-verify the preview frame before running a full shot render.

## 3. Educational Storytelling Structure (Lateral + Deep-Dive)

Every episode in `episodes/<episode-slug>/` must balance two modes of exploration in its `story/storyboard.json`:
- **Lateral Exploration (`mode: "lateral"`)**: Connects the core topic to adjacent disciplines, historical context, everyday analogies, or unexpected applications (best rendered with Remotion + Three.js interactive-style 3D mind-maps, shader transitions, or stylized Blender dioramas).
- **In-Depth Mechanics (`mode: "deep-dive"`)**: Rigorous, first-principles breakdown of how and why the phenomenon works (best rendered with Manim mathematical proofs, cross-section procedural Blender cutaways, and custom GLSL field visualizations).

## 4. Directory Layout & Conventions

- `episodes/<NNN-topic-slug>/`
  - `story/script.md` — Narrative voiceover & visual direction notes.
  - `story/storyboard.json` — Deterministic shot manifest (shot IDs, engine, duration, seed, audio cues, visual assertions).
  - `shots/` — Source code for each shot (`shot_01_*.py`, `shot_02_*.tsx`, etc.).
  - `renders/` — *(Git-ignored)* Content-addressed shot renders and keyframe PNG previews.
  - `dist/` — *(Git-ignored)* Mastered final episode `.mp4`, chapters, and thumbnail.
- `packages/blender_rig/` — Shared Python helper library for headless Blender (`bpy`) camera rigs, procedural PBR materials, volumetric studio lighting, and Geometry Node builders.
- `packages/manim_lib/` — Shared Manim base classes, studio color palette, and typography presets.
- `packages/shaders/` — Version-controlled GLSL shaders and procedural math functions.
- `packages/web-stage/` — Remotion + React Three Fiber + Three.js declarative motion graphics package.
- `packages/pipeline_cli/` — Unified build tool (`python3 -m packages.pipeline_cli.studio`) with SHA-256 shot caching, preview frame extraction, and FFmpeg mastering.
