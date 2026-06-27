import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

interface AtsGateProps {
  status: "scanning" | "warning" | "passed";
  openProgress: number; // 0 (closed) to 1 (fully open)
}

export const AtsGate: React.FC<AtsGateProps> = ({ status, openProgress }) => {
  const frame = useCurrentFrame();

  // Scanner sweep vertical translation
  const scannerY = interpolate(
    Math.sin(frame * 0.1),
    [-1, 1],
    [10, 90] // percentage from top to bottom
  );

  const getLaserColor = () => {
    if (status === "passed") return "#00f0ff"; // high-tech cyan
    if (status === "warning") return "#ff0055"; // warning red
    return "#ffaa00"; // orange scanning
  };

  const getStatusText = () => {
    if (status === "passed") return "MATCH ALIGNED - READY FOR REVIEW";
    if (status === "warning") return "LOW VISIBILITY - KEYWORD GAP DETECTED";
    return "SCANNING INCOMING RESUME... MATCHING IN PROGRESS";
  };

  const laserColor = getLaserColor();
  const leftSlide = -openProgress * 50; // slide left 50% of screen width
  const rightSlide = openProgress * 50; // slide right 50% of screen width

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 20,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none",
        overflow: "hidden",
      }}
    >
      {/* ------------------------------------------------------------- */}
      {/* 1. Left Gate Panel */}
      {/* ------------------------------------------------------------- */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "50%",
          height: "100%",
          background: "linear-gradient(to right, #08080c 40%, #0c0d16 100%)",
          borderRight: `2px dashed ${laserColor}`,
          transform: `translateX(${leftSlide}vw)`,
          transition: "transform 0.1s ease-out",
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",
          boxShadow: `0 0 40px rgba(0,0,0,0.8), inset -20px 0 50px rgba(${status === "passed" ? "0,100,255" : "255,0,0"},0.03)`,
        }}
      >
        {/* Left Side Technical Details */}
        <div style={{ marginRight: 30, color: "rgba(255,255,255,0.15)", fontFamily: "monospace", fontSize: 18, textAlign: "right" }}>
          <div>SYS_GATE_L_v2.0</div>
          <div>SECTOR_4_SECURE</div>
          <div style={{ color: laserColor }}>LOCK_STATE: {openProgress > 0 ? "RELEASING" : "ACTIVE"}</div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 2. Right Gate Panel */}
      {/* ------------------------------------------------------------- */}
      <div
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          width: "50%",
          height: "100%",
          background: "linear-gradient(to left, #08080c 40%, #0c0d16 100%)",
          borderLeft: `2px dashed ${laserColor}`,
          transform: `translateX(${rightSlide}vw)`,
          transition: "transform 0.1s ease-out",
          display: "flex",
          justifyContent: "flex-start",
          alignItems: "center",
          boxShadow: `0 0 40px rgba(0,0,0,0.8), inset 20px 0 50px rgba(${status === "passed" ? "0,100,255" : "255,0,0"},0.03)`,
        }}
      >
        {/* Right Side Technical Details */}
        <div style={{ marginLeft: 30, color: "rgba(255,255,255,0.15)", fontFamily: "monospace", fontSize: 18 }}>
          <div>SYS_GATE_R_v2.0</div>
          <div>SECTOR_4_SECURE</div>
          <div style={{ color: laserColor }}>MATCH_VAL: {status === "passed" ? "94%" : "42%"}</div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 3. Center Scanner Line (visible only when gate is not fully open) */}
      {/* ------------------------------------------------------------- */}
      {openProgress < 0.95 && (
        <div
          style={{
            position: "absolute",
            top: `${scannerY}%`,
            left: 0,
            width: "100%",
            height: 8,
            background: `linear-gradient(90deg, rgba(255,255,255,0) 0%, ${laserColor} 50%, rgba(255,255,255,0) 100%)`,
            boxShadow: `0 0 25px ${laserColor}, 0 0 10px ${laserColor}`,
            opacity: status === "passed" ? 0.3 : 1 - openProgress,
            zIndex: 22,
          }}
        />
      )}

      {/* ------------------------------------------------------------- */}
      {/* 4. Top/Bottom HUD Indicators */}
      {/* ------------------------------------------------------------- */}
      {openProgress < 0.9 && (
        <div
          style={{
            position: "absolute",
            top: 150,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            opacity: 1 - openProgress,
            zIndex: 25,
            transition: "opacity 0.2s",
          }}
        >
          <div
            style={{
              padding: "12px 36px",
              background: "rgba(10,10,15,0.85)",
              border: `2px solid ${laserColor}`,
              borderRadius: 12,
              boxShadow: `0 0 30px rgba(${status === "passed" ? "0,240,255" : "255,0,85"},0.15)`,
              display: "flex",
              alignItems: "center",
              gap: 15,
            }}
          >
            {/* Flashing light indicator */}
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                background: laserColor,
                animation: "pulse 1s infinite alternate",
                boxShadow: `0 0 10px ${laserColor}`,
              }}
            />
            <span
              style={{
                fontFamily: '"Inter", sans-serif',
                fontWeight: 900,
                fontSize: 34,
                color: "#ffffff",
                letterSpacing: 2,
              }}
            >
              ATS GATEWAY
            </span>
          </div>

          <div
            style={{
              marginTop: 30,
              fontFamily: "monospace",
              fontSize: 22,
              fontWeight: 700,
              color: laserColor,
              textAlign: "center",
              letterSpacing: 1,
              textShadow: `0 0 10px rgba(${status === "passed" ? "0,240,255" : "255,0,85"},0.4)`,
            }}
          >
            {getStatusText()}
          </div>
        </div>
      )}
    </div>
  );
};
