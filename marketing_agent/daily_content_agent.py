import argparse
import base64
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from creative_quality_gate import score_packet, score_short

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency in local dry runs
    OpenAI = None


ROOT = Path(__file__).resolve().parents[1]
MARKETING_DIR = ROOT / "marketing"
BRIEFS_DIR = MARKETING_DIR / "video_briefs"
PACKETS_DIR = MARKETING_DIR / "daily_content"
REMOTION_DIR = MARKETING_DIR / "remotion"
REMOTION_PUBLIC_DIR = REMOTION_DIR / "public"
REMOTION_AUDIO_DIR = REMOTION_PUBLIC_DIR / "audio"
CALENDAR_PATH = MARKETING_DIR / "content_calendar.json"
TREND_INTAKE_PATH = MARKETING_DIR / "content_research" / "trend_intake_latest.json"
TREND_RESEARCH_BRIEF_PATH = MARKETING_DIR / "content_research" / "resume_video_trends_2026-07-05.md"
HIGH_VIEW_SWIPE_PATH = MARKETING_DIR / "content_research" / "high_view_resume_video_swipe_2026-07-05.md"
DEFAULT_ELEVENLABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
LEGACY_ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
ELEVENLABS_VOICE_CACHE: dict | None = None
ELEVENLABS_DISABLED_REASON: str | None = None


TREND_RESEARCH_CONTRACT = {
    "humanPremise": "A recruiter-style reviewer is reading one resume line against one visible job requirement in real time.",
    "platformPattern": "recruiter reacts / resume teardown / search test",
    "copyFromResearch": (
        "Open on the resume or job post immediately; use first-person reviewer language; "
        "show one weak line, one visible source of proof, and one honest rewrite."
    ),
    "avoid": (
        "AI SaaS demo pacing, generic ATS fear, old marketing-tool defaults, rubric-first narration, "
        "and score jumps that appear before the viewer sees why."
    ),
    "researchBrief": str(TREND_RESEARCH_BRIEF_PATH.relative_to(ROOT)),
    "benchmarkUrls": [
        "https://www.youtube.com/watch?v=VDFgGi-lrD0",
        "https://www.youtube.com/watch?v=veFlfYjRo1Y",
    ],
    "borrowedMechanic": "expert red-pen teardown plus recruiter search test",
    "whyThisMechanicFits": (
        "High-view resume videos win when a human reviews a visible resume artifact, "
        "reacts to one exact flaw, then proves the fix with evidence."
    ),
    "whatNotToCopy": (
        "Do not copy creator likeness, exact wording, or generic list-video pacing; "
        "adapt only the artifact-first review mechanic."
    ),
    "highViewSwipeFile": str(HIGH_VIEW_SWIPE_PATH.relative_to(ROOT)),
}


TREND_RESEARCH_SOURCE_NOTES = [
    {
        "title": "Resume video trend research brief",
        "url": "marketing/content_research/resume_video_trends_2026-07-05.md",
        "note": "Local swipe-file synthesis for human-first resume teardown, recruiter reacts, search-test, and voice/art-direction rules.",
    },
    {
        "title": "High-view resume video swipe file",
        "url": "marketing/content_research/high_view_resume_video_swipe_2026-07-05.md",
        "note": "Point-in-time benchmark sweep of highly viewed resume, recruiter, job-search, and resume-mistake videos.",
    },
    {
        "title": "YouTube Shorts official guide",
        "url": "https://blog.youtube/creator-and-artist-stories/your-guide-to-getting-started-with-youtube-shorts/",
        "note": "Use vertical video, capture attention in the first few seconds, keep clips short, and iterate through analytics.",
    },
    {
        "title": "TikTok Resumes / CareerTok reference",
        "url": "https://newsroom.tiktok.com/find-a-job-with-tiktok-resumes?lang=en",
        "note": "Career/job content works when short videos are creative, authentic, and useful.",
    },
    {
        "title": "Former recruiter creator advice",
        "url": "https://www.businessinsider.com/former-recruiter-shares-advice-resumes-networking-strategies-2026-6",
        "note": "Recruiter-led creator authority works when the advice sounds like candidate coaching, not a product pitch.",
    },
    {
        "title": "2026 resume template advice",
        "url": "https://www.businessinsider.com/career-expert-shares-resume-template-for-ai-era-2026-6",
        "note": "Resumes should act like marketing documents with value, measurable outcomes, and context, not career-history dumps.",
    },
    {
        "title": "Gen Z social job-search trend",
        "url": "https://www.theguardian.com/money/2026/may/28/gen-z-using-social-media-in-struggling-job-market",
        "note": "Bold, funny, personal social content travels because job seekers feel brutal market pressure and want human specificity.",
    },
]


TREND_SEEDS = [
    {
        "topic": "AI resumes all sound the same, so recruiters search for proof",
        "series": "Recruiter Search Test",
        "thesis": "AI-written resumes can look polished while still missing the exact role language and proof recruiters search for.",
        "hook": "Your AI resume sounds professional. That might be the problem.",
        "keywords": ["AI resume", "recruiter search", "proof points", "job description"],
        "source_notes": TREND_RESEARCH_SOURCE_NOTES,
    },
    {
        "topic": "Same resume, different job, totally different Signal score",
        "series": "Job Description Translation",
        "thesis": "A resume is not universally good or bad; it either matches the target job language or it does not.",
        "hook": "This resume is not bad. It is aimed at the wrong job.",
        "keywords": ["job description", "resume score", "role language", "keywords"],
        "source_notes": [
            {
                "title": "YouTube Shorts discovery help",
                "url": "https://support.google.com/youtube/answer/10059070",
                "note": "Shorts can reach viewers through multiple discovery surfaces.",
            }
        ],
    },
    {
        "topic": "Resume builder subscriptions versus one targeted application package",
        "series": "Resume Builder Cost Trap",
        "thesis": "Many job seekers do not need another monthly resume tool; they need one targeted package for the job they are applying to right now.",
        "hook": "Stop paying monthly for a resume you only need to tailor today.",
        "keywords": ["resume builder", "subscription", "one-time payment", "job application"],
        "source_notes": [
            {
                "title": "Signal offer ladder",
                "url": "marketing/plan.md",
                "note": "Keep pricing claims current before naming competitors.",
            }
        ],
    },
    {
        "topic": "The ATS auto-reject myth versus recruiter search reality",
        "series": "ATS Myth Lab",
        "thesis": "The trustworthy angle is not fear of robots; it is explaining how resumes are parsed, indexed, searched, and reviewed.",
        "hook": "The ATS probably did not throw your resume away. Here is the real problem.",
        "keywords": ["ATS myth", "recruiter search", "resume parser", "keyword match"],
        "source_notes": [
            {
                "title": "Signal positioning guardrails",
                "url": "marketing/plan.md",
                "note": "Avoid unsupported auto-reject claims.",
            }
        ],
    },
]


ENTERTAINMENT_RULES = [
    "Open with a visible human review situation in the first 1.5 seconds: a resume line, job post, search box, or reviewer markup.",
    "Make the viewer feel a real person is reading the resume before Signal appears.",
    "Keep the resume/job description on screen as the main character; Signal mascot is the mischievous guide, not a corporate presenter.",
    "Use blunt recruiter-reacts energy: read the weak line, explain the miss, then rescue the person.",
    "Every joke must punch at the broken job-search process or vague resume language, never at unemployed people.",
    "Explain the score with visible factors before showing the score jump.",
    "End with a calm paid bridge: free score first, bundle only after the gap is obvious.",
]


VIRAL_FORMATS = [
    "Resume Crime Scene",
    "ATS Myth Lab",
    "Job Description Translation",
    "One Bullet Fix",
    "Recruiter Search Test",
    "AI Resume Roast",
    "Resume Builder Cost Trap",
    "Signal Mascot Rescue",
]


SHORT_STYLE_ROTATION = [
    {
        "creativeFormat": "aiResumeRoast",
        "visualStyle": "comic",
        "pace": "fast",
        "seriesLabel": "AI resume roast",
        "signalLines": {
            "hook": "This smells generated.",
            "problem": "Pretty. Still invisible.",
            "teardown": "Roast the bullet, rescue the human.",
            "fix": "Receipts found.",
            "cta": "Run the score first.",
        },
    },
    {
        "creativeFormat": "oneBulletFix",
        "visualStyle": "highlighter",
        "pace": "fast",
        "seriesLabel": "One bullet fix",
        "signalLines": {
            "hook": "One sentence is sinking this.",
            "problem": "Too vague to search.",
            "teardown": "Give me tools, scope, result.",
            "fix": "That is a real signal.",
            "cta": "Fix before applying.",
        },
    },
    {
        "creativeFormat": "atsMythLab",
        "visualStyle": "terminal",
        "pace": "balanced",
        "seriesLabel": "ATS myth lab",
        "signalLines": {
            "hook": "Mind-reading not installed.",
            "problem": "It can only parse what you wrote.",
            "teardown": "Search terms are missing.",
            "fix": "Now the proof is searchable.",
            "cta": "Test the match.",
        },
    },
    {
        "creativeFormat": "jobSearchTest",
        "visualStyle": "terminal",
        "pace": "slowBurn",
        "seriesLabel": "Recruiter search test",
        "signalLines": {
            "hook": "Would this show up?",
            "problem": "The JD is giving clues.",
            "teardown": "The resume ignores them.",
            "fix": "Translate, do not fabricate.",
            "cta": "Paste the JD.",
        },
    },
    {
        "creativeFormat": "mascotRescue",
        "visualStyle": "neon",
        "pace": "fast",
        "seriesLabel": "Signal rescue",
        "signalLines": {
            "hook": "I found the hidden proof.",
            "problem": "It is buried under corporate fog.",
            "teardown": "Let me pull it out.",
            "fix": "Much better.",
            "cta": "I will roast yours nicely.",
        },
    },
]

ENTERTAINMENT_MARKERS = [
    "screening",
    "i would circle",
    "i searched",
    "i search",
    "read this line",
    "makes me guess",
    "not mad",
    "proof is lower",
    "answer key",
    "ctrl",
    "score this low",
    "now i can see",
]


WEAK_GENERATED_PHRASES = [
    "can your ai resume do the talking",
    "wanna discover",
    "genius at vague buzzwords",
    "magical wand",
    "training their resumes like puppies",
    "glossy ai resumes",
    "misfits and clashing design",
    "pet goldfish",
    "happy job hunters",
    "agency statistics",
    "not-so-professional truth",
    "boring conference",
    "with a twist of comedy",
    "messy office interactions",
    "don't worry, it",
    "same person",
    "better signal",
    "same experience, clearer proof",
]

TEARDOWN_CASES = [
    {
        "id": "data_analyst",
        "resumeName": "Jordan Lee",
        "resumeTitle": "Data Analyst Resume",
        "resumeMeta": ["3 yrs analytics", "SQL + dashboards", "Customer churn reporting"],
        "jobTitle": "Product Data Analyst",
        "jobKeywords": ["SQL", "Tableau", "cohort analysis", "churn dashboard", "stakeholder insights"],
        "weakBullets": [
            "Created reports for business teams and leadership.",
            "Worked with data to help teams understand customer trends.",
            "Helped maintain dashboards for weekly performance meetings.",
        ],
        "beforeBullet": "Created reports for business teams and leadership.",
        "afterBullet": "Built SQL churn dashboard in Tableau that cut weekly reporting by 6 hours and flagged 18 at-risk customer accounts.",
        "beforeScore": 32,
        "afterScore": 89,
        "markedLabel": "Too vague",
        "scoreBasis": [
            {"label": "Search terms", "before": "reports", "after": "SQL + Tableau"},
            {"label": "Metric proof", "before": "missing", "after": "6 hrs saved"},
            {"label": "Business result", "before": "vague", "after": "18 risks found"},
        ],
        "shortTitle": "This data resume makes the recruiter guess",
        "hook": "This data bullet makes me do detective work.",
        "subhook": "The job needs SQL proof, not report-flavored fog.",
        "problemPunchline": "Reports is a folder name, not a selling point.",
        "teardownIssues": ["No SQL signal", "No dashboard tool", "No business result"],
        "evidenceLedger": {
            "sourceLocation": "Northstar Analytics experience, later dashboard bullet",
            "proofLine": "Built a Tableau churn tracker that saved six hours a week and flagged 18 at-risk customer accounts.",
            "visibleFacts": [
                {"fact": "SQL", "source": "skills section"},
                {"fact": "Tableau", "source": "skills section and dashboard bullet"},
                {"fact": "6 hours saved weekly", "source": "later dashboard bullet"},
                {"fact": "18 at-risk customer accounts", "source": "later dashboard bullet"},
                {"fact": "customer churn", "source": "skills section"},
            ],
        },
    },
    {
        "id": "sales_account_exec",
        "resumeName": "Maya Torres",
        "resumeTitle": "Account Executive Resume",
        "resumeMeta": ["4 yrs SaaS sales", "Mid-market accounts", "Quota-carrying role"],
        "jobTitle": "Mid-Market Account Executive",
        "jobKeywords": ["Salesforce", "pipeline generation", "quota attainment", "discovery calls", "MEDDICC"],
        "weakBullets": [
            "Managed customer conversations and followed up with prospects.",
            "Responsible for sales opportunities in assigned territory.",
            "Worked with marketing and customer success on accounts.",
        ],
        "beforeBullet": "Responsible for sales opportunities in assigned territory.",
        "afterBullet": "Generated $1.8M in qualified Salesforce pipeline through 42 monthly discovery calls and MEDDICC-based account prioritization.",
        "beforeScore": 37,
        "afterScore": 88,
        "markedLabel": "Missing proof",
        "scoreBasis": [
            {"label": "Search terms", "before": "0 strong", "after": "Salesforce + pipeline"},
            {"label": "Revenue proof", "before": "missing", "after": "$1.8M"},
            {"label": "Method", "before": "vague", "after": "MEDDICC"},
        ],
        "shortTitle": "This sales resume forgot to say sales",
        "hook": "This sales resume has conversations. The job needs pipeline.",
        "subhook": "Salesforce, discovery, quota, and MEDDICC are missing on screen.",
        "problemPunchline": "Sales resumes need numbers faster than adjectives.",
        "teardownIssues": ["No quota proof", "No CRM signal", "No pipeline number"],
        "evidenceLedger": {
            "sourceLocation": "BrightLedger experience, later pipeline bullet",
            "proofLine": "Generated $1.8M in qualified Salesforce pipeline through 42 monthly discovery calls and MEDDICC account notes.",
            "visibleFacts": [
                {"fact": "Salesforce", "source": "skills section and later pipeline bullet"},
                {"fact": "$1.8M qualified pipeline", "source": "later pipeline bullet"},
                {"fact": "42 monthly discovery calls", "source": "later pipeline bullet"},
                {"fact": "MEDDICC", "source": "skills section and later pipeline bullet"},
                {"fact": "pipeline generation", "source": "skills section"},
            ],
        },
    },
    {
        "id": "frontend_engineer",
        "resumeName": "Avery Patel",
        "resumeTitle": "Frontend Engineer Resume",
        "resumeMeta": ["5 yrs product UI", "React/TypeScript", "Accessibility fixes"],
        "jobTitle": "Frontend Software Engineer",
        "jobKeywords": ["React", "TypeScript", "Next.js", "accessibility", "performance"],
        "weakBullets": [
            "Worked on frontend features for internal and customer-facing tools.",
            "Collaborated with designers and backend engineers.",
            "Helped improve application performance and user experience.",
        ],
        "beforeBullet": "Worked on frontend features for internal and customer-facing tools.",
        "afterBullet": "Shipped React and TypeScript checkout components in Next.js, reducing form drop-off 14% and closing 11 accessibility issues.",
        "beforeScore": 41,
        "afterScore": 90,
        "markedLabel": "Too broad",
        "scoreBasis": [
            {"label": "Stack match", "before": "hidden", "after": "React + TS + Next"},
            {"label": "Feature proof", "before": "broad", "after": "checkout"},
            {"label": "Result", "before": "missing", "after": "drop-off -14%"},
        ],
        "shortTitle": "This developer resume hides the stack",
        "hook": "This developer resume says frontend. The job searches React.",
        "subhook": "The stack and impact are the search signal.",
        "problemPunchline": "Engineering resumes need proof of stack plus outcome.",
        "teardownIssues": ["Stack is vague", "No shipped feature", "No performance result"],
        "evidenceLedger": {
            "sourceLocation": "MapleStack experience, later checkout bullet",
            "proofLine": "Shipped React and TypeScript checkout components in Next.js, reduced form drop-off 14%, and closed 11 WCAG issues.",
            "visibleFacts": [
                {"fact": "React", "source": "skills section and later checkout bullet"},
                {"fact": "TypeScript", "source": "skills section and later checkout bullet"},
                {"fact": "Next.js", "source": "skills section and later checkout bullet"},
                {"fact": "14% form drop-off reduction", "source": "later checkout bullet"},
                {"fact": "11 accessibility issues", "source": "later checkout bullet"},
            ],
        },
    },
    {
        "id": "project_manager",
        "resumeName": "Chris Morgan",
        "resumeTitle": "Project Manager Resume",
        "resumeMeta": ["7 yrs operations", "Agile delivery", "Cross-functional rollout"],
        "jobTitle": "Technical Project Manager",
        "jobKeywords": ["Jira roadmap", "risk register", "stakeholder updates", "budget variance", "Agile delivery"],
        "weakBullets": [
            "Managed project timelines and coordinated team priorities.",
            "Led meetings with stakeholders and tracked action items.",
            "Helped deliver projects on time and within scope.",
        ],
        "beforeBullet": "Managed project timelines and coordinated team priorities.",
        "afterBullet": "Owned Jira roadmap and weekly risk register for a 9-person rollout, reducing schedule variance from 18% to 6%.",
        "beforeScore": 39,
        "afterScore": 87,
        "markedLabel": "Missing delivery proof",
        "scoreBasis": [
            {"label": "Tool match", "before": "missing", "after": "Jira roadmap"},
            {"label": "Delivery proof", "before": "broad", "after": "risk register"},
            {"label": "Result", "before": "missing", "after": "variance 18% -> 6%"},
        ],
        "shortTitle": "This PM resume is organized but not searchable",
        "hook": "This project manager resume looks organized. It still misses the job.",
        "subhook": "Jira, risk, stakeholders, and variance need to show up.",
        "problemPunchline": "PM bullets should prove delivery, not just calendar ownership.",
        "teardownIssues": ["No Jira signal", "No risk language", "No variance result"],
        "evidenceLedger": {
            "sourceLocation": "SummitOps experience, later rollout bullet",
            "proofLine": "Owned a Jira roadmap and weekly risk register for a 9-person rollout, reducing schedule variance from 18% to 6%.",
            "visibleFacts": [
                {"fact": "Jira roadmap", "source": "skills section and later rollout bullet"},
                {"fact": "weekly risk register", "source": "later rollout bullet"},
                {"fact": "9-person rollout", "source": "later rollout bullet"},
                {"fact": "18% to 6% schedule variance", "source": "later rollout bullet"},
                {"fact": "stakeholder updates", "source": "skills section"},
            ],
        },
    },
    {
        "id": "customer_success",
        "resumeName": "Sam Rivera",
        "resumeTitle": "Customer Success Manager Resume",
        "resumeMeta": ["6 yrs B2B accounts", "Renewal risk", "QBR owner"],
        "jobTitle": "Customer Success Manager",
        "jobKeywords": ["Gainsight", "renewal risk", "QBRs", "NPS", "net revenue retention"],
        "weakBullets": [
            "Helped customers with product questions and account needs.",
            "Built relationships with customers to improve satisfaction.",
            "Partnered with sales on renewals and expansion opportunities.",
        ],
        "beforeBullet": "Helped customers with product questions and account needs.",
        "afterBullet": "Flagged renewal risk in Gainsight and ran QBR follow-ups that protected $420K ARR across 18 customer accounts.",
        "beforeScore": 36,
        "afterScore": 89,
        "markedLabel": "Missing retention proof",
        "scoreBasis": [
            {"label": "Platform", "before": "missing", "after": "Gainsight"},
            {"label": "Revenue proof", "before": "missing", "after": "$420K ARR"},
            {"label": "Scope", "before": "vague", "after": "18 accounts"},
        ],
        "shortTitle": "This customer success resume forgot the renewal story",
        "hook": "This CSM resume sounds helpful. The job needs retention proof.",
        "subhook": "Gainsight, QBRs, NPS, and renewal risk are the clues.",
        "problemPunchline": "Helpful is nice. Retention proof gets searched.",
        "teardownIssues": ["No renewal metric", "No platform signal", "No account scope"],
        "evidenceLedger": {
            "sourceLocation": "Beaconly experience, later renewal-risk bullet",
            "proofLine": "Flagged renewal risk in Gainsight and ran QBR follow-ups that protected $420K ARR across 18 customer accounts.",
            "visibleFacts": [
                {"fact": "Gainsight", "source": "skills section and later renewal-risk bullet"},
                {"fact": "QBR follow-ups", "source": "later renewal-risk bullet"},
                {"fact": "$420K ARR protected", "source": "later renewal-risk bullet"},
                {"fact": "18 customer accounts", "source": "later renewal-risk bullet"},
                {"fact": "renewal risk", "source": "skills section"},
            ],
        },
    },
    {
        "id": "healthcare_rn",
        "resumeName": "Taylor Brooks",
        "resumeTitle": "Registered Nurse Resume",
        "resumeMeta": ["5 yrs acute care", "Epic documentation", "Discharge planning"],
        "jobTitle": "Clinical Care Coordinator",
        "jobKeywords": ["Epic", "patient education", "care coordination", "discharge planning", "HCAHPS"],
        "weakBullets": [
            "Provided patient care and supported daily clinical operations.",
            "Communicated with families and members of the care team.",
            "Assisted with discharge paperwork and patient instructions.",
        ],
        "beforeBullet": "Assisted with discharge paperwork and patient instructions.",
        "afterBullet": "Coordinated Epic discharge plans and patient education for a 24-bed unit, reducing avoidable follow-up calls 21%.",
        "beforeScore": 40,
        "afterScore": 86,
        "markedLabel": "Too generic",
        "scoreBasis": [
            {"label": "System", "before": "missing", "after": "Epic"},
            {"label": "Care scope", "before": "generic", "after": "24-bed unit"},
            {"label": "Result", "before": "missing", "after": "calls -21%"},
        ],
        "shortTitle": "This nursing resume buries care coordination",
        "hook": "This nursing resume says patient care. The role asks coordination.",
        "subhook": "Epic, discharge planning, and education need to be visible.",
        "problemPunchline": "Clinical proof has to be specific and careful.",
        "teardownIssues": ["No Epic signal", "No discharge scope", "No patient education result"],
        "evidenceLedger": {
            "sourceLocation": "Lakeside Medical Center experience, later discharge-planning bullet",
            "proofLine": "Coordinated Epic discharge plans and patient education for a 24-bed unit, reducing avoidable follow-up calls 21%.",
            "visibleFacts": [
                {"fact": "Epic", "source": "skills section and later discharge-planning bullet"},
                {"fact": "patient education", "source": "later discharge-planning bullet"},
                {"fact": "24-bed unit", "source": "later discharge-planning bullet"},
                {"fact": "21% fewer avoidable follow-up calls", "source": "later discharge-planning bullet"},
                {"fact": "discharge planning", "source": "skills section"},
            ],
        },
    },
]


