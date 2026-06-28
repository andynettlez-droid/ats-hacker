#!/usr/bin/env node
/**
 * ATSHacker auto-poster (Upload-Post).
 * Publishes or schedules local video files through Upload-Post's official API.
 *
 * Usage:
 *   node post.mjs --dry-run
 *   node post.mjs
 *   node post.mjs --only videos/signal-breakthrough-cinematic.mp4 --now --approved
 *   node post.mjs --only videos/signal-breakthrough-cinematic.mp4 --now --include-posted
 *
 * Entries with status "draft" or "review_required" are blocked from live posting
 * unless --approved is passed. Dry runs still show them for review.
 * Entries with status "posted" are skipped unless --include-posted is passed.
 */
import { readFileSync, existsSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, isAbsolute } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DRY_RUN = process.argv.includes('--dry-run');
const FORCE_NOW = process.argv.includes('--now');
const APPROVED_REVIEW = process.argv.includes('--approved');
const INCLUDE_POSTED = process.argv.includes('--include-posted');
const onlyArgIndex = process.argv.findIndex((arg) => arg === '--only');
const ONLY_FILE = onlyArgIndex >= 0 ? process.argv[onlyArgIndex + 1] : null;
const REVIEW_STATUSES = new Set(['draft', 'review_required']);
const POSTED_STATUSES = new Set(['posted']);

// Minimal .env loader; real environment variables win.
(function loadEnv() {
  try {
    for (const line of readFileSync(join(__dirname, '.env'), 'utf8').split('\n')) {
      const match = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/i);
      if (match) process.env[match[1]] ||= match[2].replace(/^["']|["']$/g, '');
    }
  } catch {
    // Rely on real env vars.
  }
})();

const API_KEY = process.env.UPLOAD_POST_API_KEY;
const USER = process.env.UPLOAD_POST_USER;
if (!API_KEY || !USER) {
  console.error('Missing UPLOAD_POST_API_KEY or UPLOAD_POST_USER. Add them to marketing/autopost/.env.');
  process.exit(1);
}

const allPosts = JSON.parse(readFileSync(join(__dirname, 'posts.json'), 'utf8'));
if (!Array.isArray(allPosts) || !allPosts.length) {
  console.error('posts.json is empty.');
  process.exit(1);
}

let posts = allPosts;
if (ONLY_FILE) {
  posts = allPosts.filter((post) => post.file === ONLY_FILE);
  if (!posts.length) {
    console.error(`No post found for --only ${ONLY_FILE}.`);
    process.exit(1);
  }
}

let bad = 0;
for (const [index, post] of posts.entries()) {
  const tag = `#${index + 1} "${(post.caption || '').slice(0, 40)}..."`;
  if (!post.caption || !Array.isArray(post.platforms) || !post.platforms.length || !post.file) {
    console.error(`${tag} needs caption, file, and a non-empty platforms array.`);
    bad++;
    post.__bad = true;
    continue;
  }

  post.__reviewRequired = REVIEW_STATUSES.has(post.status);
  post.__alreadyPosted = POSTED_STATUSES.has(post.status);
  post.__path = isAbsolute(post.file) ? post.file : join(__dirname, post.file);
  if (!existsSync(post.__path)) {
    console.error(`${tag} file not found: ${post.__path}`);
    bad++;
    post.__bad = true;
  }
}

if (bad) {
  console.error(`\nFix the ${bad} problem(s) above and re-run.`);
  process.exit(1);
}

if (DRY_RUN) {
  for (const [index, post] of posts.entries()) {
    const status = post.status ? ` [${post.status}]` : '';
    const gate = post.__reviewRequired ? ' - live posting blocked until --approved' : '';
    const postedGate = post.__alreadyPosted ? ' - skipped unless --include-posted' : '';
    const when = post.scheduleDate && !FORCE_NOW ? ` @ ${post.scheduleDate}` : ' (now)';
    console.log(
      `DRY RUN #${index + 1}${status}: ${post.platforms.join(', ')}${when}${gate}${postedGate}\n` +
        `   file: ${post.__path}\n` +
        `   caption: ${post.caption}\n`,
    );
  }
  console.log('Dry run only; nothing sent. Remove --dry-run to publish eligible entries.');
  process.exit(0);
}

let mod;
try {
  mod = await import('upload-post');
} catch {
  console.error('The upload-post SDK is not installed. Run: npm install');
  process.exit(1);
}

const UploadPost = mod.UploadPost || mod.default?.UploadPost || mod.default;
const uploader = new UploadPost(API_KEY);

let failures = 0;
let skipped = 0;
let changed = false;
for (const [index, post] of posts.entries()) {
  const tag = `#${index + 1} "${(post.caption || '').slice(0, 40)}..."`;
  if (post.__reviewRequired && !APPROVED_REVIEW) {
    console.log(`SKIP ${tag} - status=${post.status}; rerun with --approved after human review.`);
    skipped++;
    continue;
  }
  if (post.__alreadyPosted && !INCLUDE_POSTED) {
    console.log(`SKIP ${tag} - status=posted; rerun with --include-posted only if this is an intentional repost.`);
    skipped++;
    continue;
  }

  const opts = {
    title: post.title || (post.caption || '').slice(0, 96),
    user: USER,
    platforms: post.platforms,
    description: post.description || post.caption,
    instagramTitle: post.instagramTitle || post.caption,
    youtubeTitle: post.youtubeTitle || post.title || (post.caption || '').slice(0, 96),
    youtubeDescription: post.youtubeDescription || post.description || post.caption,
    ...(post.scheduleDate && !FORCE_NOW ? { scheduled_date: post.scheduleDate, async_upload: true } : {}),
  };

  try {
    const res = await uploader.upload(post.__path, opts);
    const ok = res?.success !== false;
    console.log(`${ok ? 'OK' : 'FAIL'} ${tag} - ${post.scheduleDate ? 'scheduled' : 'posted'} ${ok ? '' : '-> ' + JSON.stringify(res)}`);
    if (!ok) {
      post.status = 'failed';
      post.lastError = JSON.stringify(res);
      post.lastAttemptAt = new Date().toISOString();
      changed = true;
      failures++;
    } else {
      post.status = post.scheduleDate && !FORCE_NOW ? 'scheduled' : 'posted';
      post.postedAt = new Date().toISOString();
      post.uploadPostResult = res;
      delete post.lastError;
      changed = true;
    }
  } catch (error) {
    console.error(`FAIL ${tag} - ${error.message}`);
    post.status = 'failed';
    post.lastError = error.message;
    post.lastAttemptAt = new Date().toISOString();
    changed = true;
    failures++;
  }
}

if (changed) {
  for (const post of allPosts) {
    delete post.__reviewRequired;
    delete post.__alreadyPosted;
    delete post.__path;
    delete post.__bad;
  }
  writeFileSync(join(__dirname, 'posts.json'), JSON.stringify(allPosts, null, 4) + '\n');
  console.log('posts.json updated with latest posting status.');
}

console.log(`\nDone. ${posts.length - failures - skipped} ok, ${skipped} skipped, ${failures} failed.`);
process.exit(failures ? 1 : 0);
