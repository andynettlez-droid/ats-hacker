# ElevenLabs Voiceover Skill

## Voice

Use Abby as the brand reviewer voice:

```env
ELEVENLABS_ABBY_VOICE_ID=lkFHOvhI41u53xDdGZoZ
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

Fallback variable:

```env
ELEVENLABS_VOICE_ID=lkFHOvhI41u53xDdGZoZ
```

## Endpoint

Use the timestamp endpoint so captions and edit beats can be synchronized:

```text
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps
```

Store:

- `*.mp3` audio from `audio_base64`.
- `*.alignment.json` containing the raw character alignment.

## Voice Direction

- Fast creator read.
- Human, amused, direct.
- Short pause after the joke or blunt teardown.
- No corporate trailer voice.
- No monotone AI explainer cadence.
- Keep sentences short enough to read naturally.

Recommended settings:

```json
{
  "stability": 0.42,
  "similarity_boost": 0.86,
  "style": 0.35,
  "use_speaker_boost": true
}
```

If the read sounds robotic, do not keep rendering videos. Rewrite the script aloud first, then regenerate the voice.
