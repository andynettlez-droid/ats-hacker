# ATSHacker — Launch Strategy & Growth-to-Dashboard Playbook

_Last updated: June 2026_

> **Read first:** this doc builds on `plan.md` (positioning, keyword tiers, channel
> playbooks, 6-week calendar) and `value_pricing_growth_plan.md` (honest value prop,
> $9.99 pricing, the shareable-score viral loop). It does **not** repeat them — it
> sequences the launch, deepens the viral loop, gives a channel-by-channel operating
> playbook, and **maps every growth experiment to a specific KPI on the new
> `/admin` analytics dashboard** (powered by `/api/admin/stats`).

## 0. Honesty guardrail (applies to every line below)

We sell the **true** benefit, never the debunked myth:

- An ATS is a **search-and-rank engine** recruiters use to find candidates by keyword.
  It does **not** auto-reject your resume. Do **not** revive "robots throw out 75%."
- Truthful, still-compelling claims: keyword-matched resumes are roughly **3x more
  likely to surface** to a recruiter; **~90%+ of employers use an ATS**; screening is
  moving to **AI/semantic matching**, so phrasing your experience in the role's
  language genuinely improves ranking.
- Copy verbs: "rank higher," "get seen 3x more," "match the job in 60 seconds" —
  never "beat the robot," "bypass," or "auto-reject."

## 1. The dashboard is the scoreboard

Before launch, the founder logs into `/admin` (gated by `ADMIN_PASSWORD`). Every
experiment below names the **exact metric** to watch there:

| Dashboard metric (`/api/admin/stats`) | What it tells you |
|---|---|
| **Total Revenue** (30d window) | Headline outcome; the only number that pays bills. |
| **Total Sales** (paid checkouts) | Volume of conversions, independent of price tests. |
| **Unique Customers** (distinct emails) | Reach vs. repeat; rising repeat = stickiness/upsell working. |
| **Growth Rate** (vs prior 30d) | Is the launch compounding or fading? |
| **Daily Revenue chart** | Spot the spike from a viral clip / PH launch / Reddit post by date. |
| **Recent Transactions** (date, email, amount, method, status) | Sanity-check live sales; tie a spike to the channel that caused it. |

**Instrumentation gap to close (high priority):** the dashboard reads **Stripe only**,
so it sees *money*, not *traffic*. Pair it with:
- **UTM tags on every link** (`?utm_source=tiktok&utm_campaign=launch`) + Stripe
  Checkout `metadata` carrying the UTM, so a future dashboard column can attribute
  revenue per channel.
- **Free Match-Score completions** and **share rate** (top-of-funnel) tracked in a
  lightweight analytics tool (Plausible/PostHog) — the dashboard only sees the paid
  tail, so funnel math (`score → $9.99`) needs that upstream count.

Until per-channel attribution ships, use the **Daily Revenue chart by date** as the
proxy: launch one channel at a time and read the spike.

## 2. Launch sequence (concrete, T-minus countdown)

This assumes the value items in `value_pricing_growth_plan.md` Tier A are shipped
(before→after score, keyword gap report). Don't launch loudly before the free Match
Score front door exists — it is the conversion engine.

