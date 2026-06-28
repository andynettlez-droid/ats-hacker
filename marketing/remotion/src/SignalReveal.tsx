import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { SignalMascot } from "./components/SignalMascot";
import { AtsGate } from "./components/AtsGate";
import { ResumePanel } from "./components/ResumePanel";
import { HudChecklist } from "./components/HudChecklist";
import { KeywordStream } from "./components/KeywordStream";
import { BulletTransform } from "./components/BulletTransform";
import { HiringManagerScene } from "./components/HiringManagerScene";
import { CaptionLayer } from "./components/CaptionLayer";

// Reuse the same prop schema from AvatarReveal to ensure complete drop-in compatibility
export const signalRevealSchema = z.object({
  hook1: z.string(),
  hook2: z.string(),
  subline: z.string(),
  missing: z.array(z.string()),
  beforeScore: z.number(),
  afterScore: z.number(),
  cta: z.string(),
  avatarVideoUrl: z.string(),
});

export type SignalRevealProps = z.infer<typeof signalRevealSchema>;

export const defaultSignalRevealProps: SignalRevealProps = {
  hook1: "Most resumes",
  hook2: "get missed first.",
  subline: "Recruiters search by keywords before they ever open a resume.",
  missing: ["SQL", "Leadership", "Customer Growth", "Product Strategy", "Automation", "Stakeholder Management"],
  beforeScore: 42,
  afterScore: 94,
  cta: "Signal by ATSHacker - match the job and get seen.",
  avatarVideoUrl: "avatar.mp4",
};

const DARK = "#050508";
const CYAN = "#00f0ff";
const FONT = '"Inter", "Helvetica Neue", Arial, sans-serif';

