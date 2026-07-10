# ATSHacker Build Roadmap Status

Reviewed: 2026-07-09

## 2026-07-09 Update - Evidence-Backed Gold Short Pipeline

- Daily research now fails closed on recency, platform mix, transcripts, contact-sheet review, creator concentration, novelty, and cross-platform angle support.
- The current packet passed with 22 reviewed shorts, 12 recent examples, 12 YouTube sources, 10 valid transcripts, 2 browser-observed TikToks, and 3 browser-observed Instagram Reels.
- Script generation now uses a five-option creative council. It selected the direct human review and rejected procedural/product-forward variants without asking Andrew to approve intermediate copy.
- Production resumes are full professional artifacts with two roles, 6-10 experience bullets, projects, education, certifications, one believable weak line, and explicit proof references.
- Abby voice generation now creates multiple expressive takes, fixes known pronunciation risks, normalizes to -16 LUFS, trims dead tail, and retimes both audio and timestamps toward a measured creator pace.
- The active renderer is `controlled_resume_capture.mjs`, synchronized by `controlled_screen_sync.py`. The legacy screen renderer and Remotion lane remain retired.
- Final review freezes the video, script, AAC audio, beat map, and evidence ledger by SHA-256. Posting requires approval of the unchanged final file.
- After Effects 2026 and aerender are detected. `adobe_finish_bridge.py` prepares a fail-closed optional handoff, but unattended `.aep` creation remains disabled after local ExtendScript hangs. Adobe cannot block the daily base pipeline.
- Gold test run `20260709-1922-4ff62c61` is 1080x1920, H.264/AAC, 30 fps, 27.5 seconds, passes deterministic QA, and is awaiting exact-video Codex review. It is not posted.

Voice correction after review:

- The Abby master on the first gold cut was rejected as robotic. It stacked API speed `1.12` with a second `1.216x` waveform speed-up.
- Waveform time-compression is now disabled by default. Script length, punctuation, and voice choice must carry pacing.
- Sarah Casual with `eleven_v3` is the new screen-review baseline. The revised Leah cut lands at 142 WPM naturally and runs 27.3 seconds.
- The opening visual now shows the exact weak line and reviewer judgment at readable size while recruiter terms reveal sequentially. It adds retention beats without zoom, fake hands, or caption slabs.
- The screen-only lane is ready for a controlled social test after final human review, but real overhead footage with real hands remains the higher-upside authenticity experiment.

Immediate next actions:

1. Review the frozen Leah cybersecurity short as a viewer; revise only if the actual watch reveals a human-flow or readability problem.
2. Once one exact file is approved, use it as the screen-only visual baseline for two role-varied tests.
3. Build one manually reviewed AE comparison project later; keep it only if side-by-side review beats the base without reducing resume readability.
4. Continue the revenue path: social UTM -> free score -> sample proof -> paid resume/cover-letter package.

## 2026-07-08 Update - Site Trust And Video Pipeline Guardrails

Current direction:

- Keep the site focused on income: free score -> clear sample proof -> paid resume, cover letter, or application pack.
- Reduce gimmicky mascot/decorative energy around the money path. Signal can stay as a small brand/helper, but the resume, job description, sample files, guarantee, and checkout trust signals need to carry the sale.
- Keep the stable screen-only resume teardown as the production video baseline until a real tablet/monitor composite beats it on clarity.
- Treat physical tablet, paper, monitor, Veo/Flow, and Adobe/After Effects variants as finishing experiments that must inherit the same creative gates.

Work completed in this pass:

