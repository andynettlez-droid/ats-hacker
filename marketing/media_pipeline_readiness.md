# Signal Media Pipeline Readiness Review

Reviewed: 2026-07-04

## Verdict

The short-form pipeline is ready for supervised studio production and Codex review-gated posting. It is not yet ready for fully unattended daily channel production.

The current `ResumeCrimeScene` shorts are materially stronger than the first mascot/product-demo cuts: the resume is the main character, the humor is more native to job-search audiences, the Signal mascot is present without taking over, the CTA is clearer, and the audio direction is quieter and more premium.

The new Codex approval layer now wraps the existing daily packet, Remotion render, QC, promotion, and posting queue. Videos move through a durable local SQLite state machine and stop at `AWAITING_CODEX_APPROVAL` until the exact reviewed file is approved in Codex.

The long-form YouTube lane is render-ready but not publish-ready. It has a source packet, props, segmented ElevenLabs voiceover, thumbnail composition, a long-form Remotion renderer, and a review-cut path. It still needs a final full render review, retention edit, thumbnail QA, description/chapters/pinned comment, and metrics plan before it should be treated as a daily YouTube factory.

## What Is Ready

- `ResumeCrimeScene` renders vertical 1080x1920, 30fps shorts.
- Three daily studio short exports exist in `marketing/remotion/out/`.
- ElevenLabs voiceover assets exist for the daily shorts and long-form episode.
- Quiet music assets exist and are used instead of harsh SFX.
- The posting layer supports TikTok, Instagram, and YouTube through Upload-Post.
- The posting layer has a review gate for `draft` and `review_required` entries.
- The posting layer now requires a matching `codexApproval.fileSha256` before `--approved` can publish a review-required entry.
- `marketing_agent/codex_video_approval.py` renders, promotes, QC's, exports, and tracks videos through Codex approval state.
- `ResumeCrimeScene` can render word-level captions when fresh ElevenLabs timestamp metadata exists.
- The autopost dry run works and reports file hashes before publishing.
- The Python marketing agent stack compiles.
- The Remotion TypeScript check passes.
- The current daily script packet passes the creative quality gate.
- The studio short metadata/queue QC gate passes.
- The audio asset QC gate passes for linked voiceover, music, and episode segments.
- A source-backed trend intake file exists for the current daily packet.
- Thumbnail and long-form renderer components exist.
- A long-form YouTube quality gate now scores title, hook, retention architecture, proof density, visual plan, claim safety, creator voice, product bridge, audio readiness, and render QA.

## What Is Not Ready Yet

- Automated visual safe-area QC exists for bright/saturated margin issues. It is not a full semantic visual QA system for overlap, contrast, mascot personality, or whether the video is funny.
- No automated audio loudness/peak/LUFS check. The current audio gate validates files, codecs, duration, sample rate, bitrate, channels, and mix-volume settings, but does not measure loudness.
- Word-level caption alignment is available only for new ElevenLabs `/with-timestamps` generations. Existing cached daily voiceovers and OpenAI fallback voiceovers use scene captions.
- No automatic platform metrics ingestion from TikTok, Instagram, or YouTube.
- No live automated trend feed from TikTok Creative Center, YouTube, Google Trends, Reddit, or LinkedIn. Current trend intake is file-based.
- The script creative gate can overstate readiness because it grades packet text, not rendered video.
- Long-form YouTube has a renderer and review path, but not a fully verified final episode workflow.
- The current long-form packet scored 83/100 on the expert viral gate and is blocked from publish-ready status until the full episode is strengthened and rendered QA passes.
- The queue still contains older ad-style clips that should be reviewed or retired before they dilute the new teardown format.

## Current Codex Review Asset

- `marketing/codex_reviews/20260704-1d88e2aa73b70b86-corporate-weather-report-resume/daily-corporate-weather-report-resume.mp4`
- State: `AWAITING_CODEX_APPROVAL`
- QA: script gate passed, studio metadata QC passed, audio asset QC passed, visual safe-area QC passed.
- Approval phrase: `APPROVE POST 1d88e2aa73b70b86`

This file is local and git-ignored. To review on mobile from the repo root, run:

```bat
py -3 -m http.server 8765 --directory marketing/codex_reviews
```

Then open the URL printed by `prepare-review`.

## Current Studio Short Assets

- `marketing/remotion/out/daily-corporate-weather-report-resume.mp4`
- `marketing/remotion/out/daily-your-ai-resume-has-linkedin-breath-studio.mp4`
- `marketing/remotion/out/daily-one-bullet-fix-studio.mp4`
- `marketing/remotion/out/daily-ats-myth-lab-studio.mp4`

These are the assets that should be promoted for review-gated posting, not the earlier first-pass daily short.

## Current Queue Snapshot

Latest manual pipeline output:

- First current daily short rendered and exported to Codex review.
- Autopost dry run confirms it is blocked until Codex approval and `--approved`.
- Current post-grade packet: 1.
- Render-ready shorts in the current daily packet: 3.
- Studio voiceover: available.
- Quiet music: available.
- Source-backed trend intake: available.
- Long-form renderer: available.
- Thumbnail generator: available.
- Studio daily exports: available.
- Studio daily queue: available.
- Automated render QC: available.
- Audio asset QC: available.
- Long-form expert viral gate: available; current episode score is 83/100 and not publish-ready.
- Missing: platform metrics feed, audio loudness/peak QC, full transcript/caption alignment for cached voiceovers, automated live trend API connector.

## Current Audio Position

ElevenLabs is the current default for voiceover and generated sound because it gives us repeatable studio narration and brand-consistent audio assets in one workflow. It is the right default for now because the repo already has ElevenLabs voiceover assets for shorts and the episode, and the Remotion templates expect linked audio files.

Do not treat this as finished audio engineering yet. The next quality jump is not another sound-effect pass; it is:

- LUFS and true-peak measurement.
- Better voice direction presets by series.
- Caption timing from transcript or alignment data.
- A small music-bed library with clear usage rules.
- Manual listen test before any live post.

## Immediate Next Steps

1. Retire or rewrite older ad-style queued clips so the public queue is not diluted by weaker content.
2. Extend `npm run qc:daily:shorts` with frame still/pixel checks for text overlap, safe areas, contrast, and mascot visibility.
3. Add audio loudness/peak QC with ffmpeg/ffprobe or PCM sample analysis.
4. Add full caption/transcript alignment checks for cached and fallback voiceovers.
5. Add metrics ingestion from the posting provider and platform dashboards.
6. Rewrite the current long-form episode into 8-10 retention-focused sections and rerun the expert viral gate to 94+.
7. Build the long-form publish package: final render, thumbnail, title, description, chapters, pinned comment, and score-page UTM.
8. Convert live trend intake from file-based source notes into API-backed connectors.

## Production Recommendation

Use the pipeline now for one to three supervised shorts per day. Do not run it as a fully autonomous channel factory until render-level QC, audio loudness QC, trend ingestion, and metrics feedback are automated.

For live posting, keep the rule simple: scripts can be generated daily, but public posts must stay `review_required` until the exact video, caption, CTA, and audio pass QA and Codex approval stores the matching file hash.
