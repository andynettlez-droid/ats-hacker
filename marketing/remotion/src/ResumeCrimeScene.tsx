import React from "react";
import { Audio } from "@remotion/media";
import {
  AbsoluteFill,
  Easing,
  Sequence,
  Video,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { SignalMascot } from "./components/SignalMascot";

export const resumeCrimeSceneSchema = z.object({
  hook: z.string(),
  subhook: z.string(),
  creativeFormat: z
    .enum(["resumeCrimeScene", "aiResumeRoast", "atsMythLab", "jobSearchTest", "oneBulletFix", "mascotRescue"])
    .optional(),
  visualStyle: z.enum(["neon", "comic", "terminal", "stickyNote", "highlighter"]).optional(),
  pace: z.enum(["fast", "balanced", "slowBurn"]).optional(),
  seriesLabel: z.string().optional(),
  signalLines: z
    .object({
      hook: z.string().optional(),
      problem: z.string().optional(),
      teardown: z.string().optional(),
      fix: z.string().optional(),
      cta: z.string().optional(),
    })
    .optional(),
  punchline: z.string().optional(),
  problemPunchline: z.string().optional(),
  markedLabel: z.string().optional(),
  teardownText: z.string().optional(),
  teardownEmphasis: z.string().optional(),
  teardownPunchline: z.string().optional(),
  teardownIssues: z.array(z.string()).optional(),
  fixText: z.string().optional(),
  fixEmphasis: z.string().optional(),
  fixPunchline: z.string().optional(),
  resumeTitle: z.string(),
  jobTitle: z.string(),
  jobKeywords: z.array(z.string()),
  weakBullets: z.array(z.string()),
  beforeBullet: z.string(),
  afterBullet: z.string(),
  beforeScore: z.number(),
  afterScore: z.number(),
  cta: z.string(),
  musicSrc: z.string().optional(),
  musicVolume: z.number().min(0).max(1).optional(),
  voiceoverSrc: z.string().optional(),
  voiceoverVolume: z.number().min(0).max(1).optional(),
  sfxSrc: z.string().optional(),
  sfxVolume: z.number().min(0).max(1).optional(),
  avatarVideoUrl: z.string().optional(),
  avatarLabel: z.string().optional(),
});

export type ResumeCrimeSceneProps = z.infer<typeof resumeCrimeSceneSchema>;

export const defaultResumeCrimeSceneProps: ResumeCrimeSceneProps = {
  hook: "This resume got a 34/100.",
  subhook: "The person was actually qualified.",
  creativeFormat: "resumeCrimeScene",
  visualStyle: "neon",
  pace: "balanced",
  seriesLabel: "Recruiter reacts",
  signalLines: {
    hook: "I found the missing signal.",
    problem: "This is polished fog.",
    teardown: "Roast the bullet, not the person.",
    fix: "There it is.",
    cta: "Check before you send.",
  },
  punchline: "Qualified, but invisible.",
  problemPunchline: "Recruiters search for proof, not vibes.",
  markedLabel: "Too vague",
  teardownText: "Not fake. Just",
  teardownEmphasis: "too vague.",
  teardownPunchline: "This is the part costing you interviews.",
  teardownIssues: ["No role language", "No tools", "No measurable proof"],
  fixText: "Same experience.",
  fixEmphasis: "Better signal.",
  fixPunchline: "No fake experience. Just clearer evidence.",
  resumeTitle: "Marketing Specialist Resume",
  jobTitle: "Demand Generation Manager",
  jobKeywords: ["Demand Gen", "LinkedIn Ads", "HubSpot", "CAC analysis"],
  weakBullets: ["Responsible for social media.", "Helped with marketing campaigns.", "Worked with the team."],
  beforeBullet: "Helped with marketing campaigns.",
  afterBullet: "Cut CAC by 32% through LinkedIn Ads audience segmentation and HubSpot lead scoring.",
  beforeScore: 34,
  afterScore: 92,
  cta: "Paste the job description. Check your free Signal score before you apply.",
  musicSrc: "audio/signal-quiet-orbit.wav",
  musicVolume: 0.16,
  voiceoverVolume: 0.94,
  sfxVolume: 0.06,
  avatarLabel: "Recruiter review",
};

const FONT = '"Inter", "Helvetica Neue", Arial, sans-serif';
const TEXT = "#f8fafc";
const MUTED = "#94a3b8";
const CYAN = "#38d5ff";
const GREEN = "#16a34a";
const RED = "#dc2626";
const YELLOW = "#facc15";

const VISUAL_STYLES = {
  neon: {
    background:
      "radial-gradient(circle at 16% 10%, rgba(220,38,38,0.16), transparent 30rem), radial-gradient(circle at 84% 18%, rgba(56,213,255,0.18), transparent 34rem), linear-gradient(180deg, #020617 0%, #030712 48%, #06101e 100%)",
    accent: CYAN,
    warning: RED,
    texture: "grid",
  },
  comic: {
    background:
      "radial-gradient(circle at 18% 12%, rgba(250,204,21,0.18), transparent 28rem), radial-gradient(circle at 82% 18%, rgba(244,63,94,0.16), transparent 32rem), linear-gradient(180deg, #111827 0%, #020617 100%)",
    accent: "#facc15",
    warning: "#f43f5e",
    texture: "dots",
  },
  terminal: {
    background:
      "radial-gradient(circle at 16% 18%, rgba(34,197,94,0.14), transparent 28rem), radial-gradient(circle at 84% 14%, rgba(56,213,255,0.13), transparent 30rem), linear-gradient(180deg, #020617 0%, #03120d 100%)",
    accent: "#22c55e",
    warning: "#fb7185",
    texture: "scanlines",
  },
  stickyNote: {
    background:
      "radial-gradient(circle at 18% 16%, rgba(250,204,21,0.18), transparent 28rem), radial-gradient(circle at 80% 10%, rgba(56,213,255,0.12), transparent 30rem), linear-gradient(180deg, #0f172a 0%, #111827 100%)",
    accent: "#fef08a",
    warning: "#fb7185",
    texture: "paper",
  },
  highlighter: {
    background:
      "radial-gradient(circle at 14% 12%, rgba(45,212,191,0.17), transparent 28rem), radial-gradient(circle at 86% 18%, rgba(250,204,21,0.16), transparent 32rem), linear-gradient(180deg, #07111f 0%, #020617 100%)",
    accent: "#2dd4bf",
    warning: "#f97316",
    texture: "highlighter",
  },
} as const;

const PACE = {
  fast: {
    hook: [0, 82],
    problem: [88, 300],
    teardown: [306, 594],
    fix: [600, 990],
    cta: [996, 1350],
  },
  balanced: {
    hook: [0, 108],
    problem: [114, 348],
    teardown: [354, 696],
    fix: [702, 1020],
    cta: [1026, 1350],
  },
  slowBurn: {
    hook: [0, 132],
    problem: [138, 390],
    teardown: [396, 738],
    fix: [744, 1038],
    cta: [1044, 1350],
  },
} as const;

const fadeIn = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

const fadeOut = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

const stageOpacity = (frame: number, start: number, end: number) =>
  fadeIn(frame, start, start + 18) * fadeOut(frame, end - 22, end);

const StyleTexture: React.FC<{ styleName: keyof typeof VISUAL_STYLES }> = ({ styleName }) => {
  const texture = VISUAL_STYLES[styleName].texture;
  if (texture === "dots") {
    return (
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.16,
          backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.28) 1px, transparent 1.5px)",
          backgroundSize: "18px 18px",
        }}
      />
    );
  }
  if (texture === "scanlines") {
    return (
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.18,
          background: "repeating-linear-gradient(0deg, rgba(34,197,94,0.08) 0 2px, transparent 2px 7px)",
        }}
      />
    );
  }
  if (texture === "paper") {
    return (
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.08,
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.18) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.12) 1px, transparent 1px)",
          backgroundSize: "42px 42px",
        }}
      />
    );
  }
  if (texture === "highlighter") {
    return (
      <>
        <div style={{ position: "absolute", left: 46, top: 176, width: 440, height: 44, background: "rgba(250,204,21,0.18)", transform: "rotate(-3deg)" }} />
        <div style={{ position: "absolute", right: 70, top: 680, width: 360, height: 40, background: "rgba(45,212,191,0.16)", transform: "rotate(2deg)" }} />
      </>
    );
  }
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage:
          "linear-gradient(rgba(125,223,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(125,223,255,0.035) 1px, transparent 1px)",
        backgroundSize: "54px 54px",
        opacity: 0.62,
      }}
    />
  );
};

