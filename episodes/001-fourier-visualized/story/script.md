# Episode 001: The Geometry of Sound & Light — Visualizing the Fourier Transform

## Narrative Overview
- **Target Audience**: Curious generalists & STEM learners on YouTube.
- **Educational Structure**:
  1. **Lateral Hook (`shot_01_lateral_prism_r3f`)**: Connects acoustic chords, glass optical prisms, JPEG image compression, and radio telescopes as expressions of a single universal idea: *frequency decomposition*.
  2. **3D Spatial Intuition (`shot_02_3d_helix_blender`)**: Shifts into 3D space where a complex rotating helix $e^{i\omega t}$ casts orthogonal shadows—revealing how sine (real/vertical) and cosine (imaginary/horizontal) projections unify into a single 3D spiral.
  3. **In-Depth Mathematical Proof (`shot_03_epicycles_manim`)**: Step-by-step rotating phasor epicycles ($k = 1, 3, 5, 7$) synthesizing a crisp square wave from pure harmonic circles.

---

## Script & Visual Cues

| Shot ID | Mode | Engine | Visual & Camera Direction | Voiceover Narration |
| :--- | :--- | :--- | :--- | :--- |
| `shot_01_lateral_prism_r3f` | `lateral` | `r3f-remotion` | 3D GLSL wave interference surface morphing across harmonics (`packages/shaders/wave_interference.vert`). Camera sweeps from `-25°` to `+30°`. | *"What do a glass prism splitting sunlight, the Wi-Fi antenna in your phone, and the cochlea inside your inner ear have in common? They all run the exact same mathematical algorithm in hardware."* |
| `shot_02_3d_helix_blender` | `deep-dive` | `blender` | Headless Blender 3D scene (`bpy`): Cyan 3D complex Euler helix $e^{i\omega t}$ spiraling along the time axis, with Amber cosine shadow on the floor plane and Violet sine shadow on the back wall. Orbit camera rotates `90°`. | *"When we look at a wave in two dimensions, sine and cosine look like separate oscillations. Step into three dimensions, and they are simply two shadows cast by a single uniform helix."* |
| `shot_03_epicycles_manim` | `deep-dive` | `manim` | Manim mathematical canvas: 4 nested harmonic epicycles ($\omega, 3\omega, 5\omega, 7\omega$) rotating in sync on the left, tracing out a real-time square wave on the right. | *"By stacking rotating vectors of odd frequencies—each scaled by one over k—smooth circular motion sharpens into the crisp corners of a digital square wave."* |
