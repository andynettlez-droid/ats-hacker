import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Audio } from "@remotion/media";
import { z } from "zod";
import { SignalMascot } from "./components/SignalMascot";

export const signalViralAdSchema = z.object({
  hook1: z.string(),
  hook2: z.string(),
  subline: z.string(),
  missing: z.array(z.string()),
  beforeScore: z.number(),
  afterScore: z.number(),
  cta: z.string(),
  avatarVideoUrl: z.string().optional(),
  musicSrc: z.string().optional(),
  musicVolume: z.number().min(0).max(1).optional(),
  voiceoverSrc: z.string().optional(),
  voiceoverVolume: z.number().min(0).max(1).optional(),
});

export type SignalViralAdProps = z.infer<typeof signalViralAdSchema>;

export const defaultSignalViralAdProps: SignalViralAdProps = {
  hook1: "Qualified, but hard to find?",
  hook2: "Check the match.",
  subline: "Recruiters search resumes by job-description language before deeper review.",
  missing: ["SQL", "workflow automation", "stakeholder reporting", "metrics"],
  beforeScore: 38,
  afterScore: 91,
  cta: "Check your score free. Link in bio",
  musicSrc: "audio/signal-pulse.wav",
  musicVolume: 0.32,
};

const FONT = '"Inter", "Helvetica Neue", Arial, sans-serif';
const BG = "#030712";
const CYAN = "#38d5ff";
const GREEN = "#34d399";
const RED = "#fb7185";
const TEXT = "#f8fafc";
const MUTED = "#94a3b8";

const fade = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

const Caption: React.FC<{ children: React.ReactNode; emphasis?: string }> = ({
  children,
  emphasis,
}) => (
  <div
    style={{
      position: "absolute",
      left: 70,
      right: 70,
      bottom: 110,
      zIndex: 80,
      padding: "26px 34px",
      borderRadius: 28,
      border: "1px solid rgba(56,213,255,0.22)",
      background: "rgba(3, 7, 18, 0.82)",
      boxShadow: "0 22px 70px rgba(0,0,0,0.46)",
      textAlign: "center",
    }}
  >
    <div
      style={{
        fontFamily: FONT,
        fontSize: 46,
        lineHeight: 1.16,
        fontWeight: 900,
        color: TEXT,
        letterSpacing: 0,
        textTransform: "uppercase",
      }}
    >
      {children}
      {emphasis ? (
        <span style={{ color: CYAN, textShadow: "0 0 20px rgba(56,213,255,0.72)" }}>
          {" "}
          {emphasis}
        </span>
      ) : null}
    </div>
  </div>
);

const ResumeCard: React.FC<{ optimized: boolean; progress: number }> = ({
  optimized,
  progress,
}) => {
  const wipe = interpolate(progress, [0, 1], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "relative",
        width: 790,
        minHeight: 1010,
        borderRadius: 32,
        padding: "48px 52px",
        background: "linear-gradient(180deg, rgba(15,23,42,0.92), rgba(2,6,23,0.88))",
        border: "1px solid rgba(125,223,255,0.22)",
        boxShadow: "0 34px 100px rgba(0,0,0,0.54), inset 0 1px 0 rgba(255,255,255,0.06)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(125,223,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(125,223,255,0.035) 1px, transparent 1px)",
          backgroundSize: "44px 44px",
        }}
      />
      {progress > 0.01 && progress < 0.99 ? (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: `${wipe}%`,
            width: 4,
            height: "100%",
            background: CYAN,
            boxShadow: "0 0 26px rgba(56,213,255,0.95)",
            zIndex: 3,
          }}
        />
      ) : null}
      <div style={{ position: "relative", zIndex: 5 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 18 }}>
          <div>
            <div
              style={{
                fontFamily: FONT,
                fontSize: 44,
                fontWeight: 950,
                color: TEXT,
                letterSpacing: 0,
              }}
            >
              ALEXANDER CHEN
            </div>
            <div
              style={{
                marginTop: 8,
                color: CYAN,
                fontFamily: FONT,
                fontSize: 22,
                fontWeight: 800,
                textTransform: "uppercase",
              }}
            >
              Senior Cloud Infrastructure Engineer
            </div>
          </div>
          <SignalMascot logoMode style={{ width: 72, height: 72 }} />
        </div>

        <div style={{ height: 1, background: "rgba(255,255,255,0.12)", margin: "34px 0" }} />

        <SectionTitle>Professional Summary</SectionTitle>
        <p style={bodyText}>
          Infrastructure engineer with 6+ years designing scalable systems, automation,
          and cloud delivery pipelines.
        </p>

        <div style={{ height: 34 }} />
        <SectionTitle>Experience</SectionTitle>
        <div style={{ ...bodyText, color: optimized ? TEXT : MUTED }}>
          {optimized ? (
            <>
              Automated weekly stakeholder reporting and reduced manual tracking time by{" "}
              <Highlight>35%</Highlight>.
            </>
          ) : (
            "Helped improve team workflow."
          )}
        </div>
        <div style={{ height: 16 }} />
        <div style={{ ...bodyText, color: optimized ? TEXT : MUTED }}>
          {optimized ? (
            <>
              Built <Highlight>SQL</Highlight> dashboards for leadership metrics and
              deployment visibility.
            </>
          ) : (
            "Worked on dashboards and deployments."
          )}
        </div>

        <div style={{ height: 38 }} />
        <SectionTitle>Role Language</SectionTitle>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
          {["SQL", "Automation", "Metrics", "Stakeholder Reporting"].map((skill) => (
            <span
              key={skill}
              style={{
                padding: "12px 16px",
                borderRadius: 14,
                border: `1px solid ${optimized ? "rgba(52,211,153,0.36)" : "rgba(251,113,133,0.28)"}`,
                background: optimized ? "rgba(52,211,153,0.1)" : "rgba(251,113,133,0.08)",
                color: optimized ? "#d1fae5" : "#fecdd3",
                fontFamily: FONT,
                fontSize: 20,
                fontWeight: 850,
                textTransform: "uppercase",
              }}
            >
              {skill}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

const SectionTitle: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      fontFamily: FONT,
      fontSize: 22,
      fontWeight: 900,
      color: "rgba(203,213,225,0.62)",
      textTransform: "uppercase",
      letterSpacing: 2,
      marginBottom: 14,
    }}
  >
    {children}
  </div>
);

