# ATSHacker — Marketing Plan & Content Calendar

_Last updated: June 2026_

## 1. Positioning

**One-liner:** "Beat the resume robots for $5 — no subscription."

The entire ATS-optimization market sells **monthly subscriptions**: Jobscan (~$49.95/mo),
Teal+ (~$29/mo), Rezi (~$19–49/mo). A job seeker who just got auto-rejected does not
want another recurring bill — they want **this one resume fixed for this one job, right
now.** That is the wedge.

| | Competitors | ATSHacker |
|---|---|---|
| Price | $19–50 / month | **$5 once** |
| Commitment | Subscription | None |
| Promise | "Tools to optimize" | "Fixed resume in 60 seconds" |
| Buyer mindset | Researching | Frustrated, ready to act now |

**Core message pillars (use everywhere):**
1. ~75% of resumes are filtered out by ATS before a human sees them.
2. ATS scores you on *exact* keyword match to the job description ("Adobe Creative
   Cloud" ≠ "Adobe Creative Suite").
3. The job title is the single most important keyword — candidates who include it are
   reportedly ~10x more likely to get an interview.
4. We rewrite your existing resume to mirror the JD's language — honestly, no invented
   experience — for $5.

## 2. Product note that affects marketing (fix before scaling spend)

Many ATS parse **.docx** more reliably than PDF, and some recruiters request .docx.
ATSHacker currently outputs **PDF only**. Before pouring traffic in, consider offering a
**.docx download option** — it removes a real objection and lets you truthfully say
"ATS-friendly .docx + PDF." Don't advertise a benefit the output doesn't deliver.

## 3. Keyword strategy (ranked by intent → effort)

These are grouped by *buyer intent*. High-intent, low-competition long-tails first —
that's where a small site wins.

**Tier 1 — high intent, buy-now (target with landing pages):**
- "[role] resume keywords" (e.g. "software engineer resume keywords")
- "ats resume checker free" / "ats resume scanner"
- "tailor resume to job description"
- "optimize resume for ats"
- "make resume match job description"

**Tier 2 — high intent, problem-aware (target with blog + soft CTA):**
- "why is my resume not getting interviews"
- "applied to 100 jobs no interviews"
- "is workday rejecting my resume"
- "does my resume pass ats"
- "resume getting auto rejected"

**Tier 3 — informational, top-of-funnel (build authority, internal-link to Tier 1):**
- "what is an applicant tracking system"
- "how does workday / greenhouse screen resumes"
- "ats friendly resume format"
- "pdf vs docx resume ats"

**Programmatic SEO (your biggest lever):** the `/tailor/[job-title]` route should become
30–50 unique pages, one per high-volume role, each targeting "[role] resume keywords"
and "ats resume for [role]". Each page needs *unique* copy (role-specific keyword list +
advice) — thin/duplicated pages get ignored or penalized. Priority roles: software
engineer, data analyst, project manager, registered nurse, accountant, marketing manager,
sales rep, mechanical engineer, customer success manager, product manager.

## 4. Funnel & conversion

The highest-leverage growth move isn't more traffic — it's a **free taste**:

> **Free "ATS Match Score":** user pastes JD + uploads resume → instant 0–100 score and
> the top 3 *missing* keywords, free. The full rewrite + download is the $5 unlock.

This converts far better than a cold "pay $5" button because the score *proves the
problem* before asking for money. It's also inherently shareable ("I scored 41/100 😭").
Build this as the front door; every channel below points to it.

Funnel: Channel → free Match Score page → "you're missing 9 keywords" → $5 unlock →
download (PDF + .docx) → post-purchase ask: "tailoring for more roles? 3-pack for $10."

**Economics reality:** $5 once is thin for paid ads. Make organic + the 3-pack/upsell
carry growth first; only test paid after you know the Match-Score→$5 conversion rate.

## 5. Channel playbooks

**A. Programmatic SEO (primary, compounding):** ship the 30–50 role pages; submit a
sitemap; internal-link Tier-3 blog posts → Tier-1 role pages. Compounds for free.

**B. Short-form video (TikTok / Reels / Shorts):** the demo *is* the ad — 20–30s screen
recording: paste JD → keywords light up → score jumps → download. Post daily for 2–3
weeks; job-search content travels fast. CTA: "free score, link in bio."

**C. Reddit / forums (disclosed only):** r/resumes, r/jobs, r/recruitinghell,
r/jobsearchhacks. Build karma with genuinely helpful answers; when relevant, disclose
("full disclosure, I built a $5 tool…") and only link where the sub allows it. One good
launch post per sub beats 50 covert replies — covert promotion gets you and your domain
banned. (This matches the disclosed-reply prompt now in `scraper.py`.)

**D. Email capture:** offer the free Match Score result by email → light nurture for
people who didn't buy on the spot.

## 6. 6-week content calendar

Assumes a solo founder, ~5–7 hrs/week. "Ship" = build/publish; "Post" = social.

| Week | SEO / Product | Content | Social (3–5x/wk) | Community |
|------|---------------|---------|------------------|-----------|
| **1** | Build free **ATS Match Score** front door; add **.docx** output | Blog: "Why you're not getting interviews (it's the ATS)" → Tier-2 | Film 5 demo clips; post 3 | Lurk + answer 3 r/resumes posts (no link) |
| **2** | Ship first **10 /tailor role pages**; submit sitemap | Blog: "ATS-friendly resume format (PDF vs .docx)" → Tier-3 | Post 4 demo/tip clips | Answer 5 posts; build karma |
| **3** | Ship **next 10 role pages**; add internal links blog→role | Blog: "[Role] resume keywords: the 2026 list" (pillar) | Post 4; reuse top clip as ad creative test | **One disclosed launch post** in r/resumes |
| **4** | Ship **final 10–20 role pages** | Blog: "Is Workday auto-rejecting you? How screening works" | Post 4; start a "ATS score reactions" series | Disclosed launch post in r/jobs |
| **5** | Add **3-pack ($10) upsell** + email capture | Guest angle: pitch 2 career newsletters/creators | Post 4; first paid test ($50–100) on best clip | Disclosed post in r/recruitinghell |
| **6** | Fix top drop-off in funnel (analytics) | Refresh weakest blog post; add FAQ schema | Post 4; double down on best-performing format | Recurring "free resume review" comment habit |

## 7. Metrics (review weekly)

Track only what ties to revenue:
- **Match Score completions** (free front-door usage) — top of funnel.
- **Free → $5 conversion rate** — the number that decides if paid ads can ever work.
- **Sales / day** and **revenue / channel** (UTM tags on every link).
- **Organic impressions & clicks** (Google Search Console) per role page.
- **Upsell take rate** (3-pack).
- North-star: **profit per visitor**, not pageviews.

## 8. Guardrails (non-negotiable)

- Disclose creator status everywhere; no astroturfing, fake reviews, or personas.
- Truthful claims only — cite the ~75%/keyword stats, don't invent testimonials.
- Respect each platform's self-promotion rules and rate limits.
- Don't advertise outputs the product doesn't yet deliver (e.g. .docx until shipped).
- Get human approval before publishing, posting, emailing real people, or spending money.
