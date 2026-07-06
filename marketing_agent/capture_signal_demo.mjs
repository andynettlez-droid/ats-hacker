#!/usr/bin/env node
import { createRequire } from "node:module";
import { execFileSync, spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const key = process.argv[i];
  if (key.startsWith("--")) {
    args.set(key.slice(2), process.argv[i + 1]?.startsWith("--") ? "true" : process.argv[++i]);
  }
}

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const defaultOut = path.join(os.homedir(), "Downloads", "signal_feature_demo_recording.mp4");
const out = path.resolve(args.get("out") || defaultOut);
const url = args.get("url") || "http://localhost:3100/?capture=signal-demo-recording";
const seconds = Number(args.get("seconds") || 11);
const viewport = {
  width: Number(args.get("width") || 1080),
  height: Number(args.get("height") || 1920),
};

function findPlaywrightCore() {
  const candidates = [
    process.env.PLAYWRIGHT_CORE_DIR,
    path.join(os.tmpdir(), "signal-playwright-core", "node_modules"),
    path.join(root, "node_modules"),
    path.join(root, "web", "node_modules"),
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, "playwright-core"))) return candidate;
  }
  throw new Error(
    "playwright-core not found. Install it outside the repo with: npm.cmd install playwright-core --prefix %TEMP%\\signal-playwright-core --no-save",
  );
}

function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) return candidate;
  }
  throw new Error("Chrome or Edge executable not found.");
}

function findTool(name) {
  const command = spawnSync("where.exe", [name], { encoding: "utf8" });
  if (command.status === 0) {
    return command.stdout.split(/\r?\n/).map((line) => line.trim()).find(Boolean);
  }
  const winget = path.join(process.env.LOCALAPPDATA || "", "Microsoft", "WinGet", "Packages");
  if (fs.existsSync(winget)) {
    const ps = spawnSync(
      "powershell",
      [
        "-NoProfile",
        "-Command",
        `Get-ChildItem -Path '${winget.replace(/'/g, "''")}' -Recurse -Filter '${name}.exe' -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName`,
      ],
      { encoding: "utf8" },
    );
    const found = ps.stdout.trim();
    if (found) return found;
  }
  throw new Error(`${name} not found.`);
}

const require = createRequire(path.join(findPlaywrightCore(), "playwright-core-importer.js"));
const { chromium } = require("playwright-core");

const runId = new Date().toISOString().replace(/[-:T.Z]/g, "").slice(0, 14);
const framesDir = path.join(os.tmpdir(), `signal-demo-frames-${runId}`);
fs.rmSync(framesDir, { recursive: true, force: true });
fs.mkdirSync(framesDir, { recursive: true });

const browser = await chromium.launch({
  executablePath: findChrome(),
  headless: true,
  args: [
    "--disable-web-security",
    "--disable-features=IsolateOrigins,site-per-process",
    "--autoplay-policy=no-user-gesture-required",
  ],
});

const page = await browser.newPage({
  viewport,
  deviceScaleFactor: 1,
});
await page.addStyleTag({
  content: `
    nextjs-portal,
    [data-nextjs-dialog-overlay],
    [data-nextjs-toast],
    [data-nextjs-errors-dialog],
    [data-nextjs-dev-tools-button],
    [aria-label*="Next.js"] {
      display: none !important;
      opacity: 0 !important;
      pointer-events: none !important;
    }
  `,
}).catch(() => {});

await page.route("**/api/score", async (route) => {
  await page.waitForTimeout(650);
  await route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      score: 34,
      matchedKeywords: ["marketing campaigns", "social media", "team leadership"],
      missingKeywords: [
        "Demand Generation",
        "LinkedIn Ads",
        "HubSpot",
        "CAC/LTV",
        "Marketing Operations",
        "Paid Social",
        "Campaign Analytics",
        "Lifecycle Marketing",
      ],
      verdict:
        "Real experience is there, but the resume misses the demand-generation language recruiters search for.",
    }),
  });
});

await page.goto(url, { waitUntil: "networkidle" });
await page.addStyleTag({
  content: `
    nextjs-portal,
    [data-nextjs-dialog-overlay],
    [data-nextjs-toast],
    [data-nextjs-errors-dialog],
    [data-nextjs-dev-tools-button],
    [aria-label*="Next.js"] {
      display: none !important;
      opacity: 0 !important;
      pointer-events: none !important;
    }
  `,
}).catch(() => {});
await page.evaluate(() => {
  const removeDevChrome = () => {
    document.querySelectorAll("nextjs-portal, [data-nextjs-dialog-overlay], [data-nextjs-toast]").forEach((el) => el.remove());
  };
  removeDevChrome();
  window.setInterval(removeDevChrome, 250);
});
await page.evaluate(() => {
  document.documentElement.style.scrollBehavior = "auto";
});
await page.evaluate(() => {
  const productLabel = Array.from(document.querySelectorAll("span")).find((el) =>
    el.textContent?.includes("Product entry point"),
  );
  const section = productLabel?.closest("section");
  if (section) {
    const y = section.getBoundingClientRect().top + window.scrollY - 76;
    window.scrollTo(0, Math.max(0, y));
  }
});
await page.waitForTimeout(400);

const session = await page.context().newCDPSession(page);
let frame = 0;
let firstFrameAt = 0;
let lastFrameAt = 0;
session.on("Page.screencastFrame", async (payload) => {
  frame += 1;
  if (!firstFrameAt) firstFrameAt = Date.now();
  lastFrameAt = Date.now();
  const name = `frame-${String(frame).padStart(5, "0")}.png`;
  fs.writeFileSync(path.join(framesDir, name), Buffer.from(payload.data, "base64"));
  await session.send("Page.screencastFrameAck", { sessionId: payload.sessionId });
});

await session.send("Page.startScreencast", {
  format: "png",
  quality: 100,
  maxWidth: viewport.width,
  maxHeight: viewport.height,
  everyNthFrame: 1,
});

await page.waitForTimeout(500);
await page.getByRole("button", { name: /Run sample teardown/i }).click();
await page.getByText("Signal Match Score").waitFor({ timeout: 6000 });
await page.getByText("Signal Match Score").scrollIntoViewIfNeeded();
await page.waitForTimeout(3000);
await page.getByText("Missing keywords").scrollIntoViewIfNeeded();
await page.waitForTimeout(1700);
await page.getByText("One-bullet unlock preview").scrollIntoViewIfNeeded();
await page.waitForTimeout(Math.max(500, (seconds * 1000) - 8500));

await session.send("Page.stopScreencast").catch(() => {});
await browser.close();

if (frame < 30) {
  throw new Error(`Only captured ${frame} frames; expected at least 30.`);
}

const actualSeconds = Math.max(1, (lastFrameAt - firstFrameAt) / 1000);
const fps = Math.max(8, Math.min(30, Math.round(frame / actualSeconds)));
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
    "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1",
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
      status: "captured",
      url,
      out,
      frames: frame,
      captureFps: fps,
      durationSec: Number((frame / fps).toFixed(2)),
      framesDir,
    },
    null,
    2,
  ),
);
