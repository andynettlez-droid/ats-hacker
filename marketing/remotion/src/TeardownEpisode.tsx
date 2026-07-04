import React from "react";
import { Audio } from "@remotion/media";
import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { SignalMascot } from "./components/SignalMascot";

export const teardownEpisodeSchema = z.object({
  title: z.string(),
  thesis: z.string(),
  cta: z.string(),
  sections: z.array(
    z.object({
      label: z.string(),
      script: z.string(),
      visual: z.string(),
    }),
  ),
  keywords: z.array(z.string()),
  weakBullets: z.array(z.string()),
  beforeBullet: z.string(),
  afterBullet: z.string(),
  beforeScore: z.number(),
  afterScore: z.number(),
  musicSrc: z.string().optional(),
  musicVolume: z.number().min(0).max(1).optional(),
  voiceoverSrc: z.string().optional(),
  voiceoverVolume: z.number().min(0).max(1).optional(),
  voiceoverSegments: z
    .array(
      z.object({
        src: z.string(),
        fromFrame: z.number(),
        volume: z.number().min(0).max(1).optional(),
        alignmentRef: z.string().nullable().optional(),
        captions: z
          .array(
            z.object({
              text: z.string(),
              startMs: z.number(),
              endMs: z.number(),
              timestampMs: z.number().nullable().optional(),
              confidence: z.number().nullable().optional(),
            }),
          )
          .optional(),
      }),
    )
    .optional(),
  durationInFrames: z.number().optional(),
});

export type TeardownEpisodeProps = z.infer<typeof teardownEpisodeSchema>;

export const defaultTeardownEpisodeProps: TeardownEpisodeProps = {
  title: "Your AI resume sounds professional. That might be the problem.",
  thesis:
    "A recruiter-style teardown showing why qualified experience can become invisible when the resume misses job-description language.",
  cta: "Paste the job description and check your free Signal score before you apply.",
  sections: [
    {
      label: "Cold open",
      script:
        "This resume looks professional, but it is missing the exact language the job description is asking for.",
      visual: "Open with resume and job description side by side, then reveal the low Signal score.",
    },
    {
      label: "The problem",
      script:
        "The job asks for HubSpot, CAC analysis, LinkedIn Ads, and lifecycle marketing. The resume says helped with campaigns.",
      visual: "Highlight job keywords and circle the vague bullet.",
    },
    {
      label: "Live fix",
      script:
        "The fix is not fake experience. The fix is translating real work into tools, scope, and measurable proof.",
      visual: "Rewrite the weak bullet into a role-specific proof bullet.",
    },
    {
      label: "Score reveal",
      script:
        "Same person. Same experience. Better signal. The example score moves from 34 to 92.",
      visual: "Animate 34/100 to 92/100 and show the free score CTA.",
    },
  ],
  keywords: ["HubSpot", "CAC", "LinkedIn Ads", "lifecycle marketing"],
  weakBullets: [
    "Responsible for social media.",
    "Helped with marketing campaigns.",
    "Worked with cross-functional teams.",
  ],
  beforeBullet: "Helped with marketing campaigns.",
  afterBullet:
    "Cut CAC by 32% through LinkedIn Ads audience segmentation and HubSpot lead scoring.",
  beforeScore: 34,
  afterScore: 92,
  musicSrc: "audio/signal-quiet-orbit.wav",
  musicVolume: 0.11,
  voiceoverVolume: 0.94,
};

const FONT = '"Inter", "Helvetica Neue", Arial, sans-serif';
const TEXT = "#f8fafc";
const MUTED = "#94a3b8";
const CYAN = "#38d5ff";
const GREEN = "#22c55e";
const RED = "#fb7185";
const YELLOW = "#facc15";

const fade = (frame: number, from: number, to: number) =>
  interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

const compact = (value: string, max = 168) =>
  value.length > max ? `${value.slice(0, max - 1).trim()}...` : value;

const ScoreCard: React.FC<{ score: number; label: string; tone: "low" | "high" }> = ({
  score,
  label,
  tone,
}) => (
  <div
    style={{
      width: 210,
      padding: "20px 22px",
      borderRadius: 24,
      border: `2px solid ${tone === "high" ? "rgba(34,197,94,0.42)" : "rgba(251,113,133,0.42)"}`,
      background: tone === "high" ? "rgba(34,197,94,0.10)" : "rgba(251,113,133,0.10)",
      boxShadow: `0 0 44px ${tone === "high" ? "rgba(34,197,94,0.16)" : "rgba(251,113,133,0.16)"}`,
      textAlign: "center",
    }}
  >
    <div style={{ color: tone === "high" ? "#bbf7d0" : "#fecdd3", fontSize: 15, fontWeight: 950, textTransform: "uppercase" }}>
      {label}
    </div>
    <div style={{ color: TEXT, fontSize: 64, lineHeight: 0.95, fontWeight: 950, marginTop: 8 }}>{score}</div>
    <div style={{ color: MUTED, fontSize: 16, fontWeight: 850, marginTop: 5 }}>/100</div>
  </div>
);

