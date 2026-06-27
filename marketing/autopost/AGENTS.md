# Operating The Auto-Poster

This folder publishes short-form videos to social through the Upload-Post API. If you are an AI agent asked to queue or post content, follow this exactly.

## How It Works

- `post.mjs` reads `posts.json` and posts or schedules entries through Upload-Post.
- Credentials live in `.env` as `UPLOAD_POST_API_KEY` and `UPLOAD_POST_USER`. Never print, log, or commit these values.
- Video files live in `videos/`.
- TikTok, Instagram, and YouTube are connected.
- Posting capacity is currently unlimited, but posting should still be staggered for clean analytics.

## Queue Workflow

1. Put the MP4 in `marketing/autopost/videos/`.
2. Add an entry to `posts.json`.
3. Use `status: "review_required"` for every new creative unless the user has explicitly approved it.
4. Preview first with `node post.mjs --dry-run --only videos/NAME.mp4 --now`.
5. Only after approval, publish with `node post.mjs --only videos/NAME.mp4 --now --approved`.
6. After a successful API response, mark the entry `status: "posted"` and add `postedAt`.

Example entry:

```json
{
  "title": "Qualified but buried in search?",
  "caption": "Qualified but buried in search? Signal by ATSHacker helps match your real experience to the role language recruiters search, without fake claims. Check your score free. #jobsearch #resumehelp #careeradvice #resumetips #careertok",
  "file": "videos/signal-breakthrough-cinematic.mp4",
  "platforms": ["tiktok", "instagram", "youtube"],
  "scheduleDate": null,
  "status": "review_required"
}
```

## Hard Rules

- Do not publish live unless the user explicitly approves the exact video/caption.
- Do not pass `--approved` during normal dry-run or QA work.
- Do not repost an entry marked `posted` unless the user explicitly asks for a repost; use `--include-posted` only then.
- Do not use platforms beyond `tiktok`, `instagram`, and `youtube` unless the Upload-Post profile is connected first.
- Keep YouTube titles under 100 characters.
- Use honest framing: Signal improves match clarity and role-language alignment. Do not claim an ATS auto-rejects people based on content parsing.
- Do not fabricate stats, ratings, customers, testimonials, guarantees, or competitor results.
- For competitor or head-to-head content, include sources in the brief and avoid defamatory or unverifiable claims.
- Verify the final video has the Signal mascot, not the old human presenter, before queueing.
