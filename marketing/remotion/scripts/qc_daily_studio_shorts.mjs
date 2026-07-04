import { existsSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseMedia } from "@remotion/media-parser";
import { nodeReader } from "@remotion/media-parser/node";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const remotionDir = path.resolve(__dirname, "..");
const rootDir = path.resolve(remotionDir, "..", "..");
const outDir = path.join(remotionDir, "out");
const publicDir = path.join(remotionDir, "public");
const autopostDir = path.join(rootDir, "marketing", "autopost");
const videosDir = path.join(autopostDir, "videos");
const postsPath = path.join(autopostDir, "posts.json");
const reportPath = path.join(remotionDir, "out", "daily-studio-shorts-qc.json");

const DEFAULT_DRAFTS = path.join(
  rootDir,
  "marketing",
  "daily_content",
  "2026-06-28-ai-resumes-all-sound-the-same-so-recruiters-search-for-proof",
  "autopost_drafts.json",
);

const UNSAFE_PATTERNS = [
  [/\bauto[-\s]?reject(?:ed|s|ion)?\b/i, "Avoid unsupported ATS auto-reject claims."],
  [/\bbeat(?:ing)?\s+(?:the\s+)?(?:bots?|ats)\b/i, "Avoid adversarial beat-the-ATS framing."],
  [/\bguarantee[ds]?\b|\bwill\s+land\b|\bland\s+your\s+dream\b/i, "Avoid outcome guarantees."],
  [/\b100%\s+(?:ats\s+)?compatible\b/i, "Avoid absolute compatibility claims."],
  [/\b(?:add|adds|adding|claim|claims|claiming|create|creates|creating)\s+fake\s+(?:experience|job|skill|credential)/i, "Avoid fake-experience language."],
  [/\b(?:invent(?:ed|ing)?|made up)\s+(?:experience|job|skill|credential)/i, "Avoid fake-experience language."],
];

const EXPECTED = {
  width: 1080,
  height: 1920,
  fps: 30,
  durationInSeconds: 45,
  minBytes: 1_000_000,
  minAudioSampleRate: 44_100,
};

const parseArgs = () => {
  const args = process.argv.slice(2);
  const options = {
    drafts: DEFAULT_DRAFTS,
    json: false,
    report: reportPath,
  };

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === "--drafts") {
      options.drafts = path.resolve(process.cwd(), args[i + 1]);
      i += 1;
    } else if (arg === "--json") {
      options.json = true;
    } else if (arg === "--report") {
      options.report = path.resolve(process.cwd(), args[i + 1]);
      i += 1;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return options;
};

const readJson = (filePath) => JSON.parse(readFileSync(filePath, "utf8"));

const rel = (filePath) => path.relative(rootDir, filePath).replaceAll(path.sep, "/");

const addCheck = (checks, ok, name, details = "") => {
  checks.push({ ok, name, details });
};

const hasUnsafeClaim = (value) => {
  const text = Array.isArray(value) ? value.join("\n") : String(value ?? "");
  return UNSAFE_PATTERNS
    .filter(([pattern]) => pattern.test(text))
    .map(([, message]) => message);
};

const resolveRootRef = (ref) => path.join(rootDir, String(ref).replace(/^marketing[\\/]/, "marketing/"));

const resolvePublicRef = (ref) => {
  if (!ref) {
    return null;
  }
  return path.join(publicDir, String(ref).replaceAll("\\", "/"));
};

const parseVideo = async (filePath) => {
  return parseMedia({
    src: filePath,
    reader: nodeReader,
    acknowledgeRemotionLicense: true,
    fields: {
      dimensions: true,
      durationInSeconds: true,
      fps: true,
      videoCodec: true,
      audioCodec: true,
      tracks: true,
      container: true,
      sampleRate: true,
      numberOfAudioChannels: true,
      slowVideoBitrate: true,
      slowAudioBitrate: true,
    },
  });
};

