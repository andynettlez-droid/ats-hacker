# Signal Media Pipeline Readiness Review

Reviewed: 2026-07-06

## 2026-07-06 Active Pipeline Reset

The old `marketing_agent/video_pipeline.py` path is now retired. It remains only as a guardrail message that points agents to the new Signal Growth Engine runner. Do not use the old HeyGen/legacy Remotion command path for new public shorts.

Active production lane:

- Research and hook rules: `AGENTS.md`, `skills/hook_playbook.md`, `skills/brand.md`
- Veo shot direction: `skills/veo_prompt_template.md`
- Abby voice direction and timestamp endpoint: `skills/voiceover.md`
- Pipeline/state CLI: `marketing_agent/signal_growth_pipeline.py`
- Sync-safe editor: `skills/assemble.ps1` on Windows, `skills/assemble.sh` on bash
- Logo assets: `marketing/brand/signal-logo-mark.png` and `marketing/brand/signal-logo-mark.svg`

Current proven ad render:

- Final file: `C:\Users\andyn\Downloads\signal_ad_final.mp4`
- Mobile review URL while local server is running: `http://192.168.2.10:8770/signal_ad_final.mp4`
- QA: 1080x1920, H.264, AAC, 30fps, 47.53s
- Demo flicker fix: the site demo section now uses a real screen-recorded walkthrough from `marketing_agent/capture_signal_demo.mjs`. The assembler prefers `signal_feature_demo_recording.mp4` and only falls back to the old `signal_landing_demo.png` pan if the recording is missing.

Codex approval is the only review gate. The pipeline may render, QA, prepare metadata, and produce a review packet, but posting stays blocked until Andrew approves the exact video in Codex chat.

Core commands:

```bat
py -3 marketing_agent\signal_growth_pipeline.py init-run --topic "resume teardown"
py -3 marketing_agent\signal_growth_pipeline.py resolve-abby
py -3 marketing_agent\signal_growth_pipeline.py voice --text-file marketing\growth_runs\RUN_ID\vo.txt --out marketing\growth_runs\RUN_ID\vo.mp3 --run-id RUN_ID
py -3 marketing_agent\signal_growth_pipeline.py veo --text-file marketing\growth_runs\RUN_ID\shot01.txt --out marketing\growth_runs\RUN_ID\shot01.mp4 --run-id RUN_ID
$env:PLAYWRIGHT_CORE_DIR = "$env:TEMP\signal-playwright-core\node_modules"
node marketing_agent\capture_signal_demo.mjs --out C:\Users\andyn\Downloads\signal_feature_demo_recording.mp4 --seconds 18
powershell -ExecutionPolicy Bypass -File skills\assemble.ps1 -WorkDir C:\Users\andyn\Downloads -Out signal_ad_final.mp4
py -3 marketing_agent\signal_growth_pipeline.py qa --video C:\Users\andyn\Downloads\signal_ad_final.mp4 --run-id RUN_ID --write
py -3 marketing_agent\signal_growth_pipeline.py review --run-id RUN_ID
```

Known remaining gaps:

- The new runner can call Veo and ElevenLabs directly, but it does not yet automate the whole creative research/script-writing judgment. Keep the script/hook human-sounding gate active.
- The sync-safe assembler currently matches the successful Abby/Veo/live-product-demo ad structure. Future teardown shorts should get their own deterministic assembler or Remotion composition once the gold standard is approved.
- QA is technical plus approval-state gating. It still needs automated LUFS/true-peak checks and semantic visual overlap detection.

## Verdict

The video pipeline is paused for creative rebuild. The previous rendered shorts proved the render/posting mechanics, but they are no longer considered post-ready because the scripts still sounded generated when read aloud and the score reveals did not feel earned enough.

The script layer has now been rebuilt first. A dated research brief, a high-view benchmark swipe file, a stricter `trendResearch` packet contract, stricter creative QA, and a gold-standard single-short approval lane are in place.

The previous gold-standard candidate was superseded because the script still sounded generated. The current gold-standard candidate is rendered, queued as `review_required`, and awaiting Andrew's Codex approval before any daily posting resumes:

- Review MP4: `marketing/autopost/videos/gold-real-reviewer-teardown.mp4`
- Render output: `marketing/remotion/out/gold-real-reviewer-teardown.mp4`
- Props: `marketing/remotion/props_gold_real_reviewer_teardown.json`
- Review packet: `marketing/gold_standard_short/2026-07-05-real-reviewer-teardown/packet.json`
- Draft metadata: `marketing/gold_standard_short/2026-07-05-real-reviewer-teardown/autopost_drafts.json`
- Studio QC: `marketing/remotion/out/gold-real-reviewer-studio-qc.json`
- Audio QC: `marketing/remotion/out/gold-real-reviewer-audio-qc.json`
- Visual safe-area QC: `marketing/remotion/out/gold-real-reviewer-visual-qc.json`

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

- Daily packets now require `trendResearch.humanPremise`, `platformPattern`, `copyFromResearch`, `avoid`, at least two `benchmarkUrls`, `borrowedMechanic`, `whyThisMechanicFits`, and `whatNotToCopy`.
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
- The previous rebuilt script packet is no longer considered sufficient after the high-view benchmark research pass. The gate now requires benchmark URLs, a named borrowed mechanic, 38-72 voiceover words, and no arbitrary "I would score it around..." narration.
- A single gold-standard `ResumeDeskReview` candidate is rendered and queued for Codex approval before daily posting resumes.
- The gold-standard lane uses ElevenLabs `/with-timestamps` through `marketing/remotion/scripts/generate_short_voiceover.mjs`, producing word-level captions for a 23.6s review short.
- `ResumeDeskReview` now delays the big score badge until after the score receipt appears, so the score reveal is earned by visible evidence.
- Studio QC now allows an honest `music_omitted_no_sfx` policy for clips where clean voice is preferred over annoying effects.
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

The previous active daily batch should remain review-only and should not be posted. Older approval records from the weaker repeated batch should remain `REVISION_REQUESTED` or be ignored so they do not dilute the new direction.

| Run ID | Title | Status |
| --- | --- | --- |
| `gold-real-reviewer-teardown` | I don't hate this resume line | Rendered, QC-passed, queued `review_required`, awaiting Codex approval. |
| `gold-signal-search-test` | I would rewrite this resume line first | Superseded; do not approve/post. |
| `405962b7592c8e26` | I would circle this line first | Failed creative review; do not approve/post. |
| `553ac4f944fb4202` | I searched the resume. Bad news. | Failed creative review; do not approve/post. |
| `1233c94bb025a999` | The job post gave the answer key | Failed creative review; do not approve/post. |

Serve the current gold-standard review from the Remotion `out` directory or the autopost queue with:

```bat
py -3 -m http.server 8765 --directory marketing/remotion/out
```

Do not publish unless Andrew replies with an explicit approval phrase for the exact file.

## Current Studio Short Assets

- Previous rendered files exist in `marketing/remotion/out/`, but they are no longer approved for posting after manual creative review.
- The current approval candidate is `marketing/remotion/out/gold-real-reviewer-teardown.mp4`.
- Current gold-standard props are `marketing/remotion/props_gold_real_reviewer_teardown.json`.

The next render pass should use this gold-standard pattern only after the candidate is reviewed and either approved or revised.

## Current Queue Snapshot

Latest manual pipeline output:

- One current gold-standard short is rendered and awaiting approval; no daily batch should resume until that direction is approved or revised.
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
