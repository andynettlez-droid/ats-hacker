# Signal Video Pipeline Quality Gates

This document is the guardrail against returning to the old low-quality pipeline.

## Non-Negotiable Principle

Veo/Flow creates camera realism. Signal creates readable content.

Never rely on generated video text for resumes, job descriptions, edits, score receipts, CTAs, or captions. Those must be deterministic overlays, screen recordings, or owned assets.

## Current Production Spine

Until a real-device composite clearly beats it, the production default is the screen-only deterministic resume teardown:

- readable full resume fills the frame,
- weak line appears immediately,
- search terms and proof appear before the rewrite,
- rewrite happens in the same resume slot,
- score/receipt appears only after visible evidence,
- Abby voice is used only after a short voice test passes.

Physical tablet/paper/Veo plates are experimental. They must not replace the screen-only spine unless they beat it on readability, authenticity, and edit clarity.

### Active Gold Contract - 2026-07-09

The production path is now:

1. `youtube_research_evidence.py` plus reviewed browser evidence.
2. `assemble_daily_research_input.py` and `daily_research.py`; every hard gate must pass.
3. `materialize_run_research.py` writes the traceable swipe file and exemplar matrix.
4. `creative_council.py` evaluates exactly five scripts and selects one exact option.
5. `voice_lab.py` generates and scores Abby takes, normalizes loudness, and preserves corrected timestamps.
6. `controlled_screen_sync.py` derives visual beats from spoken cues and writes the evidence ledger.
7. `controlled_resume_capture.mjs` renders the readable same-slot edit.
8. `final_review_packet.py` freezes hashes, literal opening frames, beat timing, evidence agreement, and audio QA.
9. Only the unchanged final video may receive `APPROVE POST RUN_ID`.

Do not ask for manual approval at research, script, voice, or storyboard stages. Failed intermediate gates trigger internal revision. Codex approval is reserved for the exact final video.

## Current Experimental Lane: Physical Desk Story

Added after reviewing the Gohar Khan resume tips Short and adjacent high-view resume examples on 2026-07-09.

The next experimental style should copy the viral mechanic, not the exact content:

- use a real or clean generated desk plate,
- make the resume a tactile paper prop or clean editor surface,
- show one obvious mistake in the first two seconds,
- use large simple labels only for the active joke or critique,
- create a visible action every 2-3 seconds,
- keep the product out until the CTA.

This is a story/prop lane, not a fake tablet-edit lane. Do not use fake hands, fake stylus layers, or generated readable text. If hands appear, they must come from real filmed footage or a plate that is consistent for the full shot.

Recommended sequence:

1. Resume or job application lands on desk.
2. One weak line is boxed or stamped.
3. A short joke/critique label appears: `too vague`, `no tool`, `no proof`, or `lost in the pile`.
4. The proof already on the resume appears as a small card or callout.
5. The weak line is covered, crossed, torn, or replaced.
6. The rebuilt line appears as the hero.
7. Optional receipt appears after the proof: tool, volume, result.
8. CTA appears for the service.

After Effects is allowed in this lane only for:

- paper slide and landing motion,
- stamp hits,
- cover-strip/delete animations,
- green rewrite reveal,
- small proof cards,
- subtle camera shake,
- final cover frame.

Hard reject the experimental lane if it becomes another SaaS UI demo, if resume text floats above the paper/screen, if labels dominate the resume, if the joke is not visually clear, or if the CTA appears before the human critique is earned.

Reference research note:

- `marketing/research/after_effects_viral_style_20260708/viral_style_research_notes.md`

## Codex-Accessible Upgrade Stack

Use these tools deliberately:

- After Effects: optional finishing pass for approved screen teardowns; use it for restrained highlight motion, delete/rewrite emphasis, proof callouts, and CTA polish only after all normal gates pass.
- Media Encoder: final platform encodes and batch presets after the AE or baseline video already passes creative review.
- Photoshop: first-frame, thumbnail, and reusable highlight/texture assets; not the source of readable resume content.
- Premiere Pro: manual/long-form finishing only; it is not the automated daily-short engine.
- Browser/Chrome control: capture real product flows, inspect mobile review links, and verify the viewer sees the edit clearly.
- HyperFrames: prototype pacing, captions, title-card movement, and lower-thirds without spending Veo/Flow credits.
- Canva: create thumbnails, cover frames, and platform-specific variants after a video passes creative QA.
- HeyGen: use sparingly for recruiter/avatar explainers or long-form intros, not as the default teardown format.
- Image generation: use for blank plates, thumbnails, or metaphor frames only; never for readable resume text.
- ffmpeg/ffprobe: final assembly, loudness checks, specs, contact sheets, and duration verification.