const ResumeBoard: React.FC<{
  weakBullets: string[];
  beforeBullet: string;
  afterBullet: string;
  showFix: boolean;
}> = ({ weakBullets, beforeBullet, afterBullet, showFix }) => (
  <div
    style={{
      width: 635,
      minHeight: 565,
      borderRadius: 26,
      background: "#fbfdff",
      color: "#0f172a",
      padding: "34px 38px",
      boxShadow: "0 34px 100px rgba(0,0,0,0.34)",
      border: "1px solid rgba(15,23,42,0.12)",
      position: "relative",
      overflow: "hidden",
    }}
  >
    <div style={{ fontSize: 31, fontWeight: 950, lineHeight: 1 }}>Avery Johnson</div>
    <div style={{ color: "#475569", fontSize: 17, fontWeight: 800, marginTop: 8 }}>Marketing Specialist Resume</div>
    <div style={{ height: 2, background: "#e2e8f0", margin: "24px 0" }} />
    <div style={{ color: "#64748b", fontSize: 14, fontWeight: 950, textTransform: "uppercase" }}>Experience</div>
    <div style={{ display: "grid", gap: 15, marginTop: 16 }}>
      {weakBullets.map((bullet) => {
        const isTarget = bullet === beforeBullet;
        return (
          <div
            key={bullet}
            style={{
              position: "relative",
              padding: "15px 18px 15px 30px",
              borderRadius: 16,
              background: showFix && isTarget ? "rgba(34,197,94,0.12)" : "rgba(241,245,249,0.88)",
              border: showFix && isTarget ? "2px solid rgba(34,197,94,0.42)" : "1px solid rgba(100,116,139,0.14)",
              fontSize: 22,
              lineHeight: 1.28,
              fontWeight: 780,
            }}
          >
            <span
              style={{
                position: "absolute",
                left: 12,
                top: 26,
                width: 7,
                height: 7,
                borderRadius: 99,
                background: showFix && isTarget ? "#16a34a" : "#475569",
              }}
            />
            {showFix && isTarget ? afterBullet : bullet}
            {!showFix && isTarget ? (
              <div
                style={{
                  position: "absolute",
                  inset: -7,
                  borderRadius: 20,
                  border: `5px solid ${RED}`,
                  transform: "rotate(-1.2deg)",
                }}
              />
            ) : null}
          </div>
        );
      })}
    </div>
    <div
      style={{
        position: "absolute",
        right: 26,
        bottom: 24,
        color: showFix ? "#16a34a" : RED,
        fontSize: 18,
        fontWeight: 950,
        textTransform: "uppercase",
      }}
    >
      {showFix ? "Real proof translated" : "Too vague"}
    </div>
  </div>
);

const JobBoard: React.FC<{ keywords: string[]; progress: number }> = ({ keywords, progress }) => (
  <div
    style={{
      width: 420,
      minHeight: 565,
      borderRadius: 26,
      border: "1px solid rgba(56,213,255,0.25)",
      background: "rgba(15,23,42,0.92)",
      padding: "32px 30px",
      color: TEXT,
      boxShadow: "0 24px 80px rgba(0,0,0,0.34), inset 0 0 34px rgba(56,213,255,0.04)",
    }}
  >
    <div style={{ color: CYAN, fontSize: 15, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.5 }}>
      Job description search terms
    </div>
    <div style={{ color: TEXT, fontSize: 34, lineHeight: 1.04, fontWeight: 950, marginTop: 12 }}>
      Demand Generation Manager
    </div>
    <div style={{ height: 1, background: "rgba(255,255,255,0.12)", margin: "25px 0" }} />
    <div style={{ display: "grid", gap: 14 }}>
      {keywords.map((keyword, index) => {
        const active = progress > index / Math.max(1, keywords.length);
        return (
          <div
            key={keyword}
            style={{
              padding: "15px 16px",
              borderRadius: 16,
              background: active ? "rgba(250,204,21,0.23)" : "rgba(255,255,255,0.05)",
              border: active ? "1px solid rgba(250,204,21,0.56)" : "1px solid rgba(148,163,184,0.13)",
              color: active ? "#fef9c3" : "#cbd5e1",
              fontSize: 22,
              fontWeight: 920,
            }}
          >
            {keyword}
          </div>
        );
      })}
    </div>
  </div>
);

