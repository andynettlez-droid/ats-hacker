# Plugin Capability Inventory

Reviewed: 2026-07-05

## Installed Capability Groups

- Browser and Chrome control: inspect live pages, verify mobile/local review links, capture browser-state issues.
- Remotion: deterministic programmatic videos, captions, audio, and render QA.
- HeyGen: avatar and presenter video generation for occasional human-anchor clips.
- Canva: branded thumbnails, social variants, presentation-style creative assets.
- GitHub: repo, commit, PR, and CI workflow support.
- Google Drive, Docs, Sheets, Slides: content calendars, review docs, analytics sheets, and pitch decks.
- Gmail, Outlook, Calendar: communications and scheduling workflows if needed.
- Stripe: checkout and revenue-flow implementation/review.
- Cloudflare: Workers, Durable Objects, remote agents, MCP servers, web performance, and deployment patterns.
- Data Analytics: KPI/report/dashboard work for channel and funnel performance.
- Airtable: structured content calendar or creative pipeline base.
- Twilio and SendGrid: email/SMS flows, compliance, transactional notifications, and outreach plumbing.
- Sentry: production issue review.
- Codex Security: security scan, threat model, and finding validation.
- Hyperframes: website-to-motion/animation utilities.
- Computer-use: Windows app control when connector/browser control is not enough.

## Highest-Leverage Uses For Signal

- Use Remotion for the daily deterministic video renderer and approval gates.
- Use HeyGen sparingly for long-form intros or creator-anchor segments, not as the default short.
- Use Canva for thumbnail systems and social-format variants after a short is approved.
- Use Data Analytics plus Google Sheets or Airtable to track hooks, topics, watch time, clicks, and paid conversions.
- Use Cloudflare Workers/Durable Objects if the marketing/content agents need durable autonomous scheduling outside the local repo.
- Use Stripe tools for offer/pricing tests and checkout reliability.
- Use GitHub tools for pushing clean pipeline changes and tracing deployment state.

## Current Decision

The gold-standard short lane should remain Remotion-first. HeyGen can help later for a recognizable human/mascot presence, but the resume teardown itself should stay artifact-first so it does not become another generic AI presenter ad.