Do not treat access to more tools as permission to add complexity. If a tool makes the video feel less human, reject it.

### Optional Adobe Finishing Pass

Adobe does not replace the Signal pipeline. It only upgrades polish after the short is already good.

Run this pass only after the selected run has passed:

- `creative_gate`,
- `script_qa`,
- `voice_qa`,
- `screen_visual_qa` for the screen-only baseline, or `creative_qa` + `plate_qa` + `surface_fit_qa` for physical tablet/paper/monitor tests.

Controlled-screen Adobe commands:

```powershell
py -3 marketing_agent/adobe_finish_bridge.py readiness --source marketing/growth_runs/RUN_ID/final.mp4 --beat-map marketing/growth_runs/RUN_ID/beat_visual_map.json
py -3 marketing_agent/adobe_finish_bridge.py prepare --source marketing/growth_runs/RUN_ID/final.mp4 --beat-map marketing/growth_runs/RUN_ID/beat_visual_map.json --manifest marketing/growth_runs/RUN_ID/adobe_finish_manifest.json --adobe-video-out marketing/growth_runs/RUN_ID/adobe_finish_video_only.mov --final-out marketing/growth_runs/RUN_ID/final_adobe.mp4 --run-id RUN_ID
```

Hard reject the Adobe pass if it makes the resume less readable, adds dominant captions, feels like a product demo, adds fake hands/stylus, changes the approved script, or creates a score/CTA that was not already earned by the visible edit.

## Required Gate Order

### No-Credit Creative Proof Gate

Before any paid voice, Veo/Flow, or final rendering work starts, the run must pass a no-credit creative proof:

- at least 20 current short-form or short-form-relevant research examples,
- at least 10 resume, recruiter, job-search, or career-coach examples,
- at least 2 document-edit or tablet-edit mechanics references,
- at least 16 source-backed examples with evidence strength such as verified YouTube metadata, LinkedIn post text/transcript, or Instagram snippet review,
- at least 16 examples with explicit hook text,
- at least 14 examples with beat-by-beat breakdowns,
- most examples must state what Signal should copy and what Signal should avoid,
- five script options with read-aloud review notes,
- one selected production script,
- three storyboard directions,
- one exact human reviewer premise,
- one named candidate and target role,
- one realistic full resume artifact,
- one exact weak line read aloud,
- one visible edit plan that does not rely on generated hands,
- one proof-backed rewrite,
- no numeric score unless the visible receipt earns it,
- no product language until the CTA.

The script must follow the human reviewer order:

`candidate + target role -> recruiter search terms -> weak line -> human judgment -> proof already on resume -> visible edit -> CTA`

Scripts that contain the right ingredients but in a confusing order must fail. This is the main protection against "technically correct but sounds AI-generated."

Regression check:

```powershell
py -3 -m unittest marketing_agent.test_signal_growth_gates
```

This verifies that generic SaaS/product scripts fail and source-backed human-review packets pass.

Approved no-credit proof styles:

- Real Screen Recording Teardown,
- Desk Printout Red-Pen Fix,
- Recruiter Search Test.

Reference: `marketing/research/no_veo_authentic_video_styles_20260707.md`.

The new state path is:

`RESEARCHED -> SCRIPT_OPTIONS_WRITTEN -> HUMAN_READ_PASSED -> STORYBOARD_SELECTED -> CODEX_CREATIVE_APPROVAL -> VOICE_TEST_ALLOWED -> VIDEO_RENDER_ALLOWED`

If this gate fails, do not synthesize Abby voice, generate video, render final edits, or post.

### Voice Quality Gate

Before a full render, generate and review a short Abby test for the exact script voice. Fail the run if:

- "resume" is pronounced unnaturally,
- the read sounds corporate, robotic, or over-enunciated,
- the pacing drags past 32 seconds for a short,
- the CTA sounds like product copy instead of a creator close.

Fix order:

1. Rewrite the sentence so Abby reads it naturally.
2. Use accented `résumé` in voice text if needed.
3. Split long clauses into shorter spoken lines.
4. Regenerate the voice test before rendering the full video.

