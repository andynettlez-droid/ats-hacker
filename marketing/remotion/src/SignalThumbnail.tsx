import React from "react";
import { AbsoluteFill } from "remotion";
import { z } from "zod";
import { SignalMascot } from "./components/SignalMascot";

export const signalThumbnailSchema = z.object({
  title: z.string(),
  badge: z.string(),
  beforeScore: z.number(),
  afterScore: z.number(),
  leftLabel: z.string(),
  rightLabel: z.string(),
  keywords: z.array(z.string()),
});

export type SignalThumbnailProps = z.infer<typeof signalThumbnailSchema>;

export const defaultSignalThumbnailProps: SignalThumbnailProps = {
  title: "Qualified but invisible",
  badge: "Resume teardown",
  beforeScore: 34,
  afterScore: 92,
  leftLabel: "Vague resume",
  rightLabel: "Job-match proof",
  keywords: ["HubSpot", "CAC", "LinkedIn Ads"],
};

const TEXT = "#f8fafc";
const MUTED = "#94a3b8";
const CYAN = "#38d5ff";
const GREEN = "#22c55e";
const RED = "#fb7185";
const YELLOW = "#facc15";
const FONT = '"Inter", "Helvetica Neue", Arial, sans-serif';

const Panel: React.FC<{ label: string; tone: "bad" | "good"; children: React.ReactNode }> = ({
  label,
  tone,
  children,
}) => (
  <div
    style={{
      flex: 1,
      height: 474,
      borderRadius: 30,
      padding: 30,
      background: tone === "good" ? "rgba(34,197,94,0.10)" : "rgba(251,113,133,0.10)",
      border: `3px solid ${tone === "good" ? "rgba(34,197,94,0.45)" : "rgba(251,113,133,0.48)"}`,
      boxShadow: `0 22px 80px ${tone === "good" ? "rgba(34,197,94,0.16)" : "rgba(251,113,133,0.16)"}`,
      position: "relative",
      overflow: "hidden",
    }}
  >
    <div
      style={{
        color: tone === "good" ? "#bbf7d0" : "#fecdd3",
        fontSize: 24,
        fontWeight: 950,
        textTransform: "uppercase",
        letterSpacing: 1.5,
      }}
    >
      {label}
    </div>
    {children}
  </div>
);

const Score: React.FC<{ value: number; tone: "bad" | "good" }> = ({ value, tone }) => (
  <div
    style={{
      position: "absolute",
      right: 28,
      bottom: 24,
      color: tone === "good" ? GREEN : RED,
      fontSize: 82,
      lineHeight: 0.9,
      fontWeight: 950,
      textShadow: `0 0 30px ${tone === "good" ? "rgba(34,197,94,0.26)" : "rgba(251,113,133,0.26)"}`,
    }}
  >
    {value}
    <span style={{ color: MUTED, fontSize: 34 }}>/100</span>
  </div>
);

export const SignalThumbnail: React.FC<SignalThumbnailProps> = ({
  title,
  badge,
  beforeScore,
  afterScore,
  leftLabel,
  rightLabel,
  keywords,
}) => (
  <AbsoluteFill
    style={{
      background:
        "radial-gradient(circle at 18% 12%, rgba(251,113,133,0.17), transparent 25rem), radial-gradient(circle at 84% 20%, rgba(56,213,255,0.22), transparent 29rem), linear-gradient(135deg, #020617 0%, #030712 48%, #06101e 100%)",
      color: TEXT,
      fontFamily: FONT,
      padding: 46,
      overflow: "hidden",
    }}
  >
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage:
          "linear-gradient(rgba(125,223,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(125,223,255,0.035) 1px, transparent 1px)",
        backgroundSize: "52px 52px",
      }}
    />
    <div style={{ position: "relative", zIndex: 2 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 14,
            padding: "12px 17px",
            borderRadius: 999,
            border: "1px solid rgba(56,213,255,0.32)",
            background: "rgba(3,7,18,0.78)",
            color: CYAN,
            fontSize: 24,
            fontWeight: 950,
            textTransform: "uppercase",
            letterSpacing: 1.6,
          }}
        >
          <SignalMascot logoMode style={{ width: 44, height: 44 }} />
          {badge}
        </div>
        <div style={{ color: YELLOW, fontSize: 50, fontWeight: 950 }}>
          {beforeScore}
          {" TO "}
          {afterScore}
        </div>
      </div>

      <div style={{ fontSize: 72, lineHeight: 0.96, fontWeight: 950, letterSpacing: 0, marginTop: 28, maxWidth: 1080 }}>
        {title}
      </div>

      <div style={{ display: "flex", gap: 28, marginTop: 32 }}>
        <Panel label={leftLabel} tone="bad">
          <div style={{ marginTop: 32, display: "grid", gap: 18 }}>
            {["Helped with campaigns", "Team player", "Responsible for social"].map((line) => (
              <div
                key={line}
                style={{
                  padding: "18px 22px",
                  borderRadius: 18,
                  background: "rgba(15,23,42,0.72)",
                  border: "1px solid rgba(251,113,133,0.28)",
                  color: "#fecdd3",
                  fontSize: 31,
                  fontWeight: 900,
                }}
              >
                {line}
              </div>
            ))}
          </div>
          <Score value={beforeScore} tone="bad" />
        </Panel>
        <Panel label={rightLabel} tone="good">
          <div style={{ marginTop: 32, display: "flex", flexWrap: "wrap", gap: 14 }}>
            {keywords.slice(0, 5).map((keyword) => (
              <div
                key={keyword}
                style={{
                  padding: "18px 22px",
                  borderRadius: 18,
                  background: "rgba(34,197,94,0.14)",
                  border: "1px solid rgba(34,197,94,0.32)",
                  color: "#dcfce7",
                  fontSize: 31,
                  fontWeight: 950,
                }}
              >
                {keyword}
              </div>
            ))}
          </div>
          <div
            style={{
              position: "absolute",
              left: 30,
              bottom: 32,
              right: 220,
              color: "#bbf7d0",
              fontSize: 30,
              lineHeight: 1.14,
              fontWeight: 920,
            }}
          >
            Same experience. Clearer proof.
          </div>
          <Score value={afterScore} tone="good" />
        </Panel>
      </div>
    </div>
  </AbsoluteFill>
);
