import React from "react";
import { HarmonicFieldStage } from "../../../packages/web-stage/src/components/HarmonicFieldStage";

// Shaders are tracked in Git under packages/shaders/
const VERTEX_SHADER_PATH = "packages/shaders/wave_interference.vert";
const FRAGMENT_SHADER_PATH = "packages/shaders/wave_interference.frag";

export const Shot01LateralPrismR3F: React.FC = () => {
  return (
    <HarmonicFieldStage
      title="1. Lateral Hook: Universal Wave Superposition"
      subtitle="Optics  •  Acoustics  •  Signal Compression  •  Quantum Fields"
      harmonicsCount={5}
      vertexShader={VERTEX_SHADER_PATH}
      fragmentShader={FRAGMENT_SHADER_PATH}
    />
  );
};