Mia `20260708-1058-5fa73ec3` is the current caution case: visual structure passed, but voiceover quality did not, so it must not post until regenerated.

Run these before final QA:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py research-swipe --urls-file marketing/research/viral_resume_videos_20260707/seed_urls.txt --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --min-sources 20
py -3 marketing_agent/signal_growth_pipeline.py creative-gate --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID
py -3 marketing_agent/signal_growth_pipeline.py script-qa --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID
py -3 marketing_agent/signal_growth_pipeline.py creative-qa --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --format desk_teardown
py -3 marketing_agent/signal_growth_pipeline.py plate-qa --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --visual-reviewed
py -3 marketing_agent/signal_growth_pipeline.py surface-fit-preview --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID
py -3 marketing_agent/signal_growth_pipeline.py surface-fit-qa --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --visual-reviewed
py -3 marketing_agent/signal_growth_pipeline.py voice-qa --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --human-reviewed --pronunciation-ok --natural-read --pacing-ok --cta-ok
py -3 marketing_agent/signal_growth_pipeline.py build-surface-teardown --run-id RUN_ID --visual-reviewed
py -3 marketing_agent/signal_growth_pipeline.py review --run-id RUN_ID --host 192.168.2.10 --port 8797
```

`creative-gate` is the pre-credit gate. It validates the current swipe file, matrix, five script options, selected script, storyboard options, and blunt creative review. Production `voice`, `veo`, and `omni-video` commands with `--run-id` are blocked until this gate passes.

After Andrew approves the gate in Codex chat, record the approval:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py approve-creative --run-id RUN_ID --phrase "APPROVE CREATIVE GATE RUN_ID"
```

Production `voice`, `veo`, and `omni-video` commands with `--run-id` are blocked until both `creative-gate` and `approve-creative` are complete.

Before asking Andrew for approval, generate the Codex review packet from live gate data:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py creative-review --run-id RUN_ID --host 192.168.2.10 --port 8796
```

This writes `codex_creative_gate_packet.md` and `creative_review.html` in the run folder. Do not hand-maintain these files; regenerate them after research, script, storyboard, or gate changes.

Preflight the post-approval screen-build path without spending credits:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py screen-build-plan --run-id RUN_ID --host 192.168.2.10 --port 8796
```

This writes `post_approval_screen_build_plan.json` and confirms the voice-test, full render, final QA, contact-sheet, and review commands are ready once creative approval is recorded.

Final QA with `--run-id` will fail if any required report for the selected format is missing or failed. Screen-only teardowns require `creative_gate`, `script_qa`, `screen_visual_qa`, and `voice_qa`. Physical tablet, paper, monitor, or Veo/Flow plate teardowns require `creative_gate`, `script_qa`, `creative_qa`, `plate_qa`, `surface_fit_qa`, and `voice_qa`.

For daily live-edit shorts, set the overlay frame rate before generating overlays:

```powershell
$env:SIGNAL_OVERLAY_FPS='12'
py -3 marketing_agent/signal_growth_pipeline.py live-edit-overlays --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID
```

This keeps deterministic resume text crisp while making the overlay generation practical for daily use. The final assembled video still renders as 30fps.

If full Veo 3.1 reference-image prompts filter or exhaust credits, use Veo 3.1 Lite with simple silent b-roll prompts and no readable generated text. Record any reused successful plate or credit blocker in the run folder before review.

## Gate Details

### creative-gate

Creates:

- `quality_gates/creative_gate.json`

Pass condition:

- `viral_resume_swipe_file.md`, `exemplar_matrix.csv`, `script_options.md`, `selected_script.md`, `storyboard_options.md`, and `blunt_creative_review.md` exist.
- The matrix has at least 20 examples.
- The matrix contains source-backed evidence, hook text, beat breakdowns, and copy/avoid notes.
- Five script options exist with read-aloud notes.
- The selected script is short enough and does not contain banned AI/product phrasing.
- The selected script follows the human reviewer order.
- Preferred script length is 70-82 words; hard failure is below 42 or above 96 words.
- Three storyboard directions exist and one is selected.
- Rendering remains blocked until Codex approval.

### approve-creative

This is not a quality gate file. It records Andrew's exact approval phrase in the run metadata. Paid `voice`, `veo`, and `omni-video` steps are blocked until this approval is recorded.

### research-swipe

Creates:

- `research_swipe/metadata.jsonl`
- `research_swipe/hooks.json`
- `research_swipe/formats.md`
- `quality_gates/research_swipe.json`

