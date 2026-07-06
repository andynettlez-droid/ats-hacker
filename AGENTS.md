# Signal Growth Engine Agent Guide

This repo now uses the Signal Growth Engine pipeline for marketing videos. The old `marketing_agent/video_pipeline.py` path is retired because it produced brittle demo timing, repeated AI-style scripts, and inconsistent voice.

## Primary Workflow

Run video work in this order:

1. Research current resume/job-search short-form patterns.
2. Write one human reviewer script from the research and `skills/hook_playbook.md`.
3. Build a shot sheet from `skills/veo_prompt_template.md`.
4. Generate video clips with Veo/Gemini, using Abby and Signal/orb reference images where available.
5. Generate voiceover with ElevenLabs Abby voice from `skills/voiceover.md`.
6. Assemble with `skills/assemble.ps1` or `skills/assemble.sh`.
7. QA with `marketing_agent/signal_growth_pipeline.py qa`.
8. Export a reviewable file and stop for Codex chat approval before posting.

Do not publish from an automated run. The final publish gate remains explicit Codex approval for the exact rendered file.

## Current Abby Voice

Use this ElevenLabs voice unless Andrew rotates it:

```text
ELEVENLABS_ABBY_VOICE_ID=lkFHOvhI41u53xDdGZoZ
```

Keep keys in `marketing_agent/.env` or your local shell environment. Never paste API keys into chat, docs, commits, or generated artifacts.

## Commands

Confirm the Abby voice ID if the ElevenLabs key allows voice listing:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py resolve-abby
```

Create a reusable production folder:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py init-run --topic "resume teardown"
```

Generate Abby narration with timestamps:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py voice --text-file marketing/growth_runs/latest/vo1.txt --out marketing/growth_runs/latest/vo1.mp3
```

Generate a Veo clip when a shot needs cinematic motion:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py veo --text-file marketing/growth_runs/latest/shot01.txt --out marketing/growth_runs/latest/shot01.mp4
```

Assemble the ad with sync-safe timing:

```powershell
powershell -ExecutionPolicy Bypass -File skills/assemble.ps1 -WorkDir C:\Users\andyn\Downloads -Out signal_ad_final.mp4
```

QA the final render:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py qa --video C:\Users\andyn\Downloads\signal_ad_final.mp4
```

Print the Codex review packet for the exact rendered file:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py review --run-id RUN_ID
```

Only after Andrew approves the exact video in Codex chat:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py approve --run-id RUN_ID --phrase "APPROVE POST RUN_ID"
```

## Creative Guardrails

- The resume or job description is the visual hero.
- Signal mascot is a fun guide, not the presenter.
- Abby can appear as the human/recruiter voice, but do not make the clip feel like a founder ad.
- No fake experience.
- No outcome guarantees.
- No "ATS auto-rejected you" claims.
- Score jumps need a visible receipt before the reveal.
- The CTA is fast: "Run the free Signal score before you apply."