const RecruiterNotes: React.FC<{ sectionLabel: string; showFix: boolean }> = ({ sectionLabel, showFix }) => {
  const notes = showFix
    ? ["Rewrite one bullet", "Use real tools", "Show measurable proof"]
    : ["Missing role language", "Vague bullet", "No searchable proof"];
  return (
    <div
      style={{
        position: "absolute",
        right: 74,
        top: 142,
        width: 560,
        minHeight: 430,
        borderRadius: 30,
        border: "1px solid rgba(56,213,255,0.23)",
        background: "rgba(3,7,18,0.72)",
        boxShadow: "0 26px 90px rgba(0,0,0,0.35), inset 0 0 36px rgba(56,213,255,0.045)",
        padding: "30px 34px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
        <SignalMascot expression={showFix ? "happy" : "focused"} style={{ width: 112, height: 112 }} />
        <div>
          <div style={{ color: CYAN, fontSize: 17, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.6 }}>
            Recruiter notes
          </div>
          <div style={{ color: TEXT, fontSize: 34, lineHeight: 1.02, fontWeight: 950, marginTop: 8 }}>
            {sectionLabel}
          </div>
        </div>
      </div>
      <div style={{ display: "grid", gap: 15, marginTop: 28 }}>
        {notes.map((note, index) => (
          <div
            key={note}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 15,
              padding: "17px 18px",
              borderRadius: 18,
              border: `1px solid ${showFix ? "rgba(34,197,94,0.28)" : "rgba(251,113,133,0.28)"}`,
              background: showFix ? "rgba(34,197,94,0.09)" : "rgba(251,113,133,0.08)",
              color: showFix ? "#bbf7d0" : "#fecdd3",
              fontSize: 27,
              lineHeight: 1.08,
              fontWeight: 920,
            }}
          >
            <span
              style={{
                display: "grid",
                placeItems: "center",
                width: 34,
                height: 34,
                borderRadius: 12,
                background: showFix ? "rgba(34,197,94,0.18)" : "rgba(251,113,133,0.16)",
                color: showFix ? GREEN : RED,
                fontSize: 21,
                fontWeight: 950,
              }}
            >
              {index + 1}
            </span>
            {note}
          </div>
        ))}
      </div>
    </div>
  );
};

