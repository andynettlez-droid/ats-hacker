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
 *   node post.mjs --status <request_id>
 *
 * Entries with status "draft" or "review_required" are blocked from live posting
 * unless --approved is passed. Dry runs still show them for review.
 * Entries with status "posted" are skipped unless --include-posted is passed.
 */
import { readFileSync, existsSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, isAbsolute } from 'node:path';
import { createHash } from 'node:crypto';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DRY_RUN = process.argv.includes('--dry-run');
const FORCE_NOW = process.argv.includes('--now');
const APPROVED_REVIEW = process.argv.includes('--approved');
const INCLUDE_POSTED = process.argv.includes('--include-posted');
const onlyArgIndex = process.argv.findIndex((arg) => arg === '--only');
const ONLY_FILE = onlyArgIndex >= 0 ? process.argv[onlyArgIndex + 1] : null;
const reviewerArgIndex = process.argv.findIndex((arg) => arg === '--reviewer');
const REVIEWER = reviewerArgIndex >= 0 ? process.argv[reviewerArgIndex + 1] : (process.env.UPLOAD_POST_REVIEWER || process.env.USERNAME || process.env.USER || 'local-reviewer');
const statusArgIndex = process.argv.findIndex((arg) => arg === '--status');
const STATUS_REQUEST_ID = statusArgIndex >= 0 ? process.argv[statusArgIndex + 1] : null;
const REVIEW_STATUSES = new Set(['draft', 'review_required']);
const POSTED_STATUSES = new Set(['posted']);

const sha256File = (filePath) => createHash('sha256').update(readFileSync(filePath)).digest('hex');

const sanitizeStatus = (status) => ({
  status: status?.status,
  completed: status?.completed,
  total: status?.total,
  request_id: status?.request_id,
  last_update: status?.last_update,
  results: Array.isArray(status?.results)
    ? status.results.map((result) => ({
        platform: result.platform,
        success: result.success,
        platform_post_id: result.platform_post_id,
        post_url: result.post_url,
        error_message: result.error_message,
        error_code: result.error_code,
        upload_timestamp: result.upload_timestamp,
        media_size_bytes: result.media_size_bytes,
        video_was_transcoded: result.video_was_transcoded,
        prevalidation_metadata: result.prevalidation_metadata,
        job_id: result.job_id,
      }))
    : [],
});

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

let mod;
if (STATUS_REQUEST_ID) {
  try {
    mod = await import('upload-post');
    const UploadPost = mod.UploadPost || mod.default?.UploadPost || mod.default;
    const uploader = new UploadPost(API_KEY);
    const status = await uploader.getStatus(STATUS_REQUEST_ID);
    const sanitized = sanitizeStatus(status);
    try {
      const postsPath = join(__dirname, 'posts.json');
      const existingPosts = JSON.parse(readFileSync(postsPath, 'utf8'));
      if (Array.isArray(existingPosts)) {
        let changedStatus = false;
        for (const post of existingPosts) {
          const requestId = post.uploadPostResult?.request_id || post.uploadStatus?.request_id;
          if (requestId === STATUS_REQUEST_ID) {
            post.uploadStatus = sanitized;
            if (sanitized.status === 'completed' && sanitized.completed === sanitized.total) {
              post.status = 'posted';
            }
            changedStatus = true;
          }
        }
        if (changedStatus) {
          writeFileSync(postsPath, JSON.stringify(existingPosts, null, 4) + '\n');
        }
      }
    } catch {
      // Status lookup still succeeded; queue persistence is best-effort.
    }
    console.log(JSON.stringify(sanitized, null, 2));
    process.exit(0);
  } catch (error) {
    console.error(`Failed to fetch upload status: ${error.message}`);
    process.exit(1);
  }
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
  } else {
    post.__fileHash = sha256File(post.__path);
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
        `   sha256: ${post.__fileHash}\n` +
        `   caption: ${post.caption}\n`,
    );
  }
  console.log('Dry run only; nothing sent. Remove --dry-run to publish eligible entries.');
  process.exit(0);
}

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

  if (post.__reviewRequired && APPROVED_REVIEW) {
    post.reviewApproval = {
      reviewer: REVIEWER,
      approvedAt: new Date().toISOString(),
      fileSha256: post.__fileHash,
      file: post.file,
      caption: post.caption,
      platforms: post.platforms,
      title: post.title || (post.caption || '').slice(0, 96),
      thumbnail: post.thumbnail || null,
      scheduleDate: post.scheduleDate || null,
    };
    changed = true;
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
    delete post.__fileHash;
    delete post.__bad;
  }
  writeFileSync(join(__dirname, 'posts.json'), JSON.stringify(allPosts, null, 4) + '\n');
  console.log('posts.json updated with latest posting status.');
}

console.log(`\nDone. ${posts.length - failures - skipped} ok, ${skipped} skipped, ${failures} failed.`);
process.exit(failures ? 1 : 0);