const ScoreBadge: React.FC<{ score: number; tone: "bad" | "good"; label?: string }> = ({ score, tone, label }) => (
  <div
    style={{
      minWidth: 164,
      padding: "15px 18px",
      borderRadius: 22,
      border: `2px solid ${tone === "good" ? "rgba(22,163,74,0.42)" : "rgba(220,38,38,0.42)"}`,
      background: tone === "good" ? "rgba(22,163,74,0.10)" : "rgba(220,38,38,0.10)",
      boxShadow: `0 0 34px ${tone === "good" ? "rgba(22,163,74,0.18)" : "rgba(220,38,38,0.18)"}`,
      textAlign: "center",
    }}
  >
    <div style={{ color: tone === "good" ? "#bbf7d0" : "#fecaca", fontSize: 14, fontWeight: 950, textTransform: "uppercase" }}>
      {label || "Signal score"}
    </div>
    <div style={{ color: TEXT, fontSize: 54, fontWeight: 950, lineHeight: 1, marginTop: 5 }}>{score}/100</div>
  </div>
);

const ResumeSheet: React.FC<{
  title: string;
  bullets: string[];
  marked?: boolean;
  rewritten?: boolean;
  beforeBullet: string;
  afterBullet: string;
  markedLabel?: string;
}> = ({ title, bullets, marked, rewritten, beforeBullet, afterBullet, markedLabel = "Too vague" }) => (
  <div
    style={{
      width: 612,
      minHeight: 785,
      borderRadius: 26,
      background: "#fbfdff",
      color: "#0f172a",
      padding: "38px 42px",
      boxShadow: "0 36px 110px rgba(0,0,0,0.42)",
      border: "1px solid rgba(15,23,42,0.10)",
      position: "relative",
      overflow: "hidden",
    }}
  >
    <div style={{ fontSize: 32, fontWeight: 950, lineHeight: 1.04 }}>Avery Johnson</div>
    <div style={{ marginTop: 8, fontSize: 18, color: "#475569", fontWeight: 800 }}>{title}</div>
    <div style={{ height: 2, background: "#e2e8f0", margin: "28px 0" }} />
    <div style={{ color: "#64748b", fontSize: 15, fontWeight: 950, textTransform: "uppercase" }}>Experience</div>
    <div style={{ display: "grid", gap: 18, marginTop: 18 }}>
      {bullets.map((bullet, index) => {
        const isTarget = bullet === beforeBullet;
        return (
          <div
            key={bullet}
            style={{
              position: "relative",
              padding: "13px 14px 13px 28px",
              borderRadius: 14,
              background: rewritten && isTarget ? "rgba(22,163,74,0.10)" : "rgba(241,245,249,0.74)",
              border: rewritten && isTarget ? "2px solid rgba(22,163,74,0.42)" : "1px solid rgba(100,116,139,0.14)",
              fontSize: 23,
              lineHeight: 1.32,
              fontWeight: 750,
            }}
          >
            <span
              style={{
                position: "absolute",
                left: 11,
                top: 24,
                width: 7,
                height: 7,
                borderRadius: 99,
                background: rewritten && isTarget ? GREEN : "#475569",
              }}
            />
            {rewritten && isTarget ? afterBullet : bullet}
            {marked && isTarget ? (
              <>
                <div
                  style={{
                    position: "absolute",
                    inset: -8,
                    borderRadius: 20,
                    border: `5px solid ${RED}`,
                    transform: "rotate(-1.8deg)",
                    opacity: 0.9,
                  }}
                />
                <div
                  style={{
                    position: "absolute",
                    right: 14,
                    top: -14,
                    padding: "2px 8px",
                    borderRadius: 999,
                    background: "#fbfdff",
                    color: RED,
                    fontSize: 22,
                    fontWeight: 950,
                    transform: "rotate(2deg)",
                    zIndex: 3,
                  }}
                >
                  {markedLabel}
                </div>
              </>
            ) : null}
            {marked && index === 2 ? (
              <div
                style={{
                  position: "absolute",
                  left: 22,
                  right: 70,
                  bottom: 9,
                  height: 14,
                  background: "rgba(250,204,21,0.48)",
                  transform: "rotate(-1deg)",
                }}
              />
            ) : null}
          </div>
        );
      })}
    </div>
    {rewritten ? (
      <div
        style={{
          position: "absolute",
          right: 28,
          bottom: 28,
          display: "flex",
          alignItems: "center",
          gap: 10,
          color: GREEN,
          fontSize: 18,
          fontWeight: 950,
          textTransform: "uppercase",
        }}
      >
        <SignalMascot logoMode style={{ width: 42, height: 42 }} />
        Real proof translated
      </div>
    ) : null}
  </div>
);

