# Operating the auto-poster (instructions for AI agents)

This folder publishes short-form videos to social via the Upload-Post API. If you are an
AI agent (e.g. Antigravity) asked to post content, follow this exactly.

## How it works
- `post.mjs` reads `posts.json` and posts/schedules each entry via Upload-Post.
- Credentials live in `.env` (UPLOAD_POST_API_KEY, UPLOAD_POST_USER) — already configured on this machine. NEVER print, log, or commit these values.
- Video files live in `videos/`.

## To queue + post content
1. Put the MP4(s) in `marketing/autopost/videos/`.
2. Edit `posts.json` — an array of entries:
   `{ "caption": "...", "file": "videos/NAME.mp4", "platforms": ["instagram","youtube"], "scheduleDate": null }`
3. Preview first (sends nothing): `node post.mjs --dry-run`
4. Publish/schedule: `node post.mjs`

## HARD RULES (do not violate)
- **Only `instagram` and `youtube` are connected.** Do not add `tiktok` or others — they will error.
- **Captions must be UNDER 100 characters** (YouTube rejects longer titles).
- **Honest framing only:** resumes are ranked/searched by keyword and ~3x more likely to be seen. NEVER claim the ATS "auto-rejects" you.
- **Free tier = ~10 posts/month.** Do not burn it: post at most ~1/day, and prefer `scheduleDate` (UTC, e.g. `2026-07-01T16:00:00Z`) to stagger rather than dumping multiple at once.
- **Get human sign-off before publishing immediately.** Default to DRY-RUN, show the human the queue, and only run the live `node post.mjs` after they approve. Posting is public and irreversible.
- Disclose-and-be-honest; no fabricated stats, ratings, or testimonials in captions.
