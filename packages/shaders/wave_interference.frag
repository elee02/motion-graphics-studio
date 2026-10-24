// ============================================================================
// 3D HARMONIC WAVE INTERFERENCE - FRAGMENT SHADER
// ============================================================================
uniform float uTime;
varying vec2 vUv;
varying float vElevation;

void main() {
    vec3 bg     = vec3(0.043, 0.059, 0.098);
    vec3 cyan   = vec3(0.000, 0.898, 1.000);
    vec3 violet = vec3(0.616, 0.306, 0.992);
    vec3 amber  = vec3(1.000, 0.690, 0.000);

    float normalizedHeight = clamp((vElevation + 0.8) / 1.6, 0.0, 1.0);
    vec3 baseColor = mix(violet, cyan, normalizedHeight);
    baseColor = mix(baseColor, amber, pow(normalizedHeight, 4.0));

    // Crisp isoline grid for mathematical clarity
    float gridX = abs(fract(vUv.x * 24.0 - 0.5) - 0.5) / fwidth(vUv.x * 24.0);
    float gridY = abs(fract(vUv.y * 24.0 - 0.5) - 0.5) / fwidth(vUv.y * 24.0);
    float gridLine = 1.0 - min(min(gridX, gridY), 1.0);

    vec3 finalColor = mix(bg * 1.4, baseColor, 0.35 + 0.65 * gridLine);
    gl_FragColor = vec4(finalColor, 0.92);
}
