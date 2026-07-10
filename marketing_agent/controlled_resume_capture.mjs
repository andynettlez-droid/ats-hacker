#!/usr/bin/env node
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const VIEWPORT = Object.freeze({ width: 1080, height: 1920 });
const DEFAULT_CAPTURE_FPS = 12;
const DEFAULT_OUTPUT_FPS = 30;
const BOOLEAN_FLAGS = new Set([
  "debug",
  "dry-run",
  "help",
  "keep-frames",
  "no-storyboard",
]);
const VALUE_FLAGS = new Set([
  "capture-fps",
  "config",
  "contact-sheet",
  "duration",
  "out",
  "output-fps",
  "storyboard-dir",
  "storyboard-times",
]);

class CliError extends Error {
  constructor(message, details = []) {
    super(message);
    this.name = "CliError";
    this.details = Array.isArray(details) ? details : [details];
  }
}

function printHelp() {
  process.stdout.write(`Controlled Resume Capture v3

Render a deterministic 1080x1920 resume-editor screen recording from JSON.

Usage:
  node marketing_agent/controlled_resume_capture.mjs --config <brief.json> [options]

Required:
  --config <path>             JSON resume/edit brief.

Options:
  --out <path>                Silent H.264 MP4 output.
  --capture-fps <6-30>        Chromium screenshots per second (default: 12).
  --output-fps <24-60>        Encoded MP4 frame rate (default: 30).
  --duration <seconds>        Override config durationSec.
  --storyboard-times <csv>    Exact seconds for review stills.
  --storyboard-dir <path>     Directory for review stills.
  --contact-sheet <path>      Storyboard contact-sheet PNG.
  --no-storyboard             Skip stills and contact sheet.
  --keep-frames               Keep the temporary full frame sequence.
  --dry-run                   Validate config and dependency discovery only.
  --debug                     Include stack details on failure.
  --help                      Show this help.

Config-relative output paths are resolved beside the JSON file. CLI paths are
resolved from the current directory. See:
  marketing/video_style_templates/controlled_browser_editor_v3.md

Dependency overrides:
  PLAYWRIGHT_CORE_DIR, CHROME_PATH, FFMPEG_PATH, FFPROBE_PATH
`);
}

function parseArgs(argv) {
  const args = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      throw new CliError(`Unexpected positional argument: ${token}`);
    }
    const key = token.slice(2);
    if (!key) {
      throw new CliError("Empty option name.");
    }
    if (BOOLEAN_FLAGS.has(key)) {
      args.set(key, true);
      continue;
    }
    if (!VALUE_FLAGS.has(key)) {
      throw new CliError(`Unknown option: --${key}. Use --help for usage.`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      throw new CliError(`Missing value for --${key}.`);
    }
    args.set(key, value);
    index += 1;
  }
  return args;
}

function isObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function firstText(...values) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return "";
}

function textArray(value) {
  if (typeof value === "string" && value.trim()) return [value.trim()];
  if (!Array.isArray(value)) return [];
  return value
    .filter((item) => typeof item === "string" && item.trim())
    .map((item) => item.trim());
}