const checkProps = (draft, postsEntry, checks) => {
  const propsRef = draft.renderProps || postsEntry?.renderProps;
  addCheck(checks, Boolean(propsRef), "render props reference exists", propsRef || "");
  if (!propsRef) {
    return null;
  }

  const propsPath = resolveRootRef(propsRef);
  addCheck(checks, existsSync(propsPath), "render props file exists", rel(propsPath));
  if (!existsSync(propsPath)) {
    return null;
  }

  const props = readJson(propsPath);
  addCheck(checks, Boolean(props.hook), "hook is present", props.hook || "");
  addCheck(checks, Boolean(props.cta), "CTA is present", props.cta || "");
  addCheck(
    checks,
    String(props.cta || "").toLowerCase().includes("free") &&
      String(props.cta || "").toLowerCase().includes("signal"),
    "CTA leads with free Signal score",
    props.cta || "",
  );
  addCheck(
    checks,
    Number.isFinite(props.beforeScore) &&
      Number.isFinite(props.afterScore) &&
      props.afterScore > props.beforeScore,
    "score moves upward",
    `${props.beforeScore} -> ${props.afterScore}`,
  );
  addCheck(
    checks,
    Array.isArray(props.jobKeywords) && props.jobKeywords.length >= 3,
    "job keywords are concrete",
    Array.isArray(props.jobKeywords) ? props.jobKeywords.join(", ") : "",
  );
  addCheck(
    checks,
    props.audioReadiness?.studioVoiceover === true,
    "studio voiceover marked ready",
    props.audioReadiness?.reason || "",
  );
  addCheck(
    checks,
    props.audioReadiness?.quietMusic === true,
    "quiet music marked ready",
    props.audioReadiness?.reason || "",
  );

  const voiceoverPath = resolvePublicRef(props.voiceoverSrc);
  addCheck(
    checks,
    Boolean(voiceoverPath && existsSync(voiceoverPath)),
    "voiceover asset exists",
    voiceoverPath ? rel(voiceoverPath) : "missing voiceoverSrc",
  );

  const musicPath = resolvePublicRef(props.musicSrc);
  addCheck(
    checks,
    Boolean(musicPath && existsSync(musicPath)),
    "music asset exists",
    musicPath ? rel(musicPath) : "missing musicSrc",
  );

  const claimText = [
    draft.title,
    draft.caption,
    props.hook,
    props.subhook,
    props.beforeBullet,
    props.afterBullet,
    props.cta,
    ...(Array.isArray(props.weakBullets) ? props.weakBullets : []),
    ...(Array.isArray(props.jobKeywords) ? props.jobKeywords : []),
  ];
  const claimIssues = hasUnsafeClaim(claimText);
  addCheck(
    checks,
    claimIssues.length === 0,
    "claim safety text scan",
    claimIssues.join(" "),
  );

  return props;
};

const checkVideoMetadata = async (filePath, checks) => {
  const size = statSync(filePath).size;
  addCheck(checks, size >= EXPECTED.minBytes, "file size is plausible", `${size} bytes`);

  const metadata = await parseVideo(filePath);
  const dims = metadata.dimensions || {};
  addCheck(
    checks,
    dims.width === EXPECTED.width && dims.height === EXPECTED.height,
    "video is 1080x1920 vertical",
    `${dims.width}x${dims.height}`,
  );
  addCheck(
    checks,
    Math.abs(Number(metadata.durationInSeconds) - EXPECTED.durationInSeconds) <= 0.75,
    "duration matches composition",
    `${metadata.durationInSeconds}s`,
  );
  addCheck(
    checks,
    Math.abs(Number(metadata.fps) - EXPECTED.fps) <= 0.01,
    "fps is 30",
    `${metadata.fps}`,
  );
  addCheck(checks, metadata.container === "mp4", "container is mp4", metadata.container);
  addCheck(checks, metadata.videoCodec === "h264", "video codec is h264", metadata.videoCodec);
  addCheck(checks, metadata.audioCodec === "aac", "audio codec is aac", metadata.audioCodec);
  addCheck(
    checks,
    Number(metadata.sampleRate || 0) >= EXPECTED.minAudioSampleRate,
    "audio sample rate is studio-safe",
    `${metadata.sampleRate || "unknown"} Hz`,
  );
  addCheck(
    checks,
    Number(metadata.numberOfAudioChannels || 0) >= 1,
    "audio track has channels",
    `${metadata.numberOfAudioChannels || 0}`,
  );
  addCheck(
    checks,
    Array.isArray(metadata.tracks) && metadata.tracks.some((track) => track.type === "video"),
    "video track exists",
  );
  addCheck(
    checks,
    Array.isArray(metadata.tracks) && metadata.tracks.some((track) => track.type === "audio"),
    "audio track exists",
  );

  return {
    size,
    dimensions: metadata.dimensions,
    durationInSeconds: metadata.durationInSeconds,
    fps: metadata.fps,
    container: metadata.container,
    videoCodec: metadata.videoCodec,
    audioCodec: metadata.audioCodec,
    sampleRate: metadata.sampleRate,
    numberOfAudioChannels: metadata.numberOfAudioChannels,
    slowVideoBitrate: metadata.slowVideoBitrate,
    slowAudioBitrate: metadata.slowAudioBitrate,
  };
};

