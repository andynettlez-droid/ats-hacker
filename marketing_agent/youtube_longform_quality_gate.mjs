#!/usr/bin/env node
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const DEFAULT_MIN_SCORE = 94;

const args = process.argv.slice(2);
const getArg = (name, fallback = null) => {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : fallback;
};

const packetPath = getArg('--packet');
const propsPath = getArg('--props');
const manifestPath = getArg('--manifest');
const write = args.includes('--write');
const minScore = Number(getArg('--min-score', String(DEFAULT_MIN_SCORE)));

if (!packetPath || !propsPath) {
  console.error(
    'Usage: node marketing_agent/youtube_longform_quality_gate.mjs --packet <packet.json> --props <episode-props.json> [--manifest <channel_manifest.json>] [--write]',
  );
  process.exit(1);
}

const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));
const packet = readJson(packetPath);
const props = readJson(propsPath);
const manifest = manifestPath && existsSync(manifestPath) ? readJson(manifestPath) : null;

const text = [
  packet.topic,
  packet.thesis,
  packet.youtube?.title,
  packet.youtube?.seoTitle,
  packet.youtube?.description,
  packet.youtube?.cta,
  props.title,
  props.thesis,
  props.cta,
  ...(props.sections || []).flatMap((section) => [section.label, section.script, section.visual]),
  ...(props.keywords || []),
  ...(props.weakBullets || []),
  props.beforeBullet,
  props.afterBullet,
]
  .filter(Boolean)
  .join('\n')
  .toLowerCase();

const containsAny = (terms) => terms.some((term) => text.includes(term.toLowerCase()));
const countTerms = (terms) => terms.filter((term) => text.includes(term.toLowerCase())).length;

const sections = Array.isArray(props.sections) ? props.sections : [];
const title = String(packet.youtube?.seoTitle || packet.youtube?.title || props.title || '');
const hookText = String(sections[0]?.script || props.title || '');
const titleWordCount = title.trim().split(/\s+/).filter(Boolean).length;
const hookWordCount = hookText.trim().split(/\s+/).filter(Boolean).length;
const audio = props.audioReadiness || manifest?.episode?.audioReadiness || {};
const hasRenderedVoiceover = Boolean(props.voiceoverSrc || (Array.isArray(props.voiceoverSegments) && props.voiceoverSegments.length));
const hasQuietMusic = Boolean(props.musicSrc || audio.quietMusic);

const unsafeClaims = [
  'guaranteed interview',
  'guarantee interviews',
  'beat the ats',
  'trick the ats',
  'fool the ats',
  'automatically rejects',
  'auto rejects',
  'make up experience',
  'invent a job',
  'invented experience',
];
const hasUnsafeClaim = unsafeClaims.some((claim) => text.includes(claim));

const report = {
  minScore,
  score: 0,
  passed: false,
  verdict: 'not_ready',
  dimensions: [],
  blockers: [],
  nextActions: [],
};

const add = (name, points, max, passed, note) => {
  report.score += points;
  report.dimensions.push({ name, points, max, passed, note });
};

add(
  'Packaging: title and promise',
  titleWordCount >= 6 && titleWordCount <= 14 && containsAny(['problem', 'resume', 'teardown', 'ai resume', 'qualified', 'invisible'])
    ? 10
    : 6,
  10,
  titleWordCount >= 6 && titleWordCount <= 14,
  'Title should be specific, curiosity-driven, and not clickbait.',
);

add(
  'First 30 seconds: pattern interrupt',
  hookWordCount <= 42 && containsAny(['dangerous', 'linkedin', 'job description', 'invisible', 'professional']) ? 12 : 7,
  12,
  hookWordCount <= 42,
  'Cold open must quickly establish tension and the visible artifact.',
);

add(
  'Retention architecture',
  sections.length >= 8 && containsAny(['open loop', 'mistake', 'fix', 'score', 'proof']) ? 14 : 8,
  14,
  sections.length >= 8,
  'Expert long-form needs more than a static explainer: open loop, stakes, teardown, fix, payoff, CTA.',
);

add(
  'Proof density',
  countTerms(['HubSpot', 'CAC', 'LinkedIn Ads', 'lifecycle marketing', 'pipeline', '32%', '34', '92']) >= 6 ? 14 : 9,
  14,
  countTerms(['HubSpot', 'CAC', 'LinkedIn Ads', 'lifecycle marketing', 'pipeline', '32%', '34', '92']) >= 6,
  'Use concrete tools, metrics, before/after score, and a before/after bullet.',
);

