# ATSHacker Build Roadmap Status

Reviewed: 2026-07-04

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
- `marketing/remotion/`: Remotion video renderer for Shorts, long-form review cuts, thumbnails, and mascot ads.
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
| Video growth engine | In progress, supervised | Daily packets, professional synthetic resume/JD cases, Remotion shorts, long-form YouTube rendering, ElevenLabs timestamp narration, audio QC, visual safe-area QC, Upload-Post queue, and Codex approval state exist. The active improved batch has three varied creator-native shorts in `AWAITING_CODEX_APPROVAL`. The current 2:07 long-form render is a review cut only and is blocked from publish approval until expanded past the long-form duration gate. Needs the metrics loop, audio loudness QC, render-speed work, and publish analytics hardening. |

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
- `ResumeCrimeScene` now renders professional one-page resume artifacts, target job descriptions, marked source bullets, role context, and varied visual archetypes.
- The current long-form YouTube lane has a 9-section 1920x1080 review render, but it is not publish-ready because it fails the long-form minimum duration gate.
- ElevenLabs `/with-timestamps` now produces MP3 narration plus word-level caption alignment for fresh shorts and long-form segments.
- Daily shorts now rotate creator-native playbooks instead of repeating the same template: Resume Crime Scene roast, Recruiter Search Test, and Job Description Translation.
- The creative quality gate now penalizes repeated openings and blocked robotic phrases such as `JD asks for`, `real, but buried`, and `same person, clearer proof`.

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
- The media pipeline can create and queue stronger supervised shorts, but it should not be fully autonomous posting yet.
- The current ElevenLabs key is restricted for Text to Speech and passes TTS probes; voice-list reads may be denied by key scope, so the configured voice ID is treated as authoritative.
- The media publisher now requires Codex approval for review-required posts, but older queued ad-style clips should still be retired or rewritten before broad posting.
- Older ad-style and repeated teardown videos still exist as artifacts, but their approval records have been moved to `REVISION_REQUESTED` and should be rewritten before posting.

## Verification Snapshot

Latest checks run during this review:

- Web lint: passed with 7 existing `next/no-img-element` warnings.
- Remotion typecheck: passed.
- Studio short QC: passed for the current three Codex-reviewed varied-format daily shorts.
- Audio asset QC: passed for daily shorts and episode audio assets.
- Visual safe-area QC: passed for the current three Codex-reviewed varied-format daily shorts.
- Long-form YouTube QC: blocked the current 2:07 rendered review cut for being below the publish-ready duration floor.
- Marketing agent compile check: passed.
- Autopost dry run: passed; review-gated videos remain blocked from live posting unless Codex approval exists for the exact file hash and the poster is run with `--approved`.

## Current Build Direction

Keep building toward income in this order:

1. Make the free score feel valuable and trustworthy.
2. Make the paid unlock obvious through a real before/after preview.
3. Make fulfillment reliable enough that refunds/support stay low.
4. Make social and SEO drive measured score completions, not just views.
5. Use metrics to decide which content series and offers deserve more build time.
