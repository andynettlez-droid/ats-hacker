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
import { SignalMascot } from "./components/SignalMascot";
import type { ResumeCrimeSceneProps } from "./ResumeCrimeScene";

const FONT = '"Inter", "Helvetica Neue", Arial, sans-serif';
const INK = "#172033";
const MUTED_INK = "#475569";
const PAPER = "#fbfaf5";
const RED = "#d92d20";
const GREEN = "#15803d";
const YELLOW = "#fde68a";

const palettes = {
  stickyNote: {
    desk: "#6b4a2f",
    deskDark: "#3d291a",
    accent: "#f59e0b",
    note: "#fef3c7",
    tape: "rgba(251, 191, 36, 0.55)",
  },
  terminal: {
    desk: "#263241",
    deskDark: "#111827",
    accent: "#22c55e",
    note: "#dcfce7",
    tape: "rgba(34, 197, 94, 0.42)",
  },
  highlighter: {
    desk: "#d8c3a5",
    deskDark: "#8a6f51",
    accent: "#06b6d4",
    note: "#ecfeff",
    tape: "rgba(6, 182, 212, 0.34)",
  },
  neon: {
    desk: "#334155",
    deskDark: "#0f172a",
    accent: "#38d5ff",
    note: "#e0f2fe",
    tape: "rgba(56, 213, 255, 0.30)",
  },
  comic: {
    desk: "#754021",
    deskDark: "#3f2314",
    accent: "#ef4444",
    note: "#fee2e2",
    tape: "rgba(248, 113, 113, 0.38)",
  },
} as const;

type VisualStyle = keyof typeof palettes;

const clampWords = (text: string, max = 8) => {
  const words = text.trim().split(/\s+/).filter(Boolean);
  if (words.length <= max) return text;
  return `${words.slice(0, max).join(" ")}...`;
};

const getScoreRubric = (props: ResumeCrimeSceneProps) => props.score_rubric || props.scoreRubric;

const scoreRows = (props: ResumeCrimeSceneProps) => {
  const rubric = getScoreRubric(props);
  if (rubric && Array.isArray(rubric.rows) && rubric.rows.length) {
    return rubric.rows.slice(0, 4).map((row: any) => ({
      label: row.criterion || row.label || "Score item",
      before: `${row.before}/${row.max}`,
      after: `${row.after}/${row.max}`,
      beforeReason: row.beforeReason,
      afterReason: row.afterReason,
    }));
  }
  return (props.scoreBasis?.slice(0, 4) || [
    { label: "Tool match", before: "missing", after: "visible" },
    { label: "Metric proof", before: "missing", after: "visible" },
    { label: "Outcome", before: "vague", after: "clear" },
  ]).map((row) => ({
    label: row.label,
    before: row.before,
    after: row.after,
    beforeReason: row.before,
    afterReason: row.after,
  }));
};

