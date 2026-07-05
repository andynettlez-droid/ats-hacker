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
        "i would circle",
        "i searched",
        "i search",
        "here is my ctrl",
        "i am reading",
        "i'm reading",
        "job post already told you",
        "too vague",
        "live resume review",
        "recruiter",
        "job description",
        "open-book",
        "failed",
        "ctrl+f",
        "answer key",
    ],
    "proof": [
        "SQL",
        "Tableau",
        "cohort analysis",
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
        "lower on the page",
        "lower down",
        "source evidence",
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
        "i would circle",
        "i searched",
        "i am reading",
        "i'm reading",
        "i would write",
        "i would rewrite",
        "makes me guess",
        "okay, this is",
        "bad news",
        "see the gap",
        "not giving it",
        "cannot see",
        "ctrl+f",
        "the job post already told you",
        "the job post gave",
        "qualified people look weaker",
        "do not fake anything",
        "name the actual work",
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
    "live resume review",
    "resume crime scene",
    "ats myth lab",
    "job description review",
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
    "npc",
    "resume oatmeal",
    "beige wall",
    "bestie",
    "business casual shrug",
    "fake mustache",
    "linkedin breath",
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
    "hubspot",
    "cac",
    "demand gen",
    "linkedin ads",
]

ROBOTIC_OR_REPEATED = [
    "target:",
    "jd asks for",
    "real, but buried",
    "same person, clearer proof",
    "same person",
    "better signal",
    "same experience, clearer proof",
    "score receipt",
    "rubric gives",
    "so the rubric",
    "here is the score receipt",
    "now i see the tool",
]


NARRATIVE_BEAT_GROUPS = {
    "conflict": [
        "rejected",
        "nothing",
        "vanished",
        "expensive",
        "ignored",
        "failed",
        "why this resume",
        "why this bullet",
        "circle",
        "missed",
        "zero proof",
        "skipped",
    ],
    "target_evidence": [
        "job is asking",
        "job asks",
        "role needs",
        "job post",
        "job description",
        "i search",
        "here is my ctrl",
        "ctrl f",
        "ctrl+f",
        "search clues",
        "recruiter search",
        "answer key",
    ],
    "source_line": [
        "resume says",
        "bullet says",
        "line says",
        "resume line",
        "then i read",
        "this is the line",
        "read this line",
        "this is the line i would circle",
        "now here is the resume line",
        "resume replies",
        "resume answered",
        "your resume answered",
        "look at the resume",
        "their bullet",
        "this resume answers",
        "this bullet says",
        "this bullet shows up",
    ],
    "consequence": [
        "recruiters do not guess",
        "cannot search",
        "cannot see",
        "made me guess",
        "makes me guess",
        "buried",
        "hid",
        "hidden",
        "invisible",
        "generic",
        "weak",
        "nothing useful",
        "guessing",
        "gap",
        "missed it",
        "zero proof",
        "detective work",
        "no tool",
        "no number",
        "no result",
    ],
    "source_evidence": [
        "lower on the page",
        "lower on the resume",
        "lower down",
        "found the proof",
        "proof is lower",
        "source evidence",
        "same proof",
        "same evidence",
        "wrong place",
    ],
    "fix": [
        "rewrite",
        "i would write",
        "i would rewrite",
        "name the actual work",
        "better bullet",
        "fix is",
        "fix:",
        "instead",
        "specific",
        "receipt",
        "proof first",
    ],
    "payoff": [
        "score",
        "match score",
        "jumps",
        "moves from",
        "starts at",
        "lands at",
        "reaches",
        "to 92",
        "to 90",
        "to 88",
        "free signal score",
        "moves to",
        "not giving it an",
    ],
}


