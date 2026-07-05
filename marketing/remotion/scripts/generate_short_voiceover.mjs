#!/usr/bin/env node
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseMedia } from "@remotion/media-parser";
import { nodeReader } from "@remotion/media-parser/node";

const __dirname = dirname(fileURLToPath(import.meta.url));
const remotionDir = resolve(__dirname, "..");
const root = resolve(remotionDir, "..", "..");
const audioDir = join(remotionDir, "public", "audio");

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const arg = process.argv[i];
  if (arg.startsWith("--")) {
    const next = process.argv[i + 1];
    args.set(arg, next && !next.startsWith("--") ? next : true);
    if (next && !next.startsWith("--")) i += 1;
  }
}

const loadEnvFile = (path) => {
  if (!existsSync(path)) return;
  for (const line of readFileSync(path, "utf8").split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/i);
    if (!match) continue;
    process.env[match[1]] = match[2].replace(/^["']|["']$/g, "");
  }
};

loadEnvFile(join(root, "marketing_agent", ".env"));
loadEnvFile(join(root, "marketing", "autopost", ".env"));

const propsPath = resolve(remotionDir, String(args.get("--props") || "props_gold_signal_search_test.json"));
const force = args.has("--force");
const requireElevenLabs = args.has("--require-elevenlabs") || process.env.REQUIRE_ELEVENLABS === "true";
const provider = String(args.get("--provider") || process.env.TTS_PROVIDER || "elevenlabs").toLowerCase();
const elevenLabsApiKey = process.env.ELEVENLABS_API_KEY;
const voiceId = process.env.ELEVENLABS_VOICE_ID || "21m00Tcm4TlvDq8ikWAM";
const modelId = process.env.ELEVENLABS_MODEL_ID || "eleven_multilingual_v2";

if (provider !== "elevenlabs") {
  throw new Error("Gold-standard short voiceover currently requires provider=elevenlabs.");
}
if (!elevenLabsApiKey || elevenLabsApiKey === "your_elevenlabs_api_key_here") {
  throw new Error("ELEVENLABS_API_KEY is not configured in marketing_agent/.env or marketing/autopost/.env.");
}

const readJson = (path) => JSON.parse(readFileSync(path, "utf8"));
const writeJson = (path, value) => writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
const safeSlug = (value) =>
  String(value || "signal-short")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64) || "signal-short";

const normalizeAlignmentToCaptions = (alignment = {}) => {
  const characters = Array.isArray(alignment.characters) ? alignment.characters : [];
  const starts = Array.isArray(alignment.character_start_times_seconds) ? alignment.character_start_times_seconds : [];
  const ends = Array.isArray(alignment.character_end_times_seconds) ? alignment.character_end_times_seconds : [];
  const captions = [];
  let word = "";
  let wordStart = null;
  let wordEnd = null;

  characters.forEach((character, index) => {
    const char = String(character);
    const start = Number.isFinite(Number(starts[index])) ? Number(starts[index]) : null;
    const end = Number.isFinite(Number(ends[index])) ? Number(ends[index]) : start;
    if (/\s/.test(char)) {
      if (word) {
        const startMs = Math.round((wordStart || 0) * 1000);
        captions.push({
          text: word,
          startMs,
          endMs: Math.round((wordEnd || wordStart || 0) * 1000),
          timestampMs: startMs,
          confidence: null,
        });
      }
      word = "";
      wordStart = null;
      wordEnd = null;
      return;
    }
    if (wordStart === null) wordStart = start || 0;
    word += char;
    wordEnd = end || wordStart;
  });

  if (word) {
    const startMs = Math.round((wordStart || 0) * 1000);
    captions.push({
      text: word,
      startMs,
      endMs: Math.round((wordEnd || wordStart || 0) * 1000),
      timestampMs: startMs,
      confidence: null,
    });
  }
  return captions;
};

const getAudioDuration = async (filePath) => {
  const metadata = await parseMedia({
    src: filePath,
    reader: nodeReader,
    acknowledgeRemotionLicense: true,
    fields: {
      durationInSeconds: true,
    },
  });
  return Number(metadata.durationInSeconds || 0);
};

