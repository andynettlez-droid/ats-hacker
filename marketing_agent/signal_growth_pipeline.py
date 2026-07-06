#!/usr/bin/env python3
"""Signal Growth Engine pipeline helper.

This replaces the old one-off video script with a small, durable command runner:
research/script assets live in files, Veo creates clips, ElevenLabs creates Abby VO,
ffmpeg assembles, and Codex approval remains the only publish gate.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
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

ROOT = Path(__file__).resolve().parents[1]
MARKETING_DIR = ROOT / "marketing"
RUNS_DIR = MARKETING_DIR / "growth_runs"
DB_PATH = MARKETING_DIR / "signal_growth_engine.sqlite"
SKILLS_DIR = ROOT / "skills"
ASSEMBLE_PS1 = SKILLS_DIR / "assemble.ps1"

ABBY_VOICE_ID = "lkFHOvhI41u53xDdGZoZ"
DEFAULT_VEO_MODEL = "veo-3.1-generate-preview"

STATUS_ORDER = {
    "QUEUED",
    "RESEARCHED",
    "SCRIPTED",
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
        os.environ.setdefault(key, value)


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
    prompt = read_text_arg(args)
    output = Path(args.out).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    model = args.model or os.getenv("GEMINI_VEO_MODEL", DEFAULT_VEO_MODEL)
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    request_body: dict[str, Any] = {
        "instances": [{"prompt": prompt}],
        "parameters": {"aspectRatio": args.aspect_ratio},
    }
    if args.dry_run:
        emit({"dryRun": True, "model": model, "request": request_body, "out": str(output)})
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


def find_exe(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
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
    subprocess.run(command, cwd=str(ROOT), check=True)
    video_path = work_dir / out
    if args.run_id:
        conn = db()
        get_run(conn, args.run_id)
        update_run(conn, args.run_id, status="RENDERED", video_path=str(video_path))
        log_event(conn, args.run_id, "rendered", {"videoPath": str(video_path), "assembler": str(ASSEMBLE_PS1)})
        conn.commit()
    emit({"status": "RENDERED", "video": str(video_path)})


def ffprobe_json(video: Path) -> dict[str, Any]:
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
    voice.set_defaults(func=generate_voice)

    veo = sub.add_parser("veo", help="Generate a Veo clip through the Gemini API")
    veo.add_argument("--text")
    veo.add_argument("--text-file")
    veo.add_argument("--out", required=True)
    veo.add_argument("--run-id")
    veo.add_argument("--model")
    veo.add_argument("--aspect-ratio", default="9:16")
    veo.add_argument("--poll-sec", type=int, default=10)
    veo.add_argument("--timeout-sec", type=int, default=900)
    veo.add_argument("--dry-run", action="store_true")
    veo.set_defaults(func=generate_veo)

    assm = sub.add_parser("assemble", help="Run the sync-safe ffmpeg assembly script")
    assm.add_argument("--work-dir", default=str(Path.home() / "Downloads"))
    assm.add_argument("--out", default="signal_ad_final_pipeline.mp4")
    assm.add_argument("--run-id")
    assm.set_defaults(func=assemble)

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

    return parser


def main() -> None:
    load_env()
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
