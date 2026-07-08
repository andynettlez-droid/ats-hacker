#!/usr/bin/env python3
"""Signal Growth Engine pipeline helper.

This replaces the old one-off video script with a small, durable command runner:
research/script assets live in files, Veo creates clips, ElevenLabs creates Abby VO,
ffmpeg assembles, and Codex approval remains the only publish gate.
"""

from __future__ import annotations

import argparse
import base64
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from html import escape
import json
import mimetypes
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
MARKETING_DIR = ROOT / "marketing"
RUNS_DIR = MARKETING_DIR / "growth_runs"
DB_PATH = MARKETING_DIR / "signal_growth_engine.sqlite"
SKILLS_DIR = ROOT / "skills"
ASSEMBLE_PS1 = SKILLS_DIR / "assemble.ps1"

ABBY_VOICE_ID = "lkFHOvhI41u53xDdGZoZ"
DEFAULT_VEO_MODEL = "veo-3.1-lite-generate-preview"

OVERLAY_CANVAS = (1080, 1920)

QUALITY_GATES_DIRNAME = "quality_gates"

BANNED_SCRIPT_PATTERNS = [
    r"\bsame person\.?\s+better signal\b",
    r"\bunlock your career potential\b",
    r"\bbeat the bots\b",
    r"\bguaranteed interviews?\b",
    r"\bats auto[- ]?reject",
    r"\bautomatically reject",
    r"\bsemantic relevance\b",
    r"\boptimized alignment\b",
    r"\bATS-friendly artifact\b",
    r"\bAI-powered solution\b",
    r"\bcutting-edge\b",
]

AI_SLOP_WORDS = {
    "leverage",
    "unlock",
    "optimize",
    "streamline",
    "robust",
    "seamless",
    "synergy",
    "tailored solution",
    "career potential",
}

REQUIRED_QUALITY_GATES = ("research_swipe", "script_qa", "creative_qa", "plate_qa")

CREATIVE_GATE_FILES = (
    "viral_resume_swipe_file.md",
    "exemplar_matrix.csv",
    "script_options.md",
    "selected_script.md",
    "storyboard_options.md",
    "blunt_creative_review.md",
)

STATUS_ORDER = {
    "QUEUED",
    "RESEARCHED",
    "SCRIPTED",
    "AWAITING_CREATIVE_APPROVAL",
    "CREATIVE_APPROVED",
    "VOICED",
    "VIDEO_GENERATED",
    "RENDERED",
    "QA_PASSED",
    "AWAITING_CODEX_APPROVAL",
    "APPROVED",
    "REJECTED",
    "REVISION_REQUESTED",
    "PUBLISHED",
    "MEASURED",
    "FAILED",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        # The project .env is the source of truth for this pipeline. This avoids
        # stale shell-level keys from older projects silently taking priority.
        os.environ[key] = value


def load_env() -> None:
    load_env_file(ROOT / ".env")
    load_env_file(Path(__file__).resolve().parent / ".env")


def db() -> sqlite3.Connection:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS video_runs (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            title TEXT,
            status TEXT NOT NULL,
            landing_url TEXT,
            utm_source TEXT,
            utm_content TEXT,
            video_path TEXT,
            audio_path TEXT,
            alignment_path TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            qa_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS video_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def emit(obj: dict[str, Any]) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=True))


def run_folder(run_id: str) -> Path:
    folder = RUNS_DIR / run_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def quality_gate_dir(work_dir: Path) -> Path:
    folder = work_dir / QUALITY_GATES_DIRNAME
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def write_quality_gate(work_dir: Path, name: str, report: dict[str, Any], run_id: str | None = None) -> Path:
    report = {
        **report,
        "gate": name,
        "checkedAt": utc_now(),
    }
    path = quality_gate_dir(work_dir) / f"{name}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    if run_id:
        conn = db()
        get_run(conn, run_id)
        row = get_run(conn, run_id)
        metadata = json.loads(row["metadata_json"] or "{}")
        metadata.setdefault("qualityGates", {})[name] = {
            "path": str(path),
            "passed": bool(report.get("passed")),
            "blockerCount": len(report.get("blockers", [])),
            "warningCount": len(report.get("warnings", [])),
            "checkedAt": report["checkedAt"],
        }
        update_run(conn, run_id, metadata_json=json.dumps(metadata))
        log_event(conn, run_id, name, report)
        conn.commit()
    return path


def read_quality_gate(work_dir: Path, name: str) -> dict[str, Any] | None:
    path = work_dir / QUALITY_GATES_DIRNAME / f"{name}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"passed": False, "blockers": [f"{name}.json is not valid JSON"], "path": str(path)}


def require_quality_gates(work_dir: Path) -> list[str]:
    blockers: list[str] = []
    for gate in required_quality_gate_names(work_dir):
        report = read_quality_gate(work_dir, gate)
        if not report:
            blockers.append(f"missing quality gate: {QUALITY_GATES_DIRNAME}/{gate}.json")
            continue
        if not report.get("passed"):
            details = "; ".join(str(item) for item in report.get("blockers", [])[:3])
            blockers.append(f"quality gate failed: {gate}" + (f" ({details})" if details else ""))
    return blockers


def required_quality_gate_names(work_dir: Path) -> tuple[str, ...]:
    try:
        brief = load_resume_brief(work_dir)
    except Exception:
        brief = {}
    format_name = str(brief.get("format", "") or "").strip()
    if format_name == "screen_recording_teardown":
        return ("creative_gate", "script_qa", "screen_visual_qa")
    gates = ["creative_gate", "script_qa", "creative_qa"]
    physical_surface_formats = {
        "paper_desk_teardown",
        "paper_desk_roast_rebuild",
        "tablet_screen_teardown",
        "tablet_screen_edit_rebuild",
        "surface_fit_storyboard",
    }
    if format_name in physical_surface_formats or (work_dir / "surface_fit.json").exists():
        gates.extend(["plate_qa", "surface_fit_qa"])
    else:
        gates.append("plate_qa")
    return tuple(gates)


def extract_section(markdown: str, heading: str, next_heading_prefix: str = "## ") -> str:
    marker = f"## {heading}"
    if marker not in markdown:
        return ""
    after = markdown.split(marker, 1)[1]
    if next_heading_prefix in after:
        return after.split(next_heading_prefix, 1)[0]
    return after


def selected_voice_script(work_dir: Path) -> str:
    selected_path = work_dir / "selected_script.md"
    if not selected_path.exists():
        return ""
    selected = selected_path.read_text(encoding="utf-8", errors="ignore")
    voice = extract_section(selected, "Voiceover Script")
    return markdown_to_plain(voice or selected)


SOURCE_BACKED_EVIDENCE_STRENGTHS = {
    "verified_youtube_metadata",
    "linkedin_post_text_verified",
    "linkedin_transcript_verified",
    "instagram_snippet_verified",
}


def filled_cell(row: dict[str, str], field: str) -> bool:
    return bool(str(row.get(field, "") or "").strip())


def phrase_index(text: str, phrases: tuple[str, ...]) -> int:
    hits = [text.find(phrase) for phrase in phrases if phrase in text]
    return min(hits) if hits else -1


def has_approved_cta(text: str) -> bool:
    lower = text.lower()
    return any(
        phrase in lower
        for phrase in (
            "need your resume or cover letter fixed",
            "need your resume fixed",
            "need yours fixed",
            "upload it to signal before you apply",
            "use the link below before you apply",
            "run the free signal score before you apply",
        )
    )


def has_weak_line_cue(text: str) -> bool:
    lower = text.lower()
    return any(
        phrase in lower
        for phrase in (
            "resume says",
            "line says",
            "this line is the problem",
            "first bullet:",
            "weak line:",
            "his resume says",
            "her resume says",
        )
    )


def human_review_flow_blockers(text: str) -> list[str]:
    """Catch scripts that contain the right ingredients but in a robotic order."""
    lower = text.lower()
    checks = [
        ("candidate and role", ("this is ", "here's ", "applying for", "targeting", "i am screening", "i'm screening")),
        (
            "recruiter search terms",
            (
                "checking for",
                "checking is",
                "searching for",
                "recruiters are actually searching",
                "the job wants",
                "job is looking for",
                "job asks for",
            ),
        ),
        ("weak line quote", ("resume says", "line says", "this line is the problem", "first bullet:", "weak line:", "says,")),
        (
            "human judgment",
            (
                "sounds professional",
                "too vague",
                "means nothing",
                "too blurry",
                "gets skipped",
                "resume's not awful",
                "written like",
                "could mean",
                "now i know what you actually do",
                "that's a real",
            ),
        ),
        (
            "proof already on resume",
            (
                "lower down",
                "proof is there",
                "proof is lower",
                "already has the proof",
                "has proof lower",
                "proof lower",
            ),
        ),
        ("visible edit", ("delete", "replace", "write:", "write ", "i would delete", "pulls it up", "fix:")),
        (
            "CTA",
            (
                "need your resume or cover letter fixed",
                "need your resume fixed",
                "need yours fixed",
                "upload it to signal before you apply",
                "run the free signal score before you apply",
            ),
        ),
    ]
    blockers = [f"script missing human-review beat: {label}" for label, phrases in checks if phrase_index(lower, phrases) < 0]

    positions = {
        "candidate/role": phrase_index(lower, checks[0][1]),
        "search terms": phrase_index(lower, checks[1][1]),
        "weak line": phrase_index(lower, checks[2][1]),
        "judgment": phrase_index(lower, checks[3][1]),
        "proof": phrase_index(lower, checks[4][1]),
        "edit": phrase_index(lower, checks[5][1]),
        "CTA": phrase_index(lower, checks[6][1]),
    }
    constraints = [
        ("candidate/role", "proof"),
        ("candidate/role", "CTA"),
        ("search terms", "proof"),
        ("weak line", "proof"),
        ("judgment", "proof"),
        ("proof", "edit"),
        ("edit", "CTA"),
    ]
    for before, after in constraints:
        if positions[before] >= 0 and positions[after] >= 0 and positions[before] > positions[after]:
            blockers.append(f"script beat order problem: {before} should come before {after}")
    return blockers