const stageOpacity = (frame: number, start: number, end: number) => {
  const fadeIn = interpolate(frame, [start, start + 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const fadeOut = interpolate(frame, [end - 16, end], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return fadeIn * fadeOut;
};

const useTimings = () => {
  const { durationInFrames } = useVideoConfig();
  const at = (ratio: number) => Math.round(durationInFrames * ratio);
  return {
    hook: [0, at(0.14)] as const,
    read: [at(0.12), at(0.42)] as const,
    reason: [at(0.36), at(0.61)] as const,
    fix: [at(0.55), at(0.82)] as const,
    cta: [at(0.78), durationInFrames] as const,
  };
};

const ShortCaption: React.FC<{ captions?: ResumeCrimeSceneProps["captions"] }> = ({ captions = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const now = (frame / fps) * 1000;
  const activeIndex = captions.findIndex((caption) => now >= caption.startMs && now <= caption.endMs + 180);
  if (activeIndex < 0) return null;
  const slice = captions.slice(Math.max(0, activeIndex - 2), activeIndex + 5);
  const text = slice.map((caption) => caption.text).join(" ");
  return (
    <div
      style={{
        position: "absolute",
        left: 78,
        right: 78,
        bottom: 168,
        padding: "14px 20px",
        borderRadius: 20,
        background: "rgba(15, 23, 42, 0.86)",
        color: "white",
        fontFamily: FONT,
        fontSize: 43,
        lineHeight: 1.05,
        fontWeight: 950,
        textAlign: "center",
        textTransform: "uppercase",
        textShadow: "0 3px 0 rgba(0,0,0,0.52)",
        border: "2px solid rgba(255,255,255,0.12)",
        boxShadow: "0 18px 50px rgba(0,0,0,0.35)",
        letterSpacing: 0,
      }}
    >
      {clampWords(text, 7)}
    </div>
  );
};

const DeskTexture: React.FC<{ palette: (typeof palettes)[VisualStyle] }> = ({ palette }) => (
  <AbsoluteFill
    style={{
      background:
        `radial-gradient(circle at 22% 16%, rgba(255,255,255,0.16), transparent 20rem), linear-gradient(135deg, ${palette.desk}, ${palette.deskDark})`,
    }}
  >
    <div
      style={{
        position: "absolute",
        inset: 0,
        opacity: 0.18,
        backgroundImage:
          "repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0 2px, transparent 2px 36px), repeating-linear-gradient(0deg, rgba(0,0,0,0.08) 0 1px, transparent 1px 7px)",
      }}
    />
    <div
      style={{
        position: "absolute",
        left: -80,
        right: -80,
        top: 584,
        height: 34,
        transform: "rotate(-3deg)",
        background: "rgba(0,0,0,0.12)",
        filter: "blur(16px)",
      }}
    />
  </AbsoluteFill>
);

const Paper: React.FC<{
  x: number;
  y: number;
  rotate: number;
  scale?: number;
  children: React.ReactNode;
  width?: number;
  height?: number;
}> = ({ x, y, rotate, scale = 1, width = 650, height = 860, children }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width,
      minHeight: height,
      padding: "34px 38px",
      transform: `rotate(${rotate}deg) scale(${scale})`,
      transformOrigin: "center",
      borderRadius: 12,
      background: PAPER,
      color: INK,
      boxShadow: "0 36px 95px rgba(0,0,0,0.36)",
      border: "1px solid rgba(15,23,42,0.12)",
      fontFamily: FONT,
    }}
  >
    <div
      style={{
        position: "absolute",
        left: 190,
        top: -15,
        width: 210,
        height: 34,
        borderRadius: 6,
        background: "rgba(236, 210, 163, 0.72)",
        transform: "rotate(2deg)",
      }}
    />
    {children}
  </div>
);

const ResumePaper: React.FC<{
  props: ResumeCrimeSceneProps;
  marked: boolean;
  fixed: boolean;
  compact?: boolean;
}> = ({ props, marked, fixed, compact }) => {
  const doc = props.resumeDocument;
  const bullets = doc?.experience?.[0]?.bullets || props.weakBullets || [];
  const displayBullets = bullets.slice(0, compact ? 3 : 4);
  return (
    <>
      <div style={{ fontSize: 33, fontWeight: 950, lineHeight: 1, letterSpacing: 0 }}>{doc?.name || props.resumeName}</div>
      <div style={{ marginTop: 7, color: MUTED_INK, fontSize: 16, fontWeight: 850 }}>{doc?.headline || props.resumeTitle}</div>
      <div style={{ height: 2, background: INK, margin: "19px 0 14px" }} />
      <div style={{ fontSize: 12, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.5 }}>Experience</div>
      <div style={{ marginTop: 9, display: "grid", gap: 10 }}>
        <div style={{ fontSize: 15, fontWeight: 950 }}>{doc?.experience?.[0]?.role || props.resumeTitle}</div>
        <div style={{ marginTop: -6, fontSize: 12, color: MUTED_INK, fontWeight: 850 }}>
          {doc?.experience?.[0]?.company || "Previous Company"} | {doc?.experience?.[0]?.dates || "2023 - Present"}
        </div>
        {displayBullets.map((bullet) => {
          const isTarget = bullet === props.beforeBullet;
          const shown = fixed && isTarget ? props.afterBullet : bullet;
          return (
            <div
              key={bullet}
              style={{
                position: "relative",
                padding: isTarget ? "8px 10px 8px 24px" : "3px 0 3px 20px",
                borderRadius: 11,
                background: isTarget && fixed ? "rgba(22,163,74,0.14)" : isTarget && marked ? "rgba(254,226,226,0.82)" : "transparent",
                border: isTarget && fixed ? "2px solid rgba(22,163,74,0.38)" : isTarget && marked ? "2px solid rgba(217,45,32,0.38)" : "2px solid transparent",
                color: INK,
                fontSize: isTarget ? 15 : 13.2,
                lineHeight: 1.28,
                fontWeight: isTarget ? 870 : 650,
              }}
            >
              <span
                style={{
                  position: "absolute",
                  left: isTarget ? 9 : 4,
                  top: isTarget ? 16 : 10,
                  width: 5,
                  height: 5,
                  borderRadius: 99,
                  background: isTarget && fixed ? GREEN : INK,
                }}
              />
              {shown}
              {isTarget && marked ? (
                <div
                  style={{
                    position: "absolute",
                    inset: -10,
                    borderRadius: 20,
                    border: `5px solid ${RED}`,
                    transform: "rotate(-1.8deg)",
                    opacity: 0.88,
                  }}
                />
              ) : null}
            </div>
          );
        })}
      </div>
      <div style={{ marginTop: 24, fontSize: 12, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.5 }}>Skills</div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 9 }}>
        {(doc?.skills || props.jobKeywords || []).slice(0, 6).map((skill) => (
          <span key={skill} style={{ padding: "5px 8px", borderRadius: 999, background: "#e2e8f0", color: "#334155", fontSize: 11, fontWeight: 850 }}>
            {skill}
          </span>
        ))}
      </div>
    </>
  );
};

