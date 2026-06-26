import React from "react";
import {
  AbsoluteFill,
  Sequence,
  OffthreadVideo,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
} from "remotion";
import { z } from "zod";

// ---------------------------------------------------------------------------
// Brand
// ---------------------------------------------------------------------------
const EMERALD = "#10b981";
const DARK = "#0a0a0a";
const AMBER = "#f59e0b";
const RED = "#ef4444";
const WHITE = "#ffffff";
const FONT =
  '"Inter", "Helvetica Neue", "Segoe UI", Arial, system-ui, sans-serif';

// ---------------------------------------------------------------------------
// Props schema + defaults
// ---------------------------------------------------------------------------
export const scoreRevealSchema = z.object({
  hook1: z.string(),
  hook2: z.string(),
  subline: z.string(),
  missing: z.array(z.string()),
  beforeScore: z.number(),
  afterScore: z.number(),
  cta: z.string(),
  bgVideo: z.string().optional(),
});

export type ScoreRevealProps = z.infer<typeof scoreRevealSchema>;

export const defaultScoreRevealProps: ScoreRevealProps = {
  hook1: "327 applications.",
  hook2: "2 callbacks.",
  subline: "Recruiters search resumes by keyword.",
  missing: ["stakeholder", "Agile", "KPIs", "roadmap"],
  beforeScore: 38,
  afterScore: 89,
  cta: "Comment your job title 👇  ·  free score in bio",
  bgVideo: undefined,
};

// Color tier for a given ATS score.
const scoreColor = (score: number): string => {
  if (score >= 75) return EMERALD;
  if (score >= 50) return AMBER;
  return RED;
};

// ---------------------------------------------------------------------------
// Background: full-bleed bgVideo behind a dark scrim, or a dark gradient with
// subtle emerald accents.
// ---------------------------------------------------------------------------
const isRemote = (src: string) => /^https?:\/\//.test(src);