HUMAN_REVIEW_MARKERS = [
    "i am reading",
    "i'm reading",
    "i would circle",
    "i'd circle",
    "i would write",
    "i'd write",
    "i would rewrite",
    "i search",
    "here is my ctrl",
    "if i am screening",
    "if i'm screening",
        "here is the job post",
        "look at the job post",
        "now here is the resume line",
        "line says",
    "read this line",
    "then i read",
    "this is the line",
        "cannot see",
        "makes me guess",
        "see the gap",
        "not giving it",
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
            evidence = props.get("evidenceLedger") if isinstance(props.get("evidenceLedger"), dict) else {}
            parts.extend([
                evidence.get("sourceLocation", ""),
                evidence.get("proofLine", ""),
            ])
            for item in evidence.get("visibleFacts", []) or []:
                if isinstance(item, dict):
                    parts.extend([item.get("fact", ""), item.get("source", "")])
            parts.extend(props.get("resumeMeta", []) or [])
            parts.extend(props.get("weakBullets", []) or [])
            parts.extend(props.get("jobKeywords", []) or [])
            parts.extend(props.get("missing", []) or [])
            for row in props.get("scoreBasis", []) or []:
                if isinstance(row, dict):
                    parts.extend([row.get("label", ""), row.get("before", ""), row.get("after", "")])
            score_rubric = props.get("score_rubric") or props.get("scoreRubric") or {}
            if isinstance(score_rubric, dict):
                parts.extend([
                    score_rubric.get("label", ""),
                    score_rubric.get("beforeTotal", ""),
                    score_rubric.get("afterTotal", ""),
                    score_rubric.get("beforeExplanation", ""),
                    score_rubric.get("afterExplanation", ""),
                ])
                for row in score_rubric.get("rows", []) or []:
                    if isinstance(row, dict):
                        parts.extend([
                            row.get("criterion", ""),
                            row.get("label", ""),
                            row.get("max", ""),
                            row.get("before", ""),
                            row.get("after", ""),
                            row.get("beforeReason", ""),
                            row.get("afterReason", ""),
                        ])
            for beat in props.get("humanReadBeats", []) or []:
                if isinstance(beat, dict):
                    parts.extend([beat.get("beat", ""), beat.get("text", "")])
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


def has_score_basis(short: dict) -> bool:
    props = short.get("props") if isinstance(short.get("props"), dict) else {}
    basis = props.get("scoreBasis")
    if not isinstance(basis, list) or len(basis) < 3:
        return False
    valid = 0
    for row in basis:
        if isinstance(row, dict) and row.get("label") and row.get("before") and row.get("after"):
            valid += 1
    return valid >= 3


def score_rubric_rows(short: dict) -> list[dict]:
    props = short.get("props") if isinstance(short.get("props"), dict) else {}
    rubric = props.get("score_rubric") or props.get("scoreRubric")
    if not isinstance(rubric, dict):
        return []
    rows = rubric.get("rows")
    return rows if isinstance(rows, list) else []


def has_score_rubric(short: dict) -> bool:
    props = short.get("props") if isinstance(short.get("props"), dict) else {}
    before_score = props.get("beforeScore")
    after_score = props.get("afterScore")
    rows = score_rubric_rows(short)
    if not isinstance(before_score, (int, float)) or not isinstance(after_score, (int, float)):
        return False
    if len(rows) < 6:
        return False
    before_total = 0
    after_total = 0
    valid = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        if not row.get("criterion") and not row.get("label"):
            continue
        if not isinstance(row.get("max"), (int, float)):
            continue
        if not isinstance(row.get("before"), (int, float)) or not isinstance(row.get("after"), (int, float)):
            continue
        if not row.get("beforeReason") or not row.get("afterReason"):
            continue
        before_total += int(row["before"])
        after_total += int(row["after"])
        valid += 1
    return valid >= 6 and before_total == int(before_score) and after_total == int(after_score) and after_total > before_total


def evidence_ledger(short: dict) -> dict:
    props = short.get("props") if isinstance(short.get("props"), dict) else {}
    ledger = props.get("evidenceLedger")
    return ledger if isinstance(ledger, dict) else {}


def has_evidence_ledger(short: dict) -> bool:
    ledger = evidence_ledger(short)
    facts = ledger.get("visibleFacts")
    return bool(ledger.get("sourceLocation")) and bool(ledger.get("proofLine")) and isinstance(facts, list) and len(facts) >= 3


def evidence_text(short: dict) -> str:
    ledger = evidence_ledger(short)
    facts = ledger.get("visibleFacts") if isinstance(ledger.get("visibleFacts"), list) else []
    return " ".join([
        str(ledger.get("sourceLocation", "")),
        str(ledger.get("proofLine", "")),
        " ".join(
            " ".join(str(item.get(key, "")) for key in ("fact", "source"))
            for item in facts
            if isinstance(item, dict)
        ),
    ]).lower()


def after_rewrite_supported_by_evidence(short: dict) -> bool:
    props = short.get("props") if isinstance(short.get("props"), dict) else {}
    after = str(props.get("afterBullet", "")).lower()
    evidence = evidence_text(short)
    if not after or not evidence:
        return False
    numeric_claims = re.findall(r"(?:\$?\d+(?:\.\d+)?\s?(?:m|k|%|percent)?|\d+\s?-\s?person)", after)
    if any(claim.strip() and claim.strip() not in evidence for claim in numeric_claims):
        return False
    key_terms = [
        term.lower()
        for term in (props.get("jobKeywords") or [])
        if isinstance(term, str) and len(term) > 2
    ]
    supported_terms = sum(1 for term in key_terms if term in after and term in evidence)
    return supported_terms >= 1 and bool(numeric_claims)


def evidence_bridge_explained(blob: str) -> bool:
    low = blob.lower()
    markers = [
        "lower on the page",
        "lower on the resume",
        "lower down",
        "found the proof",
        "proof is lower",
        "same proof",
        "same evidence",
        "wrong place",
    ]
    return sum(1 for marker in markers if marker in low) >= 1


def explains_starting_score(blob: str) -> bool:
    low = blob.lower()
    score_reason_markers = [
        "starts at",
        "starts here",
        "that is why this starts",
        "why the score starts",
        "starting score",
        "low score",
        "because",
        "weak terms",
        "missing",
        "no metric",
        "no outcome",
        "no result",
        "zero proof",
        "no tool",
        "no number",
        "signal fit score",
        "rubric",
    ]
    return sum(1 for marker in score_reason_markers if marker in low) >= 3


def has_visible_artifact(blob: str) -> bool:
    low = blob.lower()
    return sum(1 for marker in VISIBLE_ARTIFACT_MARKERS if marker in low) >= 3


def has_repeatable_series(blob: str) -> bool:
    low = blob.lower()
    return any(series in low for series in SERIES_FORMATS)


def opening_signature(short: dict) -> str:
    props = short.get("props") if isinstance(short.get("props"), dict) else {}
    text = str(short.get("script") or props.get("voiceover_text") or short.get("hook") or "")
    words = re.findall(r"[a-z][a-z']+", text.lower())
    filler = {"this", "that", "your", "resume", "bullet", "the", "job", "description", "signal"}
    meaningful = [word for word in words if word not in filler]
    return " ".join(meaningful[:5])


def repeated_openings(shorts: list[dict]) -> list[str]:
    signatures: dict[str, int] = {}
    for short in shorts:
        sig = opening_signature(short)
        if sig:
            signatures[sig] = signatures.get(sig, 0) + 1
    return [sig for sig, count in signatures.items() if count > 1]


def unique_short_formats(shorts: list[dict]) -> set[str]:
    formats: set[str] = set()
    for short in shorts:
        props = short.get("props") if isinstance(short.get("props"), dict) else {}
        for key in ("playbookId", "formatArchetype", "creativeFormat", "visualStyle"):
            value = props.get(key)
            if value:
                formats.add(f"{key}:{value}")
    return formats


def narrative_beats(blob: str) -> set[str]:
    low = blob.lower()
    found: set[str] = set()
    for beat, markers in NARRATIVE_BEAT_GROUPS.items():
        if any(marker in low for marker in markers):
            found.add(beat)
    return found


def human_review_marker_count(blob: str) -> int:
    low = blob.lower()
    return sum(1 for marker in HUMAN_REVIEW_MARKERS if marker in low)


def script_word_count(short: dict) -> int:
    props = short.get("props") if isinstance(short.get("props"), dict) else {}
    text = str(props.get("voiceover_text") or short.get("script") or "")
    return len(re.findall(r"[a-zA-Z0-9']+", text))


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
            props.get("voiceover_text", ""),
            props.get("playbookId", ""),
            props.get("formatArchetype", ""),
            props.get("beforeScore", ""),
            props.get("afterScore", ""),
            *[
                f"{row.get('label', '')} {row.get('before', '')} {row.get('after', '')}"
                for row in (props.get("scoreBasis", []) or [])
                if isinstance(row, dict)
            ],
            *[
                " ".join(str(row.get(key, "")) for key in ("criterion", "label", "max", "before", "after", "beforeReason", "afterReason"))
                for row in score_rubric_rows(short)
                if isinstance(row, dict)
            ],
            *[
                f"{beat.get('beat', '')} {beat.get('text', '')}"
                for beat in (props.get("humanReadBeats", []) or [])
                if isinstance(beat, dict)
            ],
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
        notes.append("Add a natural reviewer reaction or human read, not meme-template slang.")

    if human_review_marker_count(blob) >= 2:
        score += 10
    else:
        blockers.append("Script needs first-person human review language, e.g. 'I would circle...' and 'I would write...'.")

    if count_markers(blob, POSITIVE_MARKERS["proof"]) >= 3:
        score += 18
    else:
        notes.append("Add concrete role proof: tools, metric, job keyword, or before/after score.")

    if count_markers(blob, POSITIVE_MARKERS["format"]) >= 4:
        score += 18
    else:
        notes.append("Keep resume, job description, bullet, score, and Signal visible.")

    beats = narrative_beats(blob)
    if len(beats) >= 6:
        score += 14
    elif len(beats) >= 5:
        score += 8
        blockers.append(f"Script has most narrative beats but still needs stronger {', '.join(sorted(set(NARRATIVE_BEAT_GROUPS) - beats))}.")
    else:
        blockers.append(f"Script lacks a complete viral story spine; found beats: {', '.join(sorted(beats)) or 'none'}.")

    words = script_word_count(short)
    if 42 <= words <= 96:
        score += 7
    else:
        blockers.append(f"Voiceover should be a tight 42-96 words for 18-32s Shorts; current estimate is {words}.")

    if has_visible_artifact(blob):
        score += 5
    else:
        notes.append("Every short needs a concrete on-screen artifact: resume line, JD excerpt, scorecard, redline, or before/after diff.")

    if has_numbered_payoff(blob) or has_score_props(short):
        score += 10
    else:
        notes.append("Include a clear score jump or numeric proof payoff.")

    if has_score_basis(short) and has_score_rubric(short) and explains_starting_score(blob):
        score += 10
    else:
        blockers.append("Score reveal needs scoreBasis, a six-row score_rubric with matching totals, and script language explaining why the start score is low.")

    if has_evidence_ledger(short) and after_rewrite_supported_by_evidence(short) and evidence_bridge_explained(blob):
        score += 12
    else:
        blockers.append("Rewrite needs visible source evidence: evidenceLedger, supported numeric claims, and script language explaining where the proof came from.")

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
    if any(term in low for term in ROBOTIC_OR_REPEATED):
        score -= 10
        notes.append("Replace robotic template phrasing with a more natural creator read.")
    if "rubric gives" in low or "so the rubric" in low:
        blockers.append("Do not narrate the rubric as if software is talking; explain the human-visible evidence instead.")

    return {
        "title": short.get("title", "Untitled"),
        "score": max(0, min(100, score)),
        "passed": score >= 88 and not blockers,
        "notes": notes,
        "blockers": blockers,
    }


def score_packet(packet: dict) -> dict:
    blob = text_blob(packet)
    low = blob.lower()
    score = 0
    notes: list[str] = []
    blockers: list[str] = []
    shorts = [short for short in packet.get("shorts", []) or [] if isinstance(short, dict)]

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

    beat_sets = [narrative_beats("\n".join(str(part) for part in [
        short.get("title", ""),
        short.get("hook", ""),
        short.get("script", ""),
        "\n".join(short.get("storyboard", []) or []),
        short.get("props", {}).get("voiceover_text", "") if isinstance(short.get("props"), dict) else "",
        short.get("props", {}).get("problemPunchline", "") if isinstance(short.get("props"), dict) else "",
        short.get("props", {}).get("teardownPunchline", "") if isinstance(short.get("props"), dict) else "",
        short.get("props", {}).get("fixPunchline", "") if isinstance(short.get("props"), dict) else "",
        "\n".join(
            f"{beat.get('beat', '')} {beat.get('text', '')}"
            for beat in (short.get("props", {}).get("humanReadBeats", []) if isinstance(short.get("props"), dict) else [])
            if isinstance(beat, dict)
        ),
    ])) for short in [s for s in packet.get("shorts", []) or [] if isinstance(s, dict)]]
    if beat_sets and all(len(beats) >= 6 for beats in beat_sets[:3]):
        score += 10
    else:
        blockers.append("Each short needs a complete conflict -> evidence -> consequence -> fix -> payoff spine.")

    if has_visible_artifact(blob):
        score += 4
    else:
        notes.append("Needs visible artifacts throughout: resume line, JD excerpt, scorecard, redline, or before/after diff.")

    if count_markers(blob, POSITIVE_MARKERS["humor"]) >= 3:
        score += 14
    else:
        notes.append("Needs more natural human-review reactions, not presenter/product-demo narration.")

    if shorts and all(human_review_marker_count("\n".join(str(part) for part in [
        short.get("title", ""),
        short.get("hook", ""),
        short.get("script", ""),
        "\n".join(short.get("storyboard", []) or []),
        short.get("props", {}).get("voiceover_text", "") if isinstance(short.get("props"), dict) else "",
        "\n".join(
            f"{beat.get('beat', '')} {beat.get('text', '')}"
            for beat in (short.get("props", {}).get("humanReadBeats", []) if isinstance(short.get("props"), dict) else [])
            if isinstance(beat, dict)
        ),
    ])) >= 2 for short in shorts[:3]):
        score += 10
    else:
        blockers.append("Each short needs first-person human resume-review language before it can pass creative QA.")

    if has_numbered_payoff(blob) or any(has_score_props(short) for short in packet.get("shorts", []) or [] if isinstance(short, dict)):
        score += 10
    else:
        notes.append("Needs a numeric before/after payoff.")

    if shorts and all(has_score_basis(short) and has_score_rubric(short) and explains_starting_score("\n".join(str(part) for part in [
        short.get("title", ""),
        short.get("hook", ""),
        short.get("script", ""),
        "\n".join(short.get("storyboard", []) or []),
        short.get("props", {}).get("voiceover_text", "") if isinstance(short.get("props"), dict) else "",
        short.get("props", {}).get("problemPunchline", "") if isinstance(short.get("props"), dict) else "",
        short.get("props", {}).get("teardownPunchline", "") if isinstance(short.get("props"), dict) else "",
        short.get("props", {}).get("fixPunchline", "") if isinstance(short.get("props"), dict) else "",
    ])) for short in shorts[:3]):
        score += 10
    else:
        blockers.append("Each short needs scoreBasis, a six-row score_rubric with matching totals, and an explained low-score reason before the score jump.")

    if shorts and all(has_evidence_ledger(short) and after_rewrite_supported_by_evidence(short) and evidence_bridge_explained("\n".join(str(part) for part in [
        short.get("title", ""),
        short.get("hook", ""),
        short.get("script", ""),
        "\n".join(short.get("storyboard", []) or []),
        short.get("props", {}).get("voiceover_text", "") if isinstance(short.get("props"), dict) else "",
        "\n".join(
            f"{beat.get('beat', '')} {beat.get('text', '')}"
            for beat in (short.get("props", {}).get("humanReadBeats", []) if isinstance(short.get("props"), dict) else [])
            if isinstance(beat, dict)
        ),
    ])) for short in shorts[:3]):
        score += 10
    else:
        blockers.append("Each short needs a visible evidence ledger and must explain where the stronger rewrite came from.")

    if "free signal score" in low or "free score" in low:
        score += 10
    else:
        notes.append("CTA should lead with a free score, not a hard product pitch.")

    if len(packet.get("shorts", []) or []) >= 3:
        score += 6
    else:
        notes.append("Needs at least three short-form cutdowns.")

    if len(unique_short_formats(shorts[:3])) >= 9:
        score += 8
    else:
        blockers.append("Daily shorts need distinct playbooks, archetypes, and visual styles.")

    repeated = repeated_openings(shorts[:3])
    if repeated:
        score -= 18
        notes.append(f"Repeated script openings detected: {', '.join(repeated)}.")

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
    if any(term in low for term in ROBOTIC_OR_REPEATED):
        score -= 12
        notes.append("Contains repeated robotic script phrasing from an older template.")
    if "rubric gives" in low or "so the rubric" in low:
        blockers.append("Rubric-first narration is banned; explain source evidence like a human reviewer.")

    short_scores = [score_short(short) for short in shorts]
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
