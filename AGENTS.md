# Signal Growth Engine Agent Guide

Codex should use this repo as the production home for the Signal content pipeline:

`reviewed research -> five-script council -> proof-locked resume -> Abby voice lab -> controlled browser edit -> frozen QA packet -> Codex approval`

The old `marketing_agent/video_pipeline.py` path is retired. Do not revive it. Do not build new public shorts through the older failed daily batch unless Andrew explicitly asks for that exact legacy asset. Remotion can remain in the repo for historical assets, but the active ad/short pipeline is the playbook in `/skills` plus `marketing_agent/signal_growth_pipeline.py`.

Current production default: use the controlled screen-only recruiter review unless Andrew explicitly selects a physical tablet, paper, or Veo plate experiment. `controlled_resume_capture.mjs` owns every readable pixel, `controlled_screen_sync.py` follows the selected Abby timestamps, and ffmpeg performs the final mux. HyperFrames is for no-credit experiments and overlays, not the current gold screen renderer.

Hard stop for physical-scene shorts: do not create public marketing videos with Remotion, full Pillow video renderers, custom Python video renderers, canvas mocks, or pasted fake hand/stylus layers. If a Veo/Gemini physical plate is required and it is not configured or fails, stop and report the blocker. The acceptable non-Veo visuals are the current stable screen-only reviewer format, real user-provided/owned footage, screen recordings, licensed assets explicitly selected for the video, and deterministic PNG overlays for readable resume/JD text composited over approved footage during editing.

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

1. **RESEARCH**: Build a current packet with at least 20 reviewed shorts, 12 YouTube sources, 2 browser-observed TikToks, 2 browser-observed Instagram Reels, valid transcripts, bounded contact sheets, and three cross-platform angles. Never lower a threshold to make a packet pass.
2. **SCRIPT**: Materialize the packet into the run, write five genuinely distinct 55-70 word human-reviewer scripts, and let `creative_council.py` select the exact passing option. Creative approval is internal; Andrew only approves the frozen final video.
3. **VIDEO**: Use `skills/veo_prompt_template.md` to generate each 9:16 clip through Veo/Gemini. Download clips into the run folder or `/assets`. Do not ask Veo to create readable resume/JD text.
   - For the tablet/stylus resume-review format, use the blended Signal style: `tablet_resume_review_reference_clean.jpg` for composition, `signal_tablet_teardown_premium_tech_audit.png` for mood, and `signal_tablet_teardown_bright_score_receipt.png` for the score receipt. Attach all three with the Veo reference-image option and the "Signal Tablet Teardown Style" prompt. Do not copy the source clip's exact visual language, captions, UI, or red-number treatment. Do not spend credits on this format without the reference images attached.
   - If the full reference-image path filters or fails, use `veo-3.1-lite-generate-preview` with simple silent b-roll prompts. Keep the prompt focused on a stable blank/soft tablet or screen area, and let deterministic overlays carry all readable content. Do not keep burning credits on elaborate prompts once a simple plate works.
4. **OVERLAYS**: Generate deterministic readable resume/JD overlays with `py -3 marketing_agent/signal_growth_pipeline.py overlays --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID`. These overlays carry the resume text, red markup, keyword chips, and rewritten bullet. Resume overlays must look like real one-page resumes: name/title line, summary, skills, multiple experience bullets, dates, projects, certifications, and one clearly weak bullet being repaired. When the concept is a live edit, use `py -3 marketing_agent/signal_growth_pipeline.py live-edit-overlays --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID` so marks, strike-throughs, and replacement bullets appear over time rather than popping in.
   - Daily runs should set `$env:SIGNAL_OVERLAY_FPS='12'` before `live-edit-overlays`. Final output remains 30fps, but the overlay frame stream is lighter and much faster to produce.
5. **HANDS / HUMAN ACTION**: Hands must come from the base Veo shot or owned/live footage. Do not composite separate AI hand plates into a production review cut by default; they drift from the person, look pasted on, and fail the creative bar. If a future cut truly needs hands over the readable resume layer, use a properly roto-scoped owned clip or explicitly run the assembler with hand plates enabled after visual approval of the plate.
6. **VOICE**: Use the multi-take ElevenLabs voice lab through `/with-timestamps`. Sarah Casual with `eleven_v3` is the current screen-review baseline; Abby remains an audition option until the clone is retrained. Known pronunciation risks are rewritten for voice only. The selected take is loudness-normalized but not waveform-speeded to hit a pacing target; shorten the script instead.
7. **EDIT**: For screen teardowns, run `build-screen-teardown`; do not revive `screen_teardown_renderer.mjs`. The controlled renderer visibly selects, deletes, and rewrites the same resume line. Captions stay subordinate to the resume.
   - Optional Adobe finishing pass: use `marketing_agent/adobe_finish_bridge.py` only after final base QA. It is fail-closed, hash-binds the source and beat map, requires a reviewed `.aep`, renders video-only, and restores the source AAC packets. The older JSX/payload scripts are not approved for controlled-screen production.
8. **QA**: Run ffprobe/QA checks for 1080x1920, H.264/AAC, 30fps, A/V duration match, readable captions, readable resume overlays, no unsupported claims, no unwanted source watermarks, and no wrong visible URL/logo.
   - Final `qa --run-id RUN_ID` is locked behind required quality gates. Screen-only shorts require `creative_gate`, `script_qa`, `screen_visual_qa`, and `voice_qa`. Physical/tablet/paper shorts require `creative_gate`, `script_qa`, `creative_qa`, `plate_qa`, `surface_fit_qa`, and `voice_qa`.
   - If any gate is missing or failed, the video cannot move to `AWAITING_CODEX_APPROVAL`.
