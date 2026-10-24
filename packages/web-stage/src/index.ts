import React from "react";
import { Composition, registerRoot } from "remotion";
import { HarmonicFieldStage } from "./components/HarmonicFieldStage";

const DEFAULT_VERT = `
uniform float uTime;
uniform float uHarmonics;
varying vec2 vUv;
varying float vElevation;

void main() {
    vUv = uv;
    vec3 pos = position;
    float w1 = sin(pos.x * 2.0 - uTime * 2.5) * cos(pos.y * 1.5);
    float w3 = (1.0 / 3.0) * sin(pos.x * 6.0 - uTime * 4.0) * sin(pos.y * 3.0) * clamp(uHarmonics - 1.0, 0.0, 1.0);
    float w5 = (1.0 / 5.0) * cos(pos.x * 10.0 + uTime * 5.5) * cos(pos.y * 5.0) * clamp(uHarmonics - 2.0, 0.0, 1.0);
    float elevation = (w1 + w3 + w5) * 0.65;
    pos.z += elevation;
    vElevation = elevation;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}
`;

const DEFAULT_FRAG = `
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
    gl_FragColor = vec4(mix(bg * 1.4, baseColor, 0.85), 0.95);
}
`;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="shot_01_lateral_prism_r3f"
        component={HarmonicFieldStage}
        durationInFrames={180}
        fps={60}
        width={1920}
        height={1080}
        defaultProps={{
          title: "1. Lateral Hook: Universal Wave Superposition",
          subtitle: "Optics  •  Acoustics  •  Signal Compression  •  Quantum Fields",
          harmonicsCount: 5,
          vertexShader: DEFAULT_VERT,
          fragmentShader: DEFAULT_FRAG,
        }}
      />
    </>
  );
};

registerRoot(RemotionRoot);
