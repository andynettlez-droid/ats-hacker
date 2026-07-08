# Codex Video Quality Research - 2026-07-08

Goal: improve Signal shorts without returning to the low-quality generated-video loop.

## Source-backed takeaways

- TikTok's own creative guidance emphasizes native-feeling creative strategy, not polished SaaS demos. Signal should keep the creator/recruiter teardown lane and make the first frame self-explanatory.
  - Source: https://ads.tiktok.com/business/en-US/blog/creative-best-practices-top-performing-ads
- Current Shorts guidance still points to fast hooks, purposeful cuts, and retention review before scaling a format. Signal should review each short as a format test, not only a render artifact.
  - Source: https://conthunt.app/blog/youtube-shorts-best-practices
- YouTube/creator guidance emphasizes Shorts as a repeatable strategy, not one-off clips. Signal needs format rotation with a stable QA bar: screen teardown, search test, job-post answer key, red marker roast.
  - Source: https://www.youtube.com/watch?v=WUl0Sra5XBM
- ElevenLabs documentation confirms lower stability can introduce more expressive variation, while high similarity can preserve artifacts if the source voice has issues. Signal should treat Abby voice as a per-script test, not a blanket pass.
  - Source: https://elevenlabs.io/docs/api-reference/voices/settings/update
  - Source: https://elevenlabs.io/docs/eleven-creative/playground/text-to-speech
- Descript-style transcript editing is useful as a workflow reference: cut dead words by text, then assemble. Signal can imitate that locally by storing scripts as beat rows and forcing every beat to justify a visual.
  - Source: https://www.descript.com/

## Immediate pipeline upgrades

1. Add a voice pronunciation gate.
   - Generate a 10-second Abby test before full voice.
   - Specifically listen for "resume/résumé", role terms, tool names, and CTA.
   - If it fails, rewrite the script or use accented `résumé`.

2. Add a beat-to-visual density gate.
   - Every narration beat must map to one visible action: search term appears, weak line highlight, proof box, delete, rewrite, receipt, CTA.
   - Any narration without a matching visual action should be cut.

3. Add a no-credit animatic stage.
   - Use HyperFrames or HTML/ffmpeg to test pacing, captions, and contact sheets before paid voice or generated plates.
   - The animatic should be reviewed with sound off first.

4. Add cover-frame and thumbnail generation after approval.
   - Canva is the best integrated tool for polished platform variants.
   - Generate a 9:16 cover, 1:1 crop, and YouTube Shorts title frame from the strongest visual frame.

5. Keep physical video plates experimental.
   - Only use Veo/Flow for blank realism plates.
   - Never rely on generated readable resume text.
   - Reject fake hand/stylus attempts unless they are real footage or perfectly masked.

## Recommended Codex tool use

- Browser/Chrome: mobile review, website capture, and future real product capture.
- HyperFrames: no-credit motion prototypes, captions, and timing.
- Canva: thumbnails and social cover variants after approval.
- HeyGen: occasional presenter or long-form host, not default teardown shorts.
- ffmpeg/ffprobe: final assembly, specs, contact sheets, loudness, duration.

## Next implementation targets

- `voice_pronunciation_qa.json` per run.
- `beat_visual_map.json` per run.
- `animatic_contact_sheet.png` before full voice/render.
- `cover_frame.png` and `social_variants/` after Codex approval.
