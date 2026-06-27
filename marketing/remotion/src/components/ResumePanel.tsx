import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { SignalMascot } from "./SignalMascot";

interface ResumePanelProps {
  particleProgress?: number; // 0 to 1, sweeps from left to right
  logoOpacity?: number;      // 0 to 1, fades out Signal watermark
  optimized?: boolean;       // whether to show the rewritten/improved text
  highlightedKeyword?: string;
  style?: React.CSSProperties;
}

export const ResumePanel: React.FC<ResumePanelProps> = ({
  particleProgress = 0,
  logoOpacity = 1,
  optimized = false,
  highlightedKeyword = "",
  style,
}) => {
  const frame = useCurrentFrame();

  // Wipe position (0% to 100% width)
  const wipePercentage = particleProgress * 100;

  // Render dummy particles along the wipe boundary if sweeping
  const showWipe = particleProgress > 0.01 && particleProgress < 0.99;

  return (
    <div
      style={{
        position: "relative",
        width: 820,
        height: 1100,
        background: "rgba(10, 10, 15, 0.45)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: 24,
        padding: "50px 60px",
        boxShadow: "0 30px 70px rgba(0,0,0,0.65), inset 0 1px 0 rgba(255,255,255,0.1)",
        backdropFilter: "blur(25px)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        gap: 40,
        ...style,
      }}
    >
      {/* Grid Overlay inside Resume card */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "linear-gradient(rgba(255,255,255,0.01) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.01) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
          pointerEvents: "none",
        }}
      />

      {/* ------------------------------------------------------------- */}
      {/* 1. Header (Name, Title, Watermark) */}
      {/* ------------------------------------------------------------- */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", zIndex: 5 }}>
        <div>
          <h2
            style={{
              margin: 0,
              fontFamily: '"Inter", sans-serif',
              fontWeight: 900,
              fontSize: 48,
              color: "#ffffff",
              letterSpacing: -1,
            }}
          >
            ALEXANDER CHEN
          </h2>
          <p
            style={{
              margin: "8px 0 0 0",
              fontFamily: '"Inter", sans-serif',
              fontWeight: 600,
              fontSize: 24,
              color: "#00f0ff",
              letterSpacing: 1.5,
              textTransform: "uppercase",
            }}
          >
            Senior Cloud Infrastructure Engineer
          </p>
        </div>

        {/* Signal Logo Watermark in top-right */}
        {logoOpacity > 0.01 && (
          <div
            style={{
              opacity: logoOpacity,
              display: "flex",
              alignItems: "center",
              gap: 12,
              background: "rgba(0,240,255,0.06)",
              border: "1px solid rgba(0,240,255,0.25)",
              padding: "10px 18px",
              borderRadius: 14,
              boxShadow: "0 0 15px rgba(0,240,255,0.08)",
              transition: "opacity 0.2s",
            }}
          >
            <SignalMascot logoMode style={{ width: 40, height: 40 }} />
            <span
              style={{
                fontFamily: '"Inter", sans-serif',
                fontWeight: 900,
                fontSize: 20,
                color: "#ffffff",
                letterSpacing: 2,
              }}
            >
              ATSHACKER
            </span>
          </div>
        )}
      </div>

      {/* Divider */}
      <div style={{ width: "100%", height: 1, background: "rgba(255,255,255,0.1)", zIndex: 2 }} />

      {/* ------------------------------------------------------------- */}
      {/* 2. Resume Sections */}
      {/* ------------------------------------------------------------- */}
      <div style={{ display: "flex", flexDirection: "column", gap: 36, zIndex: 2 }}>

        {/* Professional Summary */}
        <div>
          <h3 style={{ fontFamily: '"Inter", sans-serif', fontSize: 24, fontWeight: 800, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: 1.5, margin: "0 0 16px 0" }}>
            Professional Summary
          </h3>
          <p style={{ fontFamily: '"Inter", sans-serif', fontSize: 22, color: "rgba(255,255,255,0.85)", lineHeight: 1.5, margin: 0 }}>
            Results-driven infrastructure engineer with 6+ years designing scalable systems. Specialized in automating deployments, provisioning infrastructure-as-code, and deploying cloud pipelines. Proven success optimization.
          </p>
        </div>

        {/* Experience Section */}
        <div>
          <h3 style={{ fontFamily: '"Inter", sans-serif', fontSize: 24, fontWeight: 800, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: 1.5, margin: "0 0 20px 0" }}>
            Professional Experience
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                <strong style={{ fontFamily: '"Inter", sans-serif', fontSize: 24, color: "#ffffff" }}>Senior DevOps Architect</strong>
                <span style={{ fontFamily: '"Inter", sans-serif', fontSize: 22, color: "rgba(255,255,255,0.4)" }}>2022 - Present</span>
              </div>

              <ul style={{ paddingLeft: 30, margin: 0, display: "flex", flexDirection: "column", gap: 14 }}>
                <li style={{ fontFamily: '"Inter", sans-serif', fontSize: 22, color: "#ffffff", lineHeight: 1.4 }}>
                  {optimized ? (
                    <span>
                      Improved team workflow by <span style={{ color: "#00f0ff", fontWeight: 800 }}>automating weekly reporting</span>, reducing manual tracking time by <span style={{ color: "#00f0ff", fontWeight: 800 }}>35%</span>.
                    </span>
                  ) : (
                    <span style={{ color: "rgba(255,255,255,0.4)" }}>Helped improve team workflow.</span>
                  )}
                </li>

                <li style={{ fontFamily: '"Inter", sans-serif', fontSize: 22, color: "#ffffff", lineHeight: 1.4 }}>
                  {optimized ? (
                    <span>
                      Designed and scaled <span style={{ color: "#00f0ff", fontWeight: 800 }}>Kubernetes cluster deployments</span>, increasing application capacity by <span style={{ color: "#00f0ff", fontWeight: 800 }}>140%</span>.
                    </span>
                  ) : (
                    <span style={{ color: "rgba(255,255,255,0.4)" }}>Worked on cluster setups and deployments.</span>
                  )}
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Skills Section */}
        <div>
          <h3 style={{ fontFamily: '"Inter", sans-serif', fontSize: 24, fontWeight: 800, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: 1.5, margin: "0 0 16px 0" }}>
            Technical Core
          </h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 14 }}>
            {["AWS", "Kubernetes", "Docker", "Python", "SQL", "CI/CD", "Terraform", "Automation", "Leadership"].map(skill => {
              const isHighlighted = skill.toLowerCase() === highlightedKeyword.toLowerCase();
              return (
                <span
                  key={skill}
                  style={{
                    fontFamily: '"Inter", sans-serif',
                    fontSize: 20,
                    fontWeight: 700,
                    padding: "8px 18px",
                    borderRadius: 10,
                    background: isHighlighted ? "rgba(0,240,255,0.2)" : "rgba(255,255,255,0.04)",
                    color: isHighlighted ? "#00f0ff" : "rgba(255,255,255,0.7)",
                    border: `1.5px solid ${isHighlighted ? "#00f0ff" : "rgba(255,255,255,0.06)"}`,
                    boxShadow: isHighlighted ? "0 0 15px rgba(0,240,255,0.25)" : "none",
                    textTransform: "uppercase",
                    letterSpacing: 1,
                  }}
                >
                  {skill}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 3. Scanning/Wipe Neon Particle Line */}
      {/* ------------------------------------------------------------- */}
      {showWipe && (
        <>
          {/* Wipe Laser */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: `${wipePercentage}%`,
              width: 3,
              height: "100%",
              background: "#00f0ff",
              boxShadow: "0 0 15px #00f0ff, 0 0 30px #00f0ff",
              zIndex: 10,
            }}
          />
          {/* Half formed mask to represent right side in particle formation */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: `${wipePercentage}%`,
              width: `${100 - wipePercentage}%`,
              height: "100%",
              background: "rgba(10,10,25,0.45)",
              backdropFilter: "blur(4px) saturate(0.5)",
              zIndex: 8,
              pointerEvents: "none",
            }}
          />
        </>
      )}
    </div>
  );
};