GENERIC_RESUME_TERMS = {
    "ai-polished resume",
    "target job description",
    "results-driven team player",
    "helped with marketing campaigns",
    "worked with cross-functional teams",
    "role language",
    "tools",
    "metrics",
}

CASE_SERIES_ROTATION = [
    "Resume Crime Scene",
    "Recruiter Search Test",
    "Job Description Translation",
    "One Bullet Fix",
    "ATS Myth Lab",
    "Resume Crime Scene",
]

CASE_HUMOR_LINES = {
    "data_analyst": "I believe the work happened; I just cannot see the proof yet.",
    "sales_account_exec": "The sales work may be there; the pipeline proof is not.",
    "frontend_engineer": "The stack is probably real, but the bullet makes me hunt for it.",
    "project_manager": "The calendar is visible. The delivery result is not.",
    "customer_success": "Helpful is not enough here; I need retention evidence.",
    "healthcare_rn": "The care coordination is buried under generic clinical language.",
}

CASE_SPOKEN_REWRITES = {
    "data_analyst": "built a SQL churn dashboard that saved six hours a week and flagged 18 at-risk accounts",
    "sales_account_exec": "generated 1.8 million in qualified Salesforce pipeline",
    "frontend_engineer": "shipped React and TypeScript checkout work that reduced drop-off 14 percent",
    "project_manager": "owned the Jira roadmap and cut schedule variance to 6 percent",
    "customer_success": "flagged renewal risk and protected 420 thousand in ARR",
    "healthcare_rn": "coordinated Epic discharge plans and reduced avoidable follow-up calls",
}


def case_evidence_ledger(case: dict) -> dict:
    ledger = case.get("evidenceLedger")
    if isinstance(ledger, dict):
        return ledger
    return {
        "sourceLocation": "resume artifact",
        "proofLine": case.get("afterBullet", ""),
        "visibleFacts": [],
    }


def evidence_blob(case: dict) -> str:
    ledger = case_evidence_ledger(case)
    facts = ledger.get("visibleFacts") if isinstance(ledger.get("visibleFacts"), list) else []
    fact_text = " ".join(
        " ".join(str(item.get(key, "")) for key in ("fact", "source"))
        for item in facts
        if isinstance(item, dict)
    )
    return " ".join([
        str(ledger.get("sourceLocation", "")),
        str(ledger.get("proofLine", "")),
        fact_text,
        " ".join(str(item) for item in case.get("jobKeywords", [])),
    ]).lower()


def validate_case_rewrite_evidence(case: dict) -> None:
    ledger = case_evidence_ledger(case)
    facts = ledger.get("visibleFacts") if isinstance(ledger.get("visibleFacts"), list) else []
    if len(facts) < 3 or not ledger.get("proofLine") or not ledger.get("sourceLocation"):
        raise ValueError(f"Case {case['id']} needs visible evidenceLedger facts before script generation.")

    rewrite = str(case.get("afterBullet", ""))
    evidence = evidence_blob(case)
    numeric_claims = re.findall(r"(?:\$?\d+(?:\.\d+)?\s?(?:m|k|%|percent)?|\d+\s?-\s?person)", rewrite.lower())
    unsupported = [claim.strip() for claim in numeric_claims if claim.strip() and claim.strip() not in evidence]
    if unsupported:
        raise ValueError(f"Case {case['id']} rewrite has unsupported numeric claims: {unsupported}")


def evidence_summary(case: dict) -> str:
    ledger = case_evidence_ledger(case)
    facts = ledger.get("visibleFacts") if isinstance(ledger.get("visibleFacts"), list) else []
    fact_names = [str(item.get("fact", "")).strip() for item in facts if isinstance(item, dict) and item.get("fact")]
    return "; ".join(fact_names[:5])


def compact_proof_line(case: dict) -> str:
    proof = str(case_evidence_ledger(case).get("proofLine") or case.get("afterBullet", "")).strip()
    return proof.rstrip(".") + "."

CASE_SCORE_RUBRICS = {
    "data_analyst": [
        ("Job keyword/tool match", 25, 8, 23, "Only says reports", "SQL and Tableau are explicit"),
        ("Measurable proof", 20, 2, 18, "No number", "6 hours saved"),
        ("Outcome clarity", 20, 4, 17, "Leadership benefit is vague", "18 at-risk accounts flagged"),
        ("Scope/context", 15, 7, 13, "Audience only", "Churn dashboard scope"),
        ("Role alignment", 15, 8, 14, "Analytics implied", "Product analytics fit"),
        ("Formatting/readability", 5, 3, 4, "Readable but generic", "Readable and specific"),
    ],
    "sales_account_exec": [
        ("Job keyword/tool match", 25, 7, 23, "No Salesforce or MEDDICC", "Salesforce and MEDDICC appear"),
        ("Measurable proof", 20, 3, 18, "No quota or dollars", "$1.8M pipeline"),
        ("Outcome clarity", 20, 5, 17, "Sales result unclear", "Qualified pipeline result"),
        ("Scope/context", 15, 8, 13, "Territory only", "42 monthly discovery calls"),
        ("Role alignment", 15, 11, 13, "Sales role is visible", "Mid-market AE signal"),
        ("Formatting/readability", 5, 3, 4, "Readable but thin", "Readable and specific"),
    ],
    "frontend_engineer": [
        ("Job keyword/tool match", 25, 9, 24, "Frontend only", "React, TypeScript, Next.js"),
        ("Measurable proof", 20, 4, 18, "No metric", "14 percent drop-off reduction"),
        ("Outcome clarity", 20, 7, 18, "Feature work is broad", "Checkout impact is clear"),
        ("Scope/context", 15, 8, 13, "Internal/customer tools", "Checkout components"),
        ("Role alignment", 15, 10, 13, "Engineer fit implied", "Frontend role match"),
        ("Formatting/readability", 5, 3, 4, "Readable but generic", "Readable and specific"),
    ],
    "project_manager": [
        ("Job keyword/tool match", 25, 8, 22, "No Jira or risk terms", "Jira roadmap and risk register"),
        ("Measurable proof", 20, 3, 17, "No delivery metric", "Variance 18 to 6 percent"),
        ("Outcome clarity", 20, 6, 17, "Coordination only", "Schedule variance improved"),
        ("Scope/context", 15, 8, 13, "Team context missing", "9-person rollout"),
        ("Role alignment", 15, 11, 14, "PM fit is visible", "Technical PM fit"),
        ("Formatting/readability", 5, 3, 4, "Readable but generic", "Readable and specific"),
    ],
    "customer_success": [
        ("Job keyword/tool match", 25, 7, 23, "No Gainsight or QBR", "Gainsight and QBR follow-up"),
        ("Measurable proof", 20, 3, 18, "No ARR number", "$420K ARR protected"),
        ("Outcome clarity", 20, 5, 17, "Satisfaction is vague", "Renewal risk protected"),
        ("Scope/context", 15, 7, 13, "Customers are generic", "18 customer accounts"),
        ("Role alignment", 15, 11, 14, "CSM fit implied", "Retention role fit"),
        ("Formatting/readability", 5, 3, 4, "Readable but generic", "Readable and specific"),
    ],
    "healthcare_rn": [
        ("Job keyword/tool match", 25, 8, 22, "No Epic or coordination", "Epic and discharge planning"),
        ("Measurable proof", 20, 4, 17, "No care metric", "Calls reduced 21 percent"),
        ("Outcome clarity", 20, 6, 16, "Paperwork only", "Follow-up burden reduced"),
        ("Scope/context", 15, 8, 13, "Instructions only", "24-bed unit"),
        ("Role alignment", 15, 11, 14, "Clinical fit is visible", "Care coordinator fit"),
        ("Formatting/readability", 5, 3, 4, "Readable but generic", "Readable and specific"),
    ],
}

def build_score_rubric(case: dict) -> dict:
    rows = [
        {
            "criterion": criterion,
            "label": criterion,
            "max": max_score,
            "before": before,
            "after": after,
            "beforeReason": before_reason,
            "afterReason": after_reason,
        }
        for criterion, max_score, before, after, before_reason, after_reason in CASE_SCORE_RUBRICS.get(case["id"], [])
    ]
    before_total = sum(int(row["before"]) for row in rows)
    after_total = sum(int(row["after"]) for row in rows)
    return {
        "label": "Signal Fit Score",
        "scale": 100,
        "beforeTotal": before_total,
        "afterTotal": after_total,
        "rows": rows,
        "beforeExplanation": "The original line forces the reviewer to infer tools, scope, and outcome.",
        "afterExplanation": "The rewrite puts the job terms, metric proof, and outcome on the page.",
    }


def score_basis_from_rubric(score_rubric: dict) -> list[dict]:
    rows = score_rubric.get("rows") if isinstance(score_rubric, dict) else []
    basis = []
    for row in rows[:4]:
        if isinstance(row, dict):
            basis.append({
                "label": str(row.get("criterion") or row.get("label") or ""),
                "before": str(row.get("beforeReason") or row.get("before") or ""),
                "after": str(row.get("afterReason") or row.get("after") or ""),
            })
    return basis


def build_human_read_beats(case: dict, playbook: dict, score_rubric: dict) -> list[dict]:
    context = case_template_context(case)
    before_total = score_rubric.get("beforeTotal", case["beforeScore"])
    after_total = score_rubric.get("afterTotal", case["afterScore"])
    ledger = case_evidence_ledger(case)
    return [
        {
            "beat": "read_line",
            "text": f"Read the exact resume line: {context['beforeBullet']}",
        },
        {
            "beat": "natural_reaction",
            "text": CASE_HUMOR_LINES.get(case["id"], "I believe the work happened; I cannot see the proof yet."),
        },
        {
            "beat": "source_evidence",
            "text": f"Point to the visible source evidence in {ledger.get('sourceLocation')}: {ledger.get('proofLine')}",
        },
        {
            "beat": "job_requirement",
            "text": f"Compare it to the job requirement: {context['kw1']}, {context['kw2']}, {context['kw3']}.",
        },
        {
            "beat": "score_reason",
            "text": f"Explain the visible rubric before the score: {before_total}/100.",
        },
        {
            "beat": "rewrite",
            "text": f"Rewrite only the same experience: {context['spokenRewrite']}.",
        },
        {
            "beat": "score_improvement",
            "text": f"Explain what improved before showing {after_total}/100.",
        },
    ]


