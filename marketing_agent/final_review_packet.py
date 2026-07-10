#!/usr/bin/env python3
"""Build a deterministic final-video review packet without publishing anything.

The optional beat-map JSON accepts either a top-level list or an object containing
``beats``/``timeline``. A beat may contain ``audioSec`` and ``visualSec`` (aliases
are accepted), plus an optional ``cropBox``. Top-level ``cropBoxes`` are also
accepted. Crop boxes use ``x/y/width/height`` or ``left/top/right/bottom`` and may
be pixel or normalized coordinates.

The optional evidence ledger is deliberately strict. Supported comparisons are:

* ``facts``/``claims`` entries with a canonical ``value`` and two or more
  ``occurrences`` (proof, rewrite, receipt, spoken, visible, etc.); or
* ``comparisons`` entries with ``expected`` and ``actual``/``values``; or
* a score receipt with before/after totals and rows whose sums reproduce them.

This module has no queue, upload, posting, or run-state dependencies. A passing
deterministic packet still sets ``humanWatchRequired`` to true. Codex approval is
the only final creative approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont


GATE_VERSION = "1.0.0"
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30.0
MIN_DURATION_SEC = 18.0
MAX_DURATION_SEC = 28.0
MAX_BEAT_DELTA_SEC = 0.5
LITERAL_FRAME_TIMES = (0.0, 0.25, 0.5, 1.0)


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_executable(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"{name} was not found on PATH")
    return found


def run_command(command: Sequence[str], *, check: bool = True) -> CommandResult:
    proc = subprocess.run(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if check and proc.returncode:
        message = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
        raise RuntimeError(message[-2000:])
    return CommandResult(proc.stdout, proc.stderr)


def ffprobe_json(path: Path) -> dict[str, Any]:
    result = run_command(
        [
            find_executable("ffprobe"),
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(result.stdout)


def parse_frame_rate(stream: Mapping[str, Any]) -> float:
    raw = str(stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0/1")
    try:
        if "/" in raw:
            numerator, denominator = raw.split("/", 1)
            return float(numerator) / float(denominator or 1)
        return float(raw)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def validate_media(probe: Mapping[str, Any]) -> dict[str, Any]:
    streams = list(probe.get("streams") or [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    duration = _safe_float((probe.get("format") or {}).get("duration")) or 0.0
    blockers: list[str] = []

    if not video:
        blockers.append("missing video stream")
    if not audio:
        blockers.append("missing audio stream")

    fps = parse_frame_rate(video or {})
    if video:
        if str(video.get("codec_name") or "").lower() != "h264":
            blockers.append(f"video codec is {video.get('codec_name')}, expected h264")
        if int(video.get("width") or 0) != TARGET_WIDTH or int(video.get("height") or 0) != TARGET_HEIGHT:
            blockers.append(
                f"video is {video.get('width')}x{video.get('height')}, expected {TARGET_WIDTH}x{TARGET_HEIGHT}"
            )
        if abs(fps - TARGET_FPS) > 0.01:
            blockers.append(f"video is {fps:.3f}fps, expected 30fps")
    if audio and str(audio.get("codec_name") or "").lower() != "aac":
        blockers.append(f"audio codec is {audio.get('codec_name')}, expected aac")
    if not MIN_DURATION_SEC <= duration <= MAX_DURATION_SEC:
        blockers.append(
            f"duration is {duration:.3f}s, expected {MIN_DURATION_SEC:.0f}-{MAX_DURATION_SEC:.0f}s"
        )

    return {
        "passed": not blockers,
        "blockers": blockers,
        "durationSec": round(duration, 3),
        "videoCodec": video.get("codec_name") if video else None,
        "audioCodec": audio.get("codec_name") if audio else None,
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "fps": round(fps, 3),
        "audioSampleRate": int(audio.get("sample_rate") or 0) if audio else None,
    }


def extract_audio(video: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    run_command(
        [
            find_executable("ffmpeg"),
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-map",
            "0:a:0",
            "-vn",
            "-c:a",
            "pcm_s16le",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(output),
        ]
    )
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("decoded final audio was not created")


def _audio_filter(video: Path, filter_value: str) -> CommandResult:
    return run_command(
        [
            find_executable("ffmpeg"),
            "-hide_banner",
            "-nostats",
            "-i",
            str(video),
            "-map",
            "0:a:0",
            "-af",
            filter_value,
            "-f",
            "null",
            os.devnull,
        ]
    )


def _parse_loudnorm(stderr: str) -> dict[str, Any]:
    candidates = re.findall(r"\{\s*\"input_i\".*?\}", stderr, flags=re.DOTALL)
    if not candidates:
        return {"available": False}
    try:
        payload = json.loads(candidates[-1])
    except json.JSONDecodeError:
        return {"available": False}
    return {
        "available": True,
        "integratedLufs": _safe_float(payload.get("input_i")),
        "truePeakDbtp": _safe_float(payload.get("input_tp")),
        "loudnessRangeLu": _safe_float(payload.get("input_lra")),
        "thresholdLufs": _safe_float(payload.get("input_thresh")),
    }


def _parse_silence(stderr: str, duration_sec: float) -> dict[str, Any]:
    starts = [_safe_float(value) for value in re.findall(r"silence_start:\s*(-?[0-9.]+)", stderr)]
    ends = [
        (_safe_float(end), _safe_float(length))
        for end, length in re.findall(r"silence_end:\s*(-?[0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)", stderr)
    ]
    segments: list[dict[str, float]] = []
    for index, start in enumerate(starts):
        if start is None:
            continue
        if index < len(ends) and ends[index][0] is not None:
            end = float(ends[index][0])
            length = float(ends[index][1] if ends[index][1] is not None else max(0.0, end - start))
        else:
            end = duration_sec
            length = max(0.0, end - start)
        segments.append(
            {"startSec": round(max(0.0, start), 3), "endSec": round(max(0.0, end), 3), "durationSec": round(length, 3)}
        )
    return {
        "checked": True,
        "noiseThresholdDb": -45,
        "minimumDurationSec": 0.35,
        "segments": segments,
        "segmentCount": len(segments),
        "totalSilenceSec": round(sum(item["durationSec"] for item in segments), 3),
        "longestSilenceSec": round(max((item["durationSec"] for item in segments), default=0.0), 3),
    }


def _parse_volume(stderr: str) -> dict[str, Any]:
    max_match = re.search(r"max_volume:\s*(-?inf|-?[0-9.]+)\s*dB", stderr, flags=re.IGNORECASE)
    mean_match = re.search(r"mean_volume:\s*(-?inf|-?[0-9.]+)\s*dB", stderr, flags=re.IGNORECASE)

    def parse_db(match: re.Match[str] | None) -> float | None:
        if not match or match.group(1).lower() == "-inf":
            return None
        return _safe_float(match.group(1))

    max_db = parse_db(max_match)
    return {
        "checked": max_match is not None,
        "maxVolumeDb": max_db,
        "meanVolumeDb": parse_db(mean_match),
        "clippingThresholdDb": -0.05,
        "clippingRisk": bool(max_db is not None and max_db >= -0.05),
        "headroomDb": round(-max_db, 3) if max_db is not None else None,
    }


def analyze_audio(video: Path, decoded_audio: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    try:
        audio_probe = ffprobe_json(decoded_audio)
        duration = _safe_float((audio_probe.get("format") or {}).get("duration")) or 0.0
    except Exception as exc:
        duration = 0.0
        blockers.append(f"could not probe decoded final audio: {exc}")

    try:
        loudness = _parse_loudnorm(
            _audio_filter(video, "loudnorm=I=-16:LRA=7:TP=-1.5:print_format=json").stderr
        )
        if not loudness.get("available"):
            warnings.append("integrated loudness was unavailable")
    except Exception as exc:
        loudness = {"available": False, "error": str(exc)}
        warnings.append(f"integrated loudness was unavailable: {exc}")

    try:
        silence = _parse_silence(_audio_filter(video, "silencedetect=noise=-45dB:d=0.35").stderr, duration)
    except Exception as exc:
        silence = {"checked": False, "error": str(exc)}
        blockers.append(f"silence analysis failed: {exc}")

    try:
        peak = _parse_volume(_audio_filter(video, "volumedetect").stderr)
        if not peak.get("checked"):
            blockers.append("clipping/peak analysis did not produce a max-volume result")
    except Exception as exc:
        peak = {"checked": False, "error": str(exc)}
        blockers.append(f"clipping/peak analysis failed: {exc}")

    return (
        {
            "decodedAudioPath": str(decoded_audio),
            "durationSec": round(duration, 3),
            "loudness": loudness,
            "silence": silence,
            "peak": peak,
        },
        blockers,
        warnings,
    )


def _pick_number(record: Mapping[str, Any], keys: Iterable[str]) -> float | None:
    for key in keys:
        value = _safe_float(record.get(key))
        if value is not None:
            return value
    return None


def _nested_number(record: Mapping[str, Any], key: str) -> float | None:
    nested = record.get(key)
    if isinstance(nested, Mapping):
        return _pick_number(nested, ("timeSec", "startSec", "atSec", "timestampSec", "sec"))
    return None


def normalize_beat_map(payload: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    top_level_crops: list[dict[str, Any]] = []
    if isinstance(payload, list):
        raw_beats = payload
    elif isinstance(payload, Mapping):
        raw_beats = payload.get("beats") or payload.get("timeline") or payload.get("beatMap") or []
        raw_crops = payload.get("cropBoxes") or payload.get("crops") or []
        if isinstance(raw_crops, list):
            top_level_crops = [dict(item) for item in raw_crops if isinstance(item, Mapping)]
    else:
        return [], [], ["beat map must be a JSON object or list"]

    if not isinstance(raw_beats, list) or not raw_beats:
        return [], top_level_crops, ["beat map contains no beats"]

    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_beats, start=1):
        if not isinstance(raw, Mapping):
            blockers.append(f"beat {index} is not an object")
            continue
        label = str(raw.get("label") or raw.get("name") or raw.get("id") or raw.get("beat") or f"Beat {index}").strip()
        audio_sec = _pick_number(
            raw,
            (
                "audioSec",
                "audioTimeSec",
                "voiceSec",
                "voiceCueSec",
                "narrationSec",
                "audioStartSec",
            ),
        )
        if audio_sec is None:
            audio_sec = _nested_number(raw, "audio") or _nested_number(raw, "voice")
        visual_sec = _pick_number(
            raw,
            (
                "visualSec",
                "visualTimeSec",
                "videoSec",
                "actualSec",
                "visualStartSec",
            ),
        )
        if visual_sec is None:
            visual_sec = _nested_number(raw, "visual") or _nested_number(raw, "video")
        generic_sec = _pick_number(raw, ("timeSec", "timestampSec", "atSec", "startSec"))
        contact_sec = visual_sec if visual_sec is not None else generic_sec if generic_sec is not None else audio_sec
        explicit_delta = _safe_float(raw.get("deltaSec"))
        delta = abs(visual_sec - audio_sec) if visual_sec is not None and audio_sec is not None else abs(explicit_delta) if explicit_delta is not None else None
        if contact_sec is None:
            blockers.append(f"beat '{label}' has no usable timestamp")
        if delta is not None and delta > MAX_BEAT_DELTA_SEC + 1e-9:
            blockers.append(
                f"beat '{label}' audio/visual delta is {delta:.3f}s, exceeds {MAX_BEAT_DELTA_SEC:.1f}s"
            )
        normalized.append(
            {
                "label": label,
                "audioSec": round(audio_sec, 3) if audio_sec is not None else None,
                "visualSec": round(visual_sec, 3) if visual_sec is not None else None,
                "contactSec": round(contact_sec, 3) if contact_sec is not None else None,
                "deltaSec": round(delta, 3) if delta is not None else None,
                "withinTolerance": delta is None or delta <= MAX_BEAT_DELTA_SEC + 1e-9,
                "cropBox": raw.get("cropBox") or raw.get("crop"),
            }
        )
    return normalized, top_level_crops, blockers


def validate_beat_map(payload: Any) -> dict[str, Any]:
    beats, crop_boxes, blockers = normalize_beat_map(payload)
    return {
        "present": True,
        "passed": not blockers,
        "blockers": blockers,
        "maxAllowedDeltaSec": MAX_BEAT_DELTA_SEC,
        "beats": beats,
        "cropBoxes": crop_boxes,
    }


def _normalized_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value))
    return re.sub(r"\s+", " ", text).strip().casefold()


def _value_present(canonical: Any, occurrence: Any) -> bool:
    expected = _normalized_text(canonical)
    actual = _normalized_text(occurrence)
    if not expected or not actual:
        return False
    if actual == expected:
        return True
    # Keep canonical values discrete: ``35`` must not pass against ``350`` or
    # ``35+``. Ordinary sentence punctuation after a fact is valid, so commas
    # and periods cannot be part of the boundary guard.
    return re.search(
        rf"(?<![A-Za-z0-9$]){re.escape(expected)}(?![A-Za-z0-9+%])",
        actual,
    ) is not None


def _iter_occurrences(fact: Mapping[str, Any]) -> list[tuple[str, Any]]:
    occurrences = fact.get("occurrences")
    if isinstance(occurrences, Mapping):
        return [(str(key), value) for key, value in occurrences.items()]
    if isinstance(occurrences, list):
        result: list[tuple[str, Any]] = []
        for index, value in enumerate(occurrences, start=1):
            if isinstance(value, Mapping):
                result.append((str(value.get("source") or value.get("label") or index), value.get("value")))
            else:
                result.append((str(index), value))
        return result
    fields = ("proof", "rewrite", "receipt", "spoken", "visible", "script", "proofValue", "rewriteValue", "receiptValue")
    return [(key, fact.get(key)) for key in fields if fact.get(key) is not None]


def _score_receipt(ledger: Mapping[str, Any]) -> Mapping[str, Any] | None:
    candidate = ledger.get("scores") or ledger.get("scoreReceipt") or ledger.get("score")
    return candidate if isinstance(candidate, Mapping) else None


def validate_evidence_ledger(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {"present": True, "passed": False, "blockers": ["evidence ledger must be a JSON object"]}

    blockers: list[str] = []
    checks: list[dict[str, Any]] = []
    recognized = 0
    raw_facts = payload.get("facts") or payload.get("claims") or payload.get("evidence") or []
    if isinstance(raw_facts, list):
        for index, fact in enumerate(raw_facts, start=1):
            if not isinstance(fact, Mapping):
                blockers.append(f"evidence fact {index} is not an object")
                continue
            fact_id = str(fact.get("id") or fact.get("label") or f"fact-{index}")
            canonical = fact.get("value") if fact.get("value") is not None else fact.get("expected")
            occurrences = _iter_occurrences(fact)
            if canonical is None or len(occurrences) < 2:
                blockers.append(f"evidence fact '{fact_id}' requires a canonical value and at least two occurrences")
                continue
            recognized += 1
            mismatches = [source for source, value in occurrences if not _value_present(canonical, value)]
            check = {
                "id": fact_id,
                "canonicalValue": str(canonical),
                "occurrenceCount": len(occurrences),
                "sources": [source for source, _ in occurrences],
                "passed": not mismatches,
                "mismatchedSources": mismatches,
            }
            checks.append(check)
            if mismatches:
                blockers.append(
                    f"evidence fact '{fact_id}' value '{canonical}' does not agree in: {', '.join(mismatches)}"
                )

    comparisons = payload.get("comparisons") or []
    if isinstance(comparisons, list):
        for index, comparison in enumerate(comparisons, start=1):
            if not isinstance(comparison, Mapping):
                blockers.append(f"evidence comparison {index} is not an object")
                continue
            comparison_id = str(comparison.get("id") or comparison.get("label") or f"comparison-{index}")
            expected = comparison.get("expected")
            values = comparison.get("values")
            if not isinstance(values, list):
                values = [comparison.get("actual")]
            values = [value for value in values if value is not None]
            if expected is None or not values:
                blockers.append(f"evidence comparison '{comparison_id}' requires expected and actual values")
                continue
            recognized += 1
            mismatches = [str(value) for value in values if _normalized_text(value) != _normalized_text(expected)]
            checks.append(
                {
                    "id": comparison_id,
                    "expected": str(expected),
                    "actualValues": [str(value) for value in values],
                    "passed": not mismatches,
                }
            )
            if mismatches:
                blockers.append(f"evidence comparison '{comparison_id}' does not match expected value '{expected}'")

    score = _score_receipt(payload)
    score_check: dict[str, Any] | None = None
    if score:
        rows = score.get("rows") or score.get("items") or []
        before_total = _safe_float(score.get("beforeTotal") if score.get("beforeTotal") is not None else score.get("before"))
        after_total = _safe_float(score.get("afterTotal") if score.get("afterTotal") is not None else score.get("after"))
        before_values: list[float] = []
        after_values: list[float] = []
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, Mapping):
                    continue
                before = _safe_float(row.get("before") if row.get("before") is not None else row.get("beforeScore"))
                after = _safe_float(row.get("after") if row.get("after") is not None else row.get("afterScore"))
                if before is not None and after is not None:
                    before_values.append(before)
                    after_values.append(after)
        if before_total is not None and after_total is not None and before_values and len(before_values) == len(after_values):
            recognized += 1
            before_sum = sum(before_values)
            after_sum = sum(after_values)
            score_passed = math.isclose(before_sum, before_total, abs_tol=1e-6) and math.isclose(after_sum, after_total, abs_tol=1e-6)
            score_check = {
                "beforeTotal": before_total,
                "afterTotal": after_total,
                "beforeRowSum": before_sum,
                "afterRowSum": after_sum,
                "rowCount": len(before_values),
                "passed": score_passed,
            }
            if not score_passed:
                blockers.append("score receipt row sums do not equal its before/after totals")
        else:
            blockers.append("score receipt is not reproducible from before/after row values")

    if recognized == 0:
        blockers.append("evidence ledger contains no verifiable fact, comparison, or reproducible score receipt")

    return {
        "present": True,
        "passed": not blockers,
        "blockers": blockers,
        "recognizedCheckCount": recognized,
        "checks": checks,
        "scoreCheck": score_check,
    }


def extract_frame(video: Path, at_sec: float, output: Path, *, literal_first: bool = False) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    command = [find_executable("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-i", str(video)]
    if literal_first:
        command.extend(["-vf", "select=eq(n\\,0)", "-frames:v", "1"])
    else:
        command.extend(["-ss", f"{at_sec:.6f}", "-frames:v", "1"])
    command.extend(["-an", "-compression_level", "3", str(output)])
    run_command(command)
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError(f"frame at {at_sec:.2f}s was not created")


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._")
    return cleaned[:80] or "frame"


def _font(size: int) -> ImageFont.ImageFont:
    candidates = (
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "arial.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                pass
    return ImageFont.load_default()


def make_contact_sheet(entries: Sequence[Mapping[str, Any]], output: Path, run_id: str) -> None:
    if not entries:
        raise RuntimeError("no frames were supplied for the contact sheet")
    columns = 3
    thumb_width = 300
    thumb_height = int(round(thumb_width * TARGET_HEIGHT / TARGET_WIDTH))
    label_height = 78
    gap = 18
    header_height = 74
    rows = math.ceil(len(entries) / columns)
    width = columns * thumb_width + (columns + 1) * gap
    height = header_height + rows * (thumb_height + label_height + gap) + gap
    sheet = Image.new("RGB", (width, height), "#0b1220")
    draw = ImageDraw.Draw(sheet)
    draw.text((gap, 18), f"Signal final review | {run_id}", fill="#f8fafc", font=_font(28))
    label_font = _font(20)
    time_font = _font(23)

    for index, entry in enumerate(entries):
        row, column = divmod(index, columns)
        left = gap + column * (thumb_width + gap)
        top = header_height + gap + row * (thumb_height + label_height + gap)
        frame_path = Path(str(entry["path"]))
        with Image.open(frame_path) as source:
            image = source.convert("RGB")
            image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (thumb_width, thumb_height), "#111827")
            canvas.paste(image, ((thumb_width - image.width) // 2, (thumb_height - image.height) // 2))
            sheet.paste(canvas, (left, top))
        label_top = top + thumb_height
        draw.rectangle((left, label_top, left + thumb_width, label_top + label_height), fill="#111827")
        draw.text((left + 12, label_top + 8), f"{float(entry['timeSec']):.2f}s", fill="#67e8f9", font=time_font)
        label = str(entry.get("label") or "Review frame")
        if len(label) > 34:
            label = label[:31] + "..."
        draw.text((left + 12, label_top + 42), label, fill="#cbd5e1", font=label_font)

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG", optimize=True)


def _crop_rectangle(raw: Any, width: int, height: int) -> tuple[int, int, int, int]:
    if isinstance(raw, Mapping) and isinstance(raw.get("box"), (Mapping, list, tuple)):
        raw = raw.get("box")
    normalized = bool(raw.get("normalized")) if isinstance(raw, Mapping) else False
    if isinstance(raw, Mapping):
        if all(key in raw for key in ("left", "top", "right", "bottom")):
            left = _safe_float(raw.get("left"))
            top = _safe_float(raw.get("top"))
            right = _safe_float(raw.get("right"))
            bottom = _safe_float(raw.get("bottom"))
        else:
            x = _safe_float(raw.get("x"))
            y = _safe_float(raw.get("y"))
            crop_width = _safe_float(raw.get("width") if raw.get("width") is not None else raw.get("w"))
            crop_height = _safe_float(raw.get("height") if raw.get("height") is not None else raw.get("h"))
            if None in (x, y, crop_width, crop_height):
                raise ValueError("crop box requires x/y/width/height")
            left, top, right, bottom = x, y, x + crop_width, y + crop_height
    elif isinstance(raw, (list, tuple)) and len(raw) == 4:
        x, y, crop_width, crop_height = (_safe_float(value) for value in raw)
        if None in (x, y, crop_width, crop_height):
            raise ValueError("crop box values must be numeric")
        left, top, right, bottom = x, y, x + crop_width, y + crop_height
    else:
        raise ValueError("crop box must be an object or [x,y,width,height]")

    values = (left, top, right, bottom)
    if any(value is None for value in values):
        raise ValueError("crop box contains a missing coordinate")
    if normalized or all(0.0 <= float(value) <= 1.0 for value in values):
        left, right = float(left) * width, float(right) * width
        top, bottom = float(top) * height, float(bottom) * height
    left_i = max(0, min(width, int(round(float(left)))))
    top_i = max(0, min(height, int(round(float(top)))))
    right_i = max(0, min(width, int(round(float(right)))))
    bottom_i = max(0, min(height, int(round(float(bottom)))))
    if right_i <= left_i or bottom_i <= top_i:
        raise ValueError("crop box is empty or outside the frame")
    return left_i, top_i, right_i, bottom_i


def collect_crop_specs(beat_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for beat in beat_report.get("beats") or []:
        if beat.get("cropBox") is not None:
            specs.append(
                {
                    "label": beat.get("label") or "beat-crop",
                    "timeSec": beat.get("contactSec"),
                    "box": beat.get("cropBox"),
                }
            )
    for index, raw in enumerate(beat_report.get("cropBoxes") or [], start=1):
        if not isinstance(raw, Mapping):
            continue
        specs.append(
            {
                "label": raw.get("label") or raw.get("name") or f"crop-{index}",
                "timeSec": _pick_number(raw, ("timeSec", "visualSec", "atSec", "timestampSec")),
                "box": raw.get("box") or raw.get("cropBox") or raw,
            }
        )
    return specs


def generate_crops(video: Path, crop_specs: Sequence[Mapping[str, Any]], output_dir: Path, duration_sec: float) -> tuple[list[dict[str, Any]], list[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    blockers: list[str] = []
    for index, spec in enumerate(crop_specs, start=1):
        label = str(spec.get("label") or f"crop-{index}")
        time_sec = _safe_float(spec.get("timeSec"))
        if time_sec is None or not 0.0 <= time_sec <= max(0.0, duration_sec):
            blockers.append(f"crop '{label}' has an invalid timestamp")
            continue
        source = output_dir / f"_{index:02d}_{_safe_name(label)}_source.png"
        target = output_dir / f"{index:02d}_{_safe_name(label)}_{time_sec:.2f}s.png"
        try:
            extract_frame(video, time_sec, source, literal_first=time_sec == 0.0)
            with Image.open(source) as image:
                image = image.convert("RGB")
                rectangle = _crop_rectangle(spec.get("box"), image.width, image.height)
                image.crop(rectangle).save(target, format="PNG", optimize=True)
            source.unlink(missing_ok=True)
            results.append(
                {
                    "label": label,
                    "timeSec": round(time_sec, 3),
                    "boxPx": list(rectangle),
                    "path": str(target),
                    "sha256": sha256_file(target),
                }
            )
        except Exception as exc:
            blockers.append(f"crop '{label}' failed: {exc}")
            source.unlink(missing_ok=True)
    return results, blockers


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def build_review_packet(
    *,
    work_dir: Path,
    video: Path,
    script: Path,
    run_id: str,
    beat_map: Path | None = None,
    evidence_ledger: Path | None = None,
) -> dict[str, Any]:
    work_dir = work_dir.resolve()
    video = video.resolve()
    script = script.resolve()
    beat_map = beat_map.resolve() if beat_map else None
    evidence_ledger = evidence_ledger.resolve() if evidence_ledger else None
    work_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = work_dir / "review_frames"
    crops_dir = work_dir / "review_crops"
    gate_dir = work_dir / "quality_gates"
    manifest_path = work_dir / "review_manifest.json"
    contact_sheet_path = work_dir / "final_contact_sheet.png"
    decoded_audio_path = work_dir / "final_review_audio.wav"
    blockers: list[str] = []
    warnings: list[str] = []

    hashes: dict[str, Any] = {"videoSha256": None, "scriptSha256": None, "audioSha256": None}
    for label, path, key in (("video", video, "videoSha256"), ("script", script, "scriptSha256")):
        if not path.exists() or not path.is_file():
            blockers.append(f"{label} file not found: {path}")
        else:
            hashes[key] = sha256_file(path)

    media_report: dict[str, Any] = {"passed": False, "blockers": ["video was not probed"]}
    probe: dict[str, Any] = {}
    if video.exists():
        try:
            probe = ffprobe_json(video)
            media_report = validate_media(probe)
            blockers.extend(media_report["blockers"])
        except Exception as exc:
            media_report = {"passed": False, "blockers": [f"ffprobe failed: {exc}"]}
            blockers.extend(media_report["blockers"])
    duration_sec = float(media_report.get("durationSec") or 0.0)

    audio_report: dict[str, Any] = {"decodedAudioPath": str(decoded_audio_path)}
    if video.exists():
        try:
            extract_audio(video, decoded_audio_path)
            hashes["audioSha256"] = sha256_file(decoded_audio_path)
            audio_report, audio_blockers, audio_warnings = analyze_audio(video, decoded_audio_path)
            blockers.extend(audio_blockers)
            warnings.extend(audio_warnings)
        except Exception as exc:
            blockers.append(f"final audio extraction/analysis failed: {exc}")
    if not hashes.get("audioSha256"):
        blockers.append("decoded final audio SHA-256 is missing")

    beat_report: dict[str, Any] = {"present": False, "passed": True, "blockers": [], "beats": [], "cropBoxes": []}
    if beat_map:
        if not beat_map.exists():
            beat_report = {"present": True, "passed": False, "blockers": [f"beat map not found: {beat_map}"], "beats": [], "cropBoxes": []}
        else:
            hashes["beatMapSha256"] = sha256_file(beat_map)
            try:
                beat_report = validate_beat_map(load_json(beat_map))
            except Exception as exc:
                beat_report = {"present": True, "passed": False, "blockers": [f"beat map could not be read: {exc}"], "beats": [], "cropBoxes": []}
        blockers.extend(beat_report.get("blockers") or [])

    evidence_report: dict[str, Any] = {"present": False, "passed": True, "blockers": []}
    if evidence_ledger:
        if not evidence_ledger.exists():
            evidence_report = {"present": True, "passed": False, "blockers": [f"evidence ledger not found: {evidence_ledger}"]}
        else:
            hashes["evidenceLedgerSha256"] = sha256_file(evidence_ledger)
            try:
                evidence_report = validate_evidence_ledger(load_json(evidence_ledger))
            except Exception as exc:
                evidence_report = {"present": True, "passed": False, "blockers": [f"evidence ledger could not be read: {exc}"]}
        blockers.extend(evidence_report.get("blockers") or [])

    literal_frames: list[dict[str, Any]] = []
    frames_dir.mkdir(parents=True, exist_ok=True)
    if video.exists():
        for at_sec in LITERAL_FRAME_TIMES:
            millis = int(round(at_sec * 1000))
            frame_path = frames_dir / f"literal_{millis:04d}_{at_sec:.2f}s.png"
            try:
                extract_frame(video, at_sec, frame_path, literal_first=at_sec == 0.0)
                literal_frames.append(
                    {
                        "label": "Literal frame" if at_sec else "Literal frame zero",
                        "timeSec": at_sec,
                        "path": str(frame_path),
                        "sha256": sha256_file(frame_path),
                    }
                )
            except Exception as exc:
                blockers.append(f"literal frame {at_sec:.2f}s failed: {exc}")
    expected_literal_paths = {round(item["timeSec"], 2): Path(item["path"]) for item in literal_frames}
    for at_sec in LITERAL_FRAME_TIMES:
        if round(at_sec, 2) not in expected_literal_paths or not expected_literal_paths[round(at_sec, 2)].exists():
            blockers.append(f"literal frame file is missing at {at_sec:.2f}s")

    contact_entries: list[dict[str, Any]] = list(literal_frames)
    if video.exists():
        for index, beat in enumerate(beat_report.get("beats") or [], start=1):
            time_sec = _safe_float(beat.get("contactSec"))
            label = str(beat.get("label") or f"Beat {index}")
            if time_sec is None or not 0.0 <= time_sec <= duration_sec:
                blockers.append(f"beat '{label}' contact timestamp is outside the video")
                continue
            frame_path = frames_dir / f"beat_{index:02d}_{_safe_name(label)}_{time_sec:.2f}s.png"
            try:
                extract_frame(video, time_sec, frame_path, literal_first=time_sec == 0.0)
                contact_entries.append(
                    {"label": label, "timeSec": round(time_sec, 3), "path": str(frame_path), "sha256": sha256_file(frame_path)}
                )
            except Exception as exc:
                blockers.append(f"beat frame '{label}' failed: {exc}")
    try:
        make_contact_sheet(contact_entries, contact_sheet_path, run_id)
    except Exception as exc:
        blockers.append(f"final contact sheet failed: {exc}")
    if not contact_sheet_path.exists() or contact_sheet_path.stat().st_size == 0:
        blockers.append("final contact sheet is missing")

    crop_specs = collect_crop_specs(beat_report)
    crops, crop_blockers = generate_crops(video, crop_specs, crops_dir, duration_sec) if video.exists() and crop_specs else ([], [])
    blockers.extend(crop_blockers)
    if crop_specs and len(crops) != len(crop_specs):
        blockers.append(f"generated {len(crops)} of {len(crop_specs)} supplied full-resolution crops")

    for key in ("videoSha256", "scriptSha256", "audioSha256"):
        value = hashes.get(key)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            blockers.append(f"{key} is missing or invalid")

    blockers = list(dict.fromkeys(blockers))
    warnings = list(dict.fromkeys(warnings))
    input_digest = sha256_text(
        "\n".join(str(hashes.get(key) or "") for key in sorted(hashes))
    )
    deterministic_passed = not blockers
    manifest: dict[str, Any] = {
        "schemaVersion": 1,
        "gateVersion": GATE_VERSION,
        "runId": run_id,
        "createdAt": utc_now(),
        "humanWatchRequired": True,
        "humanWatchCompleted": False,
        "deterministicPassed": deterministic_passed,
        "publishingAttempted": False,
        "stateTransitioned": False,
        "inputs": {
            "workDir": str(work_dir),
            "video": str(video),
            "script": str(script),
            "beatMap": str(beat_map) if beat_map else None,
            "evidenceLedger": str(evidence_ledger) if evidence_ledger else None,
        },
        "hashes": hashes,
        "inputDigest": input_digest,
        "media": media_report,
        "audioQa": audio_report,
        "beatMapQa": beat_report,
        "evidenceLedgerQa": evidence_report,
        "artifacts": {
            "literalFrames": literal_frames,
            "contactSheet": {
                "path": str(contact_sheet_path),
                "sha256": sha256_file(contact_sheet_path) if contact_sheet_path.exists() else None,
                "frameCount": len(contact_entries),
            },
            "fullResolutionCrops": crops,
            "decodedAudio": {
                "path": str(decoded_audio_path),
                "sha256": hashes.get("audioSha256"),
            },
        },
        "blockers": blockers,
        "warnings": warnings,
        "approval": {
            "status": "DETERMINISTIC_QA_PASSED_AWAITING_HUMAN_WATCH" if deterministic_passed else "DETERMINISTIC_QA_FAILED",
            "codexApprovalRequired": True,
            "approved": False,
        },
    }
    _write_json(manifest_path, manifest)

    gate: dict[str, Any] = {
        "gate": "final_review_packet",
        "gateVersion": GATE_VERSION,
        "checkedAt": utc_now(),
        "runId": run_id,
        "passed": deterministic_passed,
        "humanWatchRequired": True,
        "humanWatchCompleted": False,
        "codexApprovalRequired": True,
        "publishingAttempted": False,
        "stateTransitioned": False,
        "inputDigest": input_digest,
        "reviewManifest": str(manifest_path),
        "reviewManifestSha256": sha256_file(manifest_path),
        "blockers": blockers,
        "warnings": warnings,
        "checks": {
            "mediaContract": bool(media_report.get("passed")),
            "requiredHashesRecorded": all(bool(hashes.get(key)) for key in ("videoSha256", "scriptSha256", "audioSha256")),
            "literalFramesPresent": len(literal_frames) == len(LITERAL_FRAME_TIMES),
            "contactSheetPresent": contact_sheet_path.exists(),
            "beatMapContract": bool(beat_report.get("passed")),
            "evidenceLedgerContract": bool(evidence_report.get("passed")),
            "audioSilenceChecked": bool((audio_report.get("silence") or {}).get("checked")),
            "audioPeakChecked": bool((audio_report.get("peak") or {}).get("checked")),
            "suppliedCropsGenerated": len(crops) == len(crop_specs),
        },
    }
    gate_path = gate_dir / "final_review_packet.json"
    _write_json(gate_path, gate)
    return {"manifest": manifest, "gate": gate, "manifestPath": manifest_path, "gatePath": gate_path}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Signal's deterministic final-video review packet.")
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--timeline", "--beat-map", dest="beat_map", type=Path)
    parser.add_argument("--evidence-ledger", type=Path)
    parser.add_argument("--run-id", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_review_packet(
        work_dir=args.work_dir,
        video=args.video,
        script=args.script,
        run_id=args.run_id,
        beat_map=args.beat_map,
        evidence_ledger=args.evidence_ledger,
    )
    output = {
        "passed": result["gate"]["passed"],
        "humanWatchRequired": True,
        "manifest": str(result["manifestPath"]),
        "qualityGate": str(result["gatePath"]),
        "contactSheet": result["manifest"]["artifacts"]["contactSheet"]["path"],
        "blockers": result["gate"]["blockers"],
        "publishingAttempted": False,
    }
    print(json.dumps(output, indent=2, ensure_ascii=True))
    return 0 if result["gate"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
