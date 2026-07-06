# Signal Growth Engine Agent Guide

Codex should use this repo as the production home for the Signal content pipeline:

`research -> script -> Veo video -> readable overlays -> optional Veo hand plates -> ElevenLabs Abby voice -> ffmpeg edit -> QA -> Codex review`

The old `marketing_agent/video_pipeline.py` path is retired. Do not revive it. Do not build new public shorts through the older failed daily batch unless Andrew explicitly asks for that exact legacy asset. Remotion can remain in the repo for historical assets, but the active ad/short pipeline is the playbook in `/skills` plus `marketing_agent/signal_growth_pipeline.py`.

Hard stop: do not create public marketing videos with Remotion, full Pillow video renderers, custom Python video renderers, canvas mocks, or any other local visual fallback. If Veo/Gemini is not configured or fails, stop and report the blocker. The acceptable non-Veo visuals are real user-provided/owned footage, screen recordings, licensed assets explicitly selected for the video, and deterministic PNG overlays for readable resume/JD text composited over Veo footage during editing.

## Required Local Inputs

- Google AI / Gemini / Veo API key in a local `.env`.
- ElevenLabs API key in a local `.env`.
- `ffmpeg` and `ffprobe` available on the machine.
- Abby voice ID:

```text
ELEVENLABS_ABBY_VOICE_ID=lkFHOvhI41u53xDdGZoZ
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

Never paste keys into chat, docs, commits, captions, or generated artifacts.

## Active Workflow

1. **RESEARCH**: Search current short-form trends for the topic. Summarize 3 winning angles with what to copy and what to avoid.
2. **SCRIPT**: Use `skills/hook_playbook.md` and `skills/brand.md` to write a 30s human reviewer script with hook, beats, CTA, and captions.
3. **VIDEO**: Use `skills/veo_prompt_template.md` to generate each 9:16 clip through Veo/Gemini. Download clips into the run folder or `/assets`. Do not ask Veo to create readable resume/JD text.
4. **OVERLAYS**: Generate deterministic readable resume/JD overlays with `py -3 marketing_agent/signal_growth_pipeline.py overlays --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID`. These overlays carry the resume text, red markup, keyword chips, and rewritten bullet. Resume overlays must look like real one-page resumes: name/title line, summary, skills, multiple experience bullets, dates, projects, certifications, and one clearly weak bullet being repaired. When the concept is a live edit, use `py -3 marketing_agent/signal_growth_pipeline.py live-edit-overlays --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID` so marks, strike-throughs, and replacement bullets appear over time rather than popping in.
5. **REAL HAND PLATES**: If the viewer needs to see hands or a stylus performing the edit, generate matching Veo green-screen hand plates named `handplate01.mp4`, `handplate02.mp4`, etc. The assembler chroma-keys those real generated hands above the readable resume overlay. Do not draw, animate, or locally fake extra hands.
6. **VOICE**: Use `skills/voiceover.md` to generate Abby narration through ElevenLabs `/with-timestamps`. Save the MP3 and alignment JSON.
7. **EDIT**: Run `skills/assemble.sh` or `skills/assemble.ps1`. Segment durations must follow the measured audio/video durations. Captions are generated from those real timings but are opt-in for this format; default review cuts should rely on the readable overlay and small in-design captions only.
8. **QA**: Run ffprobe/QA checks for 1080x1920, H.264/AAC, 30fps, A/V duration match, readable captions, readable resume overlays, no unsupported claims, no unwanted source watermarks, and no wrong visible URL/logo.
9. **REVIEW**: Export a reviewable file and stop in Codex chat before posting unless Andrew explicitly says to post that exact file.

## Commands

Create a queued run:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py init-run --topic "resume teardown"
```

Create multiple queued runs:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py batch-init --topics "network engineer teardown" "resume score myth" "job description answer key"
```

Generate Abby voice:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py voice --text-file marketing/growth_runs/RUN_ID/vo_hook.txt --out marketing/growth_runs/RUN_ID/vo_hook.mp3 --run-id RUN_ID
```

Generate a Veo clip:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py veo --text-file marketing/growth_runs/RUN_ID/shot01.txt --out marketing/growth_runs/RUN_ID/shot01.mp4 --run-id RUN_ID
```

Generate a Veo real-hand plate for a visible edit:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py veo --text-file marketing/growth_runs/RUN_ID/handplate01.txt --out marketing/growth_runs/RUN_ID/handplate01.mp4 --run-id RUN_ID
```

Generate readable resume overlays:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py overlays --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID
```

Generate animated live-edit overlays:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py live-edit-overlays --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID
```

Run voice/Veo work for several runs concurrently:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py batch-process --runs RUN_ID_1 RUN_ID_2 RUN_ID_3 --stage all --max-workers 3
```

Assemble a review cut:

```powershell
powershell -ExecutionPolicy Bypass -File skills/assemble.ps1 -WorkDir C:\Users\andyn\Downloads -Out signal_ad_final.mp4
```

QA a final render:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py qa --video C:\Users\andyn\Downloads\signal_ad_final.mp4 --write
```

Print a review packet:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py review --run-id RUN_ID
```

## Creative Rules

- The resume or job description is the visual hero.
- Veo creates motion and human context; deterministic overlays create readable resume/JD text.
- Never rely on model-generated document text for a teardown. If a viewer needs to read it, create it in the edit layer.
- Never use generic three-line resumes for teardown videos. The resume must look detailed enough that a real job seeker would recognize it as a resume.
- For edit/fix videos, the weak bullet should visibly change on screen: circle or underline, strike the vague wording, type or reveal the replacement, then show the cleaned final state. If hands/stylus are shown, they must come from Veo hand-plate footage or owned live footage composited above the readable resume layer. Locally drawn or synthetic overlay hands are banned.
- Background hands underneath the readable resume do not count as an edit. Either use proper hand plates above the resume or make the video a clean screen/demo edit with no visible hands.
- Burned-in subtitles are optional and should stay off when they compete with the resume artifact.
- Signal mascot/orb is optional. Do not force it into resume-review content.
- Most short-form videos should make the resume/JD mistake the entertainment. Signal can be the fix in the caption, spoken CTA, and link in bio.
- Abby can be the voice, but the clip should not feel like a polished founder ad.
- No fake experience.
- No outcome guarantees.
- No "ATS auto-rejected you" claims.
- Score jumps need visible receipts before the reveal.
- CTA: "Need yours fixed? Link in bio." or "Run the free Signal score before you apply."
- Do not put an actual website URL on-screen unless Andrew explicitly asks for it. Use the URL in metadata and social bio.
- If a generated source clip has a visible provider watermark, do not mask it. Regenerate cleanly, use a licensed export, or replace it with owned/captured assets.