const main = async () => {
  mkdirSync(audioDir, { recursive: true });
  const props = readJson(propsPath);
  const text = String(props.voiceover_text || "").trim();
  if (!text) throw new Error(`${relative(root, propsPath)} is missing voiceover_text.`);

  const slug = safeSlug(props.slug || props.title || props.hook || "gold-signal-short");
  const destPath = join(audioDir, `${slug}-voiceover.mp3`);
  const alignmentPath = destPath.replace(/\.mp3$/i, ".alignment.json");

  let captions = [];
  let withTimestamps = false;
  if (force || !existsSync(destPath) || !existsSync(alignmentPath)) {
    const director = props.voiceDirector || {};
    const body = {
      text,
      model_id: modelId,
      voice_settings: {
        stability: Number(director.stability ?? 0.42),
        similarity_boost: Number(director.similarity_boost ?? director.similarityBoost ?? 0.82),
        style: Number(director.style ?? 0.38),
        use_speaker_boost: director.use_speaker_boost ?? director.useSpeakerBoost ?? true,
      },
      previous_text:
        director.previous_text ||
        "Okay, I am reading this resume like a real recruiter would, not giving a product demo.",
      next_text: director.next_text || "Now show the score receipt, then the quick fix.",
      output_format: "mp3_44100_128",
    };
    const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}/with-timestamps`, {
      method: "POST",
      headers: {
        "xi-api-key": elevenLabsApiKey,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const errorBody = await response.text();
      if (requireElevenLabs) {
        throw new Error(`ElevenLabs timestamp TTS failed ${response.status}: ${errorBody.slice(0, 240)}`);
      }
      throw new Error(`ElevenLabs timestamp TTS failed ${response.status}: ${errorBody.slice(0, 240)}`);
    }
    const payload = await response.json();
    if (!payload.audio_base64) throw new Error("ElevenLabs response did not include audio_base64.");
    writeFileSync(destPath, Buffer.from(payload.audio_base64, "base64"));
    const alignment = payload.normalized_alignment || payload.alignment || {};
    captions = normalizeAlignmentToCaptions(alignment);
    withTimestamps = true;
    writeJson(alignmentPath, {
      provider: "elevenlabs",
      withTimestamps,
      captions,
      alignment,
      voiceSettings: body.voice_settings,
    });
  } else {
    const alignment = readJson(alignmentPath);
    captions = Array.isArray(alignment.captions) ? alignment.captions : [];
    withTimestamps = Boolean(alignment.withTimestamps);
  }

  const audioDuration = await getAudioDuration(destPath);
  props.voiceoverSrc = `audio/${basename(destPath)}`;
  props.voiceoverVolume = Number(props.voiceoverVolume ?? 0.96);
  props.captions = captions;
  props.durationSeconds = Math.max(18, Math.min(32, Number((audioDuration + 1.2).toFixed(2))));
  props.captionReadiness = {
    wordLevel: captions.length > 0,
    provider: "elevenlabs",
    alignmentRef: `audio/${basename(alignmentPath)}`,
    reason: withTimestamps
      ? "ElevenLabs with-timestamps word captions mapped into Remotion captions."
      : "ElevenLabs audio generated without timestamp captions.",
  };
  props.audioReadiness = {
    studioVoiceover: true,
    quietMusic: Boolean(props.musicSrc),
    musicPolicy: props.musicSrc ? "quiet_music_ready" : "music_omitted_no_sfx",
    provider: "elevenlabs",
    reason: "Single-take creator-style ElevenLabs read for gold-standard Codex review candidate.",
    wordLevelCaptions: captions.length > 0,
    withTimestamps,
  };
  writeJson(propsPath, props);

  console.log(
    JSON.stringify(
      {
        props: relative(root, propsPath),
        voiceoverSrc: props.voiceoverSrc,
        durationSeconds: props.durationSeconds,
        captions: captions.length,
        alignmentRef: props.captionReadiness.alignmentRef,
      },
      null,
      2,
    ),
  );
};

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
