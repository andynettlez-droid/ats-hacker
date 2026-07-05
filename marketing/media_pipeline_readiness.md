# Signal Media Pipeline Readiness Review

Reviewed: 2026-07-04

## Verdict

The short-form pipeline is ready for supervised Codex review-gated posting. The current long-form YouTube render is a review cut only; it is not publish-ready because it fails the minimum long-form duration gate. The system is not yet ready for fully unattended daily channel production.

The current `ResumeDeskReview` shorts are materially stronger than the rejected mascot/product-demo and repeated dashboard cuts: the resume is the main character, the job description is visible, the weak bullet is grounded in a professional resume artifact, the narration uses first-person reviewer language, and the score reveal is preceded by visible low-score rationale. The latest batch also avoids the prior robotic repetition by rotating three distinct roles: Product Data Analyst, Mid-Market Account Executive, and Frontend Software Engineer.

The new Codex approval layer now wraps the existing daily packet, Remotion render, QC, promotion, and posting queue. Videos move through a durable local SQLite state machine and stop at `AWAITING_CODEX_APPROVAL` until the exact reviewed file is approved in Codex.

The current long-form YouTube lane has a rendered 1920x1080 review cut, thumbnail path, segmented ElevenLabs voiceover, audio QC, and Codex approval gating. It still needs expansion to a real long-form structure before it can move to `AWAITING_CODEX_APPROVAL`.

## What Is Ready

- `ResumeCrimeScene` and `ResumeDeskReview` render vertical 1080x1920, 30fps shorts.
- Three daily studio short exports exist in `marketing/remotion/out/`.
- Studio voiceover assets exist for the daily shorts and long-form episode. The latest reviewed batch uses ElevenLabs `/with-timestamps` for fresh narration and caption alignment.
- Quiet music assets exist and are used instead of harsh SFX.
- The posting layer supports TikTok, Instagram, and YouTube through Upload-Post.
- The posting layer has a review gate for `draft` and `review_required` entries.
- The posting layer now requires a matching `codexApproval.fileSha256` before `--approved` can publish a review-required entry.
- `marketing_agent/codex_video_approval.py` renders, promotes, QC's, exports, and tracks videos through Codex approval state.
- `ResumeCrimeScene` and `ResumeDeskReview` render word-level captions when fresh ElevenLabs timestamp metadata exists.
- The autopost dry run works and reports file hashes before publishing.
- The Python marketing agent stack compiles.
- The Remotion TypeScript check passes.
- The current daily script packet passes the creative quality gate at 100/100, with repeated-opening, robotic-phrase, first-person reviewer, and role-rotation checks enabled.
- The studio short metadata/queue QC gate passes.
- The audio asset QC gate passes for linked short voiceovers, music, and all 9 long-form episode segments.
- A source-backed trend intake file exists for the current daily packet.
- Thumbnail and long-form renderer components exist.
- A long-form YouTube quality gate now scores title, hook, retention architecture, proof density, visual plan, claim safety, creator voice, product bridge, audio readiness, and render QA.

## What Is Not Ready Yet

- Automated visual safe-area QC exists for bright/saturated margin issues and now supports `ResumeDeskReview`. It is not a full semantic visual QA system for overlap, contrast, mascot personality, or whether the video is funny.
- No automated audio loudness/peak/LUFS check. The current audio gate validates files, codecs, duration, sample rate, bitrate, channels, and mix-volume settings, but does not measure loudness.
- Word-level caption alignment is available only for new ElevenLabs `/with-timestamps` generations. Existing cached daily voiceovers and OpenAI fallback voiceovers use scene captions.
- The daily content agent now treats ElevenLabs as required when requested, uses the configured voice ID, and fails instead of silently falling back when `--require-elevenlabs` is set.
- No automatic platform metrics ingestion from TikTok, Instagram, or YouTube.
- No live automated trend feed from TikTok Creative Center, YouTube, Google Trends, Reddit, or LinkedIn. Current trend intake is file-based.
- The script creative gate can overstate readiness because it grades packet text, not rendered video.
- Long-form YouTube has a verified render/review path for this packet, but the active render is too short for publish approval and needs expansion before any live upload.
- The queue still contains older ad-style clips that should be reviewed or retired before they dilute the new teardown format.

## Current Codex Review Assets

The active daily batch has three `ResumeDeskReview` shorts in `AWAITING_CODEX_APPROVAL`. The long-form episode for this packet has generated narration and render props, but it has not been rendered or promoted in this pass. Older approval records from the weaker repeated batch have been marked `REVISION_REQUESTED` so they are no longer the active review set.

