import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface KeywordStreamProps {
  style?: React.CSSProperties;
}

export const KeywordStream: React.FC<KeywordStreamProps> = ({ style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const keywords = [
    { text: "SQL", startOffset: 0, y: 350 },
    { text: "Leadership", startOffset: 25, y: 450 },
    { text: "Customer Growth", startOffset: 50, y: 550 },
    { text: "Product Strategy", startOffset: 75, y: 650 },
    { text: "Automation", startOffset: 100, y: 750 },
    { text: "Stakeholder Management", startOffset: 125, y: 850 },
  ];

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 15,
        pointerEvents: "none",
        ...style,
      }}
    >
      {/* Visual Indicator of Job Description Panel on Left */}
      <div
        style={{
          position: "absolute",
          top: 300,
          left: 40,
          width: 320,
          background: "rgba(255, 255, 255, 0.02)",
          border: "1px solid rgba(255, 255, 255, 0.05)",
          borderRadius: 16,
          padding: 24,
          backdropFilter: "blur(5px)",
        }}
      >
        <div style={{ fontFamily: "monospace", fontSize: 16, color: "rgba(255,255,255,0.35)", marginBottom: 12 }}>
          SYS://SOURCE_JOB_JD.TXT
        </div>
        <div style={{ fontFamily: '"Inter", sans-serif', fontSize: 20, color: "rgba(255,255,255,0.7)", lineHeight: 1.4 }}>
          "Required: experienced engineer with strong <span style={{ color: "#00f0ff" }}>SQL</span> expertise, team <span style={{ color: "#00f0ff" }}>Leadership</span> skills, who drove <span style={{ color: "#00f0ff" }}>Customer Growth</span>. Must align <span style={{ color: "#00f0ff" }}>Product Strategy</span> and deliver pipeline <span style={{ color: "#00f0ff" }}>Automation</span> and <span style={{ color: "#00f0ff" }}>Stakeholder Management</span>..."
        </div>
      </div>

      {/* Extracted Floating Keywords */}
      {keywords.map((kw, i) => {
        // Timeline calculation
        const kwStart = 330 + kw.startOffset;
        const kwEnd = kwStart + 60; // 2 seconds duration

        if (frame < kwStart || frame > kwEnd) return null;

        const progress = (frame - kwStart) / (kwEnd - kwStart);

        // Interpolations
        // X sweeps from job description box (~200px) to resume panel (~600px)
        const x = interpolate(progress, [0, 1], [220, 680]);
        // Wave-like Y motion
        const wave = Math.sin(progress * Math.PI) * 45;
        const y = kw.y + wave;

        // Opacity and scale
        const opacity = interpolate(progress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);
        const scale = interpolate(progress, [0, 0.2, 0.9, 1], [0.8, 1.1, 1, 0.8]);

        return (
          <div
            key={kw.text}
            style={{
              position: "absolute",
              left: x,
              top: y,
              transform: `translate(-50%, -50%) scale(${scale})`,
              opacity: opacity,
              background: "rgba(0, 240, 255, 0.12)",
              border: "2px solid #00f0ff",
              boxShadow: "0 0 20px rgba(0,240,255,0.35), inset 0 0 10px rgba(0,240,255,0.1)",
              padding: "14px 28px",
              borderRadius: 14,
              display: "flex",
              alignItems: "center",
              gap: 8,
              zIndex: 100,
            }}
          >
            {/* Glowing dot icon */}
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: "#00f0ff",
                boxShadow: "0 0 8px #00f0ff",
              }}
            />
            <span
              style={{
                fontFamily: '"Inter", sans-serif',
                fontWeight: 800,
                fontSize: 22,
                color: "#ffffff",
                textTransform: "uppercase",
                letterSpacing: 1,
              }}
            >
              {kw.text}
            </span>
          </div>
        );
      })}
    </div>
  );
};
