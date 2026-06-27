import React from "react";
import { Audio } from "@remotion/media";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { SignalMascot } from "./components/SignalMascot";

export const signalBreakthroughAdSchema = z.object({
  hook1: z.string(),
  hook2: z.string(),
  subline: z.string(),
  missing: z.array(z.string()),
  beforeScore: z.number(),
  afterScore: z.number(),
  cta: z.string(),
  musicSrc: z.string().optional(),
  musicVolume: z.number().min(0).max(1).optional(),
});

export type SignalBreakthroughAdProps = z.infer<typeof signalBreakthroughAdSchema>;

export const defaultSignalBreakthroughAdProps: SignalBreakthroughAdProps = {
  hook1: "Qualified, but buried in search?",
  hook2: "Signal clears the path.",
  subline: "Match your real experience to the role language recruiters search.",
  missing: ["SQL", "workflow automation", "stakeholder reporting", "cloud delivery"],
  beforeScore: 38,
  afterScore: 91,
  cta: "Check your score free. Link in bio",
  musicSrc: "audio/signal-quiet-orbit.wav",
  musicVolume: 0.28,
};

const FONT = '"Inter", "Helvetica Neue", Arial, sans-serif';
const CYAN = "#38d5ff";
const GREEN = "#34d399";
const RED = "#fb7185";
const TEXT = "#f8fafc";
const MUTED = "#94a3b8";

const clampFade = (frame: number, from: number, to: number) =>
  interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