CREATOR_FORMAT_PLAYBOOKS = [
    {
        "id": "recruiter_roast",
        "series": "Live Resume Review",
        "composition": "ResumeDeskReview",
        "creativeFormat": "resumeCrimeScene",
        "visualStyle": "stickyNote",
        "formatArchetype": "deskMarkup",
        "pace": "fast",
        "title": "I would circle this line first",
        "hook": "I would circle this line first.",
        "subhook": "The line sounds normal until you compare it to the job.",
        "voiceover": (
            "Okay, circle this line: {beforeBullet} "
            "Normal sentence, but I cannot see {kw1}, {kw2}, or a result. "
            "I would score that low because it makes me guess. "
            "Rewrite it: {spokenRewrite}. "
            "Now I can see the tool, scope, and outcome. That is why the score can move to {afterScore}. "
            "Run the free Signal score before you apply."
        ),
        "storyboard": [
            "Open on the resume as if a reviewer is reading it at a desk.",
            "Circle the exact weak line: {beforeBullet}",
            "Place the job description beside it with {kw1}, {kw2}, and {kw3} highlighted.",
            "Show the Signal Fit Score rubric before the score reveal.",
            "Rewrite the line in-place using only the real work.",
            "Reveal the score after the low-score rationale is visible.",
        ],
        "signalLines": {
            "hook": "Circle this.",
            "problem": "The proof is hidden.",
            "teardown": "Name the work clearly.",
            "fix": "Now I can read it.",
            "cta": "Check before sending.",
        },
        "problemPunchline": "The work may be real. The evidence is not readable.",
        "teardownPunchline": "Low score reason: the rubric cannot find tool, metric, or result.",
        "fixPunchline": "A recruiter should not have to infer the proof.",
    },
    {
        "id": "search_console",
        "series": "Recruiter Search Test",
        "composition": "ResumeDeskReview",
        "creativeFormat": "jobSearchTest",
        "visualStyle": "terminal",
        "formatArchetype": "recruiterSearch",
        "pace": "fast",
        "title": "I searched the resume. Bad news.",
        "hook": "I searched the resume. Bad news.",
        "subhook": "This is the search test most vague bullets fail.",
        "voiceover": (
            "Here is my Ctrl F test. I search {kw1}. Nothing useful. "
            "{kw2}? Still thin. "
            "Then I read: {beforeBullet} "
            "Real work, but I am guessing, so I would score it low. "
            "I would rewrite it: {spokenRewrite}. "
            "Now the search terms and proof are on the page. That is why it moves to {afterScore}. "
            "Run the free Signal score before you apply."
        ),
        "storyboard": [
            "Open on a reviewer search box over the resume, searching for {kw1}.",
            "Show the weak bullet that does not include the searched language.",
            "Search {kw2} and show the miss again.",
            "Show the Signal Fit Score rubric before the score reveal.",
            "Rewrite the bullet and rerun the search with a visible match.",
            "Close after the low-score rationale explains the jump.",
        ],
        "signalLines": {
            "hook": "Search missed it.",
            "problem": "Do not make them guess.",
            "teardown": "Use the real term.",
            "fix": "Now it is findable.",
            "cta": "Search-test it first.",
        },
        "problemPunchline": "A reviewer cannot search for what you meant to say.",
        "teardownPunchline": "The low score is from hidden tool and result proof in the rubric.",
        "fixPunchline": "Now the search term points to real evidence.",
    },
    {
        "id": "answer_key",
        "series": "Job Description Review",
        "composition": "ResumeDeskReview",
        "creativeFormat": "oneBulletFix",
        "visualStyle": "highlighter",
        "formatArchetype": "splitTranslation",
        "pace": "fast",
        "title": "The job post gave the answer key",
        "hook": "The job post gave the answer key.",
        "subhook": "The resume just did not answer it clearly.",
        "voiceover": (
            "Job post: {kw1}, {kw2}, {kw3}. "
            "Resume line: {beforeBullet} "
            "See the gap? The answer key is right there, but the resume answered too vaguely. "
            "I would write: {spokenRewrite}. "
            "Now the tool, metric, and outcome are visible. That is why it moves to {afterScore}. "
            "Run the free Signal score before you apply."
        ),
        "storyboard": [
            "Open on the job post with {kw1}, {kw2}, and {kw3} highlighted.",
            "Slide to the resume line and circle the mismatch.",
            "Show the Signal Fit Score rubric before the score reveal.",
            "Rewrite the line without inventing anything.",
            "Reveal the rewritten bullet and then the score movement.",
            "End with the free Signal score CTA.",
        ],
        "signalLines": {
            "hook": "Read the posting.",
            "problem": "The answer is vague.",
            "teardown": "Translate. Do not exaggerate.",
            "fix": "Now the proof matches.",
            "cta": "Paste the job first.",
        },
        "problemPunchline": "The role language is visible. The resume is not using it.",
        "teardownPunchline": "Low score reason: broad work, missing tool, no result.",
        "fixPunchline": "Use the job language only when the experience supports it.",
    },
]

CASE_RESUME_DETAILS = {
    "data_analyst": {
        "contact": ["Austin, TX", "jordan.lee@example.com", "linkedin.com/in/jordan-lee"],
        "summary": "Data analyst with 3 years building recurring reports, dashboard views, and customer trend analysis for product and revenue teams.",
        "skills": ["SQL", "Tableau", "Excel", "Customer churn", "Cohort analysis", "Data cleaning", "Stakeholder reporting"],
        "education": "B.S. Business Analytics, University of Texas at Austin",
        "experience": [
            {
                "company": "Northstar Analytics",
                "role": "Data Analyst",
                "dates": "2023 - Present",
                "bullets": [
                    "Created reports for business teams and leadership.",
                    "Worked with data to help teams understand customer trends.",
                    "Helped maintain dashboards for weekly performance meetings.",
                    "Built a Tableau churn tracker that saved six hours a week and flagged 18 at-risk customer accounts.",
                    "Cleaned product usage exports and sent weekly insights to customer success.",
                ],
            },
            {
                "company": "CedarCloud Software",
                "role": "Junior Operations Analyst",
                "dates": "2021 - 2023",
                "bullets": [
                    "Updated Excel trackers for sales, onboarding, and support activity.",
                    "Partnered with product managers to validate monthly account health data.",
                    "Reduced duplicate customer records by 17% through spreadsheet QA and CRM cleanup.",
                ],
            },
        ],
    },
    "sales_account_exec": {
        "contact": ["Chicago, IL", "maya.torres@example.com", "linkedin.com/in/maya-torres"],
        "summary": "Quota-carrying SaaS seller with 4 years across SDR and AE roles, focused on discovery, account prioritization, CRM hygiene, and mid-market pipeline creation.",
        "skills": ["Salesforce", "MEDDICC", "Discovery calls", "Pipeline generation", "Outbound sequencing", "Forecasting", "Mutual action plans"],
        "education": "B.S. Business Administration, DePaul University",
        "experience": [
            {
                "company": "BrightLedger",
                "role": "Account Executive",
                "dates": "2024 - Present",
                "bullets": [
                    "Managed customer conversations and followed up with prospects.",
                    "Responsible for sales opportunities in assigned territory.",
                    "Worked with marketing and customer success on accounts.",
                    "Maintained Salesforce notes, next steps, and close-date updates for active opportunities.",
                    "Generated $1.8M in qualified Salesforce pipeline through 42 monthly discovery calls and MEDDICC account notes.",
                ],
            },
            {
                "company": "Pinecone Workflow",
                "role": "Sales Development Representative",
                "dates": "2021 - 2024",
                "bullets": [
                    "Booked discovery meetings with operations and finance leaders.",
                    "Researched account triggers and personalized outbound email sequences.",
                    "Qualified inbound leads and routed opportunities to three AE teams.",
                ],
            },
        ],
    },
    "frontend_engineer": {
        "contact": ["Seattle, WA", "avery.patel@example.com", "github.com/averypatel"],
        "summary": "Frontend engineer with 5 years building product UI, design-system components, checkout flows, and accessibility improvements for SaaS products.",
        "skills": ["React", "TypeScript", "Next.js", "Design systems", "WCAG", "Performance profiling", "Playwright"],
        "education": "B.S. Computer Science, University of Washington",
        "experience": [
            {
                "company": "MapleStack",
                "role": "Frontend Engineer",
                "dates": "2022 - Present",
                "bullets": [
                    "Worked on frontend features for internal and customer-facing tools.",
                    "Collaborated with designers and backend engineers.",
                    "Helped improve application performance and user experience.",
                    "Maintained shared React components used by billing, onboarding, and account teams.",
                    "Shipped React and TypeScript checkout components in Next.js, reduced form drop-off 14%, and closed 11 WCAG issues.",
                ],
            },
            {
                "company": "OrbitCart",
                "role": "UI Developer",
                "dates": "2019 - 2022",
                "bullets": [
                    "Converted Figma designs into responsive TypeScript UI components.",
                    "Triaged customer-reported accessibility issues with QA and support.",
                    "Added Playwright regression coverage for checkout and profile flows.",
                ],
            },
        ],
    },
    "project_manager": {
        "contact": ["Denver, CO", "chris.morgan@example.com", "linkedin.com/in/chris-morgan"],
        "summary": "Project manager with 7 years coordinating technical rollouts, stakeholder updates, sprint ceremonies, delivery risks, and cross-functional operating rhythms.",
        "skills": ["Jira", "Risk registers", "Stakeholder updates", "Agile delivery", "Budget variance", "Roadmaps", "Vendor coordination"],
        "education": "PMP, Project Management Institute; B.A. Operations Management",
        "experience": [
            {
                "company": "SummitOps",
                "role": "Project Manager",
                "dates": "2022 - Present",
                "bullets": [
                    "Managed project timelines and coordinated team priorities.",
                    "Led meetings with stakeholders and tracked action items.",
                    "Helped deliver projects on time and within scope.",
                    "Prepared weekly Jira status summaries for engineering, product, and operations leaders.",
                    "Owned a Jira roadmap and weekly risk register for a 9-person rollout, reducing schedule variance from 18% to 6%.",
                ],
            },
            {
                "company": "Clearpath Logistics",
                "role": "Operations Coordinator",
                "dates": "2018 - 2022",
                "bullets": [
                    "Tracked vendor dependencies and updated rollout schedules.",
                    "Coordinated implementation notes across warehouse and IT teams.",
                    "Created issue logs for launch risks, owners, and resolution dates.",
                ],
            },
        ],
    },
    "customer_success": {
        "contact": ["Raleigh, NC", "sam.rivera@example.com", "linkedin.com/in/sam-rivera"],
        "summary": "Customer success manager with 6 years supporting B2B accounts, QBRs, renewal conversations, onboarding follow-up, and customer health reporting.",
        "skills": ["Gainsight", "QBRs", "Renewal risk", "NPS", "ARR retention", "Onboarding", "Expansion handoff"],
        "education": "B.A. Communications, North Carolina State University",
        "experience": [
            {
                "company": "HelioDesk",
                "role": "Customer Success Manager",
                "dates": "2021 - Present",
                "bullets": [
                    "Helped customers with product questions and account needs.",
                    "Built relationships with customers to improve satisfaction.",
                    "Partnered with sales on renewals and expansion opportunities.",
                    "Maintained Gainsight health notes and QBR follow-up tasks for strategic accounts.",
                    "Flagged renewal risk in Gainsight and ran QBR follow-ups that protected $420K ARR across 18 customer accounts.",
                ],
            },
            {
                "company": "BlueRiver Support",
                "role": "Implementation Specialist",
                "dates": "2018 - 2021",
                "bullets": [
                    "Guided new customers through onboarding milestones and training calls.",
                    "Documented common product questions for customer education materials.",
                    "Escalated account risks to support, product, and success leadership.",
                ],
            },
        ],
    },
    "healthcare_rn": {
        "contact": ["Columbus, OH", "taylor.brooks@example.com", "linkedin.com/in/taylor-brooks"],
        "summary": "Registered nurse with 5 years in acute-care environments, Epic documentation, patient education, discharge planning, and interdisciplinary care coordination.",
        "skills": ["Epic", "Discharge planning", "Patient education", "Care coordination", "HCAHPS", "Medication reconciliation", "Family communication"],
        "education": "B.S.N., Ohio State University; RN License, Ohio",
        "experience": [
            {
                "company": "Lakeside Medical Center",
                "role": "Registered Nurse",
                "dates": "2021 - Present",
                "bullets": [
                    "Provided patient care and supported daily clinical operations.",
                    "Communicated with families and members of the care team.",
                    "Assisted with discharge paperwork and patient instructions.",
                    "Documented care plans, medication changes, and patient education in Epic.",
                    "Coordinated Epic discharge plans and patient education for a 24-bed unit, reducing avoidable follow-up calls 21%.",
                ],
            },
            {
                "company": "Riverbend Health",
                "role": "Clinical Nurse",
                "dates": "2019 - 2021",
                "bullets": [
                    "Supported care transitions for post-acute patient follow-up.",
                    "Coordinated provider updates during shift handoffs.",
                    "Reviewed discharge checklists with patients and family caregivers.",
                ],
            },
        ],
    },
}


def build_professional_resume_document(case: dict) -> dict:
    details = CASE_RESUME_DETAILS.get(case["id"], {})
    experience = details.get("experience") or [
        {
            "company": "Fictional Company",
            "role": case["resumeTitle"].replace(" Resume", ""),
            "dates": "2022 - Present",
            "bullets": case["weakBullets"],
        }
    ]
    return {
        "name": case["resumeName"],
        "headline": case["resumeTitle"].replace(" Resume", ""),
        "contact": details.get("contact", ["Remote", "candidate@example.com", "linkedin.com/in/candidate"]),
        "summary": details.get(
            "summary",
            f"Professional with experience aligned to {case['jobTitle']}, including role-specific tools, collaboration, and measurable delivery.",
        ),
        "experience": experience,
        "skills": details.get("skills", case["jobKeywords"]),
        "education": details.get("education", "B.A. Business Administration, State University"),
    }


def build_realistic_job_description(case: dict) -> dict:
    keyword_a, keyword_b, keyword_c = case["jobKeywords"][:3]
    return {
        "title": case["jobTitle"],
        "company": "TargetCo",
        "summary": f"TargetCo is hiring a {case['jobTitle']} who can connect practical execution with measurable business outcomes.",
        "responsibilities": [
            f"Use {keyword_a} and {keyword_b} to improve team execution and reporting.",
            f"Translate work into measurable outcomes tied to {keyword_c}.",
            "Partner cross-functionally and communicate progress clearly to stakeholders.",
        ],
        "requirements": case["jobKeywords"][:5],
        "searchQueries": case["jobKeywords"][:4],
    }


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "daily-content"


def safe_audio_slug(date_slug: str, title: str, index: int) -> str:
    title_slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:42] or "short"
    return f"{safe_slug(date_slug)}-{title_slug}-{index}"


def public_asset_exists(ref: str | None) -> bool:
    if not ref:
        return False
    return (REMOTION_PUBLIC_DIR / ref).exists()


def ensure_dirs() -> None:
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    PACKETS_DIR.mkdir(parents=True, exist_ok=True)
    REMOTION_DIR.mkdir(parents=True, exist_ok=True)
    REMOTION_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def load_openai_client():
    load_dotenv(ROOT / "marketing_agent" / ".env", override=True)
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key == "sk-proj-your_openai_api_key_here" or OpenAI is None:
        return None
    return OpenAI(api_key=key)


def load_elevenlabs_config() -> dict:
    load_dotenv(ROOT / "marketing_agent" / ".env", override=True)
    key = os.getenv("ELEVENLABS_API_KEY", "")
    if key == "your_elevenlabs_api_key_here":
        key = ""
    return {
        "apiKey": key,
        "voiceId": os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID),
        "modelId": os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
    }


def load_openai_tts_config() -> dict:
    load_dotenv(ROOT / "marketing_agent" / ".env", override=True)
    return {
        "apiKey": os.getenv("OPENAI_API_KEY", ""),
        "model": os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        "voice": os.getenv("OPENAI_TTS_VOICE", "alloy"),
        "instructions": os.getenv(
            "OPENAI_TTS_INSTRUCTIONS",
            "Sound like a funny, sharp recruiter doing a helpful resume teardown for frustrated job hunters. Keep it quick, warm, and entertaining.",
        ),
    }


def has_elevenlabs_config() -> bool:
    return bool(load_elevenlabs_config()["apiKey"])


def has_any_tts_config() -> bool:
    return bool(load_elevenlabs_config()["apiKey"] or load_openai_tts_config()["apiKey"])


def requires_elevenlabs_audio() -> bool:
    return os.getenv("REQUIRE_ELEVENLABS", "false").lower() == "true"


def elevenlabs_error_text(error: Exception) -> str:
    response = getattr(error, "response", None)
    if response is None:
        return str(error)
    try:
        return response.text[:500]
    except Exception:
        return str(error)


def should_skip_elevenlabs_plain_retry(error: Exception) -> bool:
    text = elevenlabs_error_text(error).lower()
    return any(marker in text for marker in ["quota_exceeded", "missing_permissions", "unauthorized", "permission"])


