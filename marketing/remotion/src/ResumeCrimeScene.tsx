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
  formatArchetype: z.enum(["deskMarkup", "recruiterSearch", "splitTranslation", "redTeamAudit", "mascotAssist"]).optional(),
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
  resumeName: z.string().optional(),
  resumeTitle: z.string(),
  resumeMeta: z.array(z.string()).optional(),
  jobTitle: z.string(),
  jobKeywords: z.array(z.string()),
  weakBullets: z.array(z.string()),
  beforeBullet: z.string(),
  afterBullet: z.string(),
  resumeDocument: z
    .object({
      name: z.string(),
      headline: z.string(),
      contact: z.array(z.string()),
      summary: z.string(),
      experience: z.array(
        z.object({
          company: z.string(),
          role: z.string(),
          dates: z.string(),
          bullets: z.array(z.string()),
        }),
      ),
      skills: z.array(z.string()),
      education: z.string(),
    })
    .optional(),
  jobDescription: z
    .object({
      title: z.string(),
      company: z.string(),
      summary: z.string(),
      responsibilities: z.array(z.string()),
      requirements: z.array(z.string()),
      searchQueries: z.array(z.string()).optional(),
    })
    .optional(),
  beforeScore: z.number(),
  afterScore: z.number(),
  scoreBasis: z
    .array(
      z.object({
        label: z.string(),
        before: z.string(),
        after: z.string(),
      }),
    )
    .optional(),
  score_rubric: z
    .object({
      label: z.string().optional(),
      scale: z.number().optional(),
      beforeTotal: z.number(),
      afterTotal: z.number(),
      beforeExplanation: z.string().optional(),
      afterExplanation: z.string().optional(),
      rows: z.array(
        z.object({
          criterion: z.string().optional(),
          label: z.string().optional(),
          max: z.number(),
          before: z.number(),
          after: z.number(),
          beforeReason: z.string(),
          afterReason: z.string(),
        }),
      ),
    })
    .optional(),
  scoreRubric: z.any().optional(),
  scoreLabel: z.string().optional(),
  humanReadBeats: z
    .array(
      z.object({
        beat: z.string(),
        text: z.string(),
      }),
    )
    .optional(),
  voiceDirector: z.any().optional(),
  cta: z.string(),
  musicSrc: z.string().optional(),
  musicVolume: z.number().min(0).max(1).optional(),
  voiceoverSrc: z.string().optional(),
  voiceoverVolume: z.number().min(0).max(1).optional(),
  durationSeconds: z.number().min(18).max(36).optional(),
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
  captionReadiness: z
    .object({
      wordLevel: z.boolean().optional(),
      provider: z.string().optional(),
      alignmentRef: z.string().optional(),
      reason: z.string().optional(),
    })
    .optional(),
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
  formatArchetype: "deskMarkup",
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
  resumeName: "Avery Johnson",
  resumeTitle: "Marketing Specialist Resume",
  resumeMeta: ["3 yrs B2B SaaS", "HubSpot admin", "Paid social support"],
  jobTitle: "Demand Generation Manager",
  jobKeywords: ["Demand Gen", "LinkedIn Ads", "HubSpot", "CAC analysis"],
  weakBullets: ["Responsible for social media.", "Helped with marketing campaigns.", "Worked with the team."],
  beforeBullet: "Helped with marketing campaigns.",
  afterBullet: "Cut CAC by 32% through LinkedIn Ads audience segmentation and HubSpot lead scoring.",
  resumeDocument: {
    name: "Avery Johnson",
    headline: "Marketing Specialist",
    contact: ["Austin, TX", "avery.johnson@example.com", "linkedin.com/in/avery-johnson"],
    summary: "B2B SaaS marketer supporting lifecycle campaigns, webinars, paid social launches, and HubSpot reporting for revenue teams.",
    experience: [
      {
        company: "Northstar Analytics",
        role: "Marketing Coordinator",
        dates: "2023 - Present",
        bullets: [
          "Supported email and social campaigns across multiple channels.",
          "Helped with marketing campaigns.",
          "Pulled weekly Salesforce campaign reports for marketing and sales leadership.",
        ],
      },
      {
        company: "CedarCloud Software",
        role: "Marketing Assistant",
        dates: "2021 - 2023",
        bullets: [
          "Built event landing pages and tracked registrations through HubSpot forms.",
          "Updated campaign calendars for product launches and customer webinars.",
        ],
      },
    ],
    skills: ["HubSpot", "Salesforce reports", "LinkedIn Ads", "Lifecycle email", "UTM tracking"],
    education: "B.A. Marketing, University of Texas at Austin",
  },
  jobDescription: {
    title: "Demand Generation Manager",
    company: "TargetCo",
    summary: "TargetCo needs a demand generation manager who can connect campaign execution to measurable pipeline outcomes.",
    responsibilities: [
      "Use HubSpot workflows and LinkedIn Ads to improve lifecycle campaigns.",
      "Analyze CAC, MQL-to-SQL conversion, and pipeline sourced by campaign.",
      "Partner with sales and marketing operations on reporting.",
    ],
    requirements: ["HubSpot workflows", "LinkedIn Ads", "CAC analysis", "MQL-to-SQL", "pipeline sourced"],
    searchQueries: ["HubSpot", "CAC", "LinkedIn Ads", "pipeline"],
  },
  beforeScore: 34,
  afterScore: 92,
  scoreBasis: [
    { label: "Keyword match", before: "1/5", after: "5/5" },
    { label: "Metric proof", before: "missing", after: "CAC -32%" },
    { label: "Outcome", before: "vague", after: "MQL +18%" },
  ],
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
      "radial-gradient(circle at 20% 12%, rgba(239,68,68,0.15), transparent 26rem), radial-gradient(circle at 86% 20%, rgba(250,204,21,0.18), transparent 30rem), linear-gradient(180deg, #fff7ed 0%, #fee2e2 48%, #111827 100%)",
    accent: "#b91c1c",
    warning: "#dc2626",
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
      "radial-gradient(circle at 14% 12%, rgba(45,212,191,0.18), transparent 28rem), radial-gradient(circle at 86% 18%, rgba(250,204,21,0.22), transparent 32rem), linear-gradient(180deg, #ecfeff 0%, #fef9c3 42%, #0f172a 100%)",
    accent: "#0f766e",
    warning: "#ca8a04",
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

