# HeyGen Signal Mascot

Created: 2026-06-26

## Current Mascot Look

- HeyGen display name: `Azure Orbit Assistant`
- Intended brand name: `Signal Atomic Mascot`
- Avatar look ID: `0d5e54203dad4b9ea61abb618676d9bf`
- Avatar group ID: `1ad238ece88243eda6e3696ec4761b1c`
- Avatar type: `photo_avatar`
- Status: `completed`
- Supported engine reported by create call: `avatar_iv`

The local runtime config in `marketing_agent/.env` should contain:

```env
HEYGEN_AVATAR_ID=0d5e54203dad4b9ea61abb618676d9bf
```

## Source Reference

The avatar was created from the Signal storyboard reference asset:

```text
marketing/remotion/public/assets/signal_atomic_storyboard_reference.png
```

The creation prompt requested a fully synthetic non-human electric-blue atomic AI assistant mascot with a glowing spherical core, friendly simple face, cyan eyes, orbiting electron rings, and premium dark SaaS styling.

## Notes

- Do not commit or print `HEYGEN_API_KEY`.
- The avatar ID is the value passed as `avatar_id` when creating HeyGen videos.
- If a future creation run produces a better mascot, update `HEYGEN_AVATAR_ID` in `.env` and this note.