function uniqueStrings(values) {
  const seen = new Set();
  return values.filter((value) => {
    const key = value.toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function finiteNumber(value, fallback) {
  if (value === undefined || value === null || value === "") return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return Number.NaN;
  return parsed;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function scriptJson(value) {
  return JSON.stringify(value)
    .replace(/</g, "\\u003c")
    .replace(/>/g, "\\u003e")
    .replace(/&/g, "\\u0026");
}

function readConfig(configPath) {
  let source;
  try {
    source = fs.readFileSync(configPath, "utf8");
  } catch (error) {
    throw new CliError(`Could not read config: ${configPath}`, error.message);
  }
  try {
    const parsed = JSON.parse(source);
    if (!isObject(parsed)) throw new Error("The JSON root must be an object.");
    return parsed;
  } catch (error) {
    throw new CliError(`Invalid JSON config: ${configPath}`, error.message);
  }
}

function normalizeExperience(item, index) {
  if (!isObject(item)) {
    throw new CliError(`candidate.experience[${index}] must be an object.`);
  }
  const companyLine = firstText(
    item.companyLine,
    [item.company, item.location, item.dates].filter(Boolean).join(" | "),
  );
  return {
    title: firstText(item.title, item.role),
    companyLine,
    bullets: uniqueStrings(textArray(item.bullets)),
  };
}

function normalizeProjects(value, raw) {
  if (Array.isArray(value)) {
    return value.slice(0, 1).map((item, index) => {
      if (typeof item === "string") {
        return { name: item.trim(), detail: "", bullets: [] };
      }
      if (!isObject(item)) {
        throw new CliError(`candidate.projects[${index}] must be a string or object.`);
      }
      return {
        name: firstText(item.name, item.title),
        detail: firstText(item.detail, item.line, item.tools),
        bullets: textArray(item.bullets).slice(0, 3),
      };
    });
  }
  if (firstText(raw.projectTitle)) {
    return [{
      name: firstText(raw.projectTitle),
      detail: firstText(raw.projectLine),
      bullets: textArray(raw.projectBullets).slice(0, 3),
    }];
  }
  return [];
}

function findWeakRef(experiences, weakLine, explicitRef) {
  if (isObject(explicitRef)) {
    const experienceIndex = Number(explicitRef.experienceIndex ?? explicitRef.experience);
    const bulletIndex = Number(explicitRef.bulletIndex ?? explicitRef.bullet);
    return { experienceIndex, bulletIndex };
  }
  const matches = [];
  experiences.forEach((experience, experienceIndex) => {
    experience.bullets.forEach((bullet, bulletIndex) => {
      if (bullet === weakLine) matches.push({ experienceIndex, bulletIndex });
    });
  });
  if (matches.length !== 1) {
    throw new CliError(
      matches.length
        ? "weakLine appears more than once; set edit.weakRef explicitly."
        : "weakLine must exactly match one candidate.experience bullet.",
    );
  }
  return matches[0];
}

const TOKEN_STOP_WORDS = new Set([
  "and",
  "for",
  "from",
  "into",
  "the",
  "this",
  "that",
  "with",
  "while",
  "were",
  "was",
  "are",
  "has",
  "have",
  "had",
  "supported",
  "using",
]);

function evidenceTokens(value) {
  return new Set(
    String(value)
      .toLowerCase()
      .match(/[a-z0-9+%.-]+/g)
      ?.filter((token) => token.length >= 3 && !TOKEN_STOP_WORDS.has(token)) || [],
  );
}

function evidenceScore(label, bullet) {
  if (label.toLowerCase() === bullet.toLowerCase()) return 1000;
  const labelTokens = evidenceTokens(label);
  const bulletTokens = evidenceTokens(bullet);
  let score = 0;
  for (const token of labelTokens) {
    if (bulletTokens.has(token)) score += /\d/.test(token) ? 4 : 1;
  }
  return score;
}

function compactEvidence(value) {
  const text = String(value).replace(/[.;]\s*$/, "").trim();
  if (text.length <= 68) return text;
  return `${text.slice(0, 65).trimEnd()}...`;
}

function resolveProofs(raw, edit, experiences, weakRef) {
  const explicitRefs = Array.isArray(edit.proofRefs)
    ? edit.proofRefs
    : Array.isArray(raw.proofRefs)
      ? raw.proofRefs
      : [];
  const labels = uniqueStrings([
    ...textArray(edit.proofLabels),
    ...textArray(raw.proofLines),
    ...textArray(raw.proofAlreadyOnResume),
  ]);
  const used = new Set([`${weakRef.experienceIndex}:${weakRef.bulletIndex}`]);
  const proofs = [];

  for (const [index, item] of explicitRefs.entries()) {
    if (!isObject(item)) {
      throw new CliError(`edit.proofRefs[${index}] must be an object.`);
    }
    const experienceIndex = Number(item.experienceIndex ?? item.experience);
    const bulletIndex = Number(item.bulletIndex ?? item.bullet);
    const bullet = experiences[experienceIndex]?.bullets?.[bulletIndex];
    if (!bullet) {
      throw new CliError(
        `edit.proofRefs[${index}] points to missing experience ${experienceIndex}, bullet ${bulletIndex}.`,
      );
    }
    const key = `${experienceIndex}:${bulletIndex}`;
    if (used.has(key)) {
      throw new CliError(`edit.proofRefs[${index}] duplicates the weak line or another proof.`);
    }
    used.add(key);
    proofs.push({
      experienceIndex,
      bulletIndex,
      text: bullet,
      label: firstText(item.label, labels[index], compactEvidence(bullet)),
    });
  }

  const available = [];
  experiences.forEach((experience, experienceIndex) => {
    experience.bullets.forEach((bullet, bulletIndex) => {
      const key = `${experienceIndex}:${bulletIndex}`;
      if (!used.has(key)) available.push({ experienceIndex, bulletIndex, text: bullet, key });
    });
  });

  for (const label of labels) {
    if (proofs.length >= 3) break;
    const ranked = available
      .filter((candidate) => !used.has(candidate.key))
      .map((candidate) => ({ ...candidate, score: evidenceScore(label, candidate.text) }))
      .sort((a, b) => b.score - a.score);
    const match = ranked[0];
    if (!match) break;
    used.add(match.key);
    proofs.push({
      experienceIndex: match.experienceIndex,
      bulletIndex: match.bulletIndex,
      text: match.text,
      label: label || compactEvidence(match.text),
    });
  }

  for (const candidate of available) {
    if (proofs.length >= 3) break;
    if (used.has(candidate.key)) continue;
    used.add(candidate.key);
    proofs.push({
      experienceIndex: candidate.experienceIndex,
      bulletIndex: candidate.bulletIndex,
      text: candidate.text,
      label: compactEvidence(candidate.text),
    });
  }

  return proofs.slice(0, 3);
}

function normalizeTimeline(rawTimeline, durationSec) {
  const source = isObject(rawTimeline) ? rawTimeline : {};
  const timeline = {
    weak: finiteNumber(source.weak, 0),
    proof: finiteNumber(source.proof, 3.8),
    select: finiteNumber(
      source.select,
      source.delete === undefined ? 7.4 : Number(source.delete) - 0.9,
    ),
    delete: finiteNumber(source.delete, 8.4),
    type: finiteNumber(source.type ?? source.rewrite, 10.1),
    receipt: finiteNumber(source.receipt, 16.2),
    cta: finiteNumber(source.cta, 20),
  };
  timeline.typeEnd = Math.max(timeline.type, timeline.receipt - 0.6);
  timeline.eraseEnd = Math.max(timeline.delete, timeline.type - 0.35);
  timeline.duration = durationSec;
  return timeline;
}

function parseStoryboardTimes(value, timeline) {
  const defaults = [
    Math.max(0.2, timeline.weak + 0.4),
    timeline.proof + 0.8,
    timeline.select + 0.3,
    timeline.delete + 0.7,
    timeline.type + Math.max(0.8, (timeline.typeEnd - timeline.type) * 0.55),
    timeline.receipt + 0.8,
    timeline.cta + 0.4,
  ];
  const source = value === undefined || value === null || value === ""
    ? defaults
    : Array.isArray(value)
      ? value
      : String(value).split(",");
  return uniqueStrings(
    source
      .map((item) => Number(item))
      .filter((item) => Number.isFinite(item) && item >= 0 && item < timeline.duration)
      .map((item) => item.toFixed(3)),
  ).map(Number);
}

function normalizeConfig(raw, args) {
  const candidateSource = isObject(raw.candidate) ? raw.candidate : {};
  const edit = isObject(raw.edit) ? raw.edit : {};
  const review = isObject(raw.review) ? raw.review : {};
  const documentConfig = isObject(raw.document) ? raw.document : {};
  const legacyWeakLine = firstText(
    raw.weakLine,
    raw.resumeProblem?.weakLine,
  );
  const weakLine = firstText(edit.weakLine, legacyWeakLine);
  const rewriteLine = firstText(edit.rewriteLine, raw.rewriteLine, raw.rewrite);

  let experiences = [];
  const configuredExperiences = candidateSource.experience ?? raw.experience;
  if (Array.isArray(configuredExperiences)) {
    experiences = configuredExperiences.map(normalizeExperience);
  } else {
    const currentBullets = uniqueStrings([
      weakLine,
      ...textArray(raw.existingBullets),
    ].filter(Boolean));
    const previousBullets = textArray(raw.previousBullets);
    if (currentBullets.length || previousBullets.length) {
      experiences = [
        {
          title: firstText(raw.currentRole),
          companyLine: firstText(raw.companyLine),
          bullets: currentBullets,
        },
        {
          title: firstText(raw.previousRole),
          companyLine: firstText(raw.previousCompanyLine),
          bullets: previousBullets,
        },
      ];
    }
  }

  const candidateName = firstText(
    candidateSource.name,
    raw.candidateName,
    typeof raw.candidate === "string" ? raw.candidate : "",
  );
  const targetRole = firstText(candidateSource.targetRole, raw.targetRole);
  const contactLine = firstText(
    candidateSource.contactLine,
    candidateSource.contact,
    raw.contactLine,
    [
      candidateSource.location,
      candidateSource.email,
      candidateSource.linkedin,
    ].filter(Boolean).join(" | "),
  );
  const summary = firstText(candidateSource.summary, raw.summary);
  const skills = uniqueStrings([
    ...textArray(candidateSource.skills),
    ...textArray(raw.skills),
  ]);
  const skillsLine = firstText(candidateSource.skillsLine, raw.skillsLine)
    || skills.join(" | ");
  const projects = normalizeProjects(candidateSource.projects, raw);
  const education = uniqueStrings([
    ...textArray(candidateSource.education),
    ...textArray(raw.education),
  ]);
  const certifications = uniqueStrings([
    ...textArray(candidateSource.certifications),
    ...textArray(raw.certifications),
  ]);

  const weakRef = findWeakRef(experiences, weakLine, edit.weakRef ?? raw.weakRef);
  const proofs = resolveProofs(raw, edit, experiences, weakRef);
  const searchTerms = uniqueStrings([
    ...textArray(review.searchTerms),
    ...textArray(raw.searchTerms),
    ...(review.searchTerms || raw.searchTerms ? [] : skills.slice(0, 4)),
  ]).slice(0, 6);
  const configuredReceipt = Array.isArray(review.receiptRows)
    ? review.receiptRows
    : Array.isArray(raw.receiptRows)
      ? raw.receiptRows
      : [];
  const receiptRows = (configuredReceipt.length
    ? configuredReceipt
    : proofs.map((proof, index) => ({
      label: `EVIDENCE ${index + 1}`,
      value: proof.label,
    })))
    .slice(0, 3)
    .map((row, index) => ({
      label: firstText(row?.label, `EVIDENCE ${index + 1}`),
      value: firstText(row?.value, proofs[index]?.label),
    }));

  const durationSec = finiteNumber(
    args.get("duration"),
    finiteNumber(raw.durationSec, 22.5),
  );
  const timeline = normalizeTimeline(raw.timeline, durationSec);
  const storyboardTimes = parseStoryboardTimes(
    args.get("storyboard-times") ?? raw.storyboardTimes,
    timeline,
  );

  const normalized = {
    title: firstText(raw.title, "Controlled resume editor"),
    fileLabel: firstText(
      documentConfig.fileLabel,
      raw.fileLabel,
      `${candidateName.replace(/\s+/g, "_")}_Resume.docx`,
    ),
    candidate: {
      name: candidateName,
      targetRole,
      contactLine,
      summary,
      skillsLine,
      experience: experiences,
      projects,
      education,
      certifications,
    },
    edit: {
      weakLine,
      rewriteLine,
      weakRef,
      proofs,
    },
    review: {
      searchTerms,
      judgment: firstText(review.judgment, raw.judgment, "TOO VAGUE"),
      proofTitle: firstText(
        review.proofTitle,
        "Proof already on this resume",
      ),
      receiptTitle: firstText(review.receiptTitle, "Rewrite receipt"),
      receiptRows,
      cta: firstText(
        review.cta,
        raw.ctaText,
        "Run the free Signal score before you apply.",
      ),
    },
    durationSec,
    captureFps: finiteNumber(
      args.get("capture-fps"),
      finiteNumber(raw.captureFps, DEFAULT_CAPTURE_FPS),
    ),
    outputFps: finiteNumber(
      args.get("output-fps"),
      finiteNumber(raw.outputFps, DEFAULT_OUTPUT_FPS),
    ),
    timeline,
    storyboardTimes,
  };

  validateConfig(normalized);
  return normalized;
}

function validateText(errors, label, value, maximum) {
  if (!value) errors.push(`${label} is required.`);
  if (value && value.length > maximum) {
    errors.push(`${label} is ${value.length} characters; maximum is ${maximum}.`);
  }
}

function validateConfig(config) {
  const errors = [];
  validateText(errors, "candidate.name", config.candidate.name, 48);
  validateText(errors, "candidate.targetRole", config.candidate.targetRole, 58);
  validateText(errors, "candidate.contactLine", config.candidate.contactLine, 130);
  validateText(errors, "candidate.summary", config.candidate.summary, 260);
  validateText(errors, "candidate.skillsLine", config.candidate.skillsLine, 230);
  validateText(errors, "edit.weakLine", config.edit.weakLine, 165);
  validateText(errors, "edit.rewriteLine", config.edit.rewriteLine, 205);
  validateText(errors, "fileLabel", config.fileLabel, 70);

  if (config.candidate.experience.length !== 2) {
    errors.push("candidate.experience must contain exactly two roles for the fixed v3 page.");
  }
  let totalBullets = 0;
  config.candidate.experience.forEach((experience, experienceIndex) => {
    validateText(errors, `candidate.experience[${experienceIndex}].title`, experience.title, 64);
    validateText(
      errors,
      `candidate.experience[${experienceIndex}].companyLine`,
      experience.companyLine,
      100,
    );
    if (experience.bullets.length < 3 || experience.bullets.length > 6) {
      errors.push(
        `candidate.experience[${experienceIndex}].bullets must contain 3-6 lines.`,
      );
    }
    totalBullets += experience.bullets.length;
    experience.bullets.forEach((bullet, bulletIndex) => {
      validateText(
        errors,
        `candidate.experience[${experienceIndex}].bullets[${bulletIndex}]`,
        bullet,
        205,
      );
    });
  });
  if (totalBullets < 6 || totalBullets > 10) {
    errors.push(`The resume needs 6-10 experience bullets; received ${totalBullets}.`);
  }

  const weakBullet = config.candidate.experience[config.edit.weakRef.experienceIndex]
    ?.bullets?.[config.edit.weakRef.bulletIndex];
  if (weakBullet !== config.edit.weakLine) {
    errors.push("edit.weakRef does not point to edit.weakLine.");
  }
  if (config.edit.proofs.length < 2 || config.edit.proofs.length > 3) {
    errors.push("Provide 2-3 proof references or proof lines that map to resume bullets.");
  }
  if (config.review.searchTerms.length < 3 || config.review.searchTerms.length > 6) {
    errors.push("review.searchTerms must contain 3-6 role-specific terms.");
  }
  if (config.review.receiptRows.length < 2 || config.review.receiptRows.length > 3) {
    errors.push("review.receiptRows must contain 2-3 evidence rows.");
  }
  config.review.receiptRows.forEach((row, index) => {
    validateText(errors, `review.receiptRows[${index}].label`, row.label, 24);
    validateText(errors, `review.receiptRows[${index}].value`, row.value, 72);
  });
  if (!config.candidate.education.length) {
    errors.push("candidate.education needs at least one line.");
  }
  if (!config.candidate.certifications.length) {
    errors.push("candidate.certifications needs at least one line.");
  }
  config.candidate.projects.forEach((project, index) => {
    validateText(errors, `candidate.projects[${index}].name`, project.name, 70);
    if (project.detail.length > 130) {
      errors.push(`candidate.projects[${index}].detail exceeds 130 characters.`);
    }
  });
  if (!Number.isFinite(config.durationSec) || config.durationSec < 8 || config.durationSec > 45) {
    errors.push("durationSec must be between 8 and 45 seconds.");
  }
  if (
    !Number.isInteger(config.captureFps)
    || config.captureFps < 6
    || config.captureFps > 30
  ) {
    errors.push("captureFps must be an integer from 6 to 30.");
  }
  if (
    !Number.isInteger(config.outputFps)
    || config.outputFps < 24
    || config.outputFps > 60
  ) {
    errors.push("outputFps must be an integer from 24 to 60.");
  }

  const order = [
    ["weak", config.timeline.weak],
    ["proof", config.timeline.proof],
    ["select", config.timeline.select],
    ["delete", config.timeline.delete],
    ["type", config.timeline.type],
    ["receipt", config.timeline.receipt],
    ["cta", config.timeline.cta],
    ["durationSec", config.durationSec],
  ];
  order.forEach(([label, value]) => {
    if (!Number.isFinite(value)) errors.push(`timeline.${label} must be a number.`);
  });
  for (let index = 1; index < order.length; index += 1) {
    if (order[index][1] <= order[index - 1][1]) {
      errors.push(
        `Timeline must increase: ${order[index - 1][0]} < ${order[index][0]}.`,
      );
    }
  }
  const minimumGaps = [
    ["proof to select", config.timeline.select - config.timeline.proof, 1],
    ["select to delete", config.timeline.delete - config.timeline.select, 0.4],
    ["delete to type", config.timeline.type - config.timeline.delete, 0.8],
    ["type to receipt", config.timeline.receipt - config.timeline.type, 1.5],
    ["receipt to CTA", config.timeline.cta - config.timeline.receipt, 0.5],
    ["CTA to end", config.durationSec - config.timeline.cta, 0.5],
  ];
  for (const [label, actual, minimum] of minimumGaps) {
    if (actual < minimum) {
      errors.push(`${label} needs at least ${minimum}s; received ${actual.toFixed(2)}s.`);
    }
  }
  if (config.timeline.weak < 0) errors.push("timeline.weak cannot be negative.");
  if (config.storyboardTimes.length < 3 && config.durationSec >= 8) {
    errors.push("At least three storyboard times must fall within durationSec.");
  }

  if (errors.length) {
    throw new CliError("Config validation failed.", errors);
  }
}

function resolveCliPath(value) {
  return path.resolve(process.cwd(), value);
}

function resolveConfigPath(configDir, value) {
  return path.resolve(configDir, value);
}

function outputPlan(raw, args, configPath) {
  const configDir = path.dirname(configPath);
  const outputConfig = isObject(raw.output) ? raw.output : {};
  const defaultStem = `${path.basename(configPath, path.extname(configPath))}_controlled`;
  const configVideo = typeof raw.output === "string" ? raw.output : outputConfig.video;
  const out = args.get("out")
    ? resolveCliPath(args.get("out"))
    : resolveConfigPath(configDir, firstText(configVideo, `${defaultStem}.mp4`));
  if (path.extname(out).toLowerCase() !== ".mp4") {
    throw new CliError("--out must use an .mp4 extension.");
  }
  const storyboardDir = args.get("storyboard-dir")
    ? resolveCliPath(args.get("storyboard-dir"))
    : resolveConfigPath(
      configDir,
      firstText(outputConfig.storyboardDir, `${defaultStem}_storyboard`),
    );
  const contactSheet = args.get("contact-sheet")
    ? resolveCliPath(args.get("contact-sheet"))
    : resolveConfigPath(
      configDir,
      firstText(outputConfig.contactSheet, `${defaultStem}_contact_sheet.png`),
    );
  const storyboardEnabled = !args.get("no-storyboard") && outputConfig.storyboard !== false;
  return { out, storyboardDir, contactSheet, storyboardEnabled };
}

function findExecutable(names, envPath) {
  if (envPath) {
    const resolved = path.resolve(envPath);
    if (fs.existsSync(resolved)) return resolved;
  }
  const locator = process.platform === "win32" ? "where.exe" : "which";
  for (const name of names) {
    const result = spawnSync(locator, [name], { encoding: "utf8", windowsHide: true });
    if (result.status === 0) {
      const found = result.stdout
        .split(/\r?\n/)
        .map((line) => line.trim())
        .find(Boolean);
      if (found && fs.existsSync(found)) return found;
    }
  }
  return "";
}

function discoverBrowser() {
  const explicit = firstText(
    process.env.CHROME_PATH,
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
  );
  const candidates = [
    explicit,
    ...(process.platform === "win32"
      ? [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
        "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
      ]
      : process.platform === "darwin"
        ? [
          "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
          "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
          "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
        : [
          "/usr/bin/google-chrome",
          "/usr/bin/google-chrome-stable",
          "/usr/bin/chromium",
          "/usr/bin/chromium-browser",
          "/usr/bin/microsoft-edge",
        ]),
  ].filter(Boolean);
  const direct = candidates.find((candidate) => fs.existsSync(candidate));
  if (direct) return direct;
  return findExecutable(
    ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge"],
    "",
  );
}

function normalizeModuleRoot(candidate) {
  if (!candidate) return "";
  const resolved = path.resolve(candidate);
  if (path.basename(resolved).toLowerCase() === "playwright-core") {
    return path.dirname(resolved);
  }
  if (path.basename(resolved).toLowerCase() === "playwright") {
    return path.dirname(resolved);
  }
  if (fs.existsSync(path.join(resolved, "node_modules"))) {
    return path.join(resolved, "node_modules");
  }
  return resolved;
}

function discoverPlaywright() {
  const moduleDir = path.dirname(fileURLToPath(import.meta.url));
  const repoRoot = path.resolve(moduleDir, "..");
  const roots = uniqueStrings([
    process.env.PLAYWRIGHT_CORE_DIR || "",
    path.join(os.tmpdir(), "signal-playwright-core", "node_modules"),
    path.join(repoRoot, "node_modules"),
    path.join(repoRoot, "web", "node_modules"),
  ].filter(Boolean).map(normalizeModuleRoot));
  for (const nodeModulesDir of roots) {
    for (const packageName of ["playwright-core", "playwright"]) {
      if (fs.existsSync(path.join(nodeModulesDir, packageName, "package.json"))) {
        return { nodeModulesDir, packageName };
      }
    }
  }
  return null;
}

function loadChromium(discovery) {
  if (!discovery) {
    throw new CliError(
      "Playwright was not found.",
      "Install outside the repo: npm.cmd install playwright-core --prefix %TEMP%\\signal-playwright-core --no-save",
    );
  }
  try {
    const require = createRequire(path.join(discovery.nodeModulesDir, "signal-importer.cjs"));
    const module = require(discovery.packageName);
    if (!module.chromium) throw new Error(`${discovery.packageName} has no chromium export.`);
    return module.chromium;
  } catch (error) {
    throw new CliError(`Could not load ${discovery.packageName}.`, error.message);
  }
}

function discoverDependencies() {
  return {
    playwright: discoverPlaywright(),
    browser: discoverBrowser(),
    ffmpeg: findExecutable(["ffmpeg"], process.env.FFMPEG_PATH),
    ffprobe: findExecutable(["ffprobe"], process.env.FFPROBE_PATH),
  };
}

function dependencyProblems(dependencies) {
  const problems = [];
  if (!dependencies.playwright) {
    problems.push(
      "playwright-core not found (set PLAYWRIGHT_CORE_DIR or install it in %TEMP%\\signal-playwright-core).",
    );
  }
  if (!dependencies.browser) {
    problems.push("Chromium-based Chrome or Edge not found (set CHROME_PATH).");
  }
  if (!dependencies.ffmpeg) problems.push("ffmpeg not found (set FFMPEG_PATH).");
  if (!dependencies.ffprobe) problems.push("ffprobe not found (set FFPROBE_PATH).");
  return problems;
}

function proofKey(experienceIndex, bulletIndex) {
  return `${experienceIndex}:${bulletIndex}`;
}

function renderExperience(experience, experienceIndex, config, proofKeys) {
  const bullets = experience.bullets.map((bullet, bulletIndex) => {
    const key = proofKey(experienceIndex, bulletIndex);
    const isWeak = key === proofKey(
      config.edit.weakRef.experienceIndex,
      config.edit.weakRef.bulletIndex,
    );
    const proof = proofKeys.get(key);
    if (isWeak) {
      return `<li class="resume-bullet editable-bullet" id="weakBullet" data-fit-check="weak bullet">
        <span class="bullet-mark" aria-hidden="true"></span>
        <span class="bullet-copy" id="weakText"></span><span class="edit-caret" id="editCaret"></span>
        <span class="line-flag" id="lineFlag"></span>
      </li>`;
    }
    return `<li class="resume-bullet${proof ? " proof-line" : ""}"${proof ? ` id="proofLine${proof.index}" data-proof-index="${proof.index}"` : ""}>
      <span class="bullet-mark" aria-hidden="true"></span>
      <span class="bullet-copy">${escapeHtml(bullet)}</span>
    </li>`;
  }).join("\n");
  return `<section class="role-block">
    <div class="role-row">
      <div class="job-title">${escapeHtml(experience.title)}</div>
      <div class="company-line">${escapeHtml(experience.companyLine)}</div>
    </div>
    <ul class="resume-bullets">${bullets}</ul>
  </section>`;
}

function renderProject(project) {
  if (!project) return "";
  const bullets = project.bullets.map((bullet) => `<li>${escapeHtml(bullet)}</li>`).join("");
  return `<section class="resume-section project-section">
    <h2>PROJECTS</h2>
    <div class="project-title">${escapeHtml(project.name)}</div>
    ${project.detail ? `<div class="project-detail">${escapeHtml(project.detail)}</div>` : ""}
    ${bullets ? `<ul class="compact-list">${bullets}</ul>` : ""}
  </section>`;
}

function buildEditorHtml(config) {
  const proofKeys = new Map(
    config.edit.proofs.map((proof, index) => [
      proofKey(proof.experienceIndex, proof.bulletIndex),
      { ...proof, index },
    ]),
  );
  const experiences = config.candidate.experience
    .map((experience, index) => renderExperience(experience, index, config, proofKeys))
    .join("\n");
  const searchTerms = config.review.searchTerms
    .map((term, index) => `<div class="term-row" data-term-index="${index}">${escapeHtml(term)}</div>`)
    .join("");
  const proofRows = config.edit.proofs
    .map((proof, index) => `<div class="evidence-row">
      <span class="evidence-index">${String(index + 1).padStart(2, "0")}</span>
      <span class="evidence-value">${escapeHtml(proof.label)}</span>
    </div>`)
    .join("");
  const receiptRows = config.review.receiptRows
    .map((row) => `<div class="receipt-column" data-fit-check="receipt value">
      <div class="receipt-label">${escapeHtml(row.label)}</div>
      <div class="receipt-pass">PASS</div>
      <div class="receipt-value">${escapeHtml(row.value)}</div>
    </div>`)
    .join("");
  const educationLine = config.candidate.education.join(" | ");
  const certificationLine = config.candidate.certifications.join(" | ");
  const runtime = {
    weakLine: config.edit.weakLine,
    rewriteLine: config.edit.rewriteLine,
    judgment: config.review.judgment,
    timeline: config.timeline,
    proofCount: config.edit.proofs.length,
  };

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=1080, initial-scale=1">
  <title>${escapeHtml(config.title)}</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Arial, "Segoe UI", sans-serif;
      font-synthesis: none;
      text-rendering: geometricPrecision;
    }
    * {
      box-sizing: border-box;
      cursor: none !important;
      letter-spacing: 0;
    }
    html, body {
      margin: 0;
      width: 1080px;
      height: 1920px;
      overflow: hidden;
      background: #e9edf2;
      color: #172033;
    }
    body {
      position: relative;
    }
    .stage {
      position: relative;
      width: 1080px;
      height: 1920px;
      overflow: hidden;
      isolation: isolate;
    }
    .editor-bar {
      position: absolute;
      inset: 0 0 auto;
      height: 74px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 24px;
      padding: 0 42px;
      background: #ffffff;
      border-bottom: 1px solid #cfd6df;
      z-index: 4;
    }
    .file-identity {
      min-width: 0;
    }
    .file-name {
      overflow: hidden;
      color: #172033;
      font-size: 18px;
      font-weight: 700;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .file-mode {
      margin-top: 3px;
      color: #677386;
      font-size: 12px;
      font-weight: 600;
    }
    .save-state {
      display: flex;
      align-items: center;
      gap: 9px;
      color: #32695a;
      font-size: 13px;
      font-weight: 700;
    }
    .save-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #2f8a68;
    }
    .workspace {
      position: absolute;
      inset: 74px 0 0;
      background: #e9edf2;
    }
    .paper {
      position: absolute;
      top: 28px;
      left: 82px;
      width: 916px;
      height: 1288px;
      overflow: hidden;
      background: #ffffff;
      border: 1px solid #cbd3dd;
      box-shadow: 0 12px 26px rgba(30, 41, 59, 0.13);
    }
    .resume-content {
      height: 100%;
      overflow: hidden;
      padding: 38px 48px 34px;
    }
    .resume-header {
      padding-bottom: 15px;
      border-bottom: 2px solid #1f4f78;
    }
    .candidate-name {
      margin: 0;
      color: #111827;
      font-size: 34px;
      font-weight: 800;
      line-height: 1.05;
    }
    .target-role {
      margin-top: 6px;
      color: #235f8f;
      font-size: 17px;
      font-weight: 700;
      line-height: 1.1;
    }
    .contact-line {
      margin-top: 8px;
      overflow: hidden;
      color: #4b5565;
      font-size: 12.8px;
      line-height: 1.2;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .resume-section {
      margin-top: 18px;
    }
    .resume-section h2 {
      margin: 0 0 9px;
      padding-bottom: 6px;
      color: #172033;
      border-bottom: 1px solid #aeb9c7;
      font-size: 13.8px;
      font-weight: 800;
      line-height: 1;
    }
    .summary-copy,
    .skills-copy {
      margin: 0;
      color: #303b4d;
      font-size: 14px;
      line-height: 1.3;
    }
    .skills-copy {
      font-weight: 600;
    }
    .role-block {
      margin-top: 15px;
    }
    .role-row {
      display: grid;
      grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.35fr);
      align-items: baseline;
      gap: 18px;
    }
    .job-title {
      overflow: hidden;
      color: #172033;
      font-size: 15.4px;
      font-weight: 800;
      line-height: 1.15;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .company-line {
      overflow: hidden;
      color: #546174;
      font-size: 12.3px;
      font-weight: 600;
      line-height: 1.15;
      text-align: right;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .resume-bullets {
      margin: 8px 0 0;
      padding: 0;
      list-style: none;
    }
    .resume-bullet {
      position: relative;
      min-height: 42px;
      margin: 0;
      padding: 5px 78px 5px 18px;
      border: 1px solid transparent;
      color: #303b4d;
      font-size: 14px;
      line-height: 1.24;
    }
    .bullet-mark {
      position: absolute;
      top: 5px;
      left: 3px;
      width: 10px;
      color: #39465a;
      font-size: 14px;
      line-height: 1.24;
    }
    .bullet-mark::before {
      content: "\\2022";
    }
    .editable-bullet {
      min-height: 58px;
      overflow: hidden;
      padding-top: 5px;
      padding-bottom: 5px;
    }
    .editable-bullet .bullet-mark {
      top: 5px;
    }
    .editable-bullet.is-weak {
      background: #fff4bf;
      border-color: #ead57a;
    }
    .editable-bullet.is-selected .bullet-copy {
      color: #102a43;
      background: #b9d8f5;
      box-shadow: 0 0 0 2px #b9d8f5;
    }
    .editable-bullet.is-deleting {
      background: #fff7ed;
      border-color: #d97706;
    }
    .editable-bullet.is-typing,
    .editable-bullet.is-complete {
      background: #e9f8ef;
      border-color: #5eaa79;
      color: #1f5133;
      font-weight: 700;
    }
    .edit-caret {
      display: none;
      width: 2px;
      height: 15px;
      margin-left: 2px;
      background: #275f82;
      vertical-align: -2px;
    }
    .editable-bullet.is-deleting .edit-caret,
    .editable-bullet.is-typing .edit-caret {
      display: inline-block;
    }
    .line-flag {
      position: absolute;
      top: 6px;
      right: 7px;
      min-width: 58px;
      padding: 3px 5px;
      color: #7c4f00;
      border: 1px solid #d7ad42;
      border-radius: 3px;
      background: #fffaf0;
      font-size: 9.5px;
      font-weight: 800;
      line-height: 1;
      text-align: center;
    }
    .editable-bullet.is-typing .line-flag,
    .editable-bullet.is-complete .line-flag {
      color: #275d3c;
      border-color: #7cb18d;
      background: #f2fbf5;
    }
    .proof-line {
      border-left-width: 3px;
    }
    .proof-line.is-proof {
      color: #174e59;
      border-color: #65aebb;
      background: #e8f8fa;
    }
    .project-title {
      color: #172033;
      font-size: 14px;
      font-weight: 800;
    }
    .project-detail {
      margin-top: 2px;
      color: #546174;
      font-size: 12.4px;
      font-weight: 600;
    }
    .compact-list {
      margin: 6px 0 0;
      padding-left: 18px;
      color: #303b4d;
      font-size: 13.2px;
      line-height: 1.25;
    }
    .compact-list li {
      margin-bottom: 4px;
    }
    .education-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 22px;
    }
    .education-label {
      color: #607086;
      font-size: 9.8px;
      font-weight: 800;
    }
    .education-value {
      margin-top: 3px;
      color: #303b4d;
      font-size: 12.5px;
      font-weight: 600;
      line-height: 1.2;
    }
    .review-surface {
      position: absolute;
      top: 1348px;
      left: 82px;
      width: 916px;
      height: 384px;
      overflow: hidden;
      background: #ffffff;
      border: 1px solid #bfc8d3;
      border-radius: 6px;
    }
    .review-panel {
      position: absolute;
      inset: 0;
      display: none;
      padding: 25px 30px 28px;
    }
    .review-panel.is-active {
      display: block;
    }
    .panel-kicker {
      color: #607086;
      font-size: 11px;
      font-weight: 800;
    }
    .panel-title {
      margin-top: 5px;
      color: #172033;
      font-size: 21px;
      font-weight: 800;
      line-height: 1.15;
    }
    .panel-note {
      margin-top: 6px;
      color: #607086;
      font-size: 13px;
      line-height: 1.25;
    }
    .opening-quote {
      max-width: 820px;
      font-size: 23px;
      line-height: 1.18;
    }
    .opening-judgment {
      color: #8a4b08;
      font-size: 15px;
      font-weight: 800;
    }
    .term-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px 12px;
      margin-top: 20px;
    }
    .term-row {
      min-height: 43px;
      padding: 12px 14px;
      color: #244e6f;
      border: 1px solid #9bb8cf;
      border-radius: 4px;
      background: #f4f8fb;
      font-size: 14px;
      font-weight: 700;
      opacity: 0.38;
    }
    .term-row.is-active {
      color: #143f5e;
      border-color: #5b8db0;
      background: #eaf4fb;
      opacity: 1;
    }
    .evidence-grid {
      display: grid;
      gap: 7px;
      margin-top: 18px;
    }
    .evidence-row {
      display: grid;
      grid-template-columns: 48px minmax(0, 1fr);
      align-items: center;
      min-height: 48px;
      border-top: 1px solid #b7d8de;
    }
    .evidence-index {
      color: #23717d;
      font-size: 12px;
      font-weight: 800;
    }
    .evidence-value {
      overflow: hidden;
      color: #174e59;
      font-size: 14px;
      font-weight: 700;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .edit-progress {
      height: 4px;
      margin-top: 28px;
      overflow: hidden;
      background: #d8dee7;
    }
    .edit-progress-fill {
      width: 0;
      height: 100%;
      background: #2d6d92;
    }
    .edit-status {
      margin-top: 17px;
      color: #234b68;
      font-size: 18px;
      font-weight: 800;
    }
    .edit-detail {
      margin-top: 8px;
      color: #607086;
      font-size: 14px;
    }
    .receipt-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      min-height: 168px;
      margin-top: 19px;
      border-top: 1px solid #a8c7b4;
      border-bottom: 1px solid #a8c7b4;
    }
    .receipt-column {
      min-width: 0;
      padding: 17px 16px 14px;
      border-left: 1px solid #c9d9ce;
    }
    .receipt-column:first-child {
      border-left: 0;
    }
    .receipt-label {
      overflow: hidden;
      color: #607086;
      font-size: 10px;
      font-weight: 800;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .receipt-pass {
      margin-top: 10px;
      color: #2d6e48;
      font-size: 12px;
      font-weight: 800;
    }
    .receipt-value {
      margin-top: 7px;
      overflow: hidden;
      color: #234532;
      font-size: 14px;
      font-weight: 800;
      line-height: 1.22;
      overflow-wrap: anywhere;
    }
    .cta-line {
      display: none;
      position: absolute;
      left: 112px;
      right: 112px;
      bottom: 54px;
      min-height: 38px;
      padding-top: 11px;
      color: #344458;
      border-top: 1px solid #b8c1cc;
      font-size: 15px;
      font-weight: 700;
      line-height: 1.15;
      text-align: center;
    }
    .cta-line.is-active {
      display: block;
    }
  </style>
</head>
<body>
  <main class="stage" id="stage">
    <header class="editor-bar">
      <div class="file-identity">
        <div class="file-name">${escapeHtml(config.fileLabel)}</div>
        <div class="file-mode">Resume review / editing original document</div>
      </div>
      <div class="save-state"><span class="save-dot"></span><span>Saved locally</span></div>
    </header>
    <section class="workspace">
      <article class="paper">
        <div class="resume-content" id="resumeContent">
          <header class="resume-header">
            <h1 class="candidate-name">${escapeHtml(config.candidate.name)}</h1>
            <div class="target-role">${escapeHtml(config.candidate.targetRole)}</div>
            <div class="contact-line">${escapeHtml(config.candidate.contactLine)}</div>
          </header>
          <section class="resume-section">
            <h2>PROFESSIONAL SUMMARY</h2>
            <p class="summary-copy">${escapeHtml(config.candidate.summary)}</p>
          </section>
          <section class="resume-section">
            <h2>TECHNICAL SKILLS</h2>
            <p class="skills-copy">${escapeHtml(config.candidate.skillsLine)}</p>
          </section>
          <section class="resume-section">
            <h2>PROFESSIONAL EXPERIENCE</h2>
            ${experiences}
          </section>
          ${renderProject(config.candidate.projects[0])}
          <section class="resume-section">
            <h2>EDUCATION &amp; CERTIFICATIONS</h2>
            <div class="education-grid">
              <div>
                <div class="education-label">EDUCATION</div>
                <div class="education-value">${escapeHtml(educationLine)}</div>
              </div>
              <div>
                <div class="education-label">CERTIFICATIONS</div>
                <div class="education-value">${escapeHtml(certificationLine)}</div>
              </div>
            </div>
          </section>
        </div>
      </article>

      <aside class="review-surface">
        <section class="review-panel" id="searchPanel">
          <div class="panel-kicker">LINE I'M STOPPING ON</div>
          <div class="panel-title opening-quote">&ldquo;${escapeHtml(config.edit.weakLine)}&rdquo;</div>
          <div class="panel-note opening-judgment">${escapeHtml(config.review.judgment)}</div>
          <div class="term-grid">${searchTerms}</div>
        </section>
        <section class="review-panel" id="proofPanel">
          <div class="panel-kicker">EVIDENCE CHECK</div>
          <div class="panel-title">${escapeHtml(config.review.proofTitle)}</div>
          <div class="panel-note">These highlighted lines are the source for the rewrite.</div>
          <div class="evidence-grid">${proofRows}</div>
        </section>
        <section class="review-panel" id="editPanel">
          <div class="panel-kicker">LIVE DOCUMENT EDIT</div>
          <div class="panel-title">Editing the original bullet</div>
          <div class="panel-note">Same line. Same evidence. Clearer wording.</div>
          <div class="edit-progress"><div class="edit-progress-fill" id="editProgress"></div></div>
          <div class="edit-status" id="editStatus">Selecting the vague wording</div>
          <div class="edit-detail" id="editDetail">The resume stays fixed while the text changes in place.</div>
        </section>
        <section class="review-panel" id="receiptPanel">
          <div class="panel-kicker">EVIDENCE CHECK COMPLETE</div>
          <div class="panel-title">${escapeHtml(config.review.receiptTitle)}</div>
          <div class="receipt-grid">${receiptRows}</div>
        </section>
      </aside>

      <div class="cta-line" id="ctaLine">${escapeHtml(config.review.cta)}</div>
    </section>
  </main>
  <script>
    const runtime = ${scriptJson(runtime)};
    const weakBullet = document.getElementById("weakBullet");
    const weakText = document.getElementById("weakText");
    const editCaret = document.getElementById("editCaret");
    const lineFlag = document.getElementById("lineFlag");
    const editProgress = document.getElementById("editProgress");
    const editStatus = document.getElementById("editStatus");
    const editDetail = document.getElementById("editDetail");
    const ctaLine = document.getElementById("ctaLine");
    const panels = {
      search: document.getElementById("searchPanel"),
      proof: document.getElementById("proofPanel"),
      edit: document.getElementById("editPanel"),
      receipt: document.getElementById("receiptPanel"),
    };
    const proofLines = Array.from(document.querySelectorAll(".proof-line"));
    const termRows = Array.from(document.querySelectorAll(".term-row"));
    const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));
    const smooth = (value) => {
      const x = clamp(value, 0, 1);
      return x * x * (3 - 2 * x);
    };
    const progress = (time, start, end) => clamp((time - start) / Math.max(0.001, end - start), 0, 1);
    const showPanel = (name) => {
      Object.entries(panels).forEach(([key, panel]) => {
        panel.classList.toggle("is-active", key === name);
      });
    };

    window.__renderAt = (requestedTime) => {
      const t = clamp(Number(requestedTime) || 0, 0, runtime.timeline.duration);
      const timeline = runtime.timeline;
      const selected = t >= timeline.select && t < timeline.delete;
      const deleting = t >= timeline.delete && t < timeline.type;
      const typing = t >= timeline.type && t < timeline.receipt;
      const complete = t >= timeline.receipt;
      const proofActive = t >= timeline.proof && t < timeline.receipt;
      const weakActive = t >= timeline.weak && t < timeline.select;

      let visibleText = runtime.weakLine;
      if (deleting) {
        const amount = smooth(progress(t, timeline.delete, timeline.eraseEnd));
        visibleText = runtime.weakLine.slice(0, Math.ceil(runtime.weakLine.length * (1 - amount)));
      } else if (typing) {
        const amount = smooth(progress(t, timeline.type, timeline.typeEnd));
        visibleText = runtime.rewriteLine.slice(0, Math.floor(runtime.rewriteLine.length * amount));
      } else if (complete) {
        visibleText = runtime.rewriteLine;
      }
      weakText.textContent = visibleText;

      weakBullet.classList.toggle("is-weak", weakActive);
      weakBullet.classList.toggle("is-selected", selected);
      weakBullet.classList.toggle("is-deleting", deleting);
      weakBullet.classList.toggle("is-typing", typing);
      weakBullet.classList.toggle("is-complete", complete);
      proofLines.forEach((line) => line.classList.toggle("is-proof", proofActive));
      editCaret.style.opacity = Math.floor(t * 4) % 2 === 0 ? "1" : "0";

      if (weakActive) {
        lineFlag.textContent = runtime.judgment;
      } else if (selected) {
        lineFlag.textContent = "SELECT";
      } else if (deleting) {
        lineFlag.textContent = "DELETE";
      } else if (typing) {
        lineFlag.textContent = "REWRITE";
      } else if (complete) {
        lineFlag.textContent = "REVISED";
      } else {
        lineFlag.textContent = "";
      }
      lineFlag.style.display = t >= timeline.weak ? "block" : "none";

      const searchWindow = Math.max(3.2, Math.min(6, timeline.proof - timeline.weak));
      const activeTerms = Math.min(
        termRows.length,
        Math.max(1, Math.floor(progress(t, timeline.weak, timeline.weak + searchWindow) * termRows.length) + 1),
      );
      termRows.forEach((row, index) => row.classList.toggle("is-active", index < activeTerms));

      if (t < timeline.proof) {
        showPanel("search");
      } else if (t < timeline.select) {
        showPanel("proof");
      } else if (t < timeline.receipt) {
        showPanel("edit");
      } else {
        showPanel("receipt");
      }

      if (selected) {
        editProgress.style.width = "12%";
        editStatus.textContent = "Selecting the vague wording";
        editDetail.textContent = "Read the weak line once before removing it.";
      } else if (deleting) {
        const amount = progress(t, timeline.delete, timeline.type);
        editProgress.style.width = String(Math.round(12 + amount * 28)) + "%";
        editStatus.textContent = "Deleting the weak line";
        editDetail.textContent = "Remove the vague wording; keep the underlying proof.";
      } else if (typing) {
        const amount = progress(t, timeline.type, timeline.typeEnd);
        editProgress.style.width = String(Math.round(40 + amount * 60)) + "%";
        editStatus.textContent = "Typing the proof-backed rewrite";
        editDetail.textContent = "Tool, volume, and result come from visible resume evidence.";
      }
      ctaLine.classList.toggle("is-active", t >= timeline.cta);
      document.documentElement.dataset.captureTime = t.toFixed(3);
      return t;
    };

    window.__validateLayout = () => {
      const issues = [];
      const stage = document.getElementById("stage");
      const resumeContent = document.getElementById("resumeContent");
      const weakBounds = weakText.getBoundingClientRect();
      if (document.documentElement.scrollWidth > 1080 || document.documentElement.scrollHeight > 1920) {
        issues.push("document exceeds the 1080x1920 viewport");
      }
      if (stage.scrollWidth > stage.clientWidth || stage.scrollHeight > stage.clientHeight) {
        issues.push("stage content overflows");
      }
      if (resumeContent.scrollHeight > resumeContent.clientHeight + 1) {
        issues.push("resume overflows paper by " + (resumeContent.scrollHeight - resumeContent.clientHeight) + "px");
      }
      if (weakBounds.height > 35) {
        issues.push("editable bullet exceeds two lines (" + Math.round(weakBounds.height) + "px)");
      }
      document.querySelectorAll("[data-fit-check]").forEach((element) => {
        if (element.scrollWidth > element.clientWidth + 1 || element.scrollHeight > element.clientHeight + 1) {
          issues.push((element.dataset.fitCheck || "element") + " overflows");
        }
      });
      return {
        issues,
        metrics: {
          viewport: [document.documentElement.scrollWidth, document.documentElement.scrollHeight],
          resume: [resumeContent.clientHeight, resumeContent.scrollHeight],
          weakLineHeight: Math.round(weakBounds.height),
        },
      };
    };

    window.__renderAt(0);
    document.documentElement.dataset.captureReady = "true";
  </script>
</body>
</html>`;
}

function phaseLabel(config, time) {
  const timeline = config.timeline;
  if (time < timeline.proof) return "Weak line";
  if (time < timeline.select) return "Proof reveal";
  if (time < timeline.delete) return "Text selected";
  if (time < timeline.type) return "Visible deletion";
  if (time < timeline.receipt) return "Same-slot rewrite";
  if (time < timeline.cta) return "Evidence receipt";
  return "Receipt and CTA";
}

async function renderAt(page, time) {
  await page.evaluate((value) => window.__renderAt(value), time);
}

async function validateLayout(page, config) {
  const checkpoints = uniqueStrings([
    "0",
    config.timeline.proof.toFixed(3),
    config.timeline.select.toFixed(3),
    ((config.timeline.type + config.timeline.typeEnd) / 2).toFixed(3),
    config.timeline.receipt.toFixed(3),
    config.timeline.cta.toFixed(3),
  ]).map(Number);
  const failures = [];
  for (const time of checkpoints) {
    await renderAt(page, time);
    const report = await page.evaluate(() => window.__validateLayout());
    if (report.issues.length) {
      failures.push(`${time.toFixed(2)}s: ${report.issues.join(", ")}`);
    }
  }
  if (failures.length) {
    throw new CliError("Layout validation failed.", failures);
  }
}

async function capturePng(page, time, outputPath) {
  await renderAt(page, time);
  await page.screenshot({
    path: outputPath,
    type: "png",
    animations: "disabled",
    caret: "hide",
    fullPage: false,
  });
}

function runCommand(executable, commandArgs, label) {
  const result = spawnSync(executable, commandArgs, {
    encoding: "utf8",
    windowsHide: true,
    maxBuffer: 20 * 1024 * 1024,
  });
  if (result.error) {
    throw new CliError(`${label} could not start.`, result.error.message);
  }
  if (result.status !== 0) {
    throw new CliError(
      `${label} failed with exit code ${result.status}.`,
      [result.stderr?.trim(), result.stdout?.trim()].filter(Boolean),
    );
  }
  return result.stdout;
}

function encodeVideo(dependencies, framesDir, config, out) {
  fs.mkdirSync(path.dirname(out), { recursive: true });
  const framePattern = path.join(framesDir, "frame-%06d.png");
  runCommand(
    dependencies.ffmpeg,
    [
      "-y",
      "-hide_banner",
      "-loglevel",
      "error",
      "-framerate",
      String(config.captureFps),
      "-start_number",
      "1",
      "-i",
      framePattern,
      "-vf",
      `fps=${config.outputFps}:round=near,setsar=1`,
      "-c:v",
      "libx264",
      "-preset",
      "medium",
      "-crf",
      "17",
      "-pix_fmt",
      "yuv420p",
      "-profile:v",
      "high",
      "-level",
      "4.1",
      "-g",
      String(config.outputFps * 2),
      "-keyint_min",
      String(config.outputFps * 2),
      "-sc_threshold",
      "0",
      "-threads",
      "1",
      "-an",
      "-map_metadata",
      "-1",
      "-movflags",
      "+faststart",
      out,
    ],
    "ffmpeg encoding",
  );
  if (!fs.existsSync(out) || fs.statSync(out).size < 1024) {
    throw new CliError(`ffmpeg did not create a usable MP4: ${out}`);
  }
}

function probeVideo(ffprobe, videoPath, config) {
  const output = runCommand(
    ffprobe,
    [
      "-v",
      "error",
      "-show_entries",
      "stream=index,codec_type,codec_name,width,height,pix_fmt,avg_frame_rate:format=duration,size",
      "-of",
      "json",
      videoPath,
    ],
    "ffprobe validation",
  );
  let report;
  try {
    report = JSON.parse(output);
  } catch (error) {
    throw new CliError("ffprobe returned invalid JSON.", error.message);
  }
  const streams = Array.isArray(report.streams) ? report.streams : [];
  const videoStreams = streams.filter((stream) => stream.codec_type === "video");
  const audioStreams = streams.filter((stream) => stream.codec_type === "audio");
  const video = videoStreams[0];
  const errors = [];
  if (videoStreams.length !== 1) errors.push(`expected one video stream, found ${videoStreams.length}`);
  if (!video || video.codec_name !== "h264") errors.push(`expected H.264, found ${video?.codec_name || "none"}`);
  if (!video || video.width !== VIEWPORT.width || video.height !== VIEWPORT.height) {
    errors.push(`expected 1080x1920, found ${video?.width || 0}x${video?.height || 0}`);
  }
  if (!video || video.pix_fmt !== "yuv420p") {
    errors.push(`expected yuv420p, found ${video?.pix_fmt || "none"}`);
  }
  if (audioStreams.length) errors.push(`expected no audio streams, found ${audioStreams.length}`);
  const [rateNumerator, rateDenominator] = String(video?.avg_frame_rate || "0/1")
    .split("/")
    .map(Number);
  const rate = rateDenominator ? rateNumerator / rateDenominator : 0;
  if (Math.abs(rate - config.outputFps) > 0.01) {
    errors.push(`expected ${config.outputFps} fps, found ${rate || "unknown"}`);
  }
  if (errors.length) throw new CliError("Encoded MP4 failed media validation.", errors);
  return {
    codec: video.codec_name,
    width: video.width,
    height: video.height,
    pixelFormat: video.pix_fmt,
    fps: rate,
    audioStreams: audioStreams.length,
    durationSec: Number(Number(report.format?.duration || 0).toFixed(3)),
    sizeBytes: Number(report.format?.size || fs.statSync(videoPath).size),
  };
}

function clearStoryboardFiles(directory) {
  fs.mkdirSync(directory, { recursive: true });
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.isFile() && /^story-\d{2}-\d{6}ms\.png$/i.test(entry.name)) {
      fs.unlinkSync(path.join(directory, entry.name));
    }
  }
}

async function captureStoryboards(page, config, plan) {
  clearStoryboardFiles(plan.storyboardDir);
  const items = [];
  for (const [index, time] of config.storyboardTimes.entries()) {
    const name = `story-${String(index + 1).padStart(2, "0")}-${String(Math.round(time * 1000)).padStart(6, "0")}ms.png`;
    const file = path.join(plan.storyboardDir, name);
    await capturePng(page, time, file);
    items.push({ file, time, label: phaseLabel(config, time) });
  }
  return items;
}

async function createContactSheet(browser, items, outputPath) {
  const columns = 3;
  const thumbWidth = 324;
  const thumbHeight = 576;
  const gap = 18;
  const headerHeight = 72;
  const labelHeight = 42;
  const rowHeight = thumbHeight + labelHeight + gap;
  const rows = Math.ceil(items.length / columns);
  const pageHeight = headerHeight + rows * rowHeight + 24;
  const cards = items.map((item) => {
    const dataUrl = `data:image/png;base64,${fs.readFileSync(item.file).toString("base64")}`;
    return `<figure>
      <img src="${dataUrl}" alt="">
      <figcaption><strong>${escapeHtml(item.label)}</strong><span>${item.time.toFixed(2)}s</span></figcaption>
    </figure>`;
  }).join("");
  const html = `<!doctype html>
  <html><head><meta charset="utf-8"><style>
    * { box-sizing: border-box; letter-spacing: 0; }
    html, body { margin: 0; width: 1080px; height: ${pageHeight}px; overflow: hidden; background: #edf1f5; font-family: Arial, "Segoe UI", sans-serif; }
    header { height: ${headerHeight}px; padding: 22px 24px 0; color: #172033; font-size: 22px; font-weight: 800; }
    main { display: grid; grid-template-columns: repeat(3, ${thumbWidth}px); gap: ${gap}px; padding: 0 18px 24px; }
    figure { width: ${thumbWidth}px; margin: 0; overflow: hidden; border: 1px solid #bfc8d3; border-radius: 4px; background: #fff; }
    img { display: block; width: ${thumbWidth}px; height: ${thumbHeight}px; object-fit: cover; }
    figcaption { display: flex; align-items: center; justify-content: space-between; height: ${labelHeight}px; padding: 0 10px; color: #556274; font-size: 11px; }
    figcaption strong { overflow: hidden; max-width: 235px; color: #172033; text-overflow: ellipsis; white-space: nowrap; }
  </style></head><body><header>Controlled browser editor v3 / storyboard</header><main>${cards}</main></body></html>`;
  const page = await browser.newPage({
    viewport: { width: VIEWPORT.width, height: pageHeight },
    deviceScaleFactor: 1,
    colorScheme: "light",
    reducedMotion: "reduce",
  });
  try {
    await page.setContent(html, { waitUntil: "load" });
    await page.waitForFunction(() => Array.from(document.images).every((image) => image.complete));
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    await page.screenshot({
      path: outputPath,
      type: "png",
      animations: "disabled",
      caret: "hide",
      fullPage: false,
    });
  } finally {
    await page.close();
  }
}

function safeRemoveTempFrames(framesDir) {
  const resolved = path.resolve(framesDir);
  const tempRoot = path.resolve(os.tmpdir());
  const relative = path.relative(tempRoot, resolved);
  if (
    relative.startsWith("..")
    || path.isAbsolute(relative)
    || !path.basename(resolved).startsWith("signal-controlled-resume-")
  ) {
    throw new CliError(`Refusing to remove unexpected frame directory: ${resolved}`);
  }
  fs.rmSync(resolved, { recursive: true, force: true });
}

async function runCapture(config, plan, dependencies, keepFrames) {
  const chromium = loadChromium(dependencies.playwright);
  let browser;
  let page;
  let framesDir = "";
  let succeeded = false;
  try {
    browser = await chromium.launch({
      executablePath: dependencies.browser,
      headless: true,
      args: [
        "--autoplay-policy=no-user-gesture-required",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-extensions",
        "--disable-features=Translate,MediaRouter,OptimizationHints",
        "--disable-sync",
        "--force-color-profile=srgb",
        "--hide-scrollbars",
        "--mute-audio",
        "--no-default-browser-check",
        "--no-first-run",
      ],
    });
    page = await browser.newPage({
      viewport: VIEWPORT,
      deviceScaleFactor: 1,
      colorScheme: "light",
      reducedMotion: "reduce",
      locale: "en-US",
      timezoneId: "UTC",
    });
    await page.setContent(buildEditorHtml(config), { waitUntil: "load" });
    await page.waitForFunction(() => document.documentElement.dataset.captureReady === "true");
    await page.evaluate(() => document.fonts.ready);
    await validateLayout(page, config);

    framesDir = fs.mkdtempSync(path.join(os.tmpdir(), "signal-controlled-resume-"));
    const frameCount = Math.ceil(config.durationSec * config.captureFps);
    let nextProgress = 10;
    for (let index = 0; index < frameCount; index += 1) {
      const time = index / config.captureFps;
      const framePath = path.join(
        framesDir,
        `frame-${String(index + 1).padStart(6, "0")}.png`,
      );
      await capturePng(page, time, framePath);
      const percent = Math.floor(((index + 1) / frameCount) * 100);
      if (percent >= nextProgress) {
        process.stderr.write(`capture ${Math.min(100, nextProgress)}%\n`);
        nextProgress += 10;
      }
    }

    encodeVideo(dependencies, framesDir, config, plan.out);
    const media = probeVideo(dependencies.ffprobe, plan.out, config);
    let storyboards = [];
    if (plan.storyboardEnabled) {
      storyboards = await captureStoryboards(page, config, plan);
      await createContactSheet(browser, storyboards, plan.contactSheet);
    }
    succeeded = true;
    return {
      status: "rendered",
      config: config.configPath,
      video: plan.out,
      dimensions: VIEWPORT,
      captureFps: config.captureFps,
      outputFps: config.outputFps,
      frameCount,
      durationSec: config.durationSec,
      temporaryFrames: keepFrames ? framesDir : null,
      storyboardDir: plan.storyboardEnabled ? plan.storyboardDir : null,
      storyboardFrames: storyboards.length,
      contactSheet: plan.storyboardEnabled ? plan.contactSheet : null,
      media,
    };
  } catch (error) {
    if (framesDir) {
      error.details = [
        ...(Array.isArray(error.details) ? error.details : []),
        `Temporary frames retained at: ${framesDir}`,
      ];
    }
    throw error;
  } finally {
    if (page && !page.isClosed()) await page.close().catch(() => {});
    if (browser) await browser.close().catch(() => {});
    if (succeeded && framesDir && !keepFrames) safeRemoveTempFrames(framesDir);
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.get("help")) {
    printHelp();
    return;
  }
  const configArg = args.get("config");
  if (!configArg) {
    throw new CliError("Missing --config <brief.json>. Use --help for usage.");
  }
  const configPath = resolveCliPath(configArg);
  if (!fs.existsSync(configPath)) {
    throw new CliError(`Config does not exist: ${configPath}`);
  }
  const raw = readConfig(configPath);
  const config = normalizeConfig(raw, args);
  config.configPath = configPath;
  const plan = outputPlan(raw, args, configPath);
  const dependencies = discoverDependencies();
  const problems = dependencyProblems(dependencies);

  if (args.get("dry-run")) {
    process.stdout.write(`${JSON.stringify({
      status: "dry-run",
      ready: problems.length === 0,
      config: configPath,
      dimensions: VIEWPORT,
      durationSec: config.durationSec,
      captureFps: config.captureFps,
      outputFps: config.outputFps,
      experienceBullets: config.candidate.experience.reduce(
        (count, experience) => count + experience.bullets.length,
        0,
      ),
      proofReferences: config.edit.proofs.length,
      storyboardTimes: config.storyboardTimes,
      outputs: plan,
      dependencies: {
        playwright: dependencies.playwright
          ? `${dependencies.playwright.packageName} (${dependencies.playwright.nodeModulesDir})`
          : null,
        browser: dependencies.browser || null,
        ffmpeg: dependencies.ffmpeg || null,
        ffprobe: dependencies.ffprobe || null,
      },
      problems,
    }, null, 2)}\n`);
    if (problems.length) process.exitCode = 2;
    return;
  }

  if (problems.length) {
    throw new CliError("Capture dependencies are not ready.", problems);
  }
  const result = await runCapture(config, plan, dependencies, Boolean(args.get("keep-frames")));
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

try {
  await main();
} catch (error) {
  const debug = process.argv.includes("--debug");
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`controlled_resume_capture: ${message}\n`);
  const details = Array.isArray(error?.details) ? error.details : [];
  for (const detail of details.filter(Boolean)) {
    process.stderr.write(`  - ${detail}\n`);
  }
  if (debug && error?.stack) process.stderr.write(`${error.stack}\n`);
  process.exitCode = 1;
}
