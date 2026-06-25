# ATSHacker — Value, Pricing ($9.99) & Growth Plan

_Last updated: June 2026_

## 1. Does it genuinely help? (Honest assessment)

**The uncomfortable truth:** the product's current core claim — "Stop getting auto-rejected by robots," "90% of resumes are thrown out by ATS before a human sees them" — is **largely a myth.** In recruiter studies, ~92% say their ATS does **not** auto-reject resumes; the "75% auto-rejected" stat traces back to a defunct vendor and has been repeatedly debunked. An ATS is mostly a **search-and-rank engine** for recruiters, plus "knockout" questions (visa, hard requirements). It rarely throws your resume in the trash by itself.

**But here's what IS true — and where the product creates real value:**

- 90%+ of employers use an ATS, and recruiters **search and rank** candidates by keywords.
- Keyword-optimized resumes are roughly **3x more likely to surface** to a recruiter for the same posting.
- **88% of employers** believe they lose qualified candidates who didn't use the right keywords/format.
- Screening is shifting to **AI/semantic matching** (BERT-style models that map "client relations" ≈ "customer success"), so phrasing your experience in the role's language genuinely improves your ranking.

**Conclusion:** The product genuinely helps — not by "beating a robot that rejects you," but by making a resume **rank higher in recruiter search and read better to both AI and humans.** That's a real, defensible benefit. The fix is to **stop selling the myth and start selling the truth.** Honest framing also protects against refunds, chargebacks, and reputational/legal risk as we raise the price.

### Action: rewrite the value proposition (do this first)
- Replace "Stop getting auto-rejected by robots" / "90% thrown out" with truthful, still-compelling copy, e.g.:
  - "Recruiters find candidates by keyword. We rewrite your resume to rank higher and read better — for both the AI screener and the human."
  - "3x more likely to get seen. Match your resume to the job in 60 seconds."
- Drop "Bypass Workday & Greenhouse Filters" (implies defeating a system) → "Optimized for how Workday & Greenhouse rank candidates."
- Keep the honesty guardrails already in the rewrite API (no fabricated/inflated credentials).

## 2. Product improvements (these justify $9.99)

Don't raise the price on the current deliverable. Raise it **after** the perceived value goes up. Prioritized:

**Tier A — prove the value (do before price change)**
1. **Show before → after score.** On the result page, display "Match score: 41 → 86." Tangible ROI is the single biggest driver of willingness to pay. (You already have `/api/score`; run it on the optimized text too.)
2. **Deliver the keyword gap report** with the resume: matched keywords, the ones that were missing and are now added. Makes the work visible.
3. **ATS-readability check.** Flag real parsing killers the research actually supports: multi-column layouts, text inside images/graphics, tables, non-standard section headings, weird fonts, missing dates. Output a short checklist with pass/fail. This is genuine, honest value.
4. **.docx + PDF output** (already shipped) — keep, and label "ATS-safe .docx."

**Tier B — depth & stickiness**
5. **Quantification coach:** suggest where to add metrics ("led a team" → "led a team of 6"). Honest prompts only.
6. **Cover letter generator** matched to the same JD — natural bundle/upsell.
7. **Re-tailor for multiple jobs:** one purchase = N tailorings for 30 days (drives the value of a higher price and repeat use; job seekers apply to dozens).
8. **Money-back guarantee:** "We'll raise your match score or refund you." Cheap to honor (the score check already exists), and it removes purchase risk at $9.99.

**Tier C — trust**
9. Social proof: collect opt-in testimonials + before/after score screenshots.
10. Light account/email so users can return to their results without re-paying.

## 3. Pricing plan: move $5 → $9.99

**Why it's justified:** every competitor sells subscriptions — Jobscan ~$49.95/mo, Teal+ ~$29/mo, Rezi ~$19–49/mo. A **one-time $9.99 with no subscription** is still dramatically cheaper and removes recurring-bill friction. $9.99 is a classic charm-price with much better unit economics than $5 (paid ads, fees, and refunds are far more survivable).

