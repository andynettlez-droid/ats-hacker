import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET = ROOT / "marketing" / "daily_content"


POSITIVE_MARKERS = {
    "hook": [
        "34/100",
        "92/100",
        "invisible",
        "linkedin breath",
        "fake mustache",
        "not a wizard",
        "too vague",
        "resume crime scene",
        "recruiter",
        "job description",
    ],
    "proof": [
        "HubSpot",
        "CAC",
        "LinkedIn Ads",
        "Salesforce",
        "React",
        "TypeScript",
        "Jira",
        "Epic",
        "Gainsight",
        "pipeline",
        "lifecycle",
        "score",
        "before",
        "after",
        "rewrite",
        "keyword",
        "proof",
    ],
    "format": [
        "resume",
        "job description",
        "bullet",
        "highlight",
        "score",
        "Signal",
        "free score",
        "redline",
        "before/after",
        "scorecard",
    ],
    "humor": [
        "beige",
        "fake mustache",
        "rude",
        "side-eye",
        "airport",
        "hoodie",
        "roast",
        "mind-reading",
        "yap",
    ],
}

VISIBLE_ARTIFACT_MARKERS = [
    "resume",
    "job description",
    "bullet",
    "score",
    "keyword",
    "highlight",
    "redline",
    "before",
    "after",
]

SERIES_FORMATS = [
    "resume crime scene",
    "ats myth lab",
    "job description translation",
    "one bullet fix",
    "recruiter search test",
    "ai resume roast",
    "resume builder cost trap",
    "signal mascot rescue",
]


DISQUALIFIERS = [
    "guaranteed interviews",
    "guarantee interviews",
    "beat every ats",
    "automatically rejects",
    "fool the ats",
    "trick the ats",
    "add fake experience",
    "make up experience",
    "invent a job",
    "invented experience",
]


