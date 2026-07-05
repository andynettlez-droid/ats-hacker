# Signal Video Pipeline Overhaul Plan

Status: active build plan.
Updated: 2026-07-05.

## Current Decision

Pause posting and rendering until the creative system is rebuilt in order:

1. Research.
2. Scripts.
3. Art direction.
4. Video mechanics.
5. Audio performance.
6. Render QA and Codex approval.

The script layer is now rebuilt and validated. The previous rendered shorts remain failed creative QA.

## Phase 1 - Research Layer

Implemented:

- Dated research brief: `marketing/content_research/resume_video_trends_2026-07-05.md`
- Updated swipe file: `marketing/viral_swipe_file.md`
- Daily packet `trendResearch` contract.

Acceptance:

- Every packet includes a human premise, platform pattern, copied research mechanic, and avoided failure mode.
- Generic best-practice summaries are not enough.

## Phase 2 - Script Layer

Implemented:

- Human-review transcript builder in `marketing_agent/daily_content_agent.py`.
- Trend gate and human-premise checks in `marketing_agent/creative_quality_gate.py`.
- Script-only validation packet:
  `marketing/daily_content/2026-07-05-human-recruiter-live-resume-teardown-rebuilt-from-viral-trend-re`

Acceptance:

- 18-32 second script.
- One exact weak resume line.
- One visible job requirement.
- Low-score reason before score reveal.
- Evidence ledger proof already visible on the resume.
- Honest rewrite only.
- Human score explanation.
- Fast free-score CTA.

Current status: passed script-only creative QA.

## Phase 3 - Art Direction Layer

Next.

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

## Phase 4 - Video Mechanics Layer

After art direction.

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

## Phase 5 - Audio Layer

After script and art direction.

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

## Phase 6 - Render QA And Approval

Only after phases 3-5 pass.

Acceptance:

- Rendered file passes technical QC.
- Manual creative director review says the clip is understandable, human, and watchable.
- Codex review packet includes local path/mobile URL, metadata, QA summary, and explicit approval phrase.
- No publishing without exact-file Codex approval.

