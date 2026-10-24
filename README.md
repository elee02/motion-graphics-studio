# Motion Graphics Studio — Code-as-Scene Pipeline for Antigravity IDE & Gemini Pro

A **Zero-Binary Git ("Code-as-Scene")** educational motion graphics and 3D visual storytelling monorepo designed for **Antigravity IDE** and **Gemini Pro**.

## Why "Code-as-Scene" Solves the Git vs. Heavy Media Problem

Traditional video projects bloat Git repositories with multi-gigabyte `.blend` files, textures, intermediate `.mov` renders, and `.mp4` exports. This monorepo enforces a strict separation:

| Tracked in Git (Lightweight `< 5 MB`) | Git-Ignored (`renders/` & `dist/` — Built On-Demand) |
| :--- | :--- |
| `story/script.md` & `story/storyboard.json` | Content-addressed shot caches (`renders/cache/<shot>_<sha256>.mp4`) |
| Headless Blender Python scripts (`bpy` in `shots/*.py` & `packages/blender_rig/`) | Keyframe PNG previews for Gemini Pro multimodal QA (`renders/previews/*.png`) |
| Three.js / React Three Fiber + Remotion components (`shots/*.tsx` & `packages/web-stage/`) | Debug `.blend` exports (`renders/debug/*.blend`) |
| GLSL Vertex & Fragment Shaders (`packages/shaders/*.vert`, `*.frag`, `*.glsl`) | Final mastered YouTube `.mp4` & thumbnail (`dist/`) |
| Manim mathematical scenes (`packages/manim_lib/`) | Intermediate audio stems & frame sequences |

## Quick Commands

```bash
# 1. Check SHA-256 cache status of all shots in an episode
make status EP=001-fourier-visualized

# 2. Render keyframe preview PNGs for multimodal visual inspection
make preview EP=001-fourier-visualized

# 3. Render uncached shots and master final YouTube MP4 + Chapters + Thumbnail
make build EP=001-fourier-visualized

# 4. Scaffold a brand-new episode
make new EP=002-maxwells-equations TITLE="Maxwell's Equations: How Light Propagates"
```

## Custom Antigravity Skills Included (`.agents/skills/`)

When you open this folder as your active workspace in Antigravity IDE, the agent automatically loads:
- [`GEMINI.md`](./GEMINI.md): Enforces Zero-Binary Git rules, frame-determinism, and multimodal keyframe verification.
- [`story-to-storyboard`](./.agents/skills/story-to-storyboard/SKILL.md): Designs dual-axis educational episodes combining **Lateral Exploration** (cross-disciplinary hooks) and **In-Depth Mechanics** (first-principles math & 3D cutaways).
- [`headless-blender-crafter`](./.agents/skills/headless-blender-crafter/SKILL.md): Procedural 3D geometry, shader nodes, and camera rigging via `bpy`.
- [`threejs-remotion-shader`](./.agents/skills/threejs-remotion-shader/SKILL.md): Frame-deterministic Three.js / R3F + GLSL shaders inside Remotion.
- [`manim-math-explainer`](./.agents/skills/manim-math-explainer/SKILL.md): Mathematical derivations styled to match the studio color palette.
- [`render-and-verify`](./.agents/skills/render-and-verify/SKILL.md): Content-addressed incremental rendering and multimodal visual QA via `read_file`.
