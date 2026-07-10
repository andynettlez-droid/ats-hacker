# ElevenLabs Voiceover Skill

## Voice

Use Abby as the consistent brand reviewer voice:

```env
ELEVENLABS_ABBY_VOICE_ID=lkFHOvhI41u53xDdGZoZ
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

Fallback variable:

```env
ELEVENLABS_VOICE_ID=lkFHOvhI41u53xDdGZoZ
```

## Endpoint

Use the timestamp endpoint so captions and edit beats can sync to the actual read:

```text
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps
```

Store:

- `*.mp3` audio from `audio_base64`.
- `*.alignment.json` with normalized word timing plus raw alignment.

## Voice Direction

- Human recruiter read.
- Faster than corporate narration.
- Slightly amused, direct, useful.
- Short pauses after punchlines.
- No monotone AI explainer cadence.
- No over-polished trailer voice.
- If it sounds robotic, rewrite the script out loud before regenerating.
- The voice lab converts the word `resume` to the accented pronunciation form in API text while keeping on-screen copy unchanged. Never post a clip with the known `resum` mispronunciation.

Production method:

- Generate three deterministic takes with the current `TAKE_PRESETS` in `voice_lab.py`.
- Target 150-160 WPM for the human reviewer lane; reject anything below 140 or above 190.
- Select on pacing and pause structure, then apply at most a 1.22x transparent `atempo` correction.
- Retimestamp every aligned word by the exact same factor.
- Trim only the dead tail and normalize to -16 LUFS / -1.5 dBTP.

The current presets vary stability, style, similarity, and API speed up to 1.20. Do not reduce this to one corporate-sounding take.

Example API settings for one candidate take:

```json
{
  "stability": 0.4,
  "similarity_boost": 0.84,
  "style": 0.28,
  "speed": 1.2,
  "use_speaker_boost": true
}
```

If ElevenLabs quota is exhausted, stop and report the quota issue. Do not silently switch to a worse voice for a public post.