9. **REVIEW**: Run `final-review` with the beat map and evidence ledger. Export the exact hash-bound file and stop in Codex chat. Posting requires `APPROVE POST RUN_ID` for that unchanged file.

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

Only after a hand/roto layer has been separately approved, generate or provide an explicit hand plate:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py veo --text-file marketing/growth_runs/RUN_ID/handplate01.txt --out marketing/growth_runs/RUN_ID/handplate01.mp4 --run-id RUN_ID
```

Generate readable resume overlays:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py overlays --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID
```

Generate animated live-edit overlays:

```powershell
$env:SIGNAL_OVERLAY_FPS='12'
py -3 marketing_agent/signal_growth_pipeline.py live-edit-overlays --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID
```

Run voice/Veo work for several runs concurrently:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py batch-process --runs RUN_ID_1 RUN_ID_2 RUN_ID_3 --stage all --max-workers 3
```

Prepare an optional After Effects finishing handoff after the base video passes:

```powershell
py -3 marketing_agent/adobe_finish_bridge.py readiness --source marketing/growth_runs/RUN_ID/final.mp4 --beat-map marketing/growth_runs/RUN_ID/beat_visual_map.json
py -3 marketing_agent/adobe_finish_bridge.py prepare --source marketing/growth_runs/RUN_ID/final.mp4 --beat-map marketing/growth_runs/RUN_ID/beat_visual_map.json --manifest marketing/growth_runs/RUN_ID/adobe_finish_manifest.json --adobe-video-out marketing/growth_runs/RUN_ID/adobe_finish_video_only.mov --final-out marketing/growth_runs/RUN_ID/final_adobe.mp4 --run-id RUN_ID
```

Run the required quality gates before final QA:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py research-swipe --urls-file marketing/research/viral_resume_videos_20260707/seed_urls.txt --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --min-sources 20
py -3 marketing_agent/signal_growth_pipeline.py script-qa --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID
py -3 marketing_agent/signal_growth_pipeline.py screen-visual-qa --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --visual-reviewed
py -3 marketing_agent/signal_growth_pipeline.py creative-qa --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --format desk_teardown
py -3 marketing_agent/signal_growth_pipeline.py plate-qa --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --visual-reviewed
py -3 marketing_agent/signal_growth_pipeline.py surface-fit-qa --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --visual-reviewed
py -3 marketing_agent/signal_growth_pipeline.py voice-qa --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --human-reviewed --pronunciation-ok --natural-read --pacing-ok --cta-ok
```

For a screen-only teardown, use `screen-visual-qa` and skip `creative-qa`, `plate-qa`, and `surface-fit-qa`. For physical tablet, paper, monitor, or Veo/Flow plate tests, run `creative-qa`, `plate-qa`, and `surface-fit-qa`; `screen-visual-qa` is not enough.

Assemble a review cut:

```powershell
powershell -ExecutionPolicy Bypass -File skills/assemble.ps1 -WorkDir C:\Users\andyn\Downloads -Out signal_ad_final.mp4
```

QA a final render:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py qa --video marketing/growth_runs/RUN_ID/final.mp4 --run-id RUN_ID
```

Do not use standalone QA for production review cuts. Standalone QA only checks codecs and dimensions; `qa --run-id` enforces the creative quality gates.

Print a review packet:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py review --run-id RUN_ID
```

## Creative Rules

- The resume or job description is the visual hero.
- Veo creates motion and human context; deterministic overlays create readable resume/JD text.
- Never rely on model-generated document text for a teardown. If a viewer needs to read it, create it in the edit layer.
- Never use generic three-line resumes for teardown videos. The resume must look detailed enough that a real job seeker would recognize it as a resume.
- For edit/fix videos, the weak bullet should visibly change on screen: circle or underline, strike the vague wording, type or reveal the replacement, then show the cleaned final state.
- Do not add separate AI-generated hands to production review cuts. The human/hands layer should be part of the base Veo scene, owned footage, or a deliberately approved roto layer. Background hands underneath the readable resume do not count as an edit, so the edit itself must be visible through the resume overlay animation.
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

## Quality Gate Rules

- **research-swipe** must collect current examples, metadata, captions/hooks, and a local summary before scripts are accepted.
- **script-qa** rejects missing candidate/role, missing weak line, missing proof, overlong scripts, and banned AI/product language.
- **creative-qa** rejects videos where the score is not earned by a visible receipt or where the resume edit does not happen on screen.
- **plate-qa** extracts review frames and requires explicit visual review for fake text, watermark, hand/person consistency, and stable document area.
- **screen-visual-qa** rejects screen-only teardowns when the resume is not realistic/readable, the edit is not visible, the score receipt is unearned, captions dominate, or mascot/product UI distracts from the human review.
- **surface-fit-qa** rejects physical tablet/paper/monitor tests when deterministic resume text is not pinned inside the device/page, text is blurry, or the plate reduces clarity below the screen-only baseline.
- **voice-qa** requires a reviewed Abby test before the full build. It blocks bad "resume" pronunciation, robotic/corporate reads, slow pacing, and weak CTA delivery.
- **qa --run-id** refuses approval if any of those reports are missing or failed.
