# Signal Continuous Agents Playbook

This playbook defines the two continuous agent lanes for Signal by ATSHacker:

- Growth Studio Agent: researches topics, writes scripts, renders short-form drafts, and queues review-ready social assets.
- Product Build Agent: continues UI, product, quality, checkout, export, and resume/cover-letter improvements.

The system should automate production work, not final judgment. Public posting, competitor claims, deploys, and pushes still require explicit human approval.

## Lane 1: Growth Studio Agent

### Mission

Find timely career-tech topics and turn the best ones into trustworthy short-form video drafts for TikTok, Instagram Reels, and YouTube Shorts.

### Daily Inputs

- Current platform trends and search interest in the career, job-search, resume, ATS, AI writing, and AI coding/productivity lanes.
- Existing marketing plans in `marketing/`.
- Existing video catalog and briefs.
- Current product positioning: honest resume matching, no fake experience, no ATS auto-reject myths.
- Current mascot and Remotion pipeline.

### Topic Examples

- Claude vs Codex resume head-to-head.
- Top 10 resume builders for one specific role.
- Why one resume scores differently for different jobs.
- ATS myth: auto-reject vs recruiter search.
- Resume builder subscription traps.
- Job description language candidates miss.
- Cover letter before/after for a specific role.
- AI resume tools ranked by trust, editability, and role fit.

### Research Rules

- Use live web research for every trend or competitor claim.
- Prefer primary sources, official docs, product pages, pricing pages, and current platform trend tools.
- For competitor comparisons, save sources and avoid unverifiable superiority claims.
- Reject topics that require fabricated outcomes, fake testimonials, or fear-based misinformation.
- Score ideas on:
  - Timeliness.
  - Relevance to job seekers.
  - Search/social hook strength.
  - Trust risk.
  - Production effort.
  - Product fit.

### Output Per Candidate

Each top candidate should produce:

- Working title.
- One-sentence thesis.
- Hook variants.
- 20-35 second script.
- Storyboard.
- Visual direction.
- Audio direction.
- Caption and hashtag set.
- Platform-specific title/description.
- Source notes.
- Trust risk notes.
- Recommended status: reject, backlog, script_ready, render_ready, or review_required.

### Video Pipeline

1. Write a brief in `marketing/video_briefs/`.
2. Render through Remotion or the approved video pipeline.
3. Use the Signal mascot, not the old human presenter, unless the user explicitly asks for a presenter.
4. Use studio-style audio:
   - No harsh meme SFX.
   - No distracting whooshes.
   - Smooth low-end pulses, tasteful rises, and light shimmer are acceptable.
   - Audio must be present and balanced.
5. Extract still frames at hook, midpoint, transformation, proof, and CTA.
6. QA for mobile readability.
7. Copy final draft to `marketing/autopost/videos/`.
8. Add to `marketing/autopost/posts.json` with `status: "review_required"`.
9. Run a targeted dry run:

```bash
node post.mjs --dry-run --only videos/NAME.mp4 --now
```

10. Never publish without explicit approval. Approved one-file publish command:

```bash
node post.mjs --only videos/NAME.mp4 --now --approved
```

### Video QA Checklist

- First frame has a readable hook.
- On-screen text fits in 9:16 mobile.
- Signal mascot is visible and recognizable.
- No old human presenter is used by accident.
- Claims are accurate and non-defamatory.
- No fake customer outcomes.
- No fabricated product ratings or rankings.
- Audio track exists and is not annoying.
- Captions and CTA are clear.
- Video file is present in `marketing/autopost/videos/`.
- Queue entry has TikTok, Instagram, and YouTube.
- Queue entry uses `status: "review_required"` until approved.

## Lane 2: Product Build Agent

### Mission

Keep improving the production product while the growth lane creates draft demand.

### Priority Stack

1. Customer trust and fulfillment durability.
2. Resume and cover-letter output quality.
3. Checkout, success page, and redownload reliability.
4. Homepage and application UI polish.
5. Export quality.
6. Admin/retry tooling.
7. Analytics and conversion instrumentation.
8. Programmatic role pages and SEO.

### Current High-Value Fixes

- Persist paid outputs server-side by Stripe session ID.
- Harden resume and cover-letter grounding checks.
- Add stronger cover-letter specificity validation.
- Make export/download failures visible and recoverable.
- Finish dark Signal UI redesign across the full homepage.
- Keep the header/logo mobile-safe.
- Add tests around checkout success and export flows.

### Working Rules

- Work in an isolated worktree or clearly scoped branch.
- Do not revert user or other-agent edits.
- Keep commits small and reviewable.
- Run checks that match the touched surface:
  - Web: typecheck, lint, build, targeted route tests.
  - Marketing video: Remotion typecheck, render, still-frame QA.
  - Autopost: syntax check and dry run.
- Do not push, deploy, or publish unless explicitly told.

### Product QA Checklist

- Mobile header renders without clipping.
- Logo is present and recognizable.
- Main CTA works.
- Score flow handles empty, malformed, and realistic inputs.
- Checkout creates the intended package.
- Success page can recover/reload a purchased output.
- Resume and cover letter do not invent facts.
- Export failures are shown to users.
- Build passes or any failure is documented with the exact blocker.

## Cross-Agent Handoff

The agents should write short handoffs with:

- What changed.
- What files changed.
- What was verified.
- What is queued for review.
- What is blocked.
- The next highest-value action.

If both agents touch related areas, the Product Build Agent owns production code and the Growth Studio Agent owns marketing briefs, rendered video drafts, and social queue entries.

## Posting Policy

The current social account setup supports TikTok, Instagram, and YouTube, with unlimited posting capacity. That does not mean unlimited posting is the strategy.

Default cadence:

- 1 high-quality post per day while the account is warming up.
- Add a second daily post only when quality stays high and analytics are readable.
- Keep posts staggered so each creative gets a clean test window.

Publish only after human review of the exact file, caption, and target platforms.
