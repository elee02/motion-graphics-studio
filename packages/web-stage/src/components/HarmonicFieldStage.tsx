import React, { useMemo } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import * as THREE from "three";

export interface HarmonicFieldProps {
  title: string;
  subtitle: string;
  harmonicsCount: number;
  vertexShader: string;
  fragmentShader: string;
}

/**
 * Deterministic 3D Three.js + Custom GLSL Shader Stage for Remotion.
 * Driven 100% by `useCurrentFrame()` so parallel headless renders never drift.
 */
export const HarmonicFieldStage: React.FC<HarmonicFieldProps> = ({
  title,
  subtitle,
  harmonicsCount,
  vertexShader,
  fragmentShader,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const timeSec = frame / fps;

  const cameraAzimuth = interpolate(frame, [0, durationInFrames], [-0.45, 0.55]);
  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uHarmonics: { value: harmonicsCount },
    }),
    [harmonicsCount]
  );

  // Deterministically update uniform for current frame
  uniforms.uTime.value = timeSec;
  uniforms.uHarmonics.value = interpolate(
    frame,
    [0, durationInFrames * 0.7],
    [1.0, harmonicsCount],
    { extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#0B0F19", color: "#F8FAFC", fontFamily: "Inter, sans-serif" }}>
      <ThreeCanvas
        width={width}
        height={height}
        camera={{ position: [Math.sin(cameraAzimuth) * 4.5, -Math.cos(cameraAzimuth) * 4.5, 2.8], fov: 42 }}
      >
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, -5, 8]} intensity={1.4} />
        <mesh rotation={[0, 0, 0]}>
          <planeGeometry args={[5.5, 5.5, 128, 128]} />
          <shaderMaterial
            vertexShader={vertexShader}
            fragmentShader={fragmentShader}
            uniforms={uniforms}
            transparent
            side={THREE.DoubleSide}
          />
        </mesh>
      </ThreeCanvas>

      {/* Crisp HTML/SVG Educational Typography Overlay */}
      <div
        style={{
          position: "absolute",
          top: 52,
          left: 64,
          display: "flex",
          flexDirection: "column",
          gap: 8,
          pointerEvents: "none",
        }}
      >
        <div style={{ fontSize: 38, fontWeight: 700, letterSpacing: "-0.02em" }}>{title}</div>
        <div style={{ fontSize: 22, color: "#00E5FF", fontWeight: 500 }}>{subtitle}</div>
      </div>
    </AbsoluteFill>
  );
};
