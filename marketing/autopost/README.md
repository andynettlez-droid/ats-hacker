# ATSHacker Auto-Poster (Upload-Post)

Automatically publish or schedule your launch videos to TikTok, Instagram, and YouTube
through **Upload-Post's official API** — no browser bots, ToS-compliant. Free tier = **10 uploads/month**.

## Why this (vs. botting the apps)
Logging a bot into tiktok.com / instagram.com violates their terms, hits CAPTCHAs, and gets
accounts banned. Upload-Post uses the platforms' official publishing APIs, so it's safe and reliable.

## One-time setup (~10 min)
1. **Create an Upload-Post account:** https://app.upload-post.com (free plan is fine to start).
2. **Create a "user profile"** in their dashboard and **connect** your TikTok, Instagram, and
   YouTube accounts to it (you do the OAuth login — that part can't be automated for you).
   - Instagram must be a **Business/Creator** account to publish via API (Upload-Post walks you through it).
3. **Get your API key** from the dashboard.
4. **Configure secrets:** copy `.env.example` to `.env` and fill in:
   - `UPLOAD_POST_API_KEY` — your key
   - `UPLOAD_POST_USER` — the profile username you created in step 2
   (The repo's .gitignore already ignores `.env` — never commit it.)
5. **Add your videos:** download the 3 MP4s and put them in `marketing/autopost/videos/`
   as `score-jump.mp4`, `myth-buster.mp4`, `drop-your-score.mp4` (or edit the paths in `posts.json`).
6. **Install the SDK:**  `cd marketing/autopost && npm install`

## Use it
- Preview without sending:  `npm run dry`   (or `node post.mjs --dry-run`)
- Publish / schedule:        `npm run post`  (or `node post.mjs`)

## Editing what gets posted — `posts.json`
Each entry:
- `caption` — the post text/caption.
- `file` — path to the video (relative to this folder, e.g. `videos/score-jump.mp4`).
- `platforms` — any of `tiktok`, `instagram`, `youtube`, `x`, `linkedin`, `facebook`, etc.
- `scheduleDate` — `null` to post now, or a **UTC** time like `"2026-06-26T15:00:00Z"` to schedule.

That's it. Run `npm run post` once and Upload-Post handles publishing/scheduling to every platform.

## Notes & limits
- Free plan: 10 uploads/month, 1 profile. Paid (~$24/mo) lifts limits / adds profiles.
- Video posting is supported on the free tier (counts toward the 10/mo).
- Manage or cancel scheduled posts in the Upload-Post dashboard (or via their schedule API).
- To go fully hands-off later, this `npm run post` can be wired to a cron/scheduled task.
