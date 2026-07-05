# Signal Video Pipeline Overhaul Plan

Status: active build plan.
Updated: 2026-07-05.

## Current Decision

Pause daily posting until one gold-standard short is approved in Codex. The current approval candidate is rendered and queued as `review_required`:

- `marketing/remotion/out/gold-signal-search-test-review.mp4`
- `marketing/autopost/videos/gold-signal-search-test-review.mp4`
- `marketing/gold_standard_short/2026-07-05-signal-search-test/packet.json`

Do not resume daily generation until this candidate is approved or revised into a stronger baseline.

The rebuild order remains:

1. Research.
2. Scripts.
3. Art direction.
4. Video mechanics.
5. Audio performance.
6. Render QA and Codex approval.

The script layer is rebuilt, the desk-review art direction is implemented for the pilot, and the previous rendered shorts remain failed creative QA.

## Phase 1 - Research Layer

Implemented:

- Dated research brief: `marketing/content_research/resume_video_trends_2026-07-05.md`
- High-view benchmark swipe file: `marketing/content_research/high_view_resume_video_swipe_2026-07-05.md`
- Updated swipe file: `marketing/viral_swipe_file.md`
- Daily packet `trendResearch` contract.

Acceptance:

- Every packet includes a human premise, platform pattern, copied research mechanic, and avoided failure mode.
- Every packet must cite at least two benchmark URLs or high-view trend sources from the high-view swipe file.
- Every packet must name the specific borrowed mechanic: red-pen teardown, expressive face plus artifact, recruiter experiment/search test, taboo hack debunk, or job-seeker frustration setup.
- Generic best-practice summaries are not enough.

## Phase 2 - Script Layer

Implemented:

- Human-review transcript builder in `marketing_agent/daily_content_agent.py`.
- Trend gate and human-premise checks in `marketing_agent/creative_quality_gate.py`.
- Script-only validation packet:
  `marketing/daily_content/2026-07-05-human-recruiter-live-resume-teardown-rebuilt-from-viral-trend-re`

Acceptance:

- 18-28 second script, with 38-72 voiceover words.
- One exact weak resume line.
- One visible job requirement.
- Low-score reason before score reveal.
- Evidence ledger proof already visible on the resume.
- Honest rewrite only.
- Human score explanation.
- Fast free-score CTA.
- Script reads like a human cold review: open resume, read line, react, point to job requirement, find buried proof, rewrite.
- Numeric score is forbidden until a visible score receipt appears.
- Voiceover cannot say "I would score it around..." because that makes the score feel arbitrary.

Current status: previous script-only packets are treated as obsolete under the stricter high-view benchmark gate. The active baseline is the gold-standard rendered candidate.

## Phase 3 - Art Direction Layer

Implemented for the pilot.

Build three visually distinct, professional-looking short formats:

- Desk Markup: realistic resume paper, job post, red pen, sticky notes, Signal as small guide.
- Recruiter Search Console: resume/search interface, visible no-hit/search-hit states, minimal dark UI.
- Answer-Key Highlighter: job description terms highlighted, resume line matched against those terms.

Acceptance:

- Resume and JD look like credible professional artifacts.
- No repeated dark-neon SaaS look across a daily batch.
- Signal mascot appears as a helper/reaction character, not the presenter.
- Source proof and rewrite are visually connected.
- Score reveal appears only after the score rationale is visible.

Pilot implementation:

- `ResumeDeskReview` renders a professional resume, nearby job post, red marker/sticky-note score receipt, rewrite card, captions, and Signal CTA.
- Score badges are delayed until after the score receipt is visible.
- The pilot uses a clean desk markup style; future daily batches still need two additional distinct styles before publishing resumes.

## Phase 4 - Video Mechanics Layer

Implemented for the pilot.

Update Remotion scenes so every script beat has a visual beat:

- Hook frame.
- Weak line read.
- Job requirement/search term.
- Source proof lower on resume.
- Rewrite.
- Score rationale.
- CTA.

Acceptance:

- Vertical 1080x1920, 30fps.
- Main artifact readable on mobile.
- Captions in safe areas.
- No overlap between captions, score, CTA, and mascot.
- Three daily shorts use different visual archetypes.

Pilot status: one gold-standard archetype exists. Daily batch generation remains blocked until this single format is approved.

## Phase 5 - Audio Layer

Implemented for the pilot, with gaps.

Preferred path:

- Human scratch read.
- ElevenLabs speech-to-speech.
- Word-level timestamps for captions.

Fallback path:

- ElevenLabs multi-take TTS with faster creator-style settings.
- Select take by pacing, timestamp quality, and listen-test notes.

Acceptance:

- Sounds like a person reviewing a resume aloud.
- No corporate explainer voice.
- No harsh or repetitive sound effects.
- Quiet music only.
- Add LUFS/peak QC before posting.

Pilot status:

- ElevenLabs `/with-timestamps` generates the current short voiceover and word-level captions.
- No FFmpeg/ffprobe is installed in this environment, so LUFS/peak QC is still missing.
- No music/SFX is used in the pilot; the gate records `music_omitted_no_sfx` to avoid adding annoying effects.

## Phase 6 - Render QA And Approval

Active for the pilot.

Acceptance:

- Rendered file passes technical QC.
- Manual creative director review says the clip is understandable, human, and watchable.
- Codex review packet includes local path/mobile URL, metadata, QA summary, and explicit approval phrase.
- No publishing without exact-file Codex approval.

Pilot status:

- Studio QC passed: `marketing/remotion/out/gold-signal-search-test-studio-qc.json`
- Audio QC passed: `marketing/remotion/out/gold-signal-search-test-audio-qc.json`
- Visual safe-area QC passed: `marketing/remotion/out/gold-signal-search-test-visual-qc.json`
- Autopost entry status: `review_required`
- Approval phrase for live posting remains explicit Codex approval of the exact file.
