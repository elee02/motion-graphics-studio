// ============================================================================
// 3D HARMONIC WAVE INTERFERENCE - VERTEX SHADER
// Driven deterministically by uTime (frame / fps)
// ============================================================================
uniform float uTime;
uniform float uHarmonics;

varying vec2 vUv;
varying float vElevation;
varying vec3 vNormalDistorted;

void main() {
    vUv = uv;
    vec3 pos = position;

    // Fundamental + 3rd + 5th harmonic wave superposition
    float w1 = sin(pos.x * 2.0 - uTime * 2.5) * cos(pos.y * 1.5);
    float w3 = (1.0 / 3.0) * sin(pos.x * 6.0 - uTime * 4.0) * sin(pos.y * 3.0) * clamp(uHarmonics - 1.0, 0.0, 1.0);
    float w5 = (1.0 / 5.0) * cos(pos.x * 10.0 + uTime * 5.5) * cos(pos.y * 5.0) * clamp(uHarmonics - 2.0, 0.0, 1.0);

    float elevation = (w1 + w3 + w5) * 0.65;
    pos.z += elevation;
    vElevation = elevation;

    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}