const JobDescription: React.FC<{ jobTitle: string; keywords: string[]; highlightProgress: number }> = ({
  jobTitle,
  keywords,
  highlightProgress,
}) => (
  <div
    style={{
      width: 392,
      borderRadius: 26,
      background: "rgba(15,23,42,0.94)",
      border: "1px solid rgba(56,213,255,0.24)",
      padding: "28px 26px",
      color: TEXT,
      boxShadow: "0 26px 80px rgba(0,0,0,0.34), inset 0 0 30px rgba(56,213,255,0.045)",
    }}
  >
    <div style={{ color: CYAN, fontSize: 14, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.4 }}>
      Job description
    </div>
    <div style={{ marginTop: 12, fontSize: 30, lineHeight: 1.04, fontWeight: 950 }}>{jobTitle}</div>
    <div style={{ height: 1, background: "rgba(255,255,255,0.12)", margin: "22px 0" }} />
    <div style={{ display: "grid", gap: 13 }}>
      {keywords.map((keyword, index) => {
        const active = highlightProgress > index / keywords.length;
        return (
          <div
            key={keyword}
            style={{
              padding: "13px 14px",
              borderRadius: 15,
              background: active ? "rgba(250,204,21,0.22)" : "rgba(255,255,255,0.045)",
              border: active ? "1px solid rgba(250,204,21,0.52)" : "1px solid rgba(148,163,184,0.12)",
              color: active ? "#fef9c3" : "#cbd5e1",
              fontSize: 20,
              fontWeight: 900,
            }}
          >
            {keyword}
          </div>
        );
      })}
    </div>
  </div>
);

