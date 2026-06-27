import React from "react";

interface HudChecklistProps {
  progress: number; // 0 to 5, representing how many items are green-checked
  style?: React.CSSProperties;
}

export const HudChecklist: React.FC<HudChecklistProps> = ({ progress, style }) => {
  const items = [
    { label: "Formatting Standards", errorDesc: "Multiple column tables", successDesc: "Clean resume parser-safe layout" },
    { label: "Keywords Analysis", errorDesc: "Match density too low", successDesc: "Keyword density matches JD (94%)" },
    { label: "Experience Detail", errorDesc: "Vague action verbs used", successDesc: "Action verbs optimized" },
    { label: "Relevance Alignment", errorDesc: "Missing core credentials", successDesc: "Target credentials matched" },
    { label: "Impact Metrics", errorDesc: "No measurable data points", successDesc: "Action-result metrics inserted" },
  ];

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
        gap: 30,
        ...style,
      }}
    >
      <h3
        style={{
          margin: "0 0 10px 0",
          fontFamily: '"Inter", sans-serif',
          fontWeight: 900,
          fontSize: 28,
          color: "rgba(255,255,255,0.4)",
          textTransform: "uppercase",
          letterSpacing: 2,
        }}
      >
        ATS PARSER COMPLIANCE CHECK
      </h3>

      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {items.map((item, idx) => {
          const isChecked = progress >= idx + 1;
          const iconColor = isChecked ? "#00f0ff" : "#ff0055";
          const bgColor = isChecked ? "rgba(0,240,255,0.06)" : "rgba(255,0,85,0.04)";
          const borderStyle = `1.5px solid ${isChecked ? "rgba(0,240,255,0.3)" : "rgba(255,0,85,0.15)"}`;

          return (
            <div
              key={idx}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 24,
                padding: "20px 30px",
                background: bgColor,
                border: borderStyle,
                borderRadius: 16,
                transition: "all 0.2s ease-in-out",
              }}
            >
              {/* Checkbox status indicator */}
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 10,
                  border: `2px solid ${iconColor}`,
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  fontSize: 26,
                  fontWeight: 900,
                  color: iconColor,
                  background: "rgba(10,10,15,0.6)",
                  boxShadow: isChecked ? "0 0 10px rgba(0,240,255,0.25)" : "none",
                }}
              >
                {isChecked ? "✓" : "✕"}
              </div>

              {/* Text Labels */}
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    fontFamily: '"Inter", sans-serif',
                    fontSize: 24,
                    fontWeight: 700,
                    color: isChecked ? "#ffffff" : "rgba(255,255,255,0.4)",
                  }}
                >
                  {item.label}
                </div>
                <div
                  style={{
                    fontFamily: "monospace",
                    fontSize: 18,
                    fontWeight: 600,
                    marginTop: 4,
                    color: isChecked ? "rgba(0,240,255,0.7)" : "#ff0055",
                  }}
                >
                  {isChecked ? `[OK] ${item.successDesc}` : `[ERR] ${item.errorDesc}`}
                </div>
              </div>

              {/* Status Badge */}
              <div
                style={{
                  fontFamily: '"Inter", sans-serif',
                  fontWeight: 900,
                  fontSize: 18,
                  padding: "6px 16px",
                  borderRadius: 8,
                  background: isChecked ? "rgba(0,240,255,0.15)" : "rgba(255,0,85,0.15)",
                  color: iconColor,
                  letterSpacing: 1,
                }}
              >
                {isChecked ? "PASSED" : "FAILED"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
