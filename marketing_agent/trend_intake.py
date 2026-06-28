import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_DIR = ROOT / "marketing" / "content_research"
LATEST_PATH = RESEARCH_DIR / "trend_intake_latest.json"


DEFAULT_CANDIDATES = [
    {
        "topic": "AI resumes all sound the same, so recruiters search for proof",
        "series": "Recruiter Search Test",
        "hook": "Your AI resume sounds professional. That might be the problem.",
        "whyNow": "AI-written resumes are common enough that job seekers need a trust-building way to show real proof, not generic polish.",
        "contentAngle": "Recruiter-style teardown of an AI-polished resume that misses HubSpot, CAC, LinkedIn Ads, and lifecycle marketing.",
        "sourceNotes": [
            {
                "title": "YouTube Analytics engagement and retention",
                "url": "https://support.google.com/youtube/answer/9314355",
                "note": "Monitor retention and engagement after posting, not just views.",
            },
            {
                "title": "TikTok Creative Center",
                "url": "https://ads.tiktok.com/business/creativecenter/",
                "note": "Use trend discovery to validate current hooks and sounds before publishing.",
            },
        ],
        "score": 91,
        "status": "candidate",
    },
    {
        "topic": "The ATS auto-reject myth versus recruiter search reality",
        "series": "ATS Myth Lab",
        "hook": "The ATS probably did not throw your resume away. Here is the real problem.",
        "whyNow": "Fear-based ATS content gets clicks, but a clearer explanation builds more trust and conversion.",
        "contentAngle": "Show the difference between parsing/indexing/search and unsupported auto-reject claims.",
        "sourceNotes": [
            {
                "title": "Signal viral content workflow",
                "url": "marketing/content_research/viral_success_workflow.md",
                "note": "Keep claims safe and avoid adversarial ATS promises.",
            }
        ],
        "score": 84,
        "status": "candidate",
    },
]


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def validate_candidate(candidate: dict) -> dict:
    source_notes = candidate.get("sourceNotes")
    if not isinstance(source_notes, list):
        source_notes = []
    has_source_url = any(isinstance(item, dict) and item.get("url") for item in source_notes)
    score = int(candidate.get("score", 50) or 50)
    if has_source_url:
        score += 6
    if "resume" in str(candidate.get("topic", "")).lower():
        score += 4
    score = max(0, min(100, score))
    return {
        "topic": str(candidate.get("topic", "")).strip(),
        "series": str(candidate.get("series", "Daily Research Packet")).strip(),
        "hook": str(candidate.get("hook", candidate.get("topic", ""))).strip(),
        "whyNow": str(candidate.get("whyNow", "")).strip(),
        "contentAngle": str(candidate.get("contentAngle", "")).strip(),
        "sourceNotes": source_notes,
        "score": score,
        "status": "candidate" if has_source_url else "needs_source",
    }


def build_intake(candidates: list[dict]) -> dict:
    normalized = [validate_candidate(item) for item in candidates if isinstance(item, dict)]
    normalized = [item for item in normalized if item["topic"]]
    normalized.sort(key=lambda item: item["score"], reverse=True)
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "method": "source-backed intake file; replace or append with live exports from YouTube, TikTok Creative Center, Google Trends, Reddit, or LinkedIn.",
        "topCandidate": normalized[0] if normalized else None,
        "candidates": normalized,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a source-backed trend intake file for the daily content agent.")
    parser.add_argument("--input", type=Path, help="Optional JSON list/object of trend candidates.")
    parser.add_argument("--write", action="store_true", help="Write marketing/content_research/trend_intake_latest.json.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    if args.input:
        data = read_json(args.input, [])
        candidates = data.get("candidates", []) if isinstance(data, dict) else data
    else:
        candidates = DEFAULT_CANDIDATES

    intake = build_intake(candidates if isinstance(candidates, list) else [])
    if args.write:
        RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
        LATEST_PATH.write_text(json.dumps(intake, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(intake, indent=2))
    else:
        top = intake.get("topCandidate") or {}
        print(f"Top trend candidate: {top.get('topic', 'none')}")
        if args.write:
            print(f"Trend intake written: {LATEST_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
