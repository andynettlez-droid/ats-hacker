# Signal Media Pipeline Readiness Review

Reviewed: 2026-07-05

## Verdict

The video pipeline is paused for creative rebuild. The previous rendered shorts proved the render/posting mechanics, but they are no longer considered post-ready because the scripts still sounded generated when read aloud and the score reveals did not feel earned enough.

The script layer has now been rebuilt first. A dated research brief, a `trendResearch` packet contract, stricter creative QA, and a new script-only validation packet are in place. No new video or audio was rendered during this pass.

The new Codex approval layer now wraps the existing daily packet, Remotion render, QC, promotion, and posting queue. Videos move through a durable local SQLite state machine and stop at `AWAITING_CODEX_APPROVAL` until the exact reviewed file is approved in Codex.

The current long-form YouTube lane has a rendered 1920x1080 review cut, thumbnail path, segmented ElevenLabs voiceover, audio QC, and Codex approval gating. It still needs expansion to a real long-form structure before it can move to `AWAITING_CODEX_APPROVAL`.

## 2026-07-05 Script Layer Rebuild

New research input:

- `marketing/content_research/resume_video_trends_2026-07-05.md`
- Updated `marketing/viral_swipe_file.md`
- Updated `marketing/SHORTS_CREATIVE_SYSTEM.md`
- Updated `marketing/script_human_review_gate.md`
- Updated `marketing/voice_director.md`

New script validation packet:

- `marketing/daily_content/2026-07-05-human-recruiter-live-resume-teardown-rebuilt-from-viral-trend-re`
- Creative gate: passed, 100/100, script-only.
- Shorts: Live Resume Review, Recruiter Search Test, Job Description Review.
- Audio readiness: not requested in this pass.
- Render readiness: props written, but no render should be treated as post-ready until art direction and audio are rebuilt.

What changed:

- Daily packets now require `trendResearch.humanPremise`, `platformPattern`, `copyFromResearch`, and `avoid`.
- Script generation now prefers a human reviewer reading one resume line against one job requirement.
- Score narration now uses human judgment language instead of "the rubric gives..." phrasing.
- The older one-off `ResumeCrimeScene` preset no longer uses the rejected marketing-role/HubSpot/CAC script.
- Creative QA now fails missing human situations, missing trend research, rubric-first narration, and unexplained score jumps.

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
- The current rebuilt script packet passes the creative quality gate at 100/100, with trend-research, human-premise, repeated-opening, robotic-phrase, first-person reviewer, score-rubric, evidence-ledger, and role-rotation checks enabled.
- The studio short metadata/queue QC gate passes.
- The audio asset QC gate passes for linked short voiceovers, music, and all 9 long-form episode segments.
- A source-backed trend intake file exists for the current daily packet.
- Thumbnail and long-form renderer components exist.
- A long-form YouTube quality gate now scores title, hook, retention architecture, proof density, visual plan, claim safety, creator voice, product bridge, audio readiness, and render QA.

## What Is Not Ready Yet

- Automated visual safe-area QC exists for bright/saturated margin issues and now supports `ResumeDeskReview`. It is not a full semantic visual QA system for overlap, contrast, mascot personality, or whether the video is funny.
- No automated audio loudness/peak/LUFS check. The current audio gate validates files, codecs, duration, sample rate, bitrate, channels, and mix-volume settings, but does not measure loudness.
- Word-level caption alignment is available for new ElevenLabs `/with-timestamps` generations. Existing cached daily voiceovers and OpenAI fallback voiceovers use scene captions.
- The daily content agent now treats ElevenLabs as required when requested, uses the configured voice ID, and fails instead of silently falling back when `--require-elevenlabs` is set.
- No automatic platform metrics ingestion from TikTok, Instagram, or YouTube.
- No live automated trend feed from TikTok Creative Center, YouTube, Google Trends, Reddit, or LinkedIn. Current trend intake is file-based.
- The script creative gate can still overstate readiness because it grades packet text, not rendered video, audio, pacing, or humor in context.
- Long-form YouTube has a verified render/review path for this packet, but the active render is too short for publish approval and needs expansion before any live upload.
- The queue still contains older ad-style clips that should be reviewed or retired before they dilute the new teardown format.