- Landing-page CTA language was tightened around `Check Free Resume Score`, `Start Free Score`, and `See Sample Rewrite`.
- The old "Crime Scene" label was softened to `Sample Teardown` in the visible navigation/CTA layer.
- Decorative duplicate mascot peeks were removed from the upload/pricing/FAQ money path.
- The sample-output/download band was moved toward a calmer white/slate trust treatment with explicit "inspect the files before checkout" framing.
- Upload flow now includes clearer privacy/payment reassurance near the resume dropzone.
- Video runner now has a first-class `voice_qa` quality gate. Full screen/surface builds and final `qa --run-id` require it.
- `research-swipe` now defaults to 20 sources instead of 5.
- `AGENTS.md`, `marketing/video_pipeline_quality_gates.md`, and the Adobe upgrade plan now document the updated gate order.
- Adobe 2026 install is verified locally: After Effects, aerender, Media Encoder, Photoshop, and Premiere Pro are available.
- A first After Effects finishing scaffold now exists under `marketing/adobe/after_effects/` with preflight, payload generation, AE project creation, render, schema, and usage docs.
- The Adobe helper refuses normal payload creation unless the source run has already passed creative, script, visual, and voice gates. Old pre-voice-gate runs require an explicit local-experiment override.
- The score-results section has been moved toward a calmer white/slate trust-report style with clearer buyer proof, less mascot/gimmick energy, and direct paid unlock CTAs.

Immediate next build actions:

1. Run the AE finishing scaffold on a fresh screen-only teardown that has passed `voice_qa`, then compare it against the current baseline for readability, pacing, and trust.
2. Continue homepage trust polish below the score-results area: sample deliverable, guarantee/refund, checkout reassurance, and tighter mobile proof flow.
3. Add money-path reliability tests for checkout, rewrite fulfillment, success restore, PDF/DOCX downloads, and paid unlock behavior.
4. Keep all new social videos at Codex approval until the exact rendered file is approved.

## Goal

Build Signal by ATSHacker into a revenue-focused career tool:

Social/search traffic -> free Signal score -> clear resume-to-job gap -> trust -> paid resume, cover letter, or bundle.

The product should make money from the offers, not from vague "AI resume" hype. The best current offer path is:

- Free Signal score.
- Resume tailoring for $9.99.
- Cover letter for $9.99.
- Resume plus cover letter bundle for $14.99.
- Future multi-role pack or job-hunt pass after single-purchase reliability is solid.

## Current Repo Map

- `web/`: Next.js product site, score flow, checkout, rewrite fulfillment, SEO pages, admin stats.
- `marketing/`: revenue strategy, SEO/content plans, daily content packets, media readiness docs.
- `marketing/remotion/`: historical renderer only; do not use it for the active production short lane.
- `marketing/autopost/`: Upload-Post queue and review-gated posting to TikTok, Instagram, and YouTube.
- `marketing_agent/`: content agent, quality gates, video pipeline helpers, content monitor.

## Product Build Status

| Area | Status | Notes |
| --- | --- | --- |
| Signal homepage/UI | In progress, usable | Dark Signal redesign is in the main app, with the animated Signal mascot in header/sections and mobile-friendly CTA flow. Needs final cross-device visual QA after each large UI change. |
| Free score funnel | Implemented | `/api/score` returns a score, matched keywords, missing keywords, and a verdict. Homepage persists resume/job context for checkout. |
| Paid offers | Implemented | Stripe checkout supports resume, cover letter, and bundle at $9.99/$9.99/$14.99. Metadata tags ATSHacker sessions for admin reporting. |
| Paid rewrite fulfillment | Implemented with guardrails | `/api/rewrite` verifies paid Stripe sessions, caches fulfilled outputs, preserves candidate facts, and instructs the model not to invent metrics, jobs, tools, skills, or credentials. |
| Downloads | Implemented | Success page exports resume and cover letter as PDF and ATS-friendly DOCX. It also restores fulfilled output by Stripe session when possible. |
| Proof before payment | Implemented basic, needs testing | Score results now include a one-bullet unlock preview plus post-purchase before/after score lift and keyword gap proof. Next step is A/B testing and a stronger generated preview. |
| Shareable score card | Implemented basic | `/s/[score]` and `/api/og` support shareable score links. Needs share-rate tracking and stronger visual templates. |
| Programmatic SEO | Partially implemented | `/tailor/[job-title]` exists with 35 role records and sitemap/robots support. Roadmap target remains 50+ high-quality roles. |
| Admin/revenue visibility | Implemented basic | Admin login and Stripe-backed stats route exist. Needs fuller source-channel revenue dashboard and support recovery workflow. |
| Analytics | Partial | Vercel Analytics events exist for score completion, checkout start, paid fulfillment, post-purchase score lift, downloads, demo start, cover-letter copy, and score share. Needs UTM-to-revenue reporting and platform metrics ingestion. |
| Test coverage | Thin | Lint passes with warnings. Need checkout/rewrite/success tests and a smoke script for the main conversion flow. |
| Video growth engine | Script layer rebuilt, production paused | The previous rendered shorts are treated as failed creative QA. A 2026-07-05 trend research brief now feeds the script generator, daily packets must include `trendResearch`, and the creative gate now blocks product-demo openings, rubric-first narration, unsupported score jumps, and missing human-review premises. No new video/audio render was produced in this rebuild pass. Art direction, audio delivery, and render-level QA are next. |

