import React from "react";
import { Audio } from "@remotion/media";
import {
  AbsoluteFill,
  Img,
  Easing,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { z } from "zod";
import { SignalMascot } from "./components/SignalMascot";

const FONT = '"Inter", "Helvetica Neue", Arial, sans-serif';
const CYAN = "#38d5ff";
const GREEN = "#34d399";
const TEXT = "#f8fafc";
const MUTED = "#94a3b8";

export const signalJourneyImageVideoSchema = z.object({
  slug: z.string(),
  title: z.string(),
  subtitle: z.string(),
  imageSrc: z.string(),
  cta: z.string(),
  voiceover_text: z.string().optional(),
  voiceoverSrc: z.string().optional(),
  voiceoverVolume: z.number().min(0).max(1).optional(),
  voiceoverPlaybackRate: z.number().min(0.5).max(1.5).optional(),
  musicSrc: z.string().optional(),
  musicVolume: z.number().min(0).max(1).optional(),
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
  durationSeconds: z.number().optional(),
  captionReadiness: z.any().optional(),
  audioReadiness: z.any().optional(),
});

export type SignalJourneyImageVideoProps = z.infer<typeof signalJourneyImageVideoSchema>;

export const defaultSignalJourneyImageVideoProps: SignalJourneyImageVideoProps = {
  slug: "signal-ai-gets-you-seen-video",
  title: "Signal — The AI that gets you seen",
  subtitle: "Pass the ATS. Strengthen the resume. Impress the hiring manager.",
  imageSrc: "assets/signal-ai-gets-you-seen-reference.jpg",
  cta: "Run the free Signal score before you apply.",
  musicSrc: "audio/signal-quiet-orbit.wav",
  musicVolume: 0.1,
  voiceoverVolume: 0.95,
  voiceoverPlaybackRate: 1,
};

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

const panelOpacity = (sec: number, start: number, end: number) =>
  interpolate(sec, [start - 0.4, start, end, end + 0.45], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

const PanelGlow: React.FC<{
  x: number;
  y: number;
  width: number;
  height: number;
  opacity: number;
  label: string;
}> = ({ x, y, width, height, opacity, label }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width,
      height,
      borderRadius: 10,
      border: "2px solid rgba(56,213,255,0.84)",
      boxShadow:
        "0 0 32px rgba(56,213,255,0.42), inset 0 0 52px rgba(56,213,255,0.14)",
      opacity,
    }}
  >
    <div
      style={{
        position: "absolute",
        left: 14,
        top: 10,
        padding: "5px 9px",
        borderRadius: 999,
        background: "rgba(3,7,18,0.74)",
        color: CYAN,
        fontFamily: FONT,
        fontSize: 13,
        fontWeight: 950,
        letterSpacing: 1.5,
        textTransform: "uppercase",
      }}
    >
      {label}
    </div>
  </div>
);

const CaptionBar: React.FC<{ text: string; fallback: string; opacity: number }> = ({
  text,
  fallback,
  opacity,
}) => (
  <div
    style={{
      position: "absolute",
      left: 170,
      right: 170,
      bottom: 72,
      padding: "13px 20px",
      borderRadius: 18,
      border: "1px solid rgba(56,213,255,0.28)",
      background: "rgba(3,7,18,0.78)",
      boxShadow: "0 18px 56px rgba(0,0,0,0.44), inset 0 0 22px rgba(56,213,255,0.06)",
      textAlign: "center",
      opacity,
    }}
  >
    <div
      style={{
        color: TEXT,
        fontFamily: FONT,
        fontSize: 26,
        fontWeight: 950,
        letterSpacing: 0,
        lineHeight: 1.08,
        textTransform: "uppercase",
      }}
    >
      {text || fallback}
    </div>
  </div>
);

