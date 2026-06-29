# Signal by ATSHacker Web App

Signal is the revenue product for ATSHacker: a free resume-to-job match score that converts high-intent users into one-time paid resume and cover-letter packages.

Primary funnel:

Traffic -> free Signal score -> missing keyword gap -> Stripe checkout -> paid resume/cover letter/bundle -> PDF and DOCX downloads.

## What Exists

- Dark Signal homepage UI in `src/app/page.tsx`.
- Animated Signal mascot in `src/components/SignalMascot.tsx`.
- Free match score API at `src/app/api/score/route.ts`.
- Stripe checkout API at `src/app/api/checkout/route.ts`.
- Paid rewrite/fulfillment API at `src/app/api/rewrite/route.ts`.
- Success/download page at `src/app/success/page.tsx`.
- Shareable score pages at `src/app/s/[score]/page.tsx` plus OG image route at `src/app/api/og/route.tsx`.
- Admin login and Stripe stats at `src/app/admin` and `src/app/api/admin`.
- Programmatic role SEO pages at `src/app/tailor/[job-title]/page.tsx`, powered by `src/data/roles.ts`.

## Local Development

Install dependencies from this folder, then run the dev server:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Useful Commands

```bash
npm run lint
npm run build
```

## Required Environment

- `OPENAI_API_KEY` for scoring and rewrite generation.
- `STRIPE_SECRET_KEY` for checkout and paid session validation.
- `NEXT_PUBLIC_SITE_URL` for canonical links and share URLs.
- `ADMIN_PASSWORD` or the configured admin secret flow for `/admin`.
- Optional Redis REST env vars used by `src/lib/fulfillmentStore.ts` for server-side fulfillment restore.

## Current Roadmap

See the root roadmap status:

- `../BUILD_ROADMAP_STATUS.md`

Highest-priority web work:

- Pre-checkout before/after preview.
- Money-path tests for checkout, rewrite, restore, and downloads.
- Complete funnel analytics from source to purchase.
- Generation quality gates for grounded resume bullets and specific cover letters.
- Expand SEO role pages from 35 to 50+.