export const SignalReveal: React.FC<SignalRevealProps> = ({
  beforeScore,
  afterScore,
  cta,
  avatarVideoUrl,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // -----------------------------------------------------------------
  // Timing & Animation Interpolations
  // -----------------------------------------------------------------

  // Scene 1 & 2: Resume position
  // Starts centered, then pushes to the left when Signal enters
  const resumeX = interpolate(frame, [200, 240], [0, -180], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Scene 3: Signal enters from right
  const mascotEntrance = spring({
    frame: frame - 210,
    fps,
    config: { damping: 15, mass: 0.8 },
  });
  const mascotX = interpolate(mascotEntrance, [0, 1], [400, 180]);
  const mascotOpacity = interpolate(frame, [210, 230], [0, 1], {
    extrapolateLeft: "clamp",
  });

  // Scene 7: Signal dissolve into resume
  // Dissolves between frames 1020 and 1100
  const dissolveProgress = interpolate(frame, [1020, 1100], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Resume sweeping wipe progress as Signal dissolves into it (frames 1050 to 1180)
  const resumeWipeProgress = interpolate(frame, [1050, 1180], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Scene 8: ATS Gate Pass & Open
  // Checklist checks progress (0 to 5) between frames 1290 and 1450
  const checklistProgress = interpolate(frame, [1290, 1450], [0, 5], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Gate open progress (0 to 1) between frames 1450 and 1530
  const gateOpenProgress = spring({
    frame: frame - 1450,
    fps,
    config: { damping: 15, mass: 1 },
  });

  // Scene 11: CTA Entrance
  const ctaEntrance = spring({
    frame: frame - 2040,
    fps,
    config: { damping: 15, mass: 0.8 },
  });
  const ctaScale = interpolate(ctaEntrance, [0, 1], [0.85, 1]);
  const ctaOpacity = interpolate(frame, [2040, 2070], [0, 1], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(120% 90% at 50% 15%, #08121a 0%, ${DARK} 60%, #020204 100%)`,
        overflow: "hidden",
        fontFamily: FONT,
      }}
    >
      {/* ------------------------------------------------------------- */}
      {/* BACKGROUND ELEMENTS */}
      {/* ------------------------------------------------------------- */}

      {/* Grid Overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "linear-gradient(rgba(0, 240, 255, 0.02) 2px, transparent 2px), linear-gradient(90deg, rgba(0, 240, 255, 0.02) 2px, transparent 2px)",
          backgroundSize: "80px 80px",
          opacity: 0.7,
          pointerEvents: "none",
        }}
      />

      {/* Cybernetic Scanlines */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))",
          backgroundSize: "100% 4px, 6px 100%",
          pointerEvents: "none",
          opacity: 0.4,
        }}
      />

      {/* ------------------------------------------------------------- */}
      {/* AUDIO TRACKS */}
      {/* ------------------------------------------------------------- */}
      {/* Plays the voiceover audio generated from HeyGen */}
      <Audio src={staticFile(avatarVideoUrl)} />

      {/* ------------------------------------------------------------- */}
      {/* SCENE COMPOSITIONS */}
      {/* ------------------------------------------------------------- */}

      {/* SCENE 1 - 8: MAIN COMPONENT LAYOUT (0 - 1560 frames) */}
      {frame < 1560 && (
        <AbsoluteFill
          style={{
            display: "flex",
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "center",
            padding: 50,
          }}
        >
          {/* Resume Panel wrapper with X translation slide */}
          <div
            style={{
              transform: `translateX(${resumeX}px)`,
              zIndex: 5,
              transition: "transform 0.1s ease-out",
            }}
          >
            <ResumePanel
              optimized={frame >= 1050}
              particleProgress={resumeWipeProgress}
              logoOpacity={frame >= 1050 ? 1 : 0}
            />
          </div>

          {/* ATS GATE (Closed for Scene 1-2, Scanning status) */}
          {frame < 210 && (
            <AtsGate
              status={frame < 90 ? "scanning" : "warning"}
              openProgress={0}
            />
          )}

          {/* Mascot (Enters in Scene 3 at frame 210, merges at Scene 7) */}
          {frame >= 210 && frame < 1120 && (
            <SignalMascot
              expression={
                frame >= 750 && frame < 1020
                  ? "happy"
                  : frame >= 330 && frame < 510
                  ? "focused"
                  : "neutral"
              }
              dissolveProgress={dissolveProgress}
              style={{
                position: "absolute",
                left: `calc(50% + ${mascotX}px)`,
                top: "45%",
                transform: "translate(-50%, -50%)",
                opacity: mascotOpacity,
                zIndex: 10,
              }}
            />
          )}

          {/* Scene 4: Job Description Extraction Stream */}
          {frame >= 330 && frame < 510 && <KeywordStream />}

          {/* Scene 5: Skill Gap HUD */}
          {frame >= 510 && frame < 750 && (
            <div
              style={{
                position: "absolute",
                left: "calc(50% + 180px)",
                top: "45%",
                transform: "translate(-50%, -50%)",
                zIndex: 12,
              }}
            >
              <div
                style={{
                  width: 380,
                  background: "rgba(255, 0, 85, 0.08)",
                  border: "2px solid #ff0055",
                  borderRadius: 16,
                  padding: 24,
                  boxShadow: "0 10px 30px rgba(255,0,85,0.2)",
                  backdropFilter: "blur(10px)",
                }}
              >
                <div style={{ fontFamily: "monospace", fontSize: 16, color: "#ff0055", fontWeight: 700, marginBottom: 8 }}>
                  [GAP DETECTED]
                </div>
                <h4 style={{ color: "#ffffff", margin: 0, fontSize: 24, fontWeight: 800 }}>
                  Bullet Point Too Vague
                </h4>
                <p style={{ color: "rgba(255,255,255,0.6)", fontSize: 20, margin: "10px 0 0 0", lineHeight: 1.4 }}>
                  Resume lists "Helped improve team workflow" without metrics. System cannot verify competencies.
                </p>
              </div>
            </div>
          )}

          {/* Scene 6: Bullet Point Morph Panel */}
          {frame >= 750 && frame < 1020 && (
            <BulletTransform
              progress={interpolate(frame, [780, 960], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })}
              style={{
                position: "absolute",
                left: "calc(50% + 220px)",
                top: "45%",
                transform: "translate(-50%, -50%)",
                zIndex: 12,
              }}
            />
          )}

          {/* Scene 8: ATS Clearance Checklists */}
          {frame >= 1200 && (
            <>
              {/* Checklist details panel */}
              <HudChecklist
                progress={checklistProgress}
                style={{
                  position: "absolute",
                  left: "calc(50% + 220px)",
                  top: "45%",
                  transform: "translate(-50%, -50%)",
                  zIndex: 8,
                }}
              />
              {/* Outer sliding gate */}
              <AtsGate
                status="passed"
                openProgress={gateOpenProgress}
              />
            </>
          )}
        </AbsoluteFill>
      )}

      {/* SCENE 9 & 10: HIRING MANAGER SCREEN (1560 - 2040 frames) */}
      {frame >= 1560 && frame < 2040 && <HiringManagerScene />}

      {/* SCENE 11: OUTRO & BRAND LOCKUP (2040 - 2220 frames) */}
      {frame >= 2040 && (
        <AbsoluteFill
          style={{
            zIndex: 200,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            padding: 80,
            textAlign: "center",
            background: `radial-gradient(120% 90% at 50% 15%, #08121a 0%, ${DARK} 75%, #020204 100%)`,
            opacity: ctaOpacity,
            transform: `scale(${ctaScale})`,
          }}
        >
          {/* Logo mascot pulsing */}
          <SignalMascot style={{ marginBottom: 40 }} />

          <h2
            style={{
              fontFamily: FONT,
              fontWeight: 900,
              fontSize: 90,
              color: "#ffffff",
              letterSpacing: 2,
              margin: 0,
              textShadow: "0 0 30px rgba(0,240,255,0.4)",
            }}
          >
            Signal
          </h2>

          <p
            style={{
              fontFamily: FONT,
              fontWeight: 600,
              fontSize: 34,
              color: CYAN,
              textTransform: "uppercase",
              letterSpacing: 4,
              marginTop: 16,
              marginBottom: 80,
            }}
          >
            by ATSHacker - Resume Match Optimizer
          </p>

          <div
            style={{
              fontFamily: FONT,
              fontSize: 48,
              fontWeight: 900,
              color: "#ffffff",
              background: "rgba(0, 240, 255, 0.08)",
              border: `3px solid ${CYAN}`,
              padding: "36px 72px",
              borderRadius: 30,
              boxShadow: "0 20px 50px rgba(0,240,255,0.18)",
              letterSpacing: 1,
              maxWidth: 800,
            }}
          >
            {cta}
          </div>
        </AbsoluteFill>
      )}

      {/* ------------------------------------------------------------- */}
      {/* CAPTIONS LAYER */}
      {/* ------------------------------------------------------------- */}
      <CaptionLayer />
    </AbsoluteFill>
  );
};
