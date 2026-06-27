import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface BulletTransformProps {
  progress: number; // 0 to 1
  style?: React.CSSProperties;
}

export const BulletTransform: React.FC<BulletTransformProps> = ({ progress, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Score count-up calculation
  const scoreVal = Math.round(interpolate(progress, [0.1, 0.9], [42, 76], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }));

  // Spring scale for the optimized bullet point when it appears
  const afterSpring = spring({
    frame: Math.max(0, frame - 810), // relative offset frame
    fps,
    config: { damping: 12, mass: 0.8 },
  });

  const afterScale = interpolate(afterSpring, [0, 1], [0.95, 1]);
  const afterOpacity = interpolate(progress, [0.3, 0.6], [0, 1]);

  return (
    <div
      style={{
        width: 820,
        background: "rgba(10, 10, 15, 0.45)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: 24,
        padding: "45px 50px",
        boxShadow: "0 30px 60px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.05)",
        backdropFilter: "blur(20px)",
        display: "flex",
        flexDirection: "column",
        gap: 36,
        ...style,
      }}
    >
      <h3
        style={{
          margin: 0,
          fontFamily: '"Inter", sans-serif',
          fontWeight: 900,
          fontSize: 28,
          color: "rgba(255,255,255,0.4)",
          textTransform: "uppercase",
          letterSpacing: 2,
        }}
      >
        BULLET POINT OPTIMIZATION
      </h3>

      <div style={{ display: "flex", gap: 30 }}>
        {/* Left Side: Before/After Bullet Cards */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Before Card */}
          <div
            style={{
              padding: 24,
              background: "rgba(255, 0, 85, 0.04)",
              border: "1.5px solid rgba(255, 0, 85, 0.25)",
              borderRadius: 16,
              opacity: interpolate(progress, [0.4, 0.8], [1, 0.45]),
            }}
          >
            <div style={{ fontFamily: "monospace", fontSize: 16, color: "#ff0055", fontWeight: 700, marginBottom: 8, letterSpacing: 1 }}>
              ORIGINAL WEAK TEXT
            </div>
            <p style={{ fontFamily: '"Inter", sans-serif', fontSize: 24, color: "rgba(255,255,255,0.7)", margin: 0, lineHeight: 1.4 }}>
              "Helped improve team workflow."
            </p>
          </div>

          {/* Transformation Arrow */}
          <div style={{ display: "flex", justifyContent: "center", color: "#00f0ff", fontSize: 32, opacity: progress }}>
            ↓
          </div>

          {/* After Card */}
          <div
            style={{
              padding: 24,
              background: "rgba(0, 240, 255, 0.06)",
              border: "1.5px solid #00f0ff",
              borderRadius: 16,
              opacity: afterOpacity,
              transform: `scale(${afterScale})`,
              boxShadow: "0 10px 30px rgba(0,240,255,0.08)",
            }}
          >
            <div style={{ fontFamily: "monospace", fontSize: 16, color: "#00f0ff", fontWeight: 700, marginBottom: 8, letterSpacing: 1 }}>
              ATSHACKER OPTIMIZED
            </div>
            <p style={{ fontFamily: '"Inter", sans-serif', fontSize: 24, color: "#ffffff", margin: 0, lineHeight: 1.4, fontWeight: 500 }}>
              "Improved team workflow by <span style={{ color: "#00f0ff", fontWeight: 800 }}>automating weekly reporting</span>, reducing manual tracking time by <span style={{ color: "#00f0ff", fontWeight: 800 }}>35%</span>."
            </p>
          </div>
        </div>

        {/* Right Side: Score Gauge */}
        <div
          style={{
            width: 200,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(255,255,255,0.02)",
            border: "1px solid rgba(255,255,255,0.04)",
            borderRadius: 18,
            padding: 20,
          }}
        >
          <div style={{ position: "relative", width: 140, height: 140, display: "flex", justifyContent: "center", alignItems: "center" }}>
            {/* SVG Ring Meter */}
            <svg width="140" height="140" viewBox="0 0 140 140" style={{ transform: "rotate(-90deg)" }}>
              {/* Underlay */}
              <circle cx="70" cy="70" r="58" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
              {/* Highlight Ring */}
              <circle
                cx="70"
                cy="70"
                r="58"
                fill="none"
                stroke={scoreVal >= 70 ? "#00f0ff" : "#ff0055"}
                strokeWidth="8"
                strokeDasharray={`${2 * Math.PI * 58}`}
                strokeDashoffset={`${2 * Math.PI * 58 * (1 - scoreVal / 100)}`}
                strokeLinecap="round"
                style={{ transition: "stroke-dashoffset 0.1s ease-out, stroke 0.2s" }}
              />
            </svg>
            <div style={{ position: "absolute", textAlign: "center" }}>
              <div
                style={{
                  fontFamily: '"Inter", sans-serif',
                  fontWeight: 900,
                  fontSize: 38,
                  color: "#ffffff",
                }}
              >
                {scoreVal}%
              </div>
            </div>
          </div>
          <div
            style={{
              marginTop: 16,
              fontFamily: '"Inter", sans-serif',
              fontWeight: 800,
              fontSize: 18,
              color: scoreVal >= 70 ? "#00f0ff" : "#ff0055",
              letterSpacing: 1,
              textTransform: "uppercase",
            }}
          >
            ATS Score
          </div>
        </div>
      </div>
    </div>
  );
};
