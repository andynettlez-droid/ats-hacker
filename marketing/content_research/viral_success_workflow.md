# Signal Viral Content Workflow

Reviewed: 2026-06-29

## Research Basis

The content system should optimize for audience retention, shareability, trust, and conversion to the free Signal score. Virality cannot be guaranteed, so the workflow defines a professional creator quality bar and a measurement loop.

Primary references:

- YouTube Partner Program eligibility and monetization requirements: https://support.google.com/youtube/answer/72851
- YouTube Analytics retention and engagement metrics: https://support.google.com/youtube/answer/9314355
- YouTube Shorts creator surface: https://www.youtube.com/creators/create/shorts/
- TikTok Creative Center trend discovery: https://ads.tiktok.com/business/creativecenter/
- Pew Research Center social media platform usage context: https://www.pewresearch.org/internet/fact-sheet/social-media/

## Winning Format For ATSHacker

Signal should lead with recruiter-style resume teardowns, not polished SaaS demos.

Best-performing creative lane:

- Cold hook: a painful job-search truth or funny resume roast in the first two seconds.
- Visual proof: resume, job description, missing keywords, weak bullet, rewrite, score movement.
- Tone: blunt, helpful, funny, never cruel to job seekers.
- Product role: Signal is the tool that reveals the mismatch and gives the free next step.
- CTA: free Signal score first, paid resume or bundle only after the viewer understands the gap.

## Professional Creator Gate

Every daily packet must pass before rendering or posting:

- Hook is short, native, and immediately understandable.
- Script contains concrete job language, tools, metrics, and a before/after payoff.
- Storyboard keeps the resume and job description on screen as the main character.
- Humor punches at vague resume language or broken job-search systems, not unemployed people.
- Claims avoid guarantees, fake experience, "trick the ATS" language, and unsupported competitor claims.
- CTA leads to the free Signal score.

Current implementation:

- `marketing_agent/creative_quality_gate.py`
- Pass threshold: overall 85+ and top three shorts pass.
- Day 1 packet currently passes the script gate.
- Studio voiceover and quiet music assets exist for the current three daily shorts.
- Publishing still requires review of the rendered file, caption, CTA, and audio before status changes from `review_required`.

## Daily Production Loop

1. Trend intake:
   - Pull job-search, resume, ATS, AI writing, recruiter advice, layoffs, and hiring friction topics.
   - Source topics from YouTube, TikTok Creative Center, Google Trends, Reddit, LinkedIn, and competitor channels.
   - Save source notes so claims can be traced.

2. Creative packet:
   - One 8 to 10 minute YouTube teardown outline.
   - Three to five short-form scripts.
   - One viewer/customer review.
   - Monetization plan and UTM.

3. Quality gate:
   - Score packet.
   - Reject bland AI copy.
   - Replace generic model output with the recruiter-reacts teardown fallback.

4. Render:
   - Render still frames at hook, problem, payoff, and CTA.
   - Reject overlapping text, mismatched scores, missing mascot, weak contrast, or unreadable mobile text.
   - Render MP4 only after frame QA.

5. Audio:
   - Use studio narration when ElevenLabs is configured.
   - Keep music quiet and on-theme.
   - Avoid harsh whooshes, cartoon impacts, and repetitive SFX.

6. Posting:
   - Queue as `review_required` until both creative gate and render QA pass.
   - Store post status and upload result after posting.

7. Monitoring:
   - Collect views, retention, likes, comments, shares, profile visits, link clicks, score completions, checkout starts, and purchases.
   - Remix winners based on click-to-score and score-to-purchase performance, not vanity views alone.

## Missing For "Extraordinary"

The agent can now produce post-grade script packets, render-ready shorts, studio voiceover assets, a long-form renderer, and a thumbnail renderer. It is still missing:

- Live API-backed trend ingestion instead of file-based source notes.
- Automated frame-level visual QC for rendered clips.
- Automated LUFS/true-peak audio checks.
- Word-level transcript and caption alignment.
- Platform metrics ingestion into `marketing/content_metrics.json`.
- A/B testing of hook frames, captions, and CTAs.
- A final long-form publish package workflow: full render, thumbnail QA, description, chapters, pinned comment, and UTM.

## Monetization Focus

The primary revenue path is:

Social video view -> free Signal score -> resume package or resume plus cover letter bundle.

The videos should not try to monetize through YouTube ads first. A small side income is more likely from converting a narrow set of frustrated job seekers into $9.99 and $14.99 purchases than from ad revenue alone, especially before the channel qualifies for YouTube monetization.
