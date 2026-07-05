# Signal Voice Director

Signal shorts should sound like a real reviewer reading a resume live, not like a narrator explaining a product.

## Default Performance

- Voice: slightly amused recruiter or career coach.
- Pace: fast conversational, roughly 150-185 words per minute.
- Shape: read the weak line, react, compare it to the job, explain the score, rewrite, then reveal why the score moves.
- Pauses: short pause after the weak line and before the score reason.
- Avoid: corporate polish, trailer voice, monotone cadence, exaggerated sales pitch, and generic ATS fear language.

## Preferred Audio Path

Use ElevenLabs Speech-to-Speech when a scratch read exists. A rough human read is better than clean raw TTS because it carries timing, hesitation, emphasis, and natural sentence stress.

Scratch-read requirements:

- Record the final script as if reading the resume on camera.
- Keep small human imperfections if they help timing.
- Do not add music or room noise.
- Place the source path in `voiceDirector.scratchReadSrc`.

## Fallback Audio Path

When no scratch read exists, use ElevenLabs TTS multi-take mode.

- Generate 3-5 takes with varied stability/style settings.
- Prefer the take closest to conversational pacing.
- Preserve ElevenLabs timestamp alignment for captions.
- Reject takes that are too slow, too polished, or missing word-level alignment when another take has it.

## Pass/Fail

Passes:

- "Okay, this is the line I would circle first..."
- "I search React. Nothing useful."
- "That could be real work, but it makes me guess."

Fails:

- "This resume lacks role-specific keywords."
- "Recruiters search for role language."
- "Same person. Better signal."
- "The ATS will reject this."

The viewer should believe a person is reviewing a resume, not that software is narrating itself.