def list_elevenlabs_voices(config: dict) -> list[dict]:
    response = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={
            "xi-api-key": config["apiKey"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    voices = data.get("voices", [])
    return voices if isinstance(voices, list) else []


def resolve_elevenlabs_voice(config: dict) -> dict:
    global ELEVENLABS_VOICE_CACHE
    if ELEVENLABS_VOICE_CACHE:
        return ELEVENLABS_VOICE_CACHE

    configured = str(config.get("voiceId") or DEFAULT_ELEVENLABS_VOICE_ID)
    fallback = {"voiceId": configured, "name": "configured voice", "source": "configured"}
    if not config.get("apiKey"):
        ELEVENLABS_VOICE_CACHE = fallback
        return fallback

    try:
        voices = list_elevenlabs_voices(config)
    except Exception as error:
        print(f"[!] ElevenLabs voice list unavailable; using configured voice id: {elevenlabs_error_text(error)}")
        ELEVENLABS_VOICE_CACHE = fallback
        return fallback

    if not voices:
        ELEVENLABS_VOICE_CACHE = fallback
        return fallback

    by_id = {str(voice.get("voice_id")): voice for voice in voices if voice.get("voice_id")}
    if configured in by_id and configured != LEGACY_ELEVENLABS_VOICE_ID:
        voice = by_id[configured]
        ELEVENLABS_VOICE_CACHE = {
            "voiceId": configured,
            "name": str(voice.get("name") or "configured voice"),
            "source": "configured",
        }
        return ELEVENLABS_VOICE_CACHE

    preferred_ids = [DEFAULT_ELEVENLABS_VOICE_ID, "CwhRBWXzGAHq8TQ4Fs17", "IKne3meq5aSn9XLyUdCD", "EXAVITQu4vr4xnSDxMaL"]
    selected = None
    for voice_id in preferred_ids:
        if voice_id in by_id:
            selected = by_id[voice_id]
            break
    if selected is None:
        selected = voices[0]

    selected_id = str(selected.get("voice_id") or configured)
    selected_name = str(selected.get("name") or "available voice")
    if selected_id != configured:
        print(f"[i] ElevenLabs voice {configured} is not available to this key; using {selected_name} ({selected_id}).")
    ELEVENLABS_VOICE_CACHE = {
        "voiceId": selected_id,
        "name": selected_name,
        "source": "auto-selected",
    }
    return ELEVENLABS_VOICE_CACHE


def check_elevenlabs_health(probe_tts: bool = False) -> dict:
    config = load_elevenlabs_config()
    health = {
        "configured": bool(config.get("apiKey")),
        "voiceId": config.get("voiceId"),
        "modelId": config.get("modelId"),
        "voicesReadable": False,
        "selectedVoice": None,
        "ttsProbe": None,
        "issues": [],
    }
    if not config.get("apiKey"):
        health["issues"].append("ELEVENLABS_API_KEY is not configured.")
        return health

    try:
        selected = resolve_elevenlabs_voice(config)
        health["voicesReadable"] = True
        health["selectedVoice"] = selected
    except Exception as error:
        health["issues"].append(f"Voice lookup failed: {elevenlabs_error_text(error)}")
        return health

    if probe_tts:
        try:
            voice_id = health["selectedVoice"]["voiceId"]
            response = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps",
                headers={
                    "xi-api-key": config["apiKey"],
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "text": "Signal audio probe.",
                    "model_id": config["modelId"],
                    "voice_settings": {
                        "stability": float(os.getenv("ELEVENLABS_STABILITY", "0.52")),
                        "similarity_boost": float(os.getenv("ELEVENLABS_SIMILARITY", "0.76")),
                        "style": float(os.getenv("ELEVENLABS_STYLE", "0.12")),
                        "use_speaker_boost": True,
                    },
                },
                timeout=60,
            )
            health["ttsProbe"] = {"status": response.status_code, "ok": response.ok}
            if not response.ok:
                health["issues"].append(response.text[:500])
        except Exception as error:
            health["ttsProbe"] = {"status": "error", "ok": False}
            health["issues"].append(elevenlabs_error_text(error))

    return health


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def normalize_alignment_to_captions(alignment: dict) -> list[dict]:
    characters = alignment.get("characters") or []
    starts = alignment.get("character_start_times_seconds") or []
    ends = alignment.get("character_end_times_seconds") or []
    captions = []
    word = ""
    word_start = None
    word_end = None

    for index, character in enumerate(characters):
        char = str(character)
        start = float(starts[index]) if index < len(starts) and starts[index] is not None else None
        end = float(ends[index]) if index < len(ends) and ends[index] is not None else start
        if char.isspace():
            if word:
                captions.append({
                    "text": word,
                    "startMs": int((word_start or 0) * 1000),
                    "endMs": int((word_end or word_start or 0) * 1000),
                    "timestampMs": int((word_start or 0) * 1000),
                    "confidence": None,
                })
            word = ""
            word_start = None
            word_end = None
            continue

        if word_start is None:
            word_start = start if start is not None else 0
        word += char
        word_end = end if end is not None else word_start

    if word:
        captions.append({
            "text": word,
            "startMs": int((word_start or 0) * 1000),
            "endMs": int((word_end or word_start or 0) * 1000),
            "timestampMs": int((word_start or 0) * 1000),
            "confidence": None,
        })

    return captions


def write_alignment_metadata(dest_name: str, payload: dict, voice: dict | None = None) -> dict:
    alignment = payload.get("normalized_alignment") or payload.get("alignment") or {}
    captions = normalize_alignment_to_captions(alignment if isinstance(alignment, dict) else {})
    meta_name = dest_name.rsplit(".", 1)[0] + ".alignment.json"
    meta_path = REMOTION_AUDIO_DIR / meta_name
    metadata = {
        "provider": "elevenlabs",
        "voiceId": voice.get("voiceId") if isinstance(voice, dict) else None,
        "voiceName": voice.get("name") if isinstance(voice, dict) else None,
        "withTimestamps": True,
        "captions": captions,
        "alignment": alignment,
    }
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return {
        "alignmentRef": f"audio/{meta_name}",
        "captions": captions,
        "withTimestamps": True,
    }


def voiceover_duration_seconds(result: dict) -> float:
    captions = result.get("captions") if isinstance(result, dict) else []
    if not isinstance(captions, list):
        return 0.0
    return max((float(caption.get("endMs") or 0) for caption in captions if isinstance(caption, dict)), default=0) / 1000


def score_voiceover_take(text: str, result: dict) -> float:
    duration = voiceover_duration_seconds(result)
    words = max(1, len(re.findall(r"[A-Za-z0-9']+", text)))
    if duration <= 0:
        return 0
    wpm = words / duration * 60
    target = 168
    pacing_penalty = abs(wpm - target)
    caption_bonus = 20 if result.get("captions") else 0
    provider_bonus = 15 if result.get("provider") == "elevenlabs" else 0
    return 100 + caption_bonus + provider_bonus - pacing_penalty


def selected_take_settings(index: int) -> dict:
    presets = [
        {"stability": 0.42, "similarity_boost": 0.72, "style": 0.20, "use_speaker_boost": True},
        {"stability": 0.36, "similarity_boost": 0.70, "style": 0.28, "use_speaker_boost": True},
        {"stability": 0.48, "similarity_boost": 0.76, "style": 0.16, "use_speaker_boost": True},
        {"stability": 0.32, "similarity_boost": 0.68, "style": 0.34, "use_speaker_boost": True},
        {"stability": 0.54, "similarity_boost": 0.78, "style": 0.10, "use_speaker_boost": True},
    ]
    return presets[(index - 1) % len(presets)]


def generate_elevenlabs_voiceover_once(text: str, dest_name: str, voice_settings: dict | None = None) -> dict:
    config = load_elevenlabs_config()
    if not config["apiKey"]:
        return {"src": None, "provider": "none", "captions": []}

    voice = resolve_elevenlabs_voice(config)
    voice_id = voice["voiceId"]
    dest_path = REMOTION_AUDIO_DIR / dest_name
    payload = {
        "text": text,
        "model_id": config["modelId"],
        "output_format": "mp3_44100_128",
        "voice_settings": voice_settings or {
            "stability": float(os.getenv("ELEVENLABS_STABILITY", "0.52")),
            "similarity_boost": float(os.getenv("ELEVENLABS_SIMILARITY", "0.76")),
            "style": float(os.getenv("ELEVENLABS_STYLE", "0.12")),
            "use_speaker_boost": True,
        },
    }

    if os.getenv("ELEVENLABS_WITH_TIMESTAMPS", "true").lower() != "false":
        try:
            response = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps",
                headers={
                    "xi-api-key": config["apiKey"],
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
                timeout=90,
            )
            response.raise_for_status()
            data = response.json()
            audio_b64 = data.get("audio_base64")
            if not audio_b64:
                raise RuntimeError("ElevenLabs timestamp response did not include audio_base64")
            dest_path.write_bytes(base64.b64decode(audio_b64))
            if dest_path.stat().st_size < 1024:
                raise RuntimeError(f"ElevenLabs voiceover is too small: {dest_path}")
            return {
                "src": f"audio/{dest_name}",
                "provider": "elevenlabs",
                "voiceId": voice_id,
                "voiceName": voice.get("name"),
                **write_alignment_metadata(dest_name, data, voice),
            }
        except requests.HTTPError as error:
            if should_skip_elevenlabs_plain_retry(error):
                raise
            print(f"[!] ElevenLabs timestamp voiceover unavailable, falling back to plain TTS: {error}")
        except Exception as error:
            print(f"[!] ElevenLabs timestamp voiceover unavailable, falling back to plain TTS: {error}")

    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": config["apiKey"],
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    dest_path.write_bytes(response.content)
    if dest_path.stat().st_size < 1024:
        raise RuntimeError(f"ElevenLabs voiceover is too small: {dest_path}")
    return {
        "src": f"audio/{dest_name}",
        "provider": "elevenlabs",
        "voiceId": voice_id,
        "voiceName": voice.get("name"),
        "withTimestamps": False,
        "captions": [],
    }


def copy_selected_take(selected: dict, selected_name: str, dest_name: str, take_results: list[dict]) -> dict:
    selected_audio = REMOTION_AUDIO_DIR / selected_name
    dest_audio = REMOTION_AUDIO_DIR / dest_name
    shutil.copyfile(selected_audio, dest_audio)

    selected_alignment_name = selected_name.rsplit(".", 1)[0] + ".alignment.json"
    dest_alignment_name = dest_name.rsplit(".", 1)[0] + ".alignment.json"
    selected_alignment_path = REMOTION_AUDIO_DIR / selected_alignment_name
    dest_alignment_path = REMOTION_AUDIO_DIR / dest_alignment_name
    alignment_meta = read_json(selected_alignment_path, {}) if selected_alignment_path.exists() else {}
    alignment_meta["selectedTake"] = selected.get("take")
    alignment_meta["takeCount"] = len(take_results)
    alignment_meta["takeScores"] = [
        {
            "take": item.get("take"),
            "score": round(float(item.get("takeScore", 0)), 3),
            "durationSeconds": round(float(item.get("durationSeconds", 0)), 3),
        }
        for item in take_results
    ]
    dest_alignment_path.write_text(json.dumps(alignment_meta, indent=2), encoding="utf-8")

    for item in take_results:
        take_name = item.get("destName")
        if not take_name:
            continue
        for suffix in ("", ".alignment.json"):
            candidate = REMOTION_AUDIO_DIR / (take_name if not suffix else take_name.rsplit(".", 1)[0] + suffix)
            if candidate.exists():
                try:
                    candidate.unlink()
                except OSError:
                    pass

    return {
        "src": f"audio/{dest_name}",
        "provider": selected.get("provider", "elevenlabs"),
        "voiceId": selected.get("voiceId"),
        "voiceName": selected.get("voiceName"),
        "alignmentRef": f"audio/{dest_alignment_name}",
        "captions": alignment_meta.get("captions", selected.get("captions", [])),
        "withTimestamps": bool(alignment_meta.get("withTimestamps", selected.get("withTimestamps"))),
        "selectedTake": selected.get("take"),
        "takeCount": len(take_results),
    }


def generate_elevenlabs_voiceover(text: str, dest_name: str) -> dict:
    take_count = max(1, min(5, int(os.getenv("ELEVENLABS_TAKE_COUNT", "3") or "3")))
    if take_count <= 1:
        return generate_elevenlabs_voiceover_once(text, dest_name)

    stem, ext = dest_name.rsplit(".", 1)
    take_results = []
    errors = []
    for take in range(1, take_count + 1):
        take_name = f"{stem}-take-{take}.{ext}"
        try:
            result = generate_elevenlabs_voiceover_once(text, take_name, selected_take_settings(take))
            result["take"] = take
            result["destName"] = take_name
            result["durationSeconds"] = voiceover_duration_seconds(result)
            result["takeScore"] = score_voiceover_take(text, result)
            take_results.append(result)
        except Exception as error:
            errors.append(str(error))

    if not take_results:
        raise RuntimeError(f"ElevenLabs multi-take voiceover failed: {' | '.join(errors)}")

    selected = max(take_results, key=lambda item: float(item.get("takeScore", 0)))
    return copy_selected_take(selected, str(selected["destName"]), dest_name, take_results)


def generate_openai_voiceover(text: str, dest_name: str) -> dict:
    config = load_openai_tts_config()
    if not config["apiKey"]:
        return {"src": None, "provider": "none", "captions": []}

    dest_path = REMOTION_AUDIO_DIR / dest_name
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {config['apiKey']}",
            "Content-Type": "application/json",
        },
        json={
            "model": config["model"],
            "voice": config["voice"],
            "input": text,
            "instructions": config["instructions"],
            "response_format": "mp3",
        },
        timeout=90,
    )
    response.raise_for_status()
    dest_path.write_bytes(response.content)
    if dest_path.stat().st_size < 1024:
        raise RuntimeError(f"OpenAI voiceover is too small: {dest_path}")
    return {"src": f"audio/{dest_name}", "provider": "openai", "withTimestamps": False, "captions": []}


def generate_voiceover(text: str, dest_name: str) -> dict:
    global ELEVENLABS_DISABLED_REASON
    if has_elevenlabs_config():
        if ELEVENLABS_DISABLED_REASON:
            print(f"[i] ElevenLabs skipped for this run: {ELEVENLABS_DISABLED_REASON}")
        else:
            try:
                return generate_elevenlabs_voiceover(text, dest_name)
            except requests.HTTPError as error:
                detail = elevenlabs_error_text(error)
                if should_skip_elevenlabs_plain_retry(error):
                    ELEVENLABS_DISABLED_REASON = detail
                print(f"[!] ElevenLabs voiceover unavailable, falling back when possible: {detail}")
                if requires_elevenlabs_audio():
                    raise
            except Exception as error:
                detail = elevenlabs_error_text(error)
                print(f"[!] ElevenLabs voiceover unavailable, falling back when possible: {detail}")
                if requires_elevenlabs_audio():
                    raise
    elif requires_elevenlabs_audio():
        raise RuntimeError("REQUIRE_ELEVENLABS=true but ELEVENLABS_API_KEY is not configured.")
    if requires_elevenlabs_audio():
        raise RuntimeError("ElevenLabs narration is required; OpenAI TTS fallback is disabled.")
    if load_openai_tts_config()["apiKey"]:
        return generate_openai_voiceover(text, dest_name)
    return {"src": None, "provider": "none", "withTimestamps": False, "captions": []}


def voice_director_contract(short: dict, props: dict) -> dict:
    return {
        "mode": "human_review_read",
        "preferredProvider": "elevenlabs_speech_to_speech",
        "fallbackProvider": "elevenlabs_tts_multitake",
        "takeCount": int(os.getenv("ELEVENLABS_TAKE_COUNT", "3") or "3"),
        "delivery": [
            "Sounds like a recruiter reading the resume live.",
            "Conversational, slightly amused, direct, helpful.",
            "Short pause after the weak bullet and before the score reason.",
            "No corporate polish, no trailer voice, no product-demo cadence.",
        ],
        "scratchReadSrc": props.get("scratchReadSrc"),
        "humanReadBeats": props.get("humanReadBeats", []),
        "scriptSource": "human_read_pass",
    }


def attach_daily_audio(crime_scene_props: dict, short: dict, short_slug: str, prepare_audio: bool, force_audio: bool) -> dict:
    voiceover_text = str(
        short.get("props", {}).get("voiceover_text")
        or short.get("script")
        or crime_scene_props.get("hook")
        or ""
    )[:900]
    crime_scene_props["voiceover_text"] = voiceover_text
    crime_scene_props["audioReadiness"] = {
        "studioVoiceover": False,
        "quietMusic": public_asset_exists("audio/signal-quiet-orbit.wav"),
        "reason": "studio voiceover not requested",
    }

    if public_asset_exists("audio/signal-quiet-orbit.wav"):
        crime_scene_props["musicSrc"] = "audio/signal-quiet-orbit.wav"
        crime_scene_props["musicVolume"] = 0.16

    if not prepare_audio:
        return crime_scene_props

    if not has_any_tts_config():
        crime_scene_props["audioReadiness"]["reason"] = "No TTS provider is configured"
        return crime_scene_props

    voice_name = f"daily-{short_slug}-voiceover.mp3"
    voice_ref = f"audio/{voice_name}"
    provider = "cached"
    voice_result = {"src": voice_ref, "provider": provider, "withTimestamps": False, "captions": []}
    if force_audio or not public_asset_exists(voice_ref):
        voice_result = generate_voiceover(voiceover_text, voice_name)
        provider = voice_result.get("provider", "unknown")
        voice_ref = voice_result.get("src") or voice_ref
    else:
        alignment_ref = f"audio/{voice_name.rsplit('.', 1)[0]}.alignment.json"
        alignment_path = REMOTION_AUDIO_DIR / Path(alignment_ref).name
        if alignment_path.exists():
            alignment = read_json(alignment_path, {})
            cached_provider = str(alignment.get("provider") or ("elevenlabs" if alignment.get("withTimestamps") else provider))
            voice_result = {
                "src": voice_ref,
                "provider": cached_provider,
                "voiceId": alignment.get("voiceId"),
                "voiceName": alignment.get("voiceName"),
                "withTimestamps": bool(alignment.get("withTimestamps")),
                "captions": alignment.get("captions", []),
                "alignmentRef": alignment_ref,
            }

    if public_asset_exists(voice_ref):
        crime_scene_props["voiceoverSrc"] = voice_ref
        crime_scene_props["voiceoverVolume"] = 0.94
        provider = str(voice_result.get("provider") or provider)
        if voice_result.get("captions"):
            crime_scene_props["captions"] = voice_result["captions"]
            last_end_ms = max(
                (float(caption.get("endMs") or 0) for caption in voice_result["captions"] if isinstance(caption, dict)),
                default=0,
            )
            if last_end_ms > 0:
                crime_scene_props["durationSeconds"] = round(min(31.4, max(18, last_end_ms / 1000 + 1.2)), 3)
            crime_scene_props["captionReadiness"] = {
                "wordLevel": True,
                "provider": provider,
                "alignmentRef": voice_result.get("alignmentRef"),
            }
        else:
            crime_scene_props["captionReadiness"] = {
                "wordLevel": False,
                "provider": provider,
                "reason": "Scene captions are present; word-level TTS alignment was unavailable or cached without metadata.",
            }
        crime_scene_props["audioReadiness"] = {
            "studioVoiceover": True,
            "quietMusic": public_asset_exists("audio/signal-quiet-orbit.wav"),
            "provider": provider,
            "voiceId": voice_result.get("voiceId"),
            "voiceName": voice_result.get("voiceName"),
            "reason": f"ready via {provider}",
            "wordLevelCaptions": bool(voice_result.get("captions")),
            "voiceDirector": crime_scene_props.get("voiceDirector"),
        }
    return crime_scene_props