const exitFade = (frame: number, from: number, to: number) =>
  interpolate(frame, [from, to], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

const Caption: React.FC<{ children: React.ReactNode; emphasis?: string; top?: number }> = ({
  children,
  emphasis,
  top,
}) => (
  <div
    style={{
      position: "absolute",
      left: 64,
      right: 64,
      top,
      bottom: top == null ? 112 : undefined,
      zIndex: 80,
      padding: "25px 34px",
      borderRadius: 30,
      border: "1px solid rgba(56,213,255,0.24)",
      background: "rgba(3,7,18,0.84)",
      boxShadow: "0 24px 75px rgba(0,0,0,0.48), inset 0 0 28px rgba(56,213,255,0.055)",
      textAlign: "center",
    }}
  >
    <div
      style={{
        color: TEXT,
        fontFamily: FONT,
        fontSize: 47,
        fontWeight: 950,
        letterSpacing: 0,
        lineHeight: 1.12,
        textTransform: "uppercase",
      }}
    >
      {children}
      {emphasis ? (
        <span style={{ color: CYAN, textShadow: "0 0 24px rgba(56,213,255,0.72)" }}>
          {" "}
          {emphasis}
        </span>
      ) : null}
    </div>
  </div>
);

const ResumeDoc: React.FC<{ progress: number; compact?: boolean }> = ({ progress, compact = false }) => {
  const glow = interpolate(progress, [0, 1], [0.15, 0.9], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const lineColor = progress > 0.45 ? "rgba(209,250,229,0.92)" : "rgba(148,163,184,0.72)";

  return (
    <div
      style={{
        position: "relative",
        width: compact ? 415 : 540,
        minHeight: compact ? 560 : 760,
        borderRadius: compact ? 24 : 30,
        padding: compact ? 28 : 38,
        background: "linear-gradient(180deg, rgba(15,23,42,0.94), rgba(2,6,23,0.92))",
        border: `1px solid rgba(125,223,255,${0.22 + glow * 0.32})`,
        boxShadow: `0 34px 110px rgba(0,0,0,0.50), 0 0 ${32 + glow * 58}px rgba(56,213,255,${0.08 + glow * 0.16})`,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(125,223,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(125,223,255,0.035) 1px, transparent 1px)",
          backgroundSize: "42px 42px",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: `${interpolate(progress, [0.05, 0.95], [-12, 105], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          })}%`,
          width: 5,
          opacity: progress > 0.04 && progress < 0.98 ? 1 : 0,
          background: CYAN,
          boxShadow: "0 0 34px rgba(56,213,255,0.95)",
        }}
      />
      <div style={{ position: "relative", zIndex: 3 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 22 }}>
          <div>
            <div style={{ color: TEXT, fontSize: compact ? 31 : 40, fontWeight: 950, lineHeight: 1 }}>
              ALEXANDER CHEN
            </div>
            <div
              style={{
                color: CYAN,
                fontSize: compact ? 15 : 19,
                fontWeight: 850,
                marginTop: 8,
                textTransform: "uppercase",
              }}
            >
              Cloud Infrastructure Engineer
            </div>
          </div>
          <SignalMascot logoMode style={{ width: compact ? 56 : 68, height: compact ? 56 : 68 }} />
        </div>

        <div style={{ height: 1, background: "rgba(255,255,255,0.12)", margin: compact ? "24px 0" : "32px 0" }} />

        <DocSection title="Professional Summary" compact={compact}>
          Infrastructure engineer with 6+ years designing scalable systems, automation, and cloud delivery pipelines.
        </DocSection>

        <div style={{ height: compact ? 24 : 34 }} />
        <DocSection title="Experience" compact={compact}>
          <span style={{ color: lineColor }}>
            {progress > 0.45 ? "Automated weekly stakeholder reporting and reduced manual tracking time by 35%." : "Helped improve team workflow."}
          </span>
          <br />
          <span style={{ color: lineColor }}>
            {progress > 0.72 ? "Built SQL dashboards for leadership metrics and deployment visibility." : "Worked on dashboards and deployments."}
          </span>
        </DocSection>

        <div style={{ height: compact ? 24 : 34 }} />
        <div style={{ color: MUTED, fontSize: compact ? 13 : 16, fontWeight: 900, textTransform: "uppercase" }}>
          Role Language
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 12 }}>
          {["SQL", "Automation", "Metrics", "Stakeholders"].map((skill, index) => {
            const active = progress > 0.35 + index * 0.12;
            return (
              <span
                key={skill}
                style={{
                  padding: compact ? "9px 11px" : "11px 15px",
                  borderRadius: 13,
                  border: `1px solid ${active ? "rgba(52,211,153,0.36)" : "rgba(251,113,133,0.24)"}`,
                  background: active ? "rgba(52,211,153,0.12)" : "rgba(251,113,133,0.07)",
                  color: active ? "#d1fae5" : "#fecdd3",
                  fontSize: compact ? 13 : 17,
                  fontWeight: 850,
                  textTransform: "uppercase",
                }}
              >
                {skill}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const DocSection: React.FC<{ title: string; compact: boolean; children: React.ReactNode }> = ({
  title,
  compact,
  children,
}) => (
  <div>
    <div style={{ color: MUTED, fontSize: compact ? 13 : 16, fontWeight: 900, textTransform: "uppercase" }}>
      {title}
    </div>
    <div
      style={{
        color: "#dbeafe",
        fontSize: compact ? 19 : 25,
        lineHeight: 1.42,
        fontWeight: 650,
        marginTop: 12,
      }}
    >
      {children}
    </div>
  </div>
);

const Barrier: React.FC<{
  label: string;
  x: number;
  broken: boolean;
  crack: number;
}> = ({ label, x, broken, crack }) => {
  const shift = broken ? 130 + crack * 70 : 0;
  const opacity = broken ? interpolate(crack, [0, 1], [1, 0.18], { extrapolateRight: "clamp" }) : 1;
  const shards = Array.from({ length: 9 }).map((_, i) => {
    const angle = -1.15 + i * 0.29;
    const dist = interpolate(crack, [0, 1], [0, 120 + i * 9], { extrapolateRight: "clamp" });
    return {
      x: Math.cos(angle) * dist,
      y: Math.sin(angle) * dist + (i - 4) * 8,
      rotate: (i - 4) * 18 + crack * 80,
    };
  });

  return (
    <div style={{ position: "absolute", left: x, top: 430, width: 128, height: 590, zIndex: 25, opacity }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `translateX(${shift}px) rotate(${broken ? 10 + crack * 9 : 0}deg)`,
          borderRadius: 30,
          border: `2px solid ${broken ? "rgba(52,211,153,0.45)" : "rgba(251,113,133,0.52)"}`,
          background:
            "linear-gradient(180deg, rgba(15,23,42,0.72), rgba(3,7,18,0.82)), radial-gradient(circle at 50% 20%, rgba(56,213,255,0.12), transparent 12rem)",
          boxShadow: `0 0 ${broken ? 22 : 48}px ${broken ? "rgba(52,211,153,0.16)" : "rgba(251,113,133,0.23)"}, inset 0 0 34px rgba(56,213,255,0.055)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 38,
          left: "50%",
          transform: "translateX(-50%) rotate(90deg)",
          color: broken ? GREEN : RED,
          width: 420,
          textAlign: "center",
          fontSize: 25,
          fontWeight: 950,
          letterSpacing: 2,
          textTransform: "uppercase",
        }}
      >
        {label}
      </div>
      {broken
        ? shards.map((shard, i) => (
            <div
              key={i}
              style={{
                position: "absolute",
                left: 64 + shard.x,
                top: 290 + shard.y,
                width: 16 + (i % 3) * 9,
                height: 5,
                borderRadius: 99,
                background: "rgba(125,223,255,0.78)",
                boxShadow: "0 0 20px rgba(56,213,255,0.75)",
                transform: `rotate(${shard.rotate}deg)`,
                opacity: interpolate(crack, [0, 0.82, 1], [0, 1, 0], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            />
          ))
        : null}
    </div>
  );
};

const ScoreRing: React.FC<{ score: number; progress: number; startScore?: number }> = ({
  score,
  progress,
  startScore = 0,
}) => {
  const radius = 120;
  const circumference = 2 * Math.PI * radius;
  const displayScore = interpolate(progress, [0, 1], [startScore, score], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const strokeOffset = circumference - circumference * (displayScore / 100);

  return (
    <div style={{ position: "relative", width: 300, height: 300 }}>
      <svg width="300" height="300" viewBox="0 0 300 300" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="150" cy="150" r={radius} stroke="rgba(148,163,184,0.18)" strokeWidth="24" fill="none" />
        <circle
          cx="150"
          cy="150"
          r={radius}
          stroke={displayScore >= 80 ? GREEN : "#fbbf24"}
          strokeWidth="24"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeOffset}
          fill="none"
          style={{
            filter: `drop-shadow(0 0 18px ${
              displayScore >= 80 ? "rgba(52,211,153,0.72)" : "rgba(251,191,36,0.62)"
            })`,
          }}
        />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", textAlign: "center" }}>
        <div>
          <div style={{ color: TEXT, fontSize: 78, fontWeight: 950, lineHeight: 0.95 }}>{Math.round(displayScore)}</div>
          <div style={{ color: CYAN, fontSize: 18, fontWeight: 950, textTransform: "uppercase", marginTop: 10 }}>
            Example match
          </div>
        </div>
      </div>
    </div>
  );
};

const HiringManager: React.FC<{ reveal: number }> = ({ reveal }) => (
  <div
    style={{
      position: "relative",
      width: 360,
      height: 600,
      borderRadius: 34,
      border: "1px solid rgba(56,213,255,0.22)",
      background:
        "linear-gradient(180deg, rgba(15,23,42,0.82), rgba(2,6,23,0.92)), radial-gradient(circle at 50% 24%, rgba(255,255,255,0.18), transparent 7rem)",
      boxShadow: "0 28px 90px rgba(0,0,0,0.42), inset 0 0 50px rgba(56,213,255,0.04)",
      overflow: "hidden",
      opacity: reveal,
    }}
  >
    <div
      style={{
        position: "absolute",
        top: 92,
        left: "50%",
        width: 116,
        height: 116,
        borderRadius: "50%",
        transform: "translateX(-50%)",
        background: "radial-gradient(circle at 50% 35%, rgba(255,255,255,0.24), rgba(148,163,184,0.10) 62%, transparent 66%)",
      }}
    />
    <div
      style={{
        position: "absolute",
        left: 76,
        right: 76,
        bottom: 100,
        height: 260,
        borderRadius: "95px 95px 34px 34px",
        background: "radial-gradient(ellipse at 50% 20%, rgba(255,255,255,0.16), rgba(148,163,184,0.08) 64%, transparent 66%)",
      }}
    />
    <div
      style={{
        position: "absolute",
        left: 30,
        right: 30,
        bottom: 34,
        padding: "15px 18px",
        borderRadius: 20,
        border: "1px solid rgba(52,211,153,0.24)",
        background: "rgba(3,7,18,0.72)",
        color: "#d1fae5",
        fontSize: 19,
        fontWeight: 850,
        textAlign: "center",
      }}
    >
      Hiring manager computer
    </div>
    <div
      style={{
        position: "absolute",
        left: 38,
        right: 38,
        bottom: 128,
        height: 190,
        borderRadius: 24,
        border: "1px solid rgba(56,213,255,0.34)",
        background:
          "linear-gradient(180deg, rgba(2,6,23,0.96), rgba(15,23,42,0.88)), radial-gradient(circle at 50% 8%, rgba(56,213,255,0.22), transparent 10rem)",
        boxShadow: `0 0 ${24 + reveal * 42}px rgba(56,213,255,${0.10 + reveal * 0.18}), inset 0 0 34px rgba(56,213,255,0.08)`,
      }}
    >
      <div
        style={{
          position: "absolute",
          left: 22,
          top: 18,
          color: CYAN,
          fontSize: 13,
          fontWeight: 950,
          letterSpacing: 1.6,
          textTransform: "uppercase",
        }}
      >
        Recruiter screen
      </div>
      <div
        style={{
          position: "absolute",
          left: 24,
          right: 24,
          top: 56,
          bottom: 20,
          borderRadius: 18,
          border: "1px solid rgba(52,211,153,0.24)",
          background: "rgba(52,211,153,0.08)",
          overflow: "hidden",
        }}
      >
        {[0, 1, 2, 3].map((line) => (
          <div
            key={line}
            style={{
              position: "absolute",
              left: 18,
              right: 18 + line * 18,
              top: 18 + line * 22,
              height: 7,
              borderRadius: 99,
              background: line === 0 ? "rgba(248,250,252,0.85)" : "rgba(125,223,255,0.52)",
              boxShadow: line === 0 ? "0 0 14px rgba(255,255,255,0.18)" : undefined,
            }}
          />
        ))}
        <div
          style={{
            position: "absolute",
            right: 18,
            bottom: 14,
            color: "#d1fae5",
            fontSize: 15,
            fontWeight: 900,
          }}
        >
          Review-ready
        </div>
      </div>
    </div>
  </div>
);

export const SignalBreakthroughAd: React.FC<SignalBreakthroughAdProps> = ({
  hook1,
  hook2,
  subline,
  missing,
  beforeScore,
  afterScore,
  cta,
  musicSrc,
  musicVolume = 0.28,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sec = frame / fps;

  const introOpacity = clampFade(frame, 0, 24) * exitFade(frame, 112, 142);
  const stageOpacity = clampFade(frame, 118, 150) * exitFade(frame, 655, 690);
  const scoreOpacity = clampFade(frame, 648, 690) * exitFade(frame, 778, 805);
  const ctaOpacity = clampFade(frame, 790, 835);

  const resumeProgress = clampFade(frame, 345, 610);
  const travel = clampFade(frame, 470, 640);
  const managerReveal = clampFade(frame, 515, 590);
  const mascotDrive = spring({ frame: frame - 132, fps, config: { damping: 16, mass: 0.82 } });
  const mascotX = interpolate(frame, [135, 330], [-350, 246], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const mascotY = Math.sin(frame * 0.055) * 18;

  const cracks = [183, 246, 309].map((hitFrame) =>
    interpolate(frame, [hitFrame, hitFrame + 28], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    }),
  );

  const resumeX = interpolate(travel, [0, 1], [-245, 178], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const resumeScale = interpolate(travel, [0, 1], [0.93, 0.62], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const beamOpacity = interpolate(travel, [0.06, 0.5, 1], [0, 0.82, 0.18], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scoreProgress = clampFade(frame, 680, 755);

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 18% 8%, rgba(56,213,255,0.18), transparent 31rem), radial-gradient(circle at 86% 18%, rgba(37,99,235,0.20), transparent 34rem), linear-gradient(180deg, #020617 0%, #030712 50%, #06101e 100%)",
        fontFamily: FONT,
        overflow: "hidden",
      }}
    >
      {musicSrc ? (
        <Audio
          src={staticFile(musicSrc)}
          volume={(audioFrame) =>
            interpolate(audioFrame, [0, fps, 28 * fps, 30 * fps], [0, musicVolume, musicVolume, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })
          }
        />
      ) : null}

      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(125,223,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(125,223,255,0.035) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
          opacity: 0.75,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.10,
          background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.03) 0 1px, transparent 1px 5px)",
        }}
      />

      <AbsoluteFill style={{ opacity: introOpacity, alignItems: "center", justifyContent: "center", textAlign: "center", padding: 76 }}>
        <SignalMascot expression="focused" style={{ width: 250, height: 250, marginBottom: 40 }} />
        <div style={{ color: TEXT, fontSize: 78, lineHeight: 0.98, fontWeight: 950, letterSpacing: 0, maxWidth: 900 }}>
          {hook1}
        </div>
        <div style={{ color: CYAN, fontSize: 56, lineHeight: 1.05, fontWeight: 950, marginTop: 20 }}>{hook2}</div>
        <div style={{ color: "#cbd5e1", fontSize: 31, lineHeight: 1.36, fontWeight: 700, marginTop: 30, maxWidth: 780 }}>
          {subline}
        </div>
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: stageOpacity }}>
        <div style={{ position: "absolute", left: 66, right: 66, top: 82, display: "flex", justifyContent: "space-between" }}>
          <div style={{ color: CYAN, fontSize: 18, fontWeight: 950, textTransform: "uppercase", letterSpacing: 2 }}>
            Signal pathway // live
          </div>
          <div style={{ color: MUTED, fontSize: 18, fontWeight: 800 }}>Company filters / aligned proof / hiring manager screen</div>
        </div>

        {missing.slice(0, 4).map((keyword, index) => (
          <div
            key={keyword}
            style={{
              position: "absolute",
              top: 178 + index * 58,
              left: 62 + index * 26,
              padding: "13px 17px",
              borderRadius: 18,
              border: "1px solid rgba(251,113,133,0.28)",
              background: "rgba(251,113,133,0.065)",
              color: "#fecdd3",
              fontSize: 21,
              fontWeight: 900,
              textTransform: "uppercase",
              opacity: exitFade(frame, 330 + index * 15, 370 + index * 15),
            }}
          >
            Missing: {keyword}
          </div>
        ))}

        <Barrier label="company filters" x={450} broken={cracks[0] > 0.04} crack={cracks[0]} />
        <Barrier label="role language" x={570} broken={cracks[1] > 0.04} crack={cracks[1]} />
        <Barrier label="proof gaps" x={690} broken={cracks[2] > 0.04} crack={cracks[2]} />

        <div
          style={{
            position: "absolute",
            left: `calc(50% + ${mascotX}px)`,
            top: 744 + mascotY,
            transform: `translate(-50%, -50%) scale(${interpolate(mascotDrive, [0, 1], [0.76, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })})`,
            zIndex: 44,
          }}
        >
          <SignalMascot expression={frame > 310 ? "happy" : "focused"} style={{ width: 260, height: 260 }} />
        </div>

        <div
          style={{
            position: "absolute",
            left: `calc(50% + ${resumeX}px)`,
            top: interpolate(travel, [0, 1], [1105, 770]),
            transform: `translate(-50%, -50%) scale(${resumeScale}) rotate(${interpolate(travel, [0, 1], [-4, 1])}deg)`,
            zIndex: 35,
            opacity: frame > 212 ? 1 : 0,
          }}
        >
          <ResumeDoc progress={resumeProgress} />
        </div>

        <div
          style={{
            position: "absolute",
            left: 300,
            right: 294,
            top: 775,
            height: 4,
            background: `linear-gradient(90deg, transparent, rgba(56,213,255,${beamOpacity}), rgba(52,211,153,${beamOpacity}), transparent)`,
            boxShadow: `0 0 42px rgba(56,213,255,${beamOpacity})`,
            transform: `rotate(${interpolate(travel, [0, 1], [-8, -2])}deg)`,
            opacity: beamOpacity,
            zIndex: 20,
          }}
        />

        <div style={{ position: "absolute", right: 82, top: 515, zIndex: 18, transform: "scale(0.92)" }}>
          <HiringManager reveal={managerReveal} />
        </div>

        {frame >= 145 && frame < 345 ? <Caption emphasis="company filters">Signal breaks through</Caption> : null}
        {frame >= 345 && frame < 515 ? <Caption emphasis="real proof">Then rebuilds your</Caption> : null}
        {frame >= 515 && frame < 665 ? <Caption emphasis="the hiring manager screen">And phases it into</Caption> : null}
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: scoreOpacity, alignItems: "center", justifyContent: "center", textAlign: "center" }}>
        <SignalMascot expression="happy" style={{ width: 210, height: 210, marginBottom: 18 }} />
        <div style={{ display: "flex", alignItems: "center", gap: 48 }}>
          <div style={{ opacity: exitFade(frame, 705, 758), transform: "scale(0.86)" }}>
            <ScoreRing score={beforeScore} progress={1} />
          </div>
          <div style={{ color: CYAN, fontSize: 62, fontWeight: 950 }}>to</div>
          <ScoreRing score={afterScore} progress={scoreProgress} startScore={beforeScore} />
        </div>
        <div style={{ color: TEXT, fontSize: 62, fontWeight: 950, marginTop: 30 }}>No fake experience.</div>
        <div style={{ color: CYAN, fontSize: 45, fontWeight: 950, marginTop: 10 }}>Just a clearer job match.</div>
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: ctaOpacity, alignItems: "center", justifyContent: "center", textAlign: "center", padding: 78 }}>
        <SignalMascot expression="happy" style={{ width: 300, height: 300 }} />
        <div style={{ color: TEXT, fontSize: 86, fontWeight: 950, marginTop: 34, lineHeight: 1 }}>Signal</div>
        <div style={{ color: CYAN, fontSize: 31, fontWeight: 950, letterSpacing: 4, textTransform: "uppercase" }}>by ATSHacker</div>
        <div
          style={{
            marginTop: 70,
            color: TEXT,
            fontSize: 51,
            lineHeight: 1.18,
            fontWeight: 950,
            padding: "31px 45px",
            borderRadius: 30,
            border: "1px solid rgba(56,213,255,0.38)",
            background: "rgba(8,18,36,0.80)",
            boxShadow: "0 0 62px rgba(56,213,255,0.18), inset 0 0 34px rgba(56,213,255,0.05)",
          }}
        >
          {cta}
        </div>
        <div style={{ color: MUTED, fontSize: 22, fontWeight: 800, marginTop: 26 }}>
          Resume + cover letter matching, one application at a time.
        </div>
      </AbsoluteFill>

      <div
        style={{
          position: "absolute",
          left: 52,
          right: 52,
          bottom: 42,
          height: 4,
          borderRadius: 99,
          background: "rgba(148,163,184,0.14)",
          overflow: "hidden",
          zIndex: 100,
        }}
      >
        <div
          style={{
            width: `${interpolate(sec, [0, 30], [0, 100], { extrapolateRight: "clamp" })}%`,
            height: "100%",
            background: "linear-gradient(90deg, #2563eb, #38d5ff, #34d399)",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
