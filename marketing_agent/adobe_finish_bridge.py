#!/usr/bin/env python3
"""Fail-closed Adobe finishing handoff for controlled-screen Signal shorts.

The bridge deliberately does not generate an After Effects project. The local
AfterFX command-line scripting path is not reliable enough to make that claim.
It prepares a hash-bound handoff, requires an explicit review of a manually
created project, may render that reviewed project with aerender, and restores
the source AAC packets when producing the final MP4.

No command in this module publishes media.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA_VERSION = "signal.adobe_finish_manifest.v1"
PROJECT_REVIEW_SCHEMA_VERSION = "signal.adobe_finish_project_review.v1"
VALIDATION_RECEIPT_SCHEMA_VERSION = "signal.adobe_finish_validation.v1"
EXPECTED_WIDTH = 1080
EXPECTED_HEIGHT = 1920
MAX_BEAT_DELTA_SEC = Fraction(1, 2)
TIMING_TOLERANCE_SEC = Fraction(1, 1000)
REVIEW_COMP_NAME = "Signal Controlled Screen Finish"
ALLOWED_EFFECT_IDS = (
    "marker_sweep",
    "screen_paper_texture",
    "soft_shadow",
    "cta_polish",
)
REQUIRED_PROJECT_CHECKS = (
    "singleBakedSourceLayer",
    "sourceTransformLocked",
    "noTextLayers",
    "allowedEffectsOnly",
    "noAudioLayers",
    "noTimeRemap",
    "noPublishActions",
)
DIRECT_GENERATION_REASON = (
    "AfterFX command-line ExtendScript project generation is disabled: the local "
    "bridge has hung without creating its smoke-test project. Use a manually built, "
    "reviewed, hash-bound AEP instead."
)


class BridgeError(RuntimeError):
    """Base class for an Adobe finish bridge failure."""


class ReadinessError(BridgeError):
    """Raised when required tools or source inputs are not ready."""


class ContractError(BridgeError):
    """Raised when a manifest or review violates the finish contract."""


class OutputValidationError(BridgeError):
    """Raised when an Adobe or final output fails media validation."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _json_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _fraction(value: Any, label: str) -> Fraction:
    try:
        result = Fraction(str(value))
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{label} is not a finite number: {value!r}") from exc
    if not math.isfinite(float(result)):
        raise ValueError(f"{label} is not finite")
    return result


def _fraction_string(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _fraction_from_string(value: Any, label: str) -> Fraction:
    return _fraction(value, label)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"Could not read JSON {path}: {exc}") from exc


def _candidate_executable(value: str, which: Callable[[str], str | None]) -> Path | None:
    raw = Path(value).expanduser()
    if raw.is_file():
        return raw.resolve()
    located = which(value)
    if located and Path(located).is_file():
        return Path(located).resolve()
    return None


def _environment_value(environ: Mapping[str, str], key: str) -> str | None:
    wanted = key.casefold()
    for existing_key, value in environ.items():
        if existing_key.casefold() == wanted:
            return value
    return None


def _adobe_candidates(executable: str, environ: Mapping[str, str], system_name: str) -> list[Path]:
    candidates: list[Path] = []
    if system_name.casefold() == "windows":
        for env_name in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
            base = _environment_value(environ, env_name)
            if not base:
                continue
            adobe_root = Path(base) / "Adobe"
            if adobe_root.is_dir():
                installs = sorted(adobe_root.glob("Adobe After Effects *"), key=lambda path: path.name, reverse=True)
                candidates.extend(install / "Support Files" / executable for install in installs)
        return candidates

    if system_name.casefold() == "darwin":
        applications = Path("/Applications")
        if applications.is_dir():
            installs = sorted(applications.glob("Adobe After Effects *"), key=lambda path: path.name, reverse=True)
            for install in installs:
                app_bundles = sorted(install.glob("Adobe After Effects *.app"), reverse=True)
                for bundle in app_bundles:
                    candidates.append(bundle / "Contents" / "MacOS" / executable)
    return candidates


def _locate_tool(
    *,
    explicit: str | Path | None,
    environment_keys: Sequence[str],
    command_names: Sequence[str],
    candidates: Sequence[Path],
    environ: Mapping[str, str],
    which: Callable[[str], str | None],
) -> dict[str, Any]:
    if explicit is not None:
        path = _candidate_executable(str(explicit), which)
        return {"found": path is not None, "path": str(path) if path else None, "source": "explicit"}

    for key in environment_keys:
        value = _environment_value(environ, key)
        if value:
            path = _candidate_executable(value, which)
            return {
                "found": path is not None,
                "path": str(path) if path else None,
                "source": f"environment:{key}",
            }

    for name in command_names:
        located = which(name)
        if located and Path(located).is_file():
            path = Path(located).resolve()
            return {"found": True, "path": str(path), "source": f"PATH:{name}"}

    for candidate in candidates:
        if candidate.is_file():
            return {"found": True, "path": str(candidate.resolve()), "source": "installed"}
    return {"found": False, "path": None, "source": "not_found"}


def _adobe_install_root(path: str) -> str:
    resolved = Path(path).resolve()
    for parent in (resolved, *resolved.parents):
        if parent.name.casefold().endswith(".app"):
            return os.path.normcase(str(parent))
    return os.path.normcase(str(resolved.parent))


def detect_tools(
    *,
    afterfx_path: str | Path | None = None,
    aerender_path: str | Path | None = None,
    ffprobe_path: str | Path | None = None,
    ffmpeg_path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    which: Callable[[str], str | None] | None = None,
    system_name: str | None = None,
) -> dict[str, Any]:
    """Locate the exact tools used by the bridge without launching Adobe."""

    environment = dict(os.environ if environ is None else environ)
    find_on_path = shutil.which if which is None else which
    system = platform.system() if system_name is None else system_name

    afterfx = _locate_tool(
        explicit=afterfx_path,
        environment_keys=("SIGNAL_AFTERFX_PATH", "AFTERFX_PATH"),
        command_names=("AfterFX.exe", "AfterFX.com", "AfterFX"),
        candidates=_adobe_candidates("AfterFX.exe" if system.casefold() == "windows" else "After Effects", environment, system),
        environ=environment,
        which=find_on_path,
    )
    aerender = _locate_tool(
        explicit=aerender_path,
        environment_keys=("SIGNAL_AERENDER_PATH", "AERENDER_PATH"),
        command_names=("aerender.exe", "aerender"),
        candidates=_adobe_candidates("aerender.exe" if system.casefold() == "windows" else "aerender", environment, system),
        environ=environment,
        which=find_on_path,
    )
    ffprobe = _locate_tool(
        explicit=ffprobe_path,
        environment_keys=("SIGNAL_FFPROBE_PATH", "FFPROBE_PATH"),
        command_names=("ffprobe.exe", "ffprobe"),
        candidates=(),
        environ=environment,
        which=find_on_path,
    )
    ffmpeg = _locate_tool(
        explicit=ffmpeg_path,
        environment_keys=("SIGNAL_FFMPEG_PATH", "FFMPEG_PATH"),
        command_names=("ffmpeg.exe", "ffmpeg"),
        candidates=(),
        environ=environment,
        which=find_on_path,
    )

    blockers: list[str] = []
    labels = {
        "afterEffects": ("After Effects", afterfx),
        "aerender": ("aerender", aerender),
        "ffprobe": ("ffprobe", ffprobe),
        "ffmpeg": ("ffmpeg", ffmpeg),
    }
    for _, (label, record) in labels.items():
        if not record["found"]:
            blockers.append(f"{label} is unavailable")

    same_install = False
    if afterfx["found"] and aerender["found"]:
        same_install = _adobe_install_root(afterfx["path"]) == _adobe_install_root(aerender["path"])
        if not same_install:
            blockers.append("After Effects and aerender are not from the same installation")

    return {
        "ready": not blockers,
        "sameAdobeInstall": same_install,
        "afterEffects": afterfx,
        "aerender": aerender,
        "ffprobe": ffprobe,
        "ffmpeg": ffmpeg,
        "blockers": blockers,
    }


