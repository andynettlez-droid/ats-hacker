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

Recommended settings:

```json
{
  "stability": 0.42,
  "similarity_boost": 0.86,
  "style": 0.35,
  "use_speaker_boost": true
}
```

If ElevenLabs quota is exhausted, stop and report the quota issue. Do not silently switch to a worse voice for a public post.
