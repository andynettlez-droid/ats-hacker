# ATSHacker Auto-Poster (Upload-Post)

Publish or schedule Signal launch videos to TikTok, Instagram, and YouTube through Upload-Post's official API. TikTok, Instagram, and YouTube are connected, and the current posting cap is unlimited.

## Why This

Use the official publishing path instead of browser automation. It is more reliable, avoids login challenges, and keeps posting behavior inside the platform-approved API flow.

## One-Time Setup

1. Create an Upload-Post account: https://app.upload-post.com
2. Create a user profile in the dashboard.
3. Connect TikTok, Instagram, and YouTube to that profile.
4. Add secrets to `marketing/autopost/.env`:
   - `UPLOAD_POST_API_KEY`
   - `UPLOAD_POST_USER`
5. Put MP4 files in `marketing/autopost/videos/`.
6. Install the SDK from this folder with `npm install`.

## Use It

- Preview everything without sending: `npm run dry`
- Preview one file only: `node post.mjs --dry-run --only videos/signal-breakthrough-cinematic.mp4 --now`
- Publish approved entries: `npm run post`
- Publish one reviewed draft: `node post.mjs --only videos/signal-breakthrough-cinematic.mp4 --now --approved`
- Repost an entry already marked posted only when intentional: `node post.mjs --only videos/name.mp4 --now --include-posted`

## Review Gate

Queue entries can use:

- `"status": "review_required"`
- `"status": "draft"`

Those entries are visible in dry runs, but live posting is blocked unless the exact file has a Codex approval hash and `--approved` is passed. This keeps the pipeline fast without accidentally posting an unreviewed creative.

Prepare a video for Codex review from the repo root:

```bat
py -3 marketing_agent\codex_video_approval.py prepare-review --limit 1
```

After reviewing the exported file in Codex, approve that exact run:

```bat
py -3 marketing_agent\codex_video_approval.py approve RUN_ID --reviewer codex-chat
```

The approval command writes `codexApproval.fileSha256` to the matching `posts.json` entry. `post.mjs --approved` verifies that hash against the current file before uploading.

Entries with `"status": "posted"` are skipped by default. Use `--include-posted` only for an intentional repost.

## Long-Form YouTube Gate

Long-form YouTube entries can include:

- `"contentType": "youtube_long_form"`
- `"youtubeKind": "long_form"`
- `"qaGate": { "passed": false }`
- `"expertViralGate": { "minScore": 94, "score": 0, "passed": false }`

The poster blocks live upload for long-form entries until render QA passes and the expert viral score is at least 94. This is separate from the normal `review_required` approval gate.

## `posts.json` Fields

- `title`: short title for YouTube and API metadata.
- `caption`: post text/caption.
- `file`: path to the video relative to this folder.
- `platforms`: any connected target platforms, normally `tiktok`, `instagram`, and `youtube`.
- `scheduleDate`: `null` to post now, or a UTC time like `"2026-06-26T15:00:00Z"`.
- `status`: optional workflow state. Use `review_required` until approval, then `posted` after the API confirms publication.
- `codexApproval`: exact-file approval written by `marketing_agent/codex_video_approval.py approve`.

## Operating Notes

- Current setup: TikTok, Instagram, and YouTube connected.
- Current posting cap: unlimited.
- Still stagger posts intentionally so each creative gets a clean test window and readable analytics.
- Do not use live posting for competitor comparisons, job-market claims, or product promises until a human has reviewed the creative.