def validate_no_credit_creative_gate(
    work_dir: Path,
    min_sources: int = 20,
    min_resume_sources: int = 10,
    min_document_refs: int = 2,
    min_source_backed_rows: int = 16,
    min_hook_rows: int = 16,
    min_breakdown_rows: int = 14,
    min_words: int = 42,
    max_words: int = 96,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    for filename in CREATIVE_GATE_FILES:
        if not (work_dir / filename).exists():
            blockers.append(f"missing required creative gate file: {filename}")

    rows: list[dict[str, str]] = []
    matrix_path = work_dir / "exemplar_matrix.csv"
    if matrix_path.exists():
        try:
            with matrix_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        except Exception as exc:
            blockers.append(f"exemplar_matrix.csv could not be read: {exc}")
    else:
        blockers.append("exemplar_matrix.csv is required")

    if rows and len(rows) < min_sources:
        blockers.append(f"exemplar_matrix.csv has {len(rows)} rows; expected at least {min_sources}")

    def row_blob(row: dict[str, str]) -> str:
        return " ".join(str(value or "") for value in row.values()).lower()

    resume_related = sum(
        1
        for row in rows
        if any(term in row_blob(row) for term in ("resume", "recruiter", "job-search", "job search", "career coach", "cv"))
    )
    document_refs = sum(
        1
        for row in rows
        if any(term in row_blob(row) for term in ("document edit", "tablet", "screen recording", "screen-recording", "red pen", "word document"))
    )
    source_backed = sum(
        1
        for row in rows
        if str(row.get("evidence_strength", "") or "").strip() in SOURCE_BACKED_EVIDENCE_STRENGTHS
        or str(row.get("transcript_status", "") or "").strip().lower() in {"transcript cached locally", "metadata reviewed"}
    )
    hook_rows = sum(1 for row in rows if filled_cell(row, "hook_text"))
    breakdown_rows = sum(1 for row in rows if filled_cell(row, "beat_by_beat_breakdown"))
    copy_rows = sum(1 for row in rows if filled_cell(row, "what_signal_should_copy"))
    avoid_rows = sum(1 for row in rows if filled_cell(row, "what_signal_should_avoid"))
    if rows and resume_related < min_resume_sources:
        blockers.append(f"only {resume_related} resume/recruiter/job-search examples; expected at least {min_resume_sources}")
    if rows and document_refs < min_document_refs:
        blockers.append(f"only {document_refs} document/tablet edit references; expected at least {min_document_refs}")
    if rows and source_backed < min_source_backed_rows:
        blockers.append(f"only {source_backed} source-backed examples; expected at least {min_source_backed_rows}")
    if rows and hook_rows < min_hook_rows:
        blockers.append(f"only {hook_rows} examples have hook_text; expected at least {min_hook_rows}")
    if rows and breakdown_rows < min_breakdown_rows:
        blockers.append(f"only {breakdown_rows} examples have beat-by-beat breakdowns; expected at least {min_breakdown_rows}")
    if rows and (copy_rows < min_hook_rows or avoid_rows < min_hook_rows):
        blockers.append(
            "exemplar_matrix.csv must explain what Signal should copy and avoid for most examples "
            f"(copy rows: {copy_rows}, avoid rows: {avoid_rows}, expected at least {min_hook_rows})"
        )

    options_path = work_dir / "script_options.md"
    options_text = options_path.read_text(encoding="utf-8", errors="ignore") if options_path.exists() else ""
    option_count = len(re.findall(r"^## Option\s+\d+", options_text, flags=re.M))
    if option_count < 5:
        blockers.append(f"script_options.md has {option_count} script options; expected at least 5")
    if "Read-Aloud Review" not in options_text:
        blockers.append("script_options.md must include read-aloud review notes")
    if not re.search(r"\bRejected\b|\bParked\b", options_text, flags=re.I):
        blockers.append("script_options.md must include rejected or parked script notes")

    selected_script = selected_voice_script(work_dir)
    word_count = count_words(selected_script)
    if not selected_script:
        blockers.append("selected_script.md must include a voiceover script")
    elif word_count < min_words or word_count > max_words:
        blockers.append(f"selected voiceover is {word_count} words; expected {min_words}-{max_words}")

    selected_lower = selected_script.lower()
    banned_hits = [pattern for pattern in BANNED_SCRIPT_PATTERNS if re.search(pattern, selected_lower, flags=re.I)]
    extra_banned = [
        phrase
        for phrase in (
            "this resume is invisible",
            "same person, better signal",
            "ats rejected",
            "optimize your career journey",
            "signal helps",
        )
        if phrase in selected_lower
    ]
    if banned_hits or extra_banned:
        blockers.append("selected script contains banned language: " + ", ".join([*banned_hits, *extra_banned]))
    if not has_approved_cta(selected_script):
        blockers.append("selected script must end with an approved direct-service CTA")
    if not has_weak_line_cue(selected_script):
        blockers.append("selected script must read one exact weak resume line")
    if not any(term in selected_lower for term in ("lower down", "proof is there", "proof is lower", "proof lower", "has proof lower")):
        blockers.append("selected script must point to proof already elsewhere on the resume")
    if not any(term in selected_lower for term in ("delete", "replace", "write", "pulls it up", "fix:")):
        blockers.append("selected script must describe a visible edit")
    if "signal helps" in selected_lower or "signal is" in selected_lower:
        blockers.append("product-demo language appears before the CTA")
    blockers.extend(human_review_flow_blockers(selected_script))

    storyboard_path = work_dir / "storyboard_options.md"
    storyboard = storyboard_path.read_text(encoding="utf-8", errors="ignore") if storyboard_path.exists() else ""
    direction_count = len(re.findall(r"^## Direction\s+\d+", storyboard, flags=re.M))
    if direction_count < 3:
        blockers.append(f"storyboard_options.md has {direction_count} directions; expected at least 3")
    if "SELECTED" not in storyboard:
        blockers.append("storyboard_options.md must mark one selected direction")
    if not re.search(r"render(?:ing)? remains blocked|rendering is blocked|no.*render", storyboard, flags=re.I):
        blockers.append("storyboard_options.md must explicitly block rendering until approval")
    if re.search(r"fake hand|fake stylus", storyboard, flags=re.I) and "do not add fake hands" not in storyboard.lower():
        warnings.append("storyboard mentions fake hand/stylus; verify it is a ban, not an instruction")
    timestamped_beats = len(re.findall(r"\b\d{1,2}(?:\.\d+)?\s*(?:-|–|to)\s*\d{1,2}(?:\.\d+)?\s*s", storyboard, flags=re.I))
    if timestamped_beats < 5:
        blockers.append(
            "storyboard_options.md must include at least 5 timestamped beats like `0-2s`, `2-5s`; "
            f"found {timestamped_beats}"
        )
    if not re.search(r"first frame|opening frame|frame one", storyboard, flags=re.I):
        blockers.append("storyboard_options.md must describe the first frame because the video must work with sound off")
    if not re.search(r"camera|composition|close[- ]?up|overhead|phone[- ]?shot|desk angle|screen angle", storyboard, flags=re.I):
        blockers.append("storyboard_options.md must describe shot composition/camera language, not only concept bullets")
    if not re.search(r"payoff|reveal|transformation|before/after|visible edit|visual gag|scroll stop", storyboard, flags=re.I):
        blockers.append("storyboard_options.md must explain the visual payoff that makes the short worth watching")

    creative_review_path = work_dir / "blunt_creative_review.md"
    creative_review = creative_review_path.read_text(encoding="utf-8", errors="ignore") if creative_review_path.exists() else ""
    if creative_review:
        if re.search(r"verdict\s*:\s*fail", creative_review, flags=re.I):
            blockers.append("blunt_creative_review.md verdict is FAIL")
        if not re.search(r"verdict\s*:\s*pass", creative_review, flags=re.I):
            blockers.append("blunt_creative_review.md must include an explicit `Verdict: PASS` before creative approval")
        for required_phrase, label in (
            (r"scroll[- ]?stop|first\s+\d+\s*seconds?|first frame", "scroll-stop/first-frame critique"),
            (r"real creator|real recruiter|human reviewer|human sounding|would a real", "human creator voice critique"),
            (r"visual payoff|payoff|transformation|before/after", "visual payoff critique"),
            (r"what still fails|what still feels weak|failure risk|why it fails", "failure-risk critique"),
        ):
            if not re.search(required_phrase, creative_review, flags=re.I):
                blockers.append(f"blunt_creative_review.md missing {label}")
    else:
        blockers.append("blunt_creative_review.md is required and must contain an explicit creative verdict")

    report = {
        "passed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "sourceCount": len(rows),
        "resumeRelatedSourceCount": resume_related,
        "documentEditReferenceCount": document_refs,
        "sourceBackedExampleCount": source_backed,
        "hookRowCount": hook_rows,
        "breakdownRowCount": breakdown_rows,
        "copyRowCount": copy_rows,
        "avoidRowCount": avoid_rows,
        "scriptOptionCount": option_count,
        "selectedVoiceWordCount": word_count,
        "requiredFiles": list(CREATIVE_GATE_FILES),
        "selectedScriptPreview": selected_script[:800],
        "approvalPhrase": f"APPROVE CREATIVE GATE {work_dir.name}",
    }
    return report


def creative_gate_preflight(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve()
    report = validate_no_credit_creative_gate(
        work_dir,
        min_sources=args.min_sources,
        min_resume_sources=args.min_resume_sources,
        min_document_refs=args.min_document_refs,
        min_source_backed_rows=args.min_source_backed_rows,
        min_hook_rows=args.min_hook_rows,
        min_breakdown_rows=args.min_breakdown_rows,
        min_words=args.min_words,
        max_words=args.max_words,
    )
    path = write_quality_gate(work_dir, "creative_gate", report, args.run_id)
    report["reportPath"] = str(path)
    if args.run_id:
        conn = db()
        row = get_run(conn, args.run_id)
        metadata = json.loads(row["metadata_json"] or "{}")
        metadata["creativeApprovalPhrase"] = report["approvalPhrase"]
        metadata["creativeGateApproved"] = False
        metadata["creativeGateReportPath"] = str(path)
        if report["passed"]:
            update_run(conn, args.run_id, status="AWAITING_CREATIVE_APPROVAL", metadata_json=json.dumps(metadata))
        else:
            update_run(conn, args.run_id, status="REVISION_REQUESTED", metadata_json=json.dumps(metadata))
        log_event(conn, args.run_id, "creative_gate", report)
        conn.commit()
    emit(report)
    if report["blockers"]:
        raise SystemExit(1)


def require_creative_gate_for_paid_step(run_id: str | None, allow_unapproved: bool = False) -> None:
    if not run_id or allow_unapproved:
        return
    work_dir = run_folder(run_id)
    report = read_quality_gate(work_dir, "creative_gate")
    if not report or not report.get("passed"):
        raise SystemExit(
            "Creative gate has not passed for this run. Run "
            f"`creative-gate --work-dir {work_dir} --run-id {run_id}` and get Codex approval before paid generation."
        )
    conn = db()
    row = get_run(conn, run_id)
    metadata = json.loads(row["metadata_json"] or "{}")
    if not metadata.get("creativeGateApproved"):
        phrase = metadata.get("creativeApprovalPhrase") or report.get("approvalPhrase") or f"APPROVE CREATIVE GATE {run_id}"
        raise SystemExit(
            "Creative gate passed but has not been explicitly approved. "
            f"Approve with `approve-creative --run-id {run_id} --phrase \"{phrase}\"` before paid generation."
        )


def approve_creative(args: argparse.Namespace) -> None:
    conn = db()
    row = get_run(conn, args.run_id)
    work_dir = run_folder(args.run_id)
    report = read_quality_gate(work_dir, "creative_gate")
    if not report or not report.get("passed"):
        raise SystemExit("Cannot approve creative gate because quality_gates/creative_gate.json is missing or failed.")
    metadata = json.loads(row["metadata_json"] or "{}")
    expected = metadata.get("creativeApprovalPhrase") or report.get("approvalPhrase") or f"APPROVE CREATIVE GATE {args.run_id}"
    if args.phrase.strip() != expected:
        raise SystemExit(f"Approval phrase mismatch. Expected: {expected}")
    metadata["creativeGateApproved"] = True
    metadata["creativeApprovedAt"] = utc_now()
    metadata["creativeGateReportPath"] = str(work_dir / QUALITY_GATES_DIRNAME / "creative_gate.json")
    update_run(conn, args.run_id, status="CREATIVE_APPROVED", metadata_json=json.dumps(metadata))
    payload = {"runId": args.run_id, "status": "CREATIVE_APPROVED", "creativeApprovedAt": metadata["creativeApprovedAt"]}
    log_event(conn, args.run_id, "creative_approved", payload)
    conn.commit()
    emit(payload)


def creative_review_packet(args: argparse.Namespace) -> None:
    conn = db()
    row = get_run(conn, args.run_id)
    row_status = row["status"]
    work_dir = run_folder(args.run_id)
    metadata = json.loads(row["metadata_json"] or "{}")
    conn.close()
    creative_report = read_quality_gate(work_dir, "creative_gate") or {}
    script_report = read_quality_gate(work_dir, "script_qa") or {}
    screen_report = read_quality_gate(work_dir, "screen_visual_qa") or {}
    surface_report = read_quality_gate(work_dir, "surface_fit_qa") or {}
    brief = load_resume_brief(work_dir)
    format_name = str(brief.get("format", "") or "").strip()
    surface_formats = {
        "paper_desk_teardown",
        "paper_desk_roast_rebuild",
        "tablet_screen_teardown",
        "tablet_screen_edit_rebuild",
        "surface_fit_storyboard",
    }
    is_screen = format_name == "screen_recording_teardown"
    is_surface = format_name in surface_formats or (work_dir / "surface_fit.json").exists()
    approval_phrase = metadata.get("creativeApprovalPhrase") or creative_report.get("approvalPhrase") or f"APPROVE CREATIVE GATE {args.run_id}"
    selected_script = selected_voice_script(work_dir) or read_spoken_script(work_dir)
    storyboard_candidates = [
        work_dir / "screen_teardown_storyboard_contact_sheet.png",
        work_dir / "surface_fit_animatic_contact_sheet.png",
        work_dir / "storyboard_tablet_contact_sheet.png",
        work_dir / "storyboard_paper_contact_sheet.png",
    ]
    storyboard = next((path for path in storyboard_candidates if path.exists()), None)
    storyboard_rel = storyboard.name if storyboard else ""

    if is_screen:
        gate_passed = bool(creative_report.get("passed") and script_report.get("passed") and screen_report.get("passed"))
        direction = "Screen Recording Teardown."
        reason = "No fake hands, no fake stylus, no generated readable text, no random score jump, and the visible edit happens inside the resume."
        visual_gate_line = f'- `quality_gates/screen_visual_qa.json`: {"passed" if screen_report.get("passed") else "not passed"}.'
        visual_check = f"Screen visual QA: {'passed' if screen_report.get('passed') else 'not passed'}; {screen_report.get('frameCount', 0)} storyboard frames reviewed."
        after_approval = [
            "Record approval with `approve-creative`.",
            "Generate a 10-second Abby voice test only.",
            "Check pronunciation and pacing.",
            "If the voice passes, generate the full Abby voice.",
            "Render the screen-recording edit using deterministic readable resume text.",
            "Produce a final QA contact sheet and mobile review link.",
            "Stop before posting.",
        ]
    elif is_surface:
        gate_passed = bool(creative_report.get("passed") and script_report.get("passed"))
        direction = "Tablet/Paper Surface-Fit Teardown."
        reason = "The physical plate owns the desk/tablet realism while deterministic overlays own every readable resume word, mark, rewrite, receipt, and CTA."
        visual_gate_line = (
            f'- `quality_gates/surface_fit_qa.json`: {"passed" if surface_report.get("passed") else "not required before creative approval; required before final assembly"}.'
        )
        visual_check = (
            f"Surface-fit QA: {'passed' if surface_report.get('passed') else 'pending until clean plates exist'}; "
            "must pass after full-size fitted preview review."
        )
        after_approval = [
            "Record approval with `approve-creative`.",
            "Generate Abby voice from the approved script.",
            "Generate or source clean blank paper/tablet plates with no readable text.",
            "Run `plate-qa` on the clean plates.",
            "Corner-pin deterministic overlays with `surface-fit-preview`.",
            "Inspect full-size previews and run `surface-fit-qa --visual-reviewed`.",
            "Build the surface-fit animatic/final video, produce QA contact sheet, and stop before posting.",
        ]
    else:
        gate_passed = bool(creative_report.get("passed") and script_report.get("passed"))
        direction = "General Signal Teardown."
        reason = "Research and human-read script gate passed; format-specific production gates still apply before final assembly."
        visual_gate_line = "- Format-specific visual QA: pending."
        visual_check = "Format-specific visual QA: pending."
        after_approval = [
            "Record approval with `approve-creative`.",
            "Generate only the approved voice/video assets for the selected format.",
            "Run all required visual and technical QA gates.",
            "Stop before posting.",
        ]
    after_approval_md = "\n".join(f"{index}. {item}" for index, item in enumerate(after_approval, start=1))
    packet_md = f"""# Codex Creative Gate Packet

Run: `{args.run_id}`

Status: `{row_status}`

No Abby, Veo, Flow, final render, or posting APIs are required to create this packet.

## Gate Evidence

- `viral_resume_swipe_file.md`: research synthesis.
- `exemplar_matrix.csv`: {creative_report.get("sourceCount", 0)} examples.
- `exemplar_matrix_enriched.csv`: source/evidence-strength metadata when available.
- `script_options.md`: {creative_report.get("scriptOptionCount", 0)} scripts with read-aloud review notes.
- `selected_script.md`: selected {creative_report.get("selectedVoiceWordCount", count_words(selected_script))}-word script.
- `storyboard_options.md`: three storyboard directions with one selected direction.
- Format: `{format_name or "unspecified"}`.
- `quality_gates/creative_gate.json`: {"passed" if creative_report.get("passed") else "not passed"}.
- `quality_gates/script_qa.json`: {"passed" if script_report.get("passed") else "not passed"}.
{visual_gate_line}

## Research Gate Metrics

- Sources: {creative_report.get("sourceCount", 0)}
- Resume/recruiter/job-search sources: {creative_report.get("resumeRelatedSourceCount", 0)}
- Document/tablet edit references: {creative_report.get("documentEditReferenceCount", 0)}
- Source-backed rows: {creative_report.get("sourceBackedExampleCount", 0)}
- Hook rows: {creative_report.get("hookRowCount", 0)}
- Beat-breakdown rows: {creative_report.get("breakdownRowCount", 0)}
- Copy/avoid rows: {creative_report.get("copyRowCount", 0)} / {creative_report.get("avoidRowCount", 0)}

## Selected Creative Direction

{direction}

Reason: {reason}

## Selected Script

{selected_script}

## Approval Phrase

`{approval_phrase}`

## What Happens After Approval

{after_approval_md}
"""
    packet_path = work_dir / "codex_creative_gate_packet.md"
    packet_path.write_text(packet_md, encoding="utf-8")

    checks = [
        f"Creative gate: {'passed' if creative_report.get('passed') else 'not passed'} with {creative_report.get('sourceCount', 0)} sources.",
        (
            "Research quality: "
            f"{creative_report.get('sourceBackedExampleCount', 0)} source-backed examples, "
            f"{creative_report.get('hookRowCount', 0)} hooks, "
            f"{creative_report.get('breakdownRowCount', 0)} beat breakdowns."
        ),
        f"Script QA: {'passed' if script_report.get('passed') else 'not passed'}; {script_report.get('wordCount', count_words(selected_script))} words.",
        "Human flow: candidate and role -> recruiter search terms -> weak line -> judgment -> proof -> visible edit -> CTA.",
        visual_check,
        "Paid generation remains locked until the exact creative approval phrase is provided.",
    ]
    checks_html = "\n".join(f"<li>{escape(item)}</li>" for item in checks)
    story_html = (
        f'<img src="{escape(storyboard_rel)}" alt="Storyboard contact sheet" />'
        if storyboard_rel
        else "<p>No storyboard contact sheet found.</p>"
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Signal Creative Gate Review</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f5f7fb; color: #0f172a; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.45; }}
    main {{ width: min(100% - 28px, 980px); margin: 0 auto; padding: 22px 0 44px; }}
    h1 {{ margin: 0; font-size: clamp(32px, 8vw, 56px); line-height: .95; }}
    h2 {{ margin: 0 0 12px; font-size: 22px; }}
    p {{ margin: 0; color: #526174; }}
    .hero {{ display: grid; gap: 14px; margin-bottom: 18px; }}
    .status {{ display: inline-flex; width: fit-content; padding: 8px 12px; border-radius: 999px; background: {'#ecfdf5' if gate_passed else '#fff7ed'}; color: {'#047857' if gate_passed else '#c2410c'}; border: 1px solid {'#bbf7d0' if gate_passed else '#fed7aa'}; font-weight: 800; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 18px 0; }}
    .card {{ background: #fff; border: 1px solid #dbe3ef; border-radius: 14px; padding: 18px; box-shadow: 0 12px 34px rgba(15, 23, 42, .06); margin-bottom: 16px; }}
    .metric strong {{ display: block; font-size: 30px; }}
    .metric span {{ display: block; color: #526174; font-size: 13px; }}
    img {{ width: 100%; display: block; border-radius: 12px; border: 1px solid #dbe3ef; }}
    .script {{ white-space: pre-wrap; font-size: 18px; line-height: 1.55; }}
    .checks {{ margin: 0; padding-left: 20px; }}
    .checks li {{ margin: 8px 0; }}
    .approval {{ margin-top: 12px; padding: 14px; border-radius: 12px; background: #0f172a; color: #fff; font-weight: 900; overflow-wrap: anywhere; }}
    .warn {{ border-color: #fbbf24; background: #fffbeb; }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} .card {{ padding: 14px; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <span class="status">{'Creative Gate Passed' if gate_passed else 'Creative Gate Needs Work'}</span>
      <h1>Signal Gold Creative Review</h1>
      <p>Run <strong>{escape(args.run_id)}</strong>. No Abby, Veo, Flow, final render, or posting APIs are used by this review packet.</p>
    </section>
    <section class="grid">
      <article class="card metric"><strong>{creative_report.get('sourceCount', 0)}</strong><span>research examples</span></article>
      <article class="card metric"><strong>{creative_report.get('sourceBackedExampleCount', 0)}</strong><span>source-backed rows</span></article>
      <article class="card metric"><strong>{creative_report.get('scriptOptionCount', 0)}</strong><span>script options</span></article>
      <article class="card metric"><strong>{creative_report.get('selectedVoiceWordCount', count_words(selected_script))}</strong><span>spoken words</span></article>
    </section>
    <section class="card">
      <h2>Storyboard</h2>
      {story_html}
    </section>
    <section class="card">
      <h2>Selected Script</h2>
      <div class="script">{escape(selected_script)}</div>
    </section>
    <section class="card">
      <h2>Passed Gates</h2>
      <ul class="checks">
        {checks_html}
      </ul>
    </section>
    <section class="card warn">
      <h2>Approval Required</h2>
      <p><strong>Paid generation is locked.</strong> The pipeline will refuse Abby, Veo, Flow, and screen build commands until this exact phrase is approved in Codex:</p>
      <div class="approval">{escape(approval_phrase)}</div>
    </section>
  </main>
</body>
</html>
"""
    html_path = work_dir / "creative_review.html"
    html_path.write_text(html, encoding="utf-8")

    mobile_url = f"http://{args.host}:{args.port}/{html_path.name}" if args.host else None
    payload = {
        "runId": args.run_id,
        "status": row_status,
        "creativeGatePassed": gate_passed,
        "packetPath": str(packet_path),
        "htmlPath": str(html_path),
        "mobileUrl": mobile_url,
        "approvalPhrase": approval_phrase,
    }
    emit(payload)


def markdown_to_plain(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", text)
    text = re.sub(r"^[#>*+\-\s]+", " ", text, flags=re.M)
    return re.sub(r"\s+", " ", text).strip()


def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'$.-]*", text))


def vtt_time_to_seconds(value: str) -> float:
    parts = value.strip().split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return (int(hours) * 3600) + (int(minutes) * 60) + float(seconds)
    if len(parts) == 2:
        minutes, seconds = parts
        return (int(minutes) * 60) + float(seconds)
    return float(parts[0])


def clean_caption_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = (
        text.replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&gt;", ">")
        .replace("&lt;", "<")
    )
    return re.sub(r"\s+", " ", text).strip()


def parse_vtt(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if "-->" not in line:
            i += 1
            continue
        start_raw, rest = line.split("-->", 1)
        end_raw = rest.strip().split()[0]
        i += 1
        text_lines: list[str] = []
        while i < len(lines) and lines[i].strip():
            if not lines[i].startswith("NOTE"):
                text_lines.append(lines[i])
            i += 1
        text = clean_caption_text(" ".join(text_lines))
        if text:
            events.append({"startSec": vtt_time_to_seconds(start_raw), "endSec": vtt_time_to_seconds(end_raw), "text": text})
        i += 1
    compact: list[dict[str, Any]] = []
    last_text = ""
    for event in events:
        text = str(event["text"])
        if text == last_text:
            continue
        if last_text and text.startswith(last_text):
            delta = text[len(last_text) :].strip()
            if delta:
                compact.append({**event, "text": delta})
        else:
            compact.append(event)
        last_text = text
    return compact


def scaffold_run_files(folder: Path, title: str, topic: str) -> None:
    files = {
        "research.md": f"# Research\n\nTopic: {topic}\n\n- Winning angle 1:\n- Winning angle 2:\n- Winning angle 3:\n",
        "script.md": (
            f"# Script: {title}\n\n"
            "Hook:\n\n"
            "Beats:\n\n"
            "CTA: Need yours fixed? Link in bio.\n"
        ),
        "shot01.txt": (
            "Vertical 9:16 short-form video shot. Use the active Signal/Veo prompt template. "
            "No on-screen text generated by the model. Keep the artifact readable and the movement motivated."
        ),
        "vo_hook.txt": "This resume looks fine, and that is exactly why the mistake is easy to miss.",
        "vo_search.txt": (
            "If the job asks for specific tools, your resume needs proof in that language. "
            "Otherwise a recruiter search can miss you."
        ),
        "vo_demo.txt": "The fix is not fake experience. It is saying the real work in the language of the job.",
        "vo_cta.txt": "Need yours fixed before you apply? The link is in my bio.",
    }
    for name, content in files.items():
        target = folder / name
        if not target.exists():
            target.write_text(content, encoding="utf-8")


def create_run(args: argparse.Namespace) -> None:
    conn = db()
    run_id = f"{datetime.now().strftime('%Y%m%d-%H%M')}-{uuid.uuid4().hex[:8]}"
    title = args.title or args.topic
    landing_url = args.landing_url or "https://ats-hacker-swart.vercel.app/?utm_source=codex&utm_medium=short&utm_campaign=signal_growth"
    now = utc_now()
    metadata = {
        "platforms": ["youtube_shorts", "tiktok", "instagram_reels"],
        "reviewRequired": True,
        "approvalPhrase": f"APPROVE POST {run_id}",
        "codexOnlyApproval": True,
        "publishBlockedUntilApproval": True,
    }
    conn.execute(
        """
        INSERT INTO video_runs (
          id, topic, title, status, landing_url, utm_source, utm_content,
          metadata_json, created_at, updated_at
        ) VALUES (?, ?, ?, 'QUEUED', ?, 'codex', ?, ?, ?, ?)
        """,
        (run_id, args.topic, title, landing_url, run_id, json.dumps(metadata), now, now),
    )
    log_event(conn, run_id, "created", metadata)
    conn.commit()
    folder = run_folder(run_id)
    (folder / "README.md").write_text(
        f"# {title}\n\nStatus: QUEUED\n\nApproval phrase: `APPROVE POST {run_id}`\n",
        encoding="utf-8",
    )
    scaffold_run_files(folder, title, args.topic)
    emit({"runId": run_id, "status": "QUEUED", "folder": str(folder), "approvalPhrase": metadata["approvalPhrase"]})


def get_run(conn: sqlite3.Connection, run_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM video_runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        raise SystemExit(f"Unknown run id: {run_id}")
    return row


def log_event(conn: sqlite3.Connection, run_id: str, event_type: str, payload: dict[str, Any]) -> None:
    conn.execute(
        "INSERT INTO video_events (run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
        (run_id, event_type, json.dumps(payload), utc_now()),
    )


def update_run(conn: sqlite3.Connection, run_id: str, **fields: Any) -> None:
    if "status" in fields and fields["status"] not in STATUS_ORDER:
        raise SystemExit(f"Invalid status: {fields['status']}")
    fields["updated_at"] = utc_now()
    assignments = ", ".join(f"{key}=?" for key in fields)
    conn.execute(f"UPDATE video_runs SET {assignments} WHERE id=?", (*fields.values(), run_id))


def read_text_arg(args: argparse.Namespace) -> str:
    if getattr(args, "text", None):
        return args.text
    if getattr(args, "text_file", None):
        return Path(args.text_file).read_text(encoding="utf-8").strip()
    raise SystemExit("Provide --text or --text-file")


def elevenlabs_key() -> str:
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not key or key.startswith("sk_your_"):
        raise SystemExit("ELEVENLABS_API_KEY is missing. Add it to marketing_agent/.env.")
    return key


def abby_voice_id() -> str:
    return (
        os.getenv("ELEVENLABS_ABBY_VOICE_ID")
        or os.getenv("ELEVENLABS_VOICE_ID")
        or ABBY_VOICE_ID
    ).strip()


def resolve_abby(args: argparse.Namespace) -> None:
    load_env()
    configured = abby_voice_id()
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if key and not key.startswith("sk_your_"):
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": key},
            timeout=30,
        )
        if response.ok:
            voices = response.json().get("voices", [])
            for voice in voices:
                if voice.get("name", "").strip().lower() == "abby":
                    emit({"voice": "Abby", "voiceId": voice.get("voice_id"), "source": "elevenlabs"})
                    return
        if args.strict:
            raise SystemExit(f"Could not read Abby voice from ElevenLabs: {response.status_code} {response.text[:200]}")
    emit({"voice": "Abby", "voiceId": configured, "source": "configured"})


def seconds_from_alignment_value(value: float) -> float:
    return value / 1000 if value > 100 else value


def normalize_alignment(alignment: dict[str, Any]) -> dict[str, Any]:
    source = alignment.get("normalized_alignment") or alignment.get("alignment") or alignment
    chars = source.get("characters") or source.get("chars") or []
    starts = source.get("character_start_times_seconds") or source.get("character_start_times_ms") or []
    ends = source.get("character_end_times_seconds") or []
    durations = source.get("character_durations_seconds") or source.get("character_durations_ms") or []
    if not chars or not starts:
        return {"words": [], "raw": alignment}

    starts = [seconds_from_alignment_value(float(v)) for v in starts]
    if ends:
        ends = [seconds_from_alignment_value(float(v)) for v in ends]
    elif durations:
        durations = [seconds_from_alignment_value(float(v)) for v in durations]
        ends = [start + duration for start, duration in zip(starts, durations)]
    else:
        ends = starts[1:] + [starts[-1] + 0.08]

    words: list[dict[str, Any]] = []
    current: list[str] = []
    word_start: float | None = None
    word_end: float | None = None

    for char, start, end in zip(chars, starts, ends):
        if str(char).isspace():
            if current and word_start is not None and word_end is not None:
                words.append({"word": "".join(current), "startSec": round(word_start, 3), "endSec": round(word_end, 3)})
            current = []
            word_start = None
            word_end = None
            continue
        if word_start is None:
            word_start = start
        current.append(str(char))
        word_end = end

    if current and word_start is not None and word_end is not None:
        words.append({"word": "".join(current), "startSec": round(word_start, 3), "endSec": round(word_end, 3)})

    return {"words": words, "raw": alignment}


def generate_voice(args: argparse.Namespace) -> None:
    load_env()
    require_creative_gate_for_paid_step(args.run_id, args.allow_unapproved_creative)
    text = read_text_arg(args)
    output = Path(args.out).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    voice_id = args.voice_id or abby_voice_id()
    model_id = args.model_id or os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": args.stability,
            "similarity_boost": args.similarity,
            "style": args.style,
            "use_speaker_boost": True,
        },
    }
    if args.speed:
        payload["voice_settings"]["speed"] = args.speed
    response = requests.post(
        url,
        headers={"xi-api-key": elevenlabs_key(), "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    if not response.ok:
        raise SystemExit(f"ElevenLabs voice generation failed: {response.status_code} {response.text[:500]}")
    data = response.json()
    audio_base64 = data.get("audio_base64")
    if not audio_base64:
        raise SystemExit("ElevenLabs response did not include audio_base64.")
    output.write_bytes(base64.b64decode(audio_base64))
    alignment_path = output.with_suffix(output.suffix + ".alignment.json")
    alignment_path.write_text(json.dumps(normalize_alignment(data), indent=2), encoding="utf-8")

    if args.run_id:
        conn = db()
        get_run(conn, args.run_id)
        update_run(conn, args.run_id, status="VOICED", audio_path=str(output), alignment_path=str(alignment_path))
        log_event(conn, args.run_id, "voiced", {"audioPath": str(output), "alignmentPath": str(alignment_path), "voiceId": voice_id})
        conn.commit()

    emit({"status": "VOICED", "voiceId": voice_id, "audio": str(output), "alignment": str(alignment_path)})


def gemini_key() -> str:
    key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not key:
        raise SystemExit("GOOGLE_API_KEY or GEMINI_API_KEY is missing. Add it to marketing_agent/.env.")
    return key


def generate_veo(args: argparse.Namespace) -> None:
    load_env()
    require_creative_gate_for_paid_step(args.run_id, args.allow_unapproved_creative)
    prompt = read_text_arg(args)
    output = Path(args.out).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    model = args.model or os.getenv("GEMINI_VEO_MODEL", DEFAULT_VEO_MODEL)
    first_frame = Path(args.first_frame).resolve() if args.first_frame else None
    reference_images = [Path(path).resolve() for path in (args.reference_image or [])]
    if reference_images and "lite" in model:
        model = os.getenv("GEMINI_VEO_REFERENCE_MODEL", "veo-3.1-generate-preview")
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    instance: dict[str, Any] = {"prompt": prompt}
    if first_frame:
        if not first_frame.exists():
            raise SystemExit(f"First-frame image not found: {first_frame}")
        mime_type = mimetypes.guess_type(first_frame.name)[0] or "image/png"
        instance["image"] = {
            "mimeType": mime_type,
            "bytesBase64Encoded": base64.b64encode(first_frame.read_bytes()).decode("ascii"),
        }
    if reference_images:
        refs: list[dict[str, Any]] = []
        for path in reference_images[:3]:
            if not path.exists():
                raise SystemExit(f"Reference image not found: {path}")
            mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
            refs.append(
                {
                    "image": {
                        "mimeType": mime_type,
                        "bytesBase64Encoded": base64.b64encode(path.read_bytes()).decode("ascii"),
                    },
                    "referenceType": args.reference_type,
                }
            )
        instance["referenceImages"] = refs
    request_body: dict[str, Any] = {
        "instances": [instance],
        "parameters": {"aspectRatio": args.aspect_ratio, "durationSeconds": 8},
    }
    resolution = args.resolution or os.getenv("GEMINI_VEO_RESOLUTION", "").strip()
    if resolution:
        request_body["parameters"]["resolution"] = resolution
    if reference_images:
        request_body["parameters"]["personGeneration"] = "allow_adult"
    if args.dry_run:
        safe_request = json.loads(json.dumps(request_body))
        if "image" in safe_request["instances"][0]:
            data = safe_request["instances"][0]["image"].get("bytesBase64Encoded", "")
            safe_request["instances"][0]["image"]["bytesBase64Encoded"] = f"<base64:{len(data)} chars>"
        for ref in safe_request["instances"][0].get("referenceImages", []):
            data = ref.get("image", {}).get("bytesBase64Encoded", "")
            ref["image"]["bytesBase64Encoded"] = f"<base64:{len(data)} chars>"
        emit({"dryRun": True, "model": model, "request": safe_request, "out": str(output)})
        return

    response = requests.post(
        f"{base_url}/models/{model}:predictLongRunning",
        headers={"x-goog-api-key": gemini_key(), "Content-Type": "application/json"},
        json=request_body,
        timeout=60,
    )
    if not response.ok:
        raise SystemExit(f"Veo request failed: {response.status_code} {response.text[:500]}")
    operation_name = response.json().get("name")
    if not operation_name:
        raise SystemExit(f"Veo response did not include operation name: {response.text[:500]}")

    deadline = time.time() + args.timeout_sec
    status: dict[str, Any] = {}
    while time.time() < deadline:
        status_response = requests.get(
            f"{base_url}/{operation_name}",
            headers={"x-goog-api-key": gemini_key()},
            timeout=60,
        )
        if not status_response.ok:
            raise SystemExit(f"Veo polling failed: {status_response.status_code} {status_response.text[:500]}")
        status = status_response.json()
        if status.get("done"):
            break
        time.sleep(args.poll_sec)
    if not status.get("done"):
        raise SystemExit(f"Veo generation timed out after {args.timeout_sec}s: {operation_name}")

    try:
        uri = status["response"]["generateVideoResponse"]["generatedSamples"][0]["video"]["uri"]
    except (KeyError, IndexError, TypeError) as exc:
        raise SystemExit(f"Veo operation completed without a video URI: {json.dumps(status)[:1000]}") from exc

    download = requests.get(uri, headers={"x-goog-api-key": gemini_key()}, timeout=180)
    if not download.ok:
        raise SystemExit(f"Veo download failed: {download.status_code} {download.text[:500]}")
    output.write_bytes(download.content)

    if args.run_id:
        conn = db()
        get_run(conn, args.run_id)
        metadata = json.loads(get_run(conn, args.run_id)["metadata_json"] or "{}")
        metadata.setdefault("veoClips", []).append({"path": str(output), "model": model, "prompt": prompt[:500]})
        update_run(conn, args.run_id, status="VIDEO_GENERATED", metadata_json=json.dumps(metadata))
        log_event(conn, args.run_id, "veo_generated", {"videoPath": str(output), "model": model})
        conn.commit()

    emit({"status": "VIDEO_GENERATED", "video": str(output), "operation": operation_name})


def _omni_video_uri(payload: dict[str, Any]) -> str | None:
    output_video = payload.get("output_video") or payload.get("outputVideo") or {}
    uri = output_video.get("uri")
    if uri:
        return str(uri)
    for step in payload.get("steps", []):
        for item in step.get("content", []):
            if item.get("type") == "video" and item.get("uri"):
                return str(item["uri"])
    return None


def _omni_video_data(payload: dict[str, Any]) -> str | None:
    output_video = payload.get("output_video") or payload.get("outputVideo") or {}
    data = output_video.get("data")
    if data:
        return str(data)
    for step in payload.get("steps", []):
        for item in step.get("content", []):
            if item.get("type") == "video" and item.get("data"):
                return str(item["data"])
    return None


def generate_omni_video(args: argparse.Namespace) -> None:
    load_env()
    require_creative_gate_for_paid_step(args.run_id, args.allow_unapproved_creative)
    prompt = read_text_arg(args)
    output = Path(args.out).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    model = args.model or os.getenv("GEMINI_OMNI_MODEL", "gemini-omni-flash-preview")
    reference_images = [Path(path).resolve() for path in (args.reference_image or [])]
    if not reference_images:
        raise SystemExit("At least one --reference-image is required for the Omni reference-video path.")

    input_parts: list[dict[str, Any]] = []
    for path in reference_images[:3]:
        if not path.exists():
            raise SystemExit(f"Reference image not found: {path}")
        mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
        input_parts.append(
            {
                "type": "image",
                "data": base64.b64encode(path.read_bytes()).decode("ascii"),
                "mime_type": mime_type,
            }
        )
    input_parts.append({"type": "text", "text": prompt})

    request_body: dict[str, Any] = {
        "model": model,
        "input": input_parts,
        "response_format": {
            "type": "video",
            "aspect_ratio": args.aspect_ratio,
            "delivery": "uri",
        },
        "generation_config": {
            "video_config": {
                "task": args.task,
            }
        },
    }
    if args.dry_run:
        safe_request = json.loads(json.dumps(request_body))
        for part in safe_request["input"]:
            if part.get("type") == "image":
                data = part.get("data", "")
                part["data"] = f"<base64:{len(data)} chars>"
        emit({"dryRun": True, "model": model, "request": safe_request, "out": str(output)})
        return

    key = gemini_key()
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json=request_body,
        timeout=args.timeout_sec,
    )
    if not response.ok:
        raise SystemExit(f"Gemini Omni request failed: {response.status_code} {response.text[:1000]}")
    payload = response.json()

    data = _omni_video_data(payload)
    if data:
        output.write_bytes(base64.b64decode(data))
    else:
        uri = _omni_video_uri(payload)
        if not uri:
            raise SystemExit(f"Gemini Omni response did not include video data or URI: {json.dumps(payload)[:1200]}")
        if uri.startswith("files/"):
            file_id = uri.split("/", 1)[1].split(":", 1)[0]
            deadline = time.time() + args.timeout_sec
            while time.time() < deadline:
                status_response = requests.get(
                    f"https://generativelanguage.googleapis.com/v1beta/files/{file_id}",
                    headers={"x-goog-api-key": key},
                    timeout=60,
                )
                if not status_response.ok:
                    raise SystemExit(
                        f"Gemini Omni file status failed: {status_response.status_code} {status_response.text[:500]}"
                    )
                state = str(status_response.json().get("state", "")).upper()
                if state == "ACTIVE":
                    break
                if state == "FAILED":
                    raise SystemExit(f"Gemini Omni file processing failed: {status_response.text[:1000]}")
                time.sleep(args.poll_sec)
            else:
                raise SystemExit(f"Gemini Omni file processing timed out after {args.timeout_sec}s: {uri}")
            download_url = f"https://generativelanguage.googleapis.com/v1beta/files/{file_id}:download?alt=media"
        else:
            download_url = uri
        download = requests.get(download_url, headers={"x-goog-api-key": key}, timeout=180)
        if not download.ok:
            raise SystemExit(f"Gemini Omni download failed: {download.status_code} {download.text[:500]}")
        output.write_bytes(download.content)

    if args.run_id:
        conn = db()
        get_run(conn, args.run_id)
        metadata = json.loads(get_run(conn, args.run_id)["metadata_json"] or "{}")
        metadata.setdefault("geminiClips", []).append({"path": str(output), "model": model, "prompt": prompt[:500]})
        update_run(conn, args.run_id, status="VIDEO_GENERATED", metadata_json=json.dumps(metadata))
        log_event(conn, args.run_id, "gemini_omni_generated", {"videoPath": str(output), "model": model})
        conn.commit()
    emit({"status": "GEMINI_OMNI_GENERATED", "video": str(output), "model": model})


@lru_cache(maxsize=64)
def font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / name,
        Path("C:/Windows/Fonts") / name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def wrapped_lines(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.ImageFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=font_obj)[2] <= width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int, int], outline: tuple[int, int, int, int] | None = None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_resume_base(draw: ImageDraw.ImageDraw) -> dict[str, tuple[int, int, int, int]]:
    paper = (152, 300, 928, 1420)
    shadow = (paper[0] + 16, paper[1] + 18, paper[2] + 16, paper[3] + 18)
    rounded_rect(draw, shadow, 28, (0, 0, 0, 72))
    rounded_rect(draw, (paper[0] - 18, paper[1] - 22, paper[2] + 18, paper[3] + 22), 34, (18, 24, 31, 220), (255, 255, 255, 48), 2)
    rounded_rect(draw, paper, 18, (252, 252, 247, 248), (20, 27, 38, 70), 2)

    title = font("segoeuib.ttf", 36)
    subtitle = font("segoeui.ttf", 15)
    section = font("segoeuib.ttf", 16)
    role = font("segoeuib.ttf", 20)
    body = font("segoeui.ttf", 18)
    small = font("segoeui.ttf", 15)
    tiny = font("segoeui.ttf", 14)
    mono = font("consola.ttf", 14)

    x = paper[0] + 56
    y = paper[1] + 48
    draw.text((x, y), "SHAWN MARTIN", font=title, fill=(15, 23, 42, 255))
    draw.text((x, y + 44), "Network Support Specialist  |  Austin, TX  |  shawn.m@example.com  |  linkedin.com/in/shawnmartin", font=subtitle, fill=(72, 84, 104, 255))
    draw.line((x, y + 78, paper[2] - 56, y + 78), fill=(20, 27, 38, 80), width=2)

    y += 105
    draw.text((x, y), "PROFESSIONAL SUMMARY", font=section, fill=(9, 102, 93, 255))
    y += 27
    summary = "Network support specialist with 4+ years supporting hybrid offices, user access, endpoint deployment, and recurring incident triage across healthcare and logistics teams."
    for line in wrapped_lines(draw, summary, small, paper[2] - 112 - x):
        draw.text((x, y), line, font=small, fill=(31, 41, 55, 255))
        y += 22

    y += 20
    draw.text((x, y), "TECHNICAL SKILLS", font=section, fill=(9, 102, 93, 255))
    y += 28
    skill_rows = [
        ("Networking", "TCP/IP, DNS, DHCP, VLANs, VPN access, Wi-Fi troubleshooting"),
        ("Platforms", "Windows 10/11, Microsoft 365, Azure AD, ServiceNow, Intune, Jamf"),
        ("Hardware", "Cisco switches, Meraki APs, laptops, printers, conference rooms"),
        ("Reporting", "ticket trends, root-cause notes, knowledge base articles, SLA follow-up"),
    ]
    for label, value in skill_rows:
        draw.text((x, y), label + ":", font=font("segoeuib.ttf", 14), fill=(15, 23, 42, 255))
        draw.text((x + 118, y), value, font=tiny, fill=(55, 65, 81, 255))
        y += 22

    y += 20
    draw.text((x, y), "EXPERIENCE", font=section, fill=(9, 102, 93, 255))
    y += 30
    draw.text((x, y), "IT Support Analyst  |  Northstar Health Systems", font=role, fill=(15, 23, 42, 255))
    draw.text((paper[2] - 230, y + 3), "2022 - Present", font=small, fill=(72, 84, 104, 255))
    y += 36

    bullets = [
        "Handled network issues for internal users across four office locations.",
        "Closed 35-50 weekly tickets covering VPN access, device setup, account lockouts, printer failures, and conference-room support.",
        "Partnered with infrastructure team to document recurring Wi-Fi drops and reduce repeat tickets by 18% over two quarters.",
        "Configured onboarding access for 120+ employees across Microsoft 365, Azure AD groups, and ServiceNow requests.",
        "Updated 24 knowledge-base articles so night-shift technicians could resolve repeat VPN and printer issues without escalation.",
    ]
    boxes: dict[str, tuple[int, int, int, int]] = {}
    for idx, bullet in enumerate(bullets):
        bullet_y = y
        draw.text((x + 4, bullet_y + 2), u"\u2022", font=body, fill=(15, 23, 42, 255))
        line_x = x + 34
        lines = wrapped_lines(draw, bullet, body, paper[2] - 92 - line_x)
        for line_index, line in enumerate(lines):
            draw.text((line_x, bullet_y + line_index * 25), line, font=body, fill=(15, 23, 42, 255))
        box_h = max(30, len(lines) * 25)
        if idx == 0:
            boxes["weak_bullet"] = (line_x - 10, bullet_y - 8, paper[2] - 66, bullet_y + box_h + 6)
        y += box_h + 15

    y += 10
    draw.text((x, y), "Desktop Support Technician  |  Lakeside Logistics", font=role, fill=(15, 23, 42, 255))
    draw.text((paper[2] - 230, y + 3), "2020 - 2022", font=small, fill=(72, 84, 104, 255))
    y += 34
    earlier_bullets = [
        "Imaged and deployed 180+ Windows laptops during warehouse device refresh.",
        "Tracked recurring scanner, printer, and Wi-Fi issues in ServiceNow for operations managers.",
    ]
    for bullet in earlier_bullets:
        draw.text((x + 4, y + 2), u"\u2022", font=body, fill=(15, 23, 42, 255))
        for line in wrapped_lines(draw, bullet, small, paper[2] - 145 - x):
            draw.text((x + 34, y), line, font=small, fill=(31, 41, 55, 255))
            y += 22
        y += 8

    y += 14
    draw.text((x, y), "NETWORK PROJECTS", font=section, fill=(9, 102, 93, 255))
    y += 28
    projects = [
        "VPN migration support: validated user access, documented common failures, and escalated firewall-rule gaps.",
        "Office refresh: imaged 80+ laptops, mapped printers, and tested switch ports before go-live.",
    ]
    for project in projects:
        draw.text((x + 4, y + 2), u"\u2022", font=body, fill=(15, 23, 42, 255))
        for line in wrapped_lines(draw, project, small, paper[2] - 145 - x):
            draw.text((x + 34, y), line, font=small, fill=(31, 41, 55, 255))
            y += 22
        y += 8

    y += 10
    draw.text((x, y), "CERTIFICATIONS", font=section, fill=(9, 102, 93, 255))
    y += 28
    draw.text((x, y), "CompTIA Network+ (2023)  |  Google IT Support Certificate  |  Cisco Networking Basics", font=small, fill=(31, 41, 55, 255))

    y += 40
    chip_x = paper[0] + 56
    for skill in ["Windows", "Azure AD", "ServiceNow", "VPN", "Cisco", "Meraki"]:
        tw = draw.textbbox((0, 0), skill, font=mono)[2]
        rounded_rect(draw, (chip_x, y, chip_x + tw + 28, y + 32), 16, (235, 245, 244, 255), (9, 102, 93, 90), 1)
        draw.text((chip_x + 14, y + 7), skill, font=mono, fill=(9, 102, 93, 255))
        chip_x += tw + 38
    boxes["paper"] = paper
    return boxes


def draw_top_cleanup(draw: ImageDraw.ImageDraw) -> None:
    for y in range(0, 130):
        alpha = max(0, int(220 * (1 - (y / 130))))
        draw.rectangle((0, y, OVERLAY_CANVAS[0], y + 1), fill=(28, 18, 10, alpha))


def draw_keyword_chips(draw: ImageDraw.ImageDraw, chips: list[str], x: int, y: int) -> None:
    chip_font = font("segoeuib.ttf", 24)
    for chip in chips:
        bbox = draw.textbbox((0, 0), chip, font=chip_font)
        w = bbox[2] - bbox[0] + 42
        rounded_rect(draw, (x, y, x + w, y + 52), 24, (14, 165, 145, 238), (255, 255, 255, 130), 2)
        draw.text((x + 21, y + 12), chip, font=chip_font, fill=(255, 255, 255, 255))
        y += 66


def draw_small_caption(draw: ImageDraw.ImageDraw, text: str) -> None:
    caption_font = font("segoeuib.ttf", 22)
    lines = wrapped_lines(draw, text, caption_font, 760)
    line_h = 30
    h = line_h * len(lines) + 30
    box = (162, 1590, 918, 1590 + h)
    rounded_rect(draw, box, 18, (7, 11, 18, 150), (255, 255, 255, 55), 1)
    y = box[1] + 16
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=caption_font)
        draw.text(((1080 - (bbox[2] - bbox[0])) / 2, y), line, font=caption_font, fill=(255, 255, 255, 224))
        y += line_h


def generate_overlays(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    title_font = font("segoeuib.ttf", 46)
    note_font = font("segoeuib.ttf", 30)
    body_font = font("segoeui.ttf", 25)

    weak_text = "Handled network issues"
    rewrite = "Resolved 40+ weekly network incidents across Cisco switches, VPN access, and firewall changes."

    outputs: list[str] = []
    for index in range(1, 5):
        image = Image.new("RGBA", OVERLAY_CANVAS, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw_top_cleanup(draw)
        boxes = draw_resume_base(draw)
        weak = boxes["weak_bullet"]
        paper = boxes["paper"]

        if index >= 2:
            draw.rounded_rectangle(weak, radius=12, outline=(239, 68, 68, 235), width=7)
            draw.line((weak[0] + 18, weak[3] - 18, weak[2] - 18, weak[3] - 18), fill=(239, 68, 68, 235), width=6)
            if index < 4:
                draw.text((weak[0], weak[1] - 44), "too vague", font=note_font, fill=(239, 68, 68, 255))

        if index >= 3:
            draw_keyword_chips(draw, ["Cisco", "VPN", "Firewall", "Incidents"], 108, 1080)
            draw_small_caption(draw, "Use the job's language.")

        if index >= 4:
            cover = (paper[0] + 40, 830, paper[2] - 40, 1114)
            rounded_rect(draw, cover, 18, (255, 255, 255, 248), (20, 27, 38, 72), 2)
            draw.text((cover[0] + 24, cover[1] + 20), "Replace this:", font=note_font, fill=(239, 68, 68, 255))
            draw.text((cover[0] + 24, cover[1] + 64), weak_text, font=body_font, fill=(15, 23, 42, 255))
            draw.line((cover[0] + 24, cover[1] + 84, cover[0] + 350, cover[1] + 84), fill=(239, 68, 68, 230), width=5)
            draw.text((cover[0] + 24, cover[1] + 112), "With this:", font=note_font, fill=(9, 102, 93, 255))
            y = cover[1] + 154
            for line in wrapped_lines(draw, rewrite, body_font, cover[2] - cover[0] - 48):
                draw.text((cover[0] + 24, y), line, font=body_font, fill=(15, 23, 42, 255))
                y += 34
            draw_small_caption(draw, "Now the proof is searchable.")
        elif index == 1:
            draw_small_caption(draw, "One weak line can bury the resume.")
        elif index == 2:
            draw_small_caption(draw, "This tells a recruiter almost nothing.")

        out = work_dir / f"overlay{index:02d}.png"
        image.save(out)
        outputs.append(str(out))

    if args.run_id:
        conn = db()
        get_run(conn, args.run_id)
        metadata = json.loads(get_run(conn, args.run_id)["metadata_json"] or "{}")
        metadata["resumeOverlays"] = outputs
        update_run(conn, args.run_id, metadata_json=json.dumps(metadata))
        log_event(conn, args.run_id, "resume_overlays_generated", {"overlays": outputs})
        conn.commit()

    emit({"status": "OVERLAYS_GENERATED", "overlays": outputs})


def draw_progress_line(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], progress: float, fill: tuple[int, int, int, int], width: int) -> None:
    progress = max(0.0, min(1.0, progress))
    x = start[0] + (end[0] - start[0]) * progress
    y = start[1] + (end[1] - start[1]) * progress
    draw.line((start[0], start[1], x, y), fill=fill, width=width)


def draw_progress_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], progress: float, fill: tuple[int, int, int, int], width: int = 6) -> None:
    progress = max(0.0, min(1.0, progress))
    x1, y1, x2, y2 = box
    segments = [
        ((x1, y1), (x2, y1)),
        ((x2, y1), (x2, y2)),
        ((x2, y2), (x1, y2)),
        ((x1, y2), (x1, y1)),
    ]
    remaining = progress * 4
    for start, end in segments:
        if remaining <= 0:
            break
        draw_progress_line(draw, start, end, min(1.0, remaining), fill, width)
        remaining -= 1


def draw_badge(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, fill: tuple[int, int, int, int], text_fill: tuple[int, int, int, int]) -> None:
    badge_font = font("segoeuib.ttf", 23)
    bbox = draw.textbbox((0, 0), text, font=badge_font)
    width = bbox[2] - bbox[0] + 28
    height = bbox[3] - bbox[1] + 18
    rounded_rect(draw, (x, y, x + width, y + height), 14, fill, (255, 255, 255, 80), 1)
    draw.text((x + 14, y + 8), text, font=badge_font, fill=text_fill)


def load_resume_brief(work_dir: Path) -> dict[str, Any]:
    brief_path = work_dir / "resume_brief.json"
    if not brief_path.exists():
        return {}
    try:
        return json.loads(brief_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid resume_brief.json: {exc}") from exc


def brief_list(brief: dict[str, Any], key: str, fallback: list[str]) -> list[str]:
    value = brief.get(key)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return fallback


def draw_live_edit_resume_base(draw: ImageDraw.ImageDraw, brief: dict[str, Any] | None = None, updated: bool = False, typed_rewrite: str = "") -> dict[str, tuple[int, int, int, int]]:
    brief = brief or {}
    paper = (132, 270, 948, 1468)
    shadow = (paper[0] + 16, paper[1] + 18, paper[2] + 16, paper[3] + 18)
    rounded_rect(draw, shadow, 28, (0, 0, 0, 78))
    rounded_rect(draw, (paper[0] - 18, paper[1] - 22, paper[2] + 18, paper[3] + 22), 34, (18, 24, 31, 220), (255, 255, 255, 48), 2)
    rounded_rect(draw, paper, 18, (252, 252, 248, 250), (20, 27, 38, 70), 2)

    title = font("segoeuib.ttf", 36)
    subtitle = font("segoeui.ttf", 17)
    section = font("segoeuib.ttf", 16)
    role = font("segoeuib.ttf", 20)
    body = font("segoeui.ttf", 18)
    small = font("segoeui.ttf", 15)
    tiny = font("segoeui.ttf", 14)
    mono = font("consola.ttf", 14)

    x = paper[0] + 56
    y = paper[1] + 44
    candidate_name = str(brief.get("candidateName", "Maya Rivera"))
    target_role = str(brief.get("targetRole", "Customer Success Manager"))
    location = str(brief.get("location", "Denver, CO"))
    email = str(brief.get("email", "maya.r@example.com"))
    linkedin = str(brief.get("linkedin", "linkedin.com/in/mayarivera"))
    summary = str(
        brief.get(
            "summary",
            "Customer success manager with 5+ years supporting B2B SaaS onboarding, renewal risk reviews, user adoption, and executive account updates.",
        )
    )
    skills = brief_list(brief, "skills", ["Customer Success", "Salesforce", "Gainsight", "Renewals", "Onboarding"])
    target_language = brief_list(brief, "targetJobLanguage", ["Salesforce", "Gainsight", "Renewals", "Churn Risk"])
    hidden_proof = str(brief.get("hiddenProof", "42 accounts, $1.2M protected, Gainsight churn-risk notes."))
    current_role = str(brief.get("currentRole", target_role))
    current_company = str(brief.get("currentCompany", "Northline Software"))
    current_dates = str(brief.get("currentDates", "2022 - Present"))
    previous_role = str(brief.get("previousRole", "Customer Success Associate"))
    previous_company = str(brief.get("previousCompany", "Brightpath Learning"))
    previous_dates = str(brief.get("previousDates", "2020 - 2022"))
    weak_bullet = str(brief.get("weakBullet", "Helped customers with onboarding and renewals."))
    strong_bullet = str(
        brief.get(
            "rewrite",
            "Led onboarding for 42 B2B accounts, flagged churn risk in Gainsight, and protected $1.2M in annual renewals.",
        )
    )
    experience_bullets = brief_list(
        brief,
        "experienceBullets",
        [
            "Managed a book of 68 SMB and mid-market accounts with weekly usage reviews, renewal notes, and escalation follow-up.",
            "Built onboarding checklists that reduced first-value time from 21 days to 14 days across new customer cohorts.",
            "Partnered with sales on expansion handoffs and documented customer health trends in Salesforce.",
        ],
    )
    previous_bullets = brief_list(
        brief,
        "previousBullets",
        [
            "Answered implementation questions for 90+ customers using Zendesk and product usage reports.",
            "Created renewal briefing notes for account executives before budget meetings.",
        ],
    )
    education = str(brief.get("education", "B.A. Communication, University of Colorado"))
    certifications = brief_list(brief, "certifications", ["Certified Customer Success Manager"])

    draw.text((x, y), candidate_name.upper(), font=title, fill=(15, 23, 42, 255))
    draw.text((x, y + 44), f"{target_role}  |  {location}  |  {email}  |  {linkedin}", font=subtitle, fill=(72, 84, 104, 255))
    draw.line((x, y + 78, paper[2] - 56, y + 78), fill=(20, 27, 38, 80), width=2)

    y += 105
    draw.text((x, y), "PROFESSIONAL SUMMARY", font=section, fill=(9, 102, 93, 255))
    y += 27
    for line in wrapped_lines(draw, summary, small, paper[2] - 112 - x):
        draw.text((x, y), line, font=small, fill=(31, 41, 55, 255))
        y += 22

    y += 18
    draw.text((x, y), "CORE SKILLS", font=section, fill=(9, 102, 93, 255))
    y += 28
    skill_rows = [
        ("Target role", ", ".join(target_language[:6])),
        ("Tools", ", ".join(skills[:7])),
        ("Proof notes", hidden_proof),
    ]
    for label, value in skill_rows:
        draw.text((x, y), label + ":", font=font("segoeuib.ttf", 14), fill=(15, 23, 42, 255))
        draw.text((x + 136, y), value, font=tiny, fill=(55, 65, 81, 255))
        y += 22

    y += 18
    draw.text((x, y), "EXPERIENCE", font=section, fill=(9, 102, 93, 255))
    y += 30
    draw.text((x, y), f"{current_role}  |  {current_company}", font=role, fill=(15, 23, 42, 255))
    draw.text((paper[2] - 230, y + 3), current_dates, font=small, fill=(72, 84, 104, 255))
    y += 36

    bullets = [strong_bullet if updated else weak_bullet, *experience_bullets]
    boxes: dict[str, tuple[int, int, int, int]] = {}
    for idx, bullet in enumerate(bullets):
        bullet_y = y
        draw.text((x + 4, bullet_y + 2), u"\u2022", font=body, fill=(15, 23, 42, 255))
        line_x = x + 34
        if idx == 0 and typed_rewrite:
            rounded_rect(draw, (line_x - 8, bullet_y - 8, paper[2] - 62, bullet_y + 72), 12, (255, 255, 255, 250), (20, 27, 38, 45), 1)
            typed_lines = wrapped_lines(draw, typed_rewrite, body, paper[2] - 92 - line_x)
            for line_index, line in enumerate(typed_lines[:3]):
                draw.text((line_x, bullet_y + line_index * 25), line, font=body, fill=(15, 23, 42, 255))
            box_h = max(126, len(typed_lines[:3]) * 30 + 28)
            boxes["weak_bullet"] = (line_x - 10, bullet_y - 8, paper[2] - 66, bullet_y + box_h)
            boxes["rewrite_bullet"] = (line_x - 10, bullet_y - 8, paper[2] - 66, bullet_y + box_h)
            y += box_h + 24
            continue
        lines = wrapped_lines(draw, bullet, body, paper[2] - 92 - line_x)
        for line_index, line in enumerate(lines):
            draw.text((line_x, bullet_y + line_index * 25), line, font=body, fill=(15, 23, 42, 255))
        box_h = max(30, len(lines) * 25)
        if idx == 0:
            extra = 18 if updated else 6
            boxes["weak_bullet"] = (line_x - 10, bullet_y - 8, paper[2] - 66, bullet_y + box_h + extra)
        y += box_h + (30 if idx == 0 and updated else 15)

    y += 12
    draw.text((x, y), f"{previous_role}  |  {previous_company}", font=role, fill=(15, 23, 42, 255))
    draw.text((paper[2] - 230, y + 3), previous_dates, font=small, fill=(72, 84, 104, 255))
    y += 34
    for bullet in previous_bullets[:3]:
        draw.text((x + 4, y + 2), u"\u2022", font=body, fill=(15, 23, 42, 255))
        for line in wrapped_lines(draw, bullet, small, paper[2] - 145 - x):
            draw.text((x + 34, y), line, font=small, fill=(31, 41, 55, 255))
            y += 22
        y += 8

    y += 14
    draw.text((x, y), "PROJECTS", font=section, fill=(9, 102, 93, 255))
    y += 28
    projects = [
        f"Target-job evidence: {hidden_proof}",
        f"Search terms to surface: {', '.join(target_language[:5])}",
    ]
    for project in projects:
        draw.text((x + 4, y + 2), u"\u2022", font=body, fill=(15, 23, 42, 255))
        for line in wrapped_lines(draw, project, small, paper[2] - 145 - x):
            draw.text((x + 34, y), line, font=small, fill=(31, 41, 55, 255))
            y += 22
        y += 8

    y += 8
    draw.text((x, y), "EDUCATION", font=section, fill=(9, 102, 93, 255))
    y += 28
    cert_text = " | ".join([education, *certifications[:2]])
    for line in wrapped_lines(draw, cert_text, small, paper[2] - 112 - x):
        draw.text((x, y), line, font=small, fill=(31, 41, 55, 255))
        y += 22

    y += 38
    chip_x = paper[0] + 56
    for skill in [*target_language[:4], *skills[:2]]:
        tw = draw.textbbox((0, 0), skill, font=mono)[2]
        rounded_rect(draw, (chip_x, y, chip_x + tw + 28, y + 32), 16, (235, 245, 244, 255), (9, 102, 93, 90), 1)
        draw.text((chip_x + 14, y + 7), skill, font=mono, fill=(9, 102, 93, 255))
        chip_x += tw + 38
        if chip_x > paper[2] - 150:
            chip_x = paper[0] + 56
            y += 38

    boxes["paper"] = paper
    boxes["strong_bullet_text"] = (0, 0, 0, 0)
    return boxes


def draw_score_receipt(draw: ImageDraw.ImageDraw, brief: dict[str, Any], progress: float) -> None:
    receipt_rows = brief.get("scoreReceipt")
    if not isinstance(receipt_rows, list) or not receipt_rows:
        receipt_rows = [
            {"label": "Keyword match", "after": "8/10", "proof": "role language added"},
            {"label": "Tool match", "after": "8/10", "proof": "tools named"},
            {"label": "Metric proof", "after": "9/10", "proof": "specific number added"},
            {"label": "Outcome clarity", "after": "8/10", "proof": "impact explained"},
        ]
    score_before = int(brief.get("scoreBefore", 41))
    score_after = int(brief.get("scoreAfter", 87))
    title_font = font("segoeuib.ttf", 28)
    row_font = font("segoeuib.ttf", 19)
    small_font = font("segoeui.ttf", 16)
    score_font = font("segoeuib.ttf", 48)
    box = (206, 1000, 874, 1460)
    rounded_rect(draw, box, 24, (255, 255, 255, 248), (20, 27, 38, 88), 2)
    draw.text((box[0] + 32, box[1] + 26), "SCORE RECEIPT", font=title_font, fill=(15, 23, 42, 255))

    y = box[1] + 78
    visible_rows = min(len(receipt_rows), max(1, int(progress * (len(receipt_rows) + 1))))
    for row in receipt_rows[:visible_rows]:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label", "Score factor"))
        after = str(row.get("after", "8/10"))
        proof = str(row.get("proof", "proof added"))
        row_box = (box[0] + 30, y, box[2] - 30, y + 56)
        rounded_rect(draw, row_box, 14, (241, 245, 249, 250), (148, 163, 184, 120), 1)
        draw.text((row_box[0] + 18, y + 12), label, font=row_font, fill=(51, 65, 85, 255))
        draw.text((row_box[0] + 230, y + 12), proof, font=small_font, fill=(15, 23, 42, 255))
        draw.text((row_box[2] - 72, y + 12), after, font=row_font, fill=(9, 102, 93, 255))
        y += 62

    if progress > 0.72:
        score_box = (box[2] - 252, y + 8, box[2] - 30, y + 62)
        rounded_rect(draw, score_box, 18, (13, 148, 136, 248), (255, 255, 255, 90), 2)
        draw.text((score_box[0] + 22, score_box[1] - 2), f"{score_before} -> {score_after}", font=score_font, fill=(255, 255, 255, 255))


def draw_live_edit_frame(draw: ImageDraw.ImageDraw, stage: int, progress: float, brief: dict[str, Any] | None = None) -> None:
    brief = brief or {}
    draw_top_cleanup(draw)
    rewrite = str(
        brief.get(
            "rewrite",
            "Led onboarding for 42 B2B accounts, flagged churn risk in Gainsight, and protected $1.2M in annual renewals.",
        )
    )
    typed_rewrite = ""
    updated = stage >= 4
    if stage == 3:
        type_progress = max(0.0, min(1.0, (progress - 0.28) / 0.62))
        typed_rewrite = rewrite[: int(len(rewrite) * type_progress)]
    boxes = draw_live_edit_resume_base(draw, brief=brief, updated=updated, typed_rewrite=typed_rewrite)
    weak = boxes["weak_bullet"]

    small_note = font("segoeuib.ttf", 23)
    red = (239, 68, 68, 235)
    green = (14, 165, 145, 235)

    if stage == 1:
        draw_small_caption(draw, "Clean resume. Weak evidence.")
    elif stage == 2:
        draw_progress_rect(draw, weak, progress, red, width=7)
        if progress > 0.35:
            draw_badge(draw, "no proof", weak[2] - 142, weak[1] - 42, (127, 29, 29, 232), (255, 255, 255, 255))
        if progress > 0.65:
            draw_small_caption(draw, "No tool. No metric. No impact.")
    elif stage == 3:
        draw.rounded_rectangle(weak, radius=12, outline=green, width=6)
        draw_badge(draw, "typing proof", weak[2] - 198, weak[1] - 42, (6, 95, 70, 232), (255, 255, 255, 255))
        draw_small_caption(draw, "The vague line gets replaced with proof.")
    else:
        highlight = boxes["weak_bullet"]
        draw.rounded_rectangle(highlight, radius=14, outline=(14, 165, 145, 210), width=5)
        draw_badge(draw, "fixed with proof", highlight[2] - 220, highlight[1] - 42, (6, 95, 70, 232), (255, 255, 255, 255))
        draw_score_receipt(draw, brief, progress)
        draw_small_caption(draw, "Need yours fixed? Run the free Signal score before you apply.")


def voice_duration_sec(work_dir: Path, voice_name: str, fallback: float) -> float:
    voice_path = work_dir / voice_name
    if not voice_path.exists():
        return fallback
    try:
        ffprobe = find_exe("ffprobe")
        proc = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(voice_path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return max(0.4, float(proc.stdout.strip()))
    except Exception:
        try:
            ffmpeg = find_exe("ffmpeg")
            proc = subprocess.run(
                [ffmpeg, "-i", str(voice_path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
            if not match:
                return fallback
            hours, minutes, seconds = match.groups()
            duration = (int(hours) * 3600) + (int(minutes) * 60) + float(seconds)
            return max(0.4, duration)
        except Exception:
            return fallback


def generate_live_edit_overlays(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    brief = load_resume_brief(work_dir)
    fps = int(os.getenv("SIGNAL_OVERLAY_FPS", "12"))
    if fps < 8 or fps > 30:
        raise SystemExit("SIGNAL_OVERLAY_FPS must be between 8 and 30.")
    (work_dir / "overlay_fps.txt").write_text(str(fps), encoding="utf-8")
    defaults = [4.6, 5.4, 8.1, 5.4]
    voices = ["vo_hook.mp3", "vo_search.mp3", "vo_demo.mp3", "vo_cta.mp3"]
    outputs: list[str] = []

    for stage, (voice_name, fallback) in enumerate(zip(voices, defaults), start=1):
        duration = voice_duration_sec(work_dir, voice_name, fallback)
        frame_count = max(2, int(duration * fps))
        frame_dir = work_dir / f"overlay{stage:02d}_frames"
        if frame_dir.exists():
            shutil.rmtree(frame_dir)
        frame_dir.mkdir(parents=True, exist_ok=True)
        for frame in range(frame_count):
            progress = 1.0 if frame_count <= 1 else frame / (frame_count - 1)
            image = Image.new("RGBA", OVERLAY_CANVAS, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw_live_edit_frame(draw, stage, progress, brief)
            image.save(frame_dir / f"{frame:04d}.png")
        outputs.append(str(frame_dir))

    if args.run_id:
        conn = db()
        get_run(conn, args.run_id)
        metadata = json.loads(get_run(conn, args.run_id)["metadata_json"] or "{}")
        metadata["liveEditOverlayFrames"] = outputs
        update_run(conn, args.run_id, metadata_json=json.dumps(metadata))
        log_event(conn, args.run_id, "live_edit_overlays_generated", {"frameDirs": outputs})
        conn.commit()

    emit({"status": "LIVE_EDIT_OVERLAYS_GENERATED", "frameDirs": outputs})


def research_swipe(args: argparse.Namespace) -> None:
    urls: list[str] = []
    if args.urls:
        urls.extend(args.urls)
    if args.urls_file:
        urls.extend(
            line.strip()
            for line in Path(args.urls_file).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    urls = list(dict.fromkeys(urls))
    if len(urls) < args.min_sources:
        raise SystemExit(f"Need at least {args.min_sources} source URLs for research-swipe; got {len(urls)}.")

    if args.work_dir:
        work_dir = Path(args.work_dir).resolve()
        out_dir = work_dir / "research_swipe"
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_dir = MARKETING_DIR / "research" / "swipe_runs" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    captions_dir = out_dir / "captions"
    captions_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "seed_urls.txt").write_text("\n".join(urls) + "\n", encoding="utf-8")

    metadata_rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for url in urls:
        proc = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--skip-download", "--dump-json", "--no-warnings", url],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            failures.append({"url": url, "error": proc.stderr[-500:]})
            continue
        for line in proc.stdout.splitlines():
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            row = {
                "id": raw.get("id"),
                "title": raw.get("title"),
                "channel": raw.get("channel") or raw.get("uploader"),
                "duration": raw.get("duration"),
                "view_count": raw.get("view_count"),
                "like_count": raw.get("like_count"),
                "upload_date": raw.get("upload_date"),
                "webpage_url": raw.get("webpage_url") or url,
                "automatic_caption_langs": sorted((raw.get("automatic_captions") or {}).keys())[:25],
            }
            metadata_rows.append(row)
            break

        subprocess.run(
            [
                sys.executable,
                "-m",
                "yt_dlp",
                "--skip-download",
                "--write-auto-subs",
                "--sub-langs",
                "en.*",
                "--sub-format",
                "vtt",
                "-o",
                str(captions_dir / "%(id)s.%(ext)s"),
                url,
            ],
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    (out_dir / "metadata.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in metadata_rows),
        encoding="utf-8",
    )

    hook_rows: list[dict[str, Any]] = []
    for row in metadata_rows:
        video_id = row.get("id")
        if not video_id:
            continue
        candidates = sorted(captions_dir.glob(f"{video_id}.en*.vtt"))
        events = parse_vtt(candidates[0]) if candidates else []
        hook = clean_caption_text(" ".join(str(event["text"]) for event in events if float(event["startSec"]) < 8))
        first_20 = clean_caption_text(" ".join(str(event["text"]) for event in events if float(event["startSec"]) < 20))
        hook_rows.append(
            {
                "id": video_id,
                "title": row.get("title"),
                "channel": row.get("channel"),
                "url": row.get("webpage_url"),
                "duration": row.get("duration"),
                "views": row.get("view_count"),
                "hookFirst8Sec": hook[:320],
                "first20Sec": first_20[:700],
            }
        )
    (out_dir / "hooks.json").write_text(json.dumps(hook_rows, indent=2, ensure_ascii=True), encoding="utf-8")

    top_by_views = sorted(metadata_rows, key=lambda item: item.get("view_count") or 0, reverse=True)[:8]
    formats_md = [
        "# Research Swipe Summary",
        "",
        f"Generated: {utc_now()}",
        "",
        "## Sources",
        "",
    ]
    for row in top_by_views:
        formats_md.append(
            f"- {row.get('title')} | {row.get('channel')} | {row.get('duration')}s | views: {row.get('view_count')} | {row.get('webpage_url')}"
        )
    formats_md.extend(
        [
            "",
            "## Required Copy Patterns",
            "",
            "- Resume or job description visible immediately.",
            "- One specific weak line, not a generic resume lecture.",
            "- Natural reviewer language before product language.",
            "- The fix happens on screen before the score reveal.",
            "- Score receipt explains keyword/tool/metric/outcome improvement.",
            "",
            "## Avoid",
            "",
            "- Generated resume text in Veo/Flow footage.",
            "- Long ATS explanations.",
            "- Repeated generic hooks.",
            "- Score jumps without visible proof.",
        ]
    )
    (out_dir / "formats.md").write_text("\n".join(formats_md) + "\n", encoding="utf-8")

    blockers: list[str] = []
    if len(metadata_rows) < args.min_sources:
        blockers.append(f"only {len(metadata_rows)} metadata records collected; expected at least {args.min_sources}")
    if len(hook_rows) < max(3, args.min_sources // 2):
        blockers.append("not enough caption/hook rows collected")
    warnings = [f"{len(failures)} source URL(s) failed"] if failures else []
    report = {
        "passed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "sourceCount": len(metadata_rows),
        "hookCount": len(hook_rows),
        "outDir": str(out_dir),
        "failures": failures,
    }
    if args.work_dir:
        path = write_quality_gate(Path(args.work_dir).resolve(), "research_swipe", report, args.run_id)
        report["reportPath"] = str(path)
    emit(report)
    if blockers:
        raise SystemExit(1)


def read_spoken_script(work_dir: Path) -> str:
    voice_full = work_dir / "voice_full_script.txt"
    if voice_full.exists():
        text = voice_full.read_text(encoding="utf-8", errors="ignore").strip()
        if text:
            return text
    selected = selected_voice_script(work_dir)
    if selected:
        return selected
    voice_parts: list[str] = []
    preferred = ["vo_hook.txt", "vo_search.txt", "vo_demo.txt", "vo_cta.txt"]
    ordered_paths = [work_dir / name for name in preferred if (work_dir / name).exists()]
    ordered_paths.extend(path for path in sorted(work_dir.glob("vo_*.txt")) if path not in ordered_paths)
    for path in ordered_paths:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if text:
            voice_parts.append(text)
    if voice_parts:
        return " ".join(voice_parts)
    script_path = work_dir / "script.md"
    if script_path.exists():
        return markdown_to_plain(script_path.read_text(encoding="utf-8", errors="ignore"))
    return ""


def script_qa(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve()
    brief = load_resume_brief(work_dir)
    spoken = read_spoken_script(work_dir)
    plain = markdown_to_plain(spoken)
    lower = plain.lower()
    blockers: list[str] = []
    warnings: list[str] = []

    if not plain:
        blockers.append("no script.md or vo_*.txt text found")

    words = count_words(plain)
    if words > args.max_words:
        blockers.append(f"spoken script is {words} words; max for short is {args.max_words}")
    if words < args.min_words:
        blockers.append(f"spoken script is {words} words; minimum is {args.min_words}")

    banned_hits = [pattern for pattern in BANNED_SCRIPT_PATTERNS if re.search(pattern, lower, flags=re.I)]
    if banned_hits:
        blockers.append("banned AI/product language found: " + ", ".join(banned_hits))
    slop_hits = sorted(word for word in AI_SLOP_WORDS if word in lower)
    if slop_hits:
        warnings.append("corporate/AI-sounding words found: " + ", ".join(slop_hits))

    candidate = str(brief.get("candidateName", "")).strip()
    first_name = candidate.split()[0].lower() if candidate else ""
    target_role = str(brief.get("targetRole", "")).strip()
    weak = str(brief.get("weakBullet", "")).strip()
    rewrite = str(brief.get("rewrite", "")).strip()
    score_rows = brief.get("scoreReceipt")
    if not candidate:
        blockers.append("resume_brief.json missing candidateName")
    elif first_name and first_name not in lower:
        blockers.append(f"script does not name candidate: {candidate}")
    if not target_role:
        blockers.append("resume_brief.json missing targetRole")
    else:
        role_tokens = [token.lower() for token in re.findall(r"[A-Za-z]+", target_role) if len(token) > 2]
        if role_tokens and not any(token in lower for token in role_tokens):
            blockers.append(f"script does not mention target role: {target_role}")
    if not weak:
        blockers.append("resume_brief.json missing weakBullet")
    elif args.require_weak_quote and weak.lower() not in lower:
        blockers.append("script does not quote or closely include the weak resume line")
    if not rewrite:
        blockers.append("resume_brief.json missing rewrite")
    elif not any(token.lower() in lower for token in re.findall(r"[A-Za-z0-9]+", rewrite) if len(token) > 4):
        blockers.append("script does not reference the rewrite/proof")
    if not isinstance(score_rows, list) or len(score_rows) < 3:
        blockers.append("resume_brief.json scoreReceipt needs at least 3 visible factors")

    blockers.extend(human_review_flow_blockers(plain))

    proof_terms = [str(brief.get("hiddenProof", "")), rewrite]
    proof_words = {
        token.lower()
        for text in proof_terms
        for token in re.findall(r"[A-Za-z0-9+#.]+", text)
        if len(token) > 2
    }
    if proof_words and len(proof_words.intersection(set(re.findall(r"[a-z0-9+#.]+", lower)))) < 2:
        blockers.append("script does not include enough concrete proof words from the resume fix")

    report = {
        "passed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "wordCount": words,
        "candidate": candidate,
        "targetRole": target_role,
        "weakBullet": weak,
        "rewrite": rewrite,
        "spokenScriptPreview": plain[:800],
    }
    path = write_quality_gate(work_dir, "script_qa", report, args.run_id)
    report["reportPath"] = str(path)
    emit(report)
    if blockers:
        raise SystemExit(1)


def creative_qa(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve()
    brief = load_resume_brief(work_dir)
    spoken = read_spoken_script(work_dir)
    plain = markdown_to_plain(spoken)
    lower = plain.lower()
    blockers: list[str] = []
    warnings: list[str] = []

    research_report = read_quality_gate(work_dir, "research_swipe")
    creative_gate_report = read_quality_gate(work_dir, "creative_gate")
    script_report = read_quality_gate(work_dir, "script_qa")
    if not (creative_gate_report and creative_gate_report.get("passed")) and not (
        research_report and research_report.get("passed")
    ):
        blockers.append("creative_gate or research_swipe gate must pass before creative QA")
    if not script_report or not script_report.get("passed"):
        blockers.append("script_qa gate must pass before creative QA")

    format_name = args.format or str(brief.get("format", "") or "").strip() or "unspecified"
    surface_formats = {
        "paper_desk_teardown",
        "paper_desk_roast_rebuild",
        "tablet_screen_teardown",
        "tablet_screen_edit_rebuild",
        "surface_fit_storyboard",
    }
    is_surface = format_name in surface_formats or (work_dir / "surface_fit.json").exists()
    if format_name == "unspecified":
        warnings.append("no explicit format set; expected desk_teardown, screen_recording_teardown, search_test, myth_bust, or template_reaction")

    weak = str(brief.get("weakBullet", "")).strip()
    rewrite = str(brief.get("rewrite", "")).strip()
    score_rows = brief.get("scoreReceipt")
    if not weak or not rewrite:
        blockers.append("creative QA requires weakBullet and rewrite in resume_brief.json")
    if weak and rewrite and weak == rewrite:
        blockers.append("weakBullet and rewrite are identical")
    if isinstance(score_rows, list):
        required_receipt_terms = ("keyword", "tool", "metric", "outcome")
        receipt_blob = json.dumps(score_rows).lower()
        missing = [term for term in required_receipt_terms if term not in receipt_blob]
        if missing:
            blockers.append("score receipt missing factor(s): " + ", ".join(missing))
    else:
        blockers.append("scoreReceipt is missing or not a list")

    if not re.search(r"\b(noah|maya|shawn|[A-Z][a-z]+)\b", plain):
        warnings.append("script may not feel like a named human resume teardown")
    if "run signal" not in lower and "free signal score" not in lower and "before you apply" not in lower:
        blockers.append("CTA must drive to the free Signal score before applying")
    if "score" in lower and not isinstance(score_rows, list):
        blockers.append("script mentions score but scoreReceipt is absent")

    overlay_dirs = sorted(work_dir.glob("overlay*_frames"))
    overlay_pngs = sorted({*work_dir.glob("overlay*.png"), *work_dir.glob("*overlay*.png")})
    surface_overlay_paths: list[str] = []
    surface_fit_manifest = work_dir / "surface_fit.json"
    if surface_fit_manifest.exists():
        try:
            surface_data = json.loads(surface_fit_manifest.read_text(encoding="utf-8"))
            for surface in surface_data.get("surfaces", []):
                if not isinstance(surface, dict):
                    continue
                overlay = resolve_surface_asset(work_dir, surface.get("overlay") or surface.get("resumeOverlay"))
                if overlay and overlay.exists():
                    surface_overlay_paths.append(str(overlay))
        except Exception as exc:
            blockers.append(f"surface_fit.json could not be read for creative QA: {exc}")
    if not overlay_dirs and not overlay_pngs:
        blockers.append("no deterministic readable overlays found")
    if overlay_dirs:
        empty_dirs = [path.name for path in overlay_dirs if not any(path.glob("*.png"))]
        if empty_dirs:
            blockers.append("overlay frame directories are empty: " + ", ".join(empty_dirs))

    shot_files = sorted(work_dir.glob("shot*.mp4"))
    if is_surface:
        if not surface_fit_manifest.exists():
            blockers.append("surface-fit format requires surface_fit.json")
        if not surface_overlay_paths:
            blockers.append("surface-fit format requires deterministic overlay paths in surface_fit.json")
    elif not shot_files:
        blockers.append("no shot*.mp4 video plates found")

    report = {
        "passed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "format": format_name,
        "overlayFrameDirs": [str(path) for path in overlay_dirs],
        "overlayPngs": [str(path) for path in overlay_pngs],
        "surfaceFitManifest": str(surface_fit_manifest) if surface_fit_manifest.exists() else None,
        "surfaceOverlayPngs": surface_overlay_paths,
        "shotFiles": [str(path) for path in shot_files],
        "reviewQuestions": [
            "Does frame one show a resume/JD/problem?",
            "Does the weak line visibly change?",
            "Does the score receipt appear before the score?",
            "Would a real recruiter say this out loud?",
        ],
    }
    path = write_quality_gate(work_dir, "creative_qa", report, args.run_id)
    report["reportPath"] = str(path)
    emit(report)
    if blockers:
        raise SystemExit(1)


def screen_visual_qa(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve()
    input_path = Path(args.input).resolve() if args.input else work_dir / "screen_teardown_gold_jordan.json"
    contact_sheet = Path(args.contact_sheet).resolve() if args.contact_sheet else work_dir / "screen_teardown_storyboard_contact_sheet.png"
    frame_dir = work_dir / "screen_teardown_storyboard"
    blockers: list[str] = []
    warnings: list[str] = []

    data: dict[str, Any] = {}
    if not input_path.exists():
        blockers.append(f"screen teardown input missing: {input_path}")
    else:
        try:
            data = json.loads(input_path.read_text(encoding="utf-8"))
        except Exception as exc:
            blockers.append(f"screen teardown input is not valid JSON: {exc}")

    if not contact_sheet.exists():
        blockers.append(f"storyboard contact sheet missing: {contact_sheet}")
    if not frame_dir.exists() or len(list(frame_dir.glob("*.png"))) < 6:
        blockers.append("screen_teardown_storyboard needs at least 6 PNG frames")
    if not args.visual_reviewed:
        blockers.append("screen storyboard visual review not confirmed; inspect full-size frames, then rerun with --visual-reviewed")

    required_fields = ("candidateName", "targetRole", "weakLine", "rewriteLine", "proofLines", "searchTerms", "receiptRows")
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        blockers.append("screen teardown input missing field(s): " + ", ".join(missing))

    weak = str(data.get("weakLine", "")).strip()
    rewrite = str(data.get("rewriteLine", "")).strip()
    if weak and rewrite and weak == rewrite:
        blockers.append("weakLine and rewriteLine are identical")
    if rewrite:
        def listish(value: Any) -> list[Any]:
            return value if isinstance(value, list) else []

        rewrite_tokens = set(re.findall(r"[a-z0-9+#.-]+", rewrite.lower()))
        expected_text = " ".join(
            [
                " ".join(str(term) for term in listish(data.get("searchTerms"))),
                " ".join(str(line) for line in listish(data.get("proofLines"))),
                json.dumps(data.get("receiptRows") or [], ensure_ascii=False),
            ]
        ).lower()
        expected_tokens = {
            token
            for token in re.findall(r"[a-z0-9+#.-]+", expected_text)
            if len(token) >= 3
            and token
            not in {
                "and",
                "the",
                "for",
                "with",
                "that",
                "this",
                "proof",
                "search",
                "result",
                "tool",
                "metric",
                "outcome",
                "match",
            }
        }
        if expected_tokens and not rewrite_tokens.intersection(expected_tokens):
            warnings.append("rewrite does not appear to include terms from this run's search/proof/receipt data")

    screen_blob = json.dumps(data).lower()
    banned = [
        phrase
        for phrase in ("same person", "better signal", "ats rejected", "beat the bots", "guaranteed")
        if phrase in screen_blob
    ]
    if banned:
        blockers.append("screen teardown input contains banned phrase(s): " + ", ".join(banned))

    report = {
        "passed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "input": str(input_path),
        "contactSheet": str(contact_sheet),
        "frameDir": str(frame_dir),
        "frameCount": len(list(frame_dir.glob("*.png"))) if frame_dir.exists() else 0,
        "visualReviewed": bool(args.visual_reviewed),
        "reviewChecklist": [
            "Resume readable at full-frame size.",
            "Weak line visible before edit.",
            "Proof appears before rewrite.",
            "Rewrite appears in the same resume slot.",
            "Receipt explains the rewrite without a random score.",
            "No fake hands, fake stylus, generated readable text, wrong logo, or wrong URL.",
        ],
    }
    path = write_quality_gate(work_dir, "screen_visual_qa", report, args.run_id)
    report["reportPath"] = str(path)
    emit(report)
    if blockers:
        raise SystemExit(1)


def plate_qa(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve()
    videos: list[Path] = []
    image_plates: list[Path] = []
    discovery_blockers: list[str] = []
    image_exts = {".png", ".jpg", ".jpeg", ".webp"}
    if args.video:
        for raw_path in args.video:
            path = Path(raw_path).resolve()
            if path.suffix.lower() in image_exts:
                image_plates.append(path)
            else:
                videos.append(path)
    else:
        videos.extend(sorted(work_dir.glob("shot*.mp4")))
        surface_manifest = work_dir / "surface_fit.json"
        if surface_manifest.exists():
            try:
                surface_data = json.loads(surface_manifest.read_text(encoding="utf-8"))
                for surface in surface_data.get("surfaces", []):
                    if not isinstance(surface, dict):
                        continue
                    frame = resolve_surface_asset(work_dir, surface.get("frame") or surface.get("image"))
                    if frame and frame.suffix.lower() in image_exts and frame not in image_plates:
                        image_plates.append(frame)
            except Exception as exc:
                discovery_blockers.append(f"surface_fit.json could not be read for plate image discovery: {exc}")
    blockers: list[str] = []
    warnings: list[str] = []
    blockers.extend(discovery_blockers)
    plate_reports: list[dict[str, Any]] = []
    frame_dir = quality_gate_dir(work_dir) / "plate_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)

    for video in videos:
        if not video.exists():
            blockers.append(f"plate missing: {video}")
            continue
        data = ffprobe_json(video)
        streams = data.get("streams", [])
        video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
        duration = float(data.get("format", {}).get("duration") or 0)
        width = int(video_stream.get("width", 0)) if video_stream else 0
        height = int(video_stream.get("height", 0)) if video_stream else 0
        fps = frame_rate(video_stream) if video_stream else 0
        if not video_stream:
            blockers.append(f"plate has no video stream: {video.name}")
        if width < 720 or height < 1280:
            blockers.append(f"plate resolution too small: {video.name} is {width}x{height}")
        if height <= width:
            blockers.append(f"plate is not vertical: {video.name} is {width}x{height}")
        if duration < 3:
            blockers.append(f"plate duration too short: {video.name} is {duration:.2f}s")
        if any(token in video.name.lower() for token in ("remotion", "mock", "fallback", "canvas")):
            blockers.append(f"plate filename suggests forbidden fallback renderer: {video.name}")
        if video.suffix.lower() == ".tmp":
            warnings.append(f"plate uses temporary extension; rename after download: {video.name}")
        try:
            frame_path = frame_dir / f"{video.stem}_mid.jpg"
            subprocess.run(
                [
                    find_exe("ffmpeg"),
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-ss",
                    f"{max(0.1, duration / 2):.2f}",
                    "-i",
                    str(video),
                    "-frames:v",
                    "1",
                    str(frame_path),
                ],
                check=True,
            )
        except Exception as exc:
            warnings.append(f"could not extract QA frame for {video.name}: {exc}")
            frame_path = None
        plate_reports.append(
            {
                "type": "video",
                "video": str(video),
                "width": width,
                "height": height,
                "fps": round(fps, 3) if fps else None,
                "durationSec": round(duration, 3),
                "framePath": str(frame_path) if frame_path else None,
            }
        )

    for image in image_plates:
        if not image.exists():
            blockers.append(f"plate image missing: {image}")
            continue
        width = height = 0
        try:
            with Image.open(image) as plate_image:
                width, height = plate_image.size
        except Exception as exc:
            blockers.append(f"could not open plate image {image.name}: {exc}")
        if width < 720 or height < 1280:
            blockers.append(f"plate image resolution too small: {image.name} is {width}x{height}")
        if height <= width:
            blockers.append(f"plate image is not vertical: {image.name} is {width}x{height}")
        if any(token in image.name.lower() for token in ("remotion", "mock", "fallback", "canvas")):
            blockers.append(f"plate image filename suggests forbidden fallback renderer: {image.name}")
        plate_reports.append(
            {
                "type": "image",
                "image": str(image),
                "width": width,
                "height": height,
                "fps": None,
                "durationSec": None,
                "framePath": str(image),
            }
        )

    if not videos and not image_plates:
        blockers.append("no plate videos/images provided, found as shot*.mp4, or referenced by surface_fit.json")
    if not args.visual_reviewed:
        blockers.append("plate visual review not confirmed; inspect extracted frames for fake text, watermark, bad hands, and unstable document area, then rerun with --visual-reviewed")
    if args.generated_text_ok:
        blockers.append("generated resume/JD text is not allowed in production plates")

    report = {
        "passed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "plates": plate_reports,
        "visualReviewRequired": True,
        "visualReviewChecklist": [
            "No important generated text in the plate.",
            "No visible provider watermark.",
            "Hands/person are plausible and consistent.",
            "Document/tablet/screen area is stable enough for overlays.",
        ],
    }
    path = write_quality_gate(work_dir, "plate_qa", report, args.run_id)
    report["reportPath"] = str(path)
    emit(report)
    if blockers:
        raise SystemExit(1)


def resolve_surface_asset(work_dir: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value.strip())
    if not path.is_absolute():
        path = work_dir / path
    return path.resolve()


def normalize_surface_corners(raw: Any) -> list[tuple[float, float]]:
    if isinstance(raw, dict):
        ordered = [raw.get(key) for key in ("tl", "tr", "br", "bl")]
    elif isinstance(raw, list):
        ordered = raw
    else:
        ordered = []
    points: list[tuple[float, float]] = []
    for point in ordered:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError("each corner must be a two-number [x, y] point")
        x, y = float(point[0]), float(point[1])
        points.append((x, y))
    if len(points) != 4:
        raise ValueError("surface corners must contain exactly four points in tl,tr,br,bl order")
    return points


def polygon_area(points: list[tuple[float, float]]) -> float:
    area = 0.0
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2


def solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    rows = [matrix[index][:] + [vector[index]] for index in range(size)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda row: abs(rows[row][col]))
        if abs(rows[pivot][col]) < 1e-9:
            raise ValueError("surface perspective solve failed; corners may be degenerate")
        rows[col], rows[pivot] = rows[pivot], rows[col]
        pivot_value = rows[col][col]
        rows[col] = [value / pivot_value for value in rows[col]]
        for row in range(size):
            if row == col:
                continue
            factor = rows[row][col]
            rows[row] = [rows[row][idx] - factor * rows[col][idx] for idx in range(size + 1)]
    return [rows[index][-1] for index in range(size)]


def perspective_coefficients(
    output_points: list[tuple[float, float]],
    source_points: list[tuple[float, float]],
) -> list[float]:
    matrix: list[list[float]] = []
    vector: list[float] = []
    for (x, y), (u, v) in zip(output_points, source_points):
        matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        vector.append(u)
        matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        vector.append(v)
    return solve_linear_system(matrix, vector)


def surface_float(surface: dict[str, Any], key: str, default: float, minimum: float, maximum: float) -> float:
    raw = surface.get(key)
    if raw is None and isinstance(surface.get("blend"), dict):
        raw = surface["blend"].get(key)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def create_quad_mask(size: tuple[int, int], corners: list[tuple[float, float]], feather_px: float) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon([(float(x), float(y)) for x, y in corners], fill=255)
    if feather_px > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather_px))
    return mask


def apply_overlay_enhancements(overlay: Image.Image, surface: dict[str, Any]) -> Image.Image:
    enhanced = overlay.convert("RGBA")
    brightness = surface_float(surface, "brightness", 1.0, 0.65, 1.35)
    contrast = surface_float(surface, "contrast", 1.0, 0.65, 1.45)
    if abs(brightness - 1.0) > 0.001:
        enhanced = ImageEnhance.Brightness(enhanced).enhance(brightness)
    if abs(contrast - 1.0) > 0.001:
        enhanced = ImageEnhance.Contrast(enhanced).enhance(contrast)
    return enhanced


def create_screen_glare(size: tuple[int, int], corners: list[tuple[float, float]], strength: float) -> Image.Image:
    glare = Image.new("RGBA", size, (255, 255, 255, 0))
    if strength <= 0:
        return glare
    width, height = size
    alpha = int(70 * max(0.0, min(1.0, strength)))
    band_width = max(80, int(width * 0.18))
    draw = ImageDraw.Draw(glare)
    draw.polygon(
        [
            (int(width * 0.08), 0),
            (int(width * 0.08) + band_width, 0),
            (int(width * 0.72) + band_width, height),
            (int(width * 0.72), height),
        ],
        fill=(255, 255, 255, alpha),
    )
    glare = glare.filter(ImageFilter.GaussianBlur(radius=24))
    mask = create_quad_mask(size, corners, surface_float({"edgeFeatherPx": 1}, "edgeFeatherPx", 1.0, 0.0, 12.0))
    glare.putalpha(ImageChops.multiply(glare.getchannel("A"), mask))
    return glare


def validate_surface_fit_manifest(
    work_dir: Path,
    manifest_path: Path,
    min_area_ratio: float = 0.08,
    max_area_ratio: float = 0.92,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    surfaces_report: list[dict[str, Any]] = []

    if not manifest_path.exists():
        return {
            "passed": False,
            "blockers": [f"surface fit manifest missing: {manifest_path}"],
            "warnings": warnings,
            "surfaces": surfaces_report,
        }

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "passed": False,
            "blockers": [f"surface fit manifest is not valid JSON: {exc}"],
            "warnings": warnings,
            "surfaces": surfaces_report,
        }

    surfaces = data.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        blockers.append("surface_fit.json must contain a non-empty surfaces array")
        surfaces = []

    for index, surface in enumerate(surfaces, start=1):
        item_blockers: list[str] = []
        item_warnings: list[str] = []
        if not isinstance(surface, dict):
            blockers.append(f"surface #{index} is not an object")
            continue
        surface_type = str(surface.get("surface") or surface.get("type") or "").strip().lower()
        if surface_type not in {"paper", "tablet", "screen", "monitor", "laptop"}:
            item_blockers.append("surface must be paper, tablet, screen, monitor, or laptop")

        frame = resolve_surface_asset(work_dir, surface.get("frame") or surface.get("image"))
        overlay = resolve_surface_asset(work_dir, surface.get("overlay") or surface.get("resumeOverlay"))
        if not frame:
            item_blockers.append("frame/image path is required")
        elif not frame.exists():
            item_blockers.append(f"frame missing: {frame}")
        if not overlay:
            item_blockers.append("overlay/resumeOverlay path is required")
        elif not overlay.exists():
            item_blockers.append(f"overlay missing: {overlay}")

        points: list[tuple[float, float]] = []
        width = height = 0
        if frame and frame.exists():
            try:
                with Image.open(frame) as image:
                    width, height = image.size
            except Exception as exc:
                item_blockers.append(f"could not open frame image: {exc}")
        try:
            points = normalize_surface_corners(surface.get("corners") or surface.get("quad"))
        except Exception as exc:
            item_blockers.append(str(exc))

        area_ratio = 0.0
        if points and width and height:
            out_of_bounds = [
                (round(x, 1), round(y, 1))
                for x, y in points
                if x < 0 or y < 0 or x > width or y > height
            ]
            if out_of_bounds:
                item_blockers.append(f"corner(s) outside frame bounds: {out_of_bounds}")
            area_ratio = polygon_area(points) / max(1, width * height)
            if area_ratio < min_area_ratio:
                item_blockers.append(f"surface area too small for readable resume: {area_ratio:.3f}")
            if area_ratio > max_area_ratio:
                item_warnings.append(f"surface area fills most of frame; verify it still feels like a real {surface_type} scene: {area_ratio:.3f}")
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            if min(width - max(xs), min(xs), height - max(ys), min(ys)) < 12:
                item_warnings.append("surface is very close to frame edge; social UI/crop may hide content")

        if item_blockers:
            blockers.extend([f"surface #{index}: {blocker}" for blocker in item_blockers])
        warnings.extend([f"surface #{index}: {warning}" for warning in item_warnings])
        surfaces_report.append(
            {
                "index": index,
                "surface": surface_type,
                "frame": str(frame) if frame else None,
                "overlay": str(overlay) if overlay else None,
                "frameSize": [width, height] if width and height else None,
                "corners": [[round(x, 2), round(y, 2)] for x, y in points],
                "areaRatio": round(area_ratio, 4) if area_ratio else None,
                "blend": surface.get("blend") if isinstance(surface.get("blend"), dict) else {},
                "passed": not item_blockers,
            }
        )

    return {
        "passed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "surfaces": surfaces_report,
        "manifest": str(manifest_path),
        "reviewChecklist": [
            "Resume layer is corner-pinned into the physical paper/tablet/screen area.",
            "Resume is clipped or masked to that quadrilateral, not floating above it.",
            "Text remains readable after perspective distortion.",
            "Edge feather, opacity, and glare are subtle enough to feel physical without blurring the resume.",
            "The overlay inherits light/glare/shadow from the scene without losing sharpness.",
            "No fake hand, fake stylus, generated readable text, watermark, or wrong URL/logo appears.",
        ],
    }


def create_surface_fit_previews(work_dir: Path, manifest_path: Path, out_dir: Path) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        raise SystemExit(f"surface fit manifest missing: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    surfaces = data.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise SystemExit("surface_fit.json must contain a non-empty surfaces array")
    out_dir.mkdir(parents=True, exist_ok=True)
    previews: list[dict[str, Any]] = []
    for index, surface in enumerate(surfaces, start=1):
        if not isinstance(surface, dict):
            raise SystemExit(f"surface #{index} is not an object")
        frame_path = resolve_surface_asset(work_dir, surface.get("frame") or surface.get("image"))
        overlay_path = resolve_surface_asset(work_dir, surface.get("overlay") or surface.get("resumeOverlay"))
        if not frame_path or not frame_path.exists():
            raise SystemExit(f"surface #{index} frame missing: {frame_path}")
        if not overlay_path or not overlay_path.exists():
            raise SystemExit(f"surface #{index} overlay missing: {overlay_path}")
        corners = normalize_surface_corners(surface.get("corners") or surface.get("quad"))
        with Image.open(frame_path) as frame_image, Image.open(overlay_path) as overlay_image:
            frame = frame_image.convert("RGBA")
            overlay = apply_overlay_enhancements(overlay_image, surface)
            source_points = [
                (0.0, 0.0),
                (float(overlay.width), 0.0),
                (float(overlay.width), float(overlay.height)),
                (0.0, float(overlay.height)),
            ]
            coeffs = perspective_coefficients(corners, source_points)
            warped = overlay.transform(
                frame.size,
                Image.Transform.PERSPECTIVE,
                coeffs,
                Image.Resampling.BICUBIC,
            )
            opacity = surface_float(surface, "opacity", 1.0, 0.05, 1.0)
            edge_feather = surface_float(surface, "edgeFeatherPx", 1.0, 0.0, 16.0)
            surface_mask = create_quad_mask(frame.size, corners, edge_feather)
            alpha = ImageChops.multiply(warped.getchannel("A"), surface_mask)
            if opacity < 1:
                alpha = alpha.point(lambda value: int(value * opacity))
            warped.putalpha(alpha)
            fitted = frame.copy()
            fitted.alpha_composite(warped)
            glare_strength = surface_float(surface, "screenGlare", 0.0, 0.0, 1.0)
            if glare_strength > 0:
                fitted.alpha_composite(create_screen_glare(frame.size, corners, glare_strength))
            out_path = out_dir / f"surface_{index:02d}_{frame_path.stem}_fit.png"
            fitted.convert("RGB").save(out_path, quality=94)
        previews.append(
            {
                "index": index,
                "surface": surface.get("surface") or surface.get("type"),
                "frame": str(frame_path),
                "overlay": str(overlay_path),
                "out": str(out_path),
                "corners": [[round(x, 2), round(y, 2)] for x, y in corners],
            }
        )
    return previews


def surface_fit_preview(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve()
    manifest = Path(args.manifest).resolve() if args.manifest else work_dir / "surface_fit.json"
    report = validate_surface_fit_manifest(
        work_dir,
        manifest,
        min_area_ratio=args.min_area_ratio,
        max_area_ratio=args.max_area_ratio,
    )
    if report.get("blockers"):
        emit(report)
        raise SystemExit(1)
    out_dir = Path(args.out_dir).resolve() if args.out_dir else work_dir / "surface_fit_previews"
    previews = create_surface_fit_previews(work_dir, manifest, out_dir)
    emit(
        {
            "status": "SURFACE_FIT_PREVIEW",
            "runId": args.run_id,
            "manifest": str(manifest),
            "outDir": str(out_dir),
            "previews": previews,
            "nextStep": "Inspect the preview images full-size, then run surface-fit-qa with --visual-reviewed if the resume is pinned and readable.",
        }
    )


def surface_fit_review_packet(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve()
    manifest = Path(args.manifest).resolve() if args.manifest else work_dir / "surface_fit.json"
    report = validate_surface_fit_manifest(
        work_dir,
        manifest,
        min_area_ratio=args.min_area_ratio,
        max_area_ratio=args.max_area_ratio,
    )
    if report.get("blockers"):
        emit(report)
        raise SystemExit(1)
    out_dir = Path(args.out_dir).resolve() if args.out_dir else work_dir / "surface_fit_previews"
    previews = create_surface_fit_previews(work_dir, manifest, out_dir)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    surfaces = data.get("surfaces") if isinstance(data.get("surfaces"), list) else []

    def rel(path: Path | str | None) -> str:
        if not path:
            return ""
        resolved = Path(path).resolve()
        try:
            return resolved.relative_to(work_dir).as_posix()
        except ValueError:
            return resolved.as_posix()

    cards: list[str] = []
    for preview in previews:
        index = int(preview["index"])
        surface = surfaces[index - 1] if index - 1 < len(surfaces) and isinstance(surfaces[index - 1], dict) else {}
        frame = resolve_surface_asset(work_dir, surface.get("frame") or surface.get("image"))
        overlay = resolve_surface_asset(work_dir, surface.get("overlay") or surface.get("resumeOverlay"))
        beat = escape(str(surface.get("beat") or f"Surface {index}"))
        blend = surface.get("blend") if isinstance(surface.get("blend"), dict) else {}
        cards.append(
            f"""
    <article class="surface-card">
      <div class="surface-head">
        <h2>{beat}</h2>
        <span>{escape(str(preview.get('surface') or surface.get('surface') or 'surface'))}</span>
      </div>
      <div class="triple">
        <figure><img src="{escape(rel(frame))}" alt="Source plate {index}" /><figcaption>Source plate</figcaption></figure>
        <figure><img src="{escape(rel(overlay))}" alt="Deterministic overlay {index}" /><figcaption>Resume overlay</figcaption></figure>
        <figure><img src="{escape(rel(preview['out']))}" alt="Corner-pinned fitted preview {index}" /><figcaption>Fitted result</figcaption></figure>
      </div>
      <dl>
        <div><dt>Corners</dt><dd>{escape(json.dumps(preview.get('corners', [])))}</dd></div>
        <div><dt>Blend</dt><dd>{escape(json.dumps(blend, ensure_ascii=True))}</dd></div>
      </dl>
    </article>
"""
        )

    checklist_items = [
        "Resume sits inside the paper/tablet/screen, not above it.",
        "Edges are clipped to the physical surface and do not bleed outside corners.",
        "Readable text stays sharp after perspective mapping.",
        "Glare/brightness/opacity feels physical but does not blur the edit.",
        "No fake hand, fake stylus, generated readable text, watermark, wrong URL, or wrong logo.",
    ]
    checks_html = "\n".join(f"<li>{escape(item)}</li>" for item in checklist_items)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Signal Surface Fit Review</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f6f7fb; color: #111827; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ width: min(100% - 28px, 1180px); margin: 0 auto; padding: 24px 0 48px; }}
    h1 {{ margin: 0 0 8px; font-size: clamp(32px, 7vw, 58px); line-height: .95; }}
    p {{ margin: 0; color: #4b5563; line-height: 1.55; }}
    .hero, .surface-card, .checklist {{ background: #fff; border: 1px solid #d8e0ec; border-radius: 16px; box-shadow: 0 16px 40px rgba(15, 23, 42, .07); padding: 18px; margin-bottom: 16px; }}
    .status {{ display: inline-flex; margin-bottom: 12px; border-radius: 999px; padding: 7px 11px; background: #eef6ff; color: #075985; font-weight: 800; border: 1px solid #bfdbfe; }}
    .surface-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: start; margin-bottom: 14px; }}
    h2 {{ margin: 0; font-size: 20px; }}
    .surface-head span {{ color: #64748b; font-weight: 800; text-transform: uppercase; font-size: 12px; letter-spacing: .06em; }}
    .triple {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
    figure {{ margin: 0; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; background: #f8fafc; }}
    img {{ width: 100%; display: block; aspect-ratio: 9 / 16; object-fit: contain; background: #0f172a; }}
    figcaption {{ padding: 9px 10px; color: #334155; font-weight: 800; font-size: 13px; }}
    dl {{ display: grid; gap: 8px; margin: 12px 0 0; }}
    dl div {{ display: grid; grid-template-columns: 90px 1fr; gap: 10px; align-items: start; }}
    dt {{ color: #64748b; font-weight: 800; }}
    dd {{ margin: 0; color: #111827; overflow-wrap: anywhere; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 12px; }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin: 8px 0; }}
    @media (max-width: 860px) {{ .triple {{ grid-template-columns: 1fr; }} dl div {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <span class="status">Surface Fit Review</span>
      <h1>Paper/Tablet Fit Check</h1>
      <p>Review the source plate, deterministic overlay, and fitted result before marking <code>surface-fit-qa --visual-reviewed</code>. This page does not approve anything by itself.</p>
    </section>
    <section class="checklist">
      <h2>Pass Checklist</h2>
      <ul>{checks_html}</ul>
    </section>
    {''.join(cards)}
  </main>
</body>
</html>
"""
    html_path = work_dir / (args.html_name or "surface_fit_review.html")
    html_path.write_text(html, encoding="utf-8")
    mobile_url = f"http://{args.host}:{args.port}/{html_path.name}" if args.host else None
    payload = {
        "status": "SURFACE_FIT_REVIEW",
        "runId": args.run_id,
        "manifest": str(manifest),
        "htmlPath": str(html_path),
        "mobileUrl": mobile_url,
        "previewDir": str(out_dir),
        "surfaceCount": len(previews),
        "checklist": checklist_items,
        "nextStep": "Inspect this page. If every fitted result passes, run surface-fit-qa with --visual-reviewed.",
    }
    if args.run_id:
        conn = db()
        get_run(conn, args.run_id)
        log_event(conn, args.run_id, "surface_fit_review_packet", payload)
        conn.commit()
    emit(payload)


def surface_fit_animatic(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve()
    manifest = Path(args.manifest).resolve() if args.manifest else work_dir / "surface_fit.json"
    report = validate_surface_fit_manifest(
        work_dir,
        manifest,
        min_area_ratio=args.min_area_ratio,
        max_area_ratio=args.max_area_ratio,
    )
    if report.get("blockers"):
        emit(report)
        raise SystemExit(1)

    preview_dir = Path(args.preview_dir).resolve() if args.preview_dir else work_dir / "surface_fit_previews"
    previews = create_surface_fit_previews(work_dir, manifest, preview_dir)
    if not previews:
        raise SystemExit("No surface-fit previews were generated.")

    data = json.loads(manifest.read_text(encoding="utf-8"))
    surfaces = data.get("surfaces") if isinstance(data.get("surfaces"), list) else []
    default_duration = max(0.5, float(args.default_duration))
    durations: list[float] = []
    for surface in surfaces:
        duration = surface.get("durationSec") if isinstance(surface, dict) else None
        try:
            durations.append(max(0.5, float(duration)))
        except (TypeError, ValueError):
            durations.append(default_duration)

    out = Path(args.out).resolve() if args.out else work_dir / "surface_fit_animatic.mp4"
    temp_dir = work_dir / "surface_fit_animatic_segments"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = find_exe("ffmpeg")
    segment_paths: list[Path] = []
    for index, preview in enumerate(previews, start=1):
        image_path = Path(preview["out"])
        duration = durations[index - 1] if index - 1 < len(durations) else default_duration
        segment = temp_dir / f"segment_{index:02d}.mp4"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loop",
                "1",
                "-i",
                str(image_path),
                "-f",
                "lavfi",
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-t",
                f"{duration:.3f}",
                "-vf",
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(iw-ow)/2:(ih-oh)/2,fps=30,setsar=1,format=yuv420p",
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-shortest",
                str(segment),
            ],
            check=True,
        )
        segment_paths.append(segment)

    concat_list = temp_dir / "concat_list.txt"
    concat_list.write_text(
        "\n".join(f"file '{path.as_posix()}'" for path in segment_paths),
        encoding="utf-8",
    )
    rough = temp_dir / "surface_fit_animatic_rough.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(rough),
        ],
        check=True,
    )

    audio = Path(args.audio).resolve() if args.audio else None
    if audio:
        if not audio.exists():
            raise SystemExit(f"Audio file not found: {audio}")
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(rough),
                "-i",
                str(audio),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-movflags",
                "+faststart",
                str(out),
            ],
            check=True,
        )
    else:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(rough),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(out),
            ],
            check=True,
        )

    result = {
        "status": "SURFACE_FIT_ANIMATIC",
        "runId": args.run_id,
        "manifest": str(manifest),
        "out": str(out),
        "previewDir": str(preview_dir),
        "segments": [str(path) for path in segment_paths],
        "audio": str(audio) if audio else None,
        "durationSec": round(sum(durations[: len(segment_paths)]), 3),
        "note": "No-credit animatic for visual timing only. Final gold video still needs approved creative gate, clean blank plates, Abby voice, and final QA.",
    }
    if args.run_id:
        conn = db()
        get_run(conn, args.run_id)
        log_event(conn, args.run_id, "surface_fit_animatic", result)
        conn.commit()
    emit(result)


def surface_fit_qa(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve()
    manifest = Path(args.manifest).resolve() if args.manifest else work_dir / "surface_fit.json"
    report = validate_surface_fit_manifest(
        work_dir,
        manifest,
        min_area_ratio=args.min_area_ratio,
        max_area_ratio=args.max_area_ratio,
    )
    blockers = list(report.get("blockers", []))
    if not args.visual_reviewed:
        blockers.append("surface fit visual review not confirmed; inspect full-size corner-pinned frames, then rerun with --visual-reviewed")
    report = {
        **report,
        "passed": not blockers,
        "blockers": blockers,
        "visualReviewed": bool(args.visual_reviewed),
        "minAreaRatio": args.min_area_ratio,
        "maxAreaRatio": args.max_area_ratio,
    }
    path = write_quality_gate(work_dir, "surface_fit_qa", report, args.run_id)
    report["reportPath"] = str(path)
    emit(report)
    if blockers:
        raise SystemExit(1)


def find_exe(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    if name == "ffmpeg":
        try:
            import imageio_ffmpeg

            ffmpeg = Path(imageio_ffmpeg.get_ffmpeg_exe())
            if ffmpeg.exists():
                return str(ffmpeg)
        except Exception:
            pass
    winget_root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if winget_root.exists():
        matches = sorted(winget_root.rglob(f"{name}.exe"))
        if matches:
            return str(matches[-1])
    raise SystemExit(f"Could not find {name}. Install ffmpeg/ffprobe or add it to PATH.")


def assemble(args: argparse.Namespace) -> None:
    if not ASSEMBLE_PS1.exists():
        raise SystemExit(f"Missing assembler: {ASSEMBLE_PS1}")
    work_dir = Path(args.work_dir).resolve()
    out = args.out
    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ASSEMBLE_PS1),
        "-WorkDir",
        str(work_dir),
        "-Out",
        out,
    ]
    if getattr(args, "background_clip", None):
        command.extend(["-BackgroundClip", str(Path(args.background_clip).resolve())])
    subprocess.run(command, cwd=str(ROOT), check=True)
    video_path = work_dir / out
    if args.run_id:
        conn = db()
        get_run(conn, args.run_id)
        update_run(conn, args.run_id, status="RENDERED", video_path=str(video_path))
        log_event(conn, args.run_id, "rendered", {"videoPath": str(video_path), "assembler": str(ASSEMBLE_PS1)})
        conn.commit()
    emit({"status": "RENDERED", "video": str(video_path)})


def contact_sheet(args: argparse.Namespace) -> None:
    video = Path(args.video).resolve()
    if not video.exists():
        raise SystemExit(f"Video not found: {video}")
    data = ffprobe_json(video)
    duration = float(data.get("format", {}).get("duration") or 0)
    if duration <= 0:
        raise SystemExit(f"Could not determine video duration: {video}")

    if args.times:
        times = [float(value.strip()) for value in args.times.split(",") if value.strip()]
    else:
        count = max(3, args.count)
        times = [duration * (index + 1) / (count + 1) for index in range(count)]
    times = [min(max(0.05, value), max(0.05, duration - 0.05)) for value in times]

    out = Path(args.out).resolve() if args.out else video.with_name(video.stem + "_qa_contact_sheet.png")
    frame_dir = out.with_name(out.stem + "_frames")
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg = find_exe("ffmpeg")
    frames: list[Path] = []
    for index, at in enumerate(times, start=1):
        frame = frame_dir / f"frame_{index:02d}_{at:.2f}s.jpg"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{at:.3f}",
                "-i",
                str(video),
                "-frames:v",
                "1",
                str(frame),
            ],
            check=True,
        )
        frames.append(frame)

    thumb_w = args.thumb_width
    thumb_h = int(thumb_w * 16 / 9)
    cols = args.columns
    rows = (len(frames) + cols - 1) // cols
    title_h = 62
    gap = 16
    sheet_w = cols * thumb_w + (cols + 1) * gap
    sheet_h = rows * (thumb_h + title_h) + (rows + 1) * gap
    sheet = Image.new("RGB", (sheet_w, sheet_h), "#f8fafc")
    draw = ImageDraw.Draw(sheet)
    try:
        font_label = ImageFont.truetype("arial.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font_label = ImageFont.load_default()
        font_small = ImageFont.load_default()

    for index, frame in enumerate(frames):
        col = index % cols
        row = index // cols
        left = gap + col * (thumb_w + gap)
        top = gap + row * (thumb_h + title_h + gap)
        with Image.open(frame) as image:
            image = image.convert("RGB")
            image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (thumb_w, thumb_h), "#e5e7eb")
            canvas.paste(image, ((thumb_w - image.width) // 2, (thumb_h - image.height) // 2))
            sheet.paste(canvas, (left, top))
        draw.rectangle([left, top + thumb_h, left + thumb_w, top + thumb_h + title_h], fill="#111827")
        draw.text((left + 14, top + thumb_h + 12), f"{times[index]:.1f}s", fill="#f8fafc", font=font_label)
        draw.text((left + 90, top + thumb_h + 16), args.label or "QA frame", fill="#94a3b8", font=font_small)

    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=92)
    report = {
        "status": "CONTACT_SHEET",
        "video": str(video),
        "out": str(out),
        "frameDir": str(frame_dir),
        "durationSec": round(duration, 3),
        "timesSec": [round(value, 3) for value in times],
        "frameCount": len(frames),
    }
    emit(report)


def media_duration(path: Path) -> float:
    data = ffprobe_json(path)
    return float(data.get("format", {}).get("duration") or 0)


def screen_build_plan(args: argparse.Namespace) -> None:
    run_id = args.run_id
    work_dir = Path(args.work_dir).resolve() if args.work_dir else run_folder(run_id)
    conn = db()
    row = get_run(conn, run_id)
    metadata = json.loads(row["metadata_json"] or "{}")
    creative_report = read_quality_gate(work_dir, "creative_gate") or {}
    script_report = read_quality_gate(work_dir, "script_qa") or {}
    visual_report = read_quality_gate(work_dir, "screen_visual_qa") or {}
    approval_phrase = metadata.get("creativeApprovalPhrase") or creative_report.get("approvalPhrase") or f"APPROVE CREATIVE GATE {run_id}"

    input_json = work_dir / "screen_teardown_gold_jordan.json"
    voice_text = work_dir / "voice_full_script.txt"
    voice_test = work_dir / "voice_test_abby_10s.txt"
    audio_path = work_dir / (args.audio_name or "abby_voice_full.mp3")
    visual_path = work_dir / (args.visual_name or "gold_screen_visual_only.mp4")
    final_path = work_dir / (args.final_name or "signal_gold_screen_teardown_jordan_v1.mp4")
    sheet_path = work_dir / (args.contact_sheet_name or "signal_gold_screen_teardown_jordan_v1_contact_sheet.png")

    blockers: list[str] = []
    if not creative_report.get("passed"):
        blockers.append("creative_gate is missing or failed")
    if not script_report.get("passed"):
        blockers.append("script_qa is missing or failed")
    if not visual_report.get("passed"):
        blockers.append("screen_visual_qa is missing or failed")
    for label, path in (
        ("screen teardown JSON", input_json),
        ("full voice script", voice_text),
        ("10-second voice test script", voice_test),
        ("screen storyboard contact sheet", work_dir / "screen_teardown_storyboard_contact_sheet.png"),
    ):
        if not path.exists():
            blockers.append(f"missing {label}: {path}")
    for tool in ("node", "ffmpeg", "ffprobe"):
        try:
            find_exe(tool)
        except Exception as exc:
            blockers.append(f"{tool} unavailable: {exc}")

    creative_approved = bool(metadata.get("creativeGateApproved"))
    blocked_reason = "" if creative_approved else f"waiting for creative approval phrase: {approval_phrase}"
    commands = [
        f'py -3 marketing_agent\\signal_growth_pipeline.py approve-creative --run-id {run_id} --phrase "{approval_phrase}"',
        f"py -3 marketing_agent\\signal_growth_pipeline.py build-screen-teardown --run-id {run_id} --voice-test-only",
        f"py -3 marketing_agent\\signal_growth_pipeline.py build-screen-teardown --run-id {run_id}",
        f"py -3 marketing_agent\\signal_growth_pipeline.py review --run-id {run_id} --host {args.host or '192.168.2.10'} --port {args.port}",
    ]
    report = {
        "runId": run_id,
        "status": row["status"],
        "workDir": str(work_dir),
        "readyAfterApproval": not blockers,
        "creativeApproved": creative_approved,
        "blockedReason": blocked_reason,
        "blockers": blockers,
        "approvalPhrase": approval_phrase,
        "expectedOutputs": {
            "voiceTest": str(work_dir / "abby_voice_test_10s.mp3"),
            "audio": str(audio_path),
            "visual": str(visual_path),
            "finalVideo": str(final_path),
            "contactSheet": str(sheet_path),
        },
        "commands": commands,
        "gates": {
            "creative_gate": bool(creative_report.get("passed")),
            "script_qa": bool(script_report.get("passed")),
            "screen_visual_qa": bool(visual_report.get("passed")),
        },
    }
    out_path = work_dir / "post_approval_screen_build_plan.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    report["planPath"] = str(out_path)
    emit(report)
    if blockers:
        raise SystemExit(1)


def surface_build_plan(args: argparse.Namespace) -> None:
    run_id = args.run_id
    if run_id:
        work_dir = Path(args.work_dir).resolve() if args.work_dir else run_folder(run_id)
        conn = db()
        row = get_run(conn, run_id)
        metadata = json.loads(row["metadata_json"] or "{}")
        status = row["status"]
        title = row["title"]
    else:
        if not args.work_dir:
            raise SystemExit("Provide --run-id or --work-dir")
        work_dir = Path(args.work_dir).resolve()
        row = None
        metadata = {}
        status = "NO_DB_RUN"
        title = work_dir.name

    creative_report = read_quality_gate(work_dir, "creative_gate") or {}
    script_report = read_quality_gate(work_dir, "script_qa") or {}
    creative_qa_report = read_quality_gate(work_dir, "creative_qa") or {}
    plate_report = read_quality_gate(work_dir, "plate_qa") or {}
    surface_report = read_quality_gate(work_dir, "surface_fit_qa") or {}
    approval_phrase = metadata.get("creativeApprovalPhrase") or creative_report.get("approvalPhrase") or (f"APPROVE CREATIVE GATE {run_id}" if run_id else "")

    voice_text = work_dir / (args.voice_text_name or "voice_full_script.txt")
    selected_script = work_dir / "selected_script.md"
    manifest = work_dir / (args.manifest_name or "surface_fit.json")
    prompt_file = work_dir / (args.prompt_name or "blank_plate_generation_prompts.md")
    audio_path = work_dir / (args.audio_name or "abby_voice_full.mp3")
    animatic_path = work_dir / (args.animatic_name or "surface_fit_animatic.mp4")
    final_path = work_dir / (args.final_name or "signal_gold_surface_teardown_v1.mp4")
    sheet_path = work_dir / (args.contact_sheet_name or "signal_gold_surface_teardown_v1_contact_sheet.png")

    blockers: list[str] = []
    warnings: list[str] = []
    required_no_credit_files = [
        ("selected script", selected_script),
        ("resume brief", work_dir / "resume_brief.json"),
        ("surface fit manifest", manifest),
        ("blank plate generation prompts", prompt_file),
    ]
    for label, path in required_no_credit_files:
        if not path.exists():
            blockers.append(f"missing {label}: {path}")
    if not voice_text.exists():
        if selected_script.exists():
            warnings.append(f"{voice_text.name} missing; voice generation can use selected_script.md but a cleaned voice script is preferred")
        else:
            blockers.append(f"missing voice script: {voice_text}")

    if not creative_report.get("passed"):
        blockers.append("creative_gate is missing or failed")
    if not script_report.get("passed"):
        blockers.append("script_qa is missing or failed")

    # These gates usually require generated plates and fitted previews, so they
    # are reported as readiness signals rather than pre-approval blockers.
    production_gate_status = {
        "creative_qa": bool(creative_qa_report.get("passed")),
        "plate_qa": bool(plate_report.get("passed")),
        "surface_fit_qa": bool(surface_report.get("passed")),
    }
    if not production_gate_status["creative_qa"]:
        warnings.append("creative_qa still needs to pass after deterministic overlays/plates exist")
    if not production_gate_status["plate_qa"]:
        warnings.append("plate_qa still needs clean blank paper/tablet plates")
    if not production_gate_status["surface_fit_qa"]:
        warnings.append("surface_fit_qa still needs full-size fitted preview review for the production plates")

    for tool in ("ffmpeg", "ffprobe"):
        try:
            find_exe(tool)
        except Exception as exc:
            blockers.append(f"{tool} unavailable: {exc}")

    creative_approved = bool(metadata.get("creativeGateApproved"))
    blocked_reason = ""
    if run_id and not creative_approved:
        blocked_reason = f"waiting for creative approval phrase: {approval_phrase}"
    elif not run_id:
        blocked_reason = "no run id supplied; paid API commands must be run from a durable approved run"

    commands: list[str] = []
    if run_id:
        commands.append(f'py -3 marketing_agent\\signal_growth_pipeline.py approve-creative --run-id {run_id} --phrase "{approval_phrase}"')
        commands.append(f"py -3 marketing_agent\\signal_growth_pipeline.py prepare-plate-intake --run-id {run_id} --host {args.host or '192.168.2.10'} --port {args.port}")
        commands.append("# Generate clean blank paper/tablet plates from blank_plate_generation_prompts.md, then ingest the downloaded image/video files into the exact surface_fit.json targets.")
        commands.append(f"py -3 marketing_agent\\signal_growth_pipeline.py ingest-plate-files --run-id {run_id} --tablet-source <clean_tablet_or_screen_plate> --paper-source <clean_paper_plate>")
        commands.append(f"py -3 marketing_agent\\signal_growth_pipeline.py plate-qa --work-dir {work_dir} --run-id {run_id}")
        commands.append(f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-preview --work-dir {work_dir} --run-id {run_id}")
        commands.append(f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-review --work-dir {work_dir} --run-id {run_id} --host {args.host or '192.168.2.10'} --port {args.port}")
        commands.append("# Inspect the extracted plate frames and full-size fitted previews. Continue only if the resume is pinned into the page/screen, readable, and no generated text/watermarks/fake hands appear.")
        commands.append(f"py -3 marketing_agent\\signal_growth_pipeline.py plate-qa --work-dir {work_dir} --run-id {run_id} --visual-reviewed")
        commands.append(f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-qa --work-dir {work_dir} --run-id {run_id} --visual-reviewed")
        commands.append(f"py -3 marketing_agent\\signal_growth_pipeline.py build-surface-teardown --run-id {run_id} --visual-reviewed")
        commands.append(f"py -3 marketing_agent\\signal_growth_pipeline.py gold-readiness --run-id {run_id}")
        commands.append(f"py -3 marketing_agent\\signal_growth_pipeline.py review --run-id {run_id} --host {args.host or '192.168.2.10'} --port {args.port}")
    else:
        commands.extend(
            [
                f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-preview --work-dir {work_dir}",
                f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-animatic --work-dir {work_dir} --out {animatic_path}",
                f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-qa --work-dir {work_dir} --visual-reviewed",
            ]
        )

    report = {
        "runId": run_id,
        "status": status,
        "title": title,
        "workDir": str(work_dir),
        "readyAfterApproval": not blockers,
        "creativeApproved": creative_approved,
        "blockedReason": blocked_reason,
        "blockers": blockers,
        "warnings": warnings,
        "approvalPhrase": approval_phrase,
        "expectedOutputs": {
            "audio": str(audio_path),
            "animatic": str(animatic_path),
            "finalVideo": str(final_path),
            "contactSheet": str(sheet_path),
        },
        "gates": {
            "creative_gate": bool(creative_report.get("passed")),
            "script_qa": bool(script_report.get("passed")),
            **production_gate_status,
        },
        "commands": commands,
    }
    out_path = work_dir / "post_approval_surface_build_plan.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    commands_path = work_dir / "post_approval_surface_commands.md"
    commands_path.write_text(
        "# Post-Approval Surface Build Commands\n\n"
        + "\n".join(f"```powershell\n{command}\n```" if not command.startswith("#") else command for command in commands)
        + "\n",
        encoding="utf-8",
    )
    report["planPath"] = str(out_path)
    report["commandsPath"] = str(commands_path)
    emit(report)
    if blockers:
        raise SystemExit(1)


def collect_surface_asset_status(work_dir: Path, manifest: Path) -> dict[str, Any]:
    status: dict[str, Any] = {
        "manifest": str(manifest),
        "exists": manifest.exists(),
        "surfaces": [],
        "missingFrames": [],
        "missingOverlays": [],
    }
    if not manifest.exists():
        return status
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception as exc:
        status["error"] = str(exc)
        return status
    surfaces = data.get("surfaces") if isinstance(data.get("surfaces"), list) else []
    for index, surface in enumerate(surfaces, start=1):
        if not isinstance(surface, dict):
            continue
        frame = resolve_surface_asset(work_dir, surface.get("frame") or surface.get("image"))
        overlay = resolve_surface_asset(work_dir, surface.get("overlay") or surface.get("resumeOverlay"))
        item = {
            "index": index,
            "surface": surface.get("surface") or surface.get("type"),
            "frame": str(frame) if frame else None,
            "frameExists": bool(frame and frame.exists()),
            "overlay": str(overlay) if overlay else None,
            "overlayExists": bool(overlay and overlay.exists()),
            "beat": surface.get("beat"),
        }
        if not item["frameExists"]:
            if item["frame"] not in status["missingFrames"]:
                status["missingFrames"].append(item["frame"])
        if not item["overlayExists"]:
            if item["overlay"] not in status["missingOverlays"]:
                status["missingOverlays"].append(item["overlay"])
        status["surfaces"].append(item)
    return status


def prepare_plate_intake(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve() if args.work_dir else run_folder(args.run_id)
    manifest = work_dir / (args.manifest_name or "surface_fit.json")
    prompt_file = work_dir / (args.prompt_name or "blank_plate_generation_prompts.md")
    surface_assets = collect_surface_asset_status(work_dir, manifest)
    unique_frames: list[str] = []
    for surface in surface_assets.get("surfaces", []):
        frame = surface.get("frame")
        if frame and frame not in unique_frames:
            unique_frames.append(frame)

    prompt_text = prompt_file.read_text(encoding="utf-8", errors="ignore") if prompt_file.exists() else ""
    blockers: list[str] = []
    if not surface_assets.get("exists"):
        blockers.append(f"surface fit manifest missing: {manifest}")
    if not unique_frames:
        blockers.append("no plate frame targets found in surface_fit.json")
    if not prompt_file.exists():
        blockers.append(f"blank plate prompt file missing: {prompt_file}")

    intake = {
        "runId": args.run_id,
        "workDir": str(work_dir),
        "manifest": str(manifest),
        "promptFile": str(prompt_file),
        "passed": not blockers,
        "blockers": blockers,
        "requiredPlateFiles": [
            {
                "path": frame,
                "filename": Path(frame).name,
                "exists": Path(frame).exists(),
                "usedBySurfaces": [
                    surface.get("index")
                    for surface in surface_assets.get("surfaces", [])
                    if surface.get("frame") == frame
                ],
            }
            for frame in unique_frames
        ],
        "rules": [
            "Use clean blank paper/tablet/screen plates only.",
            "No readable generated text, logos, UI, captions, watermarks, hands writing, or fake stylus edits.",
            "All paper/screen corners must remain visible and unobstructed.",
            "Save/download files using the exact filenames listed here.",
            "After intake, run plate-qa, surface-fit-preview, and surface-fit-review before any --visual-reviewed pass.",
        ],
        "nextCommands": [
            f"py -3 marketing_agent\\signal_growth_pipeline.py ingest-plate-files --run-id {args.run_id} --tablet-source <downloaded_tablet_plate> --paper-source <downloaded_paper_plate>" if args.run_id else f"py -3 marketing_agent\\signal_growth_pipeline.py ingest-plate-files --work-dir {work_dir} --tablet-source <downloaded_tablet_plate> --paper-source <downloaded_paper_plate>",
            f"py -3 marketing_agent\\signal_growth_pipeline.py plate-qa --work-dir {work_dir} --run-id {args.run_id}" if args.run_id else f"py -3 marketing_agent\\signal_growth_pipeline.py plate-qa --work-dir {work_dir}",
            f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-preview --work-dir {work_dir} --run-id {args.run_id}" if args.run_id else f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-preview --work-dir {work_dir}",
            f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-review --work-dir {work_dir} --run-id {args.run_id} --host {args.host or '192.168.2.10'} --port {args.port}" if args.run_id else f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-review --work-dir {work_dir} --host {args.host or '192.168.2.10'} --port {args.port}",
        ],
    }
    json_path = work_dir / (args.json_name or "plate_intake_checklist.json")
    md_path = work_dir / (args.md_name or "plate_intake_checklist.md")
    json_path.write_text(json.dumps(intake, indent=2, ensure_ascii=True), encoding="utf-8")
    plate_rows = "\n".join(
        f"- `{item['filename']}` -> `{item['path']}` ({'exists' if item['exists'] else 'missing'}; surfaces {', '.join(str(value) for value in item['usedBySurfaces'])})"
        for item in intake["requiredPlateFiles"]
    )
    rule_rows = "\n".join(f"- {rule}" for rule in intake["rules"])
    command_rows = "\n".join(f"```powershell\n{command}\n```" for command in intake["nextCommands"])
    prompt_section = prompt_text.strip() or "_No prompt file found._"
    md_path.write_text(
        f"""# Plate Intake Checklist

Run: `{args.run_id or work_dir.name}`

Passed: `{intake['passed']}`

## Required Plate Files

{plate_rows or '- None'}

## Rules

{rule_rows}

## Plate Prompts

{prompt_section}

## After Download

{command_rows}
""",
        encoding="utf-8",
    )
    intake["jsonPath"] = str(json_path)
    intake["mdPath"] = str(md_path)
    emit(intake)
    if blockers:
        raise SystemExit(1)


def ingest_plate_source(source: Path, target: Path, extract_time: float, overwrite: bool) -> dict[str, Any]:
    source = source.resolve()
    target = target.resolve()
    if not source.exists():
        raise SystemExit(f"Plate source not found: {source}")
    if target.exists() and not overwrite:
        return {
            "source": str(source),
            "target": str(target),
            "status": "skipped_exists",
            "note": "Target already exists. Pass --overwrite to replace it.",
        }
    target.parent.mkdir(parents=True, exist_ok=True)
    image_exts = {".png", ".jpg", ".jpeg", ".webp"}
    video_exts = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
    if source.suffix.lower() in image_exts:
        with Image.open(source) as image:
            image.convert("RGB").save(target)
        method = "image_convert"
    elif source.suffix.lower() in video_exts:
        subprocess.run(
            [
                find_exe("ffmpeg"),
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{max(0.0, extract_time):.3f}",
                "-i",
                str(source),
                "-frames:v",
                "1",
                str(target),
            ],
            check=True,
        )
        method = "video_frame_extract"
    else:
        raise SystemExit(f"Unsupported plate source type: {source.suffix}")

    width = height = 0
    try:
        with Image.open(target) as image:
            width, height = image.size
    except Exception as exc:
        raise SystemExit(f"Could not inspect ingested plate {target}: {exc}")
    warnings: list[str] = []
    if width < 720 or height < 1280:
        warnings.append(f"plate is small: {width}x{height}")
    if height <= width:
        warnings.append(f"plate is not vertical: {width}x{height}")
    return {
        "source": str(source),
        "target": str(target),
        "status": "written",
        "method": method,
        "width": width,
        "height": height,
        "warnings": warnings,
    }


def ingest_plate_files(args: argparse.Namespace) -> None:
    work_dir = Path(args.work_dir).resolve() if args.work_dir else run_folder(args.run_id)
    manifest = work_dir / (args.manifest_name or "surface_fit.json")
    surface_assets = collect_surface_asset_status(work_dir, manifest)
    if not surface_assets.get("exists"):
        raise SystemExit(f"surface fit manifest missing: {manifest}")

    sources_by_type: dict[str, Path] = {}
    if args.tablet_source:
        sources_by_type["tablet"] = Path(args.tablet_source)
        sources_by_type["screen"] = Path(args.tablet_source)
        sources_by_type["monitor"] = Path(args.tablet_source)
        sources_by_type["laptop"] = Path(args.tablet_source)
    if args.paper_source:
        sources_by_type["paper"] = Path(args.paper_source)

    results: list[dict[str, Any]] = []
    blockers: list[str] = []
    seen_targets: set[str] = set()
    for surface in surface_assets.get("surfaces", []):
        frame = surface.get("frame")
        surface_type = str(surface.get("surface") or "").lower()
        if not frame or frame in seen_targets:
            continue
        seen_targets.add(frame)
        source = sources_by_type.get(surface_type)
        if not source:
            blockers.append(f"missing source argument for {surface_type} plate target: {frame}")
            continue
        results.append(ingest_plate_source(source, Path(frame), args.extract_time, args.overwrite))

    report = {
        "runId": args.run_id,
        "workDir": str(work_dir),
        "manifest": str(manifest),
        "passed": not blockers and all(not item.get("warnings") for item in results if item.get("status") == "written"),
        "blockers": blockers,
        "results": results,
        "nextCommands": [
            f"py -3 marketing_agent\\signal_growth_pipeline.py plate-qa --work-dir {work_dir} --run-id {args.run_id}" if args.run_id else f"py -3 marketing_agent\\signal_growth_pipeline.py plate-qa --work-dir {work_dir}",
            f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-preview --work-dir {work_dir} --run-id {args.run_id}" if args.run_id else f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-preview --work-dir {work_dir}",
            f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-review --work-dir {work_dir} --run-id {args.run_id} --host {args.host or '192.168.2.10'} --port {args.port}" if args.run_id else f"py -3 marketing_agent\\signal_growth_pipeline.py surface-fit-review --work-dir {work_dir} --host {args.host or '192.168.2.10'} --port {args.port}",
        ],
    }
    json_path = work_dir / (args.json_name or "plate_ingest_report.json")
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    report["jsonPath"] = str(json_path)
    if args.run_id:
        conn = db()
        get_run(conn, args.run_id)
        log_event(conn, args.run_id, "plate_files_ingested", report)
        conn.commit()
    emit(report)
    if blockers:
        raise SystemExit(1)


def gold_readiness(args: argparse.Namespace) -> None:
    run_id = args.run_id
    if run_id:
        work_dir = Path(args.work_dir).resolve() if args.work_dir else run_folder(run_id)
        conn = db()
        row = get_run(conn, run_id)
        metadata = json.loads(row["metadata_json"] or "{}")
        row_status = row["status"]
        title = row["title"]
        video_path = row["video_path"]
        conn.close()
    else:
        if not args.work_dir:
            raise SystemExit("Provide --run-id or --work-dir")
        work_dir = Path(args.work_dir).resolve()
        metadata = {}
        row_status = "NO_DB_RUN"
        title = work_dir.name
        video_path = None

    brief = load_resume_brief(work_dir) if (work_dir / "resume_brief.json").exists() else {}
    format_name = str(brief.get("format", "") or "").strip()
    is_screen = format_name == "screen_recording_teardown"
    manifest = work_dir / (args.manifest_name or "surface_fit.json")
    gate_names = ("creative_gate", "script_qa", "screen_visual_qa") if is_screen else ("creative_gate", "script_qa", "creative_qa", "plate_qa", "surface_fit_qa")
    gates = {name: read_quality_gate(work_dir, name) for name in gate_names}
    gate_summary = {
        name: {
            "present": report is not None,
            "passed": bool((report or {}).get("passed")),
            "blockers": (report or {}).get("blockers", []),
        }
        for name, report in gates.items()
    }
    surface_assets = collect_surface_asset_status(work_dir, manifest) if not is_screen else {"manifest": str(manifest), "exists": manifest.exists(), "surfaces": [], "missingFrames": [], "missingOverlays": []}
    default_final_name = "signal_gold_screen_teardown_jordan_v1.mp4" if is_screen else "signal_gold_surface_teardown_v1.mp4"
    default_sheet_name = "signal_gold_screen_teardown_jordan_v1_contact_sheet.png" if is_screen else "signal_gold_surface_teardown_v1_contact_sheet.png"
    final_video = Path(video_path).resolve() if video_path else work_dir / (args.final_name or default_final_name)
    contact_sheet_path = work_dir / (args.contact_sheet_name or default_sheet_name)
    audio_path = work_dir / (args.audio_name or "abby_voice_full.mp3")
    approval_phrase = (
        metadata.get("creativeApprovalPhrase")
        or (gates["creative_gate"] or {}).get("approvalPhrase")
        or (f"APPROVE CREATIVE GATE {run_id}" if run_id else "")
    )

    blockers: list[str] = []
    if not gate_summary["creative_gate"]["passed"]:
        blockers.append("creative_gate missing or failed")
    if not gate_summary["script_qa"]["passed"]:
        blockers.append("script_qa missing or failed")
    if not is_screen and not gate_summary["creative_qa"]["passed"]:
        blockers.append("creative_qa missing or failed")
    if is_screen and not gate_summary["screen_visual_qa"]["passed"]:
        blockers.append("screen_visual_qa missing or failed")
    if run_id and not metadata.get("creativeGateApproved"):
        blockers.append(f"creative approval not recorded; expected phrase: {approval_phrase}")
    if not is_screen:
        for missing in surface_assets.get("missingFrames", []):
            blockers.append(f"clean plate missing: {missing}")
        for missing in surface_assets.get("missingOverlays", []):
            blockers.append(f"deterministic overlay missing: {missing}")
        if not gate_summary["plate_qa"]["passed"]:
            blockers.append("plate_qa pending or failed")
        if not gate_summary["surface_fit_qa"]["passed"]:
            blockers.append("surface_fit_qa pending or failed")
    if not final_video.exists():
        blockers.append(f"final video missing: {final_video}")
    if final_video.exists() and not contact_sheet_path.exists():
        blockers.append(f"final contact sheet missing: {contact_sheet_path}")

    next_action = "Review final video in Codex and approve post only if it is gold-standard."
    format_gate_failed = bool(is_screen and not gate_summary["screen_visual_qa"]["passed"]) or bool(not is_screen and not gate_summary["creative_qa"]["passed"])
    if not gate_summary["creative_gate"]["passed"] or not gate_summary["script_qa"]["passed"] or format_gate_failed:
        next_action = "Fix creative/script/storyboard gates before any paid generation."
    elif run_id and not metadata.get("creativeGateApproved"):
        next_action = f"Approve the creative gate in Codex with: {approval_phrase}"
    elif not is_screen and surface_assets.get("missingFrames"):
        next_action = "Generate or source clean blank paper/tablet plates with no readable generated text, then rerun plate QA."
    elif not is_screen and not gate_summary["plate_qa"]["passed"]:
        next_action = "Run plate-qa, inspect extracted frames, then rerun with --visual-reviewed if clean."
    elif not is_screen and not gate_summary["surface_fit_qa"]["passed"]:
        next_action = "Run surface-fit-review, inspect plate/overlay/fitted result, then run surface-fit-qa --visual-reviewed if clean."
    elif not audio_path.exists() or not final_video.exists():
        next_action = "Run build-screen-teardown to generate Abby voice, final MP4, contact sheet, and final QA." if is_screen else "Run build-surface-teardown --visual-reviewed to generate Abby voice, final MP4, contact sheet, and final QA."
    elif row_status != "AWAITING_CODEX_APPROVAL":
        next_action = "Run final qa/review so the video enters AWAITING_CODEX_APPROVAL."

    report = {
        "runId": run_id,
        "status": row_status,
        "title": title,
        "format": format_name,
        "workDir": str(work_dir),
        "readyForFinalCodexReview": not blockers,
        "blockers": blockers,
        "nextAction": next_action,
        "approvalPhrase": approval_phrase,
        "creativeApproved": bool(metadata.get("creativeGateApproved")),
        "gates": gate_summary,
        "surfaceAssets": surface_assets,
        "artifacts": {
            "audio": {"path": str(audio_path), "exists": audio_path.exists()},
            "finalVideo": {"path": str(final_video), "exists": final_video.exists()},
            "contactSheet": {"path": str(contact_sheet_path), "exists": contact_sheet_path.exists()},
            "surfaceFitReview": {
                "path": str(work_dir / "surface_fit_review.html"),
                "exists": (work_dir / "surface_fit_review.html").exists(),
            },
        },
    }
    json_path = work_dir / (args.json_name or "gold_readiness_report.json")
    md_path = work_dir / (args.md_name or "gold_readiness_report.md")
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    gate_lines = "\n".join(
        f"- `{name}`: {'pass' if details['passed'] else 'pending/fail'}"
        for name, details in gate_summary.items()
    )
    blocker_lines = "\n".join(f"- {blocker}" for blocker in blockers) if blockers else "- None"
    artifact_lines = "\n".join(
        f"- `{label}`: {'exists' if details['exists'] else 'missing'} - `{details['path']}`"
        for label, details in report["artifacts"].items()
    )
    md_path.write_text(
        f"""# Gold Readiness Report

Run: `{run_id or work_dir.name}`

Status: `{row_status}`

Ready for final Codex review: `{report['readyForFinalCodexReview']}`

## Next Action

{next_action}

## Gates

{gate_lines}

## Blockers

{blocker_lines}

## Artifacts

{artifact_lines}
""",
        encoding="utf-8",
    )
    report["jsonPath"] = str(json_path)
    report["mdPath"] = str(md_path)
    emit(report)


def build_surface_teardown(args: argparse.Namespace) -> None:
    run_id = args.run_id
    work_dir = Path(args.work_dir).resolve() if args.work_dir else run_folder(run_id)
    require_creative_gate_for_paid_step(run_id, args.allow_unapproved_creative)

    voice_text = work_dir / (args.voice_text_name or "voice_full_script.txt")
    if not voice_text.exists():
        selected_script = work_dir / "selected_script.md"
        if selected_script.exists():
            voice_text = selected_script
        else:
            raise SystemExit(f"Missing voice script: {voice_text}")

    manifest = work_dir / (args.manifest_name or "surface_fit.json")
    if not manifest.exists():
        raise SystemExit(f"Missing surface fit manifest: {manifest}")
    manifest_report = validate_surface_fit_manifest(
        work_dir,
        manifest,
        min_area_ratio=args.min_area_ratio,
        max_area_ratio=args.max_area_ratio,
    )
    if manifest_report.get("blockers"):
        emit(manifest_report)
        raise SystemExit(1)

    audio_path = work_dir / (args.audio_name or "abby_voice_full.mp3")
    final_path = work_dir / (args.final_name or "signal_gold_surface_teardown_v1.mp4")
    sheet_path = work_dir / (args.contact_sheet_name or "signal_gold_surface_teardown_v1_contact_sheet.png")
    preview_dir = work_dir / (args.preview_dir_name or "surface_fit_previews")

    if args.voice_test_only:
        test_text = work_dir / "voice_test_abby_10s.txt"
        if not test_text.exists():
            raise SystemExit(f"Missing voice test file: {test_text}")
        test_out = work_dir / "abby_voice_test_10s.mp3"
        generate_voice(
            argparse.Namespace(
                text=None,
                text_file=str(test_text),
                out=str(test_out),
                run_id=None,
                voice_id=None,
                model_id=args.model_id,
                stability=args.stability,
                similarity=args.similarity,
                style=args.style,
                speed=args.speed,
                allow_unapproved_creative=args.allow_unapproved_creative,
            )
        )
        conn = db()
        log_event(conn, run_id, "surface_voice_test_generated", {"audio": str(test_out)})
        conn.commit()
        return

    surface_fit_preview(
        argparse.Namespace(
            work_dir=str(work_dir),
            run_id=run_id,
            manifest=str(manifest),
            out_dir=str(preview_dir),
            min_area_ratio=args.min_area_ratio,
            max_area_ratio=args.max_area_ratio,
        )
    )

    if args.visual_reviewed:
        plate_qa(
            argparse.Namespace(
                work_dir=str(work_dir),
                video=args.plate,
                run_id=run_id,
                visual_reviewed=True,
                generated_text_ok=False,
            )
        )
        creative_qa(
            argparse.Namespace(
                work_dir=str(work_dir),
                run_id=run_id,
                format=args.creative_format,
            )
        )
        surface_fit_qa(
            argparse.Namespace(
                work_dir=str(work_dir),
                run_id=run_id,
                manifest=str(manifest),
                visual_reviewed=True,
                min_area_ratio=args.min_area_ratio,
                max_area_ratio=args.max_area_ratio,
            )
        )
    else:
        missing = [
            name
            for name in ("creative_qa", "plate_qa", "surface_fit_qa")
            if not (read_quality_gate(work_dir, name) or {}).get("passed")
        ]
        if missing:
            raise SystemExit(
                "Surface build preview is ready, but visual review gates are still missing: "
                + ", ".join(missing)
                + ". Inspect the full-size fitted previews, then rerun with --visual-reviewed if they pass."
            )

    if not audio_path.exists() or args.force:
        generate_voice(
            argparse.Namespace(
                text=None,
                text_file=str(voice_text),
                out=str(audio_path),
                run_id=run_id,
                voice_id=None,
                model_id=args.model_id,
                stability=args.stability,
                similarity=args.similarity,
                style=args.style,
                speed=args.speed,
                allow_unapproved_creative=args.allow_unapproved_creative,
            )
        )

    surface_fit_animatic(
        argparse.Namespace(
            work_dir=str(work_dir),
            run_id=run_id,
            manifest=str(manifest),
            preview_dir=str(preview_dir),
            out=str(final_path),
            audio=str(audio_path),
            default_duration=args.default_duration,
            min_area_ratio=args.min_area_ratio,
            max_area_ratio=args.max_area_ratio,
        )
    )
    qa(argparse.Namespace(video=str(final_path), run_id=run_id, write=True))
    contact_sheet(
        argparse.Namespace(
            video=str(final_path),
            out=str(sheet_path),
            times=None,
            count=9,
            columns=3,
            thumb_width=360,
            label="Gold surface teardown",
        )
    )

    audio_duration = media_duration(audio_path)
    final_duration = media_duration(final_path)
    conn = db()
    update_run(conn, run_id, status="AWAITING_CODEX_APPROVAL", video_path=str(final_path), audio_path=str(audio_path))
    log_event(
        conn,
        run_id,
        "surface_teardown_built",
        {
            "finalVideo": str(final_path),
            "audio": str(audio_path),
            "contactSheet": str(sheet_path),
            "previewDir": str(preview_dir),
            "audioDurationSec": audio_duration,
            "finalDurationSec": final_duration,
        },
    )
    conn.commit()
    emit(
        {
            "status": "AWAITING_CODEX_APPROVAL",
            "runId": run_id,
            "video": str(final_path),
            "audio": str(audio_path),
            "contactSheet": str(sheet_path),
            "previewDir": str(preview_dir),
            "audioDurationSec": round(audio_duration, 3),
            "finalDurationSec": round(final_duration, 3),
        }
    )


def build_screen_teardown(args: argparse.Namespace) -> None:
    run_id = args.run_id
    work_dir = Path(args.work_dir).resolve() if args.work_dir else run_folder(run_id)
    require_creative_gate_for_paid_step(run_id, args.allow_unapproved_creative)

    input_json = work_dir / "screen_teardown_gold_jordan.json"
    voice_text = work_dir / "voice_full_script.txt"
    if not input_json.exists():
        raise SystemExit(f"Missing screen teardown JSON: {input_json}")
    if not voice_text.exists():
        raise SystemExit(f"Missing full voice script: {voice_text}")

    audio_path = work_dir / (args.audio_name or "abby_voice_full.mp3")
    visual_path = work_dir / (args.visual_name or "gold_screen_visual_only.mp4")
    final_path = work_dir / (args.final_name or "signal_gold_screen_teardown_jordan_v1.mp4")
    sheet_path = work_dir / (args.contact_sheet_name or "signal_gold_screen_teardown_jordan_v1_contact_sheet.png")

    if args.voice_test_only:
        test_text = work_dir / "voice_test_abby_10s.txt"
        if not test_text.exists():
            raise SystemExit(f"Missing voice test file: {test_text}")
        test_out = work_dir / "abby_voice_test_10s.mp3"
        ns = argparse.Namespace(
            text=None,
            text_file=str(test_text),
            out=str(test_out),
            run_id=None,
            voice_id=None,
            model_id=args.model_id,
            stability=args.stability,
            similarity=args.similarity,
            style=args.style,
            speed=args.speed,
            allow_unapproved_creative=args.allow_unapproved_creative,
        )
        generate_voice(ns)
        conn = db()
        log_event(conn, run_id, "voice_test_generated", {"audio": str(test_out)})
        conn.commit()
        return

    if not audio_path.exists() or args.force:
        ns = argparse.Namespace(
            text=None,
            text_file=str(voice_text),
            out=str(audio_path),
            run_id=run_id,
            voice_id=None,
            model_id=args.model_id,
            stability=args.stability,
            similarity=args.similarity,
            style=args.style,
            speed=args.speed,
            allow_unapproved_creative=args.allow_unapproved_creative,
        )
        generate_voice(ns)

    audio_duration = media_duration(audio_path)
    render_duration = args.duration or max(24.0, min(32.0, audio_duration))
    subprocess.run(
        [
            find_exe("node"),
            str(ROOT / "marketing_agent" / "screen_teardown_renderer.mjs"),
            "--input",
            str(input_json),
            "--out",
            str(visual_path),
            "--mode",
            "video",
            "--duration",
            f"{render_duration:.3f}",
        ],
        cwd=str(ROOT),
        check=True,
    )

    subprocess.run(
        [
            find_exe("ffmpeg"),
            "-y",
            "-i",
            str(visual_path),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(final_path),
        ],
        check=True,
    )

    screen_visual_qa(
        argparse.Namespace(
            work_dir=str(work_dir),
            run_id=run_id,
            input=str(input_json),
            contact_sheet=str(work_dir / "screen_teardown_storyboard_contact_sheet.png"),
            visual_reviewed=True,
        )
    )
    qa(argparse.Namespace(video=str(final_path), run_id=run_id, write=True))
    contact_sheet(
        argparse.Namespace(
            video=str(final_path),
            out=str(sheet_path),
            times=None,
            count=9,
            columns=3,
            thumb_width=360,
            label="Gold screen teardown",
        )
    )

    conn = db()
    update_run(conn, run_id, status="AWAITING_CODEX_APPROVAL", video_path=str(final_path), audio_path=str(audio_path))
    log_event(
        conn,
        run_id,
        "screen_teardown_built",
        {
            "finalVideo": str(final_path),
            "audio": str(audio_path),
            "visual": str(visual_path),
            "contactSheet": str(sheet_path),
            "audioDurationSec": audio_duration,
            "renderDurationSec": render_duration,
        },
    )
    conn.commit()
    emit(
        {
            "status": "AWAITING_CODEX_APPROVAL",
            "runId": run_id,
            "video": str(final_path),
            "audio": str(audio_path),
            "contactSheet": str(sheet_path),
            "audioDurationSec": round(audio_duration, 3),
            "renderDurationSec": round(render_duration, 3),
        }
    )


def ffprobe_json(video: Path) -> dict[str, Any]:
    try:
        ffprobe = find_exe("ffprobe")
        proc = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(video),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return json.loads(proc.stdout)
    except Exception:
        import imageio.v3 as iio

        meta = iio.immeta(video)
        width, height = meta.get("size") or meta.get("source_size") or (0, 0)
        fps = float(meta.get("fps") or 0)
        duration = float(meta.get("duration") or 0)
        streams: list[dict[str, Any]] = [
            {
                "codec_type": "video",
                "codec_name": meta.get("codec", ""),
                "width": width,
                "height": height,
                "avg_frame_rate": f"{int(round(fps * 1000))}/1000" if fps else "0/1",
            }
        ]
        if meta.get("audio_codec"):
            streams.append(
                {
                    "codec_type": "audio",
                    "codec_name": meta.get("audio_codec", ""),
                    "sample_rate": str(meta.get("audio_fps") or 48000),
                }
            )
        return {"streams": streams, "format": {"duration": str(duration), "size": str(video.stat().st_size)}}


def frame_rate(stream: dict[str, Any]) -> float:
    raw = stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0/1"
    if "/" in raw:
        num, den = raw.split("/", 1)
        return float(num) / float(den or 1)
    return float(raw)


def qa(args: argparse.Namespace) -> None:
    video = Path(args.video).resolve()
    if not video.exists():
        raise SystemExit(f"Video not found: {video}")
    gate_blockers: list[str] = []
    gate_reports: dict[str, Any] = {}
    required_gates: tuple[str, ...] = ()
    if args.run_id:
        work_dir = run_folder(args.run_id)
        required_gates = required_quality_gate_names(work_dir)
        gate_blockers = require_quality_gates(work_dir)
        for gate in required_gates:
            gate_reports[gate] = read_quality_gate(work_dir, gate)
    data = ffprobe_json(video)
    streams = data.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    blockers: list[str] = []
    if not video_stream:
        blockers.append("missing video stream")
    if not audio_stream:
        blockers.append("missing audio stream")
    if video_stream:
        fps = frame_rate(video_stream)
        if video_stream.get("codec_name") != "h264":
            blockers.append(f"video codec is {video_stream.get('codec_name')}, expected h264")
        if int(video_stream.get("width", 0)) != 1080 or int(video_stream.get("height", 0)) != 1920:
            blockers.append(f"video is {video_stream.get('width')}x{video_stream.get('height')}, expected 1080x1920")
        if abs(fps - 30) > 0.15:
            blockers.append(f"video is {fps:.3f}fps, expected 30fps")
    if audio_stream:
        if audio_stream.get("codec_name") != "aac":
            blockers.append(f"audio codec is {audio_stream.get('codec_name')}, expected aac")
        sample_rate = int(audio_stream.get("sample_rate", 0) or 0)
        if sample_rate not in {44100, 48000}:
            blockers.append(f"audio sample rate is {sample_rate}, expected 44100 or 48000")
    duration = float(data.get("format", {}).get("duration") or 0)
    if duration < 5:
        blockers.append(f"duration is {duration:.2f}s")
    blockers.extend(gate_blockers)

    report = {
        "video": str(video),
        "passed": not blockers,
        "blockers": blockers,
        "durationSec": round(duration, 3),
        "videoCodec": video_stream.get("codec_name") if video_stream else None,
        "width": video_stream.get("width") if video_stream else None,
        "height": video_stream.get("height") if video_stream else None,
        "fps": round(frame_rate(video_stream), 3) if video_stream else None,
        "audioCodec": audio_stream.get("codec_name") if audio_stream else None,
        "sampleRate": audio_stream.get("sample_rate") if audio_stream else None,
        "fileBytes": video.stat().st_size,
        "checkedAt": utc_now(),
        "qualityGates": {
            gate: {
                "present": gate_reports.get(gate) is not None,
                "passed": bool((gate_reports.get(gate) or {}).get("passed")),
                "blockers": (gate_reports.get(gate) or {}).get("blockers", []),
            }
            for gate in required_gates
        }
        if args.run_id
        else {},
    }

    if args.write:
        out = video.with_suffix(video.suffix + ".qa.json")
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["reportPath"] = str(out)

    if args.run_id:
        conn = db()
        get_run(conn, args.run_id)
        status = "AWAITING_CODEX_APPROVAL" if report["passed"] else "FAILED"
        update_run(conn, args.run_id, status=status, video_path=str(video), qa_json=json.dumps(report))
        log_event(conn, args.run_id, "qa", report)
        conn.commit()
        report["runId"] = args.run_id
        report["status"] = status

    emit(report)
    if blockers:
        raise SystemExit(1)


def review(args: argparse.Namespace) -> None:
    conn = db()
    row = get_run(conn, args.run_id)
    metadata = json.loads(row["metadata_json"] or "{}")
    qa_report = json.loads(row["qa_json"] or "{}")
    video_path = row["video_path"]
    if not video_path:
        raise SystemExit("No video_path stored for this run yet.")
    video = Path(video_path)
    if not video.exists():
        raise SystemExit(f"Stored video path does not exist: {video}")
    mobile_url = f"http://{args.host}:{args.port}/{video.name}" if args.host else None
    packet = {
        "runId": row["id"],
        "status": row["status"],
        "title": row["title"],
        "videoPath": str(video),
        "mobileUrl": mobile_url,
        "platforms": metadata.get("platforms", ["youtube_shorts", "tiktok", "instagram_reels"]),
        "cta": "Run the free Signal score before you apply.",
        "landingUrl": row["landing_url"],
        "approvalPhrase": metadata.get("approvalPhrase", f"APPROVE POST {row['id']}"),
        "qa": qa_report,
        "publishBlocked": row["status"] != "APPROVED",
    }
    emit(packet)


def approve(args: argparse.Namespace) -> None:
    expected = f"APPROVE POST {args.run_id}"
    if args.phrase.strip() != expected:
        raise SystemExit(f"Approval phrase mismatch. Expected exactly: {expected}")
    conn = db()
    row = get_run(conn, args.run_id)
    if row["status"] != "AWAITING_CODEX_APPROVAL":
        raise SystemExit(f"Run must be AWAITING_CODEX_APPROVAL before approval. Current status: {row['status']}")
    update_run(conn, args.run_id, status="APPROVED")
    log_event(conn, args.run_id, "approved", {"reviewer": "codex-chat", "phrase": args.phrase})
    conn.commit()
    emit({"runId": args.run_id, "status": "APPROVED", "publishStillRequiresPublisherCommand": True})


def mark_status(args: argparse.Namespace) -> None:
    conn = db()
    get_run(conn, args.run_id)
    update_run(conn, args.run_id, status=args.status)
    log_event(conn, args.run_id, "status_changed", {"status": args.status, "reason": args.reason or ""})
    conn.commit()
    emit({"runId": args.run_id, "status": args.status})


def show_state(args: argparse.Namespace) -> None:
    conn = db()
    if args.run_id:
        row = dict(get_run(conn, args.run_id))
        row["metadata_json"] = json.loads(row["metadata_json"] or "{}")
        row["qa_json"] = json.loads(row["qa_json"] or "{}")
        emit(row)
        return
    rows = [dict(row) for row in conn.execute("SELECT id, topic, title, status, video_path, updated_at FROM video_runs ORDER BY updated_at DESC LIMIT ?", (args.limit,))]
    emit({"runs": rows})


def create_batch(args: argparse.Namespace) -> None:
    topics: list[str] = []
    if args.topics:
        topics.extend(args.topics)
    if args.topics_file:
        topics.extend(
            line.strip()
            for line in Path(args.topics_file).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    if not topics:
        raise SystemExit("Provide --topics or --topics-file")

    created: list[dict[str, Any]] = []
    for topic in topics:
        ns = argparse.Namespace(topic=topic, title=None, landing_url=args.landing_url)
        before = set(path.name for path in RUNS_DIR.glob("*")) if RUNS_DIR.exists() else set()
        create_run(ns)
        after = set(path.name for path in RUNS_DIR.glob("*"))
        new_ids = sorted(after - before)
        if new_ids:
            created.append({"runId": new_ids[-1], "topic": topic, "folder": str(run_folder(new_ids[-1]))})
    emit({"created": created, "count": len(created)})


def run_stage_command(command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-2000:],
        "stderr": proc.stderr[-2000:],
    }


def batch_process(args: argparse.Namespace) -> None:
    run_ids = args.runs or []
    if args.runs_file:
        run_ids.extend(
            line.strip()
            for line in Path(args.runs_file).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    if not run_ids:
        conn = db()
        run_ids = [
            row["id"]
            for row in conn.execute(
                "SELECT id FROM video_runs WHERE status IN ('QUEUED', 'RESEARCHED', 'SCRIPTED', 'VOICED', 'VIDEO_GENERATED') ORDER BY created_at DESC LIMIT ?",
                (args.limit,),
            )
        ]
    if not run_ids:
        raise SystemExit("No runs found to process.")

    commands: list[list[str]] = []
    python = sys.executable
    for run_id in run_ids:
        folder = run_folder(run_id)
        if args.stage in {"voice", "all"}:
            for text_file in sorted(folder.glob("vo*.txt")):
                out = folder / f"{text_file.stem}.mp3"
                if args.force or not out.exists():
                    commands.append(
                        [
                            python,
                            str(Path(__file__).resolve()),
                            "voice",
                            "--text-file",
                            str(text_file),
                            "--out",
                            str(out),
                            "--run-id",
                            run_id,
                        ]
                    )
        if args.stage in {"veo", "all"}:
            for shot_file in sorted(folder.glob("shot*.txt")):
                out = folder / f"{shot_file.stem}.mp4"
                if args.force or not out.exists():
                    commands.append(
                        [
                            python,
                            str(Path(__file__).resolve()),
                            "veo",
                            "--text-file",
                            str(shot_file),
                            "--out",
                            str(out),
                            "--run-id",
                            run_id,
                        ]
                        + (["--model", args.model] if args.model else [])
                    )
    if not commands:
        emit({"status": "noop", "runs": run_ids, "stage": args.stage})
        return
    if args.dry_run:
        emit({"dryRun": True, "commands": commands})
        return

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as pool:
        futures = [pool.submit(run_stage_command, command) for command in commands]
        for future in as_completed(futures):
            results.append(future.result())
    failed = [result for result in results if result["returncode"] != 0]
    emit({"processed": len(results), "failed": len(failed), "results": results})
    if failed:
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Signal Growth Engine pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-run", help="Create a durable queued video run")
    init.add_argument("--topic", required=True)
    init.add_argument("--title")
    init.add_argument("--landing-url")
    init.set_defaults(func=create_run)

    resolve = sub.add_parser("resolve-abby", help="Resolve the Abby ElevenLabs voice ID")
    resolve.add_argument("--strict", action="store_true")
    resolve.set_defaults(func=resolve_abby)

    voice = sub.add_parser("voice", help="Generate Abby voiceover with timestamps")
    voice.add_argument("--text")
    voice.add_argument("--text-file")
    voice.add_argument("--out", required=True)
    voice.add_argument("--run-id")
    voice.add_argument("--voice-id")
    voice.add_argument("--model-id")
    voice.add_argument("--stability", type=float, default=0.46)
    voice.add_argument("--similarity", type=float, default=0.82)
    voice.add_argument("--style", type=float, default=0.32)
    voice.add_argument("--speed", type=float, help="ElevenLabs speech speed multiplier when supported by the API")
    voice.add_argument(
        "--allow-unapproved-creative",
        action="store_true",
        help="Override the creative-gate requirement for one-off experiments. Do not use for production runs.",
    )
    voice.set_defaults(func=generate_voice)

    veo = sub.add_parser("veo", help="Generate a Veo clip through the Gemini API")
    veo.add_argument("--text")
    veo.add_argument("--text-file")
    veo.add_argument("--out", required=True)
    veo.add_argument("--run-id")
    veo.add_argument("--model")
    veo.add_argument("--aspect-ratio", default="9:16")
    veo.add_argument("--reference-image", action="append", help="Reference image for Veo 3.1/3.1 Fast. Repeat up to three times.")
    veo.add_argument("--reference-type", choices=["asset", "style"], default="asset")
    veo.add_argument("--first-frame", help="Starting frame image for image-to-video. Use when the composition must stay stable.")
    veo.add_argument("--resolution", choices=["720p", "1080p", "4k"], help="Requested Veo output resolution when supported by the model.")
    veo.add_argument("--poll-sec", type=int, default=10)
    veo.add_argument("--timeout-sec", type=int, default=900)
    veo.add_argument("--dry-run", action="store_true")
    veo.add_argument(
        "--allow-unapproved-creative",
        action="store_true",
        help="Override the creative-gate requirement for one-off experiments. Do not use for production runs.",
    )
    veo.set_defaults(func=generate_veo)

    omni = sub.add_parser("omni-video", help="Generate a Gemini Omni Flash reference-video clip")
    omni.add_argument("--text")
    omni.add_argument("--text-file")
    omni.add_argument("--out", required=True)
    omni.add_argument("--run-id")
    omni.add_argument("--model")
    omni.add_argument("--aspect-ratio", default="9:16")
    omni.add_argument("--reference-image", action="append", required=True, help="Reference image for Gemini Omni Flash. Repeat up to three times.")
    omni.add_argument("--task", choices=["image_to_video", "reference_to_video", "text_to_video", "edit"], default="reference_to_video")
    omni.add_argument("--poll-sec", type=int, default=10)
    omni.add_argument("--timeout-sec", type=int, default=900)
    omni.add_argument("--dry-run", action="store_true")
    omni.add_argument(
        "--allow-unapproved-creative",
        action="store_true",
        help="Override the creative-gate requirement for one-off experiments. Do not use for production runs.",
    )
    omni.set_defaults(func=generate_omni_video)

    swipe = sub.add_parser("research-swipe", help="Collect source metadata/captions and create a local viral swipe report")
    swipe.add_argument("--urls", nargs="*")
    swipe.add_argument("--urls-file")
    swipe.add_argument("--work-dir", help="Run folder to receive quality_gates/research_swipe.json and research_swipe assets")
    swipe.add_argument("--run-id")
    swipe.add_argument("--min-sources", type=int, default=5)
    swipe.set_defaults(func=research_swipe)

    no_credit_gate = sub.add_parser("creative-gate", help="Validate research/script/storyboard files before any paid voice or video generation")
    no_credit_gate.add_argument("--work-dir", required=True)
    no_credit_gate.add_argument("--run-id")
    no_credit_gate.add_argument("--min-sources", type=int, default=20)
    no_credit_gate.add_argument("--min-resume-sources", type=int, default=10)
    no_credit_gate.add_argument("--min-document-refs", type=int, default=2)
    no_credit_gate.add_argument("--min-source-backed-rows", type=int, default=16)
    no_credit_gate.add_argument("--min-hook-rows", type=int, default=16)
    no_credit_gate.add_argument("--min-breakdown-rows", type=int, default=14)
    no_credit_gate.add_argument("--min-words", type=int, default=42)
    no_credit_gate.add_argument("--max-words", type=int, default=96)
    no_credit_gate.set_defaults(func=creative_gate_preflight)

    approve_creative_cmd = sub.add_parser("approve-creative", help="Mark the no-credit creative gate approved before paid voice/video generation")
    approve_creative_cmd.add_argument("--run-id", required=True)
    approve_creative_cmd.add_argument("--phrase", required=True)
    approve_creative_cmd.set_defaults(func=approve_creative)

    creative_review_cmd = sub.add_parser("creative-review", help="Generate Codex creative approval packet and mobile HTML page")
    creative_review_cmd.add_argument("--run-id", required=True)
    creative_review_cmd.add_argument("--host", help="Optional LAN host/IP for the review URL")
    creative_review_cmd.add_argument("--port", type=int, default=8796)
    creative_review_cmd.set_defaults(func=creative_review_packet)

    script_gate = sub.add_parser("script-qa", help="Fail AI-sounding scripts before voice/video generation")
    script_gate.add_argument("--work-dir", required=True)
    script_gate.add_argument("--run-id")
    script_gate.add_argument("--min-words", type=int, default=25)
    script_gate.add_argument("--max-words", type=int, default=96)
    script_gate.add_argument("--require-weak-quote", action="store_true")
    script_gate.set_defaults(func=script_qa)

    creative_gate = sub.add_parser("creative-qa", help="Check human-review story logic before assembly")
    creative_gate.add_argument("--work-dir", required=True)
    creative_gate.add_argument("--run-id")
    creative_gate.add_argument("--format", choices=["desk_teardown", "screen_recording_teardown", "search_test", "myth_bust", "template_reaction"])
    creative_gate.set_defaults(func=creative_qa)

    screen_gate = sub.add_parser("screen-visual-qa", help="Check no-credit screen-recording teardown storyboard before voice/video generation")
    screen_gate.add_argument("--work-dir", required=True)
    screen_gate.add_argument("--run-id")
    screen_gate.add_argument("--input")
    screen_gate.add_argument("--contact-sheet")
    screen_gate.add_argument("--visual-reviewed", action="store_true")
    screen_gate.set_defaults(func=screen_visual_qa)

    screen_plan = sub.add_parser("screen-build-plan", help="No-credit post-approval plan for the gold screen teardown")
    screen_plan.add_argument("--run-id", required=True)
    screen_plan.add_argument("--work-dir")
    screen_plan.add_argument("--host")
    screen_plan.add_argument("--port", type=int, default=8796)
    screen_plan.add_argument("--audio-name")
    screen_plan.add_argument("--visual-name")
    screen_plan.add_argument("--final-name")
    screen_plan.add_argument("--contact-sheet-name")
    screen_plan.set_defaults(func=screen_build_plan)

    surface_plan = sub.add_parser("surface-build-plan", help="No-credit post-approval plan for paper/tablet surface-fit teardown")
    surface_plan.add_argument("--run-id")
    surface_plan.add_argument("--work-dir")
    surface_plan.add_argument("--host")
    surface_plan.add_argument("--port", type=int, default=8797)
    surface_plan.add_argument("--voice-text-name")
    surface_plan.add_argument("--manifest-name")
    surface_plan.add_argument("--prompt-name")
    surface_plan.add_argument("--audio-name")
    surface_plan.add_argument("--animatic-name")
    surface_plan.add_argument("--final-name")
    surface_plan.add_argument("--contact-sheet-name")
    surface_plan.set_defaults(func=surface_build_plan)

    plate_intake = sub.add_parser("prepare-plate-intake", help="Write exact clean-plate filenames, prompts, and post-download QA commands for a surface-fit run")
    plate_intake.add_argument("--run-id")
    plate_intake.add_argument("--work-dir")
    plate_intake.add_argument("--manifest-name")
    plate_intake.add_argument("--prompt-name")
    plate_intake.add_argument("--json-name")
    plate_intake.add_argument("--md-name")
    plate_intake.add_argument("--host")
    plate_intake.add_argument("--port", type=int, default=8797)
    plate_intake.set_defaults(func=prepare_plate_intake)

    plate_ingest = sub.add_parser("ingest-plate-files", help="Copy image plates or extract video frames into the exact surface_fit.json plate filenames")
    plate_ingest.add_argument("--run-id")
    plate_ingest.add_argument("--work-dir")
    plate_ingest.add_argument("--manifest-name")
    plate_ingest.add_argument("--tablet-source", help="Clean tablet/screen/laptop source image or video; copied/extracted into all tablet/screen plate targets.")
    plate_ingest.add_argument("--paper-source", help="Clean paper/desk source image or video; copied/extracted into all paper plate targets.")
    plate_ingest.add_argument("--extract-time", type=float, default=2.0, help="Timestamp in seconds when extracting a still from a video source.")
    plate_ingest.add_argument("--overwrite", action="store_true", help="Replace existing plate target files.")
    plate_ingest.add_argument("--json-name")
    plate_ingest.add_argument("--host")
    plate_ingest.add_argument("--port", type=int, default=8797)
    plate_ingest.set_defaults(func=ingest_plate_files)

    readiness = sub.add_parser("gold-readiness", help="Audit one run against the gold-standard video requirements and write a current-state report")
    readiness.add_argument("--run-id")
    readiness.add_argument("--work-dir")
    readiness.add_argument("--manifest-name")
    readiness.add_argument("--audio-name")
    readiness.add_argument("--final-name")
    readiness.add_argument("--contact-sheet-name")
    readiness.add_argument("--json-name")
    readiness.add_argument("--md-name")
    readiness.set_defaults(func=gold_readiness)

    plate_gate = sub.add_parser("plate-qa", help="Check Veo/Flow/owned footage plates before overlays and final QA")
    plate_gate.add_argument("--work-dir", required=True)
    plate_gate.add_argument("--video", action="append")
    plate_gate.add_argument("--run-id")
    plate_gate.add_argument("--visual-reviewed", action="store_true", help="Set only after Codex/human inspected extracted frames for fake text, watermark, hands, and plate stability.")
    plate_gate.add_argument("--generated-text-ok", action="store_true", help="Intentional fail flag documenting that generated readable text was found.")
    plate_gate.set_defaults(func=plate_qa)

    surface_gate = sub.add_parser("surface-fit-qa", help="Check paper/tablet/screen corner-pin overlay plan before final assembly")
    surface_gate.add_argument("--work-dir", required=True)
    surface_gate.add_argument("--run-id")
    surface_gate.add_argument("--manifest", help="Defaults to surface_fit.json in the run folder")
    surface_gate.add_argument("--visual-reviewed", action="store_true", help="Set only after inspecting full-size fitted frames for floating overlays, blur, and bad clipping.")
    surface_gate.add_argument("--min-area-ratio", type=float, default=0.08)
    surface_gate.add_argument("--max-area-ratio", type=float, default=0.92)
    surface_gate.set_defaults(func=surface_fit_qa)

    surface_preview = sub.add_parser("surface-fit-preview", help="Create no-credit corner-pinned paper/tablet/screen preview images")
    surface_preview.add_argument("--work-dir", required=True)
    surface_preview.add_argument("--run-id")
    surface_preview.add_argument("--manifest", help="Defaults to surface_fit.json in the run folder")
    surface_preview.add_argument("--out-dir")
    surface_preview.add_argument("--min-area-ratio", type=float, default=0.08)
    surface_preview.add_argument("--max-area-ratio", type=float, default=0.92)
    surface_preview.set_defaults(func=surface_fit_preview)

    surface_review = sub.add_parser("surface-fit-review", help="Create a mobile HTML review page for plate/overlay/fitted surface inspection")
    surface_review.add_argument("--work-dir", required=True)
    surface_review.add_argument("--run-id")
    surface_review.add_argument("--manifest", help="Defaults to surface_fit.json in the run folder")
    surface_review.add_argument("--out-dir")
    surface_review.add_argument("--html-name")
    surface_review.add_argument("--host")
    surface_review.add_argument("--port", type=int, default=8797)
    surface_review.add_argument("--min-area-ratio", type=float, default=0.08)
    surface_review.add_argument("--max-area-ratio", type=float, default=0.92)
    surface_review.set_defaults(func=surface_fit_review_packet)

    surface_animatic = sub.add_parser("surface-fit-animatic", help="Build a no-credit review MP4 from corner-pinned paper/tablet storyboard stills")
    surface_animatic.add_argument("--work-dir", required=True)
    surface_animatic.add_argument("--run-id")
    surface_animatic.add_argument("--manifest", help="Defaults to surface_fit.json in the run folder")
    surface_animatic.add_argument("--preview-dir")
    surface_animatic.add_argument("--out")
    surface_animatic.add_argument("--audio", help="Optional existing voiceover audio to mux into the animatic")
    surface_animatic.add_argument("--default-duration", type=float, default=3.0)
    surface_animatic.add_argument("--min-area-ratio", type=float, default=0.08)
    surface_animatic.add_argument("--max-area-ratio", type=float, default=0.92)
    surface_animatic.set_defaults(func=surface_fit_animatic)

    overlays = sub.add_parser("overlays", help="Generate deterministic readable resume overlays for Veo footage")
    overlays.add_argument("--work-dir", required=True)
    overlays.add_argument("--run-id")
    overlays.set_defaults(func=generate_overlays)

    live_edit = sub.add_parser("live-edit-overlays", help="Generate animated resume edit overlay frames for Veo footage")
    live_edit.add_argument("--work-dir", required=True)
    live_edit.add_argument("--run-id")
    live_edit.set_defaults(func=generate_live_edit_overlays)

    build_screen = sub.add_parser("build-screen-teardown", help="Post-approval build for the gold screen-recording teardown")
    build_screen.add_argument("--run-id", required=True)
    build_screen.add_argument("--work-dir")
    build_screen.add_argument("--voice-test-only", action="store_true")
    build_screen.add_argument("--model-id", default="eleven_multilingual_v2")
    build_screen.add_argument("--stability", type=float, default=0.32)
    build_screen.add_argument("--similarity", type=float, default=0.84)
    build_screen.add_argument("--style", type=float, default=0.65)
    build_screen.add_argument("--speed", type=float, default=1.18)
    build_screen.add_argument("--duration", type=float)
    build_screen.add_argument("--audio-name")
    build_screen.add_argument("--visual-name")
    build_screen.add_argument("--final-name")
    build_screen.add_argument("--contact-sheet-name")
    build_screen.add_argument("--force", action="store_true")
    build_screen.add_argument(
        "--allow-unapproved-creative",
        action="store_true",
        help="Override the creative approval requirement for one-off experiments. Do not use for production runs.",
    )
    build_screen.set_defaults(func=build_screen_teardown)

    build_surface = sub.add_parser("build-surface-teardown", help="Post-approval build for the gold paper/tablet surface-fit teardown")
    build_surface.add_argument("--run-id", required=True)
    build_surface.add_argument("--work-dir")
    build_surface.add_argument("--voice-test-only", action="store_true")
    build_surface.add_argument("--visual-reviewed", action="store_true", help="Set only after inspecting full-size fitted previews and plate frames.")
    build_surface.add_argument("--plate", action="append", help="Optional clean plate video/image to include in plate QA. Defaults to shot*.mp4 and surface_fit.json frames.")
    build_surface.add_argument("--manifest-name")
    build_surface.add_argument("--voice-text-name")
    build_surface.add_argument("--audio-name")
    build_surface.add_argument("--final-name")
    build_surface.add_argument("--contact-sheet-name")
    build_surface.add_argument("--preview-dir-name")
    build_surface.add_argument("--creative-format")
    build_surface.add_argument("--model-id", default="eleven_multilingual_v2")
    build_surface.add_argument("--stability", type=float, default=0.38)
    build_surface.add_argument("--similarity", type=float, default=0.84)
    build_surface.add_argument("--style", type=float, default=0.45)
    build_surface.add_argument("--speed", type=float)
    build_surface.add_argument("--default-duration", type=float, default=3.0)
    build_surface.add_argument("--min-area-ratio", type=float, default=0.08)
    build_surface.add_argument("--max-area-ratio", type=float, default=0.92)
    build_surface.add_argument("--force", action="store_true")
    build_surface.add_argument(
        "--allow-unapproved-creative",
        action="store_true",
        help="Override the creative approval requirement for one-off experiments. Do not use for production runs.",
    )
    build_surface.set_defaults(func=build_surface_teardown)

    assm = sub.add_parser("assemble", help="Run the sync-safe ffmpeg assembly script")
    assm.add_argument("--work-dir", default=str(Path.home() / "Downloads"))
    assm.add_argument("--out", default="signal_ad_final_pipeline.mp4")
    assm.add_argument("--run-id")
    assm.add_argument("--background-clip")
    assm.set_defaults(func=assemble)

    sheet = sub.add_parser("contact-sheet", help="Extract review frames from a rendered MP4 into one QA contact sheet")
    sheet.add_argument("--video", required=True)
    sheet.add_argument("--out")
    sheet.add_argument("--times", help="Comma-separated seconds to extract")
    sheet.add_argument("--count", type=int, default=9)
    sheet.add_argument("--columns", type=int, default=3)
    sheet.add_argument("--thumb-width", type=int, default=360)
    sheet.add_argument("--label")
    sheet.set_defaults(func=contact_sheet)

    quality = sub.add_parser("qa", help="Validate render technical requirements")
    quality.add_argument("--video", required=True)
    quality.add_argument("--run-id")
    quality.add_argument("--write", action="store_true")
    quality.set_defaults(func=qa)

    review_cmd = sub.add_parser("review", help="Print Codex approval packet")
    review_cmd.add_argument("--run-id", required=True)
    review_cmd.add_argument("--host", default="192.168.2.10")
    review_cmd.add_argument("--port", default="8770")
    review_cmd.set_defaults(func=review)

    approve_cmd = sub.add_parser("approve", help="Mark a reviewed video approved")
    approve_cmd.add_argument("--run-id", required=True)
    approve_cmd.add_argument("--phrase", required=True)
    approve_cmd.set_defaults(func=approve)

    status_cmd = sub.add_parser("status", help="Set a status manually for review/revision bookkeeping")
    status_cmd.add_argument("--run-id", required=True)
    status_cmd.add_argument("--status", required=True, choices=sorted(STATUS_ORDER))
    status_cmd.add_argument("--reason")
    status_cmd.set_defaults(func=mark_status)

    state = sub.add_parser("state", help="Show recent runs or one run")
    state.add_argument("--run-id")
    state.add_argument("--limit", type=int, default=10)
    state.set_defaults(func=show_state)

    batch_init = sub.add_parser("batch-init", help="Create several queued runs from topics")
    batch_init.add_argument("--topics", nargs="*")
    batch_init.add_argument("--topics-file")
    batch_init.add_argument("--landing-url")
    batch_init.set_defaults(func=create_batch)

    batch = sub.add_parser("batch-process", help="Process ready VO/Veo files for multiple runs concurrently")
    batch.add_argument("--runs", nargs="*")
    batch.add_argument("--runs-file")
    batch.add_argument("--stage", choices=["voice", "veo", "all"], default="all")
    batch.add_argument("--max-workers", type=int, default=3)
    batch.add_argument("--limit", type=int, default=3)
    batch.add_argument("--model")
    batch.add_argument("--force", action="store_true")
    batch.add_argument("--dry-run", action="store_true")
    batch.set_defaults(func=batch_process)

    return parser


def main() -> None:
    load_env()
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