def choose_seed(topic: str | None) -> dict:
    if topic:
        return {
            "topic": topic,
            "series": "Daily Research Packet",
            "thesis": "Turn a timely job-search pain point into one useful long-form teardown and several short proof clips.",
            "hook": topic,
            "keywords": ["resume", "job description", "Signal score", "job search"],
            "source_notes": TREND_SEEDS[0]["source_notes"],
        }
    intake = read_json(TREND_INTAKE_PATH, {})
    top = intake.get("topCandidate") if isinstance(intake, dict) else None
    if isinstance(top, dict) and top.get("topic") and top.get("sourceNotes"):
        return {
            "topic": str(top.get("topic")),
            "series": str(top.get("series") or "Daily Research Packet"),
            "thesis": str(top.get("contentAngle") or top.get("whyNow") or "Turn a sourced job-search trend into a useful resume teardown."),
            "hook": str(top.get("hook") or top.get("topic")),
            "keywords": ["resume", "job description", "Signal score", "job search"],
            "source_notes": top.get("sourceNotes") or TREND_SEEDS[0]["source_notes"],
        }
    return TREND_SEEDS[0]


def text_from_topic(value: object, fallback: str = "Daily resume teardown") -> str:
    if isinstance(value, dict):
        return str(value.get("topic") or value.get("hook") or fallback)
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or item.get("script") or item.get("title") or ""))
            else:
                parts.append(str(item))
        joined = " ".join(part.strip() for part in parts if part and part.strip())
        return joined or fallback
    return str(value or fallback)


def build_fallback_packet(seed: dict, publish_date: str) -> dict:
    topic = text_from_topic(seed.get("topic"))
    hook = seed["hook"]
    keywords = seed["keywords"]
    episode_title = f"{hook} | Resume Teardown"
    shorts = [
        {
            "series": "Live Resume Review",
            "title": "I would circle this line first",
            "hook": "I would circle this line first.",
            "script": (
                "Okay, this line sounds normal until I compare it to the job. I am looking for tools, scope, "
                "and a result. The proof is lower on the resume, so I would move it into this bullet before applying."
            ),
            "storyboard": [
                "Open on a realistic one-page resume at a desk.",
                "Reviewer circle lands on one weak bullet.",
                "Job description sits beside it with three terms highlighted.",
                "Source proof lower on the resume gets boxed.",
                "Rewrite moves the proof into the circled bullet.",
                "Score appears only after the reason is visible.",
            ],
            "props": {
                "hook1": "Circle this line.",
                "hook2": "It makes me guess.",
                "subline": "The proof is real, but it is in the wrong place.",
                "beforeScore": 31,
                "afterScore": 86,
                "missing": ["SQL", "Tableau", "cohort analysis", "business result"],
                "cta": "Check your free Signal score.",
                "voiceover_text": (
                    "Okay, this line sounds normal until I compare it to the job. I am looking for tools, scope, "
                    "and a result. The proof is lower on the resume, so I would move it into this bullet before applying."
                ),
            },
        },
        {
            "series": "Recruiter Search Test",
            "title": "I searched the resume. Bad news.",
            "hook": "I searched the resume. Bad news.",
            "script": (
                "Here is the search test. I search the job's first two terms, then I read the resume line. "
                "The work may be real, but this sentence makes me guess. The fix is to move the visible proof onto the line."
            ),
            "storyboard": [
                "Show a recruiter search box typing SQL.",
                "Resume returns no useful match and Signal points at the weak line.",
                "Paste the job description next to the resume.",
                "Highlight the missing role terms.",
                "Rewrite the bullet and rerun the search after the reason is clear.",
                "CTA to the free Signal score.",
            ],
            "props": {
                "hook1": "Search test.",
                "hook2": "Bad news.",
                "subline": "A reviewer cannot search for what you meant to say.",
                "beforeScore": 34,
                "afterScore": 92,
                "missing": ["SQL", "Tableau", "cohort analysis", "churn dashboard"],
                "cta": "Run your free Signal score.",
                "voiceover_text": (
                    "Here is the search test. I search the job's first two terms, then I read the resume line. "
                    "The work may be real, but this sentence makes me guess. The fix is to move the visible proof onto the line."
                ),
            },
        },
        {
            "series": "Job Description Review",
            "title": "The job post gave the answer key",
            "hook": "The job post gave the answer key.",
            "script": (
                "The job post gave the answer key, but the resume answered too vaguely. I would read the weak line, "
                "pull the proof from lower on the page, and rewrite the bullet so the tool, metric, and outcome are visible."
            ),
            "storyboard": [
                "Open on the job post with three highlighted requirements.",
                "Slide to the resume line and circle the mismatch.",
                "Show source proof lower on the resume.",
                "Rewrite the line without inventing anything.",
                "Reveal score movement only after the reason is visible.",
                "CTA to the free Signal score.",
            ],
            "props": {
                "hook1": "Answer key.",
                "hook2": "Too vague.",
                "subline": "Use the job language only when the resume already supports it.",
                "beforeScore": 38,
                "afterScore": 91,
                "missing": ["SQL", "Tableau", "cohort analysis", "churn dashboard"],
                "cta": "Check your free Signal score.",
                "voiceover_text": (
                    "The job post gave the answer key, but the resume answered too vaguely. I would read the weak line, "
                    "pull the proof from lower on the page, and rewrite the bullet so the tool, metric, and outcome are visible."
                ),
            },
        },
    ]

    return {
        "publishDate": publish_date,
        "topic": topic,
        "series": seed["series"],
        "thesis": seed["thesis"],
        "sourceNotes": seed["source_notes"],
        "trendResearch": TREND_RESEARCH_CONTRACT,
        "youtube": {
            "title": episode_title,
            "seoTitle": f"{hook} | Resume Teardown with Signal by ATSHacker",
            "description": (
                "A funny recruiter-style teardown of why a qualified resume can be hard to find, "
                "how to translate a job description into resume proof, and where Signal fits without fake claims."
            ),
            "chapters": [
                "0:00 Cold open",
                "0:20 The open loop",
                "0:55 Translate the job description",
                "1:40 Recruiter search test",
                "2:25 Resume crime scene",
                "3:15 Why it gets missed",
                "4:05 Live bullet fix",
                "5:00 Score reveal",
                "5:35 Trust check and CTA",
            ],
            "scriptSections": [
                {
                    "label": "Cold open",
                    "script": f"{hook} This resume looks professional, which is why the mistake is dangerous. On screen, it feels polished. In a recruiter search, the proof is still hard to find.",
                    "visual": "Cold open with comic red stamp, quick zoom, Signal mascot reaction, and resume/JD split screen.",
                },
                {
                    "label": "Open loop",
                    "script": "We are not adding fake experience. We are checking whether the resume explains the real experience in the same language as the target job.",
                    "visual": "Show the weak resume score, then hold the improved score as the unresolved payoff.",
                },
                {
                    "label": "Translate the job description",
                    "script": "Before touching the resume, pull out the role title, tools, responsibilities, metrics, and proof signals the job actually asks for.",
                    "visual": "Resume on left, job description on right, mismatched terms highlighted with funny labels.",
                },
                {
                    "label": "Recruiter search test",
                    "script": "If a recruiter searches for the first three important terms from the job description, this resume should produce useful hits. Right now, the source bullet is too broad.",
                    "visual": "Search console typing the first three job-description terms and showing weak matches.",
                },
                {
                    "label": "Resume crime scene",
                    "script": "Now compare the resume line by line. The weak bullet is not dishonest. It is just too vague to carry the role-specific proof.",
                    "visual": "Red/yellow markups over weak bullets.",
                },
                {
                    "label": "Why it gets missed",
                    "script": "A polished sentence can still hide the most important evidence. Recruiters skim for tools, scope, and outcomes because those make fit easy to verify.",
                    "visual": "Zoom into the weak bullet and place missing proof labels beside it.",
                },
                {
                    "label": "Live bullet fix",
                    "script": "The fix is to say the real work clearly: what tool, what scope, what audience, and what result. No fake claims, just usable evidence.",
                    "visual": "Before/after bullet rewrite.",
                },
                {
                    "label": "Score reveal",
                    "script": "Once the evidence matches the role language, the example score moves up. The point is not gaming a robot. The point is making real fit easier to see.",
                    "visual": "Score meter jumps from low match to high match with before/after resume panels.",
                },
                {
                    "label": "Trust and CTA",
                    "script": "Signal automates this comparison. Paste the job description, upload the resume, and check the free score first. If the gap is real, then the paid resume and cover letter package makes sense.",
                    "visual": "Free Signal score page, trust badges, and bundle CTA.",
                },
            ],
            "cta": "Paste the job description and check your free Signal score before you apply.",
        },
        "shorts": shorts,
        "monetization": {
            "primaryGoal": "Site revenue from resume / cover letter packages, not ad revenue.",
            "cta": "Free Signal score -> $9.99 resume or $14.99 bundle.",
            "tracking": ["utm_source=youtube", "utm_medium=video", "utm_campaign=daily_packet"],
            "upsell": "Promote bundle after score completion and multi-role pack after first purchase.",
        },
        "viewerCustomerReview": {
            "viewerEmotion": "Frustrated job hunters should feel called out, amused, and relieved rather than shamed.",
            "customerBridge": "Laugh at the vague bullet, then show the free score as the low-risk next step.",
            "entertainmentRules": ENTERTAINMENT_RULES,
        },
    }


def select_teardown_case(index: int, short: dict | None = None, props: dict | None = None) -> dict:
    if isinstance(props, dict):
        requested = str(props.get("preferredCaseId") or "").strip()
        if requested:
            for case in TEARDOWN_CASES:
                if case["id"] == requested:
                    return case
    if os.getenv("SIGNAL_ALLOW_ROLE_INFERENCE", "false").lower() != "true":
        return TEARDOWN_CASES[(index - 1) % len(TEARDOWN_CASES)]

    text_parts = []
    if isinstance(short, dict):
        text_parts.extend([
            short.get("series", ""),
            short.get("title", ""),
            short.get("hook", ""),
            short.get("script", ""),
        ])
    blob = " ".join(str(part).lower() for part in text_parts)

    role_markers = {
        "data_analyst": ["sql", "tableau", "cohort", "churn", "data analyst", "dashboard"],
        "sales_account_exec": ["salesforce", "quota", "sales", "account executive", "meddicc"],
        "frontend_engineer": ["react", "typescript", "next.js", "developer", "frontend", "software"],
        "project_manager": ["jira", "project manager", "stakeholder", "agile", "risk register"],
        "customer_success": ["gainsight", "customer success", "renewal", "qbr", "nps"],
        "healthcare_rn": ["nurse", "clinical", "patient", "epic", "discharge"],
    }
    scores = []
    for case in TEARDOWN_CASES:
        score = sum(1 for marker in role_markers.get(case["id"], []) if marker in blob)
        scores.append((score, case))

    best_score, best_case = max(scores, key=lambda item: item[0])
    if best_score >= 3:
        return best_case
    return TEARDOWN_CASES[(index - 1) % len(TEARDOWN_CASES)]


def case_template_context(case: dict) -> dict:
    keywords = case["jobKeywords"]
    spoken_rewrite = CASE_SPOKEN_REWRITES.get(case["id"], case["afterBullet"])
    score_rubric = build_score_rubric(case)
    before_score = int(score_rubric.get("beforeTotal") or case["beforeScore"])
    after_score = int(score_rubric.get("afterTotal") or case["afterScore"])
    ledger = case_evidence_ledger(case)
    return {
        "resumeTitle": case["resumeTitle"].replace(" Resume", ""),
        "role": case["jobTitle"],
        "kw1": keywords[0],
        "kw2": keywords[1],
        "kw3": keywords[2],
        "beforeBullet": case["beforeBullet"].rstrip(".") + ".",
        "afterBullet": case["afterBullet"].rstrip(".") + ".",
        "spokenRewrite": spoken_rewrite,
        "beforeScore": before_score,
        "afterScore": after_score,
        "humorLine": CASE_HUMOR_LINES.get(case["id"], "The bullet sounds busy and allergic to numbers."),
        "proofLine": compact_proof_line(case),
        "sourceLocation": str(ledger.get("sourceLocation", "lower on the resume")),
        "evidenceSummary": evidence_summary(case),
    }


def playbook_for_short(index: int) -> dict:
    return CREATOR_FORMAT_PLAYBOOKS[(index - 1) % len(CREATOR_FORMAT_PLAYBOOKS)]


def render_case_template(template: str, case: dict) -> str:
    return template.format(**case_template_context(case))


def build_human_review_transcript(case: dict, playbook: dict, score_rubric: dict) -> str:
    context = case_template_context(case)
    proof_line = compact_proof_line(case)
    before_score = int(score_rubric.get("beforeTotal") or case["beforeScore"])
    after_score = int(score_rubric.get("afterTotal") or case["afterScore"])

    if playbook["id"] == "search_console":
        return (
            f"Here is the search test. I search {context['kw1']} and {context['kw2']}. "
            f"Then I read: {context['beforeBullet']} "
            f"That line makes me guess. Lower on the page, I found the proof: {proof_line} "
            f"So I would probably score that around {before_score}. "
            f"Rewrite it as: {context['spokenRewrite']}. "
            f"Now the search terms, metric, and result sit together, so {after_score} makes sense. "
            "Run the free Signal score before you apply."
        )

    if playbook["id"] == "answer_key":
        return (
            f"Job post answer key: {context['kw1']}, {context['kw2']}, {context['kw3']}. "
            f"Resume line: {context['beforeBullet']} "
            f"I would circle that because it answers too vaguely. Proof lower down: {proof_line} "
            f"I would score it around {before_score}. "
            f"I would write: {context['spokenRewrite']}. "
            f"Now the evidence matches, so {after_score} makes sense. "
            "Run the free Signal score before you apply."
        )

    return (
        f"Okay, this line says: {context['beforeBullet']} "
        "I would circle it because the proof is lower on the page: "
        f"{proof_line} "
        f"The job wants {context['kw1']}, {context['kw2']}, and {context['kw3']}, so I would score it around {before_score}. "
        f"Rewrite it as: {context['spokenRewrite']}. "
        f"Now I can see why it scores {after_score}. "
        "Run the free Signal score before you apply."
    )


def build_case_voiceover(case: dict, playbook: dict) -> str:
    score_rubric = build_score_rubric(case)
    return build_human_review_transcript(case, playbook, score_rubric)


def build_case_storyboard(case: dict, playbook: dict) -> list[str]:
    context_line = f"Case: {case['resumeTitle']} against {case['jobTitle']}."
    rendered = [render_case_template(step, case) for step in playbook["storyboard"]]
    return [context_line, *rendered]