const Background: React.FC<{ bgVideo?: string }> = ({ bgVideo }) => {
  if (bgVideo) {
    const src = isRemote(bgVideo) ? bgVideo : staticFile(bgVideo);
    return (
      <AbsoluteFill>
        <OffthreadVideo
          src={src}
          muted
          loop
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
        {/* dark scrim for caption legibility over B-roll */}
        <AbsoluteFill
          style={{
            background:
              "linear-gradient(180deg, rgba(10,10,10,0.65) 0%, rgba(10,10,10,0.45) 45%, rgba(10,10,10,0.8) 100%)",
          }}
        />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(120% 80% at 50% 18%, #11261f 0%, ${DARK} 55%, #050505 100%)`,
      }}
    >
      {/* subtle emerald glow accents */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(40% 22% at 50% 88%, rgba(16,185,129,0.22) 0%, rgba(16,185,129,0) 70%)`,
        }}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Scene 1 (0 - 2.5s): hook1, then hook2 punch-in.
// ---------------------------------------------------------------------------
const HookScene: React.FC<{ hook1: string; hook2: string }> = ({
  hook1,
  hook2,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const in1 = spring({ frame, fps, config: { damping: 200 } });
  const hook1Opacity = interpolate(in1, [0, 1], [0, 1]);
  const hook1Y = interpolate(in1, [0, 1], [40, 0]);

  // hook2 punches in at ~1.1s (frame 33)
  const punch = spring({
    frame: frame - 33,
    fps,
    config: { damping: 12, mass: 0.6, stiffness: 180 },
  });
  const hook2Scale = interpolate(punch, [0, 1], [0.4, 1], {
    extrapolateLeft: "clamp",
  });
  const hook2Opacity = interpolate(frame, [33, 40], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: 80,
        textAlign: "center",
      }}
    >
      <div
        style={{
          fontFamily: FONT,
          color: WHITE,
          fontWeight: 800,
          fontSize: 110,
          lineHeight: 1.05,
          opacity: hook1Opacity,
          transform: `translateY(${hook1Y}px)`,
        }}
      >
        {hook1}
      </div>
      <div
        style={{
          fontFamily: FONT,
          color: EMERALD,
          fontWeight: 900,
          fontSize: 150,
          lineHeight: 1.0,
          marginTop: 40,
          opacity: hook2Opacity,
          transform: `scale(${hook2Scale})`,
        }}
      >
        {hook2}
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Scene 2 (2.5 - 6s): subline + search-bar filtering / keyword chips.
// ---------------------------------------------------------------------------
const SearchScene: React.FC<{ subline: string; missing: string[] }> = ({
  subline,
  missing,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sublineIn = spring({ frame, fps, config: { damping: 200 } });
  const sublineOpacity = interpolate(sublineIn, [0, 1], [0, 1]);
  const sublineY = interpolate(sublineIn, [0, 1], [30, 0]);

  // Typed query effect in the search bar
  const query = "stakeholder";
  const typeProgress = interpolate(frame, [20, 55], [0, query.length], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const typed = query.slice(0, Math.round(typeProgress));
  const caretOn = Math.floor(frame / 8) % 2 === 0;

  return (
    <AbsoluteFill
      style={{ justifyContent: "center", alignItems: "center", padding: 80 }}
    >
      <div
        style={{
          fontFamily: FONT,
          color: WHITE,
          fontWeight: 700,
          fontSize: 70,
          lineHeight: 1.15,
          textAlign: "center",
          opacity: sublineOpacity,
          transform: `translateY(${sublineY}px)`,
          marginBottom: 70,
        }}
      >
        {subline}
      </div>

      {/* Search bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 24,
          width: 820,
          padding: "34px 40px",
          borderRadius: 24,
          background: "rgba(255,255,255,0.06)",
          border: `3px solid ${EMERALD}`,
          boxShadow: "0 0 40px rgba(16,185,129,0.25)",
        }}
      >
        <span style={{ fontSize: 56 }}>🔍</span>
        <span
          style={{
            fontFamily: FONT,
            color: WHITE,
            fontWeight: 600,
            fontSize: 58,
          }}
        >
          {typed}
          <span style={{ opacity: caretOn ? 1 : 0, color: EMERALD }}>|</span>
        </span>
      </div>

      {/* Keyword chips filtering in */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 22,
          justifyContent: "center",
          marginTop: 60,
          maxWidth: 900,
        }}
      >
        {missing.map((kw, i) => {
          const appear = spring({
            frame: frame - (60 + i * 8),
            fps,
            config: { damping: 14, stiffness: 160 },
          });
          return (
            <div
              key={kw}
              style={{
                fontFamily: FONT,
                fontWeight: 700,
                fontSize: 50,
                color: WHITE,
                padding: "20px 38px",
                borderRadius: 999,
                background: "rgba(16,185,129,0.15)",
                border: `2px solid ${EMERALD}`,
                opacity: interpolate(appear, [0, 1], [0, 1], {
                  extrapolateLeft: "clamp",
                }),
                transform: `scale(${interpolate(appear, [0, 1], [0.6, 1], {
                  extrapolateLeft: "clamp",
                })})`,
              }}
            >
              {kw}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Scene 3 (6 - 12s): SCORE REVEAL climax. Number counts beforeScore ->
// afterScore (color tiered), red "missing" chips flip to green.
// ---------------------------------------------------------------------------
const ScoreScene: React.FC<{
  beforeScore: number;
  afterScore: number;
  missing: string[];
}> = ({ beforeScore, afterScore, missing }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Title in
  const titleIn = spring({ frame, fps, config: { damping: 200 } });

  // Count up: hold "before" briefly (frames 18-40), then ramp to "after"
  // over frames 40-110.
  const counted = interpolate(
    frame,
    [18, 40, 110],
    [beforeScore, beforeScore, afterScore],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const displayScore = Math.round(counted);
  const color = scoreColor(displayScore);

  // Pop when the final score lands
  const pop = spring({
    frame: frame - 110,
    fps,
    config: { damping: 10, mass: 0.5, stiffness: 200 },
  });
  const popScale = interpolate(pop, [0, 1], [1, 1.12], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Progress ring sweep follows the score (0..100)
  const ringPct = displayScore / 100;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: 80,
      }}
    >
      <div
        style={{
          fontFamily: FONT,
          color: WHITE,
          fontWeight: 800,
          fontSize: 56,
          letterSpacing: 2,
          textTransform: "uppercase",
          opacity: interpolate(titleIn, [0, 1], [0, 1]),
          marginBottom: 50,
        }}
      >
        ATS Match Score
      </div>

      {/* Score dial */}
      <div
        style={{
          position: "relative",
          width: 520,
          height: 520,
          transform: `scale(${popScale})`,
        }}
      >
        <svg width="520" height="520" viewBox="0 0 520 520">
          <circle
            cx="260"
            cy="260"
            r="230"
            fill="none"
            stroke="rgba(255,255,255,0.12)"
            strokeWidth="34"
          />
          <circle
            cx="260"
            cy="260"
            r="230"
            fill="none"
            stroke={color}
            strokeWidth="34"
            strokeLinecap="round"
            strokeDasharray={2 * Math.PI * 230}
            strokeDashoffset={2 * Math.PI * 230 * (1 - ringPct)}
            transform="rotate(-90 260 260)"
          />
        </svg>
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <div
            style={{
              fontFamily: FONT,
              color,
              fontWeight: 900,
              fontSize: 220,
              lineHeight: 1,
            }}
          >
            {displayScore}
          </div>
          <div
            style={{
              fontFamily: FONT,
              color: "rgba(255,255,255,0.6)",
              fontWeight: 700,
              fontSize: 48,
            }}
          >
            / 100
          </div>
        </div>
      </div>

      {/* Missing keyword chips: red -> green as they are "fixed" */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 20,
          justifyContent: "center",
          marginTop: 70,
          maxWidth: 920,
        }}
      >
        {missing.map((kw, i) => {
          // Each chip flips around frames 50..100, staggered
          const flipStart = 50 + i * 12;
          const flip = interpolate(frame, [flipStart, flipStart + 14], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const fixed = flip > 0.5;
          return (
            <div
              key={kw}
              style={{
                fontFamily: FONT,
                fontWeight: 700,
                fontSize: 48,
                color: WHITE,
                padding: "18px 34px",
                borderRadius: 999,
                display: "flex",
                alignItems: "center",
                gap: 14,
                background: fixed
                  ? "rgba(16,185,129,0.18)"
                  : "rgba(239,68,68,0.18)",
                border: `2px solid ${fixed ? EMERALD : RED}`,
                transition: "none",
              }}
            >
              <span>{fixed ? "✓" : "✕"}</span>
              {kw}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Scene 4 (12 - 16s): CTA + "ATSHacker" wordmark.
// ---------------------------------------------------------------------------
const CtaScene: React.FC<{ cta: string }> = ({ cta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const wordmarkIn = spring({
    frame,
    fps,
    config: { damping: 13, mass: 0.7, stiffness: 170 },
  });
  const ctaIn = spring({ frame: frame - 18, fps, config: { damping: 200 } });

  // gentle pulse on the CTA
  const pulse = 1 + 0.02 * Math.sin((frame / fps) * Math.PI * 2 * 0.8);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: 80,
        textAlign: "center",
      }}
    >
      <div
        style={{
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: 130,
          letterSpacing: -2,
          transform: `scale(${interpolate(wordmarkIn, [0, 1], [0.6, 1], {
            extrapolateLeft: "clamp",
          })})`,
          opacity: interpolate(wordmarkIn, [0, 1], [0, 1]),
        }}
      >
        <span style={{ color: WHITE }}>ATS</span>
        <span style={{ color: EMERALD }}>Hacker</span>
      </div>

      <div
        style={{
          fontFamily: FONT,
          color: WHITE,
          fontWeight: 700,
          fontSize: 62,
          lineHeight: 1.2,
          marginTop: 60,
          maxWidth: 880,
          opacity: interpolate(ctaIn, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(ctaIn, [0, 1], [30, 0])}px) scale(${pulse})`,
        }}
      >
        {cta}
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Main composition: assembles all four scenes over the 16s timeline.
// ---------------------------------------------------------------------------
export const ScoreReveal: React.FC<ScoreRevealProps> = ({
  hook1,
  hook2,
  subline,
  missing,
  beforeScore,
  afterScore,
  cta,
  bgVideo,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: DARK }}>
      <Background bgVideo={bgVideo} />

      {/* 0 - 2.5s */}
      <Sequence durationInFrames={75}>
        <HookScene hook1={hook1} hook2={hook2} />
      </Sequence>

      {/* 2.5 - 6s */}
      <Sequence from={75} durationInFrames={105}>
        <SearchScene subline={subline} missing={missing} />
      </Sequence>

      {/* 6 - 12s (climax) */}
      <Sequence from={180} durationInFrames={180}>
        <ScoreScene
          beforeScore={beforeScore}
          afterScore={afterScore}
          missing={missing}
        />
      </Sequence>

      {/* 12 - 16s */}
      <Sequence from={360} durationInFrames={120}>
        <CtaScene cta={cta} />
      </Sequence>
    </AbsoluteFill>
  );
};