const JobPostPaper: React.FC<{ props: ResumeCrimeSceneProps; accent: string }> = ({ props, accent }) => {
  const jd = props.jobDescription;
  const keywords = props.jobKeywords.slice(0, 4);
  return (
    <>
      <div style={{ fontSize: 13, fontWeight: 950, textTransform: "uppercase", color: accent, letterSpacing: 1.4 }}>Job post</div>
      <div style={{ marginTop: 8, fontSize: 24, fontWeight: 950, lineHeight: 1.05 }}>{jd?.title || props.jobTitle}</div>
      <div style={{ marginTop: 8, fontSize: 13, color: MUTED_INK, lineHeight: 1.34, fontWeight: 650 }}>
        {jd?.summary || "The job description tells you what a reviewer will search for first."}
      </div>
      <div style={{ display: "grid", gap: 9, marginTop: 18 }}>
        {keywords.map((keyword, index) => (
          <div
            key={keyword}
            style={{
              padding: "9px 10px",
              borderRadius: 10,
              background: index < 3 ? YELLOW : "#e2e8f0",
              color: INK,
              fontSize: 14,
              fontWeight: 950,
              boxShadow: index < 3 ? "inset 0 -8px 0 rgba(250,204,21,0.35)" : "none",
            }}
          >
            {keyword}
          </div>
        ))}
      </div>
    </>
  );
};

const StickyScore: React.FC<{
  label: string;
  value: string;
  tone?: "bad" | "good";
  top: number;
  left: number;
  rotate?: number;
  palette: (typeof palettes)[VisualStyle];
}> = ({ label, value, tone = "bad", top, left, rotate = -3, palette }) => (
  <div
    style={{
      position: "absolute",
      top,
      left,
      width: 260,
      minHeight: 170,
      padding: 18,
      borderRadius: 6,
      transform: `rotate(${rotate}deg)`,
      background: tone === "good" ? "#dcfce7" : palette.note,
      color: INK,
      boxShadow: "0 24px 50px rgba(0,0,0,0.24)",
      fontFamily: FONT,
      border: "1px solid rgba(15,23,42,0.10)",
    }}
  >
    <div style={{ position: "absolute", top: -13, left: 62, width: 125, height: 26, background: palette.tape, borderRadius: 4 }} />
    <div style={{ color: tone === "good" ? GREEN : RED, fontSize: 15, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.2 }}>
      {label}
    </div>
    <div style={{ marginTop: 8, fontSize: 50, fontWeight: 950, lineHeight: 0.92 }}>{value}</div>
  </div>
);