type TimingRange = readonly [number, number];
type TimingPlan = {
  hook: TimingRange;
  problem: TimingRange;
  teardown: TimingRange;
  fix: TimingRange;
  cta: TimingRange;
};

const buildTiming = (durationFrames: number, pace: keyof typeof PACE): TimingPlan => {
  const usable = Math.max(18 * 30, durationFrames);
  const profiles = {
    fast: [0, 0.15, 0.37, 0.62, 0.84, 1],
    balanced: [0, 0.17, 0.39, 0.64, 0.84, 1],
    slowBurn: [0, 0.2, 0.42, 0.66, 0.84, 1],
  } as const;
  const profile = profiles[pace] || profiles.balanced;
  const frameAt = (ratio: number) => Math.round(usable * ratio);
  return {
    hook: [frameAt(profile[0]), frameAt(profile[1])],
    problem: [frameAt(profile[1]) + 4, frameAt(profile[2])],
    teardown: [frameAt(profile[2]) + 4, frameAt(profile[3])],
    fix: [frameAt(profile[3]) + 4, frameAt(profile[4])],
    cta: [frameAt(profile[4]) + 4, frameAt(profile[5])],
  };
};

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

const ScoreReceipt: React.FC<{
  basis?: ResumeCrimeSceneProps["scoreBasis"];
  beforeScore: number;
  afterScore: number;
  phase: "before" | "after";
  accent: string;
}> = ({ basis = [], beforeScore, afterScore, phase, accent }) => {
  const rows = basis.length
    ? basis
    : [
        { label: "Keyword match", before: "weak", after: "strong" },
        { label: "Metric proof", before: "missing", after: "visible" },
        { label: "Outcome", before: "vague", after: "clear" },
      ];
  const isAfter = phase === "after";
  return (
    <div
      style={{
        width: 392,
        padding: "16px 18px",
        borderRadius: 22,
        background: "rgba(2,6,23,0.90)",
        border: `2px solid ${isAfter ? "rgba(22,163,74,0.38)" : "rgba(220,38,38,0.34)"}`,
        boxShadow: "0 24px 70px rgba(0,0,0,0.42)",
        color: TEXT,
      }}
    >
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 16 }}>
        <div style={{ color: accent, fontSize: 14, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.3 }}>
          Score receipt
        </div>
        <div style={{ color: isAfter ? "#bbf7d0" : "#fecaca", fontSize: 24, fontWeight: 950 }}>
          {isAfter ? afterScore : beforeScore}/100
        </div>
      </div>
      <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
        {rows.slice(0, 3).map((row) => (
          <div
            key={row.label}
            style={{
              display: "grid",
              gridTemplateColumns: "1fr auto",
              gap: 10,
              alignItems: "center",
              padding: "9px 10px",
              borderRadius: 13,
              background: isAfter ? "rgba(22,163,74,0.11)" : "rgba(220,38,38,0.10)",
              border: isAfter ? "1px solid rgba(22,163,74,0.20)" : "1px solid rgba(220,38,38,0.18)",
            }}
          >
            <div style={{ color: "#e2e8f0", fontSize: 15, lineHeight: 1.05, fontWeight: 900 }}>{row.label}</div>
            <div
              style={{
                color: isAfter ? "#bbf7d0" : "#fecaca",
                fontSize: 14,
                lineHeight: 1.05,
                fontWeight: 950,
                textAlign: "right",
                maxWidth: 154,
              }}
            >
              {isAfter ? row.after : row.before}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const ResumeSheet: React.FC<{
  name?: string;
  title: string;
  meta?: string[];
  bullets: string[];
  resumeDocument?: ResumeCrimeSceneProps["resumeDocument"];
  marked?: boolean;
  rewritten?: boolean;
  beforeBullet: string;
  afterBullet: string;
  markedLabel?: string;
}> = ({
  name = "Avery Johnson",
  title,
  meta = [],
  bullets,
  resumeDocument,
  marked,
  rewritten,
  beforeBullet,
  afterBullet,
  markedLabel = "Too vague",
}) => {
  const fallbackExperience = [
    {
      company: "Northstar Analytics",
      role: title.replace(" Resume", ""),
      dates: "2023 - Present",
      bullets,
    },
    {
      company: "CedarCloud Software",
      role: "Associate",
      dates: "2021 - 2023",
      bullets: ["Supported reporting, launch notes, and stakeholder follow-up.", "Updated documentation for team workflows."],
    },
  ];
  const doc = resumeDocument || {
    name,
    headline: title.replace(" Resume", ""),
    contact: ["Austin, TX", "candidate@example.com", "linkedin.com/in/candidate"],
    summary: meta.length
      ? `${meta.join("; ")}. Experience includes role support, reporting, stakeholder coordination, and campaign execution.`
      : "Professional candidate with relevant role experience, stakeholder collaboration, and measurable delivery exposure.",
    experience: fallbackExperience,
    skills: ["Reporting", "Campaigns", "Stakeholder updates", "Documentation", "Analytics"],
    education: "B.A. Business Administration, State University",
  };

  return (
    <div
      style={{
        width: 642,
        minHeight: 838,
        borderRadius: 18,
        background: "#fbfdff",
        color: "#0f172a",
        padding: "30px 36px",
        boxShadow: "0 36px 110px rgba(0,0,0,0.42)",
        border: "1px solid rgba(15,23,42,0.10)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 24, alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: 31, fontWeight: 950, lineHeight: 1.02, letterSpacing: 0 }}>{doc.name}</div>
          <div style={{ marginTop: 6, fontSize: 16, color: "#334155", fontWeight: 850 }}>{doc.headline}</div>
        </div>
        <div style={{ color: "#475569", fontSize: 10.5, lineHeight: 1.35, textAlign: "right", fontWeight: 750 }}>
          {doc.contact.slice(0, 3).map((item) => (
            <div key={item}>{item}</div>
          ))}
        </div>
      </div>

      <div style={{ height: 2, background: "#0f172a", margin: "18px 0 14px" }} />

      <div style={{ color: "#0f172a", fontSize: 12, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.5 }}>Professional Summary</div>
      <div style={{ marginTop: 7, color: "#334155", fontSize: 12.8, lineHeight: 1.42, fontWeight: 650 }}>{doc.summary}</div>

      <div style={{ color: "#0f172a", fontSize: 12, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.5, marginTop: 17 }}>Experience</div>
      <div style={{ display: "grid", gap: 13, marginTop: 8 }}>
        {doc.experience.slice(0, 2).map((job) => (
          <div key={`${job.company}-${job.role}`}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "baseline" }}>
              <div style={{ fontSize: 14.2, fontWeight: 950, color: "#0f172a" }}>{job.role}</div>
              <div style={{ fontSize: 10.8, fontWeight: 850, color: "#64748b" }}>{job.dates}</div>
            </div>
            <div style={{ marginTop: 2, fontSize: 12.2, fontWeight: 850, color: "#475569" }}>{job.company}</div>
            <div style={{ display: "grid", gap: 5, marginTop: 7 }}>
              {job.bullets.slice(0, 4).map((bullet) => {
                const isTarget = bullet === beforeBullet;
                const renderedBullet = rewritten && isTarget ? afterBullet : bullet;
                return (
                  <div
                    key={bullet}
                    style={{
                      position: "relative",
                      padding: isTarget ? "6px 8px 6px 21px" : "2px 0 2px 17px",
                      borderRadius: 10,
                      background: rewritten && isTarget ? "rgba(22,163,74,0.12)" : marked && isTarget ? "rgba(254,226,226,0.60)" : "transparent",
                      border: rewritten && isTarget ? "1.5px solid rgba(22,163,74,0.38)" : marked && isTarget ? "1.5px solid rgba(220,38,38,0.34)" : "1px solid transparent",
                      color: "#1e293b",
                      fontSize: isTarget ? 13.1 : 12.1,
                      lineHeight: 1.28,
                      fontWeight: isTarget ? 820 : 650,
                    }}
                  >
                    <span
                      style={{
                        position: "absolute",
                        left: isTarget ? 8 : 3,
                        top: isTarget ? 13 : 10,
                        width: 4.5,
                        height: 4.5,
                        borderRadius: 99,
                        background: rewritten && isTarget ? GREEN : "#334155",
                      }}
                    />
                    {renderedBullet}
                    {marked && isTarget ? (
                      <>
                        <div
                          style={{
                            position: "absolute",
                            inset: -6,
                            borderRadius: 14,
                            border: `4px solid ${RED}`,
                            transform: "rotate(-1.4deg)",
                            opacity: 0.86,
                          }}
                        />
                        <div
                          style={{
                            position: "absolute",
                            right: 10,
                            top: -14,
                            padding: "2px 8px",
                            borderRadius: 999,
                            background: "#fbfdff",
                            color: RED,
                            fontSize: 15,
                            fontWeight: 950,
                            transform: "rotate(1.8deg)",
                            zIndex: 3,
                          }}
                        >
                          {markedLabel}
                        </div>
                      </>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div style={{ color: "#0f172a", fontSize: 12, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.5, marginTop: 16 }}>Skills</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
        {doc.skills.slice(0, 9).map((skill) => (
          <div
            key={skill}
            style={{
              padding: "4px 7px",
              borderRadius: 8,
              background: "rgba(14,165,233,0.08)",
              color: "#075985",
              border: "1px solid rgba(14,165,233,0.18)",
              fontSize: 10.5,
              fontWeight: 850,
            }}
          >
            {skill}
          </div>
        ))}
      </div>

      <div style={{ color: "#0f172a", fontSize: 12, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.5, marginTop: 14 }}>Education</div>
      <div style={{ marginTop: 6, color: "#334155", fontSize: 11.4, fontWeight: 720 }}>{doc.education}</div>

      {rewritten ? (
        <div
          style={{
            position: "absolute",
            right: 22,
            bottom: 22,
            display: "flex",
            alignItems: "center",
            gap: 8,
            color: GREEN,
            fontSize: 13,
            fontWeight: 950,
            textTransform: "uppercase",
          }}
        >
          <SignalMascot logoMode style={{ width: 32, height: 32 }} />
          Real proof translated
        </div>
      ) : null}
    </div>
  );
};

const JobDescription: React.FC<{
  jobTitle: string;
  keywords: string[];
  highlightProgress: number;
  jobDescription?: ResumeCrimeSceneProps["jobDescription"];
}> = ({
  jobTitle,
  keywords,
  highlightProgress,
  jobDescription,
}) => {
  const jd: NonNullable<ResumeCrimeSceneProps["jobDescription"]> = jobDescription || {
    title: jobTitle,
    company: "TargetCo",
    summary: "Target role asking for specific tools, responsibilities, and measurable outcomes.",
    responsibilities: [
      `Use ${keywords[0] || "role tools"} and ${keywords[1] || "analytics"} to improve execution.`,
      `Report progress against ${keywords[2] || "business outcomes"}.`,
      "Partner across teams and communicate progress clearly.",
    ],
    requirements: keywords,
    searchQueries: keywords.slice(0, 4),
  };
  const searchTerms: string[] = (jd.searchQueries?.length ? jd.searchQueries : jd.requirements).slice(0, 4);

  return (
    <div
      style={{
        width: 402,
        borderRadius: 22,
        background: "rgba(15,23,42,0.94)",
        border: "1px solid rgba(56,213,255,0.24)",
        padding: "24px 24px",
        color: TEXT,
        boxShadow: "0 26px 80px rgba(0,0,0,0.34), inset 0 0 30px rgba(56,213,255,0.045)",
      }}
    >
      <div style={{ color: CYAN, fontSize: 13, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.4 }}>
        Job description
      </div>
      <div style={{ marginTop: 10, fontSize: 28, lineHeight: 1.02, fontWeight: 950 }}>{jd.title}</div>
      <div style={{ color: MUTED, fontSize: 13, fontWeight: 850, marginTop: 7 }}>{jd.company}</div>
      <div style={{ color: "#cbd5e1", fontSize: 13.5, lineHeight: 1.38, marginTop: 13, fontWeight: 650 }}>{jd.summary}</div>
      <div style={{ height: 1, background: "rgba(255,255,255,0.12)", margin: "18px 0" }} />
      <div style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.1 }}>Responsibilities</div>
      <div style={{ display: "grid", gap: 8, marginTop: 9 }}>
        {jd.responsibilities.slice(0, 3).map((item) => (
          <div key={item} style={{ color: "#cbd5e1", fontSize: 13.5, lineHeight: 1.28, fontWeight: 720 }}>
            - {item}
          </div>
        ))}
      </div>
      <div style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.1, marginTop: 16 }}>Recruiter search terms</div>
      <div style={{ display: "grid", gap: 9, marginTop: 10 }}>
        {searchTerms.map((keyword, index) => {
          const active = highlightProgress > index / Math.max(1, searchTerms.length);
          return (
            <div
              key={keyword}
              style={{
                padding: "10px 12px",
                borderRadius: 13,
                background: active ? "rgba(250,204,21,0.22)" : "rgba(255,255,255,0.045)",
                border: active ? "1px solid rgba(250,204,21,0.52)" : "1px solid rgba(148,163,184,0.12)",
                color: active ? "#fef9c3" : "#cbd5e1",
                fontSize: 16,
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
};

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
      top: 42,
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

const FormatOverlay: React.FC<{
  archetype: NonNullable<ResumeCrimeSceneProps["formatArchetype"]>;
  keywords: string[];
  beforeScore: number;
  afterScore: number;
  beforeBullet: string;
  opacity: number;
  phase: "problem" | "teardown" | "fix";
}> = ({ archetype, keywords, beforeScore, afterScore, beforeBullet, opacity, phase }) => {
  const frame = useCurrentFrame();
  const term = keywords[0] || "role keyword";
  const second = keywords[1] || "proof";
  const slide = interpolate(frame, [120, 170], [28, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  if (archetype === "recruiterSearch") {
    const found = phase === "fix";
    return (
      <div
        style={{
          position: "absolute",
          left: 58,
          bottom: 318,
          width: 452,
          padding: "18px 20px",
          borderRadius: 22,
          background: "rgba(2,6,23,0.92)",
          border: "1px solid rgba(34,197,94,0.34)",
          color: "#dcfce7",
          opacity,
          zIndex: 132,
          transform: `translateY(${slide}px)`,
          boxShadow: "0 24px 70px rgba(0,0,0,0.46), inset 0 0 24px rgba(34,197,94,0.06)",
        }}
      >
        <div style={{ color: "#22c55e", fontSize: 15, fontWeight: 950, textTransform: "uppercase", letterSpacing: 1.4 }}>Recruiter search</div>
        <div style={{ marginTop: 13, padding: "12px 14px", borderRadius: 12, background: "rgba(15,23,42,0.88)", color: "#f8fafc", fontSize: 24, fontWeight: 900 }}>
          "{term}" + "{second}"
        </div>
        <div style={{ marginTop: 13, color: found ? "#bbf7d0" : "#fecaca", fontSize: 27, fontWeight: 950 }}>
          {found ? "MATCH FOUND AFTER REWRITE" : "0 STRONG HITS IN BULLET"}
        </div>
      </div>
    );
  }

  if (archetype === "splitTranslation") {
    return (
      <div
        style={{
          position: "absolute",
          left: 326,
          top: 1038,
          width: 428,
          padding: "16px 18px",
          borderRadius: 20,
          background: "rgba(2,6,23,0.88)",
          border: "1px solid rgba(56,213,255,0.30)",
          opacity,
          zIndex: 132,
          color: "#e0f7ff",
          textAlign: "center",
          boxShadow: "0 20px 60px rgba(0,0,0,0.42)",
        }}
      >
        <div style={{ color: CYAN, fontSize: 14, fontWeight: 950, textTransform: "uppercase" }}>Translate the job, not the person</div>
        <div style={{ marginTop: 8, fontSize: 24, fontWeight: 950 }}>
          Resume proof {"->"} JD language
        </div>
      </div>
    );
  }

  if (archetype === "redTeamAudit") {
    return (
      <div
        style={{
          position: "absolute",
          right: 54,
          top: 203,
          width: 346,
          padding: "18px",
          borderRadius: 18,
          background: "rgba(127,29,29,0.86)",
          border: "2px solid rgba(254,202,202,0.48)",
          color: "#fee2e2",
          opacity,
          zIndex: 132,
          transform: "rotate(1.5deg)",
          boxShadow: "0 22px 70px rgba(127,29,29,0.34)",
        }}
      >
        <div style={{ fontSize: 34, fontWeight: 950, lineHeight: 0.96 }}>RESUME AUDIT</div>
        <div style={{ marginTop: 12, fontSize: 22, fontWeight: 900 }}>Score: {phase === "fix" ? afterScore : beforeScore}/100</div>
        <div style={{ marginTop: 10, fontSize: 18, lineHeight: 1.18, fontWeight: 800 }}>Finding: proof exists, but the source bullet is too vague.</div>
      </div>
    );
  }

  if (archetype === "mascotAssist") {
    return (
      <div
        style={{
          position: "absolute",
          left: 62,
          bottom: 302,
          width: 390,
          padding: "16px 18px",
          borderRadius: 22,
          background: "rgba(8,47,73,0.86)",
          border: "1px solid rgba(125,223,255,0.34)",
          color: "#e0f7ff",
          opacity,
          zIndex: 132,
          boxShadow: "0 22px 70px rgba(14,165,233,0.20)",
        }}
      >
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <SignalMascot expression={phase === "fix" ? "happy" : "sideEye"} gesture="pointRight" style={{ width: 72, height: 72 }} />
          <div style={{ fontSize: 23, lineHeight: 1.04, fontWeight: 950 }}>
            Signal found the proof buried under "{beforeBullet.slice(0, 26)}..."
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: "absolute",
        left: 58,
        bottom: 318,
        width: 422,
        padding: "16px 18px",
        borderRadius: 20,
        background: "rgba(250,204,21,0.18)",
        border: "2px solid rgba(250,204,21,0.46)",
        color: "#fef9c3",
        opacity,
        zIndex: 132,
        transform: "rotate(-2deg)",
        boxShadow: "0 22px 70px rgba(250,204,21,0.12)",
      }}
    >
      <div style={{ fontSize: 17, fontWeight: 950, textTransform: "uppercase" }}>Desk markup</div>
      <div style={{ marginTop: 7, fontSize: 25, fontWeight: 950, lineHeight: 1.03 }}>
        Circle one bullet. Fix one signal.
      </div>
    </div>
  );
};

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

type WordCaption = NonNullable<ResumeCrimeSceneProps["captions"]>[number];

const WordCaptionLayer: React.FC<{ captions?: WordCaption[] }> = ({ captions = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!captions.length) return null;

  const nowMs = (frame / fps) * 1000;
  const activeIndex = captions.findIndex((caption) => nowMs >= caption.startMs - 80 && nowMs <= caption.endMs + 160);
  if (activeIndex < 0) return null;
  const page = captions.slice(Math.max(0, activeIndex - 2), activeIndex + 5);

  return (
    <div
      style={{
        position: "absolute",
        left: 80,
        right: 80,
        bottom: 132,
        minHeight: 104,
        zIndex: 160,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexWrap: "wrap",
        gap: "0 14px",
        padding: "18px 30px",
        borderRadius: 24,
        background: "rgba(2,6,23,0.78)",
        border: "2px solid rgba(56,213,255,0.28)",
        boxShadow: "0 18px 46px rgba(0,0,0,0.48), inset 0 0 26px rgba(56,213,255,0.06)",
      }}
    >
      {page.map((caption, index) => {
        const active = nowMs >= caption.startMs && nowMs <= caption.endMs + 80;
        return (
          <span
            key={`${caption.startMs}-${caption.text}-${index}`}
            style={{
              color: active ? CYAN : "#ffffff",
              fontSize: active ? 43 : 37,
              lineHeight: 1.12,
              fontWeight: active ? 980 : 860,
              textTransform: "uppercase",
              textShadow: active ? "0 0 18px rgba(56,213,255,0.8), 0 4px 12px rgba(0,0,0,0.8)" : "0 4px 12px rgba(0,0,0,0.8)",
              transform: active ? "translateY(-2px)" : "translateY(0)",
            }}
          >
            {caption.text}
          </span>
        );
      })}
    </div>
  );
};

export const ResumeCrimeScene: React.FC<ResumeCrimeSceneProps> = ({
  hook,
  subhook,
  creativeFormat = "resumeCrimeScene",
  visualStyle = "neon",
  formatArchetype = "deskMarkup",
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
  resumeName,
  resumeTitle,
  resumeMeta = [],
  jobTitle,
  jobKeywords,
  weakBullets,
  beforeBullet,
  afterBullet,
  resumeDocument,
  jobDescription,
  beforeScore,
  afterScore,
  scoreBasis = defaultResumeCrimeSceneProps.scoreBasis,
  cta,
  musicSrc,
  musicVolume = 0.16,
  voiceoverSrc,
  voiceoverVolume = 0.94,
  durationSeconds,
  captions,
  sfxSrc,
  sfxVolume = 0.06,
  avatarVideoUrl,
  avatarLabel = "Recruiter review",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const styleName = visualStyle in VISUAL_STYLES ? visualStyle : "neon";
  const styleTheme = VISUAL_STYLES[styleName];
  const timing = buildTiming(durationInFrames, pace);
  const totalSeconds = durationSeconds || durationInFrames / fps;
  const hasWordCaptions = Boolean(captions?.length);
  const hookOpacity = stageOpacity(frame, timing.hook[0], timing.hook[1]);
  const problemOpacity = stageOpacity(frame, timing.problem[0], timing.problem[1]);
  const teardownOpacity = stageOpacity(frame, timing.teardown[0], timing.teardown[1]);
  const fixOpacity = stageOpacity(frame, timing.fix[0], timing.fix[1]);
  const ctaOpacity = fadeIn(frame, timing.cta[0], timing.cta[0] + 62);
  const highlightProgress = fadeIn(frame, timing.problem[0] + 18, timing.problem[0] + Math.round((timing.problem[1] - timing.problem[0]) * 0.58));
  const fixSpring = spring({ frame: frame - timing.fix[0], fps, config: { damping: 18, mass: 0.9 } });
  const scoreProgress = fadeIn(
    frame,
    timing.fix[0] + Math.round((timing.fix[1] - timing.fix[0]) * 0.44),
    timing.fix[0] + Math.round((timing.fix[1] - timing.fix[0]) * 0.74),
  );

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
        <div
          style={{
            maxWidth: 910,
            padding: "34px 42px",
            borderRadius: 34,
            background: "rgba(2,6,23,0.88)",
            border: "2px solid rgba(56,213,255,0.24)",
            boxShadow: "0 30px 100px rgba(0,0,0,0.46)",
          }}
        >
          <div style={{ color: styleTheme.warning, fontSize: 26, fontWeight: 950, textTransform: "uppercase", letterSpacing: 2.4 }}>
            {creativeFormat.replace(/([A-Z])/g, " $1").trim()}
          </div>
          <div style={{ color: TEXT, fontSize: 76, lineHeight: 0.98, fontWeight: 950, marginTop: 20 }}>{hook}</div>
          <div style={{ color: styleTheme.accent, fontSize: 39, lineHeight: 1.08, fontWeight: 950, marginTop: 22 }}>{subhook}</div>
        </div>
        {!hasWordCaptions ? <LowerPunchline text={punchline} tone="yellow" /> : null}
        <SignalReaction line={signalLines?.hook} expression="surprised" gesture="wave" side="right" bottom={318} opacity={hookOpacity} />
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: problemOpacity }}>
        <TopCaption text="The job description says:" emphasis={jobKeywords.slice(0, 2).join(" + ")} />
        {!hasWordCaptions ? <LowerPunchline text={problemPunchline} tone="red" /> : null}
        <div style={{ position: "absolute", left: 58, top: 225 }}>
          <ResumeSheet
            name={resumeName}
            title={resumeTitle}
            meta={resumeMeta}
            bullets={weakBullets}
            resumeDocument={resumeDocument}
            marked
            beforeBullet={beforeBullet}
            afterBullet={afterBullet}
            markedLabel={markedLabel}
          />
        </div>
        <div style={{ position: "absolute", right: 58, top: 318 }}>
          <JobDescription jobTitle={jobTitle} keywords={jobKeywords} highlightProgress={highlightProgress} jobDescription={jobDescription} />
        </div>
        <FormatOverlay archetype={formatArchetype} keywords={jobKeywords} beforeScore={beforeScore} afterScore={afterScore} beforeBullet={beforeBullet} opacity={problemOpacity} phase="problem" />
        <div style={{ position: "absolute", right: 74, bottom: 548 }}>
          <ScoreReceipt basis={scoreBasis} beforeScore={beforeScore} afterScore={afterScore} phase="before" accent={styleTheme.accent} />
        </div>
        <SignalReaction line={signalLines?.problem} expression="sideEye" gesture="pointLeft" side="right" bottom={402} opacity={problemOpacity} />
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: teardownOpacity }}>
        <TopCaption text={teardownText} emphasis={teardownEmphasis} tone="red" />
        {!hasWordCaptions ? <LowerPunchline text={teardownPunchline} tone="red" /> : null}
        <div style={{ position: "absolute", left: 82, top: 260 }}>
          <ResumeSheet
            name={resumeName}
            title={resumeTitle}
            meta={resumeMeta}
            bullets={weakBullets}
            resumeDocument={resumeDocument}
            marked
            beforeBullet={beforeBullet}
            afterBullet={afterBullet}
            markedLabel={markedLabel}
          />
        </div>
        <FormatOverlay archetype={formatArchetype} keywords={jobKeywords} beforeScore={beforeScore} afterScore={afterScore} beforeBullet={beforeBullet} opacity={teardownOpacity} phase="teardown" />
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
        {!hasWordCaptions ? <LowerPunchline text={fixPunchline} tone="green" /> : null}
        <div
          style={{
            position: "absolute",
            left: 74,
            top: 258,
            transform: `scale(${interpolate(fixSpring, [0, 1], [0.94, 1], { extrapolateRight: "clamp" })})`,
          }}
        >
          <ResumeSheet
            name={resumeName}
            title={resumeTitle}
            meta={resumeMeta}
            bullets={weakBullets}
            resumeDocument={resumeDocument}
            rewritten
            beforeBullet={beforeBullet}
            afterBullet={afterBullet}
            markedLabel={markedLabel}
          />
        </div>
        <div style={{ position: "absolute", right: 70, top: 348 }}>
          <JobDescription jobTitle={jobTitle} keywords={jobKeywords} highlightProgress={1} jobDescription={jobDescription} />
        </div>
        <FormatOverlay archetype={formatArchetype} keywords={jobKeywords} beforeScore={beforeScore} afterScore={afterScore} beforeBullet={beforeBullet} opacity={fixOpacity} phase="fix" />
        <div
          style={{
            position: "absolute",
            right: 86,
            bottom: 315,
            display: "flex",
            alignItems: "center",
            gap: 16,
          }}
        >
          <SignalMascot expression="happy" gesture="pointLeft" style={{ width: 120, height: 120 }} />
          <ScoreReceipt basis={scoreBasis} beforeScore={beforeScore} afterScore={Math.round(animatedScore)} phase={scoreProgress > 0.72 ? "after" : "before"} accent={styleTheme.accent} />
        </div>
        <SignalReaction line={signalLines?.fix} expression="happy" gesture="pointLeft" side="right" bottom={210} opacity={fixOpacity} />
      </AbsoluteFill>

      <AbsoluteFill style={{ opacity: ctaOpacity, alignItems: "center", justifyContent: "center", textAlign: "center", padding: 78 }}>
        <SignalMascot expression="wink" gesture="wave" speaking style={{ width: 250, height: 250 }} />
        <div style={{ color: TEXT, fontSize: 84, fontWeight: 950, lineHeight: 0.96, marginTop: 34 }}>
          Score receipt: {beforeScore} {"->"} {afterScore}
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
      <WordCaptionLayer captions={captions} />
    </AbsoluteFill>
  );
};
