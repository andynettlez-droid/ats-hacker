# Signal Professional Short Pipeline Upgrade Plan - 2026-07-08

Goal: move from technically valid daily shorts to professional, creator-native resume teardown shorts that can compete on TikTok, YouTube Shorts, Instagram Reels, and LinkedIn.

## Research Summary

The strongest production path is not more AI video. It is a stricter short-form creative system:

- open with the visible problem immediately,
- use a hook/body/close structure,
- make every cut earn retention,
- keep captions supportive instead of dominant,
- test several creative variants,
- tune voice per script,
- review retention and packaging before scaling a format.

Sources:

- TikTok creative best practices recommend captions/text overlays, transitions/graphics, strong CTA, and refreshing with multiple different creatives: https://ads.tiktok.com/help/article/creative-best-practices
- TikTok's own creative blog recommends hook/body/close and notes faster scene changes can draw viewers in early: https://ads.tiktok.com/business/en-US/blog/creative-best-practices-top-performing-ads
- ElevenLabs docs say common TTS settings are around stability 50, similarity 75, style 0, but the right range depends on the performance goal: https://elevenlabs.io/docs/eleven-creative/playground/text-to-speech
- ElevenLabs API docs say lower stability gives broader emotional range while higher stability can become monotone; speed and style should be tuned per voice: https://elevenlabs.io/docs/api-reference/voices/settings/update
- ElevenLabs prompting docs say the model responds to emotional context in text, so scripts should be written for how they sound, not just what they say: https://elevenlabs.io/docs/overview/capabilities/text-to-speech
- CapCut's caption docs are useful as a benchmark for caption styling, batch editing, and visual enhancement, even if our deterministic pipeline renders locally: https://www.capcut.com/tools/add-subtitles-to-video
- HyperFrames is a good fit for no-credit animatics because it renders HTML/CSS/JS into deterministic MP4s: https://hyperframes.heygen.com/
- Google Veo 3.1 can use reference images, but for Signal it should remain a plate/background generator, not the source of readable resume text: https://ai.google.dev/gemini-api/docs/veo

## Recommended Production Architecture

### 1. Creative Brief Gate

Add `creative_brief.json` before script generation:

```json
{
  "format": "screen_teardown",
  "role": "project coordinator",
  "viewerPain": "I keep applying and never hear back",
  "firstFramePromise": "This clean resume hides the timeline proof",
  "oneMistake": "generic project support line",
  "proofAlreadyInResume": ["14 rollout schedules", "Jira dashboards", "two weeks saved"],
  "cta": "Need your resume or cover letter fixed? Use the link below before you apply."
}
```

Fail the run if the first frame promise is not visual, specific, and understandable with sound off.

### 2. Beat-To-Visual Map

Every approved script must produce `beat_visual_map.json`:

```json
[
  {"sec": "0.0-2.0", "voice": "Okay, this is Ethan...", "visual": "resume visible, weak line already in frame"},
  {"sec": "2.0-6.0", "voice": "I'm checking for Jira...", "visual": "search chips appear"},
  {"sec": "6.0-10.0", "voice": "His resume says...", "visual": "weak line highlighted"},
  {"sec": "10.0-15.0", "voice": "That sounds fine...", "visual": "red mark and short critique label"},
  {"sec": "15.0-20.0", "voice": "Lower down...", "visual": "proof box appears"},
  {"sec": "20.0-25.0", "voice": "Replace it with...", "visual": "old line deletes, rewrite types in"},
  {"sec": "25.0-29.0", "voice": "Need yours fixed...", "visual": "receipt plus CTA"}
]
```

Fail any beat where narration has no visible action.

### 3. Voice Lab

Before full voice:

- render three 8-10 second Abby samples,
- settings matrix:
  - `natural`: stability 0.42, similarity 0.78, style 0.20, speed 1.03
  - `creator`: stability 0.34, similarity 0.82, style 0.35, speed 1.06
  - `steady`: stability 0.52, similarity 0.76, style 0.12, speed 1.02
- include the hardest pronunciation terms in the sample: role, tools, `résumé`, CTA.

Create `voice_quality_qa.json` with:

- pronunciation pass/fail,
- pacing pass/fail,
- human read pass/fail,
- selected variant.

Do not full-render if voice fails.

### 4. No-Credit Animatic Gate

Use HyperFrames or the current HTML/ffmpeg renderer to create a draft animatic before paid/generated assets:

- silent version,
- captions version,
- contact sheet,
- first-frame still.

Review order:

1. first frame with sound off,
2. contact sheet for story flow,
3. silent animatic,
4. voice test,
5. final render.

### 5. Professional Caption System

Replace large generic caption slabs with creator-style micro-captions:

- 3-6 words per caption beat,
- only one caption idea on screen at once,
- no captions covering the resume line being edited,
- use captions as emphasis: "too vague", "proof is lower", "now it matches".

TikTok recommends text overlays in the 5-10 words-per-second range. Signal should stay near the low end so resume text remains the star.

### 6. Screen Teardown Visual Polish

Upgrade the current screen-only look without sacrificing readability:

- add subtle zooms tied to beats,
- add real editor affordances: insertion caret, brief selected-text state, delete flash, typed rewrite,
- add a small search bar or recruiter search panel only when it clarifies the critique,
- add a faint paper/screen texture but never blur resume text,
- use one warm neutral background and one accent color per run to vary style.

Do not add fake cursor noise. If a pointer appears, it must move like a human and point only at the active edit.

### 7. Packaging Gate

After approval, generate:

- `cover_frame_9x16.png`,
- `cover_frame_1x1.png`,
- title text variant A/B,
- platform caption variants,
- first comment / pinned comment CTA.

Use Canva for polished cover frames and social variants when available.

### 8. Analytics Loop

Every posted short should store:

- first 2-second hook category,
- format,
- role,
- script length,
- voice variant,
- caption density,
- cover frame text,
- watch/retention metrics when available,
- click-through or UTM traffic when available.

The weekly review should not ask "did it post?" It should ask:

- did the first frame stop the scroll?
- did retention survive the first 6 seconds?
- did the CTA create site visits?
- which role/style/hook pair performed best?

## Professional Quality Bar

A short is production-ready only when all are true:

- It feels like a human reviewer is doing one specific edit.
- The first frame makes the problem obvious with sound off.
- The script sounds natural when read aloud.
- The weak line is believable and professional, not cartoonishly bad.
- The proof exists lower in the resume before the rewrite.
- The edit visibly changes the resume.
- The CTA is short and not SaaS-y.
- The voice has no pronunciation or pacing issue.
- Captions support the edit instead of competing with the resume.
- The cover frame would make sense as a standalone post thumbnail.

## Highest-Impact Next Build Items

1. Add `beat_visual_map.json` generation and validation.
2. Add `voice_quality_qa.json` with three Abby voice test variants.
3. Add a no-credit animatic/contact-sheet command.
4. Add caption density checks and resume-occlusion checks.
5. Add cover-frame export after Codex approval.
6. Add an analytics table for hook/style/voice/role performance.

## Tool Decision

Default production stack:

- research + script: Codex + swipe file,
- visual: deterministic screen renderer / HyperFrames animatic,
- voice: ElevenLabs Abby with variant testing,
- assembly: ffmpeg,
- cover/social variants: Canva,
- physical plate experiments: Veo/Flow only for blank scenes,
- avatar/host experiments: HeyGen only for long-form or occasional authority intros.

Do not make Veo, HeyGen, or generated imagery the core of the resume teardown unless they improve authenticity and readability.