const ReasonCard: React.FC<{ props: ResumeCrimeSceneProps; palette: (typeof palettes)[VisualStyle] }> = ({ props, palette }) => {
  const rubric = getScoreRubric(props);
  const rows = scoreRows(props);
  return (
    <div
      style={{
        position: "absolute",
        left: 74,
        top: 1118,
        width: 510,
        padding: 18,
        borderRadius: 18,
        background: "rgba(255,255,255,0.93)",
        boxShadow: "0 28px 80px rgba(0,0,0,0.30)",
        fontFamily: FONT,
        color: INK,
        border: `4px solid ${palette.accent}`,
      }}
    >
      <div style={{ fontSize: 15, fontWeight: 950, color: RED, textTransform: "uppercase", letterSpacing: 1.2 }}>
        Score receipt before
      </div>
      <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
        {rows.map((row: { label: string; before: string; beforeReason: string }) => (
          <div key={row.label} style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 12, alignItems: "center", fontSize: 14 }}>
            <span style={{ fontWeight: 950 }}>{row.label}</span>
            <span style={{ color: RED, fontWeight: 950 }}>{row.before}</span>
            <span style={{ gridColumn: "1 / -1", color: MUTED_INK, fontSize: 12, fontWeight: 800 }}>{row.beforeReason}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const RewriteCard: React.FC<{ props: ResumeCrimeSceneProps; palette: (typeof palettes)[VisualStyle] }> = ({ props, palette }) => {
  const rubric = getScoreRubric(props);
  const rows = scoreRows(props);
  return (
    <div
      style={{
        position: "absolute",
        right: 66,
        top: 1030,
        width: 520,
        padding: 20,
        borderRadius: 18,
        background: "#f0fdf4",
        color: INK,
        fontFamily: FONT,
        boxShadow: "0 28px 80px rgba(0,0,0,0.30)",
        border: "4px solid rgba(22,163,74,0.52)",
      }}
    >
      <div style={{ fontSize: 15, fontWeight: 950, color: GREEN, textTransform: "uppercase", letterSpacing: 1.2 }}>
        Score receipt after
      </div>
      <div style={{ marginTop: 10, fontSize: 20, lineHeight: 1.22, fontWeight: 900 }}>{props.afterBullet}</div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 13 }}>
        {rows.map((row: { label: string; after: string }) => (
          <span key={row.label} style={{ background: palette.note, color: GREEN, borderRadius: 999, padding: "6px 10px", fontSize: 12, fontWeight: 950 }}>
            {row.label}: {row.after}
          </span>
        ))}
      </div>
    </div>
  );
};

const ReviewerHand: React.FC<{ visible: number; x: number; y: number; rotate: number }> = ({ visible, x, y, rotate }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      opacity: visible,
      transform: `rotate(${rotate}deg)`,
      transformOrigin: "70% 30%",
      filter: "drop-shadow(0 18px 24px rgba(0,0,0,0.22))",
    }}
  >
    <div
      style={{
        width: 250,
        height: 88,
        borderRadius: "60px 28px 26px 60px",
        background: "linear-gradient(90deg, #c98f68, #e7b28b)",
      }}
    />
    <div
      style={{
        position: "absolute",
        right: -35,
        top: 25,
        width: 170,
        height: 14,
        borderRadius: 10,
        background: "#111827",
        transform: "rotate(-18deg)",
      }}
    />
    <div
      style={{
        position: "absolute",
        right: -60,
        top: 18,
        width: 55,
        height: 25,
        clipPath: "polygon(0 0, 100% 50%, 0 100%)",
        background: RED,
        transform: "rotate(-18deg)",
      }}
    />
  </div>
);

