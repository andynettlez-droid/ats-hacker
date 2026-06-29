#!/usr/bin/env node
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { basename, dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const remotionDir = resolve(__dirname, '..');
const root = resolve(remotionDir, '..', '..');
const audioDir = join(remotionDir, 'public', 'audio');

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const arg = process.argv[i];
  if (arg.startsWith('--')) {
    const next = process.argv[i + 1];
    args.set(arg, next && !next.startsWith('--') ? next : true);
    if (next && !next.startsWith('--')) i += 1;
  }
}

const propsPath = resolve(remotionDir, String(args.get('--props') || 'props_daily_2026-06-28_ai-resumes-all-sound-the-same-so-recruiters-search-for-proof_episode.json'));
const scriptPath = resolve(root, String(args.get('--script') || 'marketing/daily_content/2026-06-28-ai-resumes-all-sound-the-same-so-recruiters-search-for-proof/longform_voiceover.md'));
const manifestPath = resolve(root, String(args.get('--manifest') || 'marketing/daily_content/2026-06-28-ai-resumes-all-sound-the-same-so-recruiters-search-for-proof/channel_manifest.json'));
const force = args.has('--force');

const loadEnvFile = (path) => {
  if (!existsSync(path)) return;
  for (const line of readFileSync(path, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/i);
    if (!match) continue;
    process.env[match[1]] ||= match[2].replace(/^["']|["']$/g, '');
  }
};

loadEnvFile(join(root, 'marketing_agent', '.env'));
loadEnvFile(join(root, 'marketing', 'autopost', '.env'));

const apiKey = process.env.ELEVENLABS_API_KEY;
if (!apiKey || apiKey === 'your_elevenlabs_api_key_here') {
  throw new Error('ELEVENLABS_API_KEY is not configured in the environment.');
}

const voiceId = process.env.ELEVENLABS_VOICE_ID || '21m00Tcm4TlvDq8ikWAM';
const modelId = process.env.ELEVENLABS_MODEL_ID || 'eleven_multilingual_v2';

const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));
const writeJson = (path, value) => writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, 'utf8');

const safeSlug = (value) =>
  String(value || 'episode')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 56) || 'episode';

const parseSections = (markdown) => {
  const lines = markdown.split(/\r?\n/);
  const sections = [];
  let current = null;
  for (const line of lines) {
    const heading = line.match(/^##\s+(.+?)\s*$/);
    if (heading) {
      if (current && current.text.trim()) sections.push(current);
      current = { label: heading[1].trim(), text: '' };
      continue;
    }
    if (current && !line.startsWith('#')) {
      current.text += `${line}\n`;
    }
  }
  if (current && current.text.trim()) sections.push(current);
  return sections
    .filter((section) => !/^status$/i.test(section.label))
    .map((section) => ({ label: section.label, text: section.text.trim().replace(/\n{2,}/g, '\n\n') }));
};

const synthesize = async (text, destPath) => {
  const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
    method: 'POST',
    headers: {
      'xi-api-key': apiKey,
      'Content-Type': 'application/json',
      Accept: 'audio/mpeg',
    },
    body: JSON.stringify({
      text,
      model_id: modelId,
      voice_settings: {
        stability: 0.5,
        similarity_boost: 0.84,
        style: 0.34,
        use_speaker_boost: true,
      },
    }),
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`ElevenLabs failed ${response.status}: ${body.slice(0, 240)}`);
  }
  const bytes = Buffer.from(await response.arrayBuffer());
  if (bytes.length < 1024) throw new Error(`Generated audio is too small for ${basename(destPath)}`);
  writeFileSync(destPath, bytes);
};

const main = async () => {
  mkdirSync(audioDir, { recursive: true });
  const props = readJson(propsPath);
  const manifest = existsSync(manifestPath) ? readJson(manifestPath) : {};
  const sections = parseSections(readFileSync(scriptPath, 'utf8'));
  if (!sections.length) throw new Error(`No voiceover sections found in ${scriptPath}`);

  const fps = 30;
  const introFrames = 8 * fps;
  const outroFrames = 18 * fps;
  const totalFrames = Number(props.durationInFrames || 8 * 60 * fps);
  const usableFrames = totalFrames - introFrames - outroFrames;
  const sectionFrames = Math.max(1, Math.floor(usableFrames / sections.length));
  const topicSlug = safeSlug(props.title || manifest.topic || 'daily-teardown-episode');
  const segments = [];

  for (const [index, section] of sections.entries()) {
    const filename = `daily-${topicSlug}-episode-${index + 1}-${safeSlug(section.label)}.mp3`;
    const destPath = join(audioDir, filename);
    if (force || !existsSync(destPath)) {
      console.log(`Generating ${filename}`);
      await synthesize(section.text.slice(0, 2800), destPath);
    } else {
      console.log(`Using cached ${filename}`);
    }
    segments.push({
      label: section.label,
      src: `audio/${filename}`,
      fromFrame: introFrames + index * sectionFrames,
      volume: 0.94,
    });
  }

  props.voiceoverSegments = segments.map(({ src, fromFrame, volume }) => ({ src, fromFrame, volume }));
  props.audioReadiness = {
    studioVoiceover: true,
    quietMusic: true,
    reason: `${segments.length} episode voiceover sections ready`,
  };
  writeJson(propsPath, props);

  manifest.episode ||= {};
  manifest.episode.voiceoverSegments = segments.map((segment) => ({
    label: segment.label,
    src: segment.src,
    fromFrame: segment.fromFrame,
  }));
  manifest.episode.audioReadiness = props.audioReadiness;
  writeJson(manifestPath, manifest);

  console.log(JSON.stringify({
    props: relative(root, propsPath),
    manifest: relative(root, manifestPath),
    segments: segments.length,
    audioDir: relative(root, audioDir),
  }, null, 2));
};

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