## What Is Done

- Honest positioning has replaced the weaker "robot auto-reject" framing in the main product language.
- Free score is the front door.
- Stripe one-time payment offer ladder exists.
- Resume, cover letter, and bundle purchase paths exist.
- Paid fulfillment is tied to Stripe session validation and a fulfillment cache.
- PDF and DOCX output are available.
- Before/after score and keyword gap proof exists after generation.
- Score results now show a one-bullet unlock preview before checkout, without inventing unsupported facts.
- Success flow now tracks paid fulfillment, score lift, document downloads, and cover-letter copy actions without sending resume content.
- Signal mascot component exists and is used throughout the product.
- 35 role SEO pages exist.
- Social/video pipeline is connected to the product CTA: "check your free Signal score."
- Codex video approval now blocks live posting until the exact QA-passed file hash is approved.
- Video scripts now rotate believable synthetic resume/job cases instead of repeating generic "AI-polished resume" placeholders.
- A new viral resume-video research brief exists at `marketing/content_research/resume_video_trends_2026-07-05.md`, based on current YouTube Shorts, CareerTok, recruiter-creator, resume-template, and social job-search research.
- Daily video packets now carry `trendResearch` fields: human premise, platform pattern, research mechanic copied, and avoided failure mode.
- The script generator now writes human reviewer reads: exact weak resume line, job requirement, low-score reason, visible source proof, honest rewrite, score rationale, and free-score CTA.
- `ResumeCrimeScene` now renders professional one-page resume artifacts, target job descriptions, marked source bullets, role context, and varied visual archetypes.
- The current long-form YouTube lane has a 9-section 1920x1080 review render, but it is not publish-ready because it fails the long-form minimum duration gate.
- ElevenLabs `/with-timestamps` now produces MP3 narration plus word-level caption alignment for fresh shorts and long-form segments.
- Daily shorts now rotate creator-native playbooks instead of repeating the same template: Live Resume Review, Recruiter Search Test, and Job Description Review.
- The creative quality gate now penalizes repeated openings and blocked robotic phrases such as `JD asks for`, `real, but buried`, and `same person, clearer proof`.
- The creative quality gate now also blocks missing `trendResearch`, missing human-review premise, rubric-first narration, and score jumps that are not explained by visible resume/JD evidence.

## Highest-Leverage Next Product Work

1. Harden and test the pre-checkout preview.
   - Measure whether the one-bullet preview lifts checkout starts.
   - Add a stronger generated preview once grounding checks are in place.
   - Keep the rest of the optimized output locked until checkout.

2. Add reliability tests for money paths.
   - Checkout session creation for each product.
   - Rewrite rejects unpaid/wrong-price/wrong-app sessions.
   - Success page restore path.
   - PDF/DOCX generation path.

