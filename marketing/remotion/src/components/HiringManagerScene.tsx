import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { ResumePanel } from "./ResumePanel";

interface HiringManagerSceneProps {
  style?: React.CSSProperties;
}

export const HiringManagerScene: React.FC<HiringManagerSceneProps> = ({ style }) => {
  const frame = useCurrentFrame();

  // Progress sweep for the resume inside the monitor: finishes assembling
  // between frames 1560 and 1680.
  const particleProgress = interpolate(frame, [1560, 1680], [0.3, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Signal logo watermark fades out between frames 1680 and 1780.
  const logoOpacity = interpolate(frame, [1680, 1780], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Hiring manager silhouette opacity: fades in at frame 1560
  const managerOpacity = interpolate(frame, [1560, 1600], [0, 0.45], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 10,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        background: "radial-gradient(circle at center, #141624 0%, #06070a 100%)",
        overflow: "hidden",
        ...style,
      }}
    >
      {/* ------------------------------------------------------------- */}
      {/* 1. Office Window / Background elements */}
      {/* ------------------------------------------------------------- */}
      <div
        style={{
          position: "absolute",
          top: 100,
          width: 900,
          height: 400,
          background: "rgba(255, 255, 255, 0.01)",
          border: "1px solid rgba(255,255,255,0.03)",
          borderRadius: 20,
          display: "flex",
          justifyContent: "space-around",
          alignItems: "center",
        }}
      >
        {/* Simplified window grids representing skyscraper lights outside */}
        <div style={{ display: "flex", gap: 10 }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} style={{ width: 14, height: 14, background: "rgba(0, 240, 255, 0.05)", borderRadius: 2 }} />
          ))}
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} style={{ width: 14, height: 14, background: "rgba(0, 240, 255, 0.05)", borderRadius: 2 }} />
          ))}
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 2. Cybernetic Monitor Console */}
      {/* ------------------------------------------------------------- */}
      <div
        style={{
          position: "relative",
          width: 800,
          height: 600,
          background: "#08090f",
          border: "4px solid rgba(255, 255, 255, 0.12)",
          borderRadius: 24,
          padding: 10,
          boxShadow: "0 40px 100px rgba(0,0,0,0.8), 0 0 50px rgba(0, 240, 255, 0.05)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          zIndex: 5,
        }}
      >
        {/* Glowing Screen Canvas */}
        <div
          style={{
            position: "relative",
            width: "100%",
            height: "100%",
            background: "#020306",
            borderRadius: 14,
            overflow: "hidden",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            border: "1px solid rgba(0,240,255,0.08)",
          }}
        >
          {/* Grid background inside screen */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundImage: "linear-gradient(rgba(0,240,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(0,240,255,0.02) 1px, transparent 1px)",
              backgroundSize: "20px 20px",
            }}
          />

          {/* Scaled Resume inside screen */}
          <div style={{ transform: "scale(0.48)", transformOrigin: "center center" }}>
            <ResumePanel
              optimized
              particleProgress={particleProgress}
              logoOpacity={logoOpacity}
              highlightedKeyword={frame >= 1860 && frame < 2040 ? "SQL" : ""}
            />
          </div>

          {/* Screen HUD Frame lines */}
          <div
            style={{
              position: "absolute",
              bottom: 12,
              left: 20,
              fontFamily: "monospace",
              fontSize: 14,
              color: "rgba(0,240,255,0.4)",
            }}
          >
            DISP_SYS: RUNNING // PORT: 8080
          </div>
          <div
            style={{
              position: "absolute",
              bottom: 12,
              right: 20,
              fontFamily: "monospace",
              fontSize: 14,
              color: logoOpacity > 0.5 ? "#00f0ff" : "rgba(255,255,255,0.2)",
              transition: "color 0.3s",
            }}
          >
            {logoOpacity > 0.5 ? "HOLOGRAPHIC_CO-PILOT_LINKED" : "HOLOGRAPHIC_CO-PILOT_TERMINATED"}
          </div>
        </div>

        {/* Monitor Stand */}
        <div
          style={{
            position: "absolute",
            bottom: -50,
            left: "50%",
            transform: "translateX(-50%)",
            width: 140,
            height: 50,
            background: "#08090f",
            borderLeft: "4px solid rgba(255,255,255,0.12)",
            borderRight: "4px solid rgba(255,255,255,0.12)",
            zIndex: -1,
          }}
        />
        {/* Monitor Base */}
        <div
          style={{
            position: "absolute",
            bottom: -65,
            left: "50%",
            transform: "translateX(-50%)",
            width: 320,
            height: 16,
            background: "#06070a",
            border: "3px solid rgba(255, 255, 255, 0.12)",
            borderRadius: 8,
            zIndex: -2,
          }}
        />
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 3. Hiring Manager Silhouette (Overlaid in foreground) */}
      {/* ------------------------------------------------------------- */}
      <div
        style={{
          position: "absolute",
          bottom: -100,
          right: -100,
          width: 500,
          height: 600,
          background: "radial-gradient(circle at 70% 80%, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.9) 70%, transparent 100%)",
          zIndex: 10,
          opacity: managerOpacity,
          pointerEvents: "none",
          transform: "scaleX(-1)", // mirror silhouette to bottom-right corner face in
        }}
      >
        {/* Custom SVG path silhouette of a human shoulder/head leaning in */}
        <svg width="100%" height="100%" viewBox="0 0 500 600" fill="#030305">
          <path d="M 100 600 Q 150 250 250 200 Q 330 180 340 100 Q 320 20 400 0 Q 480 30 470 120 Q 490 280 500 600 Z" />
        </svg>
      </div>

      {/* Ambient glowing monitor spill onto manager */}
      {managerOpacity > 0 && (
        <div
          style={{
            position: "absolute",
            bottom: 50,
            right: 150,
            width: 250,
            height: 250,
            background: "radial-gradient(circle, rgba(0,240,255,0.06) 0%, rgba(0,0,0,0) 70%)",
            filter: "blur(30px)",
            zIndex: 11,
            pointerEvents: "none",
          }}
        />
      )}
    </div>
  );
};