const AvatarBubble: React.FC<{ src: string; label: string; opacity: number }> = ({ src, label, opacity }) => (
  <div
    style={{
      position: "absolute",
      right: 44,
      top: 90,
      width: 220,
      height: 220,
      borderRadius: "50%",
      overflow: "hidden",
      border: "4px solid rgba(56,213,255,0.42)",
      background: "#020617",
      opacity,
      zIndex: 120,
      boxShadow: "0 0 44px rgba(56,213,255,0.28)",
    }}
  >
    <Video src={staticFile(src)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    <div
      style={{
        position: "absolute",
        left: 14,
        right: 14,
        bottom: 12,
        padding: "7px 8px",
        borderRadius: 999,
        background: "rgba(2,6,23,0.78)",
        color: "#dbeafe",
        fontSize: 12,
        fontWeight: 950,
        textAlign: "center",
        textTransform: "uppercase",
      }}
    >
      {label}
    </div>
  </div>
);

const TopCaption: React.FC<{ text: string; emphasis?: string; tone?: "red" | "green" | "yellow" }> = ({
  text,
  emphasis,
  tone = "yellow",
}) => {
  const color = tone === "green" ? "#bbf7d0" : tone === "red" ? "#fecaca" : "#fef08a";
  return (
    <div
      style={{
        position: "absolute",
        left: 54,
        right: 54,
        top: 92,
        padding: "20px 28px",
        borderRadius: 26,
        background: "rgba(2,6,23,0.86)",
        border: "1px solid rgba(56,213,255,0.22)",
        boxShadow: "0 22px 70px rgba(0,0,0,0.42)",
        color: TEXT,
        fontSize: 42,
        lineHeight: 1.08,
        fontWeight: 950,
        textAlign: "center",
        zIndex: 110,
      }}
    >
      {text}
      {emphasis ? <span style={{ color }}> {emphasis}</span> : null}
    </div>
  );
};

const CreatorBadge: React.FC<{ label: string }> = ({ label }) => (
  <div
    style={{
      position: "absolute",
      left: 44,
      top: 26,
      zIndex: 145,
      display: "flex",
      alignItems: "center",
      gap: 9,
      padding: "8px 12px",
      borderRadius: 999,
      border: "1px solid rgba(56,213,255,0.30)",
      background: "rgba(2,6,23,0.82)",
      color: CYAN,
      fontSize: 14,
      fontWeight: 950,
      textTransform: "uppercase",
      letterSpacing: 1.5,
      boxShadow: "0 18px 54px rgba(0,0,0,0.38)",
    }}
  >
    <SignalMascot logoMode style={{ width: 26, height: 26 }} />
    {label}
  </div>
);

const SignalReaction: React.FC<{
  line?: string;
  expression?: React.ComponentProps<typeof SignalMascot>["expression"];
  gesture?: React.ComponentProps<typeof SignalMascot>["gesture"];
  side?: "left" | "right";
  bottom?: number;
  opacity: number;
}> = ({ line, expression = "sideEye", gesture = "pointLeft", side = "right", bottom = 258, opacity }) => {
  if (!line) return null;
  const isRight = side === "right";
  return (
    <div
      style={{
        position: "absolute",
        [isRight ? "right" : "left"]: 44,
        bottom,
        width: 430,
        zIndex: 126,
        opacity,
        display: "flex",
        flexDirection: isRight ? "row-reverse" : "row",
        alignItems: "center",
        gap: 12,
        transform: `translateY(${Math.sin(useCurrentFrame() * 0.08) * 5}px)`,
      }}
    >
      <SignalMascot expression={expression} gesture={gesture} speaking style={{ width: 138, height: 138, flex: "0 0 auto" }} />
      <div
        style={{
          padding: "15px 18px",
          borderRadius: 22,
          border: "1px solid rgba(56,213,255,0.28)",
          background: "rgba(2,6,23,0.88)",
          color: "#e0f7ff",
          fontSize: 27,
          lineHeight: 1.08,
          fontWeight: 950,
          boxShadow: "0 18px 58px rgba(0,0,0,0.42)",
        }}
      >
        {line}
      </div>
    </div>
  );
};

const LowerPunchline: React.FC<{ text: string; tone?: "red" | "green" | "yellow" }> = ({ text, tone = "yellow" }) => {
  const color = tone === "green" ? "#bbf7d0" : tone === "red" ? "#fecaca" : "#fef08a";
  return (
    <div
      style={{
        position: "absolute",
        left: 58,
        right: 58,
        bottom: 158,
        zIndex: 116,
        padding: "17px 22px",
        borderRadius: 22,
        border: `1px solid ${tone === "green" ? "rgba(22,163,74,0.32)" : tone === "red" ? "rgba(220,38,38,0.32)" : "rgba(250,204,21,0.30)"}`,
        background: "rgba(2,6,23,0.84)",
        color,
        fontSize: 31,
        lineHeight: 1.06,
        fontWeight: 950,
        textAlign: "center",
        boxShadow: "0 20px 65px rgba(0,0,0,0.42)",
      }}
    >
      {text}
    </div>
  );
};

export const ResumeCrimeScene: React.FC<ResumeCrimeSceneProps> = ({
  hook,
  subhook,
  creativeFormat = "resumeCrimeScene",
  visualStyle = "neon",
  pace = "balanced",
  seriesLabel = "Recruiter reacts",
  signalLines = defaultResumeCrimeSceneProps.signalLines,
  punchline = "Qualified, but invisible.",
  problemPunchline = "Recruiters search for proof, not vibes.",
  markedLabel = "Too vague",
  teardownText = "Not fake. Just",
  teardownEmphasis = "too vague.",
  teardownPunchline = "This is the part costing you interviews.",
  teardownIssues = ["No role language", "No tools", "No measurable proof"],
  fixText = "Same experience.",
  fixEmphasis = "Better signal.",
  fixPunchline = "No fake experience. Just clearer evidence.",
  resumeTitle,
  jobTitle,
  jobKeywords,
  weakBullets,
  beforeBullet,
  afterBullet,
  beforeScore,
  afterScore,
  cta,
  musicSrc,
  musicVolume = 0.16,
  voiceoverSrc,
  voiceoverVolume = 0.94,
  sfxSrc,
  sfxVolume = 0.06,
  avatarVideoUrl,
  avatarLabel = "Recruiter review",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const styleName = visualStyle in VISUAL_STYLES ? visualStyle : "neon";
  const styleTheme = VISUAL_STYLES[styleName];
  const timing = PACE[pace] || PACE.balanced;
  const totalSeconds = 45;
  const hookOpacity = stageOpacity(frame, timing.hook[0], timing.hook[1]);
  const problemOpacity = stageOpacity(frame, timing.problem[0], timing.problem[1]);
  const teardownOpacity = stageOpacity(frame, timing.teardown[0], timing.teardown[1]);
  const fixOpacity = stageOpacity(frame, timing.fix[0], timing.fix[1]);
  const ctaOpacity = fadeIn(frame, timing.cta[0], timing.cta[0] + 62);
  const highlightProgress = fadeIn(frame, 170, 275);
  const fixSpring = spring({ frame: frame - timing.fix[0], fps, config: { damping: 18, mass: 0.9 } });
  const scoreProgress = fadeIn(frame, 822, 920);

  const animatedScore = interpolate(scoreProgress, [0, 1], [beforeScore, afterScore], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: styleTheme.background,
        fontFamily: FONT,
        overflow: "hidden",
      }}
    >
      {musicSrc ? (
        <Audio
          src={staticFile(musicSrc)}
          loop
          volume={(audioFrame) =>
            interpolate(audioFrame, [0, fps, (totalSeconds - 2) * fps, totalSeconds * fps], [0, musicVolume, musicVolume, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            })
          }
        />
      ) : null}
      {voiceoverSrc ? <Audio src={staticFile(voiceoverSrc)} volume={voiceoverVolume} /> : null}
      {sfxSrc ? <Audio src={staticFile(sfxSrc)} volume={sfxVolume} /> : null}

      <StyleTexture styleName={styleName} />

      {avatarVideoUrl ? (
        <Sequence from={0} durationInFrames={150}>
          <AvatarBubble src={avatarVideoUrl} label={avatarLabel} opacity={fadeIn(frame, 0, 15) * fadeOut(frame, 128, 150)} />
        </Sequence>
      ) : null}
      <CreatorBadge label={seriesLabel || creativeFormat} />

      <AbsoluteFill style={{ opacity: hookOpacity, alignItems: "center", justifyContent: "center", padding: 70, textAlign: "center" }}>
        <div style={{ color: styleTheme.warning, fontSize: 28, fontWeight: 950, textTransform: "uppercase", letterSpacing: 2.4 }}>
          {creativeFormat.replace(/([A-Z])/g, " $1").trim()}
        </div>
        <div style={{ color: TEXT, fontSize: 82, lineHeight: 0.98, fontWeight: 950, marginTop: 24, maxWidth: 900 }}>{hook}</div>
        <div style={{ color: styleTheme.accent, fontSize: 46, lineHeight: 1.08, fontWeight: 950, marginTop: 26, maxWidth: 800 }}>{subhook}</div>
        <ScoreBadge score={beforeScore} tone="bad" />
        <LowerPunchline text={punchline} tone="yellow" />
        <SignalReaction line={signalLines?.hook} expression="surprised" gesture="wave" side="right" bottom={318} opacity={hookOpacity} />
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: problemOpacity }}>
        <TopCaption text="The job description says:" emphasis={jobKeywords.slice(0, 2).join(" + ")} />
        <LowerPunchline text={problemPunchline} tone="red" />
        <div style={{ position: "absolute", left: 58, top: 225 }}>
          <ResumeSheet
            title={resumeTitle}
            bullets={weakBullets}
            marked
            beforeBullet={beforeBullet}
            afterBullet={afterBullet}
            markedLabel={markedLabel}
          />
        </div>
        <div style={{ position: "absolute", right: 58, top: 318 }}>
          <JobDescription jobTitle={jobTitle} keywords={jobKeywords} highlightProgress={highlightProgress} />
        </div>
        <div style={{ position: "absolute", right: 74, bottom: 585 }}>
          <ScoreBadge score={beforeScore} tone="bad" label="Low match" />
        </div>
        <SignalReaction line={signalLines?.problem} expression="sideEye" gesture="pointLeft" side="right" bottom={402} opacity={problemOpacity} />
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: teardownOpacity }}>
        <TopCaption text={teardownText} emphasis={teardownEmphasis} tone="red" />
        <LowerPunchline text={teardownPunchline} tone="red" />
        <div style={{ position: "absolute", left: 82, top: 260 }}>
          <ResumeSheet
            title={resumeTitle}
            bullets={weakBullets}
            marked
            beforeBullet={beforeBullet}
            afterBullet={afterBullet}
            markedLabel={markedLabel}
          />
        </div>
        <div
          style={{
            position: "absolute",
            right: 66,
            top: 350,
            width: 368,
            display: "grid",
            gap: 18,
          }}
        >
          {teardownIssues.slice(0, 4).map((issue, index) => (
            <div
              key={issue}
              style={{
                padding: "18px 20px",
                borderRadius: 18,
                border: "2px solid rgba(220,38,38,0.38)",
                background: "rgba(220,38,38,0.10)",
                color: "#fecaca",
                fontSize: 28,
                fontWeight: 950,
                transform: `translateX(${interpolate(frame, [340 + index * 30, 370 + index * 30], [22, 0], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                })}px)`,
              }}
            >
              {issue}
            </div>
          ))}
        </div>
        <SignalReaction line={signalLines?.teardown} expression="concerned" gesture="pointLeft" side="right" bottom={250} opacity={teardownOpacity} />
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: fixOpacity }}>
        <TopCaption text={fixText} emphasis={fixEmphasis} tone="green" />
        <LowerPunchline text={fixPunchline} tone="green" />
        <div
          style={{
            position: "absolute",
            left: 74,
            top: 258,
            transform: `scale(${interpolate(fixSpring, [0, 1], [0.94, 1], { extrapolateRight: "clamp" })})`,
          }}
        >
          <ResumeSheet
            title={resumeTitle}
            bullets={weakBullets}
            rewritten
            beforeBullet={beforeBullet}
            afterBullet={afterBullet}
            markedLabel={markedLabel}
          />
        </div>
        <div style={{ position: "absolute", right: 70, top: 348 }}>
          <JobDescription jobTitle={jobTitle} keywords={jobKeywords} highlightProgress={1} />
        </div>
        <div
          style={{
            position: "absolute",
            right: 86,
            bottom: 360,
            display: "flex",
            alignItems: "center",
            gap: 16,
          }}
        >
          <SignalMascot expression="happy" gesture="pointLeft" style={{ width: 120, height: 120 }} />
          <ScoreBadge score={Math.round(animatedScore)} tone={scoreProgress > 0.7 ? "good" : "bad"} label={scoreProgress > 0.7 ? "Optimized" : "Improving"} />
        </div>
        <SignalReaction line={signalLines?.fix} expression="happy" gesture="pointLeft" side="right" bottom={210} opacity={fixOpacity} />
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: ctaOpacity, alignItems: "center", justifyContent: "center", textAlign: "center", padding: 78 }}>
        <SignalMascot expression="wink" gesture="wave" speaking style={{ width: 250, height: 250 }} />
        <div style={{ color: TEXT, fontSize: 84, fontWeight: 950, lineHeight: 0.96, marginTop: 34 }}>
          {beforeScore}/100 to {afterScore}/100
        </div>
        <div style={{ color: styleTheme.accent, fontSize: 38, fontWeight: 950, lineHeight: 1.16, marginTop: 26, maxWidth: 790 }}>{cta}</div>
        <div
          style={{
            marginTop: 28,
            padding: "18px 34px",
            borderRadius: 999,
            background: "linear-gradient(135deg, #1d4ed8, #0891b2 54%, #34d399)",
            border: "2px solid rgba(125,223,255,0.52)",
            boxShadow: "0 20px 70px rgba(56,213,255,0.25)",
            color: "#ffffff",
            fontSize: 31,
            fontWeight: 950,
            textTransform: "uppercase",
            letterSpacing: 1.2,
          }}
        >
          Free resume roast
        </div>
        <div style={{ color: "#cbd5e1", fontSize: 26, lineHeight: 1.18, fontWeight: 900, marginTop: 20, maxWidth: 760 }}>
          Paste your resume + job description before you apply.
        </div>
        <SignalReaction line={signalLines?.cta} expression="happy" gesture="wave" side="left" bottom={276} opacity={ctaOpacity} />
      </AbsoluteFill>

      <div
        style={{
          position: "absolute",
          left: 44,
          bottom: 40,
          display: "flex",
          alignItems: "center",
          gap: 10,
          color: MUTED,
          fontSize: 18,
          fontWeight: 850,
          textTransform: "uppercase",
          letterSpacing: 1.4,
          zIndex: 140,
        }}
      >
        <SignalMascot logoMode style={{ width: 38, height: 38 }} />
        Signal by ATSHacker
      </div>
      <div
        style={{
          position: "absolute",
          right: 44,
          bottom: 52,
          width: 310,
          height: 4,
          borderRadius: 99,
          background: "rgba(148,163,184,0.18)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${interpolate(frame, [0, totalSeconds * fps], [0, 100], { extrapolateRight: "clamp" })}%`,
            height: "100%",
            background: "linear-gradient(90deg, #dc2626, #facc15, #16a34a, #38d5ff)",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
