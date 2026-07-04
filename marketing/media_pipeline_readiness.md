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
- Studio voiceover assets exist for the daily shorts and long-form episode. ElevenLabs remains preferred, but the current machine-level ElevenLabs key is low-quota and the latest reviewed short used OpenAI TTS fallback.
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
- The daily content agent now validates/selects an available ElevenLabs voice instead of assuming the legacy default voice ID. It also disables further ElevenLabs calls for the current run after quota/permission failures.
- No automatic platform metrics ingestion from TikTok, Instagram, or YouTube.
- No live automated trend feed from TikTok Creative Center, YouTube, Google Trends, Reddit, or LinkedIn. Current trend intake is file-based.
- The script creative gate can overstate readiness because it grades packet text, not rendered video.
- Long-form YouTube has a renderer and review path, but not a fully verified final episode workflow.
- The current long-form packet scored 83/100 on the expert viral gate and is blocked from publish-ready status until the full episode is strengthened and rendered QA passes.
- The queue still contains older ad-style clips that should be reviewed or retired before they dilute the new teardown format.

## Current Codex Review Assets

All three current daily shorts are in `AWAITING_CODEX_APPROVAL` and passed script, studio metadata, audio asset, and visual safe-area QC.

| Run ID | Title | Mobile review URL | Approval phrase |
| --- | --- | --- | --- |
| `50350129efcd445e` | This marketing resume hid the actual revenue proof | `http://192.168.2.10:8765/20260704-50350129efcd445e-this-marketing-resume-hid-the-actual-revenue-proof/daily-this-marketing-resume-hid-the-actual-revenue-proof.mp4` | `APPROVE POST 50350129efcd445e` |
| `d962d2cc75f39aab` | This sales resume forgot to say sales | `http://192.168.2.10:8765/20260704-d962d2cc75f39aab-this-sales-resume-forgot-to-say-sales/daily-this-sales-resume-forgot-to-say-sales.mp4` | `APPROVE POST d962d2cc75f39aab` |
| `71e14e8e21715d7d` | This developer resume hides the stack | `http://192.168.2.10:8765/20260704-71e14e8e21715d7d-this-developer-resume-hides-the-stack/daily-this-developer-resume-hides-the-stack.mp4` | `APPROVE POST 71e14e8e21715d7d` |

This file is local and git-ignored. To review on mobile from the repo root, run:

```bat
py -3 -m http.server 8765 --directory marketing/codex_reviews
```

Then open the URLs printed by `prepare-review`.

## Current Studio Short Assets

- `marketing/remotion/out/daily-this-marketing-resume-hid-the-actual-revenue-proof.mp4`
- `marketing/remotion/out/daily-this-sales-resume-forgot-to-say-sales.mp4`
- `marketing/remotion/out/daily-this-developer-resume-hides-the-stack.mp4`

These are the assets that should be promoted for review-gated posting, not the earlier first-pass daily short.

## Current Queue Snapshot

Latest manual pipeline output:

- Three improved role-specific daily shorts rendered and exported to Codex review.
- Autopost dry run confirms it is blocked until Codex approval and `--approved`.
- Current post-grade packet: 1.
- Render-ready and QA-passed shorts in the current daily packet: 3.
- Studio voiceover: available through OpenAI fallback for the latest review asset.
- Quiet music: available.
- Source-backed trend intake: available.
- Long-form renderer: available.
- Thumbnail generator: available.
- Studio daily exports: available.
- Studio daily queue: available.
- Automated render QC: available.
- Audio asset QC: available.
- Long-form expert viral gate: available; current episode score is 83/100 and not publish-ready.
- Missing: valid high-quota ElevenLabs key for full daily voiceover generation, platform metrics feed, audio loudness/peak QC, full transcript/caption alignment for cached/fallback voiceovers, automated live trend API connector.

## Current Audio Position

ElevenLabs is the preferred default for voiceover and generated sound because it can provide repeatable studio narration, brand-consistent audio assets, and timestamp alignment in one workflow.

Current credential status:

- `py -3 marketing_agent\daily_content_agent.py --check-elevenlabs --json` can read voices and selects `George - Warm, Captivating Storyteller` (`JBFqnCBsd6RMkjVDRZzb`).
- The current machine-level key has very limited remaining TTS quota, so full daily generation falls back to OpenAI TTS.
- Chrome control was unavailable from Codex even though Chrome, the Codex Chrome Extension, and the native host diagnostics passed. A new ElevenLabs key still needs to be created/copied manually or after Chrome control is restored.

Recommended env values:

```env
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_WITH_TIMESTAMPS=true
```

Verify after replacing the key:

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
6. Rewrite the current long-form episode into 8-10 retention-focused sections and rerun the expert viral gate to 94+.
7. Build the long-form publish package: final render, thumbnail, title, description, chapters, pinned comment, and score-page UTM.
8. Convert live trend intake from file-based source notes into API-backed connectors.

## Production Recommendation

Use the pipeline now for one to three supervised shorts per day. Do not run it as a fully autonomous channel factory until render-level QC, audio loudness QC, trend ingestion, and metrics feedback are automated.

For live posting, keep the rule simple: scripts can be generated daily, but public posts must stay `review_required` until the exact video, caption, CTA, and audio pass QA and Codex approval stores the matching file hash.
