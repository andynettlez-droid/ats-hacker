import argparse
import hashlib
import json
import shutil
import socket
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from promote_daily_drafts import promote


ROOT = Path(__file__).resolve().parents[1]
MARKETING_DIR = ROOT / "marketing"
DAILY_DIR = MARKETING_DIR / "daily_content"
REMOTION_DIR = MARKETING_DIR / "remotion"
REMOTION_OUT = REMOTION_DIR / "out"
AUTOPOST_DIR = MARKETING_DIR / "autopost"
AUTOPOST_VIDEOS = AUTOPOST_DIR / "videos"
POSTS_PATH = AUTOPOST_DIR / "posts.json"
REVIEWS_DIR = MARKETING_DIR / "codex_reviews"
DB_PATH = MARKETING_DIR / "video_pipeline_state.sqlite"

PIPELINE_STATES = [
    "QUEUED",
    "SCRIPTED",
    "VOICED",
    "RENDERED",
    "QA_PASSED",
    "AWAITING_CODEX_APPROVAL",
    "APPROVED",
    "REJECTED",
    "REVISION_REQUESTED",
    "PUBLISHED",
    "MEASURED",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def safe_slug(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:64] or "signal-video"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latest_drafts_path() -> Path:
    drafts = sorted(DAILY_DIR.glob("*/autopost_drafts.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not drafts:
        raise FileNotFoundError("No autopost_drafts.json found under marketing/daily_content.")
    return drafts[0]


def packet_path_for_drafts(drafts_path: Path) -> Path:
    return drafts_path.parent / "packet.json"


def manifest_path_for_drafts(drafts_path: Path) -> Path:
    return drafts_path.parent / "channel_manifest.json"


def run_id_for(drafts_path: Path, draft: dict) -> str:
    key = f"{rel(drafts_path)}::{draft.get('file')}::{draft.get('renderProps')}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def connect_db() -> sqlite3.Connection:
    MARKETING_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS video_runs (
          id TEXT PRIMARY KEY,
          packet_dir TEXT NOT NULL,
          drafts_path TEXT NOT NULL,
          draft_file TEXT NOT NULL,
          title TEXT NOT NULL,
          caption TEXT,
          platforms_json TEXT,
          composition TEXT,
          render_props TEXT,
          output_path TEXT,
          queue_path TEXT,
          review_dir TEXT,
          review_video_path TEXT,
          state TEXT NOT NULL,
          qa_json TEXT,
          post_metadata_json TEXT,
          file_sha256 TEXT,
          approval_json TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS video_run_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          run_id TEXT NOT NULL,
          state TEXT NOT NULL,
          details_json TEXT,
          created_at TEXT NOT NULL
        )
        """
    )
    return conn


def record_event(conn: sqlite3.Connection, run_id: str, state: str, details: dict | None = None) -> None:
    if state not in PIPELINE_STATES:
        raise ValueError(f"Unknown pipeline state: {state}")
    conn.execute(
        "INSERT INTO video_run_events (run_id, state, details_json, created_at) VALUES (?, ?, ?, ?)",
        (run_id, state, json.dumps(details or {}), utc_now()),
    )
    conn.commit()


def upsert_run(conn: sqlite3.Connection, run: dict) -> None:
    existing = conn.execute("SELECT id FROM video_runs WHERE id = ?", (run["id"],)).fetchone()
    now = utc_now()
    columns = [
        "id",
        "packet_dir",
        "drafts_path",
        "draft_file",
        "title",
        "caption",
        "platforms_json",
        "composition",
        "render_props",
        "output_path",
        "queue_path",
        "review_dir",
        "review_video_path",
        "state",
        "qa_json",
        "post_metadata_json",
        "file_sha256",
        "approval_json",
        "created_at",
        "updated_at",
    ]
    run.setdefault("created_at", now)
    run["updated_at"] = now
    values = [run.get(column) for column in columns]
    if existing:
        assignments = ", ".join(f"{column} = ?" for column in columns[1:])
        conn.execute(
            f"UPDATE video_runs SET {assignments} WHERE id = ?",
            [run.get(column) for column in columns[1:]] + [run["id"]],
        )
    else:
        placeholders = ", ".join("?" for _ in columns)
        conn.execute(f"INSERT INTO video_runs ({', '.join(columns)}) VALUES ({placeholders})", values)
    conn.commit()


def row_to_run(row: sqlite3.Row | tuple) -> dict:
    keys = [
        "id",
        "packet_dir",
        "drafts_path",
        "draft_file",
        "title",
        "caption",
        "platforms_json",
        "composition",
        "render_props",
        "output_path",
        "queue_path",
        "review_dir",
        "review_video_path",
        "state",
        "qa_json",
        "post_metadata_json",
        "file_sha256",
        "approval_json",
        "created_at",
        "updated_at",
    ]
    data = dict(zip(keys, row))
    for key in ("platforms_json", "qa_json", "post_metadata_json", "approval_json"):
        raw = data.get(key)
        if raw:
            try:
                data[key.replace("_json", "")] = json.loads(raw)
            except json.JSONDecodeError:
                data[key.replace("_json", "")] = raw
    return data


def list_runs(state: str | None = None, limit: int = 20) -> list[dict]:
    conn = connect_db()
    if state:
        rows = conn.execute(
            "SELECT * FROM video_runs WHERE state = ? ORDER BY updated_at DESC LIMIT ?",
            (state, limit),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM video_runs ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
    return [row_to_run(row) for row in rows]


def get_run(run_id: str) -> dict:
    conn = connect_db()
    row = conn.execute("SELECT * FROM video_runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        raise ValueError(f"No video run found for {run_id}")
    run = row_to_run(row)
    events = conn.execute(
        "SELECT state, details_json, created_at FROM video_run_events WHERE run_id = ? ORDER BY id ASC",
        (run_id,),
    ).fetchall()
    run["events"] = [
        {
            "state": state,
            "details": json.loads(details or "{}"),
            "createdAt": created_at,
        }
        for state, details, created_at in events
    ]
    return run


def resolve_root_ref(ref: str) -> Path:
    return ROOT / str(ref).replace("\\", "/")


def props_for(draft: dict) -> dict:
    props_ref = draft.get("renderProps")
    if not props_ref:
        return {}
    return read_json(resolve_root_ref(props_ref), {})


def is_youtube_longform(draft: dict) -> bool:
    return (
        draft.get("contentType") == "youtube_long_form"
        or draft.get("youtubeKind") == "long_form"
        or draft.get("composition") == "TeardownEpisode"
    )


def post_metadata_for(draft: dict, run_id: str) -> dict:
    platform = "youtube" if draft.get("platforms") == ["youtube"] else "shorts"
    return {
        "title": draft.get("youtubeTitle") or draft.get("title") or "Signal resume teardown",
        "caption": draft.get("caption", ""),
        "description": draft.get("youtubeDescription") or draft.get("description") or draft.get("caption", ""),
        "platforms": draft.get("platforms", ["tiktok", "instagram", "youtube"]),
        "cta": "Free Signal score",
        "landingUrl": (
            "https://ats-hacker-swart.vercel.app/"
            f"?utm_source={platform}&utm_medium=video&utm_campaign=codex_approval&utm_content={run_id}"
        ),
        "containsSyntheticMedia": True,
        "status": "review_required",
    }


def local_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def run_command(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def render_draft(draft: dict, force: bool = False) -> Path:
    filename = Path(str(draft.get("file", ""))).name
    if not filename:
        raise ValueError("Draft is missing file.")
    output_path = REMOTION_OUT / filename
    if output_path.exists() and not force:
        return output_path

    props_ref = str(draft.get("renderProps", ""))
    if not props_ref:
        raise ValueError(f"Draft {draft.get('title')} is missing renderProps.")
    props_path = resolve_root_ref(props_ref)
    if not props_path.exists():
        raise FileNotFoundError(f"Render props not found: {props_path}")

    props_arg = str(props_path.relative_to(REMOTION_DIR)).replace("\\", "/")
    composition = draft.get("composition") or "ResumeCrimeScene"
    run_command(["npx.cmd", "remotion", "render", composition, f"out/{filename}", f"--props={props_arg}"], REMOTION_DIR)

    thumbnail_ref = draft.get("thumbnail")
    thumbnail_props_ref = draft.get("thumbnailProps")
    if thumbnail_ref and thumbnail_props_ref:
        thumbnail_path = resolve_root_ref(str(thumbnail_ref))
        thumbnail_props_path = resolve_root_ref(str(thumbnail_props_ref))
        if not thumbnail_props_path.exists():
            raise FileNotFoundError(f"Thumbnail props not found: {thumbnail_props_path}")
        if force or not thumbnail_path.exists():
            thumbnail_arg = str(thumbnail_props_path.relative_to(REMOTION_DIR)).replace("\\", "/")
            thumbnail_out = str(thumbnail_path.relative_to(REMOTION_DIR)).replace("\\", "/")
            run_command(["npx.cmd", "remotion", "still", "SignalThumbnail", thumbnail_out, f"--props={thumbnail_arg}"], REMOTION_DIR)
    return output_path


def write_single_draft(review_dir: Path, draft: dict) -> Path:
    path = review_dir / "single_autopost_draft.json"
    write_json(path, [draft])
    return path


def run_qc_gates(drafts_path: Path, single_draft_path: Path, review_dir: Path, draft: dict) -> dict:
    reports = {
        "studio": review_dir / "studio-qc.json",
        "audio": review_dir / "audio-qc.json",
        "visual": review_dir / "visual-qc.json",
    }
    manifest = manifest_path_for_drafts(drafts_path)
    if is_youtube_longform(draft):
        commands = [
            ["studio", ["node", "scripts/qc_youtube_longform.mjs", "--drafts", str(single_draft_path), "--report", str(reports["studio"])]],
            [
                "audio",
                [
                    "node",
                    "scripts/qc_daily_audio_assets.mjs",
                    "--drafts",
                    str(single_draft_path),
                    "--manifest",
                    str(manifest),
                    "--report",
                    str(reports["audio"]),
                ],
            ],
        ]
    else:
        commands = [
            ["studio", ["node", "scripts/qc_daily_studio_shorts.mjs", "--drafts", str(single_draft_path), "--report", str(reports["studio"])]],
            [
                "audio",
                [
                    "node",
                    "scripts/qc_daily_audio_assets.mjs",
                    "--drafts",
                    str(single_draft_path),
                    "--manifest",
                    str(manifest),
                    "--report",
                    str(reports["audio"]),
                ],
            ],
            ["visual", ["node", "scripts/qc_daily_visual_safe_area.mjs", "--drafts", str(single_draft_path), "--report", str(reports["visual"])]],
        ]
    results = {}
    for name, command in commands:
        try:
            run_command(command, REMOTION_DIR)
            results[name] = read_json(reports[name], {"passed": False, "error": "missing report"})
        except subprocess.CalledProcessError as error:
            results[name] = {
                "passed": False,
                "error": f"QC command failed with exit code {error.returncode}",
                "report": rel(reports[name]) if reports[name].exists() else None,
            }
    if is_youtube_longform(draft):
        results["visual"] = {
            "passed": bool(results.get("studio", {}).get("passed")),
            "note": "Long-form visual checks are covered by 16:9 metadata, thumbnail, sections, and artifact checks.",
        }
    results["passed"] = all(isinstance(result, dict) and result.get("passed") for result in results.values())
    return results


def validate_script_gate(drafts_path: Path) -> dict:
    report_path = drafts_path.parent / "creative_quality_report.json"
    report = read_json(report_path, {})
    return {
        "path": rel(report_path) if report_path.exists() else None,
        "passed": bool(report.get("passed")),
        "score": report.get("overallScore"),
        "verdict": report.get("verdict"),
        "blockers": report.get("blockers", []),
    }


def quality_summary(draft: dict, qc: dict, script_gate: dict, output_path: Path) -> dict:
    props = props_for(draft)
    caption_ready = props.get("captionReadiness") if isinstance(props.get("captionReadiness"), dict) else {}
    audio_ready = props.get("audioReadiness") if isinstance(props.get("audioReadiness"), dict) else {}
    if is_youtube_longform(draft):
        sections = props.get("sections") if isinstance(props.get("sections"), list) else []
        voiceover_segments = props.get("voiceoverSegments") if isinstance(props.get("voiceoverSegments"), list) else []
        thumbnail_path = resolve_root_ref(str(draft.get("thumbnail", ""))) if draft.get("thumbnail") else None
        required_checks = {
            "scriptClaimSafety": script_gate.get("passed") is True,
            "renderedMp4Exists": output_path.exists(),
            "longFormMetadataQc": qc.get("studio", {}).get("passed") is True,
            "audioAssetQc": qc.get("audio", {}).get("passed") is True,
            "thumbnailRendered": bool(thumbnail_path and thumbnail_path.exists()),
            "sectionsPresent": len(sections) >= 8,
            "voiceoverSegmentsPresent": len(voiceover_segments) >= min(8, len(sections)),
            "ctaLeadsToFreeSignalScore": "free" in str(props.get("cta", draft.get("caption", ""))).lower()
            and "signal" in str(props.get("cta", draft.get("caption", ""))).lower(),
            "scoreMovesUp": int(props.get("afterScore", 0) or 0) > int(props.get("beforeScore", 0) or 0),
        }
        return {
            "passed": all(required_checks.values()),
            "requiredChecks": required_checks,
            "scriptGate": script_gate,
            "qcReports": {
                "longForm": qc.get("studio", {}).get("passed"),
                "audio": qc.get("audio", {}).get("passed"),
                "visual": qc.get("visual", {}).get("passed"),
            },
            "captionReadiness": {
                "wordLevel": False,
                "reason": "Long-form uses section narration; word-level karaoke captions are not required for review cut.",
            },
            "audioReadiness": audio_ready,
        }
    required_checks = {
        "scriptClaimSafety": script_gate.get("passed") is True,
        "renderedMp4Exists": output_path.exists(),
        "studioMetadataQc": qc.get("studio", {}).get("passed") is True,
        "audioAssetQc": qc.get("audio", {}).get("passed") is True,
        "visualSafeAreaQc": qc.get("visual", {}).get("passed") is True,
        "sceneCaptionsPresent": all(props.get(key) for key in ["hook", "subhook", "cta"]),
        "wordLevelCaptionsWhenAvailable": bool(caption_ready.get("wordLevel")) or audio_ready.get("provider") in {"cached", "openai"},
        "ctaLeadsToFreeSignalScore": "free" in str(props.get("cta", draft.get("caption", ""))).lower()
        and "signal" in str(props.get("cta", draft.get("caption", ""))).lower(),
        "scoreMovesUp": int(props.get("afterScore", 0) or 0) > int(props.get("beforeScore", 0) or 0),
    }
    return {
        "passed": all(required_checks.values()),
        "requiredChecks": required_checks,
        "scriptGate": script_gate,
        "qcReports": {
            "studio": qc.get("studio", {}).get("passed"),
            "audio": qc.get("audio", {}).get("passed"),
            "visual": qc.get("visual", {}).get("passed"),
        },
        "captionReadiness": caption_ready or {
            "wordLevel": False,
            "reason": "Scene captions present; no word-level metadata on this cached asset.",
        },
        "audioReadiness": audio_ready,
    }


def prepare_review(drafts_path: Path, draft: dict, force_render: bool = False) -> dict:
    run_id = run_id_for(drafts_path, draft)
    review_dir = REVIEWS_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%d')}-{run_id}-{safe_slug(draft.get('title', 'video'))}"
    review_dir.mkdir(parents=True, exist_ok=True)

    conn = connect_db()
    filename = Path(draft["file"]).name
    initial_run = {
        "id": run_id,
        "packet_dir": rel(drafts_path.parent),
        "drafts_path": rel(drafts_path),
        "draft_file": draft.get("file"),
        "title": draft.get("title") or filename,
        "caption": draft.get("caption", ""),
        "platforms_json": json.dumps(draft.get("platforms", [])),
        "composition": draft.get("composition"),
        "render_props": draft.get("renderProps"),
        "output_path": rel(REMOTION_OUT / filename),
        "queue_path": rel(AUTOPOST_VIDEOS / filename),
        "review_dir": rel(review_dir),
        "review_video_path": rel(review_dir / filename),
        "state": "QUEUED",
        "qa_json": None,
        "post_metadata_json": json.dumps(post_metadata_for(draft, run_id)),
        "file_sha256": None,
        "approval_json": None,
    }
    upsert_run(conn, initial_run)
    record_event(conn, run_id, "QUEUED", {"draft": draft.get("file")})
    record_event(conn, run_id, "SCRIPTED", {"renderProps": draft.get("renderProps")})
    if draft.get("audioReadiness", {}).get("studioVoiceover"):
        record_event(conn, run_id, "VOICED", draft.get("audioReadiness"))

    output_path = render_draft(draft, force=force_render)
    record_event(conn, run_id, "RENDERED", {"output": rel(output_path)})
    promote_result = promote(drafts_path, only=draft.get("file"))
    if promote_result["missing"]:
        raise RuntimeError(f"Promotion failed; missing renders: {promote_result['missing']}")

    single_draft_path = write_single_draft(review_dir, draft)
    qc = run_qc_gates(drafts_path, single_draft_path, review_dir, draft)
    script_gate = validate_script_gate(drafts_path)
    summary = quality_summary(draft, qc, script_gate, output_path)
    if is_youtube_longform(draft):
        manifest_path = manifest_path_for_drafts(drafts_path)
        manifest = read_json(manifest_path, {})
        manifest.setdefault("episode", {})
        manifest["episode"]["renderReview"] = {
            "passed": summary["passed"],
            "runId": run_id,
            "output": rel(output_path),
            "studioQcReport": rel(review_dir / "studio-qc.json"),
            "audioQcReport": rel(review_dir / "audio-qc.json"),
        }
        manifest["episode"]["qaGate"] = {
            "required": True,
            "passed": summary["passed"],
            "status": "rendered_review_required" if summary["passed"] else "rendered_needs_revision",
            "checks": summary["requiredChecks"],
        }
        manifest["episode"]["status"] = "rendered_review_required" if summary["passed"] else "rendered_needs_revision"
        manifest["status"] = "rendered_review_required" if summary["passed"] else "rendered_needs_revision"
        write_json(manifest_path, manifest)
    if not summary["passed"]:
        state = "RENDERED"
    else:
        state = "AWAITING_CODEX_APPROVAL"
        record_event(conn, run_id, "QA_PASSED", summary["requiredChecks"])

    queue_path = AUTOPOST_VIDEOS / filename
    review_video = review_dir / filename
    shutil.copyfile(queue_path if queue_path.exists() else output_path, review_video)
    file_hash = sha256_file(review_video)
    metadata = post_metadata_for(draft, run_id)
    mobile_ip = local_ip()
    review_manifest = {
        "runId": run_id,
        "state": state,
        "title": draft.get("title"),
        "file": draft.get("file"),
        "reviewVideo": rel(review_video),
        "queueVideo": rel(queue_path),
        "sha256": file_hash,
        "mobileReviewUrl": f"http://{mobile_ip}:8765/{review_dir.name}/{filename}" if mobile_ip else None,
        "serveCommand": "py -3 -m http.server 8765 --directory marketing/codex_reviews",
        "postMetadata": metadata,
        "qa": summary,
        "approvalPhrase": f"APPROVE POST {run_id}",
        "createdAt": utc_now(),
    }
    write_json(review_dir / "review_manifest.json", review_manifest)
    (review_dir / "REVIEW.md").write_text(render_review_markdown(review_manifest), encoding="utf-8")

    run = {
        "id": run_id,
        "packet_dir": rel(drafts_path.parent),
        "drafts_path": rel(drafts_path),
        "draft_file": draft.get("file"),
        "title": draft.get("title") or filename,
        "caption": draft.get("caption", ""),
        "platforms_json": json.dumps(draft.get("platforms", [])),
        "composition": draft.get("composition"),
        "render_props": draft.get("renderProps"),
        "output_path": rel(output_path),
        "queue_path": rel(queue_path),
        "review_dir": rel(review_dir),
        "review_video_path": rel(review_video),
        "state": state,
        "qa_json": json.dumps(summary),
        "post_metadata_json": json.dumps(metadata),
        "file_sha256": file_hash,
        "approval_json": None,
    }
    upsert_run(conn, run)
    record_event(conn, run_id, state, {"reviewVideo": rel(review_video)})
    return review_manifest


def render_review_markdown(manifest: dict) -> str:
    metadata = manifest["postMetadata"]
    qa = manifest["qa"]
    lines = [
        "# Codex Video Approval",
        "",
        f"Run ID: `{manifest['runId']}`",
        f"State: `{manifest['state']}`",
        f"Video: `{manifest['reviewVideo']}`",
        f"SHA256: `{manifest['sha256']}`",
        "",
        "## Mobile Review",
        "",
        f"Start server from repo root: `{manifest['serveCommand']}`",
        f"URL: `{manifest.get('mobileReviewUrl') or 'unavailable'}`",
        "",
        "## Metadata",
        "",
        f"- Title: {metadata['title']}",
        f"- Platforms: {', '.join(metadata['platforms'])}",
        f"- Landing URL: {metadata['landingUrl']}",
        f"- Synthetic media disclosure: {metadata['containsSyntheticMedia']}",
        "",
        "## Caption",
        "",
        metadata.get("caption", ""),
        "",
        "## QA",
        "",
        f"- Passed: {qa['passed']}",
    ]
    lines.extend(f"- {name}: {value}" for name, value in qa["requiredChecks"].items())
    lines.extend([
        "",
        "## Approval",
        "",
        f"Reply in Codex with `{manifest['approvalPhrase']}` to approve this exact file for posting.",
    ])
    return "\n".join(lines) + "\n"


def select_drafts(drafts_path: Path, only: str | None, include_longform: bool, limit: int | None) -> list[dict]:
    drafts = read_json(drafts_path, [])
    selected = []
    for draft in drafts:
        if not isinstance(draft, dict):
            continue
        if not include_longform and (draft.get("contentType") == "youtube_long_form" or draft.get("youtubeKind") == "long_form"):
            continue
        if only and only not in {draft.get("file"), draft.get("title")}:
            continue
        selected.append(draft)
    return selected[:limit] if limit else selected


def approve_run(run_id: str, reviewer: str, note: str = "") -> dict:
    conn = connect_db()
    row = conn.execute(
        "SELECT id, draft_file, file_sha256, qa_json, review_video_path, post_metadata_json FROM video_runs WHERE id = ?",
        (run_id,),
    ).fetchone()
    if not row:
        raise ValueError(f"No video run found for {run_id}")
    qa = json.loads(row[3] or "{}")
    if not qa.get("passed"):
        raise ValueError(f"Run {run_id} has not passed QA.")
    review_path = ROOT / row[4]
    current_hash = sha256_file(review_path)
    if current_hash != row[2]:
        raise ValueError("Review file hash changed after QA; regenerate review before approval.")

    approval = {
        "approved": True,
        "reviewer": reviewer,
        "approvedAt": utc_now(),
        "fileSha256": current_hash,
        "runId": run_id,
        "note": note,
    }
    conn.execute(
        "UPDATE video_runs SET state = ?, approval_json = ?, updated_at = ? WHERE id = ?",
        ("APPROVED", json.dumps(approval), utc_now(), run_id),
    )
    conn.commit()
    record_event(conn, run_id, "APPROVED", approval)
    metadata = json.loads(row[5] or "{}")
    update_posts_with_codex_approval(row[1], approval, metadata)
    return approval


def transition_run(run_id: str, state: str, reviewer: str, note: str = "") -> dict:
    if state not in {"REJECTED", "REVISION_REQUESTED"}:
        raise ValueError("transition_run only supports REJECTED or REVISION_REQUESTED")
    conn = connect_db()
    row = conn.execute("SELECT id, draft_file FROM video_runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        raise ValueError(f"No video run found for {run_id}")
    payload = {
        "runId": run_id,
        "state": state,
        "reviewer": reviewer,
        "note": note,
        "updatedAt": utc_now(),
    }
    conn.execute(
        "UPDATE video_runs SET state = ?, approval_json = NULL, updated_at = ? WHERE id = ?",
        (state, utc_now(), run_id),
    )
    conn.commit()
    record_event(conn, run_id, state, payload)
    update_posts_with_review_state(row[1], state, payload)
    return payload


def update_posts_with_review_state(file_ref: str, state: str, payload: dict) -> None:
    posts = read_json(POSTS_PATH, [])
    changed = False
    for post in posts:
        if post.get("file") == file_ref:
            post.pop("codexApproval", None)
            post["reviewStatus"] = state.lower()
            post["status"] = "review_required"
            post["codexReviewDecision"] = payload
            changed = True
    if not changed:
        raise ValueError(f"No post queue entry found for {file_ref}")
    POSTS_PATH.write_text(json.dumps(posts, indent=4) + "\n", encoding="utf-8")


def update_posts_with_codex_approval(file_ref: str, approval: dict, metadata: dict) -> None:
    posts = read_json(POSTS_PATH, [])
    changed = False
    for post in posts:
        if post.get("file") == file_ref:
            post["codexApproval"] = approval
            post["reviewStatus"] = "codex_approved"
            post["landingUrl"] = metadata.get("landingUrl")
            post["containsSyntheticMedia"] = True
            post["youtubeStatus"] = {
                "containsSyntheticMedia": True,
                "selfDeclaredMadeForKids": False,
            }
            changed = True
    if not changed:
        raise ValueError(f"No post queue entry found for {file_ref}")
    POSTS_PATH.write_text(json.dumps(posts, indent=4) + "\n", encoding="utf-8")


def print_review(manifest: dict, json_output: bool) -> None:
    if json_output:
        print(json.dumps(manifest, indent=2))
        return
    print("Codex video review ready")
    print(f"Run ID: {manifest['runId']}")
    print(f"State: {manifest['state']}")
    print(f"Video: {ROOT / manifest['reviewVideo']}")
    print(f"Mobile URL: {manifest.get('mobileReviewUrl') or 'unavailable'}")
    print(f"Serve command: {manifest['serveCommand']}")
    print(f"Title: {manifest['postMetadata']['title']}")
    print(f"Platforms: {', '.join(manifest['postMetadata']['platforms'])}")
    print(f"Landing URL: {manifest['postMetadata']['landingUrl']}")
    print(f"QA passed: {manifest['qa']['passed']}")
    print(f"Approval phrase: {manifest['approvalPhrase']}")


def print_run_list(runs: list[dict], json_output: bool) -> None:
    if json_output:
        print(json.dumps(runs, indent=2))
        return
    if not runs:
        print("No video runs found.")
        return
    for run in runs:
        print(f"{run['id']} [{run['state']}] {run['title']}")
        print(f"  file: {run['draft_file']}")
        if run.get("review_video_path"):
            print(f"  review: {ROOT / run['review_video_path']}")
        if run.get("post_metadata", {}).get("landingUrl"):
            print(f"  landing: {run['post_metadata']['landingUrl']}")


def print_run_status(run: dict, json_output: bool) -> None:
    if json_output:
        print(json.dumps(run, indent=2))
        return
    print(f"Run ID: {run['id']}")
    print(f"State: {run['state']}")
    print(f"Title: {run['title']}")
    print(f"File: {run['draft_file']}")
    print(f"Review video: {ROOT / run['review_video_path'] if run.get('review_video_path') else 'none'}")
    qa = run.get("qa") if isinstance(run.get("qa"), dict) else {}
    if qa:
        print(f"QA passed: {qa.get('passed')}")
        for name, passed in qa.get("requiredChecks", {}).items():
            print(f"  {name}: {passed}")
    print("Events:")
    for event in run.get("events", []):
        print(f"  {event['createdAt']} {event['state']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare, QA, and approve Signal videos through Codex chat.")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare-review", help="Render, promote, QA, and export one or more videos for Codex approval.")
    prepare.add_argument("--drafts", type=Path, default=None, help="Path to autopost_drafts.json. Defaults to newest daily packet.")
    prepare.add_argument("--only", default=None, help="Specific draft file ref or title.")
    prepare.add_argument("--limit", type=int, default=1, help="Number of drafts to prepare; default is 1.")
    prepare.add_argument("--include-longform", action="store_true", help="Allow long-form YouTube drafts.")
    prepare.add_argument("--force-render", action="store_true", help="Render even if the expected output already exists.")
    prepare.add_argument("--json", action="store_true", help="Print JSON.")

    approve = sub.add_parser("approve", help="Mark an exact QA-passed run as approved for posting.")
    approve.add_argument("run_id")
    approve.add_argument("--reviewer", default="codex-chat")
    approve.add_argument("--note", default="")
    approve.add_argument("--json", action="store_true")

    list_cmd = sub.add_parser("list", help="List tracked video runs.")
    list_cmd.add_argument("--state", choices=PIPELINE_STATES, default=None)
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--json", action="store_true")

    status_cmd = sub.add_parser("status", help="Show one video run and its state transition events.")
    status_cmd.add_argument("run_id")
    status_cmd.add_argument("--json", action="store_true")

    reject = sub.add_parser("reject", help="Reject an exact rendered video after Codex review.")
    reject.add_argument("run_id")
    reject.add_argument("--reviewer", default="codex-chat")
    reject.add_argument("--note", default="")
    reject.add_argument("--json", action="store_true")

    revise = sub.add_parser("request-revision", help="Mark a run as requiring revision after Codex review.")
    revise.add_argument("run_id")
    revise.add_argument("--reviewer", default="codex-chat")
    revise.add_argument("--note", default="")
    revise.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if args.command == "prepare-review":
        drafts_path = args.drafts or latest_drafts_path()
        if not drafts_path.is_absolute():
            drafts_path = (ROOT / drafts_path).resolve()
        drafts = select_drafts(drafts_path, args.only, args.include_longform, args.limit)
        if not drafts:
            raise SystemExit("No matching drafts found.")
        manifests = [prepare_review(drafts_path, draft, force_render=args.force_render) for draft in drafts]
        if args.json:
            print(json.dumps(manifests, indent=2))
        else:
            for manifest in manifests:
                print_review(manifest, False)
                print("")
    elif args.command == "approve":
        approval = approve_run(args.run_id, args.reviewer, args.note)
        if args.json:
            print(json.dumps(approval, indent=2))
        else:
            print(f"Codex approval stored for {args.run_id}")
            print(f"Reviewer: {approval['reviewer']}")
            print(f"File hash: {approval['fileSha256']}")
    elif args.command == "list":
        print_run_list(list_runs(args.state, args.limit), args.json)
    elif args.command == "status":
        print_run_status(get_run(args.run_id), args.json)
    elif args.command == "reject":
        result = transition_run(args.run_id, "REJECTED", args.reviewer, args.note)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Run {args.run_id} rejected.")
            print(f"Note: {args.note}")
    elif args.command == "request-revision":
        result = transition_run(args.run_id, "REVISION_REQUESTED", args.reviewer, args.note)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Run {args.run_id} marked REVISION_REQUESTED.")
            print(f"Note: {args.note}")


if __name__ == "__main__":
    main()