export const ResumeDeskReview: React.FC<ResumeCrimeSceneProps> = (props) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const timings = useTimings();
  const styleName = (props.visualStyle || "stickyNote") as VisualStyle;
  const palette = palettes[styleName] || palettes.stickyNote;
  const pop = spring({ frame, fps, config: { damping: 20, mass: 0.7 } });
  const paperScale = interpolate(frame, [0, 24], [0.92, 1], { extrapolateRight: "clamp" });
  const markVisible = stageOpacity(frame, timings.read[0], timings.reason[1]);
  const reasonVisible = stageOpacity(frame, timings.reason[0], timings.fix[0] + 8);
  const fixVisible = stageOpacity(frame, timings.fix[0], timings.cta[0] + 12);
  const beforeScoreVisible = stageOpacity(frame, timings.reason[0] + 18, timings.fix[0] + 8);
  const afterScoreVisible = stageOpacity(frame, timings.fix[0] + 18, timings.cta[0] + 12);
  const ctaVisible = interpolate(frame, [timings.cta[0], timings.cta[0] + 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const progress = frame / Math.max(1, durationInFrames);
  const mascotExpression = progress < 0.35 ? "concerned" : progress < 0.7 ? "focused" : "happy";

  return (
    <AbsoluteFill style={{ fontFamily: FONT, overflow: "hidden" }}>
      <DeskTexture palette={palette} />
      {props.musicSrc ? <Audio src={staticFile(props.musicSrc)} volume={props.musicVolume ?? 0.12} /> : null}
      {props.voiceoverSrc ? <Audio src={staticFile(props.voiceoverSrc)} volume={props.voiceoverVolume ?? 0.94} /> : null}

      <div
        style={{
          position: "absolute",
          top: 42,
          left: 50,
          right: 50,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          color: "rgba(255,255,255,0.88)",
          fontFamily: FONT,
          fontWeight: 950,
          textTransform: "uppercase",
          letterSpacing: 1.2,
          fontSize: 22,
        }}
      >
        <span>{props.seriesLabel || "Live resume review"}</span>
        <span style={{ color: palette.accent }}>Signal</span>
      </div>

      <div
        style={{
          position: "absolute",
          top: 92,
          left: 58,
          right: 58,
          color: "white",
          fontSize: 74,
          lineHeight: 0.92,
          fontWeight: 950,
          textShadow: "0 7px 22px rgba(0,0,0,0.35)",
          opacity: stageOpacity(frame, timings.hook[0], timings.hook[1] + 18),
          transform: `translateY(${interpolate(pop, [0, 1], [20, 0])}px)`,
          letterSpacing: 0,
        }}
      >
        {props.hook}
      </div>

      <Paper x={78} y={242} rotate={-2.3} scale={paperScale}>
        <ResumePaper props={props} marked={markVisible > 0.04} fixed={fixVisible > 0.18} />
      </Paper>

      <Paper x={638} y={296} rotate={4.2} scale={0.78} width={410} height={500}>
        <JobPostPaper props={props} accent={palette.accent} />
      </Paper>

      <ReviewerHand visible={markVisible} x={636} y={768} rotate={-14} />

      <div style={{ opacity: reasonVisible }}>
        <ReasonCard props={props} palette={palette} />
        <div style={{ opacity: beforeScoreVisible }}>
          <StickyScore label={props.scoreLabel || "Signal Fit"} value={`${props.beforeScore}/100`} top={792} left={752} palette={palette} />
        </div>
      </div>

      <div style={{ opacity: fixVisible }}>
        <RewriteCard props={props} palette={palette} />
        <div style={{ opacity: afterScoreVisible }}>
          <StickyScore
            label="After proof"
            value={`${props.afterScore}/100`}
            tone="good"
            top={780}
            left={742}
            rotate={2.4}
            palette={palette}
          />
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 52,
          bottom: 52,
          opacity: ctaVisible,
          display: "flex",
          alignItems: "center",
          gap: 18,
          color: "white",
        }}
      >
        <div style={{ width: 118, height: 118, borderRadius: 999, background: "rgba(255,255,255,0.13)", display: "grid", placeItems: "center" }}>
          <SignalMascot
            expression={mascotExpression}
            gesture="pointRight"
            speaking={Boolean(props.voiceoverSrc)}
            style={{ width: 122, height: 122 }}
          />
        </div>
        <div
          style={{
            width: 650,
            padding: "18px 22px",
            borderRadius: 22,
            background: "rgba(15,23,42,0.88)",
            border: `3px solid ${palette.accent}`,
            boxShadow: "0 24px 70px rgba(0,0,0,0.35)",
            fontFamily: FONT,
          }}
        >
          <div style={{ color: palette.accent, fontSize: 17, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.1 }}>Before you apply</div>
          <div style={{ marginTop: 4, fontSize: 35, lineHeight: 1.05, fontWeight: 950 }}>{props.cta}</div>
        </div>
      </div>

      <ShortCaption captions={props.captions} />
    </AbsoluteFill>
  );
};
