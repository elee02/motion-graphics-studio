// ============================================================================
// STUDIO COMMON GLSL PALETTE & HARMONIC UTILITIES
// Shared across Three.js / React Three Fiber and Blender GLSL nodes.
// ============================================================================

const vec3 STUDIO_BG      = vec3(0.043, 0.059, 0.098); // #0B0F19 Deep Obsidian
const vec3 STUDIO_CYAN    = vec3(0.000, 0.898, 1.000); // #00E5FF Primary Harmonic
const vec3 STUDIO_AMBER   = vec3(1.000, 0.690, 0.000); // #FFB000 Energy / Phase
const vec3 STUDIO_VIOLET  = vec3(0.616, 0.306, 0.992); // #9D4EDD Higher Frequency
const vec3 STUDIO_EMERALD = vec3(0.063, 0.725, 0.506); // #10B981 Convergence

// Inigo Quilez cosine palette for smooth spectral transitions
vec3 spectralPalette(float t) {
    vec3 a = vec3(0.5, 0.5, 0.5);
    vec3 b = vec3(0.5, 0.5, 0.5);
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.00, 0.33, 0.67);
    return a + b * cos(6.28318 * (c * t + d));
}

// Superposition of N harmonic waves
float harmonicSuperposition(vec2 uv, float time, int harmonics) {
    float sum = 0.0;
    for (int k = 1; k <= 9; k += 2) {
        if (k > harmonics) break;
        float fk = float(k);
        float amp = 1.0 / fk;
        sum += amp * sin(fk * uv.x * 3.14159 - time * fk * 1.5) * cos(fk * uv.y * 1.57079);
    }
    return sum;
}
