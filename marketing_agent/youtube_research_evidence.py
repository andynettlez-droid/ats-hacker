"""Collect source-backed YouTube evidence for Signal's daily research gate.

The collector separates evidence collection from creative interpretation. It may
save metadata, captions, exact early frames, and a contact sheet, but it never
derives a hook, first-frame observation, beat breakdown, or creative lesson.
Those fields are populated only from an explicitly supplied, human-reviewed
observations file.

Full source videos are not retained. Visual collection is opt-in and uses a
bounded 0-4.2 second temporary yt-dlp download before ffmpeg extracts stills.
Offline fixtures can provide metadata, VTT text, and a local media file.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

try:
    from marketing_agent.daily_research import canonicalize_url, youtube_video_id
except ModuleNotFoundError:  # Direct execution from marketing_agent/.
    from daily_research import canonicalize_url, youtube_video_id


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "marketing" / "research" / "youtube_evidence"
EARLY_FRAME_TIMES = (0.0, 0.5, 1.5, 3.0)
ANALYSIS_FIELDS = (
    "hook_0_3",
    "hook_0_8",
    "first_frame_observation",
    "beat_breakdown",
    "caption_style",
    "visual_mechanic",
    "human_premise",
    "copy",
    "avoid",
    "claim_risk",
    "angle_id",
)
EMPTY_ANALYSIS: dict[str, Any] = {
    "hook_0_3": None,
    "hook_0_8": None,
    "first_frame_observation": None,
    "beat_breakdown": [],
    "caption_style": None,
    "visual_mechanic": None,
    "human_premise": None,
    "copy": None,
    "avoid": None,
    "claim_risk": None,
    "angle_id": None,
    "observation_basis": {},
}


@dataclass(frozen=True)
class CaptionCue:
    start_sec: float
    end_sec: float
    text: str


@dataclass(frozen=True)
class CaptionPayload:
    kind: str
    language: str
    vtt_text: str
    acquisition_basis: str


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nullable_number(value: Any) -> int | float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return int(number) if number.is_integer() else number


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-.")
    return slug[:100] or "youtube-source"


def parse_timestamp(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(float(value), timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if re.fullmatch(r"\d{8}", text):
        try:
            return datetime.strptime(text, "%Y%m%d").replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def canonical_youtube_url(metadata_or_url: Mapping[str, Any] | str) -> str:
    if isinstance(metadata_or_url, str):
        raw = metadata_or_url
        video_id = youtube_video_id(raw)
    else:
        raw = str(
            metadata_or_url.get("webpage_url")
            or metadata_or_url.get("original_url")
            or metadata_or_url.get("url")
            or ""
        )
        video_id = str(metadata_or_url.get("id") or youtube_video_id(raw) or "")
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return canonicalize_url(raw, "youtube")


def _command_error(completed: subprocess.CompletedProcess[str], fallback: str) -> RuntimeError:
    detail = (completed.stderr or completed.stdout or fallback).strip().splitlines()
    return RuntimeError((detail[-1] if detail else fallback)[:1000])


def fetch_metadata(
    url: str,
    *,
    runner: CommandRunner = subprocess.run,
    timeout_sec: int = 60,
) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--dump-single-json",
        "--skip-download",
        "--no-playlist",
        "--no-warnings",
        "--socket-timeout",
        str(timeout_sec),
        url,
    ]
    completed = runner(command, capture_output=True, text=True, timeout=timeout_sec + 20, check=False)
    if completed.returncode != 0:
        raise _command_error(completed, "yt-dlp metadata lookup failed")
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise RuntimeError("yt-dlp metadata output was not a JSON object")
    return value


def discover_query(
    query: str,
    *,
    limit: int = 10,
    runner: CommandRunner = subprocess.run,
    timeout_sec: int = 90,
) -> list[dict[str, Any]]:
    bounded = max(1, min(int(limit), 50))
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--flat-playlist",
        "--dump-json",
        "--skip-download",
        "--no-warnings",
        "--playlist-end",
        str(bounded),
        f"ytsearch{bounded}:{query}",
    ]
    completed = runner(command, capture_output=True, text=True, timeout=timeout_sec, check=False)
    if completed.returncode != 0:
        raise _command_error(completed, "yt-dlp search failed")
    discovered: list[dict[str, Any]] = []
    for rank, line in enumerate(completed.stdout.splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            continue
        url = canonical_youtube_url(item)
        if not url:
            continue
        discovered.append({"url": url, "query": query, "result_rank": rank, "search_metadata": item})
    return discovered


def _vtt_seconds(value: str) -> float:
    pieces = value.strip().replace(",", ".").split(":")
    if len(pieces) == 3:
        hours, minutes, seconds = pieces
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if len(pieces) == 2:
        minutes, seconds = pieces
        return int(minutes) * 60 + float(seconds)
    return float(pieces[0])


def clean_caption_markup(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", value)
    without_positioning = re.sub(r"\{\\[^}]+}", "", without_tags)
    return re.sub(r"\s+", " ", html.unescape(without_positioning)).strip()


def parse_vtt(vtt_text: str) -> list[CaptionCue]:
    lines = vtt_text.replace("\ufeff", "").replace("\r\n", "\n").split("\n")
    cues: list[CaptionCue] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("NOTE"):
            index += 1
            while index < len(lines) and lines[index].strip():
                index += 1
            continue
        if "-->" not in line:
            index += 1
            continue
        start_raw, end_part = line.split("-->", 1)
        end_raw = end_part.strip().split()[0]
        try:
            start_sec = _vtt_seconds(start_raw)
            end_sec = _vtt_seconds(end_raw)
        except (TypeError, ValueError):
            index += 1
            continue
        index += 1
        text_lines: list[str] = []
        while index < len(lines) and lines[index].strip():
            if not lines[index].lstrip().startswith(("NOTE", "STYLE", "REGION")):
                text_lines.append(lines[index])
            index += 1
        text = clean_caption_markup(" ".join(text_lines))
        if text and end_sec >= start_sec:
            cues.append(CaptionCue(start_sec, end_sec, text))
        index += 1
    return cues


_WORD_RE = re.compile(r"[\w]+(?:['’-][\w]+)*", flags=re.UNICODE)


def _surface_tokens(text: str) -> list[str]:
    return _WORD_RE.findall(text)


def _normal_tokens(tokens: Sequence[str]) -> list[str]:
    return [token.casefold().replace("’", "'") for token in tokens]


def _maximum_overlap(existing: Sequence[str], incoming: Sequence[str], limit: int = 80) -> int:
    maximum = min(len(existing), len(incoming), limit)
    for size in range(maximum, 0, -1):
        if list(existing[-size:]) == list(incoming[:size]):
            return size
    return 0


def _adjacent_duplicate_count(tokens: Sequence[str]) -> int:
    return sum(1 for left, right in zip(tokens, tokens[1:]) if left == right)


def clean_rolling_captions(cues: Sequence[CaptionCue]) -> tuple[list[CaptionCue], dict[str, Any]]:
    """Remove the rolling prefix repeated by YouTube auto-caption cues.

    Overlap is matched against the suffix of the complete emitted transcript,
    which handles both growing cues ("this resume" -> "this resume looks") and
    sliding windows ("this resume looks" -> "resume looks fine").
    """

    emitted_normal: list[str] = []
    cleaned: list[CaptionCue] = []
    raw_token_count = 0
    removed_overlap_tokens = 0
    for cue in cues:
        surface = _surface_tokens(cue.text)
        normal = _normal_tokens(surface)
        if not normal:
            continue
        raw_token_count += len(normal)
        overlap = _maximum_overlap(emitted_normal, normal)
        removed_overlap_tokens += overlap
        novel_surface = surface[overlap:]
        novel_normal = normal[overlap:]
        if not novel_surface:
            continue
        cleaned.append(CaptionCue(cue.start_sec, cue.end_sec, " ".join(novel_surface)))
        emitted_normal.extend(novel_normal)

    residual_duplicates = _adjacent_duplicate_count(emitted_normal)
    clean_count = len(emitted_normal)
    coverage = 0.0
    if cues:
        coverage = max(cue.end_sec for cue in cues) - min(cue.start_sec for cue in cues)
    metrics = {
        "raw_token_count": raw_token_count,
        "clean_token_count": clean_count,
        "removed_overlap_token_count": removed_overlap_tokens,
        "rolling_overlap_ratio": round(removed_overlap_tokens / raw_token_count, 6) if raw_token_count else 0.0,
        "duplicate_token_ratio": round(residual_duplicates / clean_count, 6) if clean_count else 0.0,
        "transcript_coverage_sec": round(max(coverage, 0.0), 3),
    }
    return cleaned, metrics


def _format_vtt_time(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def render_vtt(cues: Sequence[CaptionCue]) -> str:
    blocks = ["WEBVTT", ""]
    for index, cue in enumerate(cues, start=1):
        blocks.extend(
            [
                str(index),
                f"{_format_vtt_time(cue.start_sec)} --> {_format_vtt_time(cue.end_sec)}",
                cue.text,
                "",
            ]
        )
    return "\n".join(blocks).rstrip() + "\n"


def choose_caption_track(metadata: Mapping[str, Any]) -> tuple[str, str] | None:
    def choose_language(container: Any) -> str | None:
        if not isinstance(container, Mapping):
            return None
        languages = [str(item) for item in container.keys() if str(item).lower() != "live_chat"]
        priorities = ("en", "en-us", "en-gb", "en-orig")
        lowered = {item.lower(): item for item in languages}
        for candidate in priorities:
            if candidate in lowered:
                return lowered[candidate]
        return next((item for item in languages if item.lower().startswith("en")), None)

    creator_language = choose_language(metadata.get("subtitles"))
    if creator_language:
        return "creator_captions", creator_language
    automatic_language = choose_language(metadata.get("automatic_captions"))
    if automatic_language:
        return "automatic_captions", automatic_language
    return None


def download_caption_payload(
    url: str,
    metadata: Mapping[str, Any],
    destination: Path,
    *,
    runner: CommandRunner = subprocess.run,
    timeout_sec: int = 90,
) -> CaptionPayload | None:
    selected = choose_caption_track(metadata)
    if not selected:
        return None
    kind, language = selected
    destination.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--skip-download",
        "--no-playlist",
        "--no-warnings",
        "--sub-langs",
        language,
        "--sub-format",
        "vtt",
        "--paths",
        str(destination),
        "-o",
        "%(id)s.%(ext)s",
        "--write-subs" if kind == "creator_captions" else "--write-auto-subs",
        url,
    ]
    completed = runner(command, capture_output=True, text=True, timeout=timeout_sec, check=False)
    if completed.returncode != 0:
        raise _command_error(completed, "yt-dlp caption download failed")
    candidates = sorted(destination.glob("*.vtt"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    return CaptionPayload(kind, language, candidates[0].read_text(encoding="utf-8", errors="replace"), "yt-dlp")


def write_caption_evidence(payload: CaptionPayload, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    original_path = output_dir / "captions.original.vtt"
    original_path.write_text(payload.vtt_text, encoding="utf-8")
    raw_cues = parse_vtt(payload.vtt_text)
    cleaned_cues, metrics = clean_rolling_captions(raw_cues)
    cleaned_path = output_dir / "transcript.cleaned.vtt"
    cleaned_path.write_text(render_vtt(cleaned_cues), encoding="utf-8")
    text_path = output_dir / "transcript.txt"
    text_path.write_text(" ".join(cue.text for cue in cleaned_cues).strip() + "\n", encoding="utf-8")
    status = "valid" if cleaned_cues and metrics["transcript_coverage_sec"] > 0 else "invalid"
    return {
        "transcript_status": status,
        "transcript_kind": payload.kind,
        "transcript_path": str(cleaned_path.resolve()),
        "transcript_sha256": sha256_file(cleaned_path),
        "transcript_coverage_sec": metrics["transcript_coverage_sec"],
        "duplicate_token_ratio": metrics["duplicate_token_ratio"],
        "caption_metrics": metrics,
        "provenance": {
            "basis": payload.acquisition_basis,
            "kind": payload.kind,
            "language": payload.language,
            "original_path": str(original_path.resolve()),
            "original_sha256": sha256_file(original_path),
            "cleaned_path": str(cleaned_path.resolve()),
            "cleaned_sha256": sha256_file(cleaned_path),
            "text_path": str(text_path.resolve()),
            "text_sha256": sha256_file(text_path),
            **metrics,
        },
    }


def download_bounded_preview(
    url: str,
    destination: Path,
    *,
    runner: CommandRunner = subprocess.run,
    timeout_sec: int = 150,
    max_megabytes: int = 40,
    max_height: int = 720,
    end_sec: float = 4.2,
) -> tuple[Path, dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=True)
    output_template = destination / "bounded-source.%(ext)s"
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "--no-warnings",
        "--download-sections",
        f"*0-{end_sec:.3f}",
        "--force-keyframes-at-cuts",
        "--max-filesize",
        f"{max_megabytes}M",
        "-f",
        f"bestvideo[height<={max_height}]/best[height<={max_height}]",
        "--merge-output-format",
        "mp4",
        "-o",
        str(output_template),
        url,
    ]
    completed = runner(command, capture_output=True, text=True, timeout=timeout_sec, check=False)
    if completed.returncode != 0:
        raise _command_error(completed, "bounded yt-dlp preview download failed")
    candidates = [path for path in destination.glob("bounded-source.*") if path.is_file()]
    if not candidates:
        raise RuntimeError("bounded yt-dlp preview produced no media file")
    media = max(candidates, key=lambda item: item.stat().st_size)
    size_bytes = media.stat().st_size
    if size_bytes > max_megabytes * 1024 * 1024:
        media.unlink(missing_ok=True)
        raise RuntimeError("bounded preview exceeded the configured byte limit")
    return media, {
        "basis": "yt-dlp-bounded-temporary-download",
        "retained": False,
        "section_start_sec": 0.0,
        "section_end_sec": end_sec,
        "max_megabytes": max_megabytes,
        "max_height": max_height,
        "downloaded_bytes": size_bytes,
    }


def _run_ffmpeg(command: list[str], runner: CommandRunner, timeout_sec: int = 90) -> None:
    completed = runner(command, capture_output=True, text=True, timeout=timeout_sec, check=False)
    if completed.returncode != 0:
        raise _command_error(completed, "ffmpeg evidence render failed")


def capture_visual_evidence(
    media_path: Path,
    output_dir: Path,
    *,
    times: Sequence[float] = EARLY_FRAME_TIMES,
    runner: CommandRunner = subprocess.run,
    ffmpeg_bin: str = "ffmpeg",
) -> dict[str, Any]:
    if len(times) != 4:
        raise ValueError("visual evidence requires exactly four early frame times")
    output_dir.mkdir(parents=True, exist_ok=True)
    frame_records: list[dict[str, Any]] = []
    frame_paths: list[Path] = []
    for position, raw_time in enumerate(times):
        timestamp = float(raw_time)
        frame_path = output_dir / f"frame_{position:02d}_{timestamp:05.2f}s.png"
        command = [
            ffmpeg_bin,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(media_path),
            "-ss",
            f"{timestamp:.3f}",
            "-map",
            "0:v:0",
            "-frames:v",
            "1",
            "-compression_level",
            "4",
            str(frame_path),
        ]
        _run_ffmpeg(command, runner)
        if not frame_path.exists() or frame_path.stat().st_size == 0:
            raise RuntimeError(f"ffmpeg did not create the {timestamp:.3f}s evidence frame")
        frame_paths.append(frame_path)
        frame_records.append(
            {"time_sec": timestamp, "path": str(frame_path.resolve()), "sha256": sha256_file(frame_path)}
        )

    contact_sheet = output_dir / "early_frames_contact_sheet.png"
    inputs: list[str] = []
    filters: list[str] = []
    for index, frame_path in enumerate(frame_paths):
        inputs.extend(["-i", str(frame_path)])
        filters.append(
            f"[{index}:v]scale=540:960:force_original_aspect_ratio=decrease,"
            f"pad=540:960:(ow-iw)/2:(oh-ih)/2:color=black[s{index}]"
        )
    layout = "0_0|540_0|0_960|540_960"
    filter_complex = ";".join(filters) + ";[s0][s1][s2][s3]" + f"xstack=inputs=4:layout={layout}:fill=black[out]"
    sheet_command = [
        ffmpeg_bin,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-frames:v",
        "1",
        "-compression_level",
        "4",
        str(contact_sheet),
    ]
    _run_ffmpeg(sheet_command, runner)
    if not contact_sheet.exists() or contact_sheet.stat().st_size == 0:
        raise RuntimeError("ffmpeg did not create the source contact sheet")
    return {
        "media_status": "captured_unreviewed",
        "contact_sheet_path": str(contact_sheet.resolve()),
        "contact_sheet_times_sec": [float(item) for item in times],
        "provenance": {
            "basis": "ffmpeg-exact-frame-capture",
            "source_media_sha256": sha256_file(media_path),
            "frames": frame_records,
            "contact_sheet_path": str(contact_sheet.resolve()),
            "contact_sheet_sha256": sha256_file(contact_sheet),
            "contact_sheet_times_sec": [float(item) for item in times],
        },
    }


def normalize_metadata(
    metadata: Mapping[str, Any],
    *,
    query: str | None,
    result_rank: int | None,
    collected_at: datetime,
) -> dict[str, Any]:
    canonical_url = canonical_youtube_url(metadata)
    video_id = str(metadata.get("id") or youtube_video_id(canonical_url) or "")
    published_at = parse_timestamp(metadata.get("timestamp")) or parse_timestamp(metadata.get("upload_date"))
    creator_id = str(metadata.get("channel_id") or metadata.get("uploader_id") or "").strip() or None
    creator_name = str(metadata.get("channel") or metadata.get("uploader") or "").strip() or None
    fingerprint = sha256_bytes(
        stable_json(
            {
                "platform": "youtube",
                "id": video_id or None,
                "url": canonical_url or None,
                "creator": creator_id or creator_name,
                "title": metadata.get("title"),
            }
        ).encode("utf-8")
    )
    return {
        "source_id": f"youtube-{video_id or fingerprint[:12]}",
        "platform": "youtube",
        "platform_post_id": video_id or None,
        "canonical_url": canonical_url,
        "creator_id": creator_id,
        "creator_name": creator_name,
        "title": str(metadata.get("title") or "").strip() or None,
        "query": query,
        "discovery_surface": "yt-dlp-search" if query else "direct-url",
        "result_rank": result_rank,
        "first_seen_at": collected_at.isoformat(),
        "collected_at": collected_at.isoformat(),
        "prior_run_ids": [],
        "content_fingerprint": fingerprint,
        "published_at": published_at,
        "views": nullable_number(metadata.get("view_count")),
        "likes": nullable_number(metadata.get("like_count")),
        "comments": nullable_number(metadata.get("comment_count")),
        "shares": nullable_number(
            metadata.get("repost_count") if metadata.get("repost_count") is not None else metadata.get("share_count")
        ),
        "metrics_captured_at": collected_at.isoformat(),
        "duration_sec": nullable_number(metadata.get("duration")),
        "format_kind": "short"
        if nullable_number(metadata.get("duration")) is None or float(metadata.get("duration") or 0) <= 90
        else "authority_long_form",
        "metadata_status": "available",
        "transcript_status": "missing",
        "transcript_kind": None,
        "transcript_path": None,
        "transcript_sha256": None,
        "transcript_coverage_sec": None,
        "duplicate_token_ratio": None,
        "media_status": "not_requested",
        "contact_sheet_path": None,
        "contact_sheet_times_sec": [],
        "access_state": "not_observed",
        "observer": None,
        "observed_at": None,
        "screenshot_paths": [],
        "visible_caption": None,
        "visible_metrics": None,
        "audio_observed": False,
        **EMPTY_ANALYSIS,
    }


def bound_sources(
    sources: Iterable[dict[str, Any]],
    *,
    max_sources: int,
    creator_cap: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen_ids: set[str] = set()
    creator_counts: dict[str, int] = {}
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for source in sources:
        identity = str(source.get("platform_post_id") or source.get("canonical_url") or source.get("source_id") or "")
        creator = str(source.get("creator_id") or source.get("creator_name") or source.get("source_id") or "").casefold()
        reason = None
        if identity in seen_ids:
            reason = "duplicate_source"
        elif creator_counts.get(creator, 0) >= max(1, creator_cap):
            reason = "creator_cap"
        elif len(kept) >= max(1, max_sources):
            reason = "source_cap"
        if reason:
            dropped.append({"source_id": source.get("source_id"), "reason": reason})
            continue
        seen_ids.add(identity)
        creator_counts[creator] = creator_counts.get(creator, 0) + 1
        kept.append(source)
    return kept, dropped


def _observation_candidates(payload: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(payload, Mapping) and isinstance(payload.get("sources"), list):
        return [item for item in payload["sources"] if isinstance(item, Mapping)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, Mapping)]
    if isinstance(payload, Mapping):
        values: list[Mapping[str, Any]] = []
        for key, value in payload.items():
            if isinstance(value, Mapping):
                values.append({"lookup_key": str(key), **value})
        return values
    return []


def find_reviewed_observation(record: Mapping[str, Any], payload: Any) -> Mapping[str, Any] | None:
    keys = {
        str(record.get("source_id") or ""),
        str(record.get("platform_post_id") or ""),
        str(record.get("canonical_url") or ""),
    }
    keys.discard("")
    for candidate in _observation_candidates(payload):
        candidate_keys = {
            str(candidate.get("source_id") or ""),
            str(candidate.get("platform_post_id") or ""),
            str(candidate.get("canonical_url") or candidate.get("url") or ""),
            str(candidate.get("lookup_key") or ""),
        }
        if keys.intersection(item for item in candidate_keys if item):
            return candidate
    return None


def apply_reviewed_observation(
    record: dict[str, Any],
    observation: Mapping[str, Any] | None,
    *,
    observations_path: Path | None = None,
) -> dict[str, Any]:
    result = dict(record)
    if not observation:
        return result
    for field in ANALYSIS_FIELDS:
        if field not in observation:
            continue
        value = observation[field]
        if field == "beat_breakdown":
            result[field] = [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []
        else:
            result[field] = value if value not in (None, "") else None
    basis = observation.get("observation_basis")
    result["observation_basis"] = dict(basis) if isinstance(basis, Mapping) else {}
    if any(result.get(field) not in (None, "", [], {}) for field in ANALYSIS_FIELDS):
        result["media_status"] = "reviewed" if result.get("contact_sheet_path") else result.get("media_status")
    provenance = dict(result.get("evidence_provenance") or {})
    provenance["reviewed_observation"] = {
        "basis": "supplied-reviewed-observations-json",
        "reviewer": observation.get("reviewer"),
        "reviewed_at": parse_timestamp(observation.get("reviewed_at")),
        "path": str(observations_path.resolve()) if observations_path else None,
        "sha256": sha256_file(observations_path) if observations_path and observations_path.exists() else None,
        "supplied_fields": [
            field for field in ANALYSIS_FIELDS if result.get(field) not in (None, "", [], {})
        ],
    }
    result["evidence_provenance"] = provenance
    return result


class FixtureStore:
    """Offline source provider.

    Format:
      {"queries": {"query": ["video-id", {"id": "other"}]},
       "sources": {"video-id": {"metadata": {...}, "vtt": "...",
                                  "caption_kind": "creator_captions",
                                  "media_path": "..."}}}
    """

    def __init__(self, path: Path):
        value = read_json(path)
        if not isinstance(value, Mapping):
            raise ValueError("fixture JSON must be an object")
        self.path = path
        self.base = path.parent
        self.queries = value.get("queries") if isinstance(value.get("queries"), Mapping) else {}
        self.sources = value.get("sources") if isinstance(value.get("sources"), Mapping) else {}

    def _keys(self, candidate: Mapping[str, Any] | str) -> list[str]:
        if isinstance(candidate, str):
            url = candidate
            video_id = youtube_video_id(candidate) or candidate
        else:
            url = str(candidate.get("url") or candidate.get("canonical_url") or "")
            video_id = str(candidate.get("id") or youtube_video_id(url) or "")
        return [item for item in (video_id, url, canonicalize_url(url, "youtube") if url else "") if item]

    def entry(self, candidate: Mapping[str, Any] | str) -> Mapping[str, Any]:
        for key in self._keys(candidate):
            value = self.sources.get(key)
            if isinstance(value, Mapping):
                return value
        raise KeyError(f"fixture has no source for {self._keys(candidate)!r}")

    def discover(self, query: str, limit: int) -> list[dict[str, Any]]:
        values = self.queries.get(query, [])
        if not isinstance(values, list):
            raise ValueError(f"fixture query {query!r} must contain a list")
        discovered: list[dict[str, Any]] = []
        for rank, item in enumerate(values[: max(1, limit)], start=1):
            if isinstance(item, str):
                entry = self.entry(item)
                metadata = entry.get("metadata") if isinstance(entry.get("metadata"), Mapping) else {}
                url = canonical_youtube_url(metadata) or canonical_youtube_url(item)
            elif isinstance(item, Mapping):
                url = canonical_youtube_url(item)
            else:
                continue
            discovered.append({"url": url, "query": query, "result_rank": rank})
        return discovered

    def metadata(self, candidate: Mapping[str, Any] | str) -> dict[str, Any]:
        entry = self.entry(candidate)
        metadata = entry.get("metadata")
        if not isinstance(metadata, Mapping):
            raise ValueError("fixture source requires a metadata object")
        return dict(metadata)

    def caption(self, candidate: Mapping[str, Any] | str) -> CaptionPayload | None:
        entry = self.entry(candidate)
        vtt = entry.get("vtt")
        if vtt is None and entry.get("vtt_path"):
            path = Path(str(entry["vtt_path"]))
            if not path.is_absolute():
                path = self.base / path
            vtt = path.read_text(encoding="utf-8")
        if not isinstance(vtt, str) or not vtt.strip():
            return None
        return CaptionPayload(
            str(entry.get("caption_kind") or "creator_captions"),
            str(entry.get("caption_language") or "en"),
            vtt,
            "offline-fixture",
        )

    def media(self, candidate: Mapping[str, Any] | str) -> Path | None:
        entry = self.entry(candidate)
        if not entry.get("media_path"):
            return None
        path = Path(str(entry["media_path"]))
        return path if path.is_absolute() else self.base / path


def collect_source_evidence(
    metadata: Mapping[str, Any],
    *,
    output_root: Path,
    query: str | None,
    result_rank: int | None,
    collected_at: datetime,
    caption_payload: CaptionPayload | None = None,
    media_path: Path | None = None,
    media_download_provenance: Mapping[str, Any] | None = None,
    reviewed_observation: Mapping[str, Any] | None = None,
    observations_path: Path | None = None,
    metadata_basis: str = "yt-dlp",
    runner: CommandRunner = subprocess.run,
) -> dict[str, Any]:
    record = normalize_metadata(metadata, query=query, result_rank=result_rank, collected_at=collected_at)
    source_dir = output_root / safe_slug(str(record["source_id"]))
    source_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = source_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    record["evidence_provenance"] = {
        "metadata": {
            "basis": metadata_basis,
            "path": str(metadata_path.resolve()),
            "sha256": sha256_file(metadata_path),
            "captured_at": collected_at.isoformat(),
        }
    }
    if caption_payload:
        caption = write_caption_evidence(caption_payload, source_dir / "captions")
        record.update({key: value for key, value in caption.items() if key != "provenance"})
        record["evidence_provenance"]["transcript"] = caption["provenance"]
    if media_path:
        visual = capture_visual_evidence(media_path, source_dir / "visual", runner=runner)
        record.update({key: value for key, value in visual.items() if key != "provenance"})
        visual_provenance = dict(visual["provenance"])
        visual_provenance["source_acquisition"] = dict(media_download_provenance or {"basis": "offline-fixture"})
        record["evidence_provenance"]["visual"] = visual_provenance
    record = apply_reviewed_observation(record, reviewed_observation, observations_path=observations_path)
    record["evidence_sha256"] = sha256_bytes(stable_json(record["evidence_provenance"]).encode("utf-8"))
    return record


def _candidate_key(candidate: Mapping[str, Any]) -> str:
    return str(candidate.get("url") or candidate.get("canonical_url") or "")


def collect(
    *,
    urls: Sequence[str],
    queries: Sequence[str],
    output_dir: Path,
    query_limit: int = 10,
    max_sources: int = 20,
    creator_cap: int = 2,
    capture_visuals: bool = False,
    collect_captions: bool = True,
    reviewed_observations: Any = None,
    observations_path: Path | None = None,
    fixture: FixtureStore | None = None,
    runner: CommandRunner = subprocess.run,
    collected_at: datetime | None = None,
) -> dict[str, Any]:
    captured_at = (collected_at or utc_now()).astimezone(timezone.utc)
    candidates: list[dict[str, Any]] = [
        {"url": canonical_youtube_url(url), "query": None, "result_rank": None} for url in urls
    ]
    discovery_errors: list[dict[str, str]] = []
    for query in queries:
        try:
            found = fixture.discover(query, query_limit) if fixture else discover_query(query, limit=query_limit, runner=runner)
            candidates.extend(found)
        except Exception as error:
            discovery_errors.append({"query": query, "error": str(error)[:1000]})

    metadata_rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    collection_errors: list[dict[str, str]] = []
    for candidate in candidates:
        try:
            metadata = fixture.metadata(candidate) if fixture else fetch_metadata(_candidate_key(candidate), runner=runner)
            normalized = normalize_metadata(
                metadata,
                query=candidate.get("query"),
                result_rank=candidate.get("result_rank"),
                collected_at=captured_at,
            )
            metadata_rows.append((candidate, {"raw": metadata, "normalized": normalized}))
        except Exception as error:
            collection_errors.append({"url": _candidate_key(candidate), "stage": "metadata", "error": str(error)[:1000]})

    normalized_rows = [value["normalized"] for _, value in metadata_rows]
    kept, dropped = bound_sources(normalized_rows, max_sources=max_sources, creator_cap=creator_cap)
    kept_ids = {str(item["source_id"]) for item in kept}
    selected: list[tuple[dict[str, Any], dict[str, Any]]] = []
    selected_ids: set[str] = set()
    for candidate, value in metadata_rows:
        source_id = str(value["normalized"]["source_id"])
        if source_id in kept_ids and source_id not in selected_ids:
            selected.append((candidate, value))
            selected_ids.add(source_id)

    output_dir.mkdir(parents=True, exist_ok=True)
    sources: list[dict[str, Any]] = []
    for candidate, value in selected:
        metadata = value["raw"]
        normalized = value["normalized"]
        source_id = str(normalized["source_id"])
        caption_payload = None
        if collect_captions:
            try:
                if fixture:
                    caption_payload = fixture.caption(candidate)
                else:
                    with tempfile.TemporaryDirectory(prefix="signal-youtube-captions-") as temporary:
                        caption_payload = download_caption_payload(
                            str(normalized["canonical_url"]), metadata, Path(temporary), runner=runner
                        )
            except Exception as error:
                collection_errors.append(
                    {"source_id": source_id, "stage": "captions", "error": str(error)[:1000]}
                )
        try:
            source = collect_source_evidence(
                metadata,
                output_root=output_dir,
                query=candidate.get("query"),
                result_rank=candidate.get("result_rank"),
                collected_at=captured_at,
                caption_payload=caption_payload,
                metadata_basis="offline-fixture" if fixture else "yt-dlp",
                runner=runner,
            )
        except Exception as error:
            collection_errors.append(
                {"source_id": source_id, "stage": "source_artifacts", "error": str(error)[:1000]}
            )
            continue

        if capture_visuals:
            source_dir = output_dir / safe_slug(source_id)
            visual: dict[str, Any] | None = None
            media_provenance: dict[str, Any] | None = None
            try:
                if fixture:
                    media = fixture.media(candidate)
                    if not media or not media.exists():
                        raise RuntimeError("fixture visual capture requested but media_path is missing")
                    media_provenance = {"basis": "offline-fixture", "retained": True}
                    visual = capture_visual_evidence(media, source_dir / "visual", runner=runner)
                else:
                    with tempfile.TemporaryDirectory(prefix="signal-youtube-visual-") as temporary:
                        media, media_provenance = download_bounded_preview(
                            str(normalized["canonical_url"]), Path(temporary), runner=runner
                        )
                        visual = capture_visual_evidence(media, source_dir / "visual", runner=runner)
                source.update({key: item for key, item in visual.items() if key != "provenance"})
                visual_provenance = dict(visual["provenance"])
                visual_provenance["source_acquisition"] = media_provenance
                source["evidence_provenance"]["visual"] = visual_provenance
            except Exception as error:
                source["media_status"] = "capture_failed"
                source.setdefault("evidence_errors", []).append(
                    {"stage": "visual", "error": str(error)[:1000]}
                )
                collection_errors.append(
                    {"source_id": source_id, "stage": "visual", "error": str(error)[:1000]}
                )

        observation = find_reviewed_observation(source, reviewed_observations)
        source = apply_reviewed_observation(source, observation, observations_path=observations_path)
        source["evidence_sha256"] = sha256_bytes(
            stable_json(source.get("evidence_provenance") or {}).encode("utf-8")
        )
        sources.append(source)

    manifest = {
        "schema_version": 1,
        "collector": "youtube_research_evidence_v1",
        "collected_at": captured_at.isoformat(),
        "urls": [canonical_youtube_url(url) for url in urls],
        "queries": list(queries),
        "query_limit": max(1, query_limit),
        "max_sources": max(1, max_sources),
        "creator_cap": max(1, creator_cap),
        "capture_visuals": capture_visuals,
        "collect_captions": collect_captions,
        "frame_times_sec": list(EARLY_FRAME_TIMES),
        "candidate_count": len(candidates),
        "metadata_count": len(metadata_rows),
        "source_count": len(sources),
        "dropped": dropped,
        "errors": [*discovery_errors, *collection_errors],
    }
    manifest["manifest_sha256"] = sha256_bytes(stable_json({**manifest, "manifest_sha256": None}).encode("utf-8"))
    payload = {"manifest": manifest, "sources": sources}
    output_path = output_dir / "youtube_evidence.json"
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    payload["manifest"]["output_path"] = str(output_path.resolve())
    payload["manifest"]["output_sha256"] = sha256_file(output_path)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect factual YouTube metadata, caption, and optional visual evidence for daily research."
    )
    parser.add_argument("--url", action="append", default=[], help="YouTube URL; repeat for multiple sources.")
    parser.add_argument("--query", action="append", default=[], help="yt-dlp search query; repeat as needed.")
    parser.add_argument("--query-limit", type=int, default=10, help="Maximum candidates discovered per query (1-50).")
    parser.add_argument("--max-sources", type=int, default=20, help="Hard cap on emitted source records.")
    parser.add_argument("--creator-cap", type=int, default=2, help="Hard cap on emitted sources per creator.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--capture-visuals",
        action="store_true",
        help="Explicitly permit a bounded temporary 0-4.2s media download for exact frames/contact sheet.",
    )
    parser.add_argument("--no-captions", action="store_true", help="Skip creator and automatic caption collection.")
    parser.add_argument("--reviewed-observations", type=Path, help="Human-reviewed analysis JSON; never inferred here.")
    parser.add_argument("--fixture-json", type=Path, help="Offline fixture with queries, metadata, VTT, and media paths.")
    parser.add_argument("--fail-on-error", action="store_true", help="Return exit code 2 when any source stage fails.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.url and not args.query:
        raise SystemExit("Provide at least one --url or --query.")
    fixture = FixtureStore(args.fixture_json) if args.fixture_json else None
    reviewed = read_json(args.reviewed_observations) if args.reviewed_observations else None
    payload = collect(
        urls=args.url,
        queries=args.query,
        output_dir=args.output_dir,
        query_limit=max(1, min(args.query_limit, 50)),
        max_sources=max(1, args.max_sources),
        creator_cap=max(1, args.creator_cap),
        capture_visuals=args.capture_visuals,
        collect_captions=not args.no_captions,
        reviewed_observations=reviewed,
        observations_path=args.reviewed_observations,
        fixture=fixture,
    )
    summary = {
        "sourceCount": payload["manifest"]["source_count"],
        "errorCount": len(payload["manifest"]["errors"]),
        "outputPath": payload["manifest"]["output_path"],
        "outputSha256": payload["manifest"]["output_sha256"],
        "visualCapture": payload["manifest"]["capture_visuals"],
    }
    print(json.dumps(summary, indent=2))
    return 2 if args.fail_on_error and summary["errorCount"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
