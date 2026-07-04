import { existsSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseMedia } from "@remotion/media-parser";
import { nodeReader } from "@remotion/media-parser/node";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const remotionDir = path.resolve(__dirname, "..");
const rootDir = path.resolve(remotionDir, "..", "..");
const publicDir = path.join(remotionDir, "public");
const reportPath = path.join(remotionDir, "out", "daily-audio-assets-qc.json");

const dailyDir = path.join(
  rootDir,
  "marketing",
  "daily_content",
  "2026-06-28-ai-resumes-all-sound-the-same-so-recruiters-search-for-proof",
);
const DEFAULT_DRAFTS = path.join(dailyDir, "autopost_drafts.json");
const DEFAULT_MANIFEST = path.join(dailyDir, "channel_manifest.json");

const EXPECTED = {
  minVoiceoverDuration: 5,
  maxShortVoiceoverDuration: 49,
  maxEpisodeSegmentDuration: 80,
  minMusicDuration: 20,
  minVoiceoverBitrate: 64_000,
  minMusicBitrate: 96_000,
  minSampleRate: 44_100,
  maxShortMusicVolume: 0.18,
  maxEpisodeMusicVolume: 0.14,
  maxSfxVolume: 0.08,
  minVoiceoverVolume: 0.8,
  maxVoiceoverVolume: 1,
  minOpenAiVoiceoverSampleRate: 24_000,
};

