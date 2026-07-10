#!/usr/bin/env python3
"""Deterministic creative-council gate for Signal short-form scripts.

The gate evaluates exactly five options against one resume brief and the saved
human-reviewer examples. It writes ``creative_council_review.json`` and
``creative_council_review.md`` in the run directory. A script outside the
55-70 word target may pass only with a specific ``Word Count Exception:`` (or
``Length Exception:``) note and must still stay inside the 42-96 hard bounds.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APPROVED_EXAMPLES = (
    ROOT / "marketing" / "script_templates" / "approved_human_reviewer_examples.md"
)

EXPECTED_OPTION_NUMBERS = (1, 2, 3, 4, 5)
TARGET_MIN_WORDS = 55
TARGET_MAX_WORDS = 70
HARD_MIN_WORDS = 42
HARD_MAX_WORDS = 96

WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['\u2019][A-Za-z0-9]+)?(?:\+|%)?")
OPTION_HEADING_RE = re.compile(r"(?m)^##[ \t]+Option[ \t]+(\d+)\b([^\r\n]*)$")
EXCEPTION_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:word[- ]count|length)\s+exception\s*:\s*(.+?)\s*$"
)
NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9])(?P<currency>[$\u00a3\u20ac])?\s*"
    r"(?P<number>\d+(?:,\d{3})*(?:\.\d+)?)"
    r"(?P<suffix>[kKmM])?(?P<plus>\+)?(?P<percent>%)?"
)

BANNED_PATTERNS: tuple[tuple[str, str], ...] = (
    ("same person, better signal", r"\bsame person[.!,:;]?\s+better signal\b"),
    ("this resume is invisible", r"\bthis resume is invisible\b"),
    ("this experience is invisible", r"\bthis experience is invisible\b"),
    ("generic keyword diagnosis", r"\bthis resume lacks role[- ]specific keywords\b"),
    ("score-receipt narration", r"\bhere is the score receipt\b"),
    ("rubric narration", r"\bthe rubric gives it\b"),
    ("ATS rejection claim", r"\bats\b.{0,28}\b(?:auto[- ]?)?reject(?:ed|s|ion)?\b"),
    ("automatic rejection claim", r"\bautomatically reject(?:ed|s|ion)?\b"),
    ("beat the bots", r"\bbeat the bots\b"),
    ("ATS optimized", r"\b(?:get|make|made)\b.{0,16}\bats[- ]optimized\b"),
    ("guaranteed interviews", r"\bguaranteed interviews?\b"),
    ("dream-job promise", r"\bland your dream job\b"),
    ("competitive-market opener", r"\bin today['\u2019]?s competitive market\b"),
    ("unlock career potential", r"\bunlock (?:your )?career potential\b"),
    ("semantic relevance", r"\bsemantic relevance\b"),
    ("optimized alignment", r"\boptimized alignment\b"),
    ("ATS-friendly artifact", r"\bats[- ]friendly artifact\b"),
    ("AI-powered solution", r"\bai[- ]powered solution\b"),
    ("cutting-edge", r"\bcutting[- ]edge\b"),
    ("product-forward Signal claim", r"\bsignal (?:helps|can optimize|optimizes)\b"),
)

PROOF_CUES = (
    "lower down",
    "lower on the page",
    "lower on this resume",
    "evidence is lower",
    "evidence is buried lower",
    "found the proof later",
    "good evidence is buried",
    "proof is there",
    "proof is in the next bullet",
    "proof is lower",
    "proof lower",
    "already has the proof",
    "has proof lower",
    "two lines down",
    "elsewhere on the resume",
    "elsewhere on the page",
    "right evidence is in the wrong place",
    "good stuff is already",
    "page already shows",
)

EDIT_CUES = (
    "changed it to",
    "change it to",
    "delete this",
    "delete the",
    "make it",
    "replace it",
    "replace this",
    "rewrite it as",
    "write this",
    "write",
    "lead with",
    "swap it",
    "change it",
    "fix it",
    "pulls it up",
    "use this instead",
)

REACTION_MARKERS = (
    "too vague",
    "too blurry",
    "too generic",
    "means nothing",
    "basically fog",
    "it is fog",
    "it's fog",
    "not wrong",
    "not awful",
    "sounds professional",
    "sounds responsible",
    "sounds safe",
    "tells a recruiter almost nothing",
    "tells a recruiter nothing",
    "tells me almost nothing",
    "tells me nothing",
    "says almost nothing",
    "says nothing",
    "not specific",
    "hides the work",
    "hides what",
    "this is the problem",
    "that is the problem",
    "that's the problem",
    "harder to find",
    "hard to trust",
    "could mean anything",
    "does not say",
    "doesn't say",
    "does no work",
    "doing no work",
    "written like",
)

DIRECT_CTA_STARTS = (
    "need your",
    "need yours",
    "upload it",
    "upload yours",
    "run the free",
    "use the link",
)

EVIDENCE_EXCLUDED_KEYS = {
    "candidate",
    "candidatename",
    "cta",
    "email",
    "format",
    "linkedin",
    "location",
    "rewrite",
    "scorereceipt",
    "searchterms",
    "targetjoblanguage",
    "targetrole",
    "weakreason",
    "wordcountexception",
    "wordcountexceptions",
}

CONTENT_STOP_WORDS = {
    "a",
    "already",
    "also",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "below",
    "by",
    "candidate",
    "down",
    "elsewhere",
    "for",
    "from",
    "good",
    "has",
    "have",
    "her",
    "here",
    "his",
    "i",
    "in",
    "is",
    "it",
    "job",
    "line",
    "lower",
    "me",
    "more",
    "now",
    "of",
    "on",
    "page",
    "proof",
    "real",
    "resume",
    "right",
    "she",
    "so",
    "that",
    "the",
    "their",
    "there",
    "they",
    "this",
    "to",
    "up",
    "was",
    "we",
    "were",
    "what",
    "with",
    "you",
    "your",
}

GENERIC_ACTION_PREFIXES = (
    "achiev",
    "assist",
    "build",
    "catch",
    "coordinat",
    "creat",
    "cut",
    "decreas",
    "deliver",
    "develop",
    "document",
    "driv",
    "execut",
    "fix",
    "grow",
    "handl",
    "help",
    "improv",
    "increas",
    "lead",
    "maintain",
    "manag",
    "monitor",
    "process",
    "protect",
    "provid",
    "reduc",
    "resolv",
    "sav",
    "schedul",
    "support",
    "triag",
    "updat",
    "us",
    "work",
)

CHECK_LABELS = {
    "human_spoken_flow": "Human spoken flow",
    "evidence_fidelity": "Evidence fidelity",
    "banned_phrases": "Banned phrases",
    "word_count": "Word count",
    "believable_mistake": "One believable mistake",
    "cta": "CTA",
}


@dataclass(frozen=True)
class ParsedOption:
    number: int
    title: str
    script: str
    raw: str
    exception_reason: str | None


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical(text: str) -> str:
    return " ".join(token.lower().replace("\u2019", "'") for token in WORD_RE.findall(text))


def _contains_phrase(text: str, phrase: str) -> bool:
    haystack = f" {_canonical(text)} "
    needle = _canonical(phrase)
    return bool(needle) and f" {needle} " in haystack


def _phrase_position(canonical_text: str, phrase: str, start: int = 0) -> int:
    needle = _canonical(phrase)
    if not needle:
        return -1
    padded = f" {canonical_text} "
    index = padded.find(f" {needle} ", start)
    return index


def _first_phrase_position(canonical_text: str, phrases: Sequence[str], start: int = 0) -> int:
    positions = [_phrase_position(canonical_text, phrase, start) for phrase in phrases]
    found = [position for position in positions if position >= 0]
    return min(found) if found else -1


def _phrase_count(text: str, phrase: str) -> int:
    haystack = _canonical(text).split()
    needle = _canonical(phrase).split()
    if not needle or len(needle) > len(haystack):
        return 0
    return sum(
        haystack[index : index + len(needle)] == needle
        for index in range(len(haystack) - len(needle) + 1)
    )


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def _plain_spoken_text(markdown: str) -> str:
    text = markdown.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    text = re.sub(r"(?m)^\s*```[^\n]*$", "", text)
    text = EXCEPTION_RE.sub("", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    text = re.sub(r"(?m)^\s*[-*+]\s+", "", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def _extract_exception(text: str) -> str | None:
    match = EXCEPTION_RE.search(text)
    return match.group(1).strip() if match else None


def _extract_voice_block(text: str, fallback: bool = True) -> str:
    voice_heading = re.search(
        r"(?im)^(?P<marks>#{1,6})\s+(?:Voiceover(?:\s+Script)?|Spoken\s+Script|"
        r"Selected\s+Script|Production\s+Script|Script)\s*$",
        text,
    )
    if voice_heading:
        tail = text[voice_heading.end() :]
        next_heading = re.search(r"(?m)^#{1,6}\s+", tail)
        block = tail[: next_heading.start()] if next_heading else tail
        return _plain_spoken_text(block)

    if not fallback:
        return ""

    block = text
    block = re.sub(r"(?m)^#\s+[^\n]+\n?", "", block, count=1)
    block = re.sub(r"(?im)^\s*(?:Status|Decision)\s*:\s*[^\n]+$", "", block)
    stop = re.search(
        r"(?im)^(?:#{2,6}\s*)?(?:Read[- ]Aloud Review|Why This|Review Notes|"
        r"Rejection Notes|Selection Notes|Council Notes|Council Review|Why Selected|"
        r"On-Screen Resume Evidence|CTA)\b.*$",
        block,
    )
    if stop:
        block = block[: stop.start()]
    heading = re.search(r"(?m)^#{2,6}\s+", block)
    if heading:
        block = block[: heading.start()]
    return _plain_spoken_text(block)


def parse_script_options(markdown: str) -> list[ParsedOption]:
    matches = list(OPTION_HEADING_RE.finditer(markdown))
    options: list[ParsedOption] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        raw = markdown[match.end() : end]
        title = match.group(2).strip().lstrip("-:").strip() or f"Option {match.group(1)}"
        options.append(
            ParsedOption(
                number=int(match.group(1)),
                title=title,
                script=_extract_voice_block(raw),
                raw=raw,
                exception_reason=_extract_exception(raw),
            )
        )
    return options


def parse_approved_examples(markdown: str) -> dict[str, Any]:
    heading_re = re.compile(r"(?m)^##\s+Example\s+\d+\b[^\r\n]*$")
    headings = list(heading_re.finditer(markdown))
    scripts: list[str] = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
        block = markdown[heading.end() : end]
        why = re.search(r"(?im)^###\s+Why This Passes\b", block)
        if why:
            block = block[: why.start()]
        script = _plain_spoken_text(block).strip()
        if len(script) >= 2 and script[0] in {'"', "\u201c"} and script[-1] in {'"', "\u201d"}:
            script = script[1:-1].strip()
        if script:
            scripts.append(script)

    ctas: list[str] = []
    for script in scripts:
        canonical_script = _canonical(script)
        positions = [
            _phrase_position(canonical_script, marker)
            for marker in DIRECT_CTA_STARTS
        ]
        positions = [position for position in positions if position >= 0]
        if positions:
            ctas.append(canonical_script[min(positions) :].strip())

    return {
        "example_count": len(scripts),
        "approved_ctas": _unique(ctas),
        "scripts": scripts,
    }


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _evidence_text(brief: dict[str, Any]) -> str:
    values: list[str] = []

    def walk(value: Any, parent_key: str = "") -> None:
        if _normalize_key(parent_key) in EVIDENCE_EXCLUDED_KEYS:
            return
        if isinstance(value, str):
            if value.strip():
                values.append(value.strip())
            return
        if isinstance(value, dict):
            for key in sorted(value):
                walk(value[key], str(key))
            return
        if isinstance(value, list):
            for item in value:
                walk(item, parent_key)

    walk(brief)
    return "\n".join(values)


def _stem(word: str) -> str:
    value = word.lower().replace("\u2019", "'").strip("'")
    aliases = {
        "daily": "day",
        "weekly": "week",
        "monthly": "month",
        "administrator": "admin",
        "administration": "admin",
    }
    if value in aliases:
        return aliases[value]
    if value.endswith("ies") and len(value) > 4:
        return value[:-3] + "y"
    if value.endswith("ing") and len(value) > 5:
        value = value[:-3]
    elif value.endswith("ed") and len(value) > 4:
        value = value[:-2]
    elif value.endswith("es") and len(value) > 4:
        value = value[:-2]
    elif value.endswith("s") and len(value) > 3:
        value = value[:-1]
    if len(value) > 3 and value[-1:] == value[-2:-1]:
        value = value[:-1]
    return value


def _content_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in WORD_RE.findall(text):
        raw_lower = raw.lower().replace("\u2019", "'").strip("+%")
        if not raw_lower.isalpha():
            continue
        stemmed = _stem(raw_lower)
        if raw_lower in CONTENT_STOP_WORDS or stemmed in CONTENT_STOP_WORDS:
            continue
        if any(stemmed.startswith(prefix) for prefix in GENERIC_ACTION_PREFIXES):
            continue
        tokens.add(stemmed)
    return tokens


def _number_key(match: re.Match[str]) -> str | None:
    raw = match.group("number").replace(",", "")
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None
    suffix = (match.group("suffix") or "").lower()
    if suffix == "k":
        value *= 1000
    elif suffix == "m":
        value *= 1_000_000
    normalized = format(value.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    if match.group("percent"):
        normalized += "%"
    return normalized


def _number_keys(text: str) -> set[str]:
    return {key for match in NUMBER_RE.finditer(text) if (key := _number_key(match))}


def _check(passed: bool, reasons: Sequence[str] = (), **details: Any) -> dict[str, Any]:
    return {"passed": passed, "reasons": list(reasons), **details}


def _valid_exception_reason(reason: str | None) -> bool:
    if not reason:
        return False
    words = WORD_RE.findall(reason)
    placeholder = _canonical(reason) in {"approved", "exception approved", "n a", "because"}
    return len(reason.strip()) >= 18 and len(words) >= 4 and not placeholder


def _word_count_check(script: str, exception_reason: str | None) -> dict[str, Any]:
    word_count = count_words(script)
    reasons: list[str] = []
    exception_used = False
    if word_count < HARD_MIN_WORDS or word_count > HARD_MAX_WORDS:
        reasons.append(
            f"script is {word_count} words; even exceptions must stay within "
            f"{HARD_MIN_WORDS}-{HARD_MAX_WORDS} words"
        )
    elif word_count < TARGET_MIN_WORDS or word_count > TARGET_MAX_WORDS:
        if _valid_exception_reason(exception_reason):
            exception_used = True
        elif exception_reason:
            reasons.append(
                f"script is {word_count} words and its exception reason is not specific enough"
            )
        else:
            reasons.append(
                f"script is {word_count} words; expected {TARGET_MIN_WORDS}-{TARGET_MAX_WORDS} "
                "or an explicit Word Count Exception with a specific reason"
            )
    return _check(
        not reasons,
        reasons,
        word_count=word_count,
        target_min=TARGET_MIN_WORDS,
        target_max=TARGET_MAX_WORDS,
        hard_min=HARD_MIN_WORDS,
        hard_max=HARD_MAX_WORDS,
        exception_used=exception_used,
        exception_reason=exception_reason if exception_used else None,
    )


def _brief_exception(brief: dict[str, Any], option_number: int | None, selected: bool) -> str | None:
    mapping = brief.get("wordCountExceptions") or brief.get("word_count_exceptions")
    if isinstance(mapping, dict):
        keys: list[str] = []
        if option_number is not None:
            keys.extend((str(option_number), f"option{option_number}", f"option_{option_number}"))
        if selected:
            keys.append("selected")
        for key in keys:
            value = mapping.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    singular = brief.get("wordCountException") or brief.get("word_count_exception")
    if isinstance(singular, str) and singular.strip() and selected:
        return singular.strip()
    if isinstance(singular, dict):
        reason = singular.get("reason")
        options = singular.get("options", [])
        applies = selected and "selected" in options
        applies = applies or option_number in options or str(option_number) in options
        if applies and isinstance(reason, str) and reason.strip():
            return reason.strip()
    return None


def _cta_match(
    script: str,
    brief: dict[str, Any],
    approved_ctas: Sequence[str],
) -> tuple[int, str, list[str]]:
    canonical_script = _canonical(script)
    reasons: list[str] = []
    brief_cta = str(brief.get("cta", "") or "").strip()
    candidates = [_canonical(brief_cta)] if brief_cta else []
    candidates.extend(_canonical(cta) for cta in approved_ctas if _canonical(cta))
    candidates = _unique(candidates)

    matched = ""
    matched_position = -1
    for candidate in sorted(candidates, key=lambda item: (-len(item), item)):
        position = _phrase_position(canonical_script, candidate)
        if position >= 0 and canonical_script.endswith(candidate):
            matched = candidate
            matched_position = position
            break

    if not matched:
        direct_positions = [
            _phrase_position(canonical_script, marker) for marker in DIRECT_CTA_STARTS
        ]
        direct_positions = [position for position in direct_positions if position >= 0]
        if direct_positions:
            matched_position = max(direct_positions)
            matched = canonical_script[matched_position:].strip()

    if brief_cta:
        expected = _canonical(brief_cta)
        expected_position = _phrase_position(canonical_script, expected)
        if expected_position < 0:
            reasons.append("script does not use the CTA from resume_brief.json")
        elif not canonical_script.endswith(expected):
            reasons.append("CTA from resume_brief.json is not the final spoken beat")
        else:
            matched = expected
            matched_position = expected_position

    if not matched:
        reasons.append("script has no direct service CTA")
    elif not any(matched.startswith(_canonical(marker)) for marker in DIRECT_CTA_STARTS):
        reasons.append("CTA is not a direct request to fix, upload, score, or use the link")
    elif not any(term in matched for term in ("fix", "upload", "score", "link", "apply")):
        reasons.append("CTA has no concrete next action")

    return matched_position, matched, reasons


def _human_flow_check(
    script: str,
    brief: dict[str, Any],
    approved_ctas: Sequence[str],
) -> dict[str, Any]:
    reasons: list[str] = []
    canonical_script = _canonical(script)
    weak = str(brief.get("weakBullet", "") or "").strip()
    rewrite = str(brief.get("rewrite", "") or "").strip()
    candidate = str(brief.get("candidateName", "") or "").strip()
    target_role = str(brief.get("targetRole", "") or "").strip()

    weak_position = _phrase_position(canonical_script, weak) if weak else -1
    rewrite_position = _phrase_position(canonical_script, rewrite) if rewrite else -1
    proof_position = _first_phrase_position(canonical_script, PROOF_CUES)
    edit_position = _first_phrase_position(
        canonical_script,
        EDIT_CUES,
        max(0, proof_position),
    )
    cta_position, _, _ = _cta_match(script, brief, approved_ctas)

    candidate_token = candidate.split()[0] if candidate else ""
    candidate_position = (
        _first_phrase_position(
            canonical_script,
            (candidate_token, f"{candidate_token}'s"),
        )
        if candidate_token
        else -1
    )
    if candidate_position < 0:
        reasons.append("candidate name is missing")
    elif proof_position >= 0 and candidate_position > proof_position:
        reasons.append("candidate is introduced after the proof beat")

    role_tokens = {
        _stem(token)
        for token in WORD_RE.findall(target_role)
        if token.lower() not in {"a", "an", "the", "role", "position"}
    }
    role_prefix = canonical_script[: proof_position if proof_position >= 0 else len(canonical_script)]
    present_role_tokens = {
        token for token in role_tokens if _contains_phrase(role_prefix, token)
    }
    required_role_tokens = min(2, len(role_tokens))
    if required_role_tokens and len(present_role_tokens) < required_role_tokens:
        reasons.append("target role is not clear before the proof beat")

    search_terms = brief.get("searchTerms") or brief.get("targetJobLanguage") or []
    if not isinstance(search_terms, list):
        search_terms = []
    search_prefix = canonical_script[: proof_position if proof_position >= 0 else len(canonical_script)]
    present_terms = [
        str(term)
        for term in search_terms
        if str(term).strip() and _contains_phrase(search_prefix, str(term))
    ]
    required_terms = min(2, len([term for term in search_terms if str(term).strip()]))
    if required_terms == 0:
        reasons.append("resume_brief.json has no recruiter/search terms to test")
    elif len(present_terms) < required_terms:
        reasons.append(
            f"only {len(present_terms)} recruiter/search terms appear before proof; "
            f"expected at least {required_terms}"
        )

    if weak_position < 0:
        reasons.append("exact weak line is missing from the spoken flow")
    if proof_position < 0:
        reasons.append("script never points to proof already on the resume")
    if edit_position < 0:
        reasons.append("script has no natural delete/replace/write edit cue")
    if rewrite_position < 0:
        reasons.append("exact rewrite is missing from the spoken flow")
    if cta_position < 0:
        reasons.append("CTA beat is missing")

    ordered_beats = (
        ("weak line", weak_position, "proof", proof_position),
        ("proof", proof_position, "edit", edit_position),
        ("edit", edit_position, "rewrite", rewrite_position),
        ("rewrite", rewrite_position, "CTA", cta_position),
    )
    for before_name, before_position, after_name, after_position in ordered_beats:
        if before_position >= 0 and after_position >= 0 and before_position > after_position:
            reasons.append(f"{before_name} must come before {after_name}")

    reaction_segment = ""
    if weak_position >= 0 and proof_position > weak_position:
        weak_end = weak_position + len(_canonical(weak))
        reaction_segment = canonical_script[weak_end:proof_position].strip()
    if not reaction_segment or not any(marker in reaction_segment for marker in REACTION_MARKERS):
        reasons.append("weak line is not followed by a natural, line-specific human reaction")

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", _plain_spoken_text(script))
        if sentence.strip()
    ]
    long_sentences = [count_words(sentence) for sentence in sentences if count_words(sentence) > 32]
    if long_sentences:
        reasons.append(f"spoken sentence is too dense ({max(long_sentences)} words; maximum 32)")
    if re.search(
        r"(?i)(?:^|[.!?]\s+)(?:candidate|target role|weak line|rewrite|cta)\s*:",
        script,
    ):
        reasons.append("spoken copy uses production labels instead of natural speech")

    if cta_position >= 0:
        pre_cta = canonical_script[:cta_position]
        if re.search(r"\b(?:signal|our tool|our platform|ai powered)\b", pre_cta):
            reasons.append("product language appears before the CTA")

    return _check(
        not reasons,
        reasons,
        beats={
            "candidate": candidate_position,
            "weak_line": weak_position,
            "proof": proof_position,
            "edit": edit_position,
            "rewrite": rewrite_position,
            "cta": cta_position,
        },
        search_terms_found=present_terms,
    )


def _evidence_check(script: str, brief: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    weak = str(brief.get("weakBullet", "") or "").strip()
    rewrite = str(brief.get("rewrite", "") or "").strip()
    evidence = _evidence_text(brief)
    canonical_script = _canonical(script)

    if not weak:
        reasons.append("resume_brief.json is missing weakBullet")
    elif _phrase_count(script, weak) != 1:
        reasons.append("script must contain the exact weakBullet once")
    if not rewrite:
        reasons.append("resume_brief.json is missing rewrite")
    elif _phrase_count(script, rewrite) != 1:
        reasons.append("script must contain the exact rewrite once")

    evidence_numbers = _number_keys(evidence)
    unsupported_numbers = sorted(_number_keys(script) - evidence_numbers)
    if unsupported_numbers:
        reasons.append(
            "numeric claims are not present in source resume evidence: "
            + ", ".join(unsupported_numbers)
        )

    evidence_tokens = _content_tokens(evidence)
    unsupported_rewrite_tokens = sorted(_content_tokens(rewrite) - evidence_tokens)
    if unsupported_rewrite_tokens:
        reasons.append(
            "rewrite introduces unsupported terms: " + ", ".join(unsupported_rewrite_tokens)
        )

    proof_position = _first_phrase_position(canonical_script, PROOF_CUES)
    rewrite_position = _phrase_position(canonical_script, rewrite) if rewrite else -1
    proof_tokens: set[str] = set()
    supported_proof_tokens: set[str] = set()
    if proof_position >= 0 and rewrite_position > proof_position:
        proof_segment = canonical_script[proof_position:rewrite_position]
        edit_position = _first_phrase_position(proof_segment, EDIT_CUES)
        if edit_position >= 0:
            proof_segment = proof_segment[:edit_position]
        proof_tokens = _content_tokens(proof_segment)
        supported_proof_tokens = proof_tokens & evidence_tokens
        unsupported_proof_tokens = sorted(proof_tokens - evidence_tokens)
        if unsupported_proof_tokens:
            reasons.append(
                "proof beat introduces unsupported terms: " + ", ".join(unsupported_proof_tokens)
            )
        if len(supported_proof_tokens) < 2:
            reasons.append("proof beat must state at least two source-backed facts")
    else:
        reasons.append("cannot verify source proof before the rewrite")

    search_terms = brief.get("targetJobLanguage") or brief.get("searchTerms") or []
    if isinstance(search_terms, list):
        unsupported_named_terms = sorted(
            {
                str(term)
                for term in search_terms
                if str(term).strip()
                and _contains_phrase(rewrite, str(term))
                and not _contains_phrase(evidence, str(term))
            }
        )
        if unsupported_named_terms:
            reasons.append(
                "rewrite promotes job terms with no candidate evidence: "
                + ", ".join(unsupported_named_terms)
            )

    return _check(
        not reasons,
        reasons,
        evidence_sha256=_sha256(evidence),
        supported_proof_terms=sorted(supported_proof_tokens),
        unsupported_numbers=unsupported_numbers,
    )


def _banned_phrase_check(script: str) -> dict[str, Any]:
    hits = [label for label, pattern in BANNED_PATTERNS if re.search(pattern, script, flags=re.I)]
    reasons = ["contains banned language: " + ", ".join(hits)] if hits else []
    return _check(not reasons, reasons, hits=hits)


def _mistake_check(script: str, brief: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    weak = str(brief.get("weakBullet", "") or "").strip()
    rewrite = str(brief.get("rewrite", "") or "").strip()
    weak_count = _phrase_count(script, weak) if weak else 0
    rewrite_count = _phrase_count(script, rewrite) if rewrite else 0
    weak_word_count = count_words(weak)

    if weak_count != 1:
        reasons.append(f"expected one weak resume line; found {weak_count}")
    if rewrite_count != 1:
        reasons.append(f"expected one replacement line; found {rewrite_count}")
    if weak and not 4 <= weak_word_count <= 24:
        reasons.append(
            f"weak line is {weak_word_count} words; a believable professional mistake should be 4-24 words"
        )
    if weak and _canonical(weak) == _canonical(rewrite):
        reasons.append("weak line and rewrite are identical")
    if re.search(
        r"\b(?:did stuff|worked hard|made things|various random tasks|was bad at|did my job)\b",
        weak,
        flags=re.I,
    ):
        reasons.append("weak line is cartoonishly bad rather than a believable professional mistake")
    if weak and not re.search(
        r"\b(?:assisted|built|conducted|coordinated|created|developed|handled|helped|led|"
        r"maintained|managed|monitored|oversaw|participated|performed|prepared|processed|"
        r"provided|responsible|resolved|reviewed|supported|updated|worked)\b|"
        r"\b[A-Za-z]+(?:ed|ing)\b",
        weak,
        flags=re.I,
    ):
        reasons.append("weak line does not read like a plausible professional resume bullet")
    if weak and re.search(r"\b(?:i|me|my)\b", weak, flags=re.I):
        reasons.append("weak line uses first-person narration instead of resume-bullet phrasing")
    if re.search(
        r"\b(?:another line|second mistake|second bad line|two mistakes|three mistakes|also fix this)\b",
        script,
        flags=re.I,
    ):
        reasons.append("script introduces more than one resume mistake")

    return _check(
        not reasons,
        reasons,
        mistake_count=1 if weak_count == 1 else weak_count,
        weak_line_word_count=weak_word_count,
    )


def _cta_check(
    script: str,
    brief: dict[str, Any],
    approved_ctas: Sequence[str],
) -> dict[str, Any]:
    position, matched, reasons = _cta_match(script, brief, approved_ctas)
    rewrite = str(brief.get("rewrite", "") or "").strip()
    rewrite_position = _phrase_position(_canonical(script), rewrite) if rewrite else -1
    if position >= 0 and rewrite_position >= 0 and position < rewrite_position:
        reasons.append("CTA appears before the rewrite")
    return _check(not reasons, reasons, matched_cta=matched or None, position=position)


def evaluate_script(
    script: str,
    brief: dict[str, Any],
    approved_ctas: Sequence[str] = (),
    exception_reason: str | None = None,
) -> dict[str, Any]:
    """Evaluate one spoken option and return a JSON-serializable review."""

    checks = {
        "human_spoken_flow": _human_flow_check(script, brief, approved_ctas),
        "evidence_fidelity": _evidence_check(script, brief),
        "banned_phrases": _banned_phrase_check(script),
        "word_count": _word_count_check(script, exception_reason),
        "believable_mistake": _mistake_check(script, brief),
        "cta": _cta_check(script, brief, approved_ctas),
    }
    rejection_reasons = [
        f"{CHECK_LABELS[name]}: {reason}"
        for name, check in checks.items()
        for reason in check["reasons"]
    ]
    return {
        "passed": not rejection_reasons,
        "word_count": checks["word_count"]["word_count"],
        "script_sha256": _sha256(_canonical(script)),
        "checks": checks,
        "rejection_reasons": rejection_reasons,
    }


def _read_text(path: Path, input_errors: list[str]) -> str:
    if not path.exists():
        input_errors.append(f"missing required input: {path.name}")
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        input_errors.append(f"could not read {path.name}: {exc}")
        return ""


def _load_brief(text: str, input_errors: list[str]) -> dict[str, Any]:
    if not text:
        return {}
    try:
        brief = json.loads(text)
    except json.JSONDecodeError as exc:
        input_errors.append(f"resume_brief.json is invalid JSON: {exc.msg}")
        return {}
    if not isinstance(brief, dict):
        input_errors.append("resume_brief.json must contain a JSON object")
        return {}
    return brief


def _render_markdown(report: dict[str, Any]) -> str:
    selected_label = (
        "Option " + str(report["selected_option"])
        if report["selected_option"]
        else "None"
    )
    passing_label = (
        ", ".join("Option " + str(number) for number in report["passing_options"])
        or "None"
    )
    lines = [
        "# Creative Council Review",
        "",
        f"**Verdict:** {report['decision']}",
        f"**Selected option:** {selected_label}",
        f"**Passing options:** {passing_label}",
        "",
        "## Council Decision",
        "",
        report["selection_reason"],
        "",
        "## Rejection Reasons",
        "",
    ]
    if report["rejection_reasons"]:
        lines.extend(f"- {reason}" for reason in report["rejection_reasons"])
    else:
        lines.append("- None.")

    lines.extend(("", "## Option Reviews", ""))
    for option in report["options"]:
        lines.extend(
            (
                f"### Option {option['option']} - {'PASS' if option['passed'] else 'FAIL'}",
                "",
                f"Title: {option['title']}",
                f"Words: {option['word_count']} (target {TARGET_MIN_WORDS}-{TARGET_MAX_WORDS})",
            )
        )
        for name, check in option["checks"].items():
            label = CHECK_LABELS[name]
            lines.append(f"- {label}: {'PASS' if check['passed'] else 'FAIL'}")
        if option["rejection_reasons"]:
            lines.append("")
            lines.append("Rejection reasons:")
            lines.extend(f"- {reason}" for reason in option["rejection_reasons"])
        else:
            lines.append("")
            lines.append("Rejection reasons: None.")
        lines.append("")

    selected = report["selected_script"]
    matched_option_label = (
        selected["matches_option"]
        if selected["matches_option"] is not None
        else "None"
    )
    lines.extend(
        (
            "## Selected Script Consistency",
            "",
            f"- Matches option: {matched_option_label}",
            f"- Script review: {'PASS' if selected['review']['passed'] else 'FAIL'}",
            f"- Words: {selected['review']['word_count']}",
        )
    )
    if selected["review"]["rejection_reasons"]:
        lines.extend(f"- {reason}" for reason in selected["review"]["rejection_reasons"])

    examples = report["approved_examples"]
    lines.extend(
        (
            "",
            "## Approved Reference",
            "",
            f"- Source: {examples['path']}",
            f"- Parsed examples: {examples['example_count']}",
            f"- SHA-256: `{examples['sha256']}`",
            "",
        )
    )
    return "\n".join(lines)


def review_creative_council(
    work_dir: str | Path,
    approved_examples_path: str | Path | None = None,
    json_output: str | Path | None = None,
    markdown_output: str | Path | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Evaluate a run directory and optionally write both council reports."""

    folder = Path(work_dir)
    approved_path = Path(approved_examples_path) if approved_examples_path else DEFAULT_APPROVED_EXAMPLES
    input_errors: list[str] = []

    option_text = _read_text(folder / "script_options.md", input_errors)
    selected_text = _read_text(folder / "selected_script.md", input_errors)
    brief_text = _read_text(folder / "resume_brief.json", input_errors)
    approved_text = _read_text(approved_path, input_errors)

    brief = _load_brief(brief_text, input_errors)
    options = parse_script_options(option_text)
    selected_script = _extract_voice_block(selected_text)
    selected_exception = _extract_exception(selected_text)
    approved = parse_approved_examples(approved_text)
    approved_ctas = approved["approved_ctas"]

    option_numbers = [option.number for option in options]
    if option_numbers != list(EXPECTED_OPTION_NUMBERS):
        input_errors.append(
            "script_options.md must contain exactly five ordered headings: "
            "Option 1 through Option 5"
        )
    if approved["example_count"] == 0:
        input_errors.append("approved examples file contains no parseable `## Example N` scripts")
    if not selected_script:
        input_errors.append("selected_script.md has no spoken script")

    selected_canonical = _canonical(selected_script)
    matching_options = [
        option.number
        for option in options
        if selected_canonical and _canonical(option.script) == selected_canonical
    ]
    matched_option = matching_options[0] if len(matching_options) == 1 else None
    if len(matching_options) > 1:
        input_errors.append("selected_script.md matches more than one duplicate option")

    canonical_options = [_canonical(option.script) for option in options if option.script]
    if len(canonical_options) != len(set(canonical_options)):
        input_errors.append("the five options must contain distinct spoken scripts")

    option_reviews: list[dict[str, Any]] = []
    for option in options:
        exception_reason = option.exception_reason or _brief_exception(brief, option.number, False)
        if option.number == matched_option:
            exception_reason = (
                exception_reason
                or selected_exception
                or _brief_exception(brief, option.number, True)
            )
        review = evaluate_script(option.script, brief, approved_ctas, exception_reason)
        option_reviews.append(
            {
                "option": option.number,
                "title": option.title,
                **review,
            }
        )

    selected_review_exception = (
        selected_exception
        or (
            next(
                (option.exception_reason for option in options if option.number == matched_option),
                None,
            )
            if matched_option is not None
            else None
        )
        or _brief_exception(brief, matched_option, True)
    )
    selected_review = evaluate_script(
        selected_script,
        brief,
        approved_ctas,
        selected_review_exception,
    )

    passing_options = [review["option"] for review in option_reviews if review["passed"]]
    if matched_option in passing_options and selected_review["passed"]:
        selected_option = matched_option
        selection_reason = (
            f"Option {selected_option} passes every council check and matches selected_script.md."
        )
    elif passing_options:
        selected_option = min(passing_options)
        selection_reason = (
            f"Option {selected_option} is the first passing option, but selected_script.md must be "
            "updated to match it before the gate can pass."
        )
    else:
        selected_option = None
        selection_reason = "All five options failed. The council selected none."

    rejection_reasons = list(input_errors)
    if not passing_options:
        rejection_reasons.append("all five script options failed; no script was selected")
    elif matched_option is None:
        rejection_reasons.append("selected_script.md does not match exactly one script option")
    elif matched_option not in passing_options:
        rejection_reasons.append(f"selected_script.md matches failing Option {matched_option}")
    elif not selected_review["passed"]:
        rejection_reasons.append("selected_script.md failed its independent consistency review")
    rejection_reasons = _unique(rejection_reasons)

    passed = (
        not rejection_reasons
        and option_numbers == list(EXPECTED_OPTION_NUMBERS)
        and selected_option is not None
        and selected_option == matched_option
        and selected_review["passed"]
    )

    inputs = {
        "script_options.md": _sha256(option_text) if option_text else None,
        "selected_script.md": _sha256(selected_text) if selected_text else None,
        "resume_brief.json": _sha256(brief_text) if brief_text else None,
        "approved_examples": _sha256(approved_text) if approved_text else None,
    }
    report: dict[str, Any] = {
        "schema_version": 1,
        "gate": "creative_council",
        "passed": passed,
        "decision": "PASS" if passed else "FAIL",
        "selected_option": selected_option,
        "passing_options": passing_options,
        "selection_reason": selection_reason,
        "rejection_reasons": rejection_reasons,
        "blockers": rejection_reasons,
        "warnings": [],
        "input_errors": input_errors,
        "requirements": {
            "option_numbers": list(EXPECTED_OPTION_NUMBERS),
            "target_words": [TARGET_MIN_WORDS, TARGET_MAX_WORDS],
            "exception_hard_bounds": [HARD_MIN_WORDS, HARD_MAX_WORDS],
            "checks": list(CHECK_LABELS),
        },
        "inputs": inputs,
        "approved_examples": {
            "path": approved_path.name,
            "sha256": inputs["approved_examples"],
            "example_count": approved["example_count"],
            "approved_cta_count": len(approved_ctas),
        },
        "options": option_reviews,
        "selected_script": {
            "matches_option": matched_option,
            "review": selected_review,
        },
    }

    if write_outputs:
        json_path = Path(json_output) if json_output else folder / "creative_council_review.json"
        markdown_path = (
            Path(markdown_output)
            if markdown_output
            else folder / "creative_council_review.md"
        )
        json_path.write_bytes(
            (json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode(
                "utf-8"
            )
        )
        markdown_path.write_bytes(_render_markdown(report).encode("utf-8"))

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the deterministic Signal creative-council script gate."
    )
    parser.add_argument("--work-dir", required=True, help="Run directory containing the three script inputs.")
    parser.add_argument(
        "--approved-examples",
        default=str(DEFAULT_APPROVED_EXAMPLES),
        help="Approved human-reviewer examples Markdown file.",
    )
    parser.add_argument("--json-output", help="Optional JSON report path.")
    parser.add_argument("--markdown-output", help="Optional Markdown report path.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    work_dir = Path(args.work_dir)
    if not work_dir.is_dir():
        print(f"creative council: work directory does not exist: {work_dir}", file=sys.stderr)
        return 2
    report = review_creative_council(
        work_dir=work_dir,
        approved_examples_path=args.approved_examples,
        json_output=args.json_output,
        markdown_output=args.markdown_output,
    )
    selected = f"Option {report['selected_option']}" if report["selected_option"] else "none"
    print(f"creative council: {report['decision']} (selected: {selected})")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