def apply_teardown_case(short: dict, title: str, hook: str, script: str, storyboard: list, props: dict, index: int) -> tuple[str, str, str, list, dict]:
    case = select_teardown_case(index, short, props)
    validate_case_rewrite_evidence(case)
    playbook = playbook_for_short(index)
    score_rubric = build_score_rubric(case)
    if score_rubric["beforeTotal"] != case["beforeScore"] or score_rubric["afterTotal"] != case["afterScore"]:
        raise ValueError(
            f"Score rubric mismatch for {case['id']}: "
            f"{score_rubric['beforeTotal']}->{score_rubric['afterTotal']} vs "
            f"{case['beforeScore']}->{case['afterScore']}"
        )
    case_voiceover = build_case_voiceover(case, playbook)
    case_storyboard = build_case_storyboard(case, playbook)
    case_title = render_case_template(playbook["title"], case)
    case_hook = render_case_template(playbook["hook"], case)
    case_subhook = render_case_template(playbook["subhook"], case)
    props.update({
        "teardownCaseId": case["id"],
        "playbookId": playbook["id"],
        "seriesOverride": playbook["series"],
        "creativeFormat": playbook["creativeFormat"],
        "visualStyle": playbook["visualStyle"],
        "formatArchetype": playbook["formatArchetype"],
        "pace": playbook["pace"],
        "subhook": case_subhook,
        "signalLines": playbook["signalLines"],
        "renderComposition": playbook.get("composition", "ResumeCrimeScene"),
        "resumeName": case["resumeName"],
        "resumeTitle": case["resumeTitle"],
        "resumeMeta": case["resumeMeta"],
        "jobTitle": case["jobTitle"],
        "jobKeywords": case["jobKeywords"],
        "weakBullets": case["weakBullets"],
        "beforeBullet": case["beforeBullet"],
        "afterBullet": case["afterBullet"],
        "beforeScore": score_rubric["beforeTotal"],
        "afterScore": score_rubric["afterTotal"],
        "scoreBasis": score_basis_from_rubric(score_rubric),
        "score_rubric": score_rubric,
        "scoreRubric": score_rubric,
        "scoreLabel": "Signal Fit Score",
        "evidenceLedger": case_evidence_ledger(case),
        "humanReadBeats": build_human_read_beats(case, playbook, score_rubric),
        "missing": case["jobKeywords"],
        "markedLabel": case["markedLabel"],
        "problemPunchline": playbook["problemPunchline"],
        "teardownPunchline": playbook["teardownPunchline"],
        "fixPunchline": playbook["fixPunchline"],
        "teardownIssues": case["teardownIssues"],
        "resumeDocument": build_professional_resume_document(case),
        "jobDescription": build_realistic_job_description(case),
        "voiceover_text": case_voiceover,
    })
    return case_title, case_hook, case_voiceover, case_storyboard, props


def normalize_short(short: dict, fallback: dict, index: int) -> dict:
    if not isinstance(short, dict):
        short = {}

    title = text_from_topic(short.get("title") or fallback.get("title"), f"Signal short {index}")
    hook = text_from_topic(short.get("hook") or short.get("content") or fallback.get("hook"), "Your resume may be invisible.")
    script = text_from_topic(short.get("script") or short.get("content") or fallback.get("script"), hook)
    entertainment_text = f"{title} {hook} {script}".lower()
    used_fallback = False
    proof_markers = ["sql", "tableau", "salesforce", "react", "pipeline", "dashboard", "32/100", "89/100", "keyword", "score"]
    has_concrete_proof = sum(1 for marker in proof_markers if marker in entertainment_text) >= 2
    weak_generated = any(marker in entertainment_text for marker in WEAK_GENERATED_PHRASES)
    script_too_thin = len(script.split()) < 18
    if (
        not any(marker in entertainment_text for marker in ENTERTAINMENT_MARKERS)
        or not has_concrete_proof
        or weak_generated
        or script_too_thin
    ):
        title = fallback.get("title") or title
        hook = fallback.get("hook") or hook
        script = fallback.get("script") or script
        short = {**short, "title": title, "hook": hook, "script": script}
        used_fallback = True
    storyboard = short.get("storyboard")
    visual_text = " ".join(str(item) for item in storyboard) if isinstance(storyboard, list) else ""
    product_visual_markers = ("resume", "job", "description", "keyword", "bullet", "score", "signal")
    if (
        used_fallback
        or not isinstance(storyboard, list)
        or not storyboard
        or not any(marker in visual_text.lower() for marker in product_visual_markers)
    ):
        storyboard = fallback.get("storyboard") or [
            "Open with the hook in large mobile-readable text.",
            "Show resume language beside target job language.",
            "Highlight the mismatch.",
            "Show Signal score/gap proof.",
            "CTA to check the free Signal score.",
        ]

    props = short.get("props") if isinstance(short.get("props"), dict) else {}
    props.setdefault("hook1", str(hook)[:55])
    props.setdefault("hook2", "Check the match.")
    props.setdefault("subline", "Signal compares resume language to the target job.")
    props.setdefault("cta", "Check your free Signal score.")
    title, hook, script, storyboard, props = apply_teardown_case(short, str(title), str(hook), str(script), storyboard, props, index)
    props.setdefault("beforeScore", 38 + index)
    props.setdefault("afterScore", 86 + index)
    props.setdefault("missing", ["role language", "tool proof", "measurable result"])
    props.setdefault("voiceover_text", str(script)[:650])

    return {
        "series": str(props.get("seriesOverride") or short.get("series") or fallback.get("series") or "Daily Short"),
        "title": str(title),
        "hook": str(hook),
        "script": str(script),
        "storyboard": [str(item) for item in storyboard[:8]],
        "props": props,
    }


def normalize_packet(packet: dict, seed: dict, publish_date: str) -> dict:
    fallback = build_fallback_packet(seed, publish_date)
    if not isinstance(packet, dict):
        return fallback

    packet["publishDate"] = publish_date
    packet["topic"] = text_from_topic(packet.get("topic") or seed.get("topic") or fallback["topic"], fallback["topic"])
    packet["series"] = str(packet.get("series") or seed.get("series") or fallback["series"])
    packet["thesis"] = str(packet.get("thesis") or seed.get("thesis") or fallback["thesis"])

    source_notes = packet.get("sourceNotes")
    if not isinstance(source_notes, list) or not source_notes:
        source_notes = seed.get("source_notes") or fallback["sourceNotes"]
    packet["sourceNotes"] = source_notes

    trend_research = packet.get("trendResearch")
    if not isinstance(trend_research, dict):
        trend_research = {}
    for key, value in TREND_RESEARCH_CONTRACT.items():
        trend_research.setdefault(key, value)
    for key in (
        "humanPremise",
        "platformPattern",
        "copyFromResearch",
        "avoid",
        "researchBrief",
        "borrowedMechanic",
        "whyThisMechanicFits",
        "whatNotToCopy",
        "highViewSwipeFile",
    ):
        value = trend_research.get(key)
        if isinstance(value, list):
            trend_research[key] = "; ".join(str(item).strip() for item in value if str(item).strip())
        elif value is not None:
            trend_research[key] = str(value)
    benchmark_urls = trend_research.get("benchmarkUrls")
    if not isinstance(benchmark_urls, list):
        benchmark_urls = [benchmark_urls] if benchmark_urls else []
    trend_research["benchmarkUrls"] = [str(url).strip() for url in benchmark_urls if str(url).strip()]
    packet["trendResearch"] = trend_research

    youtube = packet.get("youtube")
    if not isinstance(youtube, dict):
        youtube = {}
    fallback_youtube = fallback["youtube"]
    youtube["title"] = str(youtube.get("title") or fallback_youtube["title"])
    youtube["seoTitle"] = str(youtube.get("seoTitle") or f"{youtube['title']} | Signal by ATSHacker")
    youtube["description"] = str(youtube.get("description") or fallback_youtube["description"])
    youtube["cta"] = str(youtube.get("cta") or fallback_youtube["cta"])

    chapters = youtube.get("chapters")
    script_sections = youtube.get("scriptSections")
    generated_script = youtube.get("script")
    if (not isinstance(chapters, list) or not chapters) and isinstance(generated_script, list):
        chapters = []
        for item in generated_script:
            if not isinstance(item, dict):
                chapters.append("Section")
                continue
            duration = item.get("duration") or item.get("time") or ""
            if isinstance(duration, dict):
                duration = duration.get("start") or duration.get("from") or ""
            start_time = str(duration).split(" - ")[0].strip()
            label = str(item.get("chapter") or item.get("title") or "Section")
            chapters.append(f"{start_time} {label}".strip())
    if not isinstance(chapters, list) or not chapters:
        chapters = fallback_youtube["chapters"]
    youtube["chapters"] = [str(item) for item in chapters]

    if (not isinstance(script_sections, list) or not script_sections) and isinstance(generated_script, list):
        script_sections = [
            {
                "label": item.get("chapter", f"Section {idx}"),
                "script": item.get("content", ""),
                "visual": "Screen-recorded resume teardown with highlighted job-description language.",
            }
            for idx, item in enumerate(generated_script, start=1)
            if isinstance(item, dict)
        ]
    if not isinstance(script_sections, list) or not script_sections:
        script_sections = fallback_youtube["scriptSections"]
    script_blob = " ".join(
        f"{section.get('label', '')} {section.get('script', '')} {section.get('visual', '')}"
        for section in script_sections
        if isinstance(section, dict)
    ).lower()
    labels = [str(section.get("label", "")).lower() for section in script_sections if isinstance(section, dict)]
    concrete_longform_markers = sum(
        1
        for marker in ["sql", "tableau", "salesforce", "react", "score", "bullet", "before/after", "weak bullets"]
        if marker in script_blob
    )
    generic_section_labels = labels and sum(1 for label in labels if label.startswith("section")) >= min(4, len(labels))
    metadata_blob = " ".join(
        str(part)
        for part in [
            youtube.get("title", ""),
            youtube.get("seoTitle", ""),
            youtube.get("script", ""),
            youtube.get("storyboard", ""),
        ]
    ).lower()
    if (
        any(marker in script_blob for marker in WEAK_GENERATED_PHRASES)
        or any(marker in metadata_blob for marker in WEAK_GENERATED_PHRASES)
        or generic_section_labels
        or "resume" not in script_blob
        or "job description" not in script_blob
        or concrete_longform_markers < 2
    ):
        youtube["title"] = fallback_youtube["title"]
        youtube["seoTitle"] = fallback_youtube["seoTitle"]
        youtube["description"] = fallback_youtube["description"]
        youtube["chapters"] = fallback_youtube["chapters"]
        script_sections = fallback_youtube["scriptSections"]
    youtube["scriptSections"] = script_sections
    youtube.pop("script", None)
    youtube.pop("storyboard", None)
    title_low = youtube["title"].lower()
    if not any(marker in title_low for marker in ["sounds professional", "34/100", "invisible", "resume teardown"]):
        youtube["title"] = fallback_youtube["title"]
        youtube["seoTitle"] = fallback_youtube["seoTitle"]
    packet["youtube"] = youtube

    incoming_shorts = packet.get("shorts")
    if not isinstance(incoming_shorts, list) or not incoming_shorts:
        incoming_shorts = fallback["shorts"]
    fallback_shorts = fallback["shorts"]
    normalized_shorts = []
    seen_short_keys = set()
    for idx, short in enumerate(incoming_shorts[:5], start=1):
        fallback_short = fallback_shorts[(idx - 1) % len(fallback_shorts)]
        normalized = normalize_short(short, fallback_short, idx)
        if not score_short(normalized).get("passed"):
            normalized = normalize_short(fallback_short, fallback_short, idx)
        short_key = safe_slug(f"{normalized.get('title', '')}-{normalized.get('hook', '')}")
        if short_key in seen_short_keys:
            continue
        seen_short_keys.add(short_key)
        normalized_shorts.append(normalized)
        if len(normalized_shorts) >= 3:
            break
    while len(normalized_shorts) < 3:
        idx = len(normalized_shorts) + 1
        normalized = normalize_short({}, fallback_shorts[(idx - 1) % len(fallback_shorts)], idx)
        if not score_short(normalized).get("passed"):
            normalized = normalize_short(fallback_shorts[(idx - 1) % len(fallback_shorts)], fallback_shorts[(idx - 1) % len(fallback_shorts)], idx)
        short_key = safe_slug(f"{normalized.get('title', '')}-{normalized.get('hook', '')}")
        if short_key in seen_short_keys:
            break
        seen_short_keys.add(short_key)
        normalized_shorts.append(normalized)
    packet["shorts"] = normalized_shorts

    monetization = packet.get("monetization")
    if not isinstance(monetization, dict):
        monetization = {
            "primaryGoal": str(monetization or "Drive free Signal score completions and paid package purchases."),
            "cta": "Free Signal score -> $9.99 resume or $14.99 bundle.",
            "tracking": ["utm_source=youtube", "utm_medium=video", "utm_campaign=daily_packet"],
            "upsell": "Make the $14.99 bundle the default value offer after score completion.",
        }
    monetization.setdefault("primaryGoal", "Site revenue from resume / cover letter packages, not ad revenue.")
    monetization.setdefault("cta", "Free Signal score -> $9.99 resume or $14.99 bundle.")
    monetization.setdefault("tracking", ["utm_source=youtube", "utm_medium=video", "utm_campaign=daily_packet"])
    monetization.setdefault("upsell", "Promote bundle after score completion and multi-role pack after first purchase.")
    packet["monetization"] = monetization
    packet["creativeQualityGate"] = score_packet(packet)
    return packet


def maybe_generate_with_openai(seed: dict, publish_date: str) -> dict:
    client = load_openai_client()
    if client is None:
        return build_fallback_packet(seed, publish_date)

    prompt = {
        "task": "Create a daily Signal by ATSHacker content packet.",
        "topic": seed,
        "trendResearchContract": TREND_RESEARCH_CONTRACT,
        "researchBrief": str(TREND_RESEARCH_BRIEF_PATH.relative_to(ROOT)),
        "requirements": [
            "One 8-10 minute YouTube episode script with storyboard and chapters.",
            "Three short-form cutdowns, each 18-32 seconds.",
            "Start every short as a human resume-review situation, not a product demo.",
            "Make the content funny and entertaining for frustrated job hunters through real reviewer reactions, not forced slang.",
            "Humor must punch at vague resume language and the broken job-search process, not at unemployed people.",
            "Each short must read one exact weak resume line, compare it to one job requirement, explain the low score in human language, find proof already on the resume, rewrite only that proof, then explain the score movement.",
            "Claims must avoid auto-reject, guarantees, fake outcomes, and unsupported competitor claims.",
            "CTA must send users to the free Signal score.",
            "Use recruiter-reacts / resume-teardown energy, not generic SaaS demo energy.",
            "Include a trendResearch object with humanPremise, platformPattern, copyFromResearch, avoid, benchmarkUrls, borrowedMechanic, whyThisMechanicFits, and whatNotToCopy.",
            "Every trendResearch.benchmarkUrls list must include at least two URLs from the high-view swipe file or current niche research.",
            "For every short include title, series, hook, script, storyboard, and Remotion props.",
            "Return strict JSON matching keys: publishDate, topic, series, thesis, sourceNotes, trendResearch, youtube, shorts, monetization, viewerCustomerReview.",
        ],
        "entertainmentRules": ENTERTAINMENT_RULES,
        "preferredFormats": VIRAL_FORMATS,
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are the Growth Studio Agent for Signal by ATSHacker. Make sourced, safe, high-converting content plans.",
                },
                {"role": "user", "content": json.dumps(prompt)},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            return build_fallback_packet(seed, publish_date)
        generated = json.loads(content)
        generated.setdefault("publishDate", publish_date)
        generated.setdefault("sourceNotes", seed.get("source_notes", []))
        return normalize_packet(generated, seed, publish_date)
    except Exception as exc:
        print(f"[!] OpenAI packet generation failed, using fallback: {exc}")
        return build_fallback_packet(seed, publish_date)


