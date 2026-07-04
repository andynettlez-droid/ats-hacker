# Signal Shorts Creative System

Status: active direction for daily short-form production.

## Problem We Are Fixing

The first studio shorts proved the pipeline can render and post, but the creative looked too repetitive. Daily content must not feel like the same SaaS ad with swapped captions.

## Daily Format Rotation

Each day should produce three distinct short concepts:

- Red-Marker Resume Roast: paper/resume-first, red markup, blunt recruiter energy.
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

## Narration Rules

- Target runtime is 18-32 seconds for Shorts. Anything longer fails unless explicitly marked long-form.
- Open with a joke or painful job-search truth in the first two seconds.
- Punch at vague resume language and broken job-search friction, not at job seekers.
- Build a complete story spine: conflict, target evidence, weak source line, consequence, fix, payoff.
- Make one useful teaching point before the CTA, but make it feel discovered through the teardown rather than explained as a tip.
- End with the free Signal score, not an aggressive paid pitch.
- Avoid template narration. Banned recurring reads include "JD asks for," "real, but buried," and "same person, clearer proof."
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

Before script generation, update or review `marketing/viral_swipe_file.md`. The script generator should copy niche-specific patterns only: recruiter reacts, resume teardown, search test, job-description translation, and resume roast. Generic social-media best practices are not enough to pass the creative gate.

## Required Gates

- Creative director gate: hook, visible artifact, weak bullet, visible consequence, honest rewrite, score receipt, CTA.
- Visual diversity gate: the first three daily shorts must use different format archetypes and palettes.
- Duration gate: 18-32 seconds for short-form outputs.
- Score-rationale gate: no score jump without visible factors on screen.
- Voice-quality gate: ElevenLabs must be used when available, with faster creator-style settings and timestamp captions.
- Codex approval gate: all promoted files stay `review_required`; no live post without explicit chat approval.

## Current Pilot Batch

Packet: `marketing/daily_content/2026-07-04-viral-recruiter-teardown-score-receipt-clips`

Pilots:

- `This resume sentence is quietly expensive`: red-marker resume roast with a score receipt before the 34->92 reveal.
- `I searched Salesforce and this resume vanished`: recruiter search console with visible keyword/tool/search logic.
- `This resume failed an open-book test`: job-description answer-key/highlighter format with keyword and outcome receipt.

Rendered review pilot:

- `marketing/remotion/out/daily-this-resume-sentence-is-quietly-expensive.mp4`
- `marketing/remotion/out/daily-i-searched-salesforce-and-this-resume-vanished.mp4`
- `marketing/remotion/out/daily-this-resume-failed-an-open-book-test.mp4`

## Current Gate Status

- Current refreshed packet scores 100/100 and all three short concepts pass the stricter creator gate.
- Short/audio generation supports ElevenLabs first, then OpenAI TTS fallback.
- Audio QC supports provider-specific TTS sample rates and checks final rendered audio.
- ElevenLabs synthesis works with the configured voice ID, but the current key cannot list voices because it lacks `voices_read`; keep this documented until the key permission is corrected.
- Visual QC renders representative short frames and scans safe margins for clipped high-attention UI.
- Remotion typecheck passes after mascot/personality changes.
- Current post candidates remain review-only until viewed end to end for pacing, humor, text safe areas, and Signal personality.

## Lead Creative Benchmark

The shorts must now satisfy these non-technical checks before posting:

- One-second readability: a viewer can identify the resume problem before the first swipe decision.
- Authority premise: the narrator is doing a recruiter/search audit, not reading a SaaS feature list.
- Specific artifact: every short shows a named role, real-looking one-page resume, target job description, weak source bullet, and rewritten proof.
- Consequence: the weak line causes a visible miss such as "not searchable", "too vague", or "wrong language".
- Payoff: the rewrite changes the score and reinforces honest positioning: no fake experience, clearer proof.
- Native metadata: captions must explain the teardown result and score movement, not repeat the title and hook.