const ScorePulse: React.FC<{ opacity: number }> = ({ opacity }) => (
  <div
    style={{
      position: "absolute",
      left: 58,
      bottom: 116,
      width: 224,
      height: 112,
      borderRadius: 18,
      border: "1px solid rgba(52,211,153,0.36)",
      background: "rgba(5,22,28,0.62)",
      boxShadow: "0 0 32px rgba(52,211,153,0.28), inset 0 0 24px rgba(52,211,153,0.10)",
      opacity,
      display: "grid",
      placeItems: "center",
      fontFamily: FONT,
      color: GREEN,
    }}
  >
    <div style={{ textAlign: "center" }}>
      <div style={{ color: MUTED, fontSize: 13, fontWeight: 900, textTransform: "uppercase" }}>
        ATS Match
      </div>
      <div style={{ fontSize: 48, lineHeight: 1, fontWeight: 950 }}>94%</div>
      <div style={{ color: "#a7f3d0", fontSize: 13, fontWeight: 850 }}>Excellent match</div>
    </div>
  </div>
);

const KeywordStream: React.FC<{ progress: number; opacity: number }> = ({ progress, opacity }) => (
  <svg
    width="1280"
    height="720"
    viewBox="0 0 1280 720"
    style={{ position: "absolute", inset: 0, opacity, pointerEvents: "none" }}
  >
    {["Leadership", "Agile", "Results", "Impact"].map((word, index) => {
      const x = interpolate(progress, [0, 1], [410, 548 + index * 10], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
      const y = interpolate(progress, [0, 1], [206 + index * 56, 288 + index * 36], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
      return (
        <g key={word}>
          <text
            x={x}
            y={y}
            fill={index % 2 ? "#84f7cb" : CYAN}
            fontFamily={FONT}
            fontSize="15"
            fontWeight="900"
          >
            {word}
          </text>
          <circle cx={x - 10} cy={y - 5} r="3" fill={CYAN} opacity="0.8" />
        </g>
      );
    })}
  </svg>
);

export const SignalJourneyImageVideo: React.FC<SignalJourneyImageVideoProps> = ({
  imageSrc,
  cta,
  voiceoverSrc,
  voiceoverVolume = 0.95,
  voiceoverPlaybackRate = 1,
  musicSrc,
  musicVolume = 0.1,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const sec = frame / fps;

  const left = panelOpacity(sec, 3.0, 9.0);
  const center = panelOpacity(sec, 9.0, 16.0);
  const right = panelOpacity(sec, 16.0, 22.4);
  const ctaOpacity = clampFade(frame, Math.max(0, durationInFrames - 138), Math.max(1, durationInFrames - 92));
  const pathProgress = interpolate(frame, [90, durationInFrames - 100], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const mascotX = interpolate(sec, [0, 2.8, 7.8, 12.8, 18.8, 23.5], [120, 215, 230, 585, 960, 1040], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const mascotY = interpolate(sec, [0, 2.8, 7.8, 12.8, 18.8, 23.5], [52, 58, 346, 318, 350, 620], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const mascotScale = interpolate(sec, [0, 3, 12, 20, 24], [0.92, 0.66, 0.58, 0.5, 0.44], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const sceneCaption =
    sec < 7
      ? "Signal checks formatting, keywords, experience, and relevance."
      : sec < 15
        ? "Then it pulls real proof into the resume."
        : sec < 22
          ? "The cleaner story lands on the hiring manager screen."
          : cta;

  return (
    <AbsoluteFill style={{ background: "#020617", fontFamily: FONT, overflow: "hidden" }}>
      {musicSrc ? <Audio src={staticFile(musicSrc)} volume={musicVolume} /> : null}
      {voiceoverSrc ? (
        <Audio src={staticFile(voiceoverSrc)} volume={voiceoverVolume} playbackRate={voiceoverPlaybackRate} />
      ) : null}

      <Img
        src={staticFile(imageSrc)}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          opacity: 0.9,
          filter: "saturate(1.15) contrast(1.08)",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 16% 10%, rgba(56,213,255,0.24), transparent 18rem), radial-gradient(circle at 75% 54%, rgba(52,211,153,0.10), transparent 18rem), linear-gradient(180deg, rgba(2,6,23,0.08), rgba(2,6,23,0.34))",
        }}
      />

      <PanelGlow x={20} y={109} width={356} height={512} opacity={left} label="1 / pass the ATS" />
      <PanelGlow x={384} y={109} width={432} height={512} opacity={center} label="2 / merge proof" />
      <PanelGlow x={824} y={109} width={438} height={512} opacity={right} label="3 / human review" />

      <svg width="1280" height="720" viewBox="0 0 1280 720" style={{ position: "absolute", inset: 0 }}>
        <path
          d="M 58 492 C 220 420, 254 270, 344 338 C 430 402, 470 206, 592 290 C 705 368, 768 365, 832 310 C 912 242, 1014 250, 1124 326"
          fill="none"
          stroke="rgba(56,213,255,0.72)"
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray="1100"
          strokeDashoffset={1100 - 1100 * pathProgress}
          style={{ filter: "drop-shadow(0 0 18px rgba(56,213,255,0.82))" }}
        />
        <path
          d="M 58 512 C 230 442, 274 290, 350 350 C 440 420, 486 238, 604 310 C 704 370, 756 376, 824 330 C 928 260, 1036 275, 1144 348"
          fill="none"
          stroke="rgba(52,211,153,0.46)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray="980"
          strokeDashoffset={980 - 980 * pathProgress}
        />
      </svg>

      <ScorePulse opacity={left} />
      <KeywordStream progress={clampFade(frame, 270, 420)} opacity={center} />

      <div
        style={{
          position: "absolute",
          left: 895,
          top: 245,
          width: 250,
          height: 190,
          borderRadius: 20,
          background: `radial-gradient(circle at 48% 48%, rgba(56,213,255,${0.34 * right}), rgba(56,213,255,0) 68%)`,
          boxShadow: `0 0 ${70 * right}px rgba(56,213,255,${0.22 * right})`,
          opacity: right,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 875,
          top: 236 + Math.sin(frame * 0.06) * 8,
          width: 292,
          height: 3,
          background: "linear-gradient(90deg, transparent, rgba(56,213,255,0.9), transparent)",
          boxShadow: "0 0 24px rgba(56,213,255,0.75)",
          opacity: right,
        }}
      />

      <div
        style={{
          position: "absolute",
          left: mascotX,
          top: mascotY + Math.sin(frame * 0.07) * 5,
          transform: `translate(-50%, -50%) scale(${mascotScale})`,
          filter: "drop-shadow(0 0 22px rgba(56,213,255,0.85))",
          zIndex: 50,
        }}
      >
        <SignalMascot expression={right > 0.6 ? "happy" : "focused"} style={{ width: 150, height: 150 }} />
      </div>

      <CaptionBar text="" fallback={sceneCaption} opacity={exitFade(frame, durationInFrames - 42, durationInFrames - 8)} />

      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: ctaOpacity,
          background: "radial-gradient(circle at 50% 50%, rgba(3,7,18,0.20), rgba(3,7,18,0.84))",
          display: "grid",
          placeItems: "center",
          textAlign: "center",
          pointerEvents: "none",
        }}
      >
        <div>
          <SignalMascot expression="happy" style={{ width: 110, height: 110, margin: "0 auto 18px" }} />
          <div style={{ color: TEXT, fontSize: 47, lineHeight: 1, fontWeight: 950, textTransform: "uppercase" }}>
            Signal gets the resume seen.
          </div>
          <div style={{ color: CYAN, fontSize: 27, fontWeight: 900, marginTop: 12 }}>{cta}</div>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          boxShadow: "inset 0 0 85px rgba(0,0,0,0.72)",
        }}
      />
    </AbsoluteFill>
  );
};