def write_markdown_packet(packet: dict, packet_dir: Path) -> None:
    youtube = packet["youtube"]
    trend = packet.get("trendResearch") if isinstance(packet.get("trendResearch"), dict) else {}
    lines = [
        f"# {youtube['title']}",
        "",
        f"Publish date: {packet['publishDate']}",
        f"Series: {packet.get('series', 'Daily')}",
        f"Thesis: {packet.get('thesis', '')}",
        "",
        "## Trend Research",
        "",
        f"Human premise: {trend.get('humanPremise', '')}",
        f"Platform pattern: {trend.get('platformPattern', '')}",
        f"Copy from research: {trend.get('copyFromResearch', '')}",
        f"Avoid: {trend.get('avoid', '')}",
        "",
        "## SEO",
        "",
        f"Title: {youtube.get('seoTitle', youtube['title'])}",
        f"Description: {youtube.get('description', '')}",
        "",
        "## Chapters",
        "",
    ]
    lines.extend(f"- {chapter}" for chapter in youtube.get("chapters", []))
    lines.extend(["", "## Script And Storyboard", ""])
    for section in youtube.get("scriptSections", []):
        lines.extend([
            f"### {section.get('label', 'Section')}",
            "",
            f"Script: {section.get('script', '')}",
            "",
            f"Visual: {section.get('visual', '')}",
            "",
        ])
    lines.extend([
        "## CTA",
        "",
        youtube.get("cta", "Check your free Signal score."),
        "",
    ])
    (packet_dir / "youtube_episode.md").write_text("\n".join(lines), encoding="utf-8")

    voiceover_lines = [
        f"# Long-form Voiceover: {youtube['title']}",
        "",
        "This file is the narration source for the Remotion timing pass. Keep it script-only.",
        "",
    ]
    for section in youtube.get("scriptSections", []):
        label = str(section.get("label") or "Section").strip() or "Section"
        script = str(section.get("script") or "").strip()
        if not script:
            continue
        voiceover_lines.extend([f"## {label}", "", script, ""])
    (packet_dir / "longform_voiceover.md").write_text("\n".join(voiceover_lines), encoding="utf-8")

    short_lines = [
        f"# Shorts Plan: {packet['topic']}",
        "",
        "## Trend Research",
        "",
        f"Human premise: {trend.get('humanPremise', '')}",
        f"Platform pattern: {trend.get('platformPattern', '')}",
        f"Copy from research: {trend.get('copyFromResearch', '')}",
        f"Avoid: {trend.get('avoid', '')}",
        "",
    ]
    for idx, short in enumerate(packet.get("shorts", []), start=1):
        short_lines.extend([
            f"## Short {idx}: {short.get('title', 'Untitled')}",
            "",
            f"Series: {short.get('series', '')}",
            f"Hook: {short.get('hook', '')}",
            "",
            "Script:",
            short.get("script", ""),
            "",
            "Storyboard:",
        ])
        short_lines.extend(f"- {step}" for step in short.get("storyboard", []))
        short_lines.append("")
    (packet_dir / "shorts_plan.md").write_text("\n".join(short_lines), encoding="utf-8")

    monetization = packet.get("monetization", {})
    monetization_lines = [
        "# Monetization Plan",
        "",
        f"Primary goal: {monetization.get('primaryGoal', 'Site revenue')}",
        f"CTA: {monetization.get('cta', 'Free Signal score')}",
        f"Upsell: {monetization.get('upsell', '')}",
        "",
        "Tracking:",
    ]
    monetization_lines.extend(f"- {item}" for item in monetization.get("tracking", []))
    (packet_dir / "monetization.md").write_text("\n".join(monetization_lines), encoding="utf-8")

    review = packet.get("viewerCustomerReview", {})
    if not isinstance(review, dict):
        review = {}
    review_lines = [
        "# Viewer And Customer Review",
        "",
        f"Viewer emotion: {review.get('viewerEmotion', 'Frustrated job hunters should feel amused, understood, and curious enough to run a free score.')}",
        f"Customer bridge: {review.get('customerBridge', 'Use the joke to reveal the pain, then offer the free Signal score as the low-risk next step.')}",
        "",
        "Entertainment rules:",
    ]
    rules = review.get("entertainmentRules") if isinstance(review.get("entertainmentRules"), list) else ENTERTAINMENT_RULES
    review_lines.extend(f"- {rule}" for rule in rules)
    review_lines.extend([
        "",
        "Pass criteria:",
        "- Funny or painfully relatable in the first two seconds.",
        "- Resume/job description remains the star of the visual.",
        "- The viewer learns one useful fix before the CTA.",
        "- The CTA goes to the free score, then paid bundle after proof.",
        "- No shame toward job seekers and no unsupported ATS guarantees.",
        "- Professional creator gate score is 85+ before public posting.",
    ])
    gate = packet.get("creativeQualityGate")
    if isinstance(gate, dict):
        review_lines.extend([
            "",
            "Creative gate:",
            f"- Verdict: {gate.get('verdict', 'unknown')}",
            f"- Score: {gate.get('overallScore', 0)}/100",
            f"- Passed: {gate.get('passed', False)}",
        ])
        for note in gate.get("notes", [])[:8]:
            review_lines.append(f"- Note: {note}")
    (packet_dir / "viewer_customer_review.md").write_text("\n".join(review_lines), encoding="utf-8")


def first_short_props(packet: dict) -> dict:
    for short in packet.get("shorts", []) or []:
        if isinstance(short, dict) and isinstance(short.get("props"), dict):
            return short["props"]
    return {}


def build_episode_props(packet: dict) -> dict:
    youtube = packet.get("youtube") if isinstance(packet.get("youtube"), dict) else {}
    sections = [
        {
            "label": str(section.get("label", f"Section {idx}")),
            "script": str(section.get("script", "")),
            "visual": str(section.get("visual", "Resume teardown board with job-description highlights.")),
        }
        for idx, section in enumerate(youtube.get("scriptSections", []) or [], start=1)
        if isinstance(section, dict)
    ]
    props = first_short_props(packet)
    keywords = [str(item) for item in (props.get("jobKeywords") or props.get("missing", [])) if str(item).strip()][:5]
    if len(keywords) < 3:
        keywords = ["SQL", "Tableau", "cohort analysis", "churn dashboard"]

    voiceover_text = " ".join(
        str(section.get("script", ""))
        for section in sections
        if isinstance(section, dict)
    )
    return {
        "title": str(youtube.get("title") or packet.get("topic") or "Daily resume teardown"),
        "thesis": str(packet.get("thesis") or "A recruiter-style resume teardown that turns vague experience into role-specific proof."),
        "cta": str(youtube.get("cta") or "Paste the job description and check your free Signal score before you apply."),
        "sections": sections or build_fallback_packet({"topic": packet.get("topic", "Daily resume teardown"), "series": packet.get("series", "Daily"), "thesis": "", "hook": "", "keywords": keywords, "source_notes": []}, packet.get("publishDate", "daily"))["youtube"]["scriptSections"],
        "keywords": keywords,
        "weakBullets": props.get("weakBullets") or [
            "Supported cross-functional work without naming tools, scope, or outcome.",
            "Helped with projects related to the target role.",
            "Worked with teams to improve business results.",
        ],
        "beforeBullet": props.get("beforeBullet", "Helped with projects related to the target role."),
        "afterBullet": props.get("afterBullet", "Translated the same real work into role-specific tools, scope, and measurable proof."),
        "beforeScore": int(props.get("beforeScore", 34) or 34),
        "afterScore": int(props.get("afterScore", 92) or 92),
        "musicSrc": "audio/signal-quiet-orbit.wav",
        "musicVolume": 0.11,
        "voiceoverVolume": 0.94,
        "voiceover_text": voiceover_text[:3500],
        "voiceoverSegments": [],
    }


def build_thumbnail_props(packet: dict) -> dict:
    props = first_short_props(packet)
    keywords = [str(item) for item in props.get("missing", []) if str(item).strip()][:5]
    if len(keywords) < 3:
        keywords = ["SQL", "Tableau", "cohort analysis"]
    return {
        "title": "Qualified but invisible",
        "badge": str(packet.get("series") or "Resume teardown")[:32],
        "beforeScore": int(props.get("beforeScore", 34) or 34),
        "afterScore": int(props.get("afterScore", 92) or 92),
        "leftLabel": "Vague resume",
        "rightLabel": "Job-match proof",
        "keywords": keywords,
    }