**T-14 → T-8 (foundation):**
- Ship the **shareable score card + dynamic OG image** (the #1 viral feature).
- Add **UTM tagging** + Stripe metadata; confirm `/admin` shows live sales.
- Seed **karma/credibility**: answer 3–5 genuinely helpful posts per target subreddit
  (no link yet). Build the 5–10 short-form clips backlog.
- Stand up email capture for free-score users who don't buy.

**T-7 → T-1 (soft launch / warm-up):**
- Post 1 short-form clip/day; watch which format travels (reactions vs. straight demo).
- Quietly turn on the **$5.99 / $7.99 / $9.99 price test** so you have signal before
  the traffic spike. Dashboard KPI: **Revenue / Total Sales** per arm → revenue/visitor.
- Line up Product Hunt assets (gallery, tagline, first comment) and a Show HN draft.

**T-0 (launch day):**
- **Product Hunt** launch at 12:01am PT + **Show HN** same morning (stagger 2–3 hrs).
- **One disclosed launch post** in the strongest subreddit (r/resumes).
- Push the best-performing warm-up clip across all short-form platforms.
- Watch the **Daily Revenue chart** — the day's bar should visibly jump.

**T+1 → T+14 (compound):**
- Daily clips; one disclosed launch post per subreddit on separate days (so each
  spike is attributable on the chart).
- Recruit first 5–10 affiliates; ship referral ("give a free score, get $3 off").
- Introduce **Job Hunt Pass ($19.99)** once single-price winner is settled —
  watch **Unique Customers** vs **Sales** for AOV lift.

## 3. The shareable-score viral loop (deepened)

Loop (from `value_pricing_growth_plan.md`): free score → emotional result → share →
friends run their own → some convert.

**Make each step measurable and frictionless:**
1. **Trigger:** the score reveal is emotional ("41/100 for this job 😬"). Auto-generate
   a clean **score card image** + **dynamic OG image** so it previews on X/LinkedIn/
   Reddit. One-tap share buttons inline on the result page.
2. **Incentive:** **referral** — "Give a friend a free score, get $3 off your unlock."
   Tracked via `?ref=` param carried into Stripe metadata.
3. **K-factor target:** invites/user × accept rate. You can't see this on the Stripe
   dashboard directly — track shares/score-completions upstream; the dashboard
   confirms the **downstream payoff** via rising **Unique Customers** and **Growth Rate**.
4. **Loop honesty:** the share text states the real benefit ("fixed it to rank higher"),
   never "beat the bot."

**Experiment → KPI:** A/B the share-card copy and the referral discount ($3 vs free
second score). Win condition = higher **Unique Customers** and **Growth Rate** on the
dashboard over a 2-week window, at equal or better **Revenue**.

## 4. Channel-by-channel playbook (each mapped to a dashboard KPI)

### A. Short-form video (TikTok / Reels / Shorts) — primary viral bet
- **Format:** 20–30s screen recording — paste JD → keywords light up → score jumps
  41→86 → download. The before→after *is* the ad.
- **Cadence:** 1/day for 3 weeks; test 3 hooks (shock score, "applied to 100 jobs,"
  role-specific "software engineer resume keywords").
- **CTA:** "Free score, link in bio" → free Match Score page (UTM `source=tiktok`).
- **Dashboard KPI:** **Daily Revenue chart** spikes on post days for winning clips;
  **Total Sales** trend over the 3 weeks. Cut formats that don't move the chart.

### B. Programmatic SEO — compounding base (from plan.md §5A)
- Expand `/tailor/[role]` to **50+ roles**, each with unique keyword list + advice;
  submit sitemap; internal-link Tier-3 blog → Tier-1 role pages.
- **Dashboard KPI:** slow, durable rise in **Total Revenue** and **Growth Rate** with
  no paid spend; corroborate with Search Console impressions per role page.

### C. Disclosed Reddit / forums — credibility, not volume
- r/resumes, r/jobs, r/recruitinghell, r/jobsearchhacks, r/cscareerquestions.
- **One disclosed launch post per sub**, on **separate days** so each is attributable
  on the Daily Revenue chart. Lead with help; disclose ("full disclosure, I built a
  $9.99 tool"); link only where allowed. Covert promotion = domain ban — never do it.
- **Dashboard KPI:** isolated bar on the **Daily Revenue chart** the day of each post;
  **Unique Customers** bump.

### D. Product Hunt / Show HN — launch-day spikes
- PH: ship gallery + crisp tagline ("Rank higher in recruiter search for $9.99 — no
  subscription"), seed the first comment, rally a few honest early users.
- Show HN: technical, honest framing ("I built a $9.99 resume keyword optimizer — here's
  what the ATS actually does"). Expect debate; engage truthfully.
- **Dashboard KPI:** the sharpest single-day **Daily Revenue** spike; watch
  **Recent Transactions** in real time to confirm conversions, not just traffic.

### E. Referrals — turn buyers into a loop (see §3)
- "Give a friend a free score, get $3 off." `?ref=` → Stripe metadata.
- **Dashboard KPI:** **Unique Customers** rising faster than ad/clip cadence implies;
  **Growth Rate** sustained between launch spikes.

### F. Affiliates / creators — borrowed audiences
- Career coaches, "tech TikTok," university career centers, bootcamps. Offer an
  affiliate cut or bulk free codes for graduating cohorts (high-intent, time-of-need).
- Give each affiliate a unique UTM/code → Stripe metadata for later per-affiliate
  attribution.
- **Dashboard KPI:** **Total Sales** lift on affiliate-active days; once attribution
  ships, revenue-per-affiliate; **Unique Customers** growth from net-new audiences.

## 5. Experiment → KPI matrix (the operating table)

Run these one at a time where possible so the **Daily Revenue chart** can attribute each.

| # | Experiment | Hypothesis | Primary dashboard KPI | Win condition |
|---|---|---|---|---|
| 1 | Price A/B/C ($5.99/$7.99/$9.99) | Higher charm price lifts revenue/visitor | Total Revenue ÷ Total Sales per arm | Highest revenue/visitor arm wins |
| 2 | Shareable score card + OG image | Sharing drives net-new buyers | Unique Customers, Growth Rate | Both rise vs pre-launch baseline |
| 3 | Referral ($3 off vs free 2nd score) | Incentive raises invite accept rate | Unique Customers, Growth Rate | Sustained growth between spikes |
| 4 | Short-form clip formats (3 hooks) | One hook travels far better | Daily Revenue spikes on post days | Keep formats that move the chart |
| 5 | Disclosed Reddit launch (per sub) | High-intent communities convert | Daily Revenue bar that day | Clear isolated spike + customers |
| 6 | PH / Show HN launch day | One-time spike seeds reviews/backlinks | Single-day Daily Revenue peak | Largest day in window |
| 7 | Job Hunt Pass ($19.99) upsell | Anchors single price, lifts AOV | Total Revenue with flat/△ Sales | Revenue up at similar sales count |
| 8 | Programmatic SEO (50 roles) | Compounding organic revenue | Growth Rate trend (no spend) | Rising baseline over weeks |

**Weekly review ritual:** open `/admin`, read Total Revenue + Growth Rate, scan the
Daily Revenue chart for the week's spikes, reconcile spikes to the channel that ran,
and double down on what moved the chart. Kill anything that didn't.

## 6. Guardrails (carry over from plan.md §8, non-negotiable)

- Disclose creator status everywhere; no astroturfing, fake reviews, or personas.
- Truthful claims only — "rank higher / get seen 3x more," never "auto-reject."
- Respect each platform's self-promotion rules and rate limits.
- Don't advertise outputs the product doesn't deliver.
- Get human approval before publishing, posting, emailing real people, or spending money.
- The `/admin` dashboard exposes revenue — keep `ADMIN_PASSWORD` secret; never paste
  financial screenshots publicly.
