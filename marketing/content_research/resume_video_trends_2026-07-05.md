# Resume Video Trend Research - 2026-07-05

Status: active input for the Signal video pipeline overhaul.

## Sources Reviewed

- YouTube Blog, "Your guide to getting started with YouTube Shorts" (2025-04-08): Shorts must capture attention in the first few seconds, stay vertical, use clear titles/descriptions/hashtags, stay consistent, and keep testing what resonates. https://blog.youtube/creator-and-artist-stories/your-guide-to-getting-started-with-youtube-shorts/
- TikTok Newsroom, "Find a job with TikTok Resumes" (2021-07-07): career and job-related creative content is a real TikTok subculture; short creative videos work when they feel authentic, specific, and useful. https://newsroom.tiktok.com/find-a-job-with-tiktok-resumes?lang=en
- Business Insider, "I'm a former recruiter turned content creator..." (2026-06-22): recruiter-led creator authority works because it sounds like candidate coaching, not a SaaS pitch; the useful lens is what a recruiter would actually notice or miss. https://www.businessinsider.com/former-recruiter-shares-advice-resumes-networking-strategies-2026-6
- Business Insider, "The simple resume template a career expert recommends for the AI era" (2026-07-04): resumes should be marketing documents, not career histories; bullets need value, measurable outcomes, and context. https://www.businessinsider.com/career-expert-shares-resume-template-for-ai-era-2026-6
- The Guardian, "Instagram truly is the new LinkedIn" (2026-05-28): job seekers are using social content because the market feels brutal; videos that travel are bold, funny, personal, and emotionally specific. https://www.theguardian.com/money/2026/may/28/gen-z-using-social-media-in-struggling-job-market
- People, "Man Reviews Resume for Scott Kelly at Jonas Brothers Concert" (2026-05-28): a resume moment went viral because it was a human situation first, public rooting interest second, and resume content third. https://people.com/man-reviews-resume-scott-kelly-jonas-brothers-concert-11847418
- Public Shorts search sweep, 2026-07-05: current resume Shorts cluster around recruiter scans, "what recruiters actually check", "this resume looks fine but fails", AI resume review tools, and resume format warnings. Strong examples show a visible artifact immediately.
- Public Reels/TikTok/LinkedIn search sweep, 2026-07-05: high-performing job-search content leans on creator personality, candidate frustration, "read this line with me", and one practical correction instead of broad education.

## Trend Findings

1. Human situation beats product demo.
   The viewer needs to feel "a real person is looking at a real resume" before Signal appears. Product UI is a payoff, not the opening frame.

2. One problem beats three tips.
   The strongest short-form structure is one visible line, one job requirement, one reason it misses, one honest rewrite.

3. The score cannot be a magic number.
   A score reveal only works after the viewer has seen why the original line was weak: missing tool, missing metric, missing outcome, buried proof, or wrong job-language.

4. The job seeker must be protected.
   The comedy should roast vague bullets, AI sameness, recruiter skimming pressure, and job-search absurdity. It should not make unemployed people the joke.

5. Resume visuals need to look professional.
   If the resume looks fake or toy-like, the whole teardown feels AI-generated. The document should look like a plausible one-page resume with real sections, skills, dates, and credible employer placeholders.

6. Creator voice matters more than perfect narration.
   A slightly imperfect "I am reading this line" delivery is more believable than clean corporate TTS. Scratch-read speech-to-speech should become the preferred audio path.

7. Search and scan mechanics are native to the niche.
   Ctrl+F tests, recruiter skim tests, job-post answer-key highlights, and red-marker notes feel closer to existing recruiter/career content than animated SaaS explainers.

## What Signal Should Copy

- Cold open on the artifact: resume or job post visible in frame one.
- First-person reviewer language: "I would circle this", "I search React", "this line makes me guess".
- A tiny dramatic situation: "I am screening this for a frontend job", "I searched the resume", "the job post gave the answer key".
- One visible source of proof already on the resume, then move that proof to the weak bullet.
- Score movement explained in plain human language before the score appears.
- Fast CTA: "Run the free Signal score before you apply."

## What Signal Should Avoid

- Generic AI SaaS narration.
- HubSpot/CAC/Demand Gen defaults unless the selected resume is genuinely a marketing case.
- Repeated hooks such as "this resume is invisible" without a fresh situation.
- Meme slang that sounds generated rather than creator-native.
- "The rubric gives..." narration.
- Telling viewers an ATS automatically rejects them.
- Showing Signal mascot as the main presenter.
- Dark neon visuals on every short.

## Pipeline Implications

### Research Stage

Every daily packet must carry a `trendResearch` object summarizing:

- `humanPremise`: the human situation the viewer enters immediately.
- `platformPattern`: recruiter reacts, resume roast, search test, job-description translation, or one-bullet fix.
- `copyFromResearch`: the specific source-backed mechanic being copied.
- `avoid`: the failure mode being avoided.

### Script Stage

Scripts must be 18-32 seconds and read like a person reviewing a resume aloud:

1. Human premise hook.
2. Exact weak resume line.
3. One job requirement or search term.
4. Plain reason the original line scores low.
5. Visible source proof already on the resume.
6. Honest rewrite using that proof.
7. Plain reason the score improves.
8. Fast free-score CTA.

### Art Direction Stage

Rotate at least three distinct visual series before rendering a daily batch:

- Desk Markup: paper resume, job post, red pen, sticky note.
- Recruiter Search Console: search box, highlight misses, rerun search after rewrite.
- Answer-Key Highlighter: job post on one side, resume on the other, highlighted required terms.
- Evidence Board: proof cards, source line, rewritten bullet.
- Social POV: phone-screen/job-hunter panic only when the script begins with a human situation.

### Audio Stage

Preferred: scratch human read -> ElevenLabs speech-to-speech -> timestamp captions.

Fallback: ElevenLabs multi-take TTS with creator delivery settings, selected by pacing and alignment quality.

Hard fail: monotone corporate read, awkward rubric narration, or repeated templated phrasing.