def write_episode_thumbnail_and_manifest(packet: dict, packet_dir: Path, prepare_audio: bool, force_audio: bool) -> dict:
    date_slug = safe_slug(packet["publishDate"])
    topic_slug = safe_slug(packet["topic"])
    episode_props_path = REMOTION_DIR / f"props_daily_{date_slug}_{topic_slug}_episode.json"
    thumbnail_props_path = REMOTION_DIR / f"props_daily_{date_slug}_{topic_slug}_thumbnail.json"
    episode_out = f"daily-{topic_slug}-episode.mp4"
    thumbnail_out = f"daily-{topic_slug}-thumbnail.png"

    episode_props = build_episode_props(packet)
    thumbnail_props = build_thumbnail_props(packet)
    episode_props["audioReadiness"] = {
        "studioVoiceover": False,
        "quietMusic": public_asset_exists("audio/signal-quiet-orbit.wav"),
        "reason": "studio episode voiceover not requested",
    }
    if prepare_audio:
        if has_any_tts_config():
            fps = 30
            intro_frames = 8 * fps
            outro_frames = 18 * fps
            total_frames = 8 * 60 * fps
            usable_frames = total_frames - intro_frames - outro_frames
            sections = episode_props.get("sections", [])
            section_count = max(1, len(sections))
            section_frames = max(1, usable_frames // section_count)
            voiceover_segments = []
            for idx, section in enumerate(sections, start=1):
                if not isinstance(section, dict):
                    continue
                narration = str(section.get("voiceover") or section.get("script") or "").strip()
                if not narration:
                    continue
                voice_name = f"daily-{date_slug}-{topic_slug[:34]}-episode-{idx}-voiceover.mp3"
                voice_ref = f"audio/{voice_name}"
                provider = "cached"
                voice_result = {"src": voice_ref, "provider": provider, "captions": []}
                if force_audio or not public_asset_exists(voice_ref):
                    voice_result = generate_voiceover(narration[:2800], voice_name)
                    provider = voice_result.get("provider", "unknown")
                    voice_ref = voice_result.get("src") or voice_ref
                else:
                    alignment_ref = f"audio/{voice_name.rsplit('.', 1)[0]}.alignment.json"
                    alignment_path = REMOTION_AUDIO_DIR / Path(alignment_ref).name
                    if alignment_path.exists():
                        alignment = read_json(alignment_path, {})
                        provider = str(alignment.get("provider") or ("elevenlabs" if alignment.get("withTimestamps") else provider))
                        voice_result = {
                            "src": voice_ref,
                            "provider": provider,
                            "captions": alignment.get("captions", []),
                            "alignmentRef": alignment_ref,
                            "withTimestamps": bool(alignment.get("withTimestamps")),
                        }
                if public_asset_exists(voice_ref):
                    segment = {
                        "src": voice_ref,
                        "fromFrame": intro_frames + (idx - 1) * section_frames,
                        "volume": 0.94,
                        "provider": provider,
                    }
                    if voice_result.get("alignmentRef"):
                        segment["alignmentRef"] = voice_result["alignmentRef"]
                    if voice_result.get("captions"):
                        segment["captions"] = voice_result["captions"]
                    voiceover_segments.append(segment)
            if voiceover_segments:
                episode_props["voiceoverSegments"] = voiceover_segments
                episode_props["audioReadiness"] = {
                    "studioVoiceover": True,
                    "quietMusic": public_asset_exists("audio/signal-quiet-orbit.wav"),
                    "provider": voiceover_segments[0].get("provider", "unknown"),
                    "reason": f"{len(voiceover_segments)} episode sections ready",
                    "wordLevelCaptions": any(segment.get("captions") for segment in voiceover_segments),
                }
        else:
            episode_props["audioReadiness"]["reason"] = "No TTS provider is configured"

    episode_props_path.write_text(json.dumps(episode_props, indent=2), encoding="utf-8")
    thumbnail_props_path.write_text(json.dumps(thumbnail_props, indent=2), encoding="utf-8")

    manifest = {
        "date": packet["publishDate"],
        "topic": packet["topic"],
        "status": "render_ready_review_required",
        "episode": {
            "composition": "TeardownEpisode",
            "props": str(episode_props_path.relative_to(ROOT)),
            "output": f"marketing/remotion/out/{episode_out}",
            "format": "1920x1080",
            "status": "render_ready",
            "audioReadiness": episode_props.get("audioReadiness", {}),
        },
        "thumbnail": {
            "composition": "SignalThumbnail",
            "props": str(thumbnail_props_path.relative_to(ROOT)),
            "output": f"marketing/remotion/out/{thumbnail_out}",
            "format": "1280x720",
            "status": "render_ready",
        },
        "reviewGate": {
            "required": True,
            "checks": [
                "Render the episode and thumbnail.",
                "Verify the hook is visible in the opening seconds.",
                "Verify resume, job description, score movement, and Signal mascot are visible.",
                "Verify audio is studio-quality and music stays quiet.",
                "Verify no unsupported ATS, guarantee, or fake-experience claims.",
            ],
        },
    }
    (packet_dir / "channel_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def style_for_short(index: int, short: dict) -> dict:
    lower_text = f"{short.get('series', '')} {short.get('title', '')} {short.get('hook', '')}".lower()
    if "resume crime scene" in lower_text or "invisible" in lower_text:
        return {
            "creativeFormat": "resumeCrimeScene",
            "visualStyle": "highlighter",
            "formatArchetype": "deskMarkup",
            "pace": "fast",
            "seriesLabel": "Resume crime scene",
            "signalLines": {
                "hook": "I found the evidence.",
                "problem": "This bullet is hiding the proof.",
                "teardown": "Circle the vague part.",
                "fix": "Now the result is visible.",
                "cta": "Run the score first.",
            },
        }
    if "ai resume roast" in lower_text or "weather" in lower_text or "synergy" in lower_text:
        return {**SHORT_STYLE_ROTATION[0], "formatArchetype": "redTeamAudit"}
    if "signal mascot" in lower_text or "signal found" in lower_text or "rescue" in lower_text:
        return {**SHORT_STYLE_ROTATION[4], "formatArchetype": "mascotAssist"}
    if "myth" in lower_text or "wizard" in lower_text or "mind" in lower_text:
        return {**SHORT_STYLE_ROTATION[2], "formatArchetype": "recruiterSearch"}
    if "bullet" in lower_text or "mustache" in lower_text or "responsible for" in lower_text:
        return {**SHORT_STYLE_ROTATION[1], "formatArchetype": "deskMarkup"}
    if "search" in lower_text or "job description" in lower_text or "same resume" in lower_text:
        return {**SHORT_STYLE_ROTATION[3], "formatArchetype": "splitTranslation"}
    if "signal" in lower_text or "rescue" in lower_text:
        return {**SHORT_STYLE_ROTATION[4], "formatArchetype": "mascotAssist"}
    fallback = SHORT_STYLE_ROTATION[(index - 1) % len(SHORT_STYLE_ROTATION)]
    fallback_archetypes = ["redTeamAudit", "deskMarkup", "recruiterSearch", "splitTranslation", "mascotAssist"]
    return {**fallback, "formatArchetype": fallback_archetypes[(index - 1) % len(fallback_archetypes)]}


def normalize_signal_cta(value: object) -> str:
    cta = str(value or "").strip()
    lower_cta = cta.lower()
    if "free" in lower_cta and "signal" in lower_cta:
        return cta
    return "Check your free Signal score."


def write_short_briefs_and_props(packet: dict, packet_dir: Path, prepare_audio: bool, force_audio: bool) -> list[dict]:
    written = []
    date_slug = packet["publishDate"]
    topic_slug = safe_slug(packet["topic"])
    for idx, short in enumerate(packet.get("shorts", []), start=1):
        short_slug = f"{date_slug}-{topic_slug}-short-{idx}"
        brief_path = BRIEFS_DIR / f"{short_slug}.md"
        props_path = REMOTION_DIR / f"props_daily_{safe_slug(date_slug)}_{topic_slug}_short_{idx}.json"
        props = short.get("props") or {}
        props.setdefault("hook1", short.get("hook", "Resume invisible?")[:60])
        props.setdefault("hook2", "Check the match.")
        props.setdefault("subline", "Signal compares resume language to the target job.")
        props.setdefault("beforeScore", 38)
        props.setdefault("afterScore", 88)
        props.setdefault("cta", "Check your free Signal score.")
        if not props.get("lockTeardownCase"):
            _, _, _, _, props = apply_teardown_case(short, str(short.get("title", "")), str(short.get("hook", "")), str(short.get("script", "")), short.get("storyboard", []), props, idx)
        props.setdefault("missing", ["role language", "tool proof", "measurable result"])
        props.setdefault("voiceover_text", short.get("script", "")[:650])
        props["cta"] = normalize_signal_cta(props.get("cta"))
        job_keywords = [
            str(item)
            for item in (props.get("jobKeywords") or props.get("missing", ["role language", "tool proof", "measurable result"]))
        ][:5]
        if sum(1 for item in job_keywords if item.lower() in {"role language", "tools", "tool proof", "proof", "metrics", "measurable result"}) >= 2:
            job_keywords = ["role language", "tool proof", "measurable result"]
        style = style_for_short(idx, short)
        render_composition = str(props.get("renderComposition") or "ResumeCrimeScene")
        crime_scene_props = {
            "hook": short.get("hook", "This resume looks fine.")[:72],
            "subhook": str(props.get("subhook") or "The problem is vague proof, not fake experience."),
            "creativeFormat": str(props.get("creativeFormat") or style["creativeFormat"]),
            "visualStyle": str(props.get("visualStyle") or style["visualStyle"]),
            "formatArchetype": str(props.get("formatArchetype") or style["formatArchetype"]),
            "pace": str(props.get("pace") or style["pace"]),
            "seriesLabel": str(props.get("seriesOverride") or style["seriesLabel"]),
            "signalLines": props.get("signalLines") or style["signalLines"],
            "resumeName": props.get("resumeName", "Avery Johnson"),
            "resumeTitle": props.get("resumeTitle", "Role-Specific Resume"),
            "resumeMeta": props.get("resumeMeta", []),
            "jobTitle": props.get("jobTitle", "Target Role"),
            "jobKeywords": job_keywords,
            "weakBullets": props.get("weakBullets") or [
                "Supported cross-functional work without naming tools, scope, or outcome.",
                "Helped with projects related to the target role.",
                "Worked with teams to improve business results.",
            ],
            "beforeBullet": props.get("beforeBullet", "Helped with projects related to the target role."),
            "afterBullet": props.get("afterBullet", "Translated the same real work into role-specific tools, scope, and measurable proof."),
            "resumeDocument": props.get("resumeDocument"),
            "jobDescription": props.get("jobDescription"),
            "beforeScore": int(props.get("beforeScore", 38)),
            "afterScore": int(props.get("afterScore", 88)),
            "scoreBasis": props.get("scoreBasis", []),
            "score_rubric": props.get("score_rubric") or props.get("scoreRubric"),
            "scoreRubric": props.get("scoreRubric") or props.get("score_rubric"),
            "scoreLabel": props.get("scoreLabel", "Signal Fit Score"),
            "evidenceLedger": props.get("evidenceLedger", {}),
            "humanReadBeats": props.get("humanReadBeats", []),
            "markedLabel": props.get("markedLabel", "Too vague"),
            "problemPunchline": props.get("problemPunchline", "Recruiters search for proof, not vibes."),
            "teardownPunchline": props.get("teardownPunchline", "This is the part costing you interviews."),
            "fixPunchline": props.get("fixPunchline", "No fake experience. Just clearer evidence."),
            "teardownIssues": props.get("teardownIssues", ["No role language", "No tools", "No measurable proof"]),
            "cta": normalize_signal_cta(props.get("cta")),
            "musicSrc": "audio/signal-quiet-orbit.wav",
            "musicVolume": 0.16,
            "avatarLabel": "Recruiter review",
        }
        crime_scene_props["voiceDirector"] = voice_director_contract(short, props)
        lower_text = f"{short.get('title', '')} {short.get('hook', '')}".lower()
        if "linkedin breath" in lower_text or "airport" in lower_text:
            crime_scene_props["hook"] = "Your AI resume has LinkedIn breath."
            crime_scene_props["subhook"] = "Polished. Beige. Missing the role language."
            crime_scene_props["creativeFormat"] = "aiResumeRoast"
            crime_scene_props["visualStyle"] = "comic"
            crime_scene_props["formatArchetype"] = "redTeamAudit"
            crime_scene_props["pace"] = "fast"
        elif "mustache" in lower_text:
            crime_scene_props["hook"] = "This bullet is wearing a fake mustache."
            crime_scene_props["subhook"] = "It looks busy, but says almost nothing."
            crime_scene_props["creativeFormat"] = "oneBulletFix"
            crime_scene_props["visualStyle"] = "highlighter"
            crime_scene_props["formatArchetype"] = "deskMarkup"
            crime_scene_props["pace"] = "fast"
        elif "wizard" in lower_text or "mind" in lower_text:
            crime_scene_props["hook"] = "The ATS is not a wizard."
            crime_scene_props["subhook"] = "It searches what you actually wrote."
            crime_scene_props["creativeFormat"] = "atsMythLab"
            crime_scene_props["visualStyle"] = "terminal"
            crime_scene_props["formatArchetype"] = "recruiterSearch"
            crime_scene_props["pace"] = "balanced"
        voice_ref = props.get("voiceoverSrc", "audio/signal-studio-voiceover.mp3")
        sfx_ref = props.get("sfxSrc", "audio/signal-studio-sfx.mp3")
        if public_asset_exists(voice_ref):
            crime_scene_props["voiceoverSrc"] = voice_ref
            crime_scene_props["voiceoverVolume"] = 0.92
        if public_asset_exists(sfx_ref):
            crime_scene_props["sfxSrc"] = sfx_ref
            crime_scene_props["sfxVolume"] = 0.04
        audio_slug = safe_audio_slug(date_slug, short.get("title", f"short-{idx}"), idx)
        crime_scene_props = attach_daily_audio(crime_scene_props, short, audio_slug, prepare_audio, force_audio)

        brief = [
            f"# {short.get('title', 'Signal short')}",
            "",
            f"Daily packet: `{packet_dir.name}`",
            f"Series: {short.get('series', '')}",
            f"Hook: {short.get('hook', '')}",
            "",
            "## Script",
            "",
            short.get("script", ""),
            "",
            "## Storyboard",
            "",
        ]
        brief.extend(f"- {step}" for step in short.get("storyboard", []))
        brief.extend([
            "",
            "## Render Props",
            "",
            f"`{props_path.relative_to(ROOT)}`",
            "",
            f"Composition: `{render_composition}`",
            "",
            "## QA",
            "",
            "- Keep Signal mascot visible.",
            "- Keep captions readable on mobile.",
            "- No unsupported auto-reject, guarantee, or fake-outcome claims.",
            f"- Audio readiness: `{crime_scene_props.get('audioReadiness', {}).get('reason', 'unknown')}`.",
            "- Queue as review_required after rendering.",
        ])
        brief_path.write_text("\n".join(brief), encoding="utf-8")
        props_path.write_text(json.dumps(crime_scene_props, indent=2), encoding="utf-8")
        written.append({
            "brief": str(brief_path.relative_to(ROOT)),
            "props": str(props_path.relative_to(ROOT)),
            "title": short.get("title", "Signal short"),
            "composition": render_composition,
            "audioReadiness": crime_scene_props.get("audioReadiness", {}),
        })
    return written


def build_youtube_caption(packet: dict) -> str:
    youtube = packet.get("youtube") if isinstance(packet.get("youtube"), dict) else {}
    title = str(youtube.get("title") or packet.get("topic") or "Signal resume teardown").rstrip(".")
    cta = str(youtube.get("cta") or "Check your free Signal score before you apply.").rstrip(".")
    return f"{title}. {cta}. #jobsearch #resumehelp #careeradvice #resumetips"


def build_youtube_longform_draft(packet: dict, channel_manifest: dict) -> dict | None:
    episode = channel_manifest.get("episode") if isinstance(channel_manifest.get("episode"), dict) else {}
    youtube = packet.get("youtube") if isinstance(packet.get("youtube"), dict) else {}
    output = str(episode.get("output") or "")
    if not output:
        return None

    filename = Path(output).name
    title = str(youtube.get("seoTitle") or youtube.get("title") or packet.get("topic") or filename)[:96]
    description = str(youtube.get("description") or build_youtube_caption(packet))
    thumbnail = channel_manifest.get("thumbnail") if isinstance(channel_manifest.get("thumbnail"), dict) else {}

    return {
        "title": title,
        "caption": build_youtube_caption(packet),
        "file": f"videos/{filename}",
        "platforms": ["youtube"],
        "scheduleDate": None,
        "status": "review_required",
        "contentType": "youtube_long_form",
        "youtubeKind": "long_form",
        "target": "daily long-form YouTube",
        "youtubeTitle": title,
        "youtubeDescription": description,
        "composition": episode.get("composition", "TeardownEpisode"),
        "renderProps": episode.get("props"),
        "thumbnail": thumbnail.get("output"),
        "thumbnailProps": thumbnail.get("props"),
        "renderStatus": "render_required",
        "reviewStatus": "review_required",
        "audioReadiness": episode.get("audioReadiness", {}),
        "qaGate": {
            "required": True,
            "passed": False,
            "status": "requires_render_review",
            "minExpertViralScore": 94,
            "checks": [
                "Rendered MP4 exists in marketing/autopost/videos.",
                "16:9 layout is readable on desktop and mobile YouTube surfaces.",
                "Opening hook is visible in the first 5 seconds.",
                "Signal mascot or brand mark is visible.",
                "No old human presenter appears unless explicitly approved.",
                "Audio is present, balanced, and not dominated by music or effects.",
                "Claims avoid ATS auto-reject myths, guarantees, fake outcomes, and unsourced competitor rankings.",
                "Thumbnail exists or is intentionally deferred.",
                "Human reviewer approved exact file, title, description, thumbnail, and platform target.",
            ],
        },
        "expertViralGate": {
            "required": True,
            "minScore": 94,
            "score": None,
            "passed": False,
            "status": "requires_expert_viral_review",
        },
        "reviewChecklist": [
            "long-form render reviewed",
            "thumbnail reviewed",
            "audio present and balanced",
            "claims reviewed",
            "exact YouTube title and description reviewed",
            "status remains review_required until approval",
        ],
    }


def update_calendar(packet: dict, packet_dir: Path, written_shorts: list[dict], channel_manifest: dict) -> None:
    if CALENDAR_PATH.exists():
        try:
            calendar = json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
        except Exception:
            calendar = []
    else:
        calendar = []

    entry = {
        "date": packet["publishDate"],
        "topic": packet["topic"],
        "series": packet.get("series", ""),
        "packet": str(packet_dir.relative_to(ROOT)),
        "youtube": {
            "title": packet["youtube"].get("title", ""),
            "status": "render_ready_review_required",
            "target": "daily long-form YouTube",
            "manifest": str((packet_dir / "channel_manifest.json").relative_to(ROOT)),
            "props": channel_manifest.get("episode", {}).get("props"),
            "output": channel_manifest.get("episode", {}).get("output"),
            "autopostDraft": str((packet_dir / "autopost_drafts.json").relative_to(ROOT)),
            "qaGate": {
                "required": True,
                "passed": False,
                "status": "requires_render_review",
            },
        },
        "thumbnail": channel_manifest.get("thumbnail", {}),
        "shorts": [
            {
                "title": item["title"],
                "brief": item["brief"],
                "props": item["props"],
                "status": "render_ready",
                "audioReadiness": item.get("audioReadiness", {}),
            }
            for item in written_shorts
        ],
        "creativeQuality": packet.get("creativeQualityGate", {}),
        "reviewStatus": (
            "needs_render_and_review"
            if packet.get("creativeQualityGate", {}).get("passed")
            else "needs_creator_revision_before_render"
        ),
    }

    calendar = [item for item in calendar if item.get("date") != packet["publishDate"] or item.get("topic") != packet["topic"]]
    calendar.append(entry)
    calendar.sort(key=lambda item: (item.get("date", ""), item.get("topic", "")))
    CALENDAR_PATH.write_text(json.dumps(calendar, indent=2), encoding="utf-8")


def build_daily_caption(short: dict) -> str:
    def sentence(value: str) -> str:
        text = str(value).strip()
        if not text:
            return ""
        return text if text[-1] in ".?!" else f"{text}."

    title = sentence(str(short.get("title", "Resume teardown")))
    hook = sentence(str(short.get("hook", "")))
    title_norm = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
    hook_norm = re.sub(r"[^a-z0-9]+", " ", hook.lower()).strip()
    def compact_caption_text(value: str) -> str:
        words = [word for word in re.sub(r"[^a-z0-9]+", " ", value.lower()).split() if word not in {"this", "the", "a", "an", "resume"}]
        return " ".join(words)

    title_compact = compact_caption_text(title)
    hook_compact = compact_caption_text(hook)
    hook_part = "" if hook_norm and (
        hook_norm == title_norm
        or hook_norm in title_norm
        or (hook_compact and (hook_compact == title_compact or hook_compact in title_compact))
    ) else hook
    props = short.get("props") if isinstance(short.get("props"), dict) else {}
    before = props.get("beforeScore")
    after = props.get("afterScore")
    missing = [str(item).strip() for item in props.get("missing", []) if str(item).strip()]
    score_part = f"{before}->{after}" if isinstance(before, int) and isinstance(after, int) else ""
    missing_part = ", ".join(missing[:3])
    archetype = str(props.get("formatArchetype") or "")
    lesson = "The fix is not fake experience; it is making the proof searchable."
    if missing_part and score_part:
        if archetype == "recruiterSearch":
            lesson = f"Search miss: {missing_part}. Rewrite adds visible proof, so the score can move: {score_part}."
        elif archetype == "splitTranslation":
            lesson = f"Answer-key miss: {missing_part}. Rewrite puts stack, metric, and outcome on screen: {score_part}."
        else:
            lesson = f"Why it starts low: {missing_part}. Rewrite adds the missing tool, metric, and outcome: {score_part}."
    base = re.sub(
        r"\s+",
        " ",
        f"{title} {hook_part} {lesson} Run the free Signal score before you apply.",
    ).strip()
    tags = "#jobsearch #resumehelp #careertok #resumetips #airesume"
    caption = f"{base} {tags}"
    if len(caption) > 280:
        caption = f"{title} Show the missing proof first, score jump second. Run the free Signal score before you apply. {tags}"
    return caption


def write_render_commands(packet_dir: Path, written_shorts: list[dict], channel_manifest: dict) -> None:
    commands = [
        "# Run from marketing/remotion",
        "# These render-ready props produce the daily YouTube episode, thumbnail, and Shorts.",
        "# Review still frames before posting.",
        "",
    ]
    episode = channel_manifest.get("episode", {})
    thumbnail = channel_manifest.get("thumbnail", {})
    if episode.get("props") and episode.get("output"):
        props = str(episode["props"]).replace("\\", "/").replace("marketing/remotion/", "")
        output = str(episode["output"]).replace("\\", "/").replace("marketing/remotion/", "")
        voiceover_script = str((packet_dir / "longform_voiceover.md").relative_to(ROOT)).replace("\\", "/")
        manifest = str((packet_dir / "channel_manifest.json").relative_to(ROOT)).replace("\\", "/")
        commands.append(
            f"node scripts/generate_episode_voiceover.mjs --props {props} --script {voiceover_script} --manifest {manifest} --require-elevenlabs"
        )
        commands.append(f"npx remotion render TeardownEpisode {output} --props={props}")
    if thumbnail.get("props") and thumbnail.get("output"):
        props = str(thumbnail["props"]).replace("\\", "/").replace("marketing/remotion/", "")
        output = str(thumbnail["output"]).replace("\\", "/").replace("marketing/remotion/", "")
        commands.append(f"npx remotion still SignalThumbnail {output} --props={props}")
    if len(commands) > 4:
        commands.append("")
    for item in written_shorts:
        props = item["props"].replace("\\", "/").replace("marketing/remotion/", "")
        out_name = f"daily-{safe_slug(item['title'])}.mp4"
        composition = item.get("composition", "ResumeCrimeScene")
        commands.append(f"npx remotion render {composition} out/{out_name} --props={props}")
    (packet_dir / "render_commands.ps1").write_text("\n".join(commands), encoding="utf-8")


def write_autopost_drafts(packet: dict, packet_dir: Path, written_shorts: list[dict], channel_manifest: dict) -> None:
    shorts_by_title = {short.get("title"): short for short in packet.get("shorts", []) if isinstance(short, dict)}
    drafts = []
    youtube_draft = build_youtube_longform_draft(packet, channel_manifest)
    if youtube_draft:
        drafts.append(youtube_draft)
    for item in written_shorts:
        title = item["title"]
        short = shorts_by_title.get(title, {"title": title, "hook": title})
        out_name = f"daily-{safe_slug(title)}.mp4"
        drafts.append({
            "title": title[:96],
            "caption": build_daily_caption(short),
            "file": f"videos/{out_name}",
            "platforms": ["tiktok", "instagram", "youtube"],
            "scheduleDate": None,
            "status": "review_required",
            "renderProps": item["props"],
            "composition": item.get("composition", "ResumeCrimeScene"),
            "audioReadiness": item.get("audioReadiness", {}),
        })
    (packet_dir / "autopost_drafts.json").write_text(json.dumps(drafts, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily Signal content agent: YouTube episode + Shorts packets.")
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    parser.add_argument("--topic", default=None, help="Optional specific daily topic.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    parser.add_argument("--prepare-audio", action="store_true", help="Generate ElevenLabs voiceover files when credentials are configured.")
    parser.add_argument("--force-audio", action="store_true", help="Regenerate daily voiceover files even if cached files exist.")
    parser.add_argument("--require-elevenlabs", action="store_true", help="Fail instead of falling back when ElevenLabs timestamped narration is unavailable.")
    parser.add_argument("--check-elevenlabs", action="store_true", help="Validate ElevenLabs key, voice access, and optional TTS probe.")
    parser.add_argument("--probe-elevenlabs-tts", action="store_true", help="With --check-elevenlabs, run a tiny timestamped TTS request.")
    args = parser.parse_args()

    ensure_dirs()
    if args.require_elevenlabs:
        os.environ["REQUIRE_ELEVENLABS"] = "true"
    if args.check_elevenlabs:
        health = check_elevenlabs_health(args.probe_elevenlabs_tts)
        if args.json:
            print(json.dumps(health, indent=2))
        else:
            print("ElevenLabs configured:", health["configured"])
            print("Voices readable:", health["voicesReadable"])
            print("Selected voice:", health.get("selectedVoice"))
            print("TTS probe:", health.get("ttsProbe"))
            for issue in health.get("issues", []):
                print("Issue:", issue)
        return

    seed = choose_seed(args.topic)
    packet = normalize_packet(maybe_generate_with_openai(seed, args.date), seed, args.date)
    topic_slug = safe_slug(packet.get("topic", seed["topic"]))
    packet_dir = PACKETS_DIR / f"{args.date}-{topic_slug}"
    packet_dir.mkdir(parents=True, exist_ok=True)

    (packet_dir / "packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
    (packet_dir / "source_notes.json").write_text(json.dumps(packet.get("sourceNotes", []), indent=2), encoding="utf-8")
    write_markdown_packet(packet, packet_dir)
    channel_manifest = write_episode_thumbnail_and_manifest(packet, packet_dir, args.prepare_audio, args.force_audio)
    written_shorts = write_short_briefs_and_props(packet, packet_dir, args.prepare_audio, args.force_audio)
    write_render_commands(packet_dir, written_shorts, channel_manifest)
    write_autopost_drafts(packet, packet_dir, written_shorts, channel_manifest)
    update_calendar(packet, packet_dir, written_shorts, channel_manifest)

    result = {
        "packet": str(packet_dir.relative_to(ROOT)),
        "youtube": str((packet_dir / "youtube_episode.md").relative_to(ROOT)),
        "channelManifest": str((packet_dir / "channel_manifest.json").relative_to(ROOT)),
        "shorts": written_shorts,
        "autopostDrafts": str((packet_dir / "autopost_drafts.json").relative_to(ROOT)),
        "calendar": str(CALENDAR_PATH.relative_to(ROOT)),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("[+] Daily content packet created")
        print(f"    Packet: {result['packet']}")
        print(f"    YouTube: {result['youtube']}")
        print(f"    Shorts: {len(written_shorts)} render-ready briefs")


if __name__ == "__main__":
    main()