**How to do it (test, don't guess):**
1. **A/B/C price test:** randomly serve $5.99 / $7.99 / $9.99. Optimize for **revenue per visitor** (conversion × price), not conversion alone. Stripe makes this a one-line `unit_amount` change (599/799/999).
2. **Package the ladder:**
   - Single tailoring — **$9.99**
   - "Job Hunt Pass" — unlimited tailorings + cover letters for 30 days — **$19.99** (anchors the single price and lifts average order value)
   - 3-pack — **$14.99** (for the occasional applier)
3. **Anchor the price in copy:** "Less than the cost of one coffee per application — competitors charge $30–50/month."
4. **Support the price with:** the before/after score, the guarantee, and visible social proof. Price increases stick when perceived value and trust rise with them.
5. **Optional:** purchasing-power pricing by country later (Stripe + a geo lookup) to widen the global market.

**Sequencing:** ship Tier A value items → flip on the A/B price test → settle on the winner → introduce the Job Hunt Pass.

## 4. Getting it viral / into customers' hands

The product has a built-in viral mechanic if you lean into it: **the free score is shareable and emotional.**

**The core loop:** free score → shocking/satisfying result → share → friends run their own score → some convert to $9.99.

**Build the loop:**
1. **Shareable score card.** After the free score, generate a clean image ("My resume scored 41/100 for this job 😬 — fixed it with ATSHacker") with a dynamic OG image so it previews well on X/LinkedIn/Reddit. Add one-tap share buttons. This is the highest-leverage viral feature.
2. **Referral:** "Give a friend a free score, get $3 off." Tracked via a referral param.

**Distribution channels (ranked by fit):**
1. **Short-form video (TikTok/Reels/Shorts)** — the before→after score jump is the perfect 20-second demo. Post daily; job-search content travels. This is the most likely path to a genuine viral moment.
2. **Programmatic SEO** (already built: `/tailor/[role]` + sitemap) — expand to 50+ roles; compounding free traffic on "[role] resume keywords."
3. **Reddit/communities, disclosed** — r/resumes, r/jobs, r/jobsearchhacks, r/recruitinghell, r/cscareerquestions. One genuinely helpful, clearly self-disclosed launch post per sub. Never covert (it gets the domain banned and is dishonest).
4. **Launch platforms:** Product Hunt + Hacker News "Show HN." One-time spikes that seed reviews/backlinks.
5. **Creator/affiliate partnerships:** career coaches, "tech TikTok," university career centers, bootcamps. Give them an affiliate cut or free codes for their audience.
6. **Campus & bootcamp deals:** bulk codes for graduating cohorts — high-intent users at the exact moment of need.
7. **Email capture + nurture** for free-score users who didn't buy.

**Honesty note for all channels:** because we're correcting the value prop to be truthful, marketing should emphasize "rank higher / get seen 3x more," not "beat the robot." It's both more durable and more defensible.

## 5. Sequenced roadmap

**Weeks 1–2 (value + truth):** rewrite landing copy to honest framing; ship before→after score + keyword gap report on the result page; add money-back guarantee.

**Weeks 3–4 (price + share):** build the shareable score card + OG image; turn on the $5.99/$7.99/$9.99 A/B test; add referral.

**Weeks 5–6 (distribution):** daily short-form video; expand programmatic SEO to 50 roles; one disclosed launch post per subreddit; Product Hunt/Show HN.

**Weeks 7–8 (scale what works):** introduce Job Hunt Pass ($19.99) + cover letters; recruit 5–10 affiliates; double down on the best-performing channel.

## 6. Metrics that matter
- Free score completions (top of funnel) and **share rate**.
- **Revenue per visitor** (the number the price test optimizes).
- Free → paid conversion; refund rate (watch after price change).
- Organic traffic per role page (Search Console).
- Average score lift delivered (proof the product works) — and your guarantee's payout rate.
