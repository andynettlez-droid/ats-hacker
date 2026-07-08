#!/usr/bin/env node
import { execFileSync, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const key = process.argv[i];
  if (key.startsWith("--")) {
    const next = process.argv[i + 1];
    args.set(key.slice(2), next && !next.startsWith("--") ? process.argv[++i] : "true");
  }
}

const input = path.resolve(args.get("input") || "");
const out = path.resolve(args.get("out") || "screen_teardown.mp4");
const mode = args.get("mode") || "video";
const fps = Number(args.get("fps") || 12);
const width = 1080;
const height = 1920;

if (!input || !fs.existsSync(input)) {
  throw new Error("Missing --input screen_teardown.json");
}

const data = JSON.parse(fs.readFileSync(input, "utf8"));
const duration = Number(args.get("duration") || data.durationSec || 27);
const frameCount = Math.ceil(duration * fps);
const workDir = path.dirname(input);
const framesDir = path.join(workDir, "screen_teardown_frames");
const stillDir = path.join(workDir, "screen_teardown_storyboard");

function findTool(name) {
  const command = spawnSync("where.exe", [name], { encoding: "utf8" });
  if (command.status === 0) {
    return command.stdout.split(/\r?\n/).map((line) => line.trim()).find(Boolean);
  }
  throw new Error(`${name} not found.`);
}

const esc = (value) =>
  String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const lerp = (a, b, t) => a + (b - a) * t;
const ease = (t) => {
  const x = clamp(t, 0, 1);
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
};
const step = (t, start, end) => clamp((t - start) / Math.max(0.001, end - start), 0, 1);

function safeArray(value, fallback = []) {
  return Array.isArray(value) && value.length ? value : fallback;
}

