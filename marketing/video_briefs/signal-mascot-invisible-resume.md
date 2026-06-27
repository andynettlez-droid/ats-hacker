# Signal Mascot Video Brief: Invisible Resume

## Goal

Create a 20-30 second short-form video using the new Signal mascot and the existing HeyGen + Remotion pipeline.

Tone: urgent, helpful, premium, honest.

Guardrails:

- Do not claim an ATS auto-rejects candidates.
- Do not promise interviews, callbacks, offers, or jobs.
- Do not use "beat the bots" framing.
- Do not imply Signal invents experience.

## Hook

Your resume might be invisible.

## A/B Hook

Qualified, but not matching?

## Voiceover

Your resume is not being rejected by a robot. But it may be hard to find when recruiters search for job-specific language. Signal by ATSHacker reads the role, spots missing keywords and proof points, then helps rewrite your bullets around what you actually did. No fake experience. Just a clearer match.

## Storyboard

| Time | Visual | On-screen text |
| --- | --- | --- |
| 0-2s | Resume floats in a dark search interface with faint recruiter query lines passing by. | Your resume might be invisible. |
| 2-6s | ATS/search dashboard scans job language and highlights missing role terms. | Not rejected. Just hard to find. |
| 6-10s | Electric-blue atomic Signal mascot enters, orbit rings glowing, friendly expression. | Meet Signal. |
| 10-16s | Job description terms stream into the resume: SQL, stakeholder reporting, workflow automation, metrics. | Match the role language. |
| 16-22s | Weak bullet transforms into a sharper evidence-backed bullet. | No fake experience. |
| 22-27s | Match score rises from 38 to 91 while checklist lights up. | Clearer job match. |
| 27-30s | Brand lockup with mascot pulse and CTA. | Signal by ATSHacker. Check your score. |

## Remotion Props Candidate

```json
{
  "hook1": "Resume invisible?",
  "hook2": "Check the match.",
  "subline": "Recruiters search resumes by job-description language before deeper review.",
  "beforeScore": 38,
  "afterScore": 91,
  "missing": ["SQL", "workflow automation", "stakeholder reporting", "metrics"],
  "cta": "Check your score free. Link in bio",
  "voiceover_text": "Your resume is not being rejected by a robot. But it may be hard to find when recruiters search for job-specific language. Signal by ATSHacker reads the role, spots missing keywords and proof points, then helps rewrite your bullets around what you actually did. No fake experience. Just a clearer match.",
  "avatarVideoUrl": "avatar.mp4"
}
```

## Caption JSON

```json
[
  {
    "text": "Your resume is not being rejected by a robot.",
    "startMs": 0,
    "endMs": 3200,
    "timestampMs": 0,
    "confidence": null
  },
  {
    "text": "But it may be hard to find when recruiters search for job-specific language.",
    "startMs": 3200,
    "endMs": 7800,
    "timestampMs": 3200,
    "confidence": null
  },
  {
    "text": "Signal reads the role, spots missing keywords and proof points,",
    "startMs": 7800,
    "endMs": 12400,
    "timestampMs": 7800,
    "confidence": null
  },
  {
    "text": "then helps rewrite your bullets around what you actually did.",
    "startMs": 12400,
    "endMs": 17000,
    "timestampMs": 12400,
    "confidence": null
  },
  {
    "text": "No fake experience. Just a clearer match.",
    "startMs": 17000,
    "endMs": 21000,
    "timestampMs": 17000,
    "confidence": null
  }
]
```

## Social Caption

Qualified but not showing up in searches? Signal by ATSHacker helps match your real experience to the job description, without fake claims or ATS myths. Check your score free.

## Hashtags

`#jobsearch #resumehelp #careeradvice #ats #resumetips #jobseekers #SignalByATSHacker #ATSHacker`

## Pipeline Commands

Use the curated short-form viral preset with the new HeyGen Signal mascot avatar:

```powershell
Set-Location -LiteralPath "C:\Users\andyn\.gemini\antigravity\scratch\ats_hacker\marketing_agent"

& "C:\Users\andyn\AppData\Local\Programs\Python\Python313\python.exe" .\video_pipeline.py --viral --avatar 0d5e54203dad4b9ea61abb618676d9bf
```

Use GPT topic generation with the same mascot:

```powershell
Set-Location -LiteralPath "C:\Users\andyn\.gemini\antigravity\scratch\ats_hacker\marketing_agent"

& "C:\Users\andyn\AppData\Local\Programs\Python\Python313\python.exe" .\video_pipeline.py --topic "Signal by ATSHacker honest resume match check using job-description language, no auto-reject myths, no job guarantees, no fake experience" --avatar 0d5e54203dad4b9ea61abb618676d9bf
```

For the existing full Signal reveal template:

```powershell
Set-Location -LiteralPath "C:\Users\andyn\.gemini\antigravity\scratch\ats_hacker\marketing_agent"

& "C:\Users\andyn\AppData\Local\Programs\Python\Python313\python.exe" .\video_pipeline.py --signal --avatar 0d5e54203dad4b9ea61abb618676d9bf
```

Dry run the curated viral preset:

```powershell
Set-Location -LiteralPath "C:\Users\andyn\.gemini\antigravity\scratch\ats_hacker\marketing_agent"

& "C:\Users\andyn\AppData\Local\Programs\Python\Python313\python.exe" .\video_pipeline.py --viral --avatar 0d5e54203dad4b9ea61abb618676d9bf --dry-run
```
