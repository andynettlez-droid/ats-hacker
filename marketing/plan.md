# Signal by ATSHacker Marketing And Revenue Roadmap

Last updated: June 2026

## Objective

Generate small, repeatable side income by turning job-search attention into free Signal score completions, then converting the highest-intent users into one-time paid application packages.

The business is not "viral videos." The business is:

Traffic -> free score -> visible gap -> trust -> paid resume / cover letter / bundle.

## Current Offer Ladder

| Offer | Price | Purpose |
| --- | ---: | --- |
| Free Signal score | $0 | Prove the resume-to-job gap before asking for money. |
| Resume optimization | $9.99 | Main impulse purchase for one target job. |
| Cover letter only | $9.99 | Secondary purchase for users who already have a resume. |
| Resume + cover letter bundle | $14.99 | Best-value default and current AOV lift. |
| Multi-role pack | TBD, likely $19.99-$24.99 | Future repeat-purchase product for active job seekers. |

## Positioning

Signal helps qualified job seekers make their real experience easier to find and understand.

Use this language:

- "Your resume may not be speaking the job description's language."
- "Signal compares your resume to the target role and shows missing recruiter-search terms."
- "We rewrite real experience. No fake skills, jobs, degrees, or outcomes."
- "One-time payment. No subscription."

Avoid this language unless backed by a specific source in the piece:

- "ATS robots rejected you."
- "75% of resumes are automatically filtered out."
- "Guaranteed interviews."
- "We beat Workday / Greenhouse / Lever."
- "This will sort you to the top."

## Site Roadmap

### Phase 1: Revenue Foundation

- Keep the free Signal score as the primary entry point.
- Keep trust messaging beside every payment CTA: Stripe secured, no subscription, no fake experience.
- Add `.docx` export alongside PDF.
- Persist paid outputs by Stripe session ID so customers can safely redownload.
- Make export and rewrite failures visible with retry paths.
- Add checkout/success tests for resume, cover letter, and bundle purchases.

### Phase 2: Conversion Lift

- Add a before/after preview before checkout:
  - show one rewritten bullet or section preview;
  - blur the remaining optimized output;
  - CTA: "Unlock full optimized package."
- Add clearer bundle nudges after free score completion.
- Add a multi-role application pack once single-purchase flow is durable.
- Add email capture only after the free score gives value.
- Track score completion, checkout start, purchase, bundle take rate, and source channel.

### Phase 3: Quality And Trust

- Add grounding checks that flag invented facts before export.
- Add cover-letter specificity validation:
  - company name;
  - role title;
  - 2-3 role-specific requirements;
  - matching resume proof.
- Add "what changed and why" explanations after generation.
- Add better example outputs for resume and cover letter quality review.
- Add an admin retry/recovery screen for support cases.

### Phase 4: SEO

- Expand `/tailor/[job-title]` to at least 50 quality role pages.
- Prioritize role pages around:
  - "[role] resume keywords";
  - "ATS resume for [role]";
  - "tailor resume to [role] job description";
  - "resume score for [role]."
- Make every role page unique:
  - role-specific keyword list;
  - sample weak bullet;
  - sample stronger bullet;
  - role-specific free-score CTA.
- Add blog/internal-link support pages:
  - ATS-friendly resume format;
  - PDF vs DOCX resume;
  - what an ATS actually does;
  - why qualified resumes can still be hard to find.

## Social And YouTube Strategy

Short-form content is top-of-funnel. The product should appear as the proof mechanism, not as a generic SaaS ad.

### Core Series

1. Resume Crime Scene
   - Anonymous resume teardown.
   - Find 2-3 visibility problems.
   - Fix one bullet.
   - Reveal score movement.

2. ATS Myth Lab
   - Debunk common job-search myths.
   - Build trust by explaining what ATS systems usually do: parse, store, index, search, and filter.

3. Job Description Translation
   - Take a real-style job post.
   - Translate it into keywords, skills, tools, and proof points a resume should reflect.

4. One Bullet Fix
   - Before/after bullet rewrite in under 30 seconds.
   - CTA: "Run your own free Signal score."

5. Recruiter Search Test
   - Ask whether a resume would appear for specific recruiter searches such as HubSpot, CAC, lifecycle marketing, SQL, Kubernetes, Epic, or FP&A.

6. AI Resume Tool Head-To-Head
   - Compare tools using transparent criteria.
   - Use live research and source notes.
   - Avoid unverifiable "best" claims.

7. Resume Builder Cost Trap
   - Compare subscription pressure to one-time application help.
   - Keep claims current and sourced.

### Weekly Content System

- 1 researched YouTube topic per week.
- 1 long-form script or teardown outline.
- 3-5 Shorts/Reels/TikToks cut from the same research packet.
- 1 product or landing-page improvement tied to the strongest content angle.

## Side-Income Math

Targets based on a likely $13-$15 average order value:

| Monthly goal | Approximate sales needed |
| --- | ---: |
| $500 | 35-45 sales |
| $1,500 | 100-120 sales |
| $3,000 | 200-230 sales |

Early social funnel assumptions:

- 100,000 targeted short-form views.
- 0.3%-0.8% click-through to site.
- 35%-50% of visitors complete the free score.
- 3%-6% of score completers buy.

That produces a rough range of 3-24 sales per 100,000 targeted views. The path to small side income is plausible, but it requires consistent targeted content plus a high-trust conversion flow.

## Metrics

Review weekly:

- views by series;
- link clicks by post;
- free Signal score completions;
- free-score-to-checkout-start rate;
- checkout-start-to-purchase rate;
- bundle take rate;
- revenue by UTM source;
- refund/support issues;
- Google Search Console impressions and clicks for role pages.

North star: profit per visitor.

## Guardrails

- Disclose creator status in communities and founder-led posts.
- No fake reviews, fake testimonials, covert posting, or invented outcomes.
- Use sourced claims for competitor pricing, platform behavior, market stats, and tool comparisons.
- Do not publish social posts, email real people, or spend money without review of the exact asset/copy.
- Product and documentation commits may be pushed during the active autonomous build once checks pass.