function wrapText(text, maxChars) {
  const words = String(text).split(/\s+/).filter(Boolean);
  const lines = [];
  let line = "";
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (next.length > maxChars && line) {
      lines.push(line);
      line = word;
    } else {
      line = next;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function textLines(lines, x, y, options = {}) {
  const {
    size = 18,
    fill = "#111827",
    weight = 400,
    lineHeight = 1.35,
    maxChars = 80,
    anchor = "start",
    opacity = 1,
    family = "Arial, Helvetica, sans-serif",
  } = options;
  const rendered = [];
  let offset = 0;
  for (const item of lines) {
    const wrapped = wrapText(item, maxChars);
    for (const line of wrapped) {
      rendered.push(
        `<text x="${x}" y="${y + offset}" text-anchor="${anchor}" font-family="${family}" font-size="${size}" font-weight="${weight}" fill="${fill}" opacity="${opacity}">${esc(line)}</text>`,
      );
      offset += size * lineHeight;
    }
  }
  return rendered.join("\n");
}

function pill(x, y, text, color = "#0f766e", fill = "#ccfbf1", size = 14) {
  const w = Math.max(84, String(text).length * (size * 0.58) + 24);
  return `<g>
    <rect x="${x}" y="${y}" width="${w}" height="30" rx="15" fill="${fill}" stroke="${color}" stroke-opacity=".22"/>
    <text x="${x + 12}" y="${y + 20}" font-family="Arial, Helvetica, sans-serif" font-size="${size}" font-weight="800" fill="${color}">${esc(text)}</text>
  </g>`;
}

const timeline = {
  search: 2.0,
  weak: 4.8,
  red: 7.4,
  proof: 10.2,
  delete: 14.4,
  rewrite: 16.2,
  receipt: 21.4,
  cta: 24.0,
  ...(data.timeline || {}),
};

const resume = {
  fileLabel: data.fileLabel || "Jordan_Patel_Resume.pdf",
  candidateName: data.candidateName || "Jordan Patel",
  targetRole: data.targetRole || "Junior Cybersecurity Analyst",
  contactLine: data.contactLine || "Toronto, ON | jordan.patel@email.com | linkedin.com/in/jordanpatel",
  summary:
    data.summary ||
    "Entry-level cybersecurity analyst with hands-on SOC lab, endpoint, and alert triage experience across Microsoft Sentinel and CrowdStrike environments.",
  currentRole: data.currentRole || "IT Security Intern",
  companyLine: data.companyLine || "Northlake Health Systems | January 2025 - Present",
  weakLine: data.weakLine || "Monitored security alerts and supported investigations.",
  rewriteLine:
    data.rewriteLine || "Triaged 120+ Sentinel and CrowdStrike alerts, cutting false positives 22%.",
  existingBullets: safeArray(data.existingBullets, [
    "Reviewed 120+ security alerts monthly in Microsoft Sentinel and documented escalation notes.",
    "Escalated phishing incidents and VPN lockout patterns to the senior security analyst.",
    "Used CrowdStrike to validate endpoint activity during weekly investigation reviews.",
    "Reduced repeat false positives by 22% by documenting alert rules and recurring noise patterns.",
  ]),
  previousRole: data.previousRole || "IT Help Desk Technician",
  previousCompanyLine:
    data.previousCompanyLine || `${data.previousCompany || "MetroLink Services"} | ${data.previousDates || "2023 - 2025"}`,
  previousBullets: safeArray(data.previousBullets, [
    "Resolved password resets, VPN lockouts, MFA enrollment, and Windows 11 setup requests for 180+ staff.",
    "Created Jira tickets for recurring endpoint, account access, and network connectivity incidents.",
    "Documented repeat access issues and escalated suspicious sign-in patterns to the security team.",
  ]),
  education: data.education || "A.A.S. Cybersecurity, Columbus State Community College",
  certifications: safeArray(data.certifications, ["CompTIA Security+", "Microsoft SC-900"]),
  projectTitle: data.projectTitle || "Home SOC Lab",
  projectLine: data.projectLine || "Microsoft Sentinel, Windows Event Forwarding, CrowdStrike Community Tools | 2024",
  projectBullets: safeArray(data.projectBullets, [
    "Built a small lab to ingest Windows sign-in events, investigate failed logons, and document escalation notes.",
    "Mapped alert notes to phishing, endpoint, VPN, and suspicious authentication scenarios.",
    "Practiced basic incident notes, severity labels, and analyst handoff summaries.",
  ]),
  proofLines: safeArray(data.proofLines, [
    "120+ alerts/month",
    "Sentinel + CrowdStrike",
    "False positives down 22%",
  ]),
  skills: safeArray(data.skills, ["Microsoft Sentinel", "CrowdStrike", "Phishing Triage", "VPN", "Windows 11"]),
  skillsLine:
    data.skillsLine ||
    `SIEM/EDR: ${safeArray(data.skills, ["Microsoft Sentinel", "CrowdStrike"]).slice(0, 2).join(", ")} | Security Operations: phishing triage, alert review, false-positive tuning | IT Support: VPN, MFA, Windows 11, Jira`,
};

function resumePage(t) {
  const pageX = 84;
  const pageY = 128;
  const pageW = 912;
  const contentX = 138;
  const ruleX2 = 942;
  const lineX = contentX;
  const weakY = 548;
  const proofY = 730;
  const replaceProgress = ease(step(t, timeline.delete, timeline.rewrite + 2.4));
  const showRewrite = step(t, timeline.rewrite, timeline.rewrite + 3.8);
  const deleteWidth = 620 * ease(step(t, timeline.delete, timeline.delete + 1.7));
  const typed = resume.rewriteLine.slice(0, Math.floor(resume.rewriteLine.length * ease(showRewrite)));

  const weakHighlightOpacity = step(t, timeline.weak, timeline.weak + 0.8) * (1 - step(t, timeline.delete, timeline.delete + 1.3));
  const redMarkOpacity = step(t, timeline.red, timeline.red + 0.7) * (1 - step(t, timeline.delete - 0.5, timeline.delete + 0.8));
  const proofOpacity = step(t, timeline.proof, timeline.proof + 0.8) * (1 - step(t, timeline.delete - 0.4, timeline.delete + 0.7));
  const rewriteOpacity = step(t, timeline.rewrite, timeline.rewrite + 1.1);

  const coreSkills = resume.skillsLine;
  const certLine = resume.certifications.join(" | ");

  return `<g id="resume-page">
    <rect x="${pageX}" y="${pageY}" width="${pageW}" height="1258" rx="12" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
    <rect x="${pageX}" y="${pageY}" width="${pageW}" height="50" rx="12" fill="#f8fafc"/>
    <circle cx="${pageX + 28}" cy="${pageY + 25}" r="6" fill="#ef4444"/>
    <circle cx="${pageX + 50}" cy="${pageY + 25}" r="6" fill="#f59e0b"/>
    <circle cx="${pageX + 72}" cy="${pageY + 25}" r="6" fill="#22c55e"/>
    <text x="${pageX + pageW / 2}" y="${pageY + 32}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="700" fill="#64748b">${esc(resume.fileLabel)}</text>

    <text x="${contentX}" y="226" font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="800" fill="#111827">${esc(resume.candidateName)}</text>
    <text x="${contentX}" y="258" font-family="Arial, Helvetica, sans-serif" font-size="16.5" font-weight="800" fill="#1d4ed8">${esc(resume.targetRole)}</text>
    <text x="${contentX}" y="285" font-family="Arial, Helvetica, sans-serif" font-size="13.4" fill="#475569">${esc(resume.contactLine)}</text>

    <text x="${contentX}" y="336" font-family="Arial, Helvetica, sans-serif" font-size="14.8" font-weight="900" fill="#0f172a">PROFESSIONAL SUMMARY</text>
    <line x1="${contentX}" y1="350" x2="${ruleX2}" y2="350" stroke="#cbd5e1" stroke-width="2"/>
    ${textLines([resume.summary], contentX, 378, { size: 14.4, fill: "#334155", maxChars: 104, lineHeight: 1.25 })}

    <text x="${contentX}" y="446" font-family="Arial, Helvetica, sans-serif" font-size="14.8" font-weight="900" fill="#0f172a">TECHNICAL SKILLS</text>
    <line x1="${contentX}" y1="460" x2="${ruleX2}" y2="460" stroke="#cbd5e1" stroke-width="2"/>
    ${textLines([coreSkills], contentX, 486, { size: 13.6, fill: "#334155", weight: 700, maxChars: 112, lineHeight: 1.22 })}

    <text x="${contentX}" y="572" font-family="Arial, Helvetica, sans-serif" font-size="14.8" font-weight="900" fill="#0f172a">PROFESSIONAL EXPERIENCE</text>
    <line x1="${contentX}" y1="586" x2="${ruleX2}" y2="586" stroke="#cbd5e1" stroke-width="2"/>
    <text x="${contentX}" y="615" font-family="Arial, Helvetica, sans-serif" font-size="17" font-weight="900" fill="#111827">${esc(resume.currentRole)}</text>
    <text x="${contentX}" y="639" font-family="Arial, Helvetica, sans-serif" font-size="13.5" font-weight="700" fill="#475569">${esc(resume.companyLine)}</text>

    <rect x="${lineX - 8}" y="${weakY + 101}" width="710" height="30" rx="6" fill="#fde68a" opacity="${0.76 * weakHighlightOpacity}"/>
    <text x="${lineX}" y="${weakY + 122}" font-family="Arial, Helvetica, sans-serif" font-size="14.4" fill="#111827" opacity="${1 - replaceProgress}">- ${esc(resume.weakLine)}</text>
    <rect x="${lineX - 2}" y="${weakY + 106}" width="${deleteWidth}" height="21" rx="5" fill="#ffffff" opacity="${replaceProgress}"/>
    <line x1="${lineX - 5}" y1="${weakY + 118}" x2="${lineX + 626}" y2="${weakY + 118}" stroke="#dc2626" stroke-width="4.2" stroke-linecap="round" opacity="${redMarkOpacity}"/>

    <rect x="${lineX - 8}" y="${weakY + 94}" width="744" height="44" rx="9" fill="#dc2626" opacity="${0.08 * redMarkOpacity}"/>
    <text x="${lineX + 642}" y="${weakY + 122}" font-family="Arial, Helvetica, sans-serif" font-size="13.5" font-weight="900" fill="#dc2626" opacity="${redMarkOpacity}">too vague</text>

    <rect x="${lineX - 8}" y="${weakY + 95}" width="752" height="54" rx="9" fill="#dcfce7" stroke="#22c55e" stroke-width="2" opacity="${rewriteOpacity}"/>
    ${textLines([`- ${typed}`], lineX, weakY + 119, { size: 14.1, fill: "#14532d", weight: 900, maxChars: 90, opacity: rewriteOpacity })}

    ${textLines(resume.existingBullets.map((line) => `- ${line}`), contentX, 715, { size: 12.9, fill: "#334155", maxChars: 112, lineHeight: 1.25 })}

    <rect x="${contentX - 10}" y="${proofY - 26}" width="780" height="98" rx="11" fill="#ecfeff" stroke="#0891b2" stroke-width="2.2" opacity="${proofOpacity}"/>
    <text x="${contentX + 6}" y="${proofY - 5}" font-family="Arial, Helvetica, sans-serif" font-size="13.2" font-weight="900" fill="#0e7490" opacity="${proofOpacity}">Proof was already lower on the page</text>
    ${resume.proofLines.map((p, i) => `<text x="${contentX + 6}" y="${proofY + 17 + i * 20}" font-family="Arial, Helvetica, sans-serif" font-size="13.1" font-weight="800" fill="#155e75" opacity="${proofOpacity}">Evidence ${i + 1}: ${esc(p)}</text>`).join("\n")}

    <text x="${contentX}" y="848" font-family="Arial, Helvetica, sans-serif" font-size="16.2" font-weight="900" fill="#111827">${esc(resume.previousRole)}</text>
    <text x="${contentX}" y="870" font-family="Arial, Helvetica, sans-serif" font-size="13.2" font-weight="700" fill="#475569">${esc(resume.previousCompanyLine)}</text>
    ${textLines(resume.previousBullets.map((line) => `- ${line}`), contentX, 898, { size: 12.6, fill: "#334155", maxChars: 114, lineHeight: 1.22 })}

    <text x="${contentX}" y="1026" font-family="Arial, Helvetica, sans-serif" font-size="14.8" font-weight="900" fill="#0f172a">PROJECTS</text>
    <line x1="${contentX}" y1="1040" x2="${ruleX2}" y2="1040" stroke="#cbd5e1" stroke-width="2"/>
    <text x="${contentX}" y="1066" font-family="Arial, Helvetica, sans-serif" font-size="15.2" font-weight="900" fill="#111827">${esc(resume.projectTitle)}</text>
    <text x="${contentX}" y="1088" font-family="Arial, Helvetica, sans-serif" font-size="12.8" font-weight="700" fill="#475569">${esc(resume.projectLine)}</text>
    ${textLines(resume.projectBullets.map((line) => `- ${line}`), contentX, 1114, { size: 12.4, fill: "#334155", maxChars: 114, lineHeight: 1.2 })}

    <text x="${contentX}" y="1262" font-family="Arial, Helvetica, sans-serif" font-size="14.8" font-weight="900" fill="#0f172a">EDUCATION &amp; CERTIFICATIONS</text>
    <line x1="${contentX}" y1="1276" x2="${ruleX2}" y2="1276" stroke="#cbd5e1" stroke-width="2"/>
    ${textLines([`${resume.education} | ${certLine}`], contentX, 1302, { size: 12.8, fill: "#334155", weight: 700, maxChars: 116, lineHeight: 1.24 })}
  </g>`;
}

function jobPanel(t) {
  const opacity = step(t, timeline.search, timeline.search + 0.8) * (1 - step(t, timeline.receipt - 0.5, timeline.receipt + 0.2));
  const terms = safeArray(data.searchTerms, ["Sentinel", "CrowdStrike", "phishing triage", "alert volume"]);
  return `<g opacity="${opacity}">
    <rect x="80" y="1380" width="920" height="210" rx="26" fill="#0f172a"/>
    <text x="118" y="1432" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="900" fill="#f8fafc">Recruiter search terms</text>
    <text x="118" y="1464" font-family="Arial, Helvetica, sans-serif" font-size="15" fill="#94a3b8">What the job is actually asking for</text>
    ${terms.map((term, i) => pill(118 + (i % 2) * 390, 1492 + Math.floor(i / 2) * 42, term, "#67e8f9", "#083344")).join("\n")}
  </g>`;
}

function receipt(t) {
  const opacity = step(t, timeline.receipt, timeline.receipt + 0.8);
  const rows = safeArray(data.receiptRows, [
    { label: "SEARCH", value: "Sentinel + CrowdStrike" },
    { label: "PROOF", value: "120+ alerts/month" },
    { label: "RESULT", value: "22% fewer false positives" },
  ]);
  return `<g opacity="${opacity}">
    <rect x="84" y="1365" width="912" height="265" rx="30" fill="#052e2b" stroke="#2dd4bf" stroke-width="2"/>
    <text x="128" y="1420" font-family="Arial, Helvetica, sans-serif" font-size="25" font-weight="900" fill="#f0fdfa">Why the rewrite works</text>
    ${rows.slice(0, 3).map((row, i) => {
      const fills = ["#ecfeff", "#eff6ff", "#f0fdf4"];
      const colors = ["#0f766e", "#1d4ed8", "#16a34a"];
      return `<g transform="translate(${128 + i * 264} 1462)">
        <rect x="0" y="0" width="238" height="96" rx="18" fill="${fills[i]}"/>
        <text x="22" y="35" font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="900" fill="${colors[i]}">${esc(row.label)}</text>
        ${textLines([row.value], 22, 68, { size: 16.5, weight: 900, fill: "#0f172a", maxChars: 21 })}
      </g>`;
    }).join("\n")}
  </g>`;
}

function caption(t) {
  const beats = safeArray(data.captionBeats, []);
  const active = beats.find((beat) => t >= beat.start && t < beat.end);
  if (!active) return "";
  const fade = Math.min(step(t, active.start, active.start + 0.25), 1 - step(t, active.end - 0.25, active.end));
  return `<g opacity="${fade}">
    <rect x="96" y="1665" width="888" height="82" rx="24" fill="#111827" opacity=".88"/>
    <text x="540" y="1717" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="28" font-weight="900" fill="#f8fafc">${esc(active.text)}</text>
  </g>`;
}

function ctaCard(t) {
  const opacity = step(t, timeline.cta, timeline.cta + 0.6);
  return `<g opacity="${opacity}">
    <rect x="74" y="152" width="932" height="116" rx="30" fill="#0f172a" opacity=".96"/>
    <text x="540" y="206" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="27" font-weight="900" fill="#ffffff">Need yours fixed to match the job?</text>
    <text x="540" y="244" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="800" fill="#67e8f9">Use the link below before you apply.</text>
  </g>`;
}

function cameraTransform(t) {
  const panToWeak = ease(step(t, timeline.weak, timeline.weak + 1.2)) * (1 - ease(step(t, timeline.proof - 0.8, timeline.proof)));
  const panToProof = ease(step(t, timeline.proof, timeline.proof + 1.2)) * (1 - ease(step(t, timeline.delete - 0.7, timeline.delete)));
  const panBack = ease(step(t, timeline.delete - 0.2, timeline.delete + 1.0));
  let scale = 0.95;
  let tx = 0;
  let ty = 0;
  if (panToWeak > 0) {
    scale = lerp(scale, 1.2, panToWeak);
    tx = lerp(tx, -80, panToWeak);
    ty = lerp(ty, -430, panToWeak);
  }
  if (panToProof > 0) {
    scale = lerp(0.95, 1.16, panToProof);
    tx = lerp(0, -80, panToProof);
    ty = lerp(0, -610, panToProof);
  }
  if (panBack > 0) {
    scale = lerp(scale, 1.18, panBack);
    tx = lerp(tx, -80, panBack);
    ty = lerp(ty, -430, panBack);
  }
  return { tx, ty, scale };
}

function svgFor(t) {
  const { tx, ty, scale } = cameraTransform(t);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
    <defs>
      <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="18" stdDeviation="24" flood-color="#0f172a" flood-opacity=".18"/>
      </filter>
    </defs>
    <rect width="${width}" height="${height}" fill="#eef2f7"/>
    <rect x="0" y="0" width="${width}" height="88" fill="#ffffff"/>
    <circle cx="52" cy="44" r="12" fill="#ef4444"/>
    <circle cx="88" cy="44" r="12" fill="#f59e0b"/>
    <circle cx="124" cy="44" r="12" fill="#22c55e"/>
    <rect x="172" y="23" width="650" height="42" rx="21" fill="#f1f5f9"/>
    <text x="496" y="51" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="18" font-weight="700" fill="#64748b">${esc(data.windowTitle || "Signal resume teardown screen test")}</text>
    <text x="910" y="52" font-family="Arial, Helvetica, sans-serif" font-size="17" font-weight="800" fill="#0f766e">SCREEN EDIT</text>

    <g transform="translate(${tx} ${ty}) scale(${scale})" filter="url(#shadow)">
      ${resumePage(t)}
    </g>
    ${jobPanel(t)}
    ${receipt(t)}
    ${caption(t)}
    ${ctaCard(t)}
  </svg>`;
}

async function renderFrame(t, file) {
  await sharp(Buffer.from(svgFor(t))).png().toFile(file);
}

async function renderStoryboard() {
  fs.rmSync(stillDir, { recursive: true, force: true });
  fs.mkdirSync(stillDir, { recursive: true });
  const times = String(args.get("still-times") || data.storyboardTimes || "0.8,3.0,5.6,8.0,11.2,15.0,18.6,22.2,25.0")
    .split(",")
    .map((value) => Number(value.trim()))
    .filter((value) => Number.isFinite(value));
  const files = [];
  for (const t of times) {
    const file = path.join(stillDir, `story_${String(Math.round(t * 10)).padStart(4, "0")}.png`);
    await renderFrame(t, file);
    files.push(file);
  }
  const thumbs = await Promise.all(
    files.map((file) => sharp(file).resize(360, 640, { fit: "cover" }).png().toBuffer()),
  );
  const sheet = sharp({
    create: {
      width: 1080,
      height: Math.ceil(thumbs.length / 3) * 690,
      channels: 4,
      background: "#f8fafc",
    },
  });
  const composites = thumbs.map((input, index) => ({
    input,
    left: (index % 3) * 360,
    top: Math.floor(index / 3) * 690,
  }));
  const sheetPath = path.join(workDir, "screen_teardown_storyboard_contact_sheet.png");
  await sheet.composite(composites).png().toFile(sheetPath);
  console.log(
    JSON.stringify(
      {
        status: "storyboard_rendered",
        input,
        stillDir,
        sheetPath,
        stillCount: files.length,
      },
      null,
      2,
    ),
  );
}

async function renderVideo() {
  fs.rmSync(framesDir, { recursive: true, force: true });
  fs.mkdirSync(framesDir, { recursive: true });
  for (let i = 0; i < frameCount; i += 1) {
    const t = i / fps;
    const file = path.join(framesDir, `frame-${String(i + 1).padStart(5, "0")}.png`);
    await renderFrame(t, file);
  }

  fs.mkdirSync(path.dirname(out), { recursive: true });
  const ffmpeg = findTool("ffmpeg");
  execFileSync(
    ffmpeg,
    [
      "-y",
      "-framerate",
      String(fps),
      "-i",
      path.join(framesDir, "frame-%05d.png"),
      "-vf",
      "fps=30,setsar=1",
      "-c:v",
      "libx264",
      "-preset",
      "medium",
      "-crf",
      "18",
      "-pix_fmt",
      "yuv420p",
      "-movflags",
      "+faststart",
      out,
    ],
    { stdio: "inherit" },
  );

  console.log(
    JSON.stringify(
      {
        status: "rendered",
        input,
        out,
        framesDir,
        frameCount,
        fps,
        durationSec: duration,
      },
      null,
      2,
    ),
  );
}

if (mode === "storyboard") {
  await renderStoryboard();
} else if (mode === "video") {
  await renderVideo();
} else {
  throw new Error(`Unknown --mode ${mode}`);
}
