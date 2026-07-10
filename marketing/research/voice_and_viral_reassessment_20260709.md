# Signal Voice and Viral Readiness Reassessment

Date: 2026-07-09

## Decision

- The prior Leah cut is a useful visual control, but its Abby master is rejected. The source take was generated at API speed 1.12 and then time-compressed another 1.216x. That stacked acceleration caused the robotic read.
- Sarah Casual (`uG1JFy6xppqckhHCs2KG`) with `eleven_v3` is the new screen-review baseline. The selected full take lands at 142.4 WPM with `postSpeedFactor: 1.0`.
- Abby remains available for auditions. The current clone lands around 113 WPM with Multilingual v2 and 122 WPM with v3. Do not force it into short-form pace. Re-clone it later from a 2-3 minute continuous recording with natural reviewer energy and varied inflection.
- The screen-only format is close enough to test once the voice is fixed. It is not the viral ceiling. The stronger future lane is a real overhead desk or creator-presence plate using real footage, not generated hands.

## Voice Audition

All samples used the same resume-review passage and no waveform time-compression.

| Voice | Model | Measured pace | Assessment |
|---|---|---:|---|
| Abby clone | Multilingual v2 | 113 WPM | Too slow for a 20-28 second teardown; speed-up damages naturalness. |
| Abby clone | Eleven v3 | 123 WPM | More expressive, still too slow as the default. |
| Sarah Casual | Multilingual v2 | 165 WPM | Naturally quick, but slightly brisk for proof-heavy copy. |
| Sarah Casual | Eleven v3 | 150 WPM audition / 142 WPM selected full take | Best balance of authority, warmth, and creator pacing. |
| Laura Social | Multilingual v2 | 139 WPM | Viable warmer alternative; more personality risk. |
| Brian Relatable | Multilingual v2 | 124 WPM | Trustworthy but too slow for this lane without a shorter script. |

ElevenLabs' current guidance supports this direction: extreme speed values can reduce quality; pacing inherits heavily from the source recording; v3 offers the most expressive delivery; and Instant Voice Clones need training audio with the intended cadence and emotional range.

## What The Reviewed Winners Do

The current research packet contains 22 reviewed shorts across YouTube, Instagram, and TikTok. The strongest relevant examples consistently do five things:

1. Show the category and problem on frame one.
2. Cover one mistake, not a list of loosely related tips.
3. Give the eye a new object, reaction, evidence mark, or edit every 2-3 seconds.
4. Let a human judgment or tactile action carry the entertainment.
5. Keep the product until the end.

Evidence used:

- Gohar Khan, `Resume Tips You Should Use`: physical desk story, real hands, rejection stamp, prop jokes, about 28 seconds.
- My Perfect Resume, `Top 5 Resume Mistakes` parts 1 and 2: one named mistake, acted human reaction, concrete correction; locally observed at roughly 2.1M and 2.8M views.
- cvboost.us recruiter reviews: a detailed resume dominates a real overhead tablet frame; locally observed examples include roughly 1.4M views.
- AdviceWithErin and Sabrina Ramonov: immediate creator presence and brisk delivery, but Signal should not copy vague promises, comment gates, or "unrejectable" claims.

## Current Cut Versus The Bar

### Strong enough to test

- Professional, believable one-page resume.
- Weak sentence is visible from frame one.
- Proof exists elsewhere on the same resume.
- The delete and rewrite occur in the original slot.
- No fake score, fake hand, fake stylus, mascot distraction, or oversized captions.
- Revised opening panel makes the exact weak sentence readable without zooming.

### Still below the viral ceiling

- No real human face, hand, desk, or environmental context.
- The full resume remains visually stable for long stretches; the opening chip progression helps, but it is less tactile than the best examples.
- The video teaches clearly but has limited comedy or story tension.
- It resembles a high-quality screen review more than a native creator clip.

## Production Recommendation

1. Post-test the Sarah v3 screen cut as the control after human review.
2. Do not add more zoom, large captions, or synthetic sound effects.
3. Build the next challenger from real footage: overhead desk, printed resume, real hand, one stamp/marker action, and deterministic close-up text inserts.
4. If real footage is unavailable, keep screen-only rather than returning to generated tablet hands.
5. Measure three-second retention, average percentage viewed, replays, saves, profile visits, and free-score starts. Do not call a format viral-ready from production quality alone.

## Pipeline Changes

- Default screen narrator: Sarah Casual + `eleven_v3`.
- Voice target: 135-155 WPM.
- API speed range: 1.00-1.07.
- Post-generation time compression: disabled by default.
- Natural action language such as "I'd write" now drives the live edit timeline.
- Opening review panel now displays the weak sentence and judgment at readable size, with sequential recruiter-term reveals.