## Current Codex Review Assets

The previous active daily batch should remain review-only and should not be posted. The current rebuild produced a script-only packet for validation, not a new approval-ready render. Older approval records from the weaker repeated batch should remain `REVISION_REQUESTED` or be ignored so they do not dilute the new direction.

| Run ID | Title | Status |
| --- | --- | --- |
| `405962b7592c8e26` | I would circle this line first | Failed creative review; do not approve/post. |
| `553ac4f944fb4202` | I searched the resume. Bad news. | Failed creative review; do not approve/post. |
| `1233c94bb025a999` | The job post gave the answer key | Failed creative review; do not approve/post. |

When a new render is ready, export it to `marketing/codex_reviews` and serve it from the repo root with:

```bat
py -3 -m http.server 8765 --directory marketing/codex_reviews
```

Only use the URLs printed by the next `prepare-review` run for current approval decisions.

## Current Studio Short Assets

- Previous rendered files exist in `marketing/remotion/out/`, but they are no longer approved for posting after manual creative review.
- Current script-only props exist under `marketing/remotion/props_daily_2026-07-05_human-recruiter-live-resume-teardown-rebuilt-from-viral-trend-re_*`.

The next render pass should use the new script-only packet only after art direction and audio have been updated.

## Current Queue Snapshot

Latest manual pipeline output:

- Three human-read resume-review scripts passed the rebuilt creative gate; no new renders were produced in the rebuild pass.
- The long-form packet has generated voiceover segments and props, but the episode MP4 was not rendered in this pass; expand and render before review approval.
- Autopost dry run confirms it is blocked until Codex approval and `--approved`.
- Current post-grade packet: 1.
- Render-ready and QA-passed shorts in the current daily packet: 3.
- Render-ready and QA-passed long-form YouTube episodes in the current daily packet: 0.
- Rendered long-form review cuts in the current daily packet: 1.
- Studio voiceover: available through ElevenLabs `/with-timestamps`, but the next pass should test creator-style delivery against the rebuilt scripts before rendering final videos.
- Quiet music: available.
- Source-backed trend intake: available.
- Long-form renderer: available.
- Thumbnail generator: available.
- Studio daily exports: available.
- Studio daily queue: available.
- Automated render QC: available.
- Audio asset QC: available.
- Score-rubric QA report: `marketing/daily_content/2026-07-05-human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor/score_rubric_qa_report.md`.
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

1. Rebuild art direction around the script packet: desk markup, recruiter search console, and answer-key highlighter should look visually distinct.
2. Generate ElevenLabs voice tests for the rebuilt scripts before full render; prefer scratch-read speech-to-speech when a human read exists.
3. Add audio loudness/peak QC with ffmpeg/ffprobe or PCM sample analysis.
4. Extend `npm run qc:daily:shorts` with frame still/pixel checks for text overlap, safe areas, contrast, and mascot visibility.
5. Retire or rewrite older ad-style queued clips so the public queue is not diluted by weaker content.
6. Add metrics ingestion from the posting provider and platform dashboards.
7. Add a pinned-comment template and platform-specific long-form description checklist.
8. Add long-form transcript/caption generation from the final rendered audio.
9. Convert live trend intake from file-based source notes into API-backed connectors.

## Production Recommendation

Use the pipeline now for script generation and supervised pre-production only. Do not publish or resume daily video production until the art direction and audio rebuilds pass manual review plus render-level QC.

For live posting, keep the rule simple: scripts can be generated daily, but public posts must stay `review_required` until the exact video, caption, CTA, and audio pass QA and Codex approval stores the matching file hash.
