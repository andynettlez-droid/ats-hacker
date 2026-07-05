# Signal Shorts Creative System

Status: active direction for daily short-form production.

## Problem We Are Fixing

The first studio shorts proved the pipeline can render and post, but the creative looked too repetitive. Daily content must not feel like the same SaaS ad with swapped captions.

## Daily Format Rotation

Each day should produce three distinct short concepts:

- Red-Marker Resume Roast: paper/resume-first, red markup, blunt recruiter energy.
- Human Desk Review: top-down paper resume, job post nearby, reviewer-style narration, and one circled line. This is the default for clips that need to feel more human and less like a software demo.
- Recruiter Search Console: search term premise, visible no-hit or weak-hit result, then the rewrite changes the search receipt.
- Job-Description Answer Key: the JD is treated like the answer sheet, and the resume either answers it or fails it.
- AI Resume Roast: funny, blunt, comic palette, fast pace.
- Recruiter Search Test: search-box premise, sticky-note or desk-review palette, slower proof reveal.
- Signal Rescue: Signal acts like a helpful character inside a repeatable series wrapper, pulling buried proof out of vague resume language.
- ATS Myth Lab: terminal/search-system palette, debunks one myth without fearmongering.
- One Bullet Fix: highlighter palette, before/after rewrite with a visible score movement.

## Visual Rules

- Signal must speak, point, react, wink, or rescue at least once per short.
- Resume and job description stay on screen as the main artifact.
- Avoid using the same palette in two consecutive shorts when possible.
- Do not repeat the same dark neon SaaS palette across the daily batch.
- Avoid overlapping full resume boards during scene transitions.
- Keep bottom-third reaction bubbles clear of the CTA and score badge.
- Run visual safe-area QC after rendering stills so edge-clipped labels and CTA collisions fail before posting.
- Music stays quiet; no harsh repetitive sound effects.
- Prefer physical paper, desk, marker, highlighter, and sticky-note devices when the script is a resume teardown. Use dashboards only when the premise is explicitly a search console or product walkthrough.

## Narration Rules

- Target runtime is 18-32 seconds for Shorts. Anything longer fails unless explicitly marked long-form.
- Open with a joke or painful job-search truth in the first two seconds.
- Punch at vague resume language and broken job-search friction, not at job seekers.
- Build a complete story spine: conflict, target evidence, weak source line, consequence, fix, payoff.
- Make one useful teaching point before the CTA, but make it feel discovered through the teardown rather than explained as a tip.
- End with the free Signal score, not an aggressive paid pitch.
- Avoid template narration. Banned recurring reads include "JD asks for," "real, but buried," and "same person, clearer proof."
- Also ban default HubSpot/CAC examples unless the selected case is explicitly a marketing role.
- Prefer first-person reviewer phrasing: "I would circle this...", "I searched the resume...", "I would write...".
- Do not force meme slang. Terms like "NPC bullet", "resume oatmeal", "LinkedIn breath", and "business casual shrug" fail unless there is a very clear human reason to use them.
- The score reveal must be earned. Show the score receipt first: keyword match, tool match, metric proof, and/or outcome clarity.

## Viral Script Spine

Every short must answer these in order:

1. Why should the viewer stop scrolling?
2. What did the recruiter or job description look for?
3. What did the resume actually say?
4. Why does that create a miss?
5. What is the honest rewrite?
6. What changed in the score, and what should the viewer do next?

## Viral Research Stage

Before script generation, update or review `marketing/viral_swipe_file.md` and the latest dated research brief under `marketing/content_research/`. The script generator should copy niche-specific patterns only: recruiter reacts, resume teardown, search test, job-description translation, and resume roast. Generic social-media best practices are not enough to pass the creative gate.

Every packet now needs a `trendResearch` object:

- `humanPremise`: the real-feeling situation in the first frame.
- `platformPattern`: the short-form pattern being copied.
- `copyFromResearch`: which researched mechanic the clip borrows.
- `avoid`: the failed pattern this script is explicitly avoiding.
- `benchmarkUrls`: at least two real benchmark URLs from the high-view swipe file or current niche research.
- `borrowedMechanic`: the specific mechanic being adapted, such as red-pen teardown, recruiter experiment, taboo hack debunk, or job-seeker frustration setup.
- `whyThisMechanicFits`: why that benchmark mechanic fits this resume/JD case.
- `whatNotToCopy`: what must not be copied from the benchmark, such as exact wording, creator likeness, or generic list pacing.
- `avoid`: which previous failure mode the clip refuses to repeat.

If the clip starts as a product demo instead of a human review situation, it fails before rendering.

## Required Gates

- Creative director gate: hook, visible artifact, weak bullet, visible consequence, honest rewrite, score receipt, CTA.
- Visual diversity gate: the first three daily shorts must use different format archetypes and palettes.
- Duration gate: 18-32 seconds for short-form outputs.
- Score-rationale gate: no score jump without the six-part `score_rubric` totals matching the visible score reveal.
- Human-read gate: reviewer reads one exact resume line, reacts naturally, compares it to one job requirement, then rewrites only that experience.
- Trend gate: packet includes `trendResearch` and the script hook sounds like a human situation, not a feature pitch.
- Voice-quality gate: ElevenLabs must be used when available, with faster creator-style settings, multiple TTS takes or speech-to-speech, and timestamp captions.
- Codex approval gate: all promoted files stay `review_required`; no live post without explicit chat approval.

## Current Pilot Batch

The previous rendered pilot batch is now treated as failed creative QA. It proved the technical pipeline, but the scripts still sounded generated when read aloud and the score movement did not feel earned enough.

Current gold-standard baseline:

- Review packet: `marketing/gold_standard_short/2026-07-05-real-reviewer-teardown/packet.json`
- Props: `marketing/remotion/props_gold_real_reviewer_teardown.json`
- Render: `marketing/remotion/out/gold-real-reviewer-teardown.mp4`
- Queue file: `marketing/autopost/videos/gold-real-reviewer-teardown.mp4`
- Research brief: `marketing/content_research/resume_video_trends_2026-07-05.md`
- Status: rendered, QC-passed, `review_required`, awaiting Codex approval.

Daily posting remains paused until this exact direction is approved or revised.

## Current Gate Status

- Current preferred render baseline is `ResumeDeskReview` for resume teardown shorts. It should be used before dashboard-style layouts unless the premise explicitly needs a software/search console.
- Short/audio generation supports ElevenLabs multi-take voiceover first, with speech-to-speech preferred when a scratch read is supplied.
- Audio QC supports provider-specific TTS sample rates and checks final rendered audio.
- ElevenLabs synthesis works with the configured voice ID, but the current key cannot list voices because it lacks `voices_read`; keep this documented until the key permission is corrected.
- Visual QC renders representative short frames and scans safe margins for clipped high-attention UI.
- Remotion typecheck passes after mascot/personality changes.
- Current post candidates remain review-only until viewed end to end for pacing, humor, text safe areas, Signal personality, and human voice believability.
- The gold-standard candidate uses `music_omitted_no_sfx`; this is allowed only when the voice is clean and no annoying sound effects are present.
- `ResumeDeskReview` delays score badges until after the score receipt appears. New formats must keep this rule.

Supporting docs:

- `marketing/voice_director.md`
- `marketing/script_human_review_gate.md`
- `marketing/daily_content/2026-07-05-human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor/score_rubric_qa_report.md`

## Lead Creative Benchmark

The shorts must now satisfy these non-technical checks before posting:

- One-second readability: a viewer can identify the resume problem before the first swipe decision.
- Authority premise: the narrator is doing a recruiter/search audit, not reading a SaaS feature list.
- Human read: the script sounds like a person reviewing a resume aloud, not a generated product ad.
- Specific artifact: every short shows a named role, real-looking one-page resume, target job description, weak source bullet, and rewritten proof.
- Consequence: the weak line causes a visible miss such as "not searchable", "too vague", or "wrong language".
- Payoff: the rewrite changes the score and reinforces honest positioning: no fake experience, clearer proof.
- Native metadata: captions must explain the teardown result and score movement, not repeat the title and hook.