const parseArgs = () => {
  const args = process.argv.slice(2);
  const options = {
    drafts: DEFAULT_DRAFTS,
    manifest: DEFAULT_MANIFEST,
    json: false,
    report: reportPath,
  };

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === "--drafts") {
      options.drafts = path.resolve(process.cwd(), args[i + 1]);
      i += 1;
    } else if (arg === "--manifest") {
      options.manifest = path.resolve(process.cwd(), args[i + 1]);
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

const resolveRootRef = (ref) => path.join(rootDir, String(ref).replace(/^marketing[\\/]/, "marketing/"));

const resolvePublicRef = (ref) => {
  if (!ref) {
    return null;
  }
  return path.join(publicDir, String(ref).replaceAll("\\", "/"));
};

const parseAudio = async (filePath) => {
  return parseMedia({
    src: filePath,
    reader: nodeReader,
    acknowledgeRemotionLicense: true,
    fields: {
      size: true,
      container: true,
      durationInSeconds: true,
      audioCodec: true,
      sampleRate: true,
      numberOfAudioChannels: true,
      slowAudioBitrate: true,
    },
  });
};

const checkVolume = (checks, value, min, max, name) => {
  const numeric = Number(value);
  addCheck(
    checks,
    Number.isFinite(numeric) && numeric >= min && numeric <= max,
    name,
    Number.isFinite(numeric) ? `${numeric}` : "missing",
  );
};

const collectShortAssets = (drafts) => {
  const items = [];
  for (const draft of drafts) {
    if (
      draft.composition !== "ResumeCrimeScene" &&
      !String(draft.file || "").endsWith("-studio.mp4")
    ) {
      continue;
    }
    const propsPath = resolveRootRef(draft.renderProps);
    const props = readJson(propsPath);
    const base = {
      scope: "short",
      title: draft.title,
      propsPath,
      props,
    };
    items.push({
      ...base,
      role: "voiceover",
      src: props.voiceoverSrc,
      volume: props.voiceoverVolume,
      provider: props.audioReadiness?.provider,
      minDuration: EXPECTED.minVoiceoverDuration,
      maxDuration: EXPECTED.maxShortVoiceoverDuration,
      minBitrate: EXPECTED.minVoiceoverBitrate,
    });
    items.push({
      ...base,
      role: "music",
      src: props.musicSrc,
      volume: props.musicVolume,
      minDuration: EXPECTED.minMusicDuration,
      maxDuration: null,
      minBitrate: EXPECTED.minMusicBitrate,
    });
    if (props.sfxSrc) {
      items.push({
        ...base,
        role: "sfx",
        src: props.sfxSrc,
        volume: props.sfxVolume,
        minDuration: 1,
        maxDuration: 45,
        minBitrate: 32_000,
      });
    }
  }
  return items;
};

const collectEpisodeAssets = (manifest) => {
  const items = [];
  const episodePropsRef = manifest.episode?.props;
  if (!episodePropsRef) {
    return items;
  }
  const propsPath = resolveRootRef(episodePropsRef);
  const props = readJson(propsPath);
  const base = {
    scope: "episode",
    title: props.title || manifest.topic || "Daily episode",
    propsPath,
    props,
  };
  items.push({
    ...base,
    role: "music",
    src: props.musicSrc,
    volume: props.musicVolume,
    minDuration: EXPECTED.minMusicDuration,
    maxDuration: null,
    minBitrate: EXPECTED.minMusicBitrate,
  });
  for (const [index, segment] of (props.voiceoverSegments || []).entries()) {
    items.push({
      ...base,
      role: "episode-voiceover",
      src: segment.src,
      volume: segment.volume ?? props.voiceoverVolume,
      fromFrame: segment.fromFrame,
      provider: segment.provider || props.audioReadiness?.provider,
      segmentIndex: index + 1,
      minDuration: EXPECTED.minVoiceoverDuration,
      maxDuration: EXPECTED.maxEpisodeSegmentDuration,
      minBitrate: EXPECTED.minVoiceoverBitrate,
    });
  }
  return items;
};

const checkAsset = async (item) => {
  const checks = [];
  const filePath = resolvePublicRef(item.src);
  const minSampleRate =
    item.role.includes("voiceover") && ["openai", "cached"].includes(item.provider)
      ? EXPECTED.minOpenAiVoiceoverSampleRate
      : EXPECTED.minSampleRate;

  addCheck(checks, Boolean(item.src), "asset source is set", item.src || "");
  addCheck(checks, Boolean(filePath && existsSync(filePath)), "asset exists", filePath ? rel(filePath) : "");

  if (item.role.includes("voiceover")) {
    checkVolume(
      checks,
      item.volume,
      EXPECTED.minVoiceoverVolume,
      EXPECTED.maxVoiceoverVolume,
      "voiceover volume is in studio narration range",
    );
  } else if (item.role === "music" && item.scope === "short") {
    checkVolume(checks, item.volume, 0.04, EXPECTED.maxShortMusicVolume, "short music volume is restrained");
  } else if (item.role === "music" && item.scope === "episode") {
    checkVolume(checks, item.volume, 0.04, EXPECTED.maxEpisodeMusicVolume, "episode music volume is restrained");
  } else if (item.role === "sfx") {
    checkVolume(checks, item.volume, 0, EXPECTED.maxSfxVolume, "SFX volume is restrained");
  }

  let metadata = null;
  if (filePath && existsSync(filePath)) {
    metadata = await parseAudio(filePath);
    const size = statSync(filePath).size;
    addCheck(checks, size > 1024, "asset size is plausible", `${size} bytes`);
    addCheck(checks, Boolean(metadata.audioCodec), "audio codec detected", metadata.audioCodec || "");
    addCheck(
      checks,
      Number(metadata.sampleRate || 0) >= minSampleRate,
      "sample rate meets provider floor",
      `${metadata.sampleRate || "unknown"} Hz (provider=${item.provider || "default"}, min=${minSampleRate})`,
    );
    addCheck(
      checks,
      Number(metadata.numberOfAudioChannels || 0) >= 1,
      "audio channels present",
      `${metadata.numberOfAudioChannels || 0}`,
    );
    addCheck(
      checks,
      Number(metadata.durationInSeconds || 0) >= item.minDuration,
      "duration is long enough",
      `${metadata.durationInSeconds || 0}s`,
    );
    if (item.maxDuration) {
      addCheck(
        checks,
        Number(metadata.durationInSeconds || 0) <= item.maxDuration,
        "duration is not excessive",
        `${metadata.durationInSeconds || 0}s`,
      );
    }
    addCheck(
      checks,
      Number(metadata.slowAudioBitrate || 0) >= item.minBitrate,
      "audio bitrate is plausible",
      `${Math.round(metadata.slowAudioBitrate || 0)} bps`,
    );
  }

  return {
    scope: item.scope,
    title: item.title,
    role: item.role,
    segmentIndex: item.segmentIndex,
    fromFrame: item.fromFrame,
    src: item.src,
    volume: item.volume,
    passed: checks.every((check) => check.ok),
    checks,
    metadata,
  };
};

const checkEpisodeTiming = (manifest) => {
  const checks = [];
  const episodePropsRef = manifest.episode?.props;
  addCheck(checks, Boolean(episodePropsRef), "episode props reference exists", episodePropsRef || "");
  if (!episodePropsRef) {
    return checks;
  }

  const props = readJson(resolveRootRef(episodePropsRef));
  const segments = props.voiceoverSegments || [];
  addCheck(checks, Array.isArray(segments) && segments.length >= 3, "episode has multiple voiceover segments", `${segments.length}`);
  const fromFrames = segments.map((segment) => Number(segment.fromFrame));
  const ascending = fromFrames.every((frame, index) => index === 0 || frame > fromFrames[index - 1]);
  addCheck(checks, ascending, "episode voiceover segments are chronological", fromFrames.join(", "));
  addCheck(
    checks,
    props.audioReadiness?.studioVoiceover === true,
    "episode audio readiness marks studio voiceover ready",
    props.audioReadiness?.reason || "",
  );
  addCheck(
    checks,
    props.audioReadiness?.quietMusic === true,
    "episode audio readiness marks quiet music ready",
    props.audioReadiness?.reason || "",
  );
  return checks;
};

const main = async () => {
  const options = parseArgs();
  const drafts = readJson(options.drafts);
  const manifest = readJson(options.manifest);
  const assets = [...collectShortAssets(drafts), ...collectEpisodeAssets(manifest)].filter((item) => item.src);

  if (assets.length === 0) {
    throw new Error("No audio assets found for daily shorts or episode.");
  }

  const results = [];
  for (const item of assets) {
    results.push(await checkAsset(item));
  }

  const episodeTimingChecks = checkEpisodeTiming(manifest);
  const report = {
    generatedAt: new Date().toISOString(),
    drafts: rel(options.drafts),
    manifest: rel(options.manifest),
    passed: results.every((item) => item.passed) && episodeTimingChecks.every((check) => check.ok),
    notes: [
      "This gate validates asset presence, codec metadata, duration, sample rate, bitrate, channels, and mix volume settings.",
      "It does not measure LUFS or true peak; add ffmpeg/ffprobe or PCM sample analysis for that later gate.",
    ],
    episodeTimingChecks,
    assets: results,
  };

  writeFileSync(options.report, `${JSON.stringify(report, null, 2)}\n`, "utf8");

  if (options.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    for (const result of results) {
      const icon = result.passed ? "PASS" : "FAIL";
      const label = result.segmentIndex ? `${result.role} ${result.segmentIndex}` : result.role;
      console.log(`${icon} ${result.scope} ${label}: ${result.src}`);
      for (const check of result.checks.filter((item) => !item.ok)) {
        console.log(`  - ${check.name}: ${check.details}`);
      }
    }
    for (const check of episodeTimingChecks.filter((item) => !item.ok)) {
      console.log(`FAIL episode timing: ${check.name}: ${check.details}`);
    }
    console.log(`\nReport: ${rel(options.report)}`);
    console.log(report.passed ? "Daily audio asset QC passed." : "Daily audio asset QC failed.");
  }

  if (!report.passed) {
    process.exitCode = 1;
  }
};

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