| Run ID | Title | Mobile review URL | Approval phrase |
| --- | --- | --- | --- |
| `99bb86ba61d0ca1c` | I would rewrite this bullet immediately | `http://192.168.2.10:8765/20260705-99bb86ba61d0ca1c-i-would-rewrite-this-bullet-immediately/daily-i-would-rewrite-this-bullet-immediately.mp4` | `APPROVE POST 99bb86ba61d0ca1c` |
| `b40eb88cf2c39668` | The Ctrl+F test this resume fails | `http://192.168.2.10:8765/20260705-b40eb88cf2c39668-the-ctrl-f-test-this-resume-fails/daily-the-ctrl-f-test-this-resume-fails.mp4` | `APPROVE POST b40eb88cf2c39668` |
| `a389a69ed7d879e3` | This resume missed the job posting | `http://192.168.2.10:8765/20260705-a389a69ed7d879e3-this-resume-missed-the-job-posting/daily-this-resume-missed-the-job-posting.mp4` | `APPROVE POST a389a69ed7d879e3` |

This file is local and git-ignored. To review on mobile from the repo root, run:

```bat
py -3 -m http.server 8765 --directory marketing/codex_reviews
```

Then open the URLs printed by `prepare-review`.

## Current Studio Short Assets

- `marketing/remotion/out/daily-i-would-rewrite-this-bullet-immediately.mp4`
- `marketing/remotion/out/daily-the-ctrl-f-test-this-resume-fails.mp4`
- `marketing/remotion/out/daily-this-resume-missed-the-job-posting.mp4`

The three `human-desk-resume-review-inspired-by-gohar-khan-resume-tips` shorts are the active review assets. Older role-specific assets are retained in the tree for traceability but should not be posted without a fresh review.

## Current Queue Snapshot

Latest manual pipeline output:

- Three human desk-review daily shorts rendered, passed QA, and exported to Codex review.
- The long-form packet has generated voiceover segments and props, but the episode MP4 was not rendered in this pass; expand and render before review approval.
- Older repeated/role-specific review records have been moved to `REVISION_REQUESTED`.
- Autopost dry run confirms it is blocked until Codex approval and `--approved`.
- Current post-grade packet: 1.
- Render-ready and QA-passed shorts in the current daily packet: 3.
- Render-ready and QA-passed long-form YouTube episodes in the current daily packet: 0.
- Rendered long-form review cuts in the current daily packet: 1.
- Studio voiceover: available through ElevenLabs `/with-timestamps` for the latest review asset.
- Quiet music: available.
- Source-backed trend intake: available.
- Long-form renderer: available.
- Thumbnail generator: available.
- Studio daily exports: available.
- Studio daily queue: available.
- Automated render QC: available.
- Audio asset QC: available.
- Long-form metadata/audio/thumbnail QC: audio and thumbnail paths exist; publish QC fails duration for the active review cut.
- Missing: platform metrics feed, audio loudness/peak QC, full transcript/caption alignment for cached/fallback voiceovers, automated live trend API connector, and faster long-form rendering.

## Current Audio Position

ElevenLabs is the preferred default for voiceover and generated sound because it can provide repeatable studio narration, brand-consistent audio assets, and timestamp alignment in one workflow.

Current credential status:

- `py -3 marketing_agent\daily_content_agent.py --check-elevenlabs --probe-elevenlabs-tts --json` passes a TTS probe using the configured voice ID.
- The current key is restricted to Text to Speech. That is acceptable for generation, but voice-list reads can return permission errors, so do not rely on voice discovery with this key.
- The latest current batch generated fresh ElevenLabs narration and timestamp alignment for all three shorts and the long-form episode.

Recommended env values:

```env
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_WITH_TIMESTAMPS=true
```

Verify after replacing or rotating the key:

```bat
py -3 marketing_agent\daily_content_agent.py --check-elevenlabs --probe-elevenlabs-tts --json
```

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
6. Add a pinned-comment template and platform-specific long-form description checklist.
7. Add long-form transcript/caption generation from the final rendered audio.
8. Convert live trend intake from file-based source notes into API-backed connectors.

## Production Recommendation

Use the pipeline now for one to three supervised shorts per day. Do not run it as a fully autonomous channel factory until render-level QC, audio loudness QC, trend ingestion, and metrics feedback are automated.

For live posting, keep the rule simple: scripts can be generated daily, but public posts must stay `review_required` until the exact video, caption, CTA, and audio pass QA and Codex approval stores the matching file hash.
