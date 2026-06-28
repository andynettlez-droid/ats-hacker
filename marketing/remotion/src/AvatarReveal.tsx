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

// Brand Colors
const EMERALD = "#10b981";
const DARK = "#0a0a0a";
const AMBER = "#f59e0b";
const RED = "#ef4444";
const WHITE = "#ffffff";
const FONT = '"Inter", "Helvetica Neue", "Segoe UI", Arial, system-ui, sans-serif';

// Prop Schema
export const avatarRevealSchema = z.object({
  hook1: z.string(),
  hook2: z.string(),
  subline: z.string(),
  missing: z.array(z.string()),
  beforeScore: z.number(),
  afterScore: z.number(),
  cta: z.string(),
  avatarVideoUrl: z.string(),
});

export type AvatarRevealProps = z.infer<typeof avatarRevealSchema>;

export const defaultAvatarRevealProps: AvatarRevealProps = {
  hook1: "Resume not surfacing?",
  hook2: "Keywords are missing.",
  subline: "Recruiters search and rank resumes by job-description match.",
  missing: ["Kubernetes", "CI/CD", "scalability"],
  beforeScore: 34,
  afterScore: 91,
  cta: "Get your score free. Link in bio",
  avatarVideoUrl: "avatar.mp4",
};

const scoreColor = (score: number): string => {
  if (score >= 75) return EMERALD;
  if (score >= 50) return AMBER;
  return RED;
};