const Highlight: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span style={{ color: CYAN, fontWeight: 950 }}>{children}</span>
);

const bodyText: React.CSSProperties = {
  fontFamily: FONT,
  fontSize: 29,
  lineHeight: 1.42,
  color: TEXT,
  fontWeight: 650,
};

const ScoreRing: React.FC<{ score: number }> = ({ score }) => {
  const circumference = 2 * Math.PI * 132;
  const stroke = score >= 80 ? GREEN : score >= 55 ? "#fbbf24" : RED;

  return (
    <div style={{ position: "relative", width: 320, height: 320 }}>
      <svg width="320" height="320" viewBox="0 0 320 320" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="160" cy="160" r="132" stroke="rgba(148,163,184,0.16)" strokeWidth="25" fill="none" />
        <circle
          cx="160"
          cy="160"
          r="132"
          stroke={stroke}
          strokeWidth="25"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - score / 100)}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: FONT,
        }}
      >
        <div style={{ color: stroke, fontSize: 88, fontWeight: 950, lineHeight: 1 }}>
          {score}
        </div>
        <div style={{ color: MUTED, fontSize: 24, fontWeight: 800, marginTop: 8 }}>
          EXAMPLE MATCH
        </div>
      </div>
    </div>
  );
};

export const SignalViralAd: React.FC<SignalViralAdProps> = ({
  hook1,
  hook2,
  subline,
  missing,
  beforeScore,
  afterScore,
  cta,
  musicSrc,
  musicVolume = 0.32,
  voiceoverSrc,
  voiceoverVolume = 1,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mascotSpring = spring({ frame: frame - 170, fps, config: { damping: 13, mass: 0.8 } });
  const score = Math.round(
    interpolate(frame, [670, 760], [beforeScore, afterScore], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );
  const optimizeProgress = interpolate(frame, [500, 650], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 20% 8%, rgba(56,213,255,0.18), transparent 430px), radial-gradient(circle at 82% 20%, rgba(37,99,235,0.2), transparent 480px), linear-gradient(180deg, #020617 0%, #030712 52%, #06101e 100%)",
        overflow: "hidden",
        fontFamily: FONT,
      }}
    >
      {musicSrc ? (
        <Audio
          src={staticFile(musicSrc)}
          volume={(audioFrame) =>
            interpolate(
              audioFrame,
              [0, fps, 28 * fps, 30 * fps],
              [0, musicVolume, musicVolume, 0],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              },
            )
          }
        />
      ) : null}
      {voiceoverSrc ? (
        <Audio src={staticFile(voiceoverSrc)} volume={voiceoverVolume} />
      ) : null}

      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(125,223,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(125,223,255,0.035) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
        }}
      />

      {frame < 135 ? (
        <AbsoluteFill
          style={{
            opacity: interpolate(frame, [0, 20, 105, 130], [0, 1, 1, 0]),
            alignItems: "center",
            justifyContent: "center",
            padding: 78,
            textAlign: "center",
          }}
        >
          <div style={{ color: TEXT, fontSize: 92, lineHeight: 1.04, fontWeight: 950 }}>
            {hook1}
          </div>
          <div
            style={{
              marginTop: 28,
              color: CYAN,
              fontSize: 76,
              lineHeight: 1.03,
              fontWeight: 950,
              textShadow: "0 0 28px rgba(56,213,255,0.7)",
            }}
          >
            {hook2}
          </div>
          <div style={{ marginTop: 42, color: "#cbd5e1", fontSize: 34, lineHeight: 1.32, fontWeight: 700 }}>
            {subline}
          </div>
        </AbsoluteFill>
      ) : null}

      {frame >= 135 && frame < 665 ? (
        <AbsoluteFill
          style={{
            opacity: fade(frame, 135, 165),
            alignItems: "center",
            justifyContent: "center",
            paddingTop: 10,
          }}
        >
          <div
            style={{
              transform: `translateX(${interpolate(frame, [170, 250], [0, -116], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })}px) scale(${interpolate(frame, [120, 210], [0.88, 0.78], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })})`,
            }}
          >
            <ResumeCard optimized={frame >= 500} progress={optimizeProgress} />
          </div>

          <div
            style={{
              position: "absolute",
              right: 66,
              top: 265,
              opacity: interpolate(frame, [165, 210], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              transform: `translateY(${interpolate(mascotSpring, [0, 1], [80, 0])}px)`,
              zIndex: 30,
            }}
          >
            <SignalMascot
              expression={frame > 430 ? "happy" : frame > 300 ? "focused" : "neutral"}
              style={{ width: 300, height: 300 }}
            />
          </div>

          {frame >= 250 && frame < 455 ? (
            <div
              style={{
                position: "absolute",
                left: 70,
                right: 70,
                top: 118,
                display: "flex",
                flexWrap: "wrap",
                gap: 16,
                justifyContent: "center",
                opacity: interpolate(frame, [250, 280, 430, 455], [0, 1, 1, 0]),
              }}
            >
              {missing.map((keyword, index) => (
                <div
                  key={keyword}
                  style={{
                    padding: "16px 20px",
                    borderRadius: 18,
                    border: "1px solid rgba(56,213,255,0.32)",
                    background: "rgba(8,18,36,0.78)",
                    color: "#dbeafe",
                    fontSize: 25,
                    fontWeight: 900,
                    textTransform: "uppercase",
                    transform: `translateY(${Math.sin((frame + index * 12) * 0.08) * 8}px)`,
                    boxShadow: "0 0 28px rgba(56,213,255,0.12)",
                  }}
                >
                  {keyword}
                </div>
              ))}
            </div>
          ) : null}

          {frame >= 455 && frame < 650 ? (
            <div
              style={{
                position: "absolute",
                right: 80,
                bottom: 430,
                width: 390,
                padding: 24,
                borderRadius: 26,
                border: "1px solid rgba(52,211,153,0.34)",
                background: "rgba(3,7,18,0.84)",
                boxShadow: "0 20px 60px rgba(0,0,0,0.42)",
                opacity: interpolate(frame, [455, 485, 630, 650], [0, 1, 1, 0]),
              }}
            >
              <div style={{ color: GREEN, fontSize: 19, fontWeight: 950, textTransform: "uppercase" }}>
                Signal rewrite
              </div>
              <div style={{ marginTop: 10, color: TEXT, fontSize: 33, lineHeight: 1.18, fontWeight: 950 }}>
                Same experience.
                <br />
                Clearer proof.
              </div>
            </div>
          ) : null}
        </AbsoluteFill>
      ) : null}

      {frame >= 665 && frame < 800 ? (
        <AbsoluteFill
          style={{
            opacity: interpolate(frame, [665, 695, 780, 800], [0, 1, 1, 0]),
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
          }}
        >
          <SignalMascot expression="happy" style={{ width: 240, height: 240, marginBottom: 22 }} />
          <div style={{ display: "flex", alignItems: "center", gap: 34 }}>
            <ScoreRing score={score} />
          </div>
          <div
            style={{
              marginTop: 30,
              color: TEXT,
              fontSize: 62,
              fontWeight: 950,
              opacity: interpolate(frame, [745, 765], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            No fake experience.
          </div>
          <div
            style={{
              marginTop: 10,
              color: CYAN,
              fontSize: 48,
              fontWeight: 950,
              opacity: interpolate(frame, [760, 780], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            Just a clearer job match.
          </div>
        </AbsoluteFill>
      ) : null}

      {frame >= 780 ? (
        <AbsoluteFill
          style={{
            opacity: fade(frame, 780, 820),
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            padding: 82,
          }}
        >
          <SignalMascot expression="happy" style={{ width: 320, height: 320 }} />
          <div style={{ marginTop: 38, color: TEXT, fontSize: 86, fontWeight: 950, lineHeight: 1.02 }}>
            Signal
          </div>
          <div style={{ color: CYAN, fontSize: 32, fontWeight: 900, textTransform: "uppercase", letterSpacing: 4 }}>
            by ATSHacker
          </div>
          <div
            style={{
              marginTop: 68,
              color: TEXT,
              fontSize: 50,
              lineHeight: 1.18,
              fontWeight: 950,
              padding: "30px 44px",
              borderRadius: 28,
              border: "1px solid rgba(56,213,255,0.38)",
              background: "rgba(8,18,36,0.78)",
              boxShadow: "0 0 54px rgba(56,213,255,0.16)",
            }}
          >
            {cta}
          </div>
        </AbsoluteFill>
      ) : null}

      {frame < 250 ? <Caption emphasis="hard to find">Your resume might be</Caption> : null}
      {frame >= 250 && frame < 455 ? <Caption emphasis="role language">Signal spots missing</Caption> : null}
      {frame >= 455 && frame < 650 ? <Caption emphasis="real proof">Then rewrites your</Caption> : null}
    </AbsoluteFill>
  );
};
