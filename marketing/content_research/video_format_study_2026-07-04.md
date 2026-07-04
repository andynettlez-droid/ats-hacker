# Signal Video Format Study - 2026-07-04

## Sources Reviewed

- YouTube Help confirms Shorts are vertical videos up to 3 minutes, discovered through the Shorts feed, search, homepage, channel pages, subscriptions, and notifications. It also notes Shorts views changed on 2025-03-31, while "Engaged views" remains the key comparison metric in Analytics.
- TikTok for Business recommends platform-native text overlays, voiceovers, vertical high-resolution footage, safe-space awareness, frequent creative refreshes, and a hook-body-close structure. It says most ad recall impact is captured in the first six seconds, and that sound is central to the TikTok experience.
- ElevenLabs current API docs document `POST /v1/text-to-speech/:voice_id/with-timestamps`, returning `audio_base64`, `alignment`, and `normalized_alignment` character timing for synchronization.
- Resume-writing references from Harvard career services and Indeed emphasize action verbs, role-specific skills, and quantified accomplishments instead of vague responsibility statements.

## Format To Imitate

Primary format: recruiter-style resume teardown, not founder demo and not abstract AI SaaS ad.

Opening pattern:

1. First frame must show the resume artifact or a recruiter search UI, not a mascot-only scene.
2. Hook must land in the first 0-2 seconds as a direct critique: "This resume looks qualified, but search cannot find it."
3. The first six seconds must show the central conflict: target job language versus resume language.

Body pattern:

1. Show a realistic one-page resume with name/contact, summary, experience, skills, and education/certification sections.
2. Show a realistic job-description card with requirements, responsibilities, and keywords.
3. Circle one weak source bullet.
4. Explain why it is invisible: missing tool, missing metric, missing scope, missing role language.
5. Rewrite the same bullet without adding fake experience.

Close pattern:

1. Reveal the score movement.
2. State a fresh, case-specific summary of the transformation. Avoid repeating stock phrases like "same person, clearer proof."
3. CTA: "Check your free Signal score before you apply."

## Visual Archetypes

Rotate these. Do not ship three shorts in the same visual language.

1. Recruiter Search Console
   - Search field, typed keyword, "0 exact hits" before, "match found" after.
   - Best for technical, sales, and ATS myth videos.

2. Desk Markup Teardown
   - Real resume sheet on desk, marker circles, sticky notes, highlighter sweeps.
   - Best for one-bullet fixes and resume crime scenes.

3. Split-Screen Translation
   - Resume left, job description right, arrows translating evidence.
   - Best for JD translation and score movement.

4. Red-Team Audit
   - Red stamps, checklist, "missing proof" labels.
   - Best for blunt recruiter-reacts hooks.

5. Signal Mascot Assist
   - Mascot points, reacts, and reveals proof, but never replaces the resume as the hero.
   - Best as accent behavior, not primary format.

## Pipeline Rules

- Every short must include a `resumeDocument` object, a `jobDescription` object, and a `formatArchetype`.
- The resume must have at least two experience roles, at least six total bullets, skills, and education/certification.
- The marked `beforeBullet` must appear verbatim inside the resume document.
- The job description must include responsibilities and requirements, not just keyword chips.
- Music must stay restrained under the narration. Sound effects are optional and must be quiet.
- Public review batches should fail QC if they use non-ElevenLabs voice when ElevenLabs is configured or required.
- When ElevenLabs timestamps are available, captions must use word-level timing derived from `normalized_alignment`.

## 2026-07-04 Correction After Review

Problem found: the first working batch was technically valid but creatively repetitive. The videos used similar openings, similar score cadence, and repeated phrasing, so they sounded like a template instead of a creator.

Pipeline changes made:

1. Added creator playbooks so a daily batch rotates formats instead of cloning one structure.
   - `recruiter_roast`: blunt Resume Crime Scene teardown.
   - `search_console`: recruiter keyword/search-box test.
   - `answer_key`: job-description translation / one-bullet fix.
2. Added dynamic short duration from ElevenLabs word timestamps, clamped to 29-52 seconds, so the render follows the voiceover instead of forcing every short into the same 45-second arc.
3. Added creative gate penalties for repeated openings and robotic phrases:
   - `target:`
   - `JD asks for`
   - `real, but buried`
   - `same person, clearer proof`
4. Required each short to carry a `playbookId`, `formatArchetype`, `visualStyle`, `pace`, and fresh `signalLines` so Remotion can vary the visual system.
5. Confirmed the active improved batch:
   - Resume Crime Scene: `This resume sentence is quietly expensive`
   - Recruiter Search Test: `I searched Salesforce and this resume vanished`
   - Job Description Translation: `The job post gave the answer key`

Research implications:

- TikTok's creative guidance prioritizes a strong first 3-6 seconds, platform-native overlays, voiceover, motion, and frequent creative refresh. That supports refusing repeated openings at the gate.
- YouTube Shorts guidance confirms the channel can use vertical clips up to 3 minutes, but for this niche the highest-probability top-of-funnel unit remains a tight 30-55 second teardown.
- Recruiter-led resume content works because it makes the viewer feel a specific error quickly: the resume can look acceptable and still be hard for a recruiter to skim/search.

Next required improvement:

Long-form should not be an elongated Short. Build it as a 6-8 minute episode with chapters: hook, resume scan, recruiter search test, JD translation, three bullet fixes, ethical guardrails, and the free Signal score CTA.