export const TeardownEpisode: React.FC<TeardownEpisodeProps> = ({
  title,
  thesis,
  cta,
  sections,
  keywords,
  weakBullets,
  beforeBullet,
  afterBullet,
  beforeScore,
  afterScore,
  musicSrc,
  musicVolume = 0.11,
  voiceoverSrc,
  voiceoverVolume = 0.94,
  voiceoverSegments = [],
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const introEnd = 8 * fps;
  const outroStart = durationInFrames - 18 * fps;
  const usableFrames = Math.max(1, outroStart - introEnd);
  const sectionFrames = usableFrames / Math.max(1, sections.length);
  const sectionIndex = Math.min(
    Math.max(0, Math.floor((frame - introEnd) / sectionFrames)),
    Math.max(0, sections.length - 1),
  );
  const section = sections[sectionIndex] || sections[0] || defaultTeardownEpisodeProps.sections[0];
  const localFrame = frame - introEnd - sectionIndex * sectionFrames;
  const progress = fade(frame, introEnd + 20, outroStart - 40);
  const sectionPop = spring({ frame: localFrame, fps, config: { damping: 18, mass: 0.84 } });
  const showFix = progress > 0.58 || section.label.toLowerCase().includes("fix") || section.label.toLowerCase().includes("score");
  const score = Math.round(
    interpolate(progress, [0.62, 0.88], [beforeScore, afterScore], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );
  const introOpacity = fade(frame, 0, 24) * interpolate(frame, [introEnd - 20, introEnd], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const mainOpacity = fade(frame, introEnd - 12, introEnd + 18) * interpolate(frame, [outroStart - 20, outroStart + 10], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const outroOpacity = fade(frame, outroStart - 6, outroStart + 35);

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 14% 8%, rgba(56,213,255,0.18), transparent 32rem), radial-gradient(circle at 88% 16%, rgba(251,113,133,0.13), transparent 34rem), linear-gradient(180deg, #020617 0%, #030712 52%, #06101e 100%)",
        color: TEXT,
        fontFamily: FONT,
        overflow: "hidden",
      }}
    >
      {musicSrc ? (
        <Audio
          src={staticFile(musicSrc)}
          loop
          volume={(audioFrame) =>
            interpolate(audioFrame, [0, fps, durationInFrames - 2 * fps, durationInFrames], [0, musicVolume, musicVolume, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })
          }
        />
      ) : null}
      {voiceoverSrc ? <Audio src={staticFile(voiceoverSrc)} volume={voiceoverVolume} /> : null}
      {voiceoverSegments.map((segment) => (
        <Sequence key={`${segment.src}-${segment.fromFrame}`} from={segment.fromFrame} premountFor={30}>
          <Audio src={staticFile(segment.src)} volume={segment.volume ?? voiceoverVolume} />
        </Sequence>
      ))}

      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(125,223,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(125,223,255,0.035) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
          opacity: 0.65,
        }}
      />

      <AbsoluteFill style={{ opacity: introOpacity, alignItems: "center", justifyContent: "center", textAlign: "center", padding: 90 }}>
        <SignalMascot expression="focused" style={{ width: 220, height: 220, marginBottom: 34 }} />
        <div style={{ color: CYAN, fontSize: 26, fontWeight: 950, textTransform: "uppercase", letterSpacing: 3 }}>
          Recruiter reacts / resume teardown
        </div>
        <div style={{ color: TEXT, fontSize: 74, lineHeight: 0.98, fontWeight: 950, maxWidth: 1320, marginTop: 26 }}>
          {title}
        </div>
        <div style={{ color: "#cbd5e1", fontSize: 30, lineHeight: 1.38, fontWeight: 720, maxWidth: 1120, marginTop: 30 }}>
          {thesis}
        </div>
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: mainOpacity }}>
        <div style={{ position: "absolute", left: 58, right: 58, top: 42, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <SignalMascot logoMode style={{ width: 56, height: 56 }} />
            <div>
              <div style={{ color: TEXT, fontSize: 23, fontWeight: 950 }}>Signal by ATSHacker</div>
              <div style={{ color: MUTED, fontSize: 15, fontWeight: 820, marginTop: 3 }}>Daily resume teardown</div>
            </div>
          </div>
          <div style={{ color: CYAN, fontSize: 19, fontWeight: 950, textTransform: "uppercase", letterSpacing: 2 }}>
            {sectionIndex + 1}/{Math.max(1, sections.length)} {section.label}
          </div>
        </div>

        <div style={{ position: "absolute", left: 74, top: 132, display: "flex", gap: 34, alignItems: "flex-start" }}>
          <ResumeBoard weakBullets={weakBullets} beforeBullet={beforeBullet} afterBullet={afterBullet} showFix={showFix} />
          <JobBoard keywords={keywords} progress={fade(frame, introEnd + 30, introEnd + 130)} />
        </div>
        <RecruiterNotes sectionLabel={section.label} showFix={showFix} />

        <div
          style={{
            position: "absolute",
            right: 74,
            top: 742,
            display: "flex",
            gap: 18,
            alignItems: "center",
          }}
        >
          <ScoreCard score={beforeScore} label="Before" tone="low" />
          <div style={{ color: CYAN, fontSize: 44, fontWeight: 950 }}>to</div>
          <ScoreCard score={score} label="After" tone={score > beforeScore + 18 ? "high" : "low"} />
        </div>

        <div
          style={{
            position: "absolute",
            left: 74,
            right: 560,
            bottom: 58,
            padding: "26px 30px",
            borderRadius: 24,
            border: "1px solid rgba(56,213,255,0.22)",
            background: "rgba(3,7,18,0.84)",
            boxShadow: "0 24px 80px rgba(0,0,0,0.42), inset 0 0 28px rgba(56,213,255,0.04)",
            transform: `scale(${interpolate(sectionPop, [0, 1], [0.982, 1], { extrapolateRight: "clamp" })})`,
          }}
        >
          <div style={{ color: YELLOW, fontSize: 21, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.4 }}>
            {section.label}
          </div>
          <div style={{ color: TEXT, fontSize: 34, lineHeight: 1.18, fontWeight: 920, marginTop: 12 }}>
            {compact(section.script, 240)}
          </div>
          <div style={{ color: "#cbd5e1", fontSize: 22, lineHeight: 1.34, fontWeight: 760, marginTop: 16 }}>
            Visual: {compact(section.visual, 190)}
          </div>
        </div>
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: outroOpacity, alignItems: "center", justifyContent: "center", textAlign: "center", padding: 90 }}>
        <SignalMascot expression="happy" style={{ width: 245, height: 245, marginBottom: 26 }} />
        <div style={{ color: TEXT, fontSize: 86, lineHeight: 0.95, fontWeight: 950 }}>
          Same experience. Better signal.
        </div>
        <div style={{ color: CYAN, fontSize: 43, lineHeight: 1.17, fontWeight: 920, maxWidth: 1000, marginTop: 28 }}>
          {cta}
        </div>
      </AbsoluteFill>

      <div
        style={{
          position: "absolute",
          left: 58,
          right: 58,
          bottom: 28,
          height: 5,
          borderRadius: 99,
          background: "rgba(148,163,184,0.16)",
          overflow: "hidden",
          zIndex: 80,
        }}
      >
        <div
          style={{
            width: `${interpolate(frame, [0, durationInFrames], [0, 100], { extrapolateRight: "clamp" })}%`,
            height: "100%",
            background: "linear-gradient(90deg, #fb7185, #facc15, #22c55e, #38d5ff)",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