add(
  'Visual plan',
  countTerms(['resume', 'job description', 'highlight', 'score', 'bullet', 'mascot', 'split screen']) >= 5 ? 12 : 8,
  12,
  countTerms(['resume', 'job description', 'highlight', 'score', 'bullet', 'mascot', 'split screen']) >= 5,
  'Long-form must keep artifacts on-screen, not become presenter-only.',
);

add(
  'Trust and claim safety',
  hasUnsafeClaim ? 0 : 12,
  12,
  !hasUnsafeClaim,
  'No ATS mythology, fake outcomes, fabricated rankings, or callback guarantees.',
);

add(
  'Audience empathy and creator voice',
  countTerms(['not bad experience', 'invisible experience', 'mind readers', 'polite fog', 'not inventing', 'evidence is wearing camouflage', 'professional fog']) >= 3
    ? 10
    : 6,
  10,
  countTerms(['not bad experience', 'invisible experience', 'mind readers', 'polite fog', 'not inventing', 'evidence is wearing camouflage', 'professional fog']) >= 3,
  'Should feel like a sharp creator teardown, not generic SaaS education.',
);

add(
  'Product bridge',
  containsAny(['free signal score', 'paste the job description', 'no fake experience']) ? 8 : 5,
  8,
  containsAny(['free signal score']),
  'CTA should be useful and trust-preserving.',
);

add(
  'Audio readiness',
  hasRenderedVoiceover && hasQuietMusic ? 10 : hasQuietMusic ? 4 : 0,
  10,
  hasRenderedVoiceover && hasQuietMusic,
  'Publish-ready long-form requires voiceover/narration plus balanced music.',
);

add(
  'Render and QA evidence',
  manifest?.episode?.renderReview?.passed === true || manifest?.episode?.qaGate?.passed === true ? 8 : 0,
  8,
  manifest?.episode?.renderReview?.passed === true || manifest?.episode?.qaGate?.passed === true,
  'Must include rendered MP4 and QA pass before publish-ready status.',
);

report.score = Math.min(100, report.score);

if (!hasRenderedVoiceover) report.blockers.push('Long-form narration is not rendered; only music/props are ready.');
if (!(manifest?.episode?.renderReview?.passed === true || manifest?.episode?.qaGate?.passed === true)) {
  report.blockers.push('Rendered long-form MP4 has not passed visual/audio QA.');
}
if (hasUnsafeClaim) report.blockers.push('Unsafe claim language found.');

report.passed = report.score >= minScore && report.blockers.length === 0;
report.verdict = report.passed ? 'publish_ready_expert_viral_pass' : 'needs_work_before_publish_ready';
if (!report.passed) {
  if (sections.length < 8) report.nextActions.push('Expand to 8-10 retention-focused sections.');
  if (!hasRenderedVoiceover) report.nextActions.push('Render studio-quality narration or add approved voiceover segments.');
  report.nextActions.push('Render the full 16:9 episode, inspect hook/midpoint/payoff/CTA frames, and verify audio metadata.');
  report.nextActions.push(`Only mark qaGate.passed=true after score is at least ${minScore} and blockers are zero.`);
}

if (write) {
  const outJson = join(dirname(packetPath), 'youtube_viral_quality_report.json');
  const outMd = join(dirname(packetPath), 'youtube_viral_quality_report.md');
  writeFileSync(outJson, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  writeFileSync(
    outMd,
    [
      '# YouTube Long-Form Viral Quality Gate',
      '',
      `Verdict: ${report.verdict}`,
      `Score: ${report.score}/100`,
      `Minimum: ${report.minScore}/100`,
      `Passed: ${report.passed}`,
      '',
      '## Dimensions',
      '',
      ...report.dimensions.map((item) => `- ${item.name}: ${item.points}/${item.max} - ${item.note}`),
      '',
      '## Blockers',
      '',
      ...(report.blockers.length ? report.blockers.map((item) => `- ${item}`) : ['- None']),
      '',
      '## Next Actions',
      '',
      ...(report.nextActions.length ? report.nextActions.map((item) => `- ${item}`) : ['- Ready for final approval workflow.']),
      '',
    ].join('\n'),
    'utf8',
  );

  if (manifestPath && manifest) {
    manifest.episode = manifest.episode || {};
    manifest.episode.expertViralGate = {
      minScore,
      score: report.score,
      passed: report.passed,
      verdict: report.verdict,
      report: relative(ROOT, outJson).replaceAll('\\', '/'),
    };
    manifest.episode.status = report.passed ? 'publish_ready_review_required' : 'needs_expert_viral_work';
    manifest.status = report.passed ? 'publish_ready_review_required' : 'needs_expert_viral_work';
    writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  }
}

console.log(JSON.stringify(report, null, 2));