3. Add complete funnel analytics.
   - Score completed.
   - Checkout started by product.
   - Purchase completed by product.
   - Bundle take rate.
   - Share-score clicks.
   - UTM source to purchase.

4. Improve generation quality gates.
   - Cover letter specificity validation: company, role title, requirements, matching proof.
   - Resume grounding check: flag unsupported metrics/tools/skills before export.
   - "What changed and why" explanation after generation.

5. Expand SEO to 50+ role pages.
   - Prioritize roles with strong search intent and clear keyword language.
   - Keep each page unique: keywords, weak bullet, stronger bullet, role-specific CTA.

6. Add support/recovery UX.
   - Admin view for failed generations.
   - Retry fulfillment.
   - Customer redownload by session ID.

## Revenue Roadmap

### Phase 1: Stabilize The Sale

Status: Mostly built, needs testing and polish.

- Keep free score as primary CTA.
- Keep trust badges near every payment CTA.
- Finish tests on checkout, rewrite, exports, and restore.
- Add pre-checkout preview to increase confidence.

### Phase 2: Lift Conversion

Status: Next.

- Add blurred preview.
- Add stronger bundle nudge after score results.
- Add score-share card polish.
- Track all funnel events and source attribution.
- Start measuring revenue per visitor.

### Phase 3: Increase AOV And Repeat Use

Status: Planned.

- Multi-role pack or job-hunt pass.
- Referral discount or friend-share incentive.
- Optional email capture after free score delivers value.
- Affiliates for career coaches and resume creators.

### Phase 4: Compound Traffic

Status: Started.

- Expand role SEO pages.
- Publish daily social packets only when creative passes review.
- Feed best-performing content angles back into landing page copy.
- Build content metrics into the product analytics loop.

## Current Risk List

- The product can take payment and generate files, but money-path automated tests are still thin.
- The score and rewrite flows depend on OpenAI availability and should expose better retry/fallback states.
- Analytics does not yet prove which video/SEO/social source creates purchases.
- The media pipeline can create and queue supervised shorts, but public posting is paused until the art direction and audio layers are rebuilt to match the new script standard.
- The current ElevenLabs key is restricted for Text to Speech and passes TTS probes; voice-list reads may be denied by key scope, so the configured voice ID is treated as authoritative.
- The media publisher now requires Codex approval for review-required posts, but older queued ad-style clips should still be retired or rewritten before broad posting.
- Older ad-style and repeated teardown videos still exist as artifacts, but they should be considered failed creative QA and must be rewritten before posting.

## Verification Snapshot

Latest checks run during this review:

- Web lint: passed with 7 existing `next/no-img-element` warnings.
- Remotion typecheck: passed.
- New script-only creative gate: passed for `marketing/daily_content/2026-07-05-human-recruiter-live-resume-teardown-rebuilt-from-viral-trend-re`.
- Marketing agent compile check: passed after the script-layer rebuild.
- Studio short QC: last passed for the previous rendered varied-format daily shorts, but those renders are no longer considered post-ready after manual creative review.
- Audio asset QC: passed for daily shorts and episode audio assets.
- Visual safe-area QC: passed for the current three Codex-reviewed varied-format daily shorts.
- Long-form YouTube QC: blocked the current 2:07 rendered review cut for being below the publish-ready duration floor.
- Autopost dry run: passed; review-gated videos remain blocked from live posting unless Codex approval exists for the exact file hash and the poster is run with `--approved`.

## Current Build Direction

Keep building toward income in this order:

1. Make the free score feel valuable and trustworthy.
2. Make the paid unlock obvious through a real before/after preview.
3. Make fulfillment reliable enough that refunds/support stay low.
4. Make social and SEO drive measured score completions, not just views.
5. Use metrics to decide which content series and offers deserve more build time.