GENERIC_OR_WEAK = [
    "can your ai resume do the talking",
    "wanna discover",
    "genius at vague buzzwords",
    "magical wand",
    "training their resumes like puppies",
    "glossy ai resumes",
    "misfits and clashing design",
    "ai-polished resume",
    "target job description",
    "results-driven team player",
    "helped with marketing campaigns",
    "worked with cross-functional teams",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def text_blob(packet: dict) -> str:
    parts = [
        packet.get("topic", ""),
        packet.get("series", ""),
        packet.get("thesis", ""),
    ]
    youtube = packet.get("youtube", {})
    if isinstance(youtube, dict):
        parts.extend([youtube.get("title", ""), youtube.get("description", ""), youtube.get("cta", "")])
        for section in youtube.get("scriptSections", []) or []:
            if isinstance(section, dict):
                parts.extend([section.get("label", ""), section.get("script", ""), section.get("visual", "")])
    for short in packet.get("shorts", []) or []:
        if isinstance(short, dict):
            props = short.get("props") if isinstance(short.get("props"), dict) else {}
            parts.extend([short.get("series", ""), short.get("title", ""), short.get("hook", ""), short.get("script", "")])
            parts.extend([
                props.get("hook1", ""),
                props.get("hook2", ""),
                props.get("subline", ""),
                props.get("cta", ""),
                props.get("resumeTitle", ""),
                props.get("jobTitle", ""),
                props.get("beforeBullet", ""),
                props.get("afterBullet", ""),
                props.get("beforeScore", ""),
                props.get("afterScore", ""),
            ])
            parts.extend(props.get("resumeMeta", []) or [])
            parts.extend(props.get("weakBullets", []) or [])
            parts.extend(props.get("jobKeywords", []) or [])
            parts.extend(props.get("missing", []) or [])
            parts.extend(short.get("storyboard", []) or [])
    return "\n".join(str(part) for part in parts)


def count_markers(blob: str, markers: list[str]) -> int:
    low = blob.lower()
    return sum(1 for marker in markers if marker.lower() in low)


def has_numbered_payoff(blob: str) -> bool:
    return bool(re.search(r"\b\d{2,3}\s*/\s*100\b", blob)) or bool(re.search(r"\b\d{2,3}\s*(?:→|->|to)\s*\d{2,3}\b", blob))


def has_score_props(short: dict) -> bool:
    props = short.get("props") if isinstance(short.get("props"), dict) else {}
    before = props.get("beforeScore")
    after = props.get("afterScore")
    return isinstance(before, (int, float)) and isinstance(after, (int, float)) and after > before


def has_visible_artifact(blob: str) -> bool:
    low = blob.lower()
    return sum(1 for marker in VISIBLE_ARTIFACT_MARKERS if marker in low) >= 3


def has_repeatable_series(blob: str) -> bool:
    low = blob.lower()
    return any(series in low for series in SERIES_FORMATS)


def score_short(short: dict) -> dict:
    props = short.get("props") if isinstance(short.get("props"), dict) else {}
    blob = "\n".join(
        str(part)
        for part in [
            short.get("series", ""),
            short.get("title", ""),
            short.get("hook", ""),
            short.get("script", ""),
            props.get("hook1", ""),
            props.get("hook2", ""),
            props.get("subline", ""),
            props.get("cta", ""),
            props.get("resumeTitle", ""),
            props.get("jobTitle", ""),
            props.get("beforeBullet", ""),
            props.get("afterBullet", ""),
            props.get("beforeScore", ""),
            props.get("afterScore", ""),
            *(props.get("resumeMeta", []) or []),
            *(props.get("weakBullets", []) or []),
            *(props.get("jobKeywords", []) or []),
            *(props.get("missing", []) or []),
            *(short.get("storyboard", []) or []),
        ]
    )
    low = blob.lower()
    score = 0
    notes: list[str] = []
    blockers: list[str] = []

    if len(str(short.get("hook", "")).split()) <= 11:
        score += 10
    else:
        notes.append("Shorten the first on-screen hook to 11 words or fewer.")

    if count_markers(blob, POSITIVE_MARKERS["hook"]) >= 1:
        score += 12
    else:
        notes.append("Hook needs a sharper recruiter/reacts angle.")

    if count_markers(blob, POSITIVE_MARKERS["humor"]) >= 1:
        score += 12
    else:
        notes.append("Add one job-search-safe joke or visual gag.")

    if count_markers(blob, POSITIVE_MARKERS["proof"]) >= 3:
        score += 18
    else:
        notes.append("Add concrete role proof: tools, metric, job keyword, or before/after score.")

    if count_markers(blob, POSITIVE_MARKERS["format"]) >= 4:
        score += 18
    else:
        notes.append("Keep resume, job description, bullet, score, and Signal visible.")

    if has_visible_artifact(blob):
        score += 5
    else:
        notes.append("Every short needs a concrete on-screen artifact: resume line, JD excerpt, scorecard, redline, or before/after diff.")

    if has_numbered_payoff(blob) or has_score_props(short):
        score += 10
    else:
        notes.append("Include a clear score jump or numeric proof payoff.")

    if has_repeatable_series(blob):
        score += 5
    else:
        notes.append("Use a repeatable series shell such as Resume Crime Scene, ATS Myth Lab, or One Bullet Fix.")

    if "free signal score" in low or "free score" in low:
        score += 10
    else:
        notes.append("CTA should lead with the free Signal score.")

    if any(term in low for term in DISQUALIFIERS):
        blockers.append("Contains unsafe claim language.")
    if any(term in low for term in GENERIC_OR_WEAK):
        score -= 12
        notes.append("Replace generic or overly goofy phrasing with a sharper teardown line.")

    return {
        "title": short.get("title", "Untitled"),
        "score": max(0, min(100, score)),
        "passed": score >= 80 and not blockers,
        "notes": notes,
        "blockers": blockers,
    }


def score_packet(packet: dict) -> dict:
    blob = text_blob(packet)
    low = blob.lower()
    score = 0
    notes: list[str] = []
    blockers: list[str] = []

    if count_markers(blob, POSITIVE_MARKERS["hook"]) >= 3:
        score += 16
    else:
        notes.append("Needs more native hooks: resume crime scene, invisible, score jump, recruiter angle.")

    if count_markers(blob, POSITIVE_MARKERS["proof"]) >= 6:
        score += 20
    else:
        notes.append("Needs more concrete proof markers: tools, keywords, metrics, before/after rewrite.")

    if count_markers(blob, POSITIVE_MARKERS["format"]) >= 5:
        score += 18
    else:
        notes.append("Needs stronger visual plan around resume/JD/bullet/score, not presenter-only content.")

    if has_visible_artifact(blob):
        score += 4
    else:
        notes.append("Needs visible artifacts throughout: resume line, JD excerpt, scorecard, redline, or before/after diff.")

    if count_markers(blob, POSITIVE_MARKERS["humor"]) >= 3:
        score += 14
    else:
        notes.append("Needs more safe humor that punches at vague resume language or job-search friction.")

    if has_numbered_payoff(blob) or any(has_score_props(short) for short in packet.get("shorts", []) or [] if isinstance(short, dict)):
        score += 10
    else:
        notes.append("Needs a numeric before/after payoff.")

    if "free signal score" in low or "free score" in low:
        score += 10
    else:
        notes.append("CTA should lead with a free score, not a hard product pitch.")

    if len(packet.get("shorts", []) or []) >= 3:
        score += 6
    else:
        notes.append("Needs at least three short-form cutdowns.")

    if has_repeatable_series(blob):
        score += 4
    else:
        notes.append("Needs a repeatable creator series wrapper, not a one-off tip.")

    if packet.get("sourceNotes"):
        score += 6
    else:
        notes.append("Needs source notes for the research claim trail.")

    if any(term in low for term in DISQUALIFIERS):
        blockers.append("Contains unsafe or overpromising claim language.")
    if any(term in low for term in GENERIC_OR_WEAK):
        score -= 10
        notes.append("Contains weak/generic creator phrasing that should be replaced before production.")

    short_scores = [score_short(short) for short in packet.get("shorts", []) or [] if isinstance(short, dict)]
    if short_scores and not all(item["passed"] for item in short_scores[:3]):
        notes.append("One or more shorts failed the professional creator gate.")

    passed = score >= 85 and not blockers and bool(short_scores) and all(item["passed"] for item in short_scores[:3])
    return {
        "overallScore": max(0, min(100, score)),
        "passed": passed,
        "verdict": "post_grade_script_packet" if passed else "needs_revision_before_posting",
        "notes": notes,
        "blockers": blockers,
        "shorts": short_scores,
    }


def latest_packet_path() -> Path:
    packet_files = sorted(DEFAULT_PACKET.glob("*/packet.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not packet_files:
        raise FileNotFoundError("No daily packet found under marketing/daily_content.")
    return packet_files[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Score a Signal content packet against professional creator-readiness criteria.")
    parser.add_argument("--packet", type=Path, default=None, help="Path to packet.json. Defaults to the newest daily packet.")
    parser.add_argument("--write", action="store_true", help="Write creative_quality_report.json and .md next to the packet.")
    args = parser.parse_args()

    packet_path = args.packet or latest_packet_path()
    packet = read_json(packet_path)
    report = score_packet(packet)
    print(json.dumps(report, indent=2))

    if args.write:
        out_json = packet_path.parent / "creative_quality_report.json"
        out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
        lines = [
            "# Creative Quality Gate",
            "",
            f"Verdict: {report['verdict']}",
            f"Score: {report['overallScore']}/100",
            f"Passed: {report['passed']}",
            "",
            "## Notes",
            "",
        ]
        lines.extend(f"- {note}" for note in report["notes"] or ["No revision notes."])
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {blocker}" for blocker in report["blockers"] or ["None"])
        lines.extend(["", "## Shorts", ""])
        for short in report["shorts"]:
            lines.extend([
                f"### {short['title']}",
                "",
                f"- Score: {short['score']}/100",
                f"- Passed: {short['passed']}",
            ])
            lines.extend(f"- Note: {note}" for note in short["notes"])
            lines.extend(f"- Blocker: {blocker}" for blocker in short["blockers"])
            lines.append("")
        (packet_path.parent / "creative_quality_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