Pass condition:

- At least 20 source videos or short-form-relevant references are collected.
- At least 10 are directly resume/recruiter/job-search related.
- At least 2 are document/tablet edit mechanic references.
- Enough captions/hooks are extracted to inform script generation.

### script-qa

Creates:

- `quality_gates/script_qa.json`

Pass condition:

- The script names a candidate and target role.
- The script has one visible weak line.
- The script contains proof from the fix.
- The script is short enough for a punchy short.
- Banned AI/product phrases are absent.
- The script follows a human resume reviewer flow: named candidate, role, search terms, weak line, judgment, hidden proof, edit, CTA.

Common blockers:

- Generic script with no candidate.
- Score without proof.
- "Beat the bots" or "ATS auto-rejected you" language.
- Product-demo narration instead of human reviewer narration.

### voice-qa

Creates:

- `quality_gates/voice_qa.json`

Pass condition:

- A short Abby voice test exists in the run folder.
- The exact test audio has been listened to before the full render.
- "Resume" / "resume" pronunciation sounds natural, or the script has been rewritten around the issue.
- The read sounds like a human reviewer: conversational, lightly amused, and not corporate.
- Pacing is fast enough for an 18-32 second short.
- CTA delivery sounds natural instead of like product copy.

Common blockers:

- Abby says "resum" or otherwise mispronounces the core word.
- The read is slow, monotone, over-enunciated, or too polished.
- The CTA feels bolted on.
- The gate is marked without listening to the test audio.

### creative-qa

Creates:

- `quality_gates/creative_qa.json`

Pass condition:

- Research and script gates already passed.
- Resume/JD overlays exist.
- Video plates exist.
- Weak line and rewrite are different.
- Score receipt includes keyword, tool, metric, and outcome logic.
- CTA points to the free Signal score.

### plate-qa

Creates:

- `quality_gates/plate_qa.json`
- `quality_gates/plate_frames/*.jpg`

Pass condition:

- Footage is vertical and usable.
- Plate frames have been visually reviewed.
- No important generated text.
- No visible provider watermark.
- Hands/person are plausible and consistent.
- Document/tablet/screen area is stable enough for overlays.

`--visual-reviewed` means Codex or Andrew inspected the extracted frames. Do not use it blindly.

### surface-fit-qa

Use this for paper desk, tablet screen, laptop, monitor, and any physical plate where a readable resume/editor layer is composited onto a real surface.

Creates:

- `quality_gates/surface_fit_qa.json`

Preview command:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py surface-fit-preview --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID
```

This writes full-size preview images to `surface_fit_previews/` so the corner-pinned resume can be inspected before the pass/fail gate is recorded.

Mobile review packet:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py surface-fit-review --work-dir marketing/growth_runs/RUN_ID --run-id RUN_ID --host 192.168.2.10 --port 8797
```

This writes `surface_fit_review.html`, showing the source plate, deterministic overlay, and fitted result side by side for every surface. Use this before running any `--visual-reviewed` pass.

Optional no-credit animatic command:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py surface-fit-animatic --work-dir marketing/growth_runs/RUN_ID --out marketing/growth_runs/RUN_ID/surface_fit_animatic.mp4
```

This turns the fitted paper/tablet stills into a silent review MP4. It is only a timing and layout proof, not a final social-ready render. Final production still requires clean blank plates, Abby voice, final QA, and Codex approval.

Post-approval production wrapper:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py build-surface-teardown --run-id RUN_ID --visual-reviewed
```

This creates the fitted preview, refuses to continue unless `creative_qa`, `plate_qa`, and `surface_fit_qa` pass, generates Abby voice, builds the final MP4, creates a QA contact sheet, runs final technical QA, and stores the run as `AWAITING_CODEX_APPROVAL`.

Current-state audit:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py gold-readiness --run-id RUN_ID
```

This writes `gold_readiness_report.json` and `gold_readiness_report.md`, listing the next action, missing clean plates, gate states, final video/contact-sheet artifacts, and whether the run is ready for final Codex review.

Plate intake checklist:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py prepare-plate-intake --run-id RUN_ID --host 192.168.2.10 --port 8797
```

This writes `plate_intake_checklist.json` and `plate_intake_checklist.md`, listing the exact clean plate filenames required by `surface_fit.json`, the plate prompts, rules, and post-download QA commands.

