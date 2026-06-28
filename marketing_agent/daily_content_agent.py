import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from creative_quality_gate import score_packet

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
        "voiceId": os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
        "modelId": os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
    }


def has_elevenlabs_config() -> bool:
    return bool(load_elevenlabs_config()["apiKey"])


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def generate_elevenlabs_voiceover(text: str, dest_name: str) -> str | None:
    config = load_elevenlabs_config()
    if not config["apiKey"]:
        return None

    dest_path = REMOTION_AUDIO_DIR / dest_name
    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{config['voiceId']}",
        headers={
            "xi-api-key": config["apiKey"],
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={
            "text": text,
            "model_id": config["modelId"],
            "voice_settings": {
                "stability": 0.48,
                "similarity_boost": 0.82,
                "style": 0.28,
                "use_speaker_boost": True,
            },
        },
        timeout=90,
    )
    response.raise_for_status()
    dest_path.write_bytes(response.content)
    if dest_path.stat().st_size < 1024:
        raise RuntimeError(f"ElevenLabs voiceover is too small: {dest_path}")
    return f"audio/{dest_name}"


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

    if not has_elevenlabs_config():
        crime_scene_props["audioReadiness"]["reason"] = "ELEVENLABS_API_KEY is not configured"
        return crime_scene_props

    voice_name = f"daily-{short_slug}-voiceover.mp3"
    voice_ref = f"audio/{voice_name}"
    if force_audio or not public_asset_exists(voice_ref):
        voice_ref = generate_elevenlabs_voiceover(voiceover_text, voice_name) or voice_ref

    if public_asset_exists(voice_ref):
        crime_scene_props["voiceoverSrc"] = voice_ref
        crime_scene_props["voiceoverVolume"] = 0.94
        crime_scene_props["audioReadiness"] = {
            "studioVoiceover": True,
            "quietMusic": public_asset_exists("audio/signal-quiet-orbit.wav"),
            "reason": "ready",
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
            "title": "Your AI resume has LinkedIn breath",
            "hook": "Your AI resume sounds like it networks at airport lounges.",
            "script": (
                "Your AI resume sounds like it networks at airport lounges. Very polished. Very beige. "
                "But the job asks for HubSpot, CAC, and lifecycle marketing, and your resume says results-driven team player. "
                "Signal finds the missing role language before you apply."
            ),
            "storyboard": [
                "Open with giant text: 'LinkedIn breath detected.'",
                "Show an over-polished AI resume with a beige 'professional yap' stamp.",
                "Cut to job description terms highlighted in yellow.",
                "Signal mascot side-eyes the missing keyword chips.",
                "Reveal free Signal score and CTA.",
            ],
            "props": {
                "hook1": "LinkedIn breath.",
                "hook2": "Zero job signal.",
                "subline": "Polished does not mean matched to the role.",
                "beforeScore": 39,
                "afterScore": 88,
                "missing": keywords[:4],
                "cta": "Check your free Signal score.",
                "voiceover_text": (
                    "Your AI resume sounds like it networks at airport lounges. Very polished. Very beige. "
                    "But if the job asks for HubSpot, CAC, and lifecycle marketing, results-driven team player is not enough. "
                    "Signal finds the missing role language before you apply."
                ),
            },
        },
        {
            "series": "One Bullet Fix",
            "title": "Stop writing helped with campaigns",
            "hook": "This bullet is wearing a fake mustache.",
            "script": (
                "This bullet is wearing a fake mustache. 'Helped with campaigns' tells me almost nothing. "
                "If you used HubSpot, ran paid social, or moved pipeline, say that clearly. "
                "No fake experience. Just stop hiding the good part."
            ),
            "storyboard": [
                "Circle weak bullet and stamp 'suspiciously vague'.",
                "Show target job terms.",
                "Rewrite with only true tools/scope/outcomes.",
                "Show score movement.",
                "CTA to free score.",
            ],
            "props": {
                "hook1": "Fake mustache bullet.",
                "hook2": "Still too vague.",
                "subline": "Replace vague activity with role-specific proof.",
                "beforeScore": 34,
                "afterScore": 82,
                "missing": ["Demand Gen", "HubSpot", "CAC", "pipeline"],
                "cta": "Run your free Signal score.",
                "voiceover_text": (
                    "This bullet is wearing a fake mustache. Helped with campaigns tells me almost nothing. "
                    "If you used HubSpot, ran paid social, or moved pipeline, say that clearly. "
                    "No fake experience. Just stop hiding the good part."
                ),
            },
        },
        {
            "series": "ATS Myth Lab",
            "title": "The ATS is not a wizard",
            "hook": "The ATS did not read your mind. Rude, honestly.",
            "script": (
                "The ATS did not read your mind. Rude, honestly. But it usually stores and searches what you actually wrote. "
                "If the job says lifecycle marketing and your resume says helped the team, your best experience is hiding in a hoodie."
            ),
            "storyboard": [
                "Open with 'mind-reading not installed' error.",
                "Show database/search visual.",
                "Type recruiter search terms.",
                "Resume misses terms.",
                "Signal highlights gap.",
                "CTA to score.",
            ],
            "props": {
                "hook1": "Mind-reading?",
                "hook2": "Not installed.",
                "subline": "Different language can hide relevant experience.",
                "beforeScore": 46,
                "afterScore": 86,
                "missing": ["role title", "tools", "metrics", "responsibilities"],
                "cta": "Check your free match score.",
                "voiceover_text": (
                    "The ATS did not read your mind. Rude, honestly. But it usually stores and searches what you actually wrote. "
                    "If the job says lifecycle marketing and your resume says helped the team, your best experience is hiding in a hoodie."
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

    return {
        "series": short.get("series") or fallback.get("series") or "Daily Short",
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
        chapters = [
            f"{item.get('duration', '').split(' - ')[0] if isinstance(item, dict) else ''} {item.get('chapter', 'Section') if isinstance(item, dict) else 'Section'}".strip()
            for item in generated_script
        ]
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
    for idx, short in enumerate(incoming_shorts[:5], start=1):
        fallback_short = fallback_shorts[(idx - 1) % len(fallback_shorts)]
        normalized_shorts.append(normalize_short(short, fallback_short, idx))
    while len(normalized_shorts) < 3:
        idx = len(normalized_shorts) + 1
        normalized_shorts.append(normalize_short({}, fallback_shorts[(idx - 1) % len(fallback_shorts)], idx))
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
    keywords = [str(item) for item in props.get("missing", []) if str(item).strip()][:5]
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
        "weakBullets": [
            "Results-driven team player.",
            "Helped with marketing campaigns.",
            "Worked with cross-functional teams.",
        ],
        "beforeBullet": "Helped with marketing campaigns.",
        "afterBullet": "Cut CAC by 32% through LinkedIn Ads audience segmentation and HubSpot lead scoring.",
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
        if has_elevenlabs_config():
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
                if force_audio or not public_asset_exists(voice_ref):
                    generated_ref = generate_elevenlabs_voiceover(narration[:2800], voice_name)
                    voice_ref = generated_ref or voice_ref
                if public_asset_exists(voice_ref):
                    voiceover_segments.append({
                        "src": voice_ref,
                        "fromFrame": intro_frames + (idx - 1) * section_frames,
                        "volume": 0.94,
                    })
            if voiceover_segments:
                episode_props["voiceoverSegments"] = voiceover_segments
                episode_props["audioReadiness"] = {
                    "studioVoiceover": True,
                    "quietMusic": public_asset_exists("audio/signal-quiet-orbit.wav"),
                    "reason": f"{len(voiceover_segments)} episode sections ready",
                }
        else:
            episode_props["audioReadiness"]["reason"] = "ELEVENLABS_API_KEY is not configured"

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
        job_keywords = [str(item) for item in props.get("missing", ["HubSpot", "CAC", "LinkedIn Ads", "lifecycle marketing"])][:4]
        if sum(1 for item in job_keywords if item.lower() in {"role language", "tools", "proof", "metrics"}) >= 2:
            job_keywords = ["HubSpot", "CAC", "LinkedIn Ads", "lifecycle marketing"]
        crime_scene_props = {
            "hook": short.get("hook", "This resume looks fine.")[:72],
            "subhook": "The problem is vague proof, not fake experience.",
            "resumeTitle": "AI-Polished Resume",
            "jobTitle": "Target Job Description",
            "jobKeywords": job_keywords,
            "weakBullets": [
                "Results-driven team player.",
                "Helped with marketing campaigns.",
                "Worked with cross-functional teams.",
            ],
            "beforeBullet": "Helped with marketing campaigns.",
            "afterBullet": "Cut CAC by 32% through LinkedIn Ads audience segmentation and HubSpot lead scoring.",
            "beforeScore": int(props.get("beforeScore", 38)),
            "afterScore": int(props.get("afterScore", 88)),
            "cta": props.get("cta", "Check your free Signal score."),
            "musicSrc": "audio/signal-quiet-orbit.wav",
            "musicVolume": 0.16,
            "avatarLabel": "Recruiter review",
        }
        lower_text = f"{short.get('title', '')} {short.get('hook', '')}".lower()
        if "linkedin breath" in lower_text or "airport" in lower_text:
            crime_scene_props["hook"] = "Your AI resume has LinkedIn breath."
            crime_scene_props["subhook"] = "Polished. Beige. Missing the role language."
        elif "mustache" in lower_text:
            crime_scene_props["hook"] = "This bullet is wearing a fake mustache."
            crime_scene_props["subhook"] = "It looks busy, but says almost nothing."
        elif "wizard" in lower_text or "mind" in lower_text:
            crime_scene_props["hook"] = "The ATS is not a wizard."
            crime_scene_props["subhook"] = "It searches what you actually wrote."
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
    title = str(short.get("title", "Resume teardown")).rstrip(".")
    hook = str(short.get("hook", "")).rstrip(".")
    base = f"{title}. {hook}. Check your free Signal score before you apply."
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


def write_autopost_drafts(packet: dict, packet_dir: Path, written_shorts: list[dict]) -> None:
    shorts_by_title = {short.get("title"): short for short in packet.get("shorts", []) if isinstance(short, dict)}
    drafts = []
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
    args = parser.parse_args()

    ensure_dirs()
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
    write_autopost_drafts(packet, packet_dir, written_shorts)
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
