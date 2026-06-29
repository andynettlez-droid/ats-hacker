# Signal Media Pipeline Readiness Review

Reviewed: 2026-06-28

## Verdict

The short-form pipeline is ready for supervised studio production and review-gated posting. It is not yet ready for fully unattended daily channel production.

The current `ResumeCrimeScene` shorts are materially stronger than the first mascot/product-demo cuts: the resume is the main character, the humor is more native to job-search audiences, the Signal mascot is present without taking over, the CTA is clearer, and the audio direction is quieter and more premium.

The long-form YouTube lane is not yet production-ready. It has a script packet, props, segmented voiceover, thumbnail composition, and a 2-minute review cut, but it still needs a full render/review path, retention editing, thumbnail QA, and a publish package before it should be treated as a daily YouTube factory.

## What Is Ready

- `ResumeCrimeScene` renders vertical 1080x1920, 30fps shorts.
- Three daily studio short exports exist in `marketing/remotion/out/`.
- ElevenLabs voiceover assets exist for the daily shorts and long-form episode.
- Quiet music assets exist and are used instead of harsh SFX.
- The posting layer supports TikTok, Instagram, and YouTube through Upload-Post.
- The posting layer has a review gate for `draft` and `review_required` entries.
- The autopost dry run works and reports file hashes before publishing.
- The Python marketing agent stack compiles.
- The Remotion TypeScript check passes.
- The current daily script packet passes the creative quality gate.

## What Is Not Ready Yet

- No automated frame-level video QC for overlap, safe areas, cropped text, contrast, or mascot visibility.
- No automated audio loudness/peak/LUFS check.
- No word-level transcript/caption alignment.
- No automatic platform metrics ingestion from TikTok, Instagram, or YouTube.
- No automatic trend feed from TikTok Creative Center, YouTube, Google Trends, Reddit, or LinkedIn.
- The script creative gate can overstate readiness because it grades packet text, not rendered video.
- Long-form YouTube has a review cut, but not a fully verified final episode workflow.
- The queue still contains older ad-style clips that should be reviewed or retired before they dilute the new teardown format.

## Current Studio Short Assets

- `marketing/remotion/out/daily-your-ai-resume-has-linkedin-breath-studio.mp4`
- `marketing/remotion/out/daily-one-bullet-fix-studio.mp4`
- `marketing/remotion/out/daily-ats-myth-lab-studio.mp4`

These are the assets that should be promoted for review-gated posting, not the earlier first-pass daily short.

## Immediate Next Steps

1. Promote the three studio short assets into `marketing/autopost/videos/` as `review_required`.
2. Dry-run the queue and confirm the three studio cuts show as blocked until approval.
3. Add an automated render QC script that checks expected frame stills exist and forces a human review checklist before queue promotion.
4. Add audio QC with ffmpeg/ffprobe or a Node media parser dependency.
5. Add metrics ingestion from the posting provider and platform dashboards.
6. Build the long-form publish package: final render, thumbnail, title, description, chapters, pinned comment, and score-page UTM.

## Production Recommendation

Use the pipeline now for one to three supervised shorts per day. Do not run it as a fully autonomous channel factory until render-level QC, audio QC, trend ingestion, and metrics feedback are automated.
