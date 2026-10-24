---
name: threejs-remotion-shader
description: >-
  Guides authoring deterministic Three.js, React Three Fiber (@react-three/fiber),
  and custom GLSL shader animations inside Remotion (`packages/web-stage/`).
  Use when creating interactive-style 3D graphs, shader visualizations, lateral topic
  maps, or kinetic typography overlays (`engine: "r3f-remotion"`).
---

# Three.js + Remotion + GLSL Shader Skill

Use this skill when building declarative web/3D motion graphics in `packages/web-stage/` or `episodes/<slug>/shots/*.tsx` and custom shaders in `packages/shaders/`.

## 1. Frame-Deterministic Rendering Rules (Critical)

Headless Chromium rendering via Remotion captures frames out-of-order and in parallel. To guarantee 100% deterministic, flicker-free output:
1. **Drive Time via `useCurrentFrame()` Only**:
   ```tsx
   const frame = useCurrentFrame();
   const { fps } = useVideoConfig();
   const timeSec = frame / fps;
   ```
   Pass `timeSec` directly into your GLSL shader `uTime` uniform and mesh transforms.
2. **Never use `useFrame((state, delta) => ...)` with real-time `clock.getElapsedTime()`** or incremental state mutation (`mesh.rotation.y += delta`). Every frame `N` must be a pure function of `(N, fps, props)`.
3. **Wrap Three.js Canvas in `<ThreeCanvas>`** from `@remotion/three` with explicit `width` and `height` from `useVideoConfig()`.

## 2. Sharing GLSL Shaders (`packages/shaders/`)

- Store vertex and fragment shaders as pure `.glsl`, `.vert`, or `.frag` files in `packages/shaders/`.
- Use shared utility chunks like `packages/shaders/common/math_palette.glsl` so colors and harmonic functions match Blender and Manim shots seamlessly.

## 3. Single-Frame Visual Verification

Render a still PNG from Remotion before running a full MP4 encode:
```bash
npx remotion still packages/web-stage/src/index.ts <CompositionId> episodes/<slug>/renders/previews/<shot_id>.png --frame=45
```
Then inspect `episodes/<slug>/renders/previews/<shot_id>.png` with `read_file`.