export const AvatarReveal: React.FC<AvatarRevealProps> = ({
  hook1,
  hook2,
  subline,
  missing,
  beforeScore,
  afterScore,
  cta,
  avatarVideoUrl,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Animations timings (frames)
  // Scene 1: Hook (0 - 90 frames / 0 - 3s)
  // Scene 2: Interactive Scan UI (90 - 390 frames / 3 - 13s)
  // Scene 3: Climax count-up & chips flip (120 - 240 frames / 4 - 8s)
  // Scene 4: CTA overlay (390 - end / 13s - end)

  // 1. Hook animations
  const hookSpring = spring({ frame, fps, config: { damping: 15 } });
  const hookOpacity = interpolate(frame, [0, 15, 80, 90], [0, 1, 1, 0]);
  const hookY = interpolate(hookSpring, [0, 1], [30, 0]);

  const hook2Spring = spring({ frame: frame - 30, fps, config: { damping: 12 } });
  const hook2Scale = interpolate(hook2Spring, [0, 1], [0.8, 1]);
  const hook2Opacity = interpolate(frame, [30, 40, 80, 90], [0, 1, 1, 0]);

  // 2. Scan UI Entrance (fades in at frame 90)
  const uiEntrance = spring({ frame: frame - 90, fps, config: { damping: 20 } });
  const uiOpacity = interpolate(uiEntrance, [0, 1], [0, 1]);
  const uiY = interpolate(uiEntrance, [0, 1], [40, 0]);

  // 3. Score count-up (frames 120 to 220)
  const counted = interpolate(
    frame,
    [120, 220],
    [beforeScore, afterScore],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const displayScore = Math.round(counted);
  const currentColor = scoreColor(displayScore);
  const ringPct = displayScore / 100;

  // Pop when score reaches maximum
  const pop = spring({ frame: frame - 220, fps, config: { damping: 8, mass: 0.5 } });
  const popScale = interpolate(pop, [0, 1], [1, 1.08], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // 4. Captions animation (mock captions parsed from words/timings, scrolling automatically)
  // Let's create general captions that scroll up based on frame.
  const captionItems = [
    { text: "If your resume keeps disappearing in recruiter search...", start: 0, end: 90 },
    { text: "It may not match the recruiter search.", start: 90, end: 150 },
    { text: "Applicant Tracking Systems index and rank keywords.", start: 150, end: 230 },
    { text: "Match the job language without inventing experience.", start: 230, end: 320 },
    { text: "Signal scans the JD and rewrites your resume bullets around real proof.", start: 320, end: 410 },
    { text: "Check your match score free. Link in bio to try it now.", start: 410, end: durationInFrames }
  ];

  const currentCaption = captionItems.find(c => frame >= c.start && frame < c.end)?.text || "";

  // 5. CTA entrance
  const ctaEntrance = spring({ frame: frame - 410, fps, config: { damping: 15 } });
  const ctaOpacity = interpolate(ctaEntrance, [0, 1], [0, 1]);
  const ctaScale = interpolate(ctaEntrance, [0, 1], [0.9, 1]);

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(120% 80% at 50% 18%, #11261f 0%, ${DARK} 55%, #050505 100%)`,
        overflow: "hidden",
      }}
    >
      {/* Background Accent Grid */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "linear-gradient(rgba(16,185,129,0.03) 2px, transparent 2px), linear-gradient(90deg, rgba(16,185,129,0.03) 2px, transparent 2px)",
          backgroundSize: "60px 60px",
          opacity: 0.6
        }}
      />

      {/* Glow effect at top */}
      <div
        style={{
          position: "absolute",
          top: -300,
          left: "50%",
          transform: "translateX(-50%)",
          width: 1000,
          height: 600,
          background: "radial-gradient(circle, rgba(16,185,129,0.12) 0%, rgba(16,185,129,0) 70%)",
          filter: "blur(50px)",
          pointerEvents: "none"
        }}
      />

      {/* --------------------------------------------------------------------- */}
      {/* SCENE 1: HOOK SCENE (0 - 3s) */}
      {/* --------------------------------------------------------------------- */}
      {frame < 95 && (
        <AbsoluteFill
          style={{
            justifyContent: "center",
            alignItems: "center",
            padding: 80,
            textAlign: "center",
            zIndex: 10
          }}
        >
          <div
            style={{
              fontFamily: FONT,
              color: WHITE,
              fontWeight: 800,
              fontSize: 105,
              lineHeight: 1.1,
              letterSpacing: -1,
              opacity: hookOpacity,
              transform: `translateY(${hookY}px)`,
              textShadow: "0 10px 30px rgba(0,0,0,0.5)"
            }}
          >
            {hook1}
          </div>
          <div
            style={{
              fontFamily: FONT,
              color: EMERALD,
              fontWeight: 900,
              fontSize: 130,
              lineHeight: 1.0,
              marginTop: 40,
              opacity: hook2Opacity,
              transform: `scale(${hook2Scale})`,
              textShadow: "0 10px 40px rgba(16,185,129,0.3)"
            }}
          >
            {hook2}
          </div>
        </AbsoluteFill>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* SCENE 2: INTERACTIVE DASHBOARD UI (3s - End) */}
      {/* --------------------------------------------------------------------- */}
      {frame >= 90 && (
        <AbsoluteFill
          style={{
            padding: 80,
            opacity: uiOpacity,
            transform: `translateY(${uiY}px)`,
          }}
        >
          {/* Main Layout Area */}
          <div style={{ width: 920, display: "flex", flexDirection: "column", gap: 50 }}>
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2
                style={{
                  fontFamily: FONT,
                  color: WHITE,
                  fontWeight: 800,
                  fontSize: 52,
                  letterSpacing: 1
                }}
              >
                ATS Match Report
              </h2>
              <span
                style={{
                  fontFamily: FONT,
                  color: currentColor,
                  fontWeight: 900,
                  fontSize: 32,
                  textTransform: "uppercase",
                  letterSpacing: 2,
                  background: `${currentColor}15`,
                  border: `2px solid ${currentColor}30`,
                  padding: "10px 24px",
                  borderRadius: 12
                }}
              >
                {displayScore >= 75 ? "Optimal Match" : "Keywords Deficit"}
              </span>
            </div>

            {/* Score Ring Section */}
            <div style={{ display: "flex", alignItems: "center", gap: 60, background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 32, padding: 50, boxShadow: "0 30px 60px rgba(0,0,0,0.3)" }}>
              <div
                style={{
                  position: "relative",
                  width: 320,
                  height: 320,
                  transform: `scale(${popScale})`,
                }}
              >
                <svg width="320" height="320" viewBox="0 0 320 320">
                  <circle
                    cx="160"
                    cy="160"
                    r="135"
                    fill="none"
                    stroke="rgba(255,255,255,0.06)"
                    strokeWidth="24"
                  />
                  <circle
                    cx="160"
                    cy="160"
                    r="135"
                    fill="none"
                    stroke={currentColor}
                    strokeWidth="24"
                    strokeLinecap="round"
                    strokeDasharray={2 * Math.PI * 135}
                    strokeDashoffset={2 * Math.PI * 135 * (1 - ringPct)}
                    transform="rotate(-90 160 160)"
                    style={{ transition: "stroke 0.2s" }}
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
                  <span
                    style={{
                      fontFamily: FONT,
                      color: currentColor,
                      fontWeight: 900,
                      fontSize: 110,
                      lineHeight: 1,
                    }}
                  >
                    {displayScore}
                  </span>
                  <span
                    style={{
                      fontFamily: FONT,
                      color: "rgba(255,255,255,0.4)",
                      fontWeight: 700,
                      fontSize: 28,
                    }}
                  >
                    / 100
                  </span>
                </div>
              </div>

              {/* Text explanations */}
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16 }}>
                <h3 style={{ fontFamily: FONT, color: WHITE, fontWeight: 700, fontSize: 38 }}>
                  {displayScore < 75 ? "Low Match Score" : "Resume Optimized"}
                </h3>
                <p style={{ fontFamily: FONT, color: "rgba(255,255,255,0.5)", fontSize: 28, lineHeight: 1.4, fontWeight: 400 }}>
                  {displayScore < 75
                    ? "Critical semantic gaps detected. Resume will be ranked low in recruiter search results."
                    : "Excellent match density! Bullet points optimized for the target job description keywords."}
                </p>
              </div>
            </div>

            {/* Keyword chips mapping */}
            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              <h4 style={{ fontFamily: FONT, color: "rgba(255,255,255,0.4)", fontSize: 28, fontWeight: 800, textTransform: "uppercase", letterSpacing: 1.5 }}>
                Semantic Keywords Analysis
              </h4>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 20 }}>
                {missing.map((kw, i) => {
                  const flipStart = 130 + i * 15;
                  const flip = interpolate(frame, [flipStart, flipStart + 16], [0, 1], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  });
                  const isFixed = flip > 0.5;

                  return (
                    <div
                      key={kw}
                      style={{
                        fontFamily: FONT,
                        fontWeight: 700,
                        fontSize: 34,
                        color: WHITE,
                        padding: "16px 30px",
                        borderRadius: 20,
                        display: "flex",
                        alignItems: "center",
                        gap: 12,
                        background: isFixed ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.12)",
                        border: `2px solid ${isFixed ? EMERALD : RED}`,
                        boxShadow: isFixed ? "0 8px 24px rgba(16,185,129,0.15)" : "none",
                        transition: "background 0.2s, border-color 0.2s"
                      }}
                    >
                      <span>{isFixed ? "âœ“" : "âœ•"}</span>
                      <span>{kw}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </AbsoluteFill>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* FLOATING HEYGEN AVATAR CARD (0 - End) */}
      {/* --------------------------------------------------------------------- */}
      <div
        style={{
          position: "absolute",
          bottom: 180,
          right: 80,
          width: 380,
          height: 560,
          borderRadius: 36,
          border: "3px solid rgba(255,255,255,0.12)",
          background: "rgba(15,15,15,0.65)",
          backdropFilter: "blur(20px)",
          boxShadow: "0 30px 60px rgba(0,0,0,0.6)",
          overflow: "hidden",
          zIndex: 40,
        }}
      >
        <OffthreadVideo
          src={staticFile(avatarVideoUrl)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
        {/* Soft dark vignette over video bottom */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "linear-gradient(to top, rgba(0,0,0,0.4) 0%, transparent 30%)",
            pointerEvents: "none"
          }}
        />
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* DYNAMIC SCROLLING CAPTIONS PANEL (0 - End) */}
      {/* --------------------------------------------------------------------- */}
      <div
        style={{
          position: "absolute",
          bottom: 50,
          left: 80,
          width: 800,
          height: 100,
          zIndex: 50,
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-start",
        }}
      >
        {currentCaption && (
          <p
            style={{
              fontFamily: FONT,
              fontWeight: 800,
              fontSize: 38,
              lineHeight: 1.3,
              color: WHITE,
              margin: 0,
              textShadow: "0 4px 12px rgba(0,0,0,0.8)",
              background: "rgba(0,0,0,0.5)",
              padding: "12px 24px",
              borderRadius: 16,
              borderLeft: `5px solid ${EMERALD}`,
              animation: "fadeIn 0.2s"
            }}
          >
            {currentCaption}
          </p>
        )}
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* SCENE 4: CTA FINAL SCREEN OVERLAY (13s - End) */}
      {/* --------------------------------------------------------------------- */}
      {frame >= 390 && (
        <AbsoluteFill
          style={{
            background: `radial-gradient(120% 80% at 50% 18%, #11261f 0%, ${DARK} 75%, #050505 100%)`,
            zIndex: 100,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            padding: 80,
            textAlign: "center",
            opacity: ctaOpacity,
            transform: `scale(${ctaScale})`
          }}
        >
          {/* Logo / Brand mark */}
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 80 }}>
            <span style={{ fontSize: 90 }}>ðŸš€</span>
            <span style={{ fontFamily: FONT, color: WHITE, fontWeight: 900, fontSize: 80, letterSpacing: -1 }}>
              ATS<span style={{ color: EMERALD }}>Hacker</span>
            </span>
          </div>

          <h3
            style={{
              fontFamily: FONT,
              color: WHITE,
              fontWeight: 800,
              fontSize: 72,
              lineHeight: 1.2,
              marginBottom: 40,
              maxWidth: 900
            }}
          >
            Stop Letting Good Experience Get Buried
          </h3>

          <p
            style={{
              fontFamily: FONT,
              color: "rgba(255,255,255,0.5)",
              fontSize: 38,
              fontWeight: 500,
              marginBottom: 90,
              maxWidth: 800,
              lineHeight: 1.4
            }}
          >
            Rewrite your bullets. Match the job description. Get seen by recruiters.
          </p>

          <div
            style={{
              fontFamily: FONT,
              fontSize: 48,
              fontWeight: 900,
              color: EMERALD,
              background: "rgba(16,185,129,0.08)",
              border: `3px solid ${EMERALD}`,
              padding: "36px 72px",
              borderRadius: 30,
              boxShadow: "0 20px 50px rgba(16,185,129,0.2)",
              textTransform: "uppercase",
              letterSpacing: 2
            }}
          >
            {cta}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
