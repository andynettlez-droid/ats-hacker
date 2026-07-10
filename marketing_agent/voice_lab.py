"""ElevenLabs creator-voice lab for the active Signal production pipeline."""

from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


TAKE_PRESETS = (
    {"stability": 0.34, "similarity_boost": 0.82, "style": 0.34, "speed": 1.16},
    {"stability": 0.40, "similarity_boost": 0.84, "style": 0.28, "speed": 1.20},
    {"stability": 0.46, "similarity_boost": 0.86, "style": 0.22, "speed": 1.12},
    {"stability": 0.37, "similarity_boost": 0.80, "style": 0.31, "speed": 1.18},
    {"stability": 0.43, "similarity_boost": 0.85, "style": 0.25, "speed": 1.14},
)


@dataclass(frozen=True)
class TakeScore:
    score: float
    duration_sec: float
    words_per_minute: float
    long_pause_count: int
    word_count: int


def prepare_voice_text(text: str) -> str:
    """Make known trouble words pronounceable without changing on-screen copy."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"\bresume\b", "résumé", cleaned, flags=re.IGNORECASE)
    replacements = {
        r"\bVPN\b": "V P N",
        r"\bATS\b": "A T S",
        r"\bMQL\b": "M Q L",
        r"\bSQL\b": "S Q L",
    }
    for pattern, replacement in replacements.items():
        cleaned = re.sub(pattern, replacement, cleaned)
    return cleaned


def normalize_alignment(payload: dict[str, Any]) -> list[dict[str, Any]]:
    source = payload.get("normalized_alignment") or payload.get("alignment") or payload
    chars = source.get("characters") or []
    starts = source.get("character_start_times_seconds") or []
    ends = source.get("character_end_times_seconds") or []
    if not chars or not starts:
        return []
    if not ends:
        ends = list(starts[1:]) + [float(starts[-1]) + 0.08]

    words: list[dict[str, Any]] = []
    current: list[str] = []
    start: float | None = None
    end: float | None = None
    for char, char_start, char_end in zip(chars, starts, ends):
        if str(char).isspace():
            if current and start is not None and end is not None:
                words.append({"word": "".join(current), "startSec": round(start, 3), "endSec": round(end, 3)})
            current, start, end = [], None, None
            continue
        if start is None:
            start = float(char_start)
        current.append(str(char))
        end = float(char_end)
    if current and start is not None and end is not None:
        words.append({"word": "".join(current), "startSec": round(start, 3), "endSec": round(end, 3)})
    return words


def score_take(words: list[dict[str, Any]], target_wpm: float = 166.0) -> TakeScore:
    if not words:
        return TakeScore(0.0, 0.0, 0.0, 99, 0)
    duration = max(float(words[-1]["endSec"]), 0.001)
    word_count = len(words)
    wpm = word_count / duration * 60
    pauses = [
        max(0.0, float(current["startSec"]) - float(previous["endSec"]))
        for previous, current in zip(words, words[1:])
    ]
    long_pause_count = sum(1 for pause in pauses if pause > 0.85)
    very_short_count = sum(1 for pause in pauses if 0 < pause < 0.015)
    pace_penalty = abs(wpm - target_wpm) * 0.85
    range_penalty = 35 if wpm < 140 or wpm > 190 else 0
    score = 120 - pace_penalty - long_pause_count * 18 - very_short_count * 0.5 - range_penalty
    return TakeScore(round(score, 3), round(duration, 3), round(wpm, 2), long_pause_count, word_count)


def request_take(
    *,
    api_key: str,
    voice_id: str,
    model_id: str,
    text: str,
    preset: dict[str, float],
    seed: int,
    timeout_sec: int = 120,
) -> tuple[bytes, dict[str, Any]]:
    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps",
        headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "application/json"},
        params={"output_format": "mp3_44100_128"},
        json={
            "text": text,
            "model_id": model_id,
            "seed": seed,
            "apply_text_normalization": "on",
            "voice_settings": {
                "stability": preset["stability"],
                "similarity_boost": preset["similarity_boost"],
                "style": preset["style"],
                "speed": preset["speed"],
                "use_speaker_boost": True,
            },
        },
        timeout=timeout_sec,
    )
    if not response.ok:
        raise RuntimeError(f"ElevenLabs returned {response.status_code}: {response.text[:400]}")
    payload = response.json()
    audio = payload.get("audio_base64")
    if not audio:
        raise RuntimeError("ElevenLabs timestamp response omitted audio_base64")
    return base64.b64decode(audio), payload


def retime_words(words: list[dict[str, Any]], speed_factor: float) -> list[dict[str, Any]]:
    if speed_factor <= 0:
        raise ValueError("speed_factor must be positive")
    return [
        {
            **word,
            "startSec": round(float(word["startSec"]) / speed_factor, 3),
            "endSec": round(float(word["endSec"]) / speed_factor, 3),
        }
        for word in words
    ]


def master_audio(
    source: Path,
    output: Path,
    speed_factor: float = 1.0,
    trim_duration_sec: float | None = None,
) -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        shutil.copyfile(source, output)
        return "copy-no-ffmpeg"
    filters = [f"atempo={speed_factor:.6f}"]
    if trim_duration_sec is not None:
        filters.append(f"atrim=end={trim_duration_sec:.3f}")
    filters.extend(("highpass=f=65", "lowpass=f=16000", "loudnorm=I=-16:TP=-1.5:LRA=7"))
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(source),
        "-af",
        ",".join(filters),
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "192k",
        str(output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or "ffmpeg voice mastering failed")[-800:])
    return f"ffmpeg-atempo-{speed_factor:.4f}-loudnorm--16lufs"


def generate_voice_lab(
    *,
    display_text: str,
    output: Path,
    api_key: str,
    voice_id: str,
    model_id: str = "eleven_multilingual_v2",
    take_count: int = 3,
    target_wpm: float = 166.0,
) -> dict[str, Any]:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    voice_text = prepare_voice_text(display_text)
    takes: list[dict[str, Any]] = []
    errors: list[str] = []

    for index in range(1, max(1, min(5, take_count)) + 1):
        take_path = output.with_name(f"{output.stem}.take-{index}.raw.mp3")
        alignment_path = output.with_name(f"{output.stem}.take-{index}.alignment.json")
        preset = TAKE_PRESETS[index - 1]
        try:
            audio, payload = request_take(
                api_key=api_key,
                voice_id=voice_id,
                model_id=model_id,
                text=voice_text,
                preset=preset,
                seed=1977 + index,
            )
            take_path.write_bytes(audio)
            words = normalize_alignment(payload)
            score = score_take(words, target_wpm)
            alignment_path.write_text(json.dumps({"words": words, "raw": payload}, indent=2), encoding="utf-8")
            takes.append(
                {
                    "take": index,
                    "audio": str(take_path),
                    "alignment": str(alignment_path),
                    "settings": preset,
                    "score": score.score,
                    "durationSec": score.duration_sec,
                    "wordsPerMinute": score.words_per_minute,
                    "longPauseCount": score.long_pause_count,
                    "wordCount": score.word_count,
                }
            )
        except Exception as error:
            errors.append(f"take {index}: {error}")

    if not takes:
        raise RuntimeError("All ElevenLabs creator takes failed: " + " | ".join(errors))
    selected = max(takes, key=lambda item: float(item["score"]))
    raw_alignment = json.loads(Path(selected["alignment"]).read_text(encoding="utf-8"))
    raw_words = raw_alignment.get("words") or []
    raw_wpm = float(selected.get("wordsPerMinute") or 0)
    post_speed_factor = min(max(target_wpm / raw_wpm, 1.0), 1.22) if raw_wpm > 0 else 1.0
    mastered_words = retime_words(raw_words, post_speed_factor)
    mastered_score = score_take(mastered_words, target_wpm)
    mastering = master_audio(
        Path(selected["audio"]),
        output,
        post_speed_factor,
        mastered_score.duration_sec + 0.35,
    )
    output_alignment = output.with_suffix(output.suffix + ".alignment.json")
    output_alignment.write_text(
        json.dumps(
            {
                "words": mastered_words,
                "raw": raw_alignment.get("raw"),
                "sourceAlignment": selected["alignment"],
                "postSpeedFactor": round(post_speed_factor, 6),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    selected["rawDurationSec"] = selected["durationSec"]
    selected["rawWordsPerMinute"] = selected["wordsPerMinute"]
    selected["postSpeedFactor"] = round(post_speed_factor, 6)
    selected["durationSec"] = mastered_score.duration_sec
    selected["wordsPerMinute"] = mastered_score.words_per_minute
    selected["longPauseCount"] = mastered_score.long_pause_count
    selected["score"] = mastered_score.score
    manifest = {
        "provider": "elevenlabs",
        "voiceId": voice_id,
        "modelId": model_id,
        "displayText": display_text,
        "voiceText": voice_text,
        "takeCount": len(takes),
        "targetWordsPerMinute": target_wpm,
        "selectedTake": selected["take"],
        "selectedScore": selected["score"],
        "postSpeedFactor": round(post_speed_factor, 6),
        "mastering": mastering,
        "output": str(output),
        "alignment": str(output_alignment),
        "takes": takes,
        "errors": errors,
    }
    manifest_path = output.with_suffix(output.suffix + ".voice-lab.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["manifest"] = str(manifest_path)
    return manifest
