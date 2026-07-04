import argparse
import base64
import json
import os
import re
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
DEFAULT_ELEVENLABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
LEGACY_ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
ELEVENLABS_VOICE_CACHE: dict | None = None
ELEVENLABS_DISABLED_REASON: str | None = None


TREND_SEEDS = [
    {
        "topic": "AI resumes all sound the same, so recruiters search for proof",
        "series": "Recruiter Search Test",
        "thesis": "AI-written resumes can look polished while still missing the exact role language and proof recruiters search for.",
        "hook": "Your AI resume sounds professional. That might be the problem.",
        "keywords": ["AI resume", "recruiter search", "proof points", "job description"],
        "source_notes": [
            {
                "title": "YouTube Partner Program eligibility",
                "url": "https://support.google.com/youtube/answer/72851",
                "note": "Use YouTube as a monetization target, but optimize first for site conversions.",
            },
            {
                "title": "Pew Research Center Social Media Fact Sheet",
                "url": "https://www.pewresearch.org/internet/fact-sheet/social-media/",
                "note": "YouTube, Instagram, and TikTok are large discovery channels for job-search education.",
            },
        ],
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
    "Open with a frustrated job-hunter joke or painfully relatable line in the first 2 seconds.",
    "Make the viewer laugh before teaching: rage scrolling, spreadsheet of applications, 'professional yap' bullets, or AI resume sameness.",
    "Keep the resume/job description on screen as the main character; Signal mascot is the mischievous guide, not a corporate presenter.",
    "Use blunt recruiter-reacts energy: roast the bullet, then rescue the person.",
    "Every joke must punch at the broken job-search process or vague resume language, never at unemployed people.",
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
        "visualStyle": "stickyNote",
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
    "rude",
    "beige",
    "fake mustache",
    "airport",
    "airplane mode",
    "yap",
    "rage",
    "hoodie",
    "roast",
    "side-eye",
    "mind-reading",
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
]

TEARDOWN_CASES = [
    {
        "id": "demand_gen_marketing",
        "resumeName": "Jordan Lee",
        "resumeTitle": "Marketing Coordinator -> Demand Gen Candidate",
        "resumeMeta": ["3 yrs B2B SaaS", "HubSpot admin", "Paid social support"],
        "jobTitle": "Demand Generation Manager",
        "jobKeywords": ["HubSpot workflows", "LinkedIn Ads", "CAC analysis", "MQL-to-SQL", "pipeline sourced"],
        "weakBullets": [
            "Supported email and social campaigns across multiple channels.",
            "Helped maintain HubSpot lists for webinars and nurture emails.",
            "Coordinated paid social assets with design and sales.",
        ],
        "beforeBullet": "Helped maintain HubSpot lists for webinars and nurture emails.",
        "afterBullet": "Built HubSpot lead-scoring and LinkedIn retargeting segments that cut CAC 32% and lifted MQL-to-SQL conversion 18%.",
        "beforeScore": 34,
        "afterScore": 92,
        "markedLabel": "Buried proof",
        "shortTitle": "This marketing resume hid the actual revenue proof",
        "hook": "This marketing resume sounds busy. Recruiters need revenue proof.",
        "subhook": "The job asks for tools, metrics, and pipeline impact.",
        "problemPunchline": "A recruiter cannot search for proof you buried.",
        "teardownIssues": ["Tool is hidden", "No CAC result", "No pipeline language"],
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
        "markedLabel": "No quota signal",
        "shortTitle": "This sales resume forgot to say sales",
        "hook": "This sales resume has conversations. The job needs pipeline.",
        "subhook": "Salesforce, discovery, quota, and MEDDICC are missing on screen.",
        "problemPunchline": "Sales resumes need numbers faster than adjectives.",
        "teardownIssues": ["No quota proof", "No CRM signal", "No pipeline number"],
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
        "shortTitle": "This developer resume hides the stack",
        "hook": "This developer resume says frontend. The job searches React.",
        "subhook": "The stack and impact are the search signal.",
        "problemPunchline": "Engineering resumes need proof of stack plus outcome.",
        "teardownIssues": ["Stack is vague", "No shipped feature", "No performance result"],
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
        "markedLabel": "No delivery proof",
        "shortTitle": "This PM resume is organized but not searchable",
        "hook": "This project manager resume looks organized. It still misses the job.",
        "subhook": "Jira, risk, stakeholders, and variance need to show up.",
        "problemPunchline": "PM bullets should prove delivery, not just calendar ownership.",
        "teardownIssues": ["No Jira signal", "No risk language", "No variance result"],
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
        "markedLabel": "No retention proof",
        "shortTitle": "This customer success resume forgot the renewal story",
        "hook": "This CSM resume sounds helpful. The job needs retention proof.",
        "subhook": "Gainsight, QBRs, NPS, and renewal risk are the clues.",
        "problemPunchline": "Helpful is nice. Retention proof gets searched.",
        "teardownIssues": ["No renewal metric", "No platform signal", "No account scope"],
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
        "shortTitle": "This nursing resume buries care coordination",
        "hook": "This nursing resume says patient care. The role asks coordination.",
        "subhook": "Epic, discharge planning, and education need to be visible.",
        "problemPunchline": "Clinical proof has to be specific and careful.",
        "teardownIssues": ["No Epic signal", "No discharge scope", "No patient education result"],
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
    "demand_gen_marketing": "Corporate weather report: high synergy, zero proof.",
    "sales_account_exec": "Pipeline proof is hiding under a hoodie.",
    "frontend_engineer": "The tech stack is wearing a fake mustache.",
    "project_manager": "The calendar is talking. Proof is in airplane mode.",
    "customer_success": "Helpful-sounding customer success yap.",
    "healthcare_rn": "Clinical proof is doing mind-reading homework.",
}

CASE_SPOKEN_REWRITES = {
    "demand_gen_marketing": "built lead scoring and retargeting that cut CAC 32 percent",
    "sales_account_exec": "generated 1.8 million in qualified Salesforce pipeline",
    "frontend_engineer": "shipped React and TypeScript checkout work that reduced drop-off 14 percent",
    "project_manager": "owned the Jira roadmap and cut schedule variance to 6 percent",
    "customer_success": "flagged renewal risk and protected 420 thousand in ARR",
    "healthcare_rn": "coordinated Epic discharge plans and reduced avoidable follow-up calls",
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
    load_dotenv(ROOT / "marketing_agent" / ".env")
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or key == "sk-proj-your_openai_api_key_here" or OpenAI is None:
        return None
    return OpenAI(api_key=key)


def load_elevenlabs_config() -> dict:
    load_dotenv(ROOT / "marketing_agent" / ".env")
    key = os.getenv("ELEVENLABS_API_KEY", "")
    if key == "your_elevenlabs_api_key_here":
        key = ""
    return {
        "apiKey": key,
        "voiceId": os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID),
        "modelId": os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
    }


def load_openai_tts_config() -> dict:
    load_dotenv(ROOT / "marketing_agent" / ".env")
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
                        "stability": 0.48,
                        "similarity_boost": 0.82,
                        "style": 0.28,
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


def write_alignment_metadata(dest_name: str, payload: dict) -> dict:
    alignment = payload.get("normalized_alignment") or payload.get("alignment") or {}
    captions = normalize_alignment_to_captions(alignment if isinstance(alignment, dict) else {})
    meta_name = dest_name.rsplit(".", 1)[0] + ".alignment.json"
    meta_path = REMOTION_AUDIO_DIR / meta_name
    metadata = {
        "provider": "elevenlabs",
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


def generate_elevenlabs_voiceover(text: str, dest_name: str) -> dict:
    config = load_elevenlabs_config()
    if not config["apiKey"]:
        return {"src": None, "provider": "none", "captions": []}

    voice = resolve_elevenlabs_voice(config)
    voice_id = voice["voiceId"]
    dest_path = REMOTION_AUDIO_DIR / dest_name
    payload = {
        "text": text,
        "model_id": config["modelId"],
        "voice_settings": {
            "stability": 0.48,
            "similarity_boost": 0.82,
            "style": 0.28,
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
                **write_alignment_metadata(dest_name, data),
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
            except Exception as error:
                detail = elevenlabs_error_text(error)
                print(f"[!] ElevenLabs voiceover unavailable, falling back when possible: {detail}")
    if load_openai_tts_config()["apiKey"]:
        return generate_openai_voiceover(text, dest_name)
    return {"src": None, "provider": "none", "withTimestamps": False, "captions": []}


def attach_daily_audio(crime_scene_props: dict, short: dict, short_slug: str, prepare_audio: bool, force_audio: bool) -> dict:
    voiceover_text = str(
        short.get("props", {}).get("voiceover_text")
        or short.get("script")
        or crime_scene_props.get("hook")
        or ""
    )[:900]
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
            voice_result = {
                "src": voice_ref,
                "provider": provider,
                "withTimestamps": bool(alignment.get("withTimestamps")),
                "captions": alignment.get("captions", []),
                "alignmentRef": alignment_ref,
            }

    if public_asset_exists(voice_ref):
        crime_scene_props["voiceoverSrc"] = voice_ref
        crime_scene_props["voiceoverVolume"] = 0.94
        if voice_result.get("captions"):
            crime_scene_props["captions"] = voice_result["captions"]
            crime_scene_props["captionReadiness"] = {
                "wordLevel": True,
                "provider": voice_result.get("provider", provider),
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


def build_fallback_packet(seed: dict, publish_date: str) -> dict:
    topic = seed["topic"]
    hook = seed["hook"]
    keywords = seed["keywords"]
    episode_title = f"{hook} | Resume Teardown"
    shorts = [
        {
            "series": "AI Resume Roast",
            "title": "Corporate weather report resume",
            "hook": "This bullet has a high chance of synergy and zero proof.",
            "script": (
                "This bullet has a high chance of synergy and zero proof. It says results-driven team player, "
                "which sounds expensive and tells me almost nothing. The job asks for HubSpot, CAC, LinkedIn Ads, "
                "and pipeline impact. Signal pulls the real proof out of the corporate weather report before you apply."
            ),
            "storyboard": [
                "Open with a fake weather alert: 'High chance of synergy.'",
                "Signal side-eyes a polished but empty resume bullet.",
                "Job description terms pop in like warning labels.",
                "Signal points to the missing proof chips.",
                "Reveal free Signal score and CTA.",
            ],
            "props": {
                "hook1": "Corporate weather report.",
                "hook2": "Zero proof.",
                "subline": "AI polish can hide the actual evidence.",
                "beforeScore": 31,
                "afterScore": 86,
                "missing": ["HubSpot", "CAC", "LinkedIn Ads", "pipeline"],
                "cta": "Check your free Signal score.",
                "voiceover_text": (
                    "This bullet has a high chance of synergy and zero proof. It says results-driven team player, "
                    "which sounds expensive and tells me almost nothing. The job asks for HubSpot, CAC, LinkedIn Ads, "
                    "and pipeline impact. Signal pulls the real proof out of the corporate weather report before you apply."
                ),
            },
        },
        {
            "series": "Recruiter Search Test",
            "title": "Would your resume appear in search?",
            "hook": "If I search HubSpot, does your resume even show up?",
            "script": (
                "If I search HubSpot, does your resume even show up? The job description says HubSpot, CAC, "
                "LinkedIn Ads, and lifecycle marketing. Your resume says helped with campaigns. That might be true, "
                "but it is not searchable enough. Signal translates the real work into role language."
            ),
            "storyboard": [
                "Show a recruiter search box typing HubSpot.",
                "Resume returns no match and Signal looks concerned.",
                "Paste the job description next to the resume.",
                "Highlight the missing role terms.",
                "Rewrite the bullet and rerun the search.",
                "CTA to free score.",
            ],
            "props": {
                "hook1": "Search box test.",
                "hook2": "No match found.",
                "subline": "Recruiters search for role language and proof.",
                "beforeScore": 34,
                "afterScore": 92,
                "missing": ["HubSpot", "CAC", "LinkedIn Ads", "lifecycle marketing"],
                "cta": "Run your free Signal score.",
                "voiceover_text": (
                    "If I search HubSpot, does your resume even show up? The job description says HubSpot, CAC, "
                    "LinkedIn Ads, and lifecycle marketing. Your resume says helped with campaigns. That might be true, "
                    "but it is not searchable enough. Signal translates the real work into role language."
                ),
            },
        },
        {
            "series": "Resume Crime Scene",
            "title": "Resume Crime Scene: Hidden Proof",
            "hook": "This resume is invisible because the best bullet is buried.",
            "script": (
                "This resume is invisible because the best bullet is buried. Signal is giving it dramatic side-eye, "
                "because helped with campaigns could mean almost anything. The job description asks for HubSpot, CAC, "
                "LinkedIn Ads, and pipeline impact. So we turn the same real experience into: cut CAC by thirty two percent "
                "through LinkedIn Ads audience segmentation and HubSpot lead scoring. Same person. Better signal."
            ),
            "storyboard": [
                "Open with a Resume Crime Scene tape over the weak bullet.",
                "Signal side-eyes 'helped with campaigns' and waves a tiny red flag.",
                "Pin the job description clues: HubSpot, CAC, LinkedIn Ads, pipeline.",
                "Signal points from the vague bullet to the corrected proof bullet.",
                "Score jumps from 38/100 to 91/100 while Signal celebrates.",
                "CTA to the free Signal score.",
            ],
            "props": {
                "hook1": "Resume Crime Scene.",
                "hook2": "Hidden proof.",
                "subline": "The fix is translation, not fabrication.",
                "beforeScore": 38,
                "afterScore": 91,
                "missing": ["HubSpot", "CAC", "LinkedIn Ads", "pipeline"],
                "cta": "Check your free Signal score.",
                "voiceover_text": (
                    "This resume is invisible because the best bullet is buried. Signal is giving it dramatic side-eye, "
                    "because helped with campaigns could mean almost anything. The job description asks for HubSpot, CAC, "
                    "LinkedIn Ads, and pipeline impact. So we turn the same real experience into: cut CAC by thirty two percent "
                    "through LinkedIn Ads audience segmentation and HubSpot lead scoring. Same person. Better signal."
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
        "youtube": {
            "title": episode_title,
            "seoTitle": f"{hook} | Resume Teardown with Signal by ATSHacker",
            "description": (
                "A funny recruiter-style teardown of why a qualified resume can be hard to find, "
                "how to translate a job description into resume proof, and where Signal fits without fake claims."
            ),
            "chapters": [
                "0:00 Cold open",
                "0:30 The resume problem",
                "1:45 The job description translation",
                "3:30 Live teardown",
                "6:30 Bullet rewrite",
                "8:00 Signal score and takeaway",
                "9:00 CTA",
            ],
            "scriptSections": [
                {
                    "label": "Cold open",
                    "script": f"{hook} Today we are lovingly roasting a resume that looks professional but has the job-description equivalent of airplane mode turned on.",
                    "visual": "Cold open with comic red stamp, quick zoom, Signal mascot reaction, and resume/JD split screen.",
                },
                {
                    "label": "The real problem",
                    "script": "Most resumes are not failing because the person is unqualified. They fail because the resume says 'helped with stuff' while the job description is asking for a specific toolkit.",
                    "visual": "Resume on left, job description on right, mismatched terms highlighted with funny labels.",
                },
                {
                    "label": "Translate the job",
                    "script": "Before rewriting anything, pull out the role title, tools, responsibilities, metrics, and proof signals the job actually asks for.",
                    "visual": "Keyword extraction board.",
                },
                {
                    "label": "Teardown",
                    "script": "Now compare the resume line by line. Vague bullets like 'helped with campaigns' do not give recruiters the same signal as specific tools, scope, and outcomes.",
                    "visual": "Red/yellow markups over weak bullets.",
                },
                {
                    "label": "Fix one bullet",
                    "script": "The fix is not to invent experience. The fix is to say the real work clearly: what tool, what scope, what audience, what result.",
                    "visual": "Before/after bullet rewrite.",
                },
                {
                    "label": "Product bridge",
                    "script": "Signal automates this comparison. Paste the job description, upload the resume, and see the free score first. If the gap is real, then the paid resume and cover letter bundle makes sense.",
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
    text_parts = []
    if isinstance(short, dict):
        text_parts.extend([
            short.get("series", ""),
            short.get("title", ""),
            short.get("hook", ""),
            short.get("script", ""),
        ])
    if isinstance(props, dict):
        text_parts.extend([
            props.get("resumeTitle", ""),
            props.get("jobTitle", ""),
            props.get("beforeBullet", ""),
            props.get("afterBullet", ""),
            " ".join(str(item) for item in props.get("missing", []) or []),
            " ".join(str(item) for item in props.get("jobKeywords", []) or []),
        ])
    blob = " ".join(str(part).lower() for part in text_parts)

    role_markers = {
        "demand_gen_marketing": ["hubspot", "linkedin ads", "cac", "demand", "marketing"],
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
    generic_markers = sum(1 for marker in ["hubspot", "cac", "linkedin ads"] if marker in blob)
    if best_score >= 2 and generic_markers < 3:
        return best_case
    return TEARDOWN_CASES[(index - 1) % len(TEARDOWN_CASES)]


def build_case_voiceover(case: dict) -> str:
    keywords = case["jobKeywords"]
    humor_line = CASE_HUMOR_LINES.get(case["id"], "Right now the bullet is professional yap: polite, busy, and allergic to numbers.")
    spoken_rewrite = CASE_SPOKEN_REWRITES.get(case["id"], case["afterBullet"])
    return (
        f"{case['hook']} Target: {case['jobTitle']}. "
        f"JD asks for {keywords[0]}, {keywords[1]}, {keywords[2]}. "
        f"{humor_line} Resume says: {case['beforeBullet']} "
        f"Real, but buried. Better: {spoken_rewrite}. "
        f"Same person, clearer proof. {case['beforeScore']} to {case['afterScore']}. "
        "Check your free Signal score before you apply."
    )


def build_case_storyboard(case: dict) -> list[str]:
    return [
        f"Open on the weak {case['resumeTitle']} with the score at {case['beforeScore']}/100.",
        f"Show the target role: {case['jobTitle']}.",
        f"Highlight missing terms: {', '.join(case['jobKeywords'][:3])}.",
        f"Circle the weak bullet: {case['beforeBullet']}",
        "Signal points at the missing proof instead of taking over the scene.",
        f"Reveal the rewrite: {case['afterBullet']}",
        f"Score jumps to {case['afterScore']}/100.",
        "End on the free Signal score CTA with UTM-ready posting metadata.",
    ]


def apply_teardown_case(short: dict, title: str, hook: str, script: str, storyboard: list, props: dict, index: int) -> tuple[str, str, str, list, dict]:
    case = select_teardown_case(index, short, props)
    case_voiceover = build_case_voiceover(case)
    case_storyboard = build_case_storyboard(case)
    props.update({
        "teardownCaseId": case["id"],
        "seriesOverride": CASE_SERIES_ROTATION[(index - 1) % len(CASE_SERIES_ROTATION)],
        "resumeName": case["resumeName"],
        "resumeTitle": case["resumeTitle"],
        "resumeMeta": case["resumeMeta"],
        "jobTitle": case["jobTitle"],
        "jobKeywords": case["jobKeywords"],
        "weakBullets": case["weakBullets"],
        "beforeBullet": case["beforeBullet"],
        "afterBullet": case["afterBullet"],
        "beforeScore": case["beforeScore"],
        "afterScore": case["afterScore"],
        "missing": case["jobKeywords"],
        "markedLabel": case["markedLabel"],
        "problemPunchline": case["problemPunchline"],
        "teardownIssues": case["teardownIssues"],
        "voiceover_text": case_voiceover,
    })
    return case["shortTitle"], case["hook"], case_voiceover, case_storyboard, props


def normalize_short(short: dict, fallback: dict, index: int) -> dict:
    if not isinstance(short, dict):
        short = {}

    title = short.get("title") or fallback.get("title") or f"Signal short {index}"
    hook = short.get("hook") or short.get("content") or fallback.get("hook") or "Your resume may be invisible."
    script = short.get("script") or short.get("content") or fallback.get("script") or hook
    entertainment_text = f"{title} {hook} {script}".lower()
    used_fallback = False
    proof_markers = ["hubspot", "cac", "linkedin ads", "pipeline", "lifecycle", "34/100", "92/100", "keyword", "score"]
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
    props.setdefault("beforeScore", 38 + index)
    props.setdefault("afterScore", 86 + index)
    props.setdefault("missing", ["HubSpot", "CAC", "LinkedIn Ads", "lifecycle marketing"])
    props.setdefault("cta", "Check your free Signal score.")
    props.setdefault("voiceover_text", str(script)[:650])
    title, hook, script, storyboard, props = apply_teardown_case(short, str(title), str(hook), str(script), storyboard, props, index)

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
    packet["topic"] = str(packet.get("topic") or seed.get("topic") or fallback["topic"])
    packet["series"] = str(packet.get("series") or seed.get("series") or fallback["series"])
    packet["thesis"] = str(packet.get("thesis") or seed.get("thesis") or fallback["thesis"])

    source_notes = packet.get("sourceNotes")
    if not isinstance(source_notes, list) or not source_notes:
        source_notes = seed.get("source_notes") or fallback["sourceNotes"]
    packet["sourceNotes"] = source_notes

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
        for marker in ["hubspot", "cac", "linkedin ads", "score", "bullet", "before/after", "weak bullets"]
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
        "requirements": [
            "One 8-10 minute YouTube episode script with storyboard and chapters.",
            "Three short-form cutdowns, each 22-45 seconds.",
            "Make the content funny and entertaining for frustrated job hunters: relatable job-search pain, quick jokes, visual gags, and recruiter-reacts roasts.",
            "Humor must punch at vague resume language and the broken job-search process, not at unemployed people.",
            "Claims must avoid auto-reject, guarantees, fake outcomes, and unsupported competitor claims.",
            "CTA must send users to the free Signal score.",
            "Use recruiter-reacts / resume-teardown energy, not generic SaaS demo energy.",
            "For every short include title, series, hook, script, storyboard, and Remotion props.",
            "Return strict JSON matching keys: publishDate, topic, series, thesis, sourceNotes, youtube, shorts, monetization, viewerCustomerReview.",
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
    lines = [
        f"# {youtube['title']}",
        "",
        f"Publish date: {packet['publishDate']}",
        f"Series: {packet.get('series', 'Daily')}",
        f"Thesis: {packet.get('thesis', '')}",
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

    short_lines = [f"# Shorts Plan: {packet['topic']}", ""]
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
        keywords = ["HubSpot", "CAC", "LinkedIn Ads", "lifecycle marketing"]

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
        keywords = ["HubSpot", "CAC", "LinkedIn Ads"]
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
        return SHORT_STYLE_ROTATION[0]
    if "signal mascot" in lower_text or "signal found" in lower_text or "rescue" in lower_text:
        return SHORT_STYLE_ROTATION[4]
    if "myth" in lower_text or "wizard" in lower_text or "mind" in lower_text:
        return SHORT_STYLE_ROTATION[2]
    if "bullet" in lower_text or "mustache" in lower_text or "responsible for" in lower_text:
        return SHORT_STYLE_ROTATION[1]
    if "search" in lower_text or "job description" in lower_text or "same resume" in lower_text:
        return SHORT_STYLE_ROTATION[3]
    if "signal" in lower_text or "rescue" in lower_text:
        return SHORT_STYLE_ROTATION[4]
    return SHORT_STYLE_ROTATION[(index - 1) % len(SHORT_STYLE_ROTATION)]


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
        props.setdefault("missing", ["role language", "tools", "metrics"])
        props.setdefault("cta", "Check your free Signal score.")
        props.setdefault("voiceover_text", short.get("script", "")[:650])
        if not props.get("teardownCaseId"):
            _, _, _, _, props = apply_teardown_case(short, str(short.get("title", "")), str(short.get("hook", "")), str(short.get("script", "")), short.get("storyboard", []), props, idx)
        props["cta"] = normalize_signal_cta(props.get("cta"))
        job_keywords = [
            str(item)
            for item in (props.get("jobKeywords") or props.get("missing", ["HubSpot", "CAC", "LinkedIn Ads", "lifecycle marketing"]))
        ][:5]
        if sum(1 for item in job_keywords if item.lower() in {"role language", "tools", "proof", "metrics"}) >= 2:
            job_keywords = ["HubSpot", "CAC", "LinkedIn Ads", "lifecycle marketing"]
        style = style_for_short(idx, short)
        crime_scene_props = {
            "hook": short.get("hook", "This resume looks fine.")[:72],
            "subhook": "The problem is vague proof, not fake experience.",
            "creativeFormat": style["creativeFormat"],
            "visualStyle": style["visualStyle"],
            "pace": style["pace"],
            "seriesLabel": style["seriesLabel"],
            "signalLines": style["signalLines"],
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
            "beforeScore": int(props.get("beforeScore", 38)),
            "afterScore": int(props.get("afterScore", 88)),
            "markedLabel": props.get("markedLabel", "Too vague"),
            "problemPunchline": props.get("problemPunchline", "Recruiters search for proof, not vibes."),
            "teardownIssues": props.get("teardownIssues", ["No role language", "No tools", "No measurable proof"]),
            "cta": normalize_signal_cta(props.get("cta")),
            "musicSrc": "audio/signal-quiet-orbit.wav",
            "musicVolume": 0.16,
            "avatarLabel": "Recruiter review",
        }
        lower_text = f"{short.get('title', '')} {short.get('hook', '')}".lower()
        if "linkedin breath" in lower_text or "airport" in lower_text:
            crime_scene_props["hook"] = "Your AI resume has LinkedIn breath."
            crime_scene_props["subhook"] = "Polished. Beige. Missing the role language."
            crime_scene_props["creativeFormat"] = "aiResumeRoast"
            crime_scene_props["visualStyle"] = "comic"
            crime_scene_props["pace"] = "fast"
        elif "mustache" in lower_text:
            crime_scene_props["hook"] = "This bullet is wearing a fake mustache."
            crime_scene_props["subhook"] = "It looks busy, but says almost nothing."
            crime_scene_props["creativeFormat"] = "oneBulletFix"
            crime_scene_props["visualStyle"] = "highlighter"
            crime_scene_props["pace"] = "fast"
        elif "wizard" in lower_text or "mind" in lower_text:
            crime_scene_props["hook"] = "The ATS is not a wizard."
            crime_scene_props["subhook"] = "It searches what you actually wrote."
            crime_scene_props["creativeFormat"] = "atsMythLab"
            crime_scene_props["visualStyle"] = "terminal"
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
            "Composition: `ResumeCrimeScene`",
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
            "composition": "ResumeCrimeScene",
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
    base = f"{title} {hook} Check your free Signal score before you apply.".strip()
    tags = "#jobsearch #resumehelp #careertok #resumetips #airesume"
    caption = f"{base} {tags}"
    if len(caption) > 280:
        caption = f"{title}. Check your free Signal score before you apply. {tags}"
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
    parser.add_argument("--check-elevenlabs", action="store_true", help="Validate ElevenLabs key, voice access, and optional TTS probe.")
    parser.add_argument("--probe-elevenlabs-tts", action="store_true", help="With --check-elevenlabs, run a tiny timestamped TTS request.")
    args = parser.parse_args()

    ensure_dirs()
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