const main = async () => {
  const options = parseArgs();
  const drafts = readJson(options.drafts);
  const posts = readJson(postsPath);
  const studioDrafts = drafts.filter(
    (draft) => draft.composition === "ResumeCrimeScene" || String(draft.file || "").endsWith("-studio.mp4"),
  );

  const report = {
    generatedAt: new Date().toISOString(),
    drafts: rel(options.drafts),
    posts: rel(postsPath),
    expectedCount: studioDrafts.length,
    passed: false,
    assets: [],
  };

  if (studioDrafts.length === 0) {
    throw new Error(`No studio drafts found in ${options.drafts}`);
  }

  for (const draft of studioDrafts) {
    const fileName = path.basename(draft.file);
    const renderPath = path.join(outDir, fileName);
    const queuePath = path.join(videosDir, fileName);
    const postsEntry = posts.find((post) => post.file === draft.file);
    const checks = [];

    addCheck(checks, existsSync(renderPath), "rendered studio MP4 exists", rel(renderPath));
    addCheck(checks, existsSync(queuePath), "promoted queue MP4 exists", rel(queuePath));
    addCheck(checks, Boolean(postsEntry), "autopost entry exists", draft.file);
    addCheck(
      checks,
      postsEntry?.status === "review_required",
      "autopost entry is review-gated",
      postsEntry?.status || "missing",
    );
    addCheck(
      checks,
      Array.isArray(postsEntry?.platforms) &&
        ["tiktok", "instagram", "youtube"].every((platform) => postsEntry.platforms.includes(platform)),
      "autopost platforms include TikTok, Instagram, YouTube",
      Array.isArray(postsEntry?.platforms) ? postsEntry.platforms.join(", ") : "missing",
    );

    let renderMetadata = null;
    let queueMetadata = null;
    if (existsSync(renderPath)) {
      renderMetadata = await checkVideoMetadata(renderPath, checks);
    }
    if (existsSync(queuePath)) {
      queueMetadata = await checkVideoMetadata(queuePath, checks);
    }
    if (existsSync(renderPath) && existsSync(queuePath)) {
      addCheck(
        checks,
        statSync(renderPath).size === statSync(queuePath).size,
        "render and queue files match size",
        `${statSync(renderPath).size} vs ${statSync(queuePath).size}`,
      );
    }

    const props = checkProps(draft, postsEntry, checks);
    const passed = checks.every((check) => check.ok);

    report.assets.push({
      title: draft.title || postsEntry?.title || fileName,
      file: draft.file,
      passed,
      checks,
      render: renderMetadata,
      queue: queueMetadata,
      propsSummary: props
        ? {
            hook: props.hook,
            beforeScore: props.beforeScore,
            afterScore: props.afterScore,
            cta: props.cta,
            audioReadiness: props.audioReadiness,
          }
        : null,
    });
  }

  report.passed = report.assets.every((asset) => asset.passed);
  writeFileSync(options.report, `${JSON.stringify(report, null, 2)}\n`, "utf8");

  if (options.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    for (const asset of report.assets) {
      const icon = asset.passed ? "PASS" : "FAIL";
      console.log(`${icon} ${asset.file}`);
      for (const check of asset.checks.filter((item) => !item.ok)) {
        console.log(`  - ${check.name}: ${check.details}`);
      }
    }
    console.log(`\nReport: ${rel(options.report)}`);
    console.log(report.passed ? "Studio short QC passed." : "Studio short QC failed.");
  }

  if (!report.passed) {
    process.exitCode = 1;
  }
};

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
