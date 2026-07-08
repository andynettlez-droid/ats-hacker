# Signal Video Pipeline Improvement Log - 2026-07-08

## What shipped

Approved and posted:

- Jordan cybersecurity screen teardown
  - YouTube: https://www.youtube.com/watch?v=EmuocEG-59o
  - Instagram: https://www.instagram.com/reel/DaiTuSsCasf/
  - TikTok: https://www.tiktok.com/@Andrew/video/7660171437755387154
- Ethan project coordinator screen teardown
  - YouTube: https://www.youtube.com/watch?v=xxO3nXTl5Zw
  - Instagram: https://www.instagram.com/reel/DaidDeAFLnq/
  - TikTok: https://www.tiktok.com/@Andrew/video/7660192425243102482

Held back:

- Mia patient access coordinator screen teardown, run `20260708-1058-5fa73ec3`
  - Visual structure passed.
  - Voiceover did not pass creative review.
  - Do not post until the voice is regenerated and re-reviewed.

## Current production spine

Use the screen-only deterministic resume teardown as the production default:

1. Full, realistic resume visible immediately.
2. Search terms shown before the critique.
3. Weak line highlighted.
4. Proof already on the resume appears before the fix.
5. Rewrite happens in the same resume slot.
6. Receipt/score logic appears only after visible rationale.
7. CTA is short and human.

Physical tablet/paper/Veo plates stay experimental until they clearly beat screen-only on readability and authenticity.

## Improvements applied

- Fixed `screen_visual_qa` so it checks the run's own `searchTerms`, `proofLines`, and `receiptRows` instead of stale cybersecurity terms.
- Re-ran Ethan screen visual QA: passed with no warnings.
- Re-ran Ethan final QA: passed.
- Updated the reusable Codex skill with the current production default, tool stack rules, and voice quality gate.
- Updated `marketing/video_pipeline_quality_gates.md` with the same guardrails.

## Previous research-agent recommendations now adopted

- Keep deterministic screen-edit as the stable spine.
- Use Browser/Chrome control for mobile review and future real product captures.
- Use HyperFrames for no-credit motion/caption/title-card prototypes.
- Use Canva only after approval for thumbnails and platform variants.
- Use HeyGen sparingly for presenter/long-form assets, not default shorts.
- Use image generation only for blank plates, thumbnails, or metaphors; never for readable resume text.

## Next research question

A new research agent should review the current repo pipeline and Codex-accessible tools, then recommend:

- how to improve script variety without losing the human reviewer logic,
- how to automate Abby voice pronunciation checks,
- how to create better no-credit animatics before final assembly,
- how to produce stronger thumbnails/cover frames,
- how to add real product/screen captures without making the shorts feel like SaaS demos.
