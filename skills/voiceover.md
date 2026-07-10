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

- Use Sarah Casual (`uG1JFy6xppqckhHCs2KG`) with `eleven_v3` as the current screen-review baseline. Her tested native delivery lands near 142-150 WPM without waveform speed-up.
- Keep Abby available for comparison, but do not make the current clone the default. Its tested native cadence is roughly 113-123 WPM and forcing it faster made the read sound robotic.
- Generate three takes with the current `TAKE_PRESETS` in `voice_lab.py`.
- Target 135-155 WPM for the human reviewer lane; reject anything below 120 or above 175.
- Select on pacing and pause structure. Do not time-compress the waveform to hit a numeric WPM target; shorten the script instead.
- Trim only the dead tail and normalize to -16 LUFS / -1.5 dBTP.

The current presets vary stability, style, similarity, and API speed only from 1.00 to 1.07. Do not reduce this to one corporate-sounding take or restore the old 1.20 API speed plus `atempo` stack.

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