def _run_json(command: Sequence[str], *, timeout_sec: int = 120) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReadinessError(f"Could not run {command[0]}: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise ReadinessError(f"{command[0]} failed: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ReadinessError(f"{command[0]} returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ReadinessError(f"{command[0]} returned a non-object JSON payload")
    return payload


def probe_media(path: Path, ffprobe_path: str) -> dict[str, Any]:
    return _run_json(
        (
            ffprobe_path,
            "-v",
            "error",
            "-count_frames",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        )
    )


def _stream_time(stream: Mapping[str, Any], *, duration: bool, fallback: Fraction | None = None) -> Fraction:
    integer_key = "duration_ts" if duration else "start_pts"
    decimal_key = "duration" if duration else "start_time"
    integer_value = stream.get(integer_key)
    time_base = stream.get("time_base")
    if integer_value not in (None, "N/A") and time_base not in (None, "N/A", "0/0"):
        return _fraction(integer_value, integer_key) * _fraction(time_base, "time_base")
    decimal_value = stream.get(decimal_key)
    if decimal_value not in (None, "N/A"):
        return _fraction(decimal_value, decimal_key)
    if fallback is not None:
        return fallback
    raise ValueError(f"stream has no usable {decimal_key}")


def _frame_count(stream: Mapping[str, Any]) -> int:
    for key in ("nb_read_frames", "nb_frames"):
        value = stream.get(key)
        if value not in (None, "N/A"):
            count = int(value)
            if count > 0:
                return count
    raise ValueError("video stream has no counted frames")


def _rotation(stream: Mapping[str, Any]) -> int:
    tags = stream.get("tags")
    if isinstance(tags, Mapping) and tags.get("rotate") not in (None, ""):
        try:
            return int(round(float(tags["rotate"]))) % 360
        except (TypeError, ValueError):
            return 1
    side_data = stream.get("side_data_list")
    if isinstance(side_data, list):
        for item in side_data:
            if isinstance(item, Mapping) and item.get("rotation") not in (None, ""):
                try:
                    return int(round(float(item["rotation"]))) % 360
                except (TypeError, ValueError):
                    return 1
    return 0


def summarize_probe(payload: Mapping[str, Any]) -> dict[str, Any]:
    streams = payload.get("streams")
    if not isinstance(streams, list):
        raise ValueError("ffprobe payload contains no streams")
    videos = [item for item in streams if isinstance(item, Mapping) and item.get("codec_type") == "video"]
    audios = [item for item in streams if isinstance(item, Mapping) and item.get("codec_type") == "audio"]
    others = [
        item
        for item in streams
        if isinstance(item, Mapping) and item.get("codec_type") not in {"video", "audio"}
    ]
    format_payload = payload.get("format")
    format_names = []
    if isinstance(format_payload, Mapping):
        format_names = [name.strip().casefold() for name in str(format_payload.get("format_name") or "").split(",") if name.strip()]

    summary: dict[str, Any] = {
        "videoStreamCount": len(videos),
        "audioStreamCount": len(audios),
        "otherStreamCount": len(others),
        "otherStreamTypes": sorted({str(item.get("codec_type") or "unknown") for item in others}),
        "formatNames": format_names,
        "video": None,
        "audio": None,
    }
    if videos:
        stream = videos[0]
        frame_rate = _fraction(stream.get("avg_frame_rate"), "avg_frame_rate")
        nominal_rate = _fraction(stream.get("r_frame_rate"), "r_frame_rate")
        count = _frame_count(stream)
        duration = _stream_time(stream, duration=True, fallback=Fraction(count, 1) / frame_rate)
        summary["video"] = {
            "codec": str(stream.get("codec_name") or "").casefold(),
            "width": int(stream.get("width") or 0),
            "height": int(stream.get("height") or 0),
            "pixelFormat": str(stream.get("pix_fmt") or ""),
            "sampleAspectRatio": str(stream.get("sample_aspect_ratio") or ""),
            "rotationDegrees": _rotation(stream),
            "frameRate": _fraction_string(frame_rate),
            "nominalFrameRate": _fraction_string(nominal_rate),
            "frameCount": count,
            "startTime": _fraction_string(_stream_time(stream, duration=False, fallback=Fraction(0))),
            "duration": _fraction_string(duration),
        }
    if audios:
        stream = audios[0]
        summary["audio"] = {
            "codec": str(stream.get("codec_name") or "").casefold(),
            "sampleRate": int(stream.get("sample_rate") or 0),
            "channels": int(stream.get("channels") or 0),
            "channelLayout": str(stream.get("channel_layout") or ""),
            "startTime": _fraction_string(_stream_time(stream, duration=False, fallback=Fraction(0))),
            "duration": _fraction_string(_stream_time(stream, duration=True)),
            "timeBase": str(stream.get("time_base") or ""),
        }
    return summary


def source_media_blockers(summary: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if summary.get("videoStreamCount") != 1:
        blockers.append("source must contain exactly one video stream")
    if summary.get("audioStreamCount") != 1:
        blockers.append("source must contain exactly one audio stream")
    if summary.get("otherStreamCount") != 0:
        blockers.append("source must not contain subtitle, data, or attachment streams")
    if "mp4" not in summary.get("formatNames", []):
        blockers.append("source container must be MP4")
    video = summary.get("video")
    audio = summary.get("audio")
    if isinstance(video, Mapping):
        if video.get("codec") != "h264":
            blockers.append("source video codec must be H.264")
        if (video.get("width"), video.get("height")) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
            blockers.append(f"source dimensions must be {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
        if video.get("rotationDegrees") != 0:
            blockers.append("source must not rely on rotation metadata")
        if video.get("sampleAspectRatio") not in ("", "1:1"):
            blockers.append("source must use square pixels")
        if video.get("frameRate") != video.get("nominalFrameRate"):
            blockers.append("source must use a constant frame rate")
        try:
            if _fraction_from_string(video.get("duration"), "source video duration") <= 0:
                blockers.append("source video duration must be positive")
        except ValueError as exc:
            blockers.append(str(exc))
    if isinstance(audio, Mapping):
        if audio.get("codec") != "aac":
            blockers.append("source audio codec must be AAC")
        if int(audio.get("sampleRate") or 0) <= 0 or int(audio.get("channels") or 0) <= 0:
            blockers.append("source AAC stream has invalid channel or sample-rate metadata")
    return blockers


def audio_packet_fingerprint(path: Path, ffprobe_path: str, media_summary: Mapping[str, Any]) -> dict[str, Any]:
    audio = media_summary.get("audio")
    if not isinstance(audio, Mapping):
        raise ReadinessError("Cannot fingerprint audio: media has no audio summary")
    time_base = _fraction(audio.get("timeBase"), "audio time_base")
    payload = _run_json(
        (
            ffprobe_path,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_packets",
            "-show_data_hash",
            "sha256",
            "-show_entries",
            "packet=pts,dts,duration,size,data_hash",
            "-of",
            "json",
            str(path),
        )
    )
    packets = payload.get("packets")
    if not isinstance(packets, list) or not packets:
        raise ReadinessError("AAC stream contains no inspectable packets")

    first = packets[0]
    if not isinstance(first, Mapping) or first.get("pts") in (None, "N/A"):
        raise ReadinessError("AAC packets contain no usable PTS values")
    first_pts = int(first["pts"])
    first_dts = int(first.get("dts", first_pts))
    payload_records: list[list[Any]] = []
    timing_records: list[list[str]] = []
    for index, packet in enumerate(packets, start=1):
        if not isinstance(packet, Mapping):
            raise ReadinessError(f"AAC packet {index} is not an object")
        data_hash = packet.get("data_hash")
        if not data_hash:
            raise ReadinessError(f"AAC packet {index} has no data hash")
        try:
            pts = int(packet["pts"])
            dts = int(packet.get("dts", packet["pts"]))
            duration = int(packet["duration"])
            size = int(packet["size"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ReadinessError(f"AAC packet {index} has incomplete timing metadata") from exc
        payload_records.append([str(data_hash), size])
        timing_records.append(
            [
                _fraction_string((pts - first_pts) * time_base),
                _fraction_string((dts - first_dts) * time_base),
                _fraction_string(duration * time_base),
            ]
        )

    return {
        "codec": audio.get("codec"),
        "sampleRate": audio.get("sampleRate"),
        "channels": audio.get("channels"),
        "packetCount": len(packets),
        "packetPayloadSha256": _json_digest(payload_records),
        "relativeTimingSha256": _json_digest(timing_records),
        "firstPacketPts": _fraction_string(first_pts * time_base),
    }


def _beat_role(label: str) -> str:
    normalized = label.casefold()
    if "cta" in normalized or "call to action" in normalized:
        return "cta"
    if "rewrite" in normalized or "type" in normalized:
        return "rewrite"
    if "delete" in normalized or "remove" in normalized:
        return "delete"
    if "proof" in normalized or "evidence" in normalized:
        return "proof"
    if "receipt" in normalized:
        return "receipt"
    if "weak" in normalized:
        return "weak_line"
    if "open" in normalized or "hook" in normalized:
        return "opening"
    return "beat"


def normalize_beat_map(payload: Any, *, source_duration: Fraction) -> tuple[list[dict[str, Any]], list[str]]:
    if isinstance(payload, Mapping):
        raw_beats = payload.get("beats")
    else:
        raw_beats = payload
    if not isinstance(raw_beats, list) or not raw_beats:
        return [], ["beat map must contain a non-empty beats list"]

    blockers: list[str] = []
    events: list[dict[str, Any]] = []
    previous_audio = Fraction(-1)
    previous_visual = Fraction(-1)
    for index, raw in enumerate(raw_beats, start=1):
        if not isinstance(raw, Mapping):
            blockers.append(f"beat {index} is not an object")
            continue
        label = str(raw.get("label") or raw.get("name") or raw.get("id") or f"Beat {index}").strip()
        try:
            audio = _fraction(raw.get("audioSec"), f"beat {index} audioSec")
            visual = _fraction(raw.get("visualSec"), f"beat {index} visualSec")
        except ValueError as exc:
            blockers.append(str(exc))
            continue
        if audio < 0 or visual < 0:
            blockers.append(f"beat {index} timestamps must be non-negative")
        if audio > source_duration + TIMING_TOLERANCE_SEC or visual > source_duration + TIMING_TOLERANCE_SEC:
            blockers.append(f"beat {index} falls outside the source duration")
        if audio < previous_audio or visual < previous_visual:
            blockers.append(f"beat {index} timestamps are not monotonic")
        if abs(audio - visual) > MAX_BEAT_DELTA_SEC:
            blockers.append(f"beat {index} audio/visual delta exceeds 0.5 seconds")
        previous_audio = audio
        previous_visual = visual
        events.append(
            {
                "id": f"beat-{index:03d}",
                "role": _beat_role(label),
                "audioSec": round(float(audio), 3),
                "visualSec": round(float(visual), 3),
            }
        )
    return events, blockers


def assess_readiness(
    *,
    source: Path,
    beat_map: Path,
    afterfx_path: str | Path | None = None,
    aerender_path: str | Path | None = None,
    ffprobe_path: str | Path | None = None,
    ffmpeg_path: str | Path | None = None,
    tools: Mapping[str, Any] | None = None,
    probe_func: Callable[[Path, str], Mapping[str, Any]] | None = None,
    fingerprint_func: Callable[[Path, str, Mapping[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    source = _resolve(source)
    beat_map = _resolve(beat_map)
    tool_report = dict(
        tools
        if tools is not None
        else detect_tools(
            afterfx_path=afterfx_path,
            aerender_path=aerender_path,
            ffprobe_path=ffprobe_path,
            ffmpeg_path=ffmpeg_path,
        )
    )
    blockers = list(tool_report.get("blockers") or [])
    source_record: dict[str, Any] | None = None
    beat_record: dict[str, Any] | None = None
    media_summary: dict[str, Any] | None = None

    if not source.is_file():
        blockers.append(f"source short does not exist: {source}")
    elif source.suffix.casefold() != ".mp4":
        blockers.append("source short must be an MP4 file")
    elif tool_report.get("ffprobe", {}).get("found"):
        probe = probe_media if probe_func is None else probe_func
        fingerprint = audio_packet_fingerprint if fingerprint_func is None else fingerprint_func
        try:
            media_summary = summarize_probe(probe(source, tool_report["ffprobe"]["path"]))
            blockers.extend(source_media_blockers(media_summary))
            if not source_media_blockers(media_summary):
                audio_provenance = dict(fingerprint(source, tool_report["ffprobe"]["path"], media_summary))
                source_record = {
                    "path": str(source),
                    "sha256": sha256_file(source),
                    "media": media_summary,
                    "audioProvenance": audio_provenance,
                }
        except (BridgeError, OSError, ValueError, TypeError) as exc:
            blockers.append(f"source media validation failed: {exc}")

    if not beat_map.is_file():
        blockers.append(f"beat map does not exist: {beat_map}")
    elif media_summary and isinstance(media_summary.get("video"), Mapping):
        try:
            events, beat_blockers = normalize_beat_map(
                _read_json(beat_map),
                source_duration=_fraction_from_string(media_summary["video"]["duration"], "source duration"),
            )
            blockers.extend(beat_blockers)
            if not beat_blockers:
                beat_record = {
                    "path": str(beat_map),
                    "sha256": sha256_file(beat_map),
                    "maxAudioVisualDeltaSec": float(MAX_BEAT_DELTA_SEC),
                    "events": events,
                }
        except (BridgeError, OSError, ValueError, TypeError) as exc:
            blockers.append(f"beat map validation failed: {exc}")

    return {
        "ready": not blockers and source_record is not None and beat_record is not None,
        "readyForReviewedProjectHandoff": not blockers and source_record is not None and beat_record is not None,
        "readyForAutomatedProjectGeneration": False,
        "checkedAt": _utc_now(),
        "mode": "reviewed_project_handoff_only",
        "directProjectGeneration": {"enabled": False, "reason": DIRECT_GENERATION_REASON},
        "tools": tool_report,
        "source": source_record,
        "beatMap": beat_record,
        "blockers": blockers,
    }


def _allowed_effects(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    marker_events = [event["id"] for event in events if event.get("role") in {"proof", "delete", "rewrite", "receipt"}]
    cta_events = [event["id"] for event in events if event.get("role") == "cta"]
    return [
        {
            "id": "marker_sweep",
            "optional": True,
            "eligibleEventIds": marker_events,
            "maxOpacity": 0.16,
            "minDurationSec": 0.25,
            "maxDurationSec": 0.75,
            "maxPerEvent": 1,
            "usesBakedPixelsOnly": True,
        },
        {
            "id": "screen_paper_texture",
            "optional": True,
            "maxOpacity": 0.05,
            "animated": False,
            "usesBakedPixelsOnly": True,
        },
        {
            "id": "soft_shadow",
            "optional": True,
            "maxOpacity": 0.18,
            "minBlurPx": 24,
            "maxDistancePx": 10,
            "usesBakedPixelsOnly": True,
        },
        {
            "id": "cta_polish",
            "optional": True,
            "eligibleEventIds": cta_events,
            "maxOpacity": 0.18,
            "maxDurationSec": 1.2,
            "usesBakedPixelsOnly": True,
        },
    ]


def _finish_contract(source_media: Mapping[str, Any], events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    video = source_media["video"]
    return {
        "effectsAreOptional": True,
        "composition": {
            "width": EXPECTED_WIDTH,
            "height": EXPECTED_HEIGHT,
            "frameRate": video["frameRate"],
            "frameCount": video["frameCount"],
            "duration": video["duration"],
            "sourceTransform": {
                "positionPx": [EXPECTED_WIDTH // 2, EXPECTED_HEIGHT // 2],
                "scalePercent": 100,
                "rotationDegrees": 0,
                "keyframesAllowed": False,
                "timeRemapAllowed": False,
            },
        },
        "layers": {
            "singleBakedSourceLayerRequired": True,
            "newTextLayersAllowed": False,
            "camerasAllowed": False,
            "threeDLayersAllowed": False,
        },
        "audio": {
            "importIntoAdobe": False,
            "retimingAllowed": False,
            "finalStrategy": "copy_original_aac_packets",
        },
        "allowedEffects": _allowed_effects(events),
        "forbiddenOperations": [
            "resume_text_generation",
            "document_zoom_or_reframe",
            "narration_edit_or_retime",
            "new_cta_copy",
            "camera_motion",
            "publishing",
        ],
    }


def _manifest_digest(manifest: Mapping[str, Any]) -> str:
    unsigned = dict(manifest)
    unsigned.pop("manifestSha256", None)
    return _json_digest(unsigned)


def _path_blockers(
    *,
    source: Path,
    beat_map: Path,
    manifest_path: Path,
    adobe_video_path: Path,
    final_path: Path,
    project_review_path: Path,
    validation_receipt_path: Path,
) -> list[str]:
    named = {
        "source": source,
        "beat map": beat_map,
        "manifest": manifest_path,
        "Adobe video": adobe_video_path,
        "final output": final_path,
        "project review": project_review_path,
        "validation receipt": validation_receipt_path,
    }
    normalized: dict[str, str] = {}
    blockers: list[str] = []
    for label, path in named.items():
        key = os.path.normcase(str(path))
        if key in normalized:
            blockers.append(f"{label} path collides with {normalized[key]}: {path}")
        else:
            normalized[key] = label
    if final_path.suffix.casefold() != ".mp4":
        blockers.append("final output path must end in .mp4")
    for label, path in named.items():
        if label not in {"source", "beat map"} and path.exists():
            blockers.append(f"{label} already exists; the bridge will not overwrite it: {path}")
    return blockers


def prepare_manifest(
    *,
    source: Path,
    beat_map: Path,
    manifest_path: Path,
    adobe_video_path: Path,
    final_path: Path,
    project_review_path: Path | None = None,
    validation_receipt_path: Path | None = None,
    run_id: str | None = None,
    dry_run: bool = False,
    afterfx_path: str | Path | None = None,
    aerender_path: str | Path | None = None,
    ffprobe_path: str | Path | None = None,
    ffmpeg_path: str | Path | None = None,
    tools: Mapping[str, Any] | None = None,
    probe_func: Callable[[Path, str], Mapping[str, Any]] | None = None,
    fingerprint_func: Callable[[Path, str, Mapping[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    source = _resolve(source)
    beat_map = _resolve(beat_map)
    manifest_path = _resolve(manifest_path)
    adobe_video_path = _resolve(adobe_video_path)
    final_path = _resolve(final_path)
    project_review_path = _resolve(
        project_review_path or manifest_path.with_name(f"{manifest_path.stem}.project_review.json")
    )
    validation_receipt_path = _resolve(
        validation_receipt_path or final_path.with_name(f"{final_path.stem}.adobe_finish_receipt.json")
    )
    readiness = assess_readiness(
        source=source,
        beat_map=beat_map,
        afterfx_path=afterfx_path,
        aerender_path=aerender_path,
        ffprobe_path=ffprobe_path,
        ffmpeg_path=ffmpeg_path,
        tools=tools,
        probe_func=probe_func,
        fingerprint_func=fingerprint_func,
    )
    path_blockers = _path_blockers(
        source=source,
        beat_map=beat_map,
        manifest_path=manifest_path,
        adobe_video_path=adobe_video_path,
        final_path=final_path,
        project_review_path=project_review_path,
        validation_receipt_path=validation_receipt_path,
    )
    if path_blockers:
        readiness["blockers"] = [*readiness["blockers"], *path_blockers]
        readiness["ready"] = False
        readiness["readyForReviewedProjectHandoff"] = False
    if not readiness["ready"]:
        result = {"ready": False, "dryRun": dry_run, "written": False, "readiness": readiness}
        if dry_run:
            return result
        raise ReadinessError("Adobe finish is not ready: " + "; ".join(readiness["blockers"]))

    source_record = readiness["source"]
    beat_record = readiness["beatMap"]
    tool_report = readiness["tools"]
    manifest: dict[str, Any] = {
        "$schema": "marketing/adobe/after_effects/controlled_screen_finish_manifest.schema.json",
        "schemaVersion": MANIFEST_SCHEMA_VERSION,
        "manifestType": "controlled_screen_optional_finish",
        "state": "prepared_for_reviewed_project_handoff",
        "createdAt": _utc_now(),
        "runId": run_id or source.stem,
        "inputs": {"sourceShort": source_record, "beatMap": beat_record},
        "toolchain": {
            "afterEffectsPath": tool_report["afterEffects"]["path"],
            "aerenderPath": tool_report["aerender"]["path"],
            "ffprobePath": tool_report["ffprobe"]["path"],
            "ffmpegPath": tool_report["ffmpeg"]["path"],
            "directProjectGeneration": {
                "enabled": False,
                "mode": "manual_review_required",
                "reason": DIRECT_GENERATION_REASON,
            },
        },
        "finishContract": _finish_contract(source_record["media"], beat_record["events"]),
        "outputs": {
            "reviewedProject": {
                "reviewPath": str(project_review_path),
                "requiredBeforeRender": True,
            },
            "adobeVideoOnly": {
                "path": str(adobe_video_path),
                "requiredAudioStreamCount": 0,
                "status": "not_rendered",
            },
            "finalShort": {
                "path": str(final_path),
                "container": "mp4",
                "videoCodec": "h264",
                "audioCodec": "aac",
                "status": "not_finalized",
            },
            "validationReceipt": {"path": str(validation_receipt_path)},
        },
        "validationPolicy": {
            "dimensionsExact": [EXPECTED_WIDTH, EXPECTED_HEIGHT],
            "frameRateMustMatchSource": True,
            "frameCountMustMatchSource": True,
            "maxTimestampDifferenceSec": float(TIMING_TOLERANCE_SEC),
            "audioPacketPayloadMustMatchSource": True,
            "audioPacketTimingMustMatchSource": True,
        },
        "publishing": {"allowed": False, "performedByBridge": False, "destination": None},
    }
    manifest["manifestSha256"] = _manifest_digest(manifest)
    if not dry_run:
        _atomic_write_json(manifest_path, manifest)
    return {
        "ready": True,
        "dryRun": dry_run,
        "written": not dry_run,
        "manifestPath": str(manifest_path),
        "manifest": manifest,
        "readiness": readiness,
    }


def manifest_blockers(manifest: Any) -> list[str]:
    if not isinstance(manifest, Mapping):
        return ["manifest root must be an object"]
    blockers: list[str] = []
    if manifest.get("schemaVersion") != MANIFEST_SCHEMA_VERSION:
        blockers.append("unsupported manifest schemaVersion")
    if manifest.get("manifestType") != "controlled_screen_optional_finish":
        blockers.append("manifestType is not controlled_screen_optional_finish")
    expected_digest = _manifest_digest(manifest)
    if manifest.get("manifestSha256") != expected_digest:
        blockers.append("manifestSha256 does not match the manifest contents")

    toolchain = manifest.get("toolchain")
    direct = toolchain.get("directProjectGeneration") if isinstance(toolchain, Mapping) else None
    if not isinstance(direct, Mapping) or direct.get("enabled") is not False or direct.get("mode") != "manual_review_required":
        blockers.append("direct project generation must remain disabled")

    inputs = manifest.get("inputs")
    source = inputs.get("sourceShort") if isinstance(inputs, Mapping) else None
    beat_map = inputs.get("beatMap") if isinstance(inputs, Mapping) else None
    contract = manifest.get("finishContract")
    if not isinstance(source, Mapping) or not isinstance(beat_map, Mapping) or not isinstance(contract, Mapping):
        blockers.append("manifest is missing input or finish-contract objects")
    else:
        events = beat_map.get("events")
        media = source.get("media")
        if not isinstance(events, list) or not isinstance(media, Mapping):
            blockers.append("manifest inputs are incomplete")
        else:
            try:
                expected_contract = _finish_contract(media, events)
            except (KeyError, TypeError, ValueError):
                blockers.append("manifest source media is incomplete")
            else:
                if contract != expected_contract:
                    blockers.append("finishContract differs from the locked production contract")
            effect_ids = [item.get("id") for item in contract.get("allowedEffects", []) if isinstance(item, Mapping)]
            if tuple(effect_ids) != ALLOWED_EFFECT_IDS:
                blockers.append("finishContract effect allowlist is invalid")

    outputs = manifest.get("outputs")
    if not isinstance(outputs, Mapping):
        blockers.append("manifest outputs are missing")
    else:
        try:
            if outputs["adobeVideoOnly"]["requiredAudioStreamCount"] != 0:
                blockers.append("Adobe output must be video-only")
            if outputs["finalShort"]["videoCodec"] != "h264" or outputs["finalShort"]["audioCodec"] != "aac":
                blockers.append("final output codecs must remain H.264/AAC")
        except (KeyError, TypeError):
            blockers.append("manifest outputs are incomplete")

    publishing = manifest.get("publishing")
    if publishing != {"allowed": False, "performedByBridge": False, "destination": None}:
        blockers.append("publishing must remain disabled")
    return blockers


def load_manifest(path: Path) -> dict[str, Any]:
    payload = _read_json(_resolve(path))
    blockers = manifest_blockers(payload)
    if blockers:
        raise ContractError("Invalid Adobe finish manifest: " + "; ".join(blockers))
    return dict(payload)


def create_project_review(
    *,
    manifest_path: Path,
    project_path: Path,
    reviewed_by: str,
    confirm_contract: bool,
) -> dict[str, Any]:
    manifest_path = _resolve(manifest_path)
    manifest = load_manifest(manifest_path)
    project_path = _resolve(project_path)
    if not confirm_contract:
        raise ContractError("Project review requires an explicit --confirm-contract acknowledgement")
    if not reviewed_by.strip():
        raise ContractError("Project review requires a non-empty reviewer name")
    if not project_path.is_file() or project_path.suffix.casefold() != ".aep":
        raise ContractError(f"Reviewed project is not an existing .aep file: {project_path}")
    review_path = _resolve(manifest["outputs"]["reviewedProject"]["reviewPath"])
    if review_path.exists():
        raise ContractError(f"Project review already exists; refusing to overwrite: {review_path}")

    review: dict[str, Any] = {
        "schemaVersion": PROJECT_REVIEW_SCHEMA_VERSION,
        "manifestPath": str(manifest_path),
        "manifestSha256": manifest["manifestSha256"],
        "projectPath": str(project_path),
        "projectSha256": sha256_file(project_path),
        "compositionName": REVIEW_COMP_NAME,
        "reviewedBy": reviewed_by.strip(),
        "reviewedAt": _utc_now(),
        "checks": {key: True for key in REQUIRED_PROJECT_CHECKS},
        "note": "This is an explicit human review record; the bridge does not inspect AEP internals.",
    }
    review["reviewSha256"] = _json_digest({key: value for key, value in review.items() if key != "reviewSha256"})
    _atomic_write_json(review_path, review)
    return review


def validate_project_review(manifest: Mapping[str, Any]) -> dict[str, Any]:
    review_path = _resolve(manifest["outputs"]["reviewedProject"]["reviewPath"])
    if not review_path.is_file():
        raise ContractError(f"Reviewed-project record is missing: {review_path}")
    review = _read_json(review_path)
    if not isinstance(review, Mapping):
        raise ContractError("Reviewed-project record must be a JSON object")
    blockers: list[str] = []
    if review.get("schemaVersion") != PROJECT_REVIEW_SCHEMA_VERSION:
        blockers.append("project review schemaVersion is invalid")
    unsigned = {key: value for key, value in review.items() if key != "reviewSha256"}
    if review.get("reviewSha256") != _json_digest(unsigned):
        blockers.append("project review hash does not match its contents")
    if review.get("manifestSha256") != manifest.get("manifestSha256"):
        blockers.append("project review is bound to a different manifest")
    if review.get("compositionName") != REVIEW_COMP_NAME:
        blockers.append(f"reviewed composition must be named {REVIEW_COMP_NAME!r}")
    checks = review.get("checks")
    for key in REQUIRED_PROJECT_CHECKS:
        if not isinstance(checks, Mapping) or checks.get(key) is not True:
            blockers.append(f"project review check is not affirmed: {key}")
    project_path = _resolve(str(review.get("projectPath") or ""))
    if not project_path.is_file() or project_path.suffix.casefold() != ".aep":
        blockers.append(f"reviewed AEP is missing: {project_path}")
    elif review.get("projectSha256") != sha256_file(project_path):
        blockers.append("reviewed AEP hash has changed")
    if blockers:
        raise ContractError("Invalid reviewed-project record: " + "; ".join(blockers))
    return dict(review)


def _same_path(first: str, second: str) -> bool:
    return os.path.normcase(str(_resolve(first))) == os.path.normcase(str(_resolve(second)))


def verify_manifest_environment(
    manifest: Mapping[str, Any],
    *,
    afterfx_path: str | Path | None = None,
    aerender_path: str | Path | None = None,
    ffprobe_path: str | Path | None = None,
    ffmpeg_path: str | Path | None = None,
    probe_func: Callable[[Path, str], Mapping[str, Any]] | None = None,
    fingerprint_func: Callable[[Path, str, Mapping[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    inputs = manifest["inputs"]
    source = _resolve(inputs["sourceShort"]["path"])
    beat_map = _resolve(inputs["beatMap"]["path"])
    tools = detect_tools(
        afterfx_path=afterfx_path or manifest["toolchain"]["afterEffectsPath"],
        aerender_path=aerender_path or manifest["toolchain"]["aerenderPath"],
        ffprobe_path=ffprobe_path or manifest["toolchain"]["ffprobePath"],
        ffmpeg_path=ffmpeg_path or manifest["toolchain"]["ffmpegPath"],
    )
    readiness = assess_readiness(
        source=source,
        beat_map=beat_map,
        tools=tools,
        probe_func=probe_func,
        fingerprint_func=fingerprint_func,
    )
    blockers = list(readiness["blockers"])
    if readiness.get("source") != inputs["sourceShort"]:
        blockers.append("source short hash, media timing, or AAC provenance changed after manifest creation")
    if readiness.get("beatMap") != inputs["beatMap"]:
        blockers.append("beat map changed after manifest creation")
    for key, manifest_key in (
        ("afterEffects", "afterEffectsPath"),
        ("aerender", "aerenderPath"),
        ("ffprobe", "ffprobePath"),
        ("ffmpeg", "ffmpegPath"),
    ):
        current = tools.get(key, {}).get("path")
        recorded = manifest["toolchain"].get(manifest_key)
        if current and recorded and not _same_path(current, recorded):
            blockers.append(f"{key} path differs from the manifest")
    if blockers:
        raise ReadinessError("Manifest environment is not ready: " + "; ".join(dict.fromkeys(blockers)))
    return readiness


def _timing_blockers(reference: Mapping[str, Any], candidate: Mapping[str, Any], label: str) -> list[str]:
    blockers: list[str] = []
    if candidate.get("frameRate") != reference.get("frameRate"):
        blockers.append(f"{label} frame rate differs from source")
    if candidate.get("nominalFrameRate") != reference.get("nominalFrameRate"):
        blockers.append(f"{label} nominal frame rate differs from source")
    if candidate.get("frameRate") != candidate.get("nominalFrameRate"):
        blockers.append(f"{label} must use a constant frame rate")
    if candidate.get("frameCount") != reference.get("frameCount"):
        blockers.append(f"{label} frame count differs from source")
    for key, friendly in (("startTime", "start timestamp"), ("duration", "duration")):
        try:
            difference = abs(
                _fraction_from_string(candidate.get(key), f"{label} {key}")
                - _fraction_from_string(reference.get(key), f"source {key}")
            )
        except ValueError as exc:
            blockers.append(str(exc))
            continue
        if difference > TIMING_TOLERANCE_SEC:
            blockers.append(f"{label} {friendly} differs from source by more than 0.001 seconds")
    return blockers


def adobe_intermediate_blockers(manifest: Mapping[str, Any], probe_payload: Mapping[str, Any]) -> list[str]:
    try:
        summary = summarize_probe(probe_payload)
    except (TypeError, ValueError) as exc:
        return [f"Adobe video probe is invalid: {exc}"]
    blockers: list[str] = []
    if summary.get("videoStreamCount") != 1:
        blockers.append("Adobe intermediate must contain exactly one video stream")
    if summary.get("audioStreamCount") != 0:
        blockers.append("Adobe intermediate must be video-only; narration may not pass through Adobe")
    if summary.get("otherStreamCount") != 0:
        blockers.append("Adobe intermediate must not contain subtitle, data, or attachment streams")
    video = summary.get("video")
    reference = manifest["inputs"]["sourceShort"]["media"]["video"]
    if isinstance(video, Mapping):
        if (video.get("width"), video.get("height")) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
            blockers.append(f"Adobe intermediate dimensions must be {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
        if video.get("rotationDegrees") != 0:
            blockers.append("Adobe intermediate must not use rotation metadata")
        if video.get("sampleAspectRatio") not in ("", "1:1"):
            blockers.append("Adobe intermediate must use square pixels")
        blockers.extend(_timing_blockers(reference, video, "Adobe intermediate"))
    return blockers


def final_output_blockers(
    manifest: Mapping[str, Any],
    probe_payload: Mapping[str, Any],
    audio_provenance: Mapping[str, Any],
) -> list[str]:
    try:
        summary = summarize_probe(probe_payload)
    except (TypeError, ValueError) as exc:
        return [f"final output probe is invalid: {exc}"]
    blockers: list[str] = []
    if summary.get("videoStreamCount") != 1 or summary.get("audioStreamCount") != 1:
        blockers.append("final output must contain exactly one video and one audio stream")
    if summary.get("otherStreamCount") != 0:
        blockers.append("final output must not contain subtitle, data, or attachment streams")
    if "mp4" not in summary.get("formatNames", []):
        blockers.append("final output container must be MP4")
    video = summary.get("video")
    audio = summary.get("audio")
    reference_video = manifest["inputs"]["sourceShort"]["media"]["video"]
    reference_audio = manifest["inputs"]["sourceShort"]["media"]["audio"]
    reference_provenance = manifest["inputs"]["sourceShort"]["audioProvenance"]
    if isinstance(video, Mapping):
        if video.get("codec") != "h264":
            blockers.append("final video codec must be H.264")
        if (video.get("width"), video.get("height")) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
            blockers.append(f"final dimensions must be {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
        if video.get("rotationDegrees") != 0:
            blockers.append("final output must not use rotation metadata")
        if video.get("sampleAspectRatio") not in ("", "1:1"):
            blockers.append("final output must use square pixels")
        blockers.extend(_timing_blockers(reference_video, video, "final output"))
    if isinstance(audio, Mapping):
        if audio.get("codec") != "aac":
            blockers.append("final audio codec must be AAC")
        for key in ("sampleRate", "channels"):
            if audio.get(key) != reference_audio.get(key):
                blockers.append(f"final audio {key} differs from source")

    for key in ("codec", "sampleRate", "channels", "packetCount", "packetPayloadSha256", "relativeTimingSha256"):
        if audio_provenance.get(key) != reference_provenance.get(key):
            blockers.append(f"final AAC provenance differs from source: {key}")
    if isinstance(video, Mapping):
        try:
            source_offset = (
                _fraction_from_string(reference_provenance.get("firstPacketPts"), "source first audio PTS")
                - _fraction_from_string(reference_video.get("startTime"), "source video start")
            )
            output_offset = (
                _fraction_from_string(audio_provenance.get("firstPacketPts"), "output first audio PTS")
                - _fraction_from_string(video.get("startTime"), "output video start")
            )
            if abs(output_offset - source_offset) > TIMING_TOLERANCE_SEC:
                blockers.append("final narration offset differs from source by more than 0.001 seconds")
        except ValueError as exc:
            blockers.append(str(exc))
    return blockers


def _probe_intermediate(manifest: Mapping[str, Any], ffprobe_path: str) -> tuple[Path, dict[str, Any]]:
    path = _resolve(manifest["outputs"]["adobeVideoOnly"]["path"])
    if not path.is_file():
        raise OutputValidationError(f"Adobe video-only output is missing: {path}")
    payload = probe_media(path, ffprobe_path)
    blockers = adobe_intermediate_blockers(manifest, payload)
    if blockers:
        raise OutputValidationError("Adobe intermediate rejected: " + "; ".join(blockers))
    return path, payload


def build_aerender_command(manifest: Mapping[str, Any], review: Mapping[str, Any]) -> list[str]:
    return [
        str(manifest["toolchain"]["aerenderPath"]),
        "-project",
        str(review["projectPath"]),
        "-comp",
        REVIEW_COMP_NAME,
        "-output",
        str(manifest["outputs"]["adobeVideoOnly"]["path"]),
    ]


def render_reviewed_project(
    *,
    manifest_path: Path,
    dry_run: bool = False,
    timeout_sec: int = 900,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    readiness = verify_manifest_environment(manifest)
    review = validate_project_review(manifest)
    output = _resolve(manifest["outputs"]["adobeVideoOnly"]["path"])
    if output.exists():
        raise OutputValidationError(f"Adobe output already exists; refusing to overwrite: {output}")
    command = build_aerender_command(manifest, review)
    if dry_run:
        return {"ready": True, "dryRun": True, "rendered": False, "command": command, "readiness": readiness}
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(command, check=False, timeout=timeout_sec)
    except (OSError, subprocess.TimeoutExpired) as exc:
        output.unlink(missing_ok=True)
        raise OutputValidationError(f"aerender did not complete safely: {exc}") from exc
    if completed.returncode != 0:
        output.unlink(missing_ok=True)
        raise OutputValidationError(f"aerender failed with exit code {completed.returncode}")
    try:
        _probe_intermediate(manifest, manifest["toolchain"]["ffprobePath"])
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return {"ready": True, "dryRun": False, "rendered": True, "output": str(output)}


def build_finalize_command(manifest: Mapping[str, Any], *, temporary_output: Path) -> list[str]:
    return [
        str(manifest["toolchain"]["ffmpegPath"]),
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-copyts",
        "-i",
        str(manifest["outputs"]["adobeVideoOnly"]["path"]),
        "-i",
        str(manifest["inputs"]["sourceShort"]["path"]),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-map_metadata",
        "1",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "17",
        "-pix_fmt",
        "yuv420p",
        "-fps_mode",
        "passthrough",
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        "-avoid_negative_ts",
        "disabled",
        str(temporary_output),
    ]


def _validate_final_path(manifest: Mapping[str, Any], path: Path) -> dict[str, Any]:
    ffprobe_path = manifest["toolchain"]["ffprobePath"]
    probe_payload = probe_media(path, ffprobe_path)
    summary = summarize_probe(probe_payload)
    provenance = audio_packet_fingerprint(path, ffprobe_path, summary)
    blockers = final_output_blockers(manifest, probe_payload, provenance)
    if blockers:
        raise OutputValidationError("Final output rejected: " + "; ".join(blockers))
    return {"media": summary, "audioProvenance": provenance}


def finalize_output(*, manifest_path: Path, timeout_sec: int = 900) -> dict[str, Any]:
    manifest_path = _resolve(manifest_path)
    manifest = load_manifest(manifest_path)
    verify_manifest_environment(manifest)
    review = validate_project_review(manifest)
    intermediate, _ = _probe_intermediate(manifest, manifest["toolchain"]["ffprobePath"])
    final_path = _resolve(manifest["outputs"]["finalShort"]["path"])
    receipt_path = _resolve(manifest["outputs"]["validationReceipt"]["path"])
    if final_path.exists():
        raise OutputValidationError(f"Final output already exists; refusing to overwrite: {final_path}")
    if receipt_path.exists():
        raise OutputValidationError(f"Validation receipt already exists; refusing to overwrite: {receipt_path}")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = final_path.with_name(f".{final_path.stem}.partial-{os.getpid()}{final_path.suffix}")
    temporary.unlink(missing_ok=True)
    command = build_finalize_command(manifest, temporary_output=temporary)
    moved = False
    try:
        try:
            completed = subprocess.run(command, check=False, timeout=timeout_sec)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise OutputValidationError(f"ffmpeg finalization did not complete safely: {exc}") from exc
        if completed.returncode != 0:
            raise OutputValidationError(f"ffmpeg finalization failed with exit code {completed.returncode}")
        validation = _validate_final_path(manifest, temporary)
        output_hash = sha256_file(temporary)
        os.replace(temporary, final_path)
        moved = True
        receipt: dict[str, Any] = {
            "schemaVersion": VALIDATION_RECEIPT_SCHEMA_VERSION,
            "status": "media_validated_not_published",
            "validatedAt": _utc_now(),
            "manifestPath": str(manifest_path),
            "manifestSha256": manifest["manifestSha256"],
            "projectPath": review["projectPath"],
            "projectSha256": review["projectSha256"],
            "adobeVideoPath": str(intermediate),
            "adobeVideoSha256": sha256_file(intermediate),
            "finalPath": str(final_path),
            "finalSha256": output_hash,
            "validation": validation,
            "audioStrategy": "copied_source_aac_packets",
            "published": False,
        }
        receipt["receiptSha256"] = _json_digest(receipt)
        _atomic_write_json(receipt_path, receipt)
    except Exception:
        temporary.unlink(missing_ok=True)
        if moved:
            final_path.unlink(missing_ok=True)
        raise
    return {"finalPath": str(final_path), "receiptPath": str(receipt_path), "published": False}


def validate_existing_output(*, manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    verify_manifest_environment(manifest)
    validate_project_review(manifest)
    _probe_intermediate(manifest, manifest["toolchain"]["ffprobePath"])
    final_path = _resolve(manifest["outputs"]["finalShort"]["path"])
    if not final_path.is_file():
        raise OutputValidationError(f"Final output is missing: {final_path}")
    validation = _validate_final_path(manifest, final_path)
    return {"valid": True, "finalPath": str(final_path), "validation": validation, "published": False}


def _add_tool_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--afterfx", type=Path)
    parser.add_argument("--aerender", type=Path)
    parser.add_argument("--ffprobe", type=Path)
    parser.add_argument("--ffmpeg", type=Path)


def _print_json(payload: Any, *, stream: Any = sys.stdout) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True), file=stream)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    readiness = commands.add_parser("readiness", help="Check source, beat map, and local tool readiness.")
    readiness.add_argument("--source", required=True, type=Path)
    readiness.add_argument("--beat-map", required=True, type=Path)
    _add_tool_arguments(readiness)

    prepare = commands.add_parser("prepare", help="Create a reviewed-project handoff manifest.")
    prepare.add_argument("--source", required=True, type=Path)
    prepare.add_argument("--beat-map", required=True, type=Path)
    prepare.add_argument("--manifest", required=True, type=Path)
    prepare.add_argument("--adobe-video-out", required=True, type=Path)
    prepare.add_argument("--final-out", required=True, type=Path)
    prepare.add_argument("--project-review", type=Path)
    prepare.add_argument("--validation-receipt", type=Path)
    prepare.add_argument("--run-id")
    prepare.add_argument("--dry-run", action="store_true")
    _add_tool_arguments(prepare)

    review = commands.add_parser("review-project", help="Record explicit review of a manually built AEP.")
    review.add_argument("--manifest", required=True, type=Path)
    review.add_argument("--project", required=True, type=Path)
    review.add_argument("--reviewed-by", required=True)
    review.add_argument("--confirm-contract", action="store_true")

    render = commands.add_parser("render", help="Run aerender only on the reviewed, hash-bound AEP.")
    render.add_argument("--manifest", required=True, type=Path)
    render.add_argument("--dry-run", action="store_true")
    render.add_argument("--timeout-sec", type=int, default=900)

    finalize = commands.add_parser("finalize", help="Copy source AAC into the validated Adobe video output.")
    finalize.add_argument("--manifest", required=True, type=Path)
    finalize.add_argument("--timeout-sec", type=int, default=900)

    validate = commands.add_parser("validate", help="Revalidate an existing final output without publishing it.")
    validate.add_argument("--manifest", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "readiness":
            result = assess_readiness(
                source=args.source,
                beat_map=args.beat_map,
                afterfx_path=args.afterfx,
                aerender_path=args.aerender,
                ffprobe_path=args.ffprobe,
                ffmpeg_path=args.ffmpeg,
            )
            _print_json(result)
            return 0 if result["ready"] else 2
        if args.command == "prepare":
            result = prepare_manifest(
                source=args.source,
                beat_map=args.beat_map,
                manifest_path=args.manifest,
                adobe_video_path=args.adobe_video_out,
                final_path=args.final_out,
                project_review_path=args.project_review,
                validation_receipt_path=args.validation_receipt,
                run_id=args.run_id,
                dry_run=args.dry_run,
                afterfx_path=args.afterfx,
                aerender_path=args.aerender,
                ffprobe_path=args.ffprobe,
                ffmpeg_path=args.ffmpeg,
            )
            _print_json(result)
            return 0 if result["ready"] else 2
        if args.command == "review-project":
            _print_json(
                create_project_review(
                    manifest_path=args.manifest,
                    project_path=args.project,
                    reviewed_by=args.reviewed_by,
                    confirm_contract=args.confirm_contract,
                )
            )
            return 0
        if args.command == "render":
            _print_json(
                render_reviewed_project(
                    manifest_path=args.manifest,
                    dry_run=args.dry_run,
                    timeout_sec=args.timeout_sec,
                )
            )
            return 0
        if args.command == "finalize":
            _print_json(finalize_output(manifest_path=args.manifest, timeout_sec=args.timeout_sec))
            return 0
        if args.command == "validate":
            _print_json(validate_existing_output(manifest_path=args.manifest))
            return 0
    except BridgeError as exc:
        _print_json({"ok": False, "error": str(exc), "published": False}, stream=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
