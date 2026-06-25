#!/usr/bin/env node
/**
 * ATSHacker auto-poster (Upload-Post).
 * Publishes/schedules local video files to your connected socials via Upload-Post's
 * official API (ToS-compliant — no browser botting). Free tier = 10 uploads/month.
 *
 * Usage:
 *   node post.mjs --dry-run   # validate + preview, send nothing
 *   node post.mjs             # actually post / schedule
 *
 * Setup (see README.md):
 *   1) npm install            (installs the official upload-post SDK)
 *   2) create .env with UPLOAD_POST_API_KEY and UPLOAD_POST_USER (see .env.example)
 *   3) edit posts.json (caption, local video file path, platforms, optional scheduleDate)
 *
 * Requires Node 18+.
 */
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, isAbsolute } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DRY_RUN = process.argv.includes('--dry-run');

// Minimal .env loader (no dependency).
(function loadEnv() {
  try {
    for (const line of readFileSync(join(__dirname, '.env'), 'utf8').split('\n')) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/i);
      if (m) process.env[m[1]] ||= m[2].replace(/^["']|["']$/g, '');
    }
  } catch { /* rely on real env vars */ }
})();

const API_KEY = process.env.UPLOAD_POST_API_KEY;
const USER = process.env.UPLOAD_POST_USER;
if (!API_KEY || !USER) {
  console.error('❌ Missing UPLOAD_POST_API_KEY or UPLOAD_POST_USER. Add them to marketing/autopost/.env (see .env.example).');
  process.exit(1);
}

const posts = JSON.parse(readFileSync(join(__dirname, 'posts.json'), 'utf8'));
if (!Array.isArray(posts) || !posts.length) {
  console.error('❌ posts.json is empty.');
  process.exit(1);
}

// Resolve + validate every post before sending anything.
let bad = 0;
for (const [i, p] of posts.entries()) {
  const tag = `#${i + 1} "${(p.caption || '').slice(0, 40)}…"`;
  if (!p.caption || !Array.isArray(p.platforms) || !p.platforms.length || !p.file) {
    console.error(`❌ ${tag} — needs caption, file, and a non-empty platforms array.`);
    bad++; p.__bad = true; continue;
  }
  p.__path = isAbsolute(p.file) ? p.file : join(__dirname, p.file);
  if (!existsSync(p.__path)) {
    console.error(`❌ ${tag} — file not found: ${p.__path}`);
    bad++; p.__bad = true;
  }
}
if (bad) { console.error(`\nFix the ${bad} problem(s) above and re-run.`); process.exit(1); }

if (DRY_RUN) {
  for (const [i, p] of posts.entries()) {
    console.log(`🟡 DRY RUN #${i + 1}: ${p.platforms.join(', ')}${p.scheduleDate ? ` @ ${p.scheduleDate}` : ' (now)'}\n   file: ${p.__path}\n   caption: ${p.caption}\n`);
  }
  console.log('Dry run only — nothing sent. Remove --dry-run to publish.');
  process.exit(0);
}

// Real send via the official SDK.
let mod;
try {
  mod = await import('upload-post');
} catch {
  console.error('❌ The upload-post SDK is not installed. Run: npm install');
  process.exit(1);
}
const UploadPost = mod.UploadPost || mod.default?.UploadPost || mod.default;
const uploader = new UploadPost(API_KEY);

let failures = 0;
for (const [i, p] of posts.entries()) {
  const tag = `#${i + 1} "${(p.caption || '').slice(0, 40)}…"`;
  const opts = {
    title: p.caption,
    user: USER,
    platforms: p.platforms,
    ...(p.scheduleDate ? { scheduled_date: p.scheduleDate, async_upload: true } : {}),
  };
  try {
    const res = await uploader.upload(p.__path, opts);
    const ok = res?.success !== false;
    console.log(`${ok ? '✅' : '❌'} ${tag} — ${p.scheduleDate ? 'scheduled' : 'posted'} ${ok ? '' : '→ ' + JSON.stringify(res)}`);
    if (!ok) failures++;
  } catch (e) {
    console.error(`❌ ${tag} — ${e.message}`);
    failures++;
  }
}
console.log(`\nDone. ${posts.length - failures} ok, ${failures} failed.`);
process.exit(failures ? 1 : 0);