Plate file ingest:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py ingest-plate-files --run-id RUN_ID --tablet-source PATH_TO_TABLET_OR_SCREEN_PLATE --paper-source PATH_TO_PAPER_PLATE
```

This copies clean image plates or extracts still frames from clean plate videos into the exact filenames declared in `surface_fit.json`. It preserves the originals, writes `plate_ingest_report.json`, and does not mark visual gates as passed. After ingest, always run `plate-qa`, `surface-fit-preview`, and `surface-fit-review` so the physical plate, deterministic resume overlay, and fitted result can be inspected side by side.

No-credit post-approval build plan:

```powershell
py -3 marketing_agent/signal_growth_pipeline.py surface-build-plan --run-id RUN_ID --host 192.168.2.10 --port 8797
```

This writes `post_approval_surface_build_plan.json` and `post_approval_surface_commands.md`. It should report `readyAfterApproval: true` before paid voice or clean plate generation starts.

Requires a `surface_fit.json` file in the run folder, for example:

```json
{
  "surfaces": [
    {
      "surface": "tablet",
      "frame": "tablet_plate_clean.png",
      "overlay": "resume_editor_overlay.png",
      "corners": {
        "tl": [150, 280],
        "tr": [930, 250],
        "br": [920, 1540],
        "bl": [130, 1500]
      },
      "blend": {
        "edgeFeatherPx": 2,
        "opacity": 0.98,
        "brightness": 0.99,
        "contrast": 1.03,
        "screenGlare": 0.08
      }
    }
  ]
}
```

Pass condition:

- Every physical paper/tablet/screen surface has exactly four corner points.
- The target area is inside the frame and large enough to keep the resume readable.
- The deterministic resume/editor overlay file exists.
- Codex or Andrew inspected full-size fitted frames and confirmed the resume is clipped or masked into the surface, not floating above it.
- `plate_qa` can validate either `shot*.mp4` video plates or clean image plates referenced by `surface_fit.json`, but visual review is still mandatory.
- Surface blend settings stay subtle: edge feather should usually be 1-2px, opacity 0.98-1.0, and screen glare under 0.10 so the resume still reads sharply.

This is now mandatory for `paper_desk_teardown`, `paper_desk_roast_rebuild`, `tablet_screen_teardown`, `tablet_screen_edit_rebuild`, and any run containing `surface_fit.json`.

### screen-visual-qa

Use this instead of `plate-qa` for the selected Screen Recording Teardown format.

Creates:

- `quality_gates/screen_visual_qa.json`

Pass condition:

- Screen teardown JSON exists and includes candidate, target role, weak line, rewrite, proof, search terms, and receipt.
- Storyboard contact sheet exists.
- At least six storyboard frames exist.
- Codex or Andrew inspected the frames and reran the command with `--visual-reviewed`.

This gate exists because the selected gold-standard path intentionally avoids Veo/Flow plates, fake hands, and fake stylus layers.

## Production Rule

No public posting until:

1. All quality gates pass.
2. Final QA passes with `--run-id`.
3. Codex provides the review link.
4. Andrew explicitly approves the exact rendered video.

## Physical Prop Resume Teardown Lane

Use this for Gohar-inspired desk/prop concepts such as paper roast, stamped resume, crumple/toss, rebuilt resume, and score receipt.

Hard pass conditions:

- The resume must look like a real professional one-page resume, not a three-line placeholder.
- The candidate, target role, weak line, proof, and rewrite must all be readable in the contact sheet.
- The weak mistake must be believable for a professional resume.
- The proof must exist elsewhere on the visible resume before the rewrite is revealed.
- The physical gag may reject the weak line or old version, but must not imply the person is bad or hopeless.
- Use deterministic text overlays only. No generated readable text.
- If using a physical desk/tablet/monitor plate, corner-pin or mask the resume into the surface; it cannot float above the paper or screen.
- After Effects finishing is recommended for final polish: paper shadow, stamp bounce, crumple/throw physics, subtle camera shake, paper texture, and motion blur.
- Abby voice should be generated only after script length is checked. Target 24-30 seconds before TTS; do not rely on heavy speed-up to fix a bloated script.

Current baseline run:

- `marketing/growth_runs/20260709-physical-desk-prop-marcus-v3-production`
- This is approved as a direction baseline only, not a universal standard. Next upgrade should replace the deterministic desk with a real overhead plate or After Effects-finished physical composite.
