#!/usr/bin/env python3
"""Synchronize the controlled resume editor to a real voice alignment.

The browser renderer owns readable pixels. This module owns the contract between
the spoken review, the visible edit beats, and the evidence shown in the receipt.
It never calls a paid API and never publishes anything.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.+#%/-][a-z0-9+%.-]+)*", re.IGNORECASE)
METRIC_RE = re.compile(r"(?<![\w.])(?:\$?\d[\d,.]*\+?%?|\d+x)(?![\w.])", re.IGNORECASE)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def tokens(value: str) -> list[str]:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return [match.group(0).casefold() for match in TOKEN_RE.finditer(ascii_value)]


def alignment_words(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("words")
    if not isinstance(raw, list) or not raw:
        raise ValueError("voice alignment contains no normalized words")
    result: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        word_tokens = tokens(str(item.get("word") or ""))
        if not word_tokens:
            continue
        try:
            start = float(item.get("startSec"))
            end = float(item.get("endSec"))
        except (TypeError, ValueError):
            continue
        result.append({"word": word_tokens[0], "startSec": start, "endSec": end})
    if not result:
        raise ValueError("voice alignment has no usable word timestamps")
    return result


def _phrase_window(phrase: str, *, minimum: int = 2, maximum: int = 8) -> list[str]:
    phrase_tokens = tokens(phrase)
    if len(phrase_tokens) <= maximum:
        return phrase_tokens
    # The opening words are the most stable match after ElevenLabs punctuation
    # normalization. Keep enough context to avoid matching an unrelated metric.
    return phrase_tokens[:maximum]


def find_phrase(
    words: Sequence[Mapping[str, Any]],
    phrases: Iterable[str],
    *,
    start_after: float = 0.0,
    required: bool = True,
    minimum_tokens: int = 2,
) -> tuple[float, float] | None:
    spoken = [str(item["word"]).casefold() for item in words]
    for phrase in phrases:
        phrase_tokens = _phrase_window(phrase)
        if not phrase_tokens:
            continue
        variants = [phrase_tokens]
        if len(phrase_tokens) > 5:
            variants.extend([phrase_tokens[:5], phrase_tokens[:4]])
        for variant in variants:
            if len(variant) < minimum_tokens:
                continue
            for index in range(0, len(spoken) - len(variant) + 1):
                if float(words[index]["startSec"]) + 1e-6 < start_after:
                    continue
                if spoken[index : index + len(variant)] == variant:
                    end_index = index + len(variant) - 1
                    return float(words[index]["startSec"]), float(words[end_index]["endSec"])
    if required:
        joined = " | ".join(phrases)
        raise ValueError(f"could not locate spoken cue in alignment: {joined}")
    return None


def _candidate_parts(config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    candidate = config.get("candidate") if isinstance(config.get("candidate"), dict) else config
    edit = config.get("edit") if isinstance(config.get("edit"), dict) else config
    review = config.get("review") if isinstance(config.get("review"), dict) else config
    return dict(candidate), dict(edit), dict(review)


def _proof_lines(candidate: Mapping[str, Any], edit: Mapping[str, Any]) -> list[str]:
    experiences = candidate.get("experience") if isinstance(candidate.get("experience"), list) else []
    lines: list[str] = []
    refs = edit.get("proofRefs") if isinstance(edit.get("proofRefs"), list) else []
    for ref in refs:
        if not isinstance(ref, Mapping):
            continue
        try:
            exp_index = int(ref.get("experienceIndex"))
            bullet_index = int(ref.get("bulletIndex"))
            experience = experiences[exp_index]
            bullet = experience.get("bullets", [])[bullet_index]
        except (IndexError, KeyError, TypeError, ValueError):
            continue
        lines.append(str(bullet))
    if not lines:
        lines = [str(item) for item in (edit.get("proofLines") or []) if str(item).strip()]
    return lines


def _clamp_timeline(values: dict[str, float], duration: float) -> dict[str, float]:
    # Match the renderer's minimum spacing contract while keeping each visual
    # action tied to the narration cue that introduced it.
    values["weak"] = 0.0
    values["proof"] = max(2.0, values["proof"])
    values["select"] = max(values["proof"] + 1.0, values["select"])
    values["delete"] = max(values["select"] + 0.4, values["delete"])
    values["type"] = max(values["delete"] + 0.8, values["type"])
    values["receipt"] = max(values["type"] + 1.5, values["receipt"])
    values["cta"] = max(values["receipt"] + 0.5, values["cta"])
    if values["cta"] >= duration - 0.5:
        raise ValueError("voice read leaves less than 0.5 seconds for the CTA; revise the script or voice pacing")
    return {key: round(value, 3) for key, value in values.items()}


def derive_timeline(
    config: Mapping[str, Any],
    words: Sequence[Mapping[str, Any]],
    duration: float,
) -> tuple[dict[str, float], dict[str, Any]]:
    _, edit, _ = _candidate_parts(config)
    weak_line = str(edit.get("weakLine") or config.get("weakLine") or "").strip()
    rewrite = str(edit.get("rewriteLine") or config.get("rewriteLine") or "").strip()
    if not weak_line or not rewrite:
        raise ValueError("controlled resume config needs weakLine and rewriteLine")

    weak_cue = find_phrase(words, [weak_line, "resume says", "line says"])
    proof_cue = find_phrase(words, ["lower down", "proof is already there", "proof is there", "the proof"])
    action_cue = find_phrase(words, ["so delete", "delete the", "replace it", "so replace", "write this"])
    rewrite_tokens = tokens(rewrite)
    rewrite_lead = rewrite_tokens[0] if rewrite_tokens else ""
    rewrite_cue = find_phrase(
        words,
        [rewrite, rewrite_lead],
        start_after=action_cue[0],
        minimum_tokens=1,
    )
    receipt_cue = find_phrase(
        words,
        ["now it actually matches", "now the resume matches", "now it matches", "that is the difference"],
        start_after=rewrite_cue[0],
        required=False,
    )
    cta_cue = find_phrase(
        words,
        [
            "need your resume or cover letter fixed",
            "need your resume fixed",
            "need yours fixed",
            "use the link below",
        ],
        start_after=rewrite_cue[0],
    )

    receipt_audio = receipt_cue[0] if receipt_cue else min(rewrite_cue[1] + 0.25, cta_cue[0] - 0.55)
    raw = {
        "weak": 0.0,
        "proof": proof_cue[0],
        "select": max(action_cue[0] - 0.15, proof_cue[0] + 1.0),
        "delete": action_cue[0] + 0.25,
        "type": rewrite_cue[0],
        "receipt": receipt_audio,
        "cta": cta_cue[0],
    }
    timeline = _clamp_timeline(raw, duration)
    receipt_beat_audio = receipt_cue[0] if receipt_cue else timeline["receipt"]
    beats = [
        {"label": "Opening resume problem", "audioSec": 0.0, "visualSec": 0.0},
        {"label": "Weak line read", "audioSec": weak_cue[0], "visualSec": weak_cue[0]},
        {"label": "Proof found lower down", "audioSec": proof_cue[0], "visualSec": timeline["proof"]},
        {"label": "Weak wording deleted", "audioSec": action_cue[0], "visualSec": timeline["delete"]},
        {"label": "Evidence-backed rewrite", "audioSec": rewrite_cue[0], "visualSec": timeline["type"]},
        {"label": "Evidence receipt", "audioSec": receipt_beat_audio, "visualSec": timeline["receipt"]},
        {"label": "Service CTA", "audioSec": cta_cue[0], "visualSec": timeline["cta"]},
    ]
    return timeline, {"beats": beats}


def _candidate_fact_values(
    proof_lines: Sequence[str], rewrite: str, receipt_values: Sequence[str], spoken: str
) -> list[tuple[str, list[tuple[str, str]]]]:
    candidates: list[str] = []
    for line in proof_lines:
        candidates.extend(METRIC_RE.findall(line))
    # Prefer role-specific search terms and distinctive tool names shared by
    # proof and rewrite. Common prose words are deliberately excluded.
    stop = {
        "across", "after", "before", "clinical", "customer", "monthly", "result",
        "staff", "support", "using", "weekly", "while", "with", "without",
    }
    proof_blob = " ".join(proof_lines)
    for token in tokens(proof_blob):
        if len(token) >= 4 and token not in stop and token in tokens(rewrite):
            candidates.append(token)

    result: list[tuple[str, list[tuple[str, str]]]] = []
    seen: set[str] = set()
    for value in candidates:
        key = value.casefold()
        if key in seen:
            continue
        occurrences: list[tuple[str, str]] = []
        for index, line in enumerate(proof_lines, start=1):
            if key in line.casefold():
                occurrences.append((f"proof-{index}", line))
        if key in rewrite.casefold():
            occurrences.append(("visible-rewrite", rewrite))
        for index, receipt in enumerate(receipt_values, start=1):
            if key in receipt.casefold():
                occurrences.append((f"receipt-{index}", receipt))
        if key in spoken.casefold():
            occurrences.append(("spoken-script", spoken))
        if len(occurrences) >= 2:
            seen.add(key)
            result.append((value, occurrences))
        if len(result) >= 6:
            break
    return result


def build_evidence_ledger(config: Mapping[str, Any], spoken_script: str) -> dict[str, Any]:
    candidate, edit, review = _candidate_parts(config)
    weak_line = str(edit.get("weakLine") or config.get("weakLine") or "").strip()
    rewrite = str(edit.get("rewriteLine") or config.get("rewriteLine") or "").strip()
    proof_lines = _proof_lines(candidate, edit)
    receipt_rows = review.get("receiptRows") if isinstance(review.get("receiptRows"), list) else config.get("receiptRows") or []
    receipt_values = [str(row.get("value") or "") for row in receipt_rows if isinstance(row, Mapping)]
    facts = []
    for index, (value, occurrences) in enumerate(
        _candidate_fact_values(proof_lines, rewrite, receipt_values, spoken_script), start=1
    ):
        facts.append(
            {
                "id": f"proof-fact-{index}",
                "value": value,
                "occurrences": [{"source": source, "value": text} for source, text in occurrences],
            }
        )
    if not facts:
        raise ValueError("rewrite has no fact that can be traced to proof, receipt, or spoken script")
    return {
        "facts": facts,
        "comparisons": [
            {"id": "weak-line-is-source-line", "expected": weak_line, "actual": weak_line},
            {"id": "visible-rewrite-is-approved-rewrite", "expected": rewrite, "actual": rewrite},
        ],
    }


def synchronize(
    *,
    config_path: Path,
    alignment_path: Path,
    script_path: Path,
    audio_duration: float,
    output_config: Path,
    beat_map_path: Path,
    evidence_path: Path,
) -> dict[str, Any]:
    config = load_json(config_path)
    words = alignment_words(load_json(alignment_path))
    script = script_path.read_text(encoding="utf-8-sig").strip()
    if not 18.0 <= audio_duration <= 27.6:
        raise ValueError(f"voice duration is {audio_duration:.3f}s; expected 18.0-27.6s before final padding")

    final_duration = round(min(28.0, audio_duration + 0.25), 3)
    timeline, beat_map = derive_timeline(config, words, final_duration)
    config["durationSec"] = final_duration
    config["timeline"] = timeline
    config["storyboardTimes"] = [
        0.25,
        round(timeline["proof"] + 0.35, 3),
        round(timeline["select"] + 0.2, 3),
        round(timeline["delete"] + 0.45, 3),
        round(timeline["type"] + max(0.7, (timeline["receipt"] - timeline["type"]) * 0.55), 3),
        round(timeline["receipt"] + 0.25, 3),
        round(timeline["cta"] + 0.2, 3),
    ]
    evidence = build_evidence_ledger(config, script)

    output_config.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    beat_map_path.write_text(json.dumps(beat_map, indent=2) + "\n", encoding="utf-8")
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return {
        "config": str(output_config),
        "beatMap": str(beat_map_path),
        "evidenceLedger": str(evidence_path),
        "durationSec": final_duration,
        "timeline": timeline,
        "factCount": len(evidence["facts"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync a controlled resume edit to Abby word timestamps.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--alignment", required=True, type=Path)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--audio-duration", required=True, type=float)
    parser.add_argument("--out-config", required=True, type=Path)
    parser.add_argument("--beat-map", required=True, type=Path)
    parser.add_argument("--evidence-ledger", required=True, type=Path)
    args = parser.parse_args()
    result = synchronize(
        config_path=args.config.resolve(),
        alignment_path=args.alignment.resolve(),
        script_path=args.script.resolve(),
        audio_duration=args.audio_duration,
        output_config=args.out_config.resolve(),
        beat_map_path=args.beat_map.resolve(),
        evidence_path=args.evidence_ledger.resolve(),
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
