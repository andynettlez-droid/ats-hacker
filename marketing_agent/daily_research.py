"""Build a source-backed daily research packet for Signal content production.

The module deliberately contains no LLM calls. It normalizes evidence collected by
other tools, ranks sources with transparent arithmetic, and refuses to label social
posts as browser-observed unless the input includes an observer, timestamp, and
screenshots. All network discovery is optional; fixtures can exercise the complete
pipeline offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "marketing" / "research" / "daily"
TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "igsh",
    "si",
    "ref",
    "ref_src",
    "source",
    "feature",
}
PLATFORM_HOSTS = {
    "youtube": {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"},
    "tiktok": {"tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"},
    "instagram": {"instagram.com", "www.instagram.com", "m.instagram.com"},
    "linkedin": {"linkedin.com", "www.linkedin.com"},
}
SCORE_WEIGHTS = {
    "freshness": 0.30,
    "views_per_day": 0.25,
    "engagement": 0.10,
    "evidence_fit": 0.20,
    "novelty": 0.15,
}


@dataclass(frozen=True)
class GateThresholds:
    min_short_sources: int = 20
    min_first_seen_today: int = 8
    min_recent_90d: int = 12
    max_evergreen_over_year: int = 4
    creator_cap: int = 2
    min_youtube: int = 12
    min_browser_tiktok: int = 2
    min_browser_instagram: int = 2
    min_valid_youtube_transcripts: int = 8
    min_reviewed_youtube_contact_sheets: int = 6
    min_top_sources_with_full_evidence: int = 10
    min_novelty_rate: float = 0.40
    max_packet_age_hours: float = 24.0
    max_long_form_authority: int = 2
    required_angle_count: int = 3
    min_angle_sources: int = 3
    min_angle_platforms: int = 2


def _pick(record: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in record:
            return record[key]
    return default


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, time.min, tzinfo=timezone.utc)
    elif isinstance(value, str) and value.strip():
        candidate = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            for fmt in ("%Y%m%d", "%Y-%m-%d"):
                try:
                    parsed = datetime.strptime(candidate, fmt)
                    break
                except ValueError:
                    continue
            else:
                return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_or_none(value: Any) -> str | None:
    parsed = parse_datetime(value)
    return parsed.isoformat() if parsed else None


def nullable_number(value: Any) -> int | float | None:
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return int(number) if number.is_integer() else number


def infer_platform(url: str, explicit: str = "") -> str:
    supplied = explicit.strip().lower()
    if supplied:
        return supplied
    host = (urlparse(url).hostname or "").lower()
    for platform, hosts in PLATFORM_HOSTS.items():
        if host in hosts or any(host.endswith(f".{item}") for item in hosts):
            return platform
    return "unknown"


def youtube_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    parts = [part for part in parsed.path.split("/") if part]
    if host == "youtu.be" and parts:
        return parts[0]
    if parts and parts[0] in {"shorts", "embed", "live"} and len(parts) > 1:
        return parts[1]
    for key, value in parse_qsl(parsed.query, keep_blank_values=False):
        if key == "v" and value:
            return value
    return ""


def platform_post_id(url: str, platform: str) -> str:
    if platform == "youtube":
        return youtube_video_id(url)
    parts = [part for part in urlparse(url).path.split("/") if part]
    if platform == "instagram":
        for marker in ("reel", "reels", "p", "tv"):
            if marker in parts and parts.index(marker) + 1 < len(parts):
                return parts[parts.index(marker) + 1]
    if platform == "tiktok" and "video" in parts and parts.index("video") + 1 < len(parts):
        return parts[parts.index("video") + 1]
    return parts[-1] if parts else ""


def canonicalize_url(url: str, platform: str = "") -> str:
    raw = _text(url)
    if not raw:
        return ""
    if "://" not in raw:
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    resolved_platform = infer_platform(raw, platform)
    if resolved_platform == "youtube":
        video_id = youtube_video_id(raw)
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    scheme = "https"
    if resolved_platform in PLATFORM_HOSTS:
        host = {
            "instagram": "www.instagram.com",
            "tiktok": "www.tiktok.com",
            "linkedin": "www.linkedin.com",
        }.get(resolved_platform, host)
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=False):
        lower = key.lower()
        if lower.startswith("utm_") or lower in TRACKING_QUERY_KEYS:
            continue
        query.append((key, value))
    query.sort()
    return urlunparse((scheme, host, path, "", urlencode(query), ""))


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "unclassified"


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, Sequence):
        return []
    return [_text(item) for item in value if _text(item)]


def _beats(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    beats: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        start = nullable_number(_pick(item, "start_sec", "startSec", "start"))
        end = nullable_number(_pick(item, "end_sec", "endSec", "end"))
        description = _text(_pick(item, "description", "beat", "text"))
        if description and start is not None:
            beats.append({"start_sec": start, "end_sec": end, "description": description})
    return beats


def _browser_evidence(record: Mapping[str, Any]) -> dict[str, Any]:
    access = _text(_pick(record, "access_state", "accessState")).lower()
    observer = _text(_pick(record, "observer"))
    observed_at = iso_or_none(_pick(record, "observed_at", "observedAt"))
    screenshots = _string_list(_pick(record, "screenshot_paths", "screenshotPaths", default=[]))
    is_observed = access in {"browser_observed", "observed"} and bool(observer and observed_at and screenshots)
    if not is_observed:
        return {
            "access_state": "not_observed",
            "observer": None,
            "observed_at": None,
            "screenshot_paths": [],
            "visible_caption": None,
            "visible_metrics": None,
            "audio_observed": False,
        }
    visible_metrics = _pick(record, "visible_metrics", "visibleMetrics")
    return {
        "access_state": "browser_observed",
        "observer": observer,
        "observed_at": observed_at,
        "screenshot_paths": screenshots,
        "visible_caption": _text(_pick(record, "visible_caption", "visibleCaption")) or None,
        "visible_metrics": dict(visible_metrics) if isinstance(visible_metrics, Mapping) else None,
        "audio_observed": bool(_pick(record, "audio_observed", "audioObserved", default=False)),
    }


def _evidence_fit(source: Mapping[str, Any]) -> float:
    points = 0.0
    points += 0.22 if source.get("hook_0_3") else 0.0
    points += 0.10 if source.get("hook_0_8") else 0.0
    points += 0.18 if source.get("first_frame_observation") else 0.0
    points += 0.18 if source.get("beat_breakdown") else 0.0
    points += 0.15 if source.get("transcript_status") == "valid" else 0.0
    points += 0.12 if source.get("contact_sheet_path") else 0.0
    points += 0.05 if source.get("access_state") == "browser_observed" else 0.0
    return round(min(points, 1.0), 6)


def _freshness_score(published: datetime | None, collected: datetime) -> float | None:
    if not published:
        return None
    days = max(0.0, (collected - published).total_seconds() / 86400)
    if days <= 7:
        return 1.0
    if days <= 30:
        return 0.85
    if days <= 90:
        return 0.65
    if days <= 365:
        return 0.30
    return 0.10


def score_source(source: Mapping[str, Any], previous_fingerprints: set[str] | None = None) -> dict[str, Any]:
    collected = parse_datetime(source.get("collected_at")) or datetime.now(timezone.utc)
    published = parse_datetime(source.get("published_at"))
    views = nullable_number(source.get("views"))
    likes = nullable_number(source.get("likes"))
    comments = nullable_number(source.get("comments"))
    shares = nullable_number(source.get("shares"))
    age_days = max((collected - published).total_seconds() / 86400, 1 / 24) if published else None
    views_per_day = float(views) / age_days if views is not None and age_days is not None else None
    engagement_values = [item for item in (likes, comments, shares) if item is not None]
    engagement_rate = sum(float(item) for item in engagement_values) / float(views) if views and engagement_values else None
    components: dict[str, float | None] = {
        "freshness": _freshness_score(published, collected),
        "views_per_day": min(math.log1p(max(views_per_day, 0)) / math.log1p(100_000), 1.0) if views_per_day is not None else None,
        "engagement": min(max(engagement_rate, 0) / 0.10, 1.0) if engagement_rate is not None else None,
        "evidence_fit": _evidence_fit(source),
        "novelty": (0.0 if source.get("content_fingerprint") in previous_fingerprints else 1.0) if previous_fingerprints is not None else None,
    }
    available_weight = sum(SCORE_WEIGHTS[key] for key, value in components.items() if value is not None)
    score = sum(float(value) * SCORE_WEIGHTS[key] for key, value in components.items() if value is not None)
    normalized_score = 100 * score / available_weight if available_weight else 0.0
    result = dict(source)
    result.update(
        {
            "views_per_day": round(views_per_day, 3) if views_per_day is not None else None,
            "engagement_rate": round(engagement_rate, 6) if engagement_rate is not None else None,
            "score_components": {key: round(value, 6) if value is not None else None for key, value in components.items()},
            "score": round(normalized_score, 3),
        }
    )
    return result


def normalize_source(
    record: Mapping[str, Any],
    *,
    collected_at: datetime,
    research_date: date,
    previous_fingerprints: set[str] | None = None,
) -> dict[str, Any]:
    raw_url = _text(_pick(record, "canonical_url", "canonicalUrl", "url", "webpage_url"))
    platform = infer_platform(raw_url, _text(_pick(record, "platform")))
    canonical_url = canonicalize_url(raw_url, platform)
    post_id = _text(_pick(record, "platform_post_id", "platformPostId", "id")) or platform_post_id(canonical_url, platform)
    creator_id = _text(_pick(record, "creator_id", "creatorId", "channel_id", "uploader_id"))
    creator_name = _text(_pick(record, "creator_name", "creatorName", "channel", "uploader"))
    published_at = iso_or_none(_pick(record, "published_at", "publishedAt", "timestamp", "upload_date"))
    first_seen_at = iso_or_none(_pick(record, "first_seen_at", "firstSeenAt")) or datetime.combine(
        research_date, time.min, tzinfo=timezone.utc
    ).isoformat()
    source_id = _text(_pick(record, "source_id", "sourceId"))
    fingerprint_seed = {
        "platform": platform,
        "platform_post_id": post_id or None,
        "canonical_url": canonical_url or None,
        "creator": creator_id or creator_name or None,
        "title": _text(_pick(record, "title")) or None,
    }
    fingerprint = _text(_pick(record, "content_fingerprint", "contentFingerprint")) or sha256_json(fingerprint_seed)
    source_id = source_id or f"{platform}-{(post_id or fingerprint[:12])}"
    browser = _browser_evidence(record)
    basis = _pick(record, "observation_basis", "observationBasis", default={})
    observation_basis = dict(basis) if isinstance(basis, Mapping) else {}
    duration = nullable_number(_pick(record, "duration_sec", "durationSec", "duration"))
    format_kind = _text(_pick(record, "format_kind", "formatKind")) or (
        "short" if duration is None or float(duration) <= 90 else "authority_long_form"
    )
    transcript_status = _text(_pick(record, "transcript_status", "transcriptStatus")).lower()
    if transcript_status in {"available", "complete", "ok"}:
        transcript_status = "valid"
    normalized = {
        "source_id": source_id,
        "platform": platform,
        "platform_post_id": post_id or None,
        "canonical_url": canonical_url,
        "creator_id": creator_id or None,
        "creator_name": creator_name or None,
        "title": _text(_pick(record, "title")) or None,
        "query": _text(_pick(record, "query")) or None,
        "discovery_surface": _text(_pick(record, "discovery_surface", "discoverySurface")) or None,
        "result_rank": nullable_number(_pick(record, "result_rank", "resultRank")),
        "first_seen_at": first_seen_at,
        "collected_at": collected_at.isoformat(),
        "prior_run_ids": _string_list(_pick(record, "prior_run_ids", "priorRunIds", default=[])),
        "content_fingerprint": fingerprint,
        "published_at": published_at,
        "views": nullable_number(_pick(record, "views", "view_count", "viewCount")),
        "likes": nullable_number(_pick(record, "likes", "like_count", "likeCount")),
        "comments": nullable_number(_pick(record, "comments", "comment_count", "commentCount")),
        "shares": nullable_number(_pick(record, "shares", "share_count", "repost_count", "shareCount")),
        "metrics_captured_at": iso_or_none(_pick(record, "metrics_captured_at", "metricsCapturedAt")),
        "duration_sec": duration,
        "format_kind": format_kind,
        "metadata_status": _text(_pick(record, "metadata_status", "metadataStatus")) or ("available" if canonical_url else "missing"),
        "transcript_status": transcript_status or "missing",
        "transcript_kind": _text(_pick(record, "transcript_kind", "transcriptKind")) or None,
        "transcript_path": _text(_pick(record, "transcript_path", "transcriptPath")) or None,
        "transcript_sha256": _text(_pick(record, "transcript_sha256", "transcriptSha256")) or None,
        "transcript_coverage_sec": nullable_number(_pick(record, "transcript_coverage_sec", "transcriptCoverageSec")),
        "duplicate_token_ratio": nullable_number(_pick(record, "duplicate_token_ratio", "duplicateTokenRatio")),
        "media_status": _text(_pick(record, "media_status", "mediaStatus")) or "missing",
        "contact_sheet_path": _text(_pick(record, "contact_sheet_path", "contactSheetPath")) or None,
        "contact_sheet_times_sec": [
            value
            for value in (nullable_number(item) for item in _pick(record, "contact_sheet_times_sec", "contactSheetTimesSec", default=[]))
            if value is not None
        ],
        **browser,
        "hook_0_3": _text(_pick(record, "hook_0_3", "hook0To3", "hook")) or None,
        "hook_0_8": _text(_pick(record, "hook_0_8", "hook0To8")) or None,
        "first_frame_observation": _text(_pick(record, "first_frame_observation", "firstFrameObservation")) or None,
        "beat_breakdown": _beats(_pick(record, "beat_breakdown", "beatBreakdown", default=[])),
        "caption_style": _text(_pick(record, "caption_style", "captionStyle")) or None,
        "visual_mechanic": _text(_pick(record, "visual_mechanic", "visualMechanic")) or None,
        "human_premise": _text(_pick(record, "human_premise", "humanPremise", "topic")) or None,
        "copy": _text(_pick(record, "copy", "copy_guidance", "copyGuidance")) or None,
        "avoid": _text(_pick(record, "avoid", "avoid_guidance", "avoidGuidance")) or None,
        "claim_risk": _text(_pick(record, "claim_risk", "claimRisk")) or None,
        "angle_id": _slug(_text(_pick(record, "angle_id", "angleId", "human_premise", "humanPremise", "visual_mechanic", "visualMechanic"))),
        "observation_basis": observation_basis,
    }
    return score_source(normalized, previous_fingerprints)


def _dedupe_key(source: Mapping[str, Any]) -> tuple[str, str]:
    post_id = _text(source.get("platform_post_id"))
    return (_text(source.get("platform")), post_id or _text(source.get("content_fingerprint")))


def _merge_sources(primary: dict[str, Any], secondary: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(primary)
    for key, value in secondary.items():
        if merged.get(key) in (None, "", [], {}) and value not in (None, "", [], {}):
            merged[key] = value
    return merged


def deduplicate_sources(sources: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for source in sorted(sources, key=lambda item: (-float(item.get("score") or 0), _text(item.get("source_id")))):
        key = _dedupe_key(source)
        buckets[key] = _merge_sources(buckets[key], source) if key in buckets else dict(source)
    return sorted(buckets.values(), key=lambda item: (-float(item.get("score") or 0), _text(item.get("source_id"))))


def apply_creator_cap(sources: Iterable[dict[str, Any]], cap: int = 2) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    counts: Counter[str] = Counter()
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for source in sources:
        creator = _text(source.get("creator_id") or source.get("creator_name") or source.get("source_id")).lower()
        if counts[creator] >= cap:
            dropped.append(source)
            continue
        counts[creator] += 1
        kept.append(source)
    return kept, dropped


def _has_visual_evidence(source: Mapping[str, Any]) -> bool:
    return bool(source.get("contact_sheet_path") or source.get("access_state") == "browser_observed")


def derive_ranked_angles(sources: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for source in sources:
        if source.get("format_kind") == "short":
            groups[_text(source.get("angle_id")) or "unclassified"].append(source)
    angles: list[dict[str, Any]] = []
    for angle_id, members in groups.items():
        ranked = sorted(members, key=lambda item: (-float(item.get("score") or 0), _text(item.get("source_id"))))
        platforms = sorted({_text(item.get("platform")) for item in ranked if item.get("platform")})
        primary = next((item for item in ranked if _has_visual_evidence(item)), ranked[0])
        copy_items = list(dict.fromkeys(_text(item.get("copy")) for item in ranked if item.get("copy")))
        avoid_items = list(dict.fromkeys(_text(item.get("avoid")) for item in ranked if item.get("avoid")))
        angles.append(
            {
                "angle_id": angle_id,
                "score": round(sum(float(item.get("score") or 0) for item in ranked) / len(ranked), 3),
                "supporting_source_ids": [_text(item.get("source_id")) for item in ranked],
                "platforms": platforms,
                "primary_mechanic_source_id": _text(primary.get("source_id")),
                "primary_has_visual_evidence": _has_visual_evidence(primary),
                "hook_pattern": _text(primary.get("hook_0_3")),
                "first_frame_plan": _text(primary.get("first_frame_observation")),
                "beat_pattern": primary.get("beat_breakdown") or [],
                "copy": copy_items[:5],
                "avoid": avoid_items[:5],
            }
        )
    return sorted(angles, key=lambda item: (-float(item["score"]), item["angle_id"]))


def research_digest_payload(packet: Mapping[str, Any]) -> dict[str, Any]:
    manifest = packet.get("manifest") if isinstance(packet.get("manifest"), Mapping) else {}
    sources: list[dict[str, Any]] = []
    for source in packet.get("sources") or []:
        if not isinstance(source, Mapping):
            continue
        stable_source = dict(source)
        for volatile_key in ("collected_at", "views_per_day", "engagement_rate", "score_components", "score"):
            stable_source.pop(volatile_key, None)
        sources.append(stable_source)
    sources.sort(key=lambda item: (_text(item.get("platform")), _text(item.get("source_id"))))
    angles: list[dict[str, Any]] = []
    for angle in packet.get("ranked_angles") or []:
        if not isinstance(angle, Mapping):
            continue
        stable_angle = dict(angle)
        stable_angle.pop("score", None)
        angles.append(stable_angle)
    angles.sort(key=lambda item: _text(item.get("angle_id")))
    return {
        "research_date": packet.get("research_date"),
        "queries": manifest.get("queries") or [],
        "sources": sources,
        "ranked_angles": angles,
    }


def compute_research_digest(packet: Mapping[str, Any]) -> str:
    return sha256_json(research_digest_payload(packet))


def _valid_transcript(source: Mapping[str, Any]) -> bool:
    duplicate_ratio = nullable_number(source.get("duplicate_token_ratio"))
    return bool(
        source.get("platform") == "youtube"
        and source.get("transcript_status") == "valid"
        and source.get("transcript_path")
        and nullable_number(source.get("transcript_coverage_sec")) is not None
        and float(source.get("transcript_coverage_sec") or 0) >= 8
        and (duplicate_ratio is None or float(duplicate_ratio) <= 0.20)
    )


def _reviewed_contact_sheet(source: Mapping[str, Any]) -> bool:
    return bool(
        source.get("platform") == "youtube"
        and source.get("contact_sheet_path")
        and len(source.get("contact_sheet_times_sec") or []) >= 3
        and source.get("first_frame_observation")
    )


def _full_top_evidence(source: Mapping[str, Any]) -> bool:
    basis = source.get("observation_basis") if isinstance(source.get("observation_basis"), Mapping) else {}
    return bool(
        source.get("hook_0_3")
        and source.get("first_frame_observation")
        and source.get("beat_breakdown")
        and basis.get("hook_0_3") in {"transcript", "browser"}
        and basis.get("first_frame_observation") in {"contact_sheet", "browser"}
        and basis.get("beat_breakdown") in {"transcript", "contact_sheet", "browser"}
    )


def validate_packet(
    packet: Mapping[str, Any],
    *,
    now: datetime | None = None,
    previous_digests: set[str] | None = None,
    thresholds: GateThresholds | None = None,
) -> dict[str, Any]:
    limits = thresholds or GateThresholds()
    checked_at = now or datetime.now(timezone.utc)
    sources = [item for item in packet.get("sources", []) if isinstance(item, Mapping)]
    shorts = [item for item in sources if item.get("format_kind") == "short"]
    long_form = [item for item in sources if item.get("format_kind") == "authority_long_form"]
    research_date_text = _text(packet.get("research_date"))
    try:
        research_date = datetime.strptime(research_date_text, "%Y%m%d").date()
        valid_research_date = True
    except ValueError:
        research_date = checked_at.date()
        valid_research_date = False
    manifest = packet.get("manifest") if isinstance(packet.get("manifest"), Mapping) else {}
    collected_at = parse_datetime(manifest.get("collected_at"))
    digest = _text(manifest.get("research_digest")) or compute_research_digest(packet)
    platform_counts = Counter(_text(item.get("platform")) for item in shorts)
    browser_counts = Counter(
        _text(item.get("platform")) for item in shorts if item.get("access_state") == "browser_observed"
    )
    first_seen_today = sum(
        1 for item in shorts if (parse_datetime(item.get("first_seen_at")) or datetime.min.replace(tzinfo=timezone.utc)).date() == research_date
    )
    recent_90d = 0
    evergreen = 0
    for item in shorts:
        published = parse_datetime(item.get("published_at"))
        if not published:
            continue
        age_days = (datetime.combine(research_date, time.max, tzinfo=timezone.utc) - published).total_seconds() / 86400
        recent_90d += int(age_days <= 90)
        evergreen += int(age_days > 365)
    novelty_rate = nullable_number(manifest.get("novelty_rate"))
    top = shorts[: limits.min_top_sources_with_full_evidence]
    angles = [item for item in packet.get("ranked_angles", []) if isinstance(item, Mapping)]
    top_angles = angles[: limits.required_angle_count]
    creator_counts = Counter(
        _text(item.get("creator_id") or item.get("creator_name") or item.get("source_id")).lower() for item in sources
    )
    checks = {
        "research_date_format": (valid_research_date, research_date_text, "YYYYMMDD"),
        "short_source_count": (len(shorts) >= limits.min_short_sources, len(shorts), limits.min_short_sources),
        "first_seen_today": (first_seen_today >= limits.min_first_seen_today, first_seen_today, limits.min_first_seen_today),
        "recent_within_90_days": (recent_90d >= limits.min_recent_90d, recent_90d, limits.min_recent_90d),
        "evergreen_cap": (evergreen <= limits.max_evergreen_over_year, evergreen, limits.max_evergreen_over_year),
        "creator_cap": (max(creator_counts.values(), default=0) <= limits.creator_cap, max(creator_counts.values(), default=0), limits.creator_cap),
        "youtube_coverage": (platform_counts["youtube"] >= limits.min_youtube, platform_counts["youtube"], limits.min_youtube),
        "tiktok_browser_observed": (browser_counts["tiktok"] >= limits.min_browser_tiktok, browser_counts["tiktok"], limits.min_browser_tiktok),
        "instagram_browser_observed": (browser_counts["instagram"] >= limits.min_browser_instagram, browser_counts["instagram"], limits.min_browser_instagram),
        "valid_youtube_transcripts": (sum(_valid_transcript(item) for item in shorts) >= limits.min_valid_youtube_transcripts, sum(_valid_transcript(item) for item in shorts), limits.min_valid_youtube_transcripts),
        "reviewed_youtube_contact_sheets": (sum(_reviewed_contact_sheet(item) for item in shorts) >= limits.min_reviewed_youtube_contact_sheets, sum(_reviewed_contact_sheet(item) for item in shorts), limits.min_reviewed_youtube_contact_sheets),
        "top_source_evidence": (len(top) >= limits.min_top_sources_with_full_evidence and all(_full_top_evidence(item) for item in top), sum(_full_top_evidence(item) for item in top), limits.min_top_sources_with_full_evidence),
        "novelty_rate": (novelty_rate is not None and float(novelty_rate) >= limits.min_novelty_rate, novelty_rate, limits.min_novelty_rate),
        "packet_freshness": (collected_at is not None and 0 <= (checked_at - collected_at).total_seconds() / 3600 <= limits.max_packet_age_hours, round((checked_at - collected_at).total_seconds() / 3600, 3) if collected_at else None, limits.max_packet_age_hours),
        "not_copied": (not previous_digests or digest not in previous_digests, digest, "new digest"),
        "long_form_cap": (len(long_form) <= limits.max_long_form_authority, len(long_form), limits.max_long_form_authority),
        "angle_count": (len(top_angles) >= limits.required_angle_count, len(top_angles), limits.required_angle_count),
        "angle_support": (
            len(top_angles) >= limits.required_angle_count
            and all(
                len(item.get("supporting_source_ids") or []) >= limits.min_angle_sources
                and len(item.get("platforms") or []) >= limits.min_angle_platforms
                and item.get("primary_has_visual_evidence")
                for item in top_angles
            ),
            sum(
                len(item.get("supporting_source_ids") or []) >= limits.min_angle_sources
                and len(item.get("platforms") or []) >= limits.min_angle_platforms
                and bool(item.get("primary_has_visual_evidence"))
                for item in top_angles
            ),
            limits.required_angle_count,
        ),
    }
    serialized_checks = {
        name: {"passed": bool(value[0]), "actual": value[1], "required": value[2]} for name, value in checks.items()
    }
    failures = [name for name, value in serialized_checks.items() if not value["passed"]]
    return {
        "gate": "daily_research",
        "passed": not failures,
        "checked_at": checked_at.isoformat(),
        "research_digest": digest,
        "thresholds": asdict(limits),
        "checks": serialized_checks,
        "failures": failures,
    }


def _previous_context(previous_packets: Sequence[Mapping[str, Any]]) -> tuple[set[str], set[str]]:
    digests: set[str] = set()
    fingerprints: set[str] = set()
    for packet in previous_packets:
        manifest = packet.get("manifest") if isinstance(packet.get("manifest"), Mapping) else {}
        digest = _text(manifest.get("research_digest"))
        if digest:
            digests.add(digest)
        for source in packet.get("sources", []):
            if isinstance(source, Mapping) and source.get("content_fingerprint"):
                fingerprints.add(_text(source.get("content_fingerprint")))
    return digests, fingerprints


def build_daily_packet(
    records: Sequence[Mapping[str, Any]],
    *,
    research_date: date | None = None,
    collected_at: datetime | None = None,
    queries: Sequence[str] = (),
    previous_packets: Sequence[Mapping[str, Any]] = (),
    thresholds: GateThresholds | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    collected = collected_at or datetime.now(timezone.utc)
    if collected.tzinfo is None:
        collected = collected.replace(tzinfo=timezone.utc)
    collected = collected.astimezone(timezone.utc)
    research_day = research_date or collected.date()
    previous_digests, previous_fingerprints = _previous_context(previous_packets)
    normalized = [
        normalize_source(
            record,
            collected_at=collected,
            research_date=research_day,
            previous_fingerprints=previous_fingerprints,
        )
        for record in records
        if isinstance(record, Mapping)
    ]
    unique = deduplicate_sources(normalized)
    unique = sorted(
        (score_source(item, previous_fingerprints) for item in unique),
        key=lambda item: (-float(item.get("score") or 0), _text(item.get("source_id"))),
    )
    kept, dropped = apply_creator_cap(unique, (thresholds or GateThresholds()).creator_cap)
    angles = derive_ranked_angles(kept)
    novelty_rate = (
        sum(item.get("content_fingerprint") not in previous_fingerprints for item in kept) / len(kept)
        if kept and previous_packets
        else (1.0 if kept else 0.0)
    )
    packet: dict[str, Any] = {
        "schema_version": 1,
        "research_date": research_day.strftime("%Y%m%d"),
        "manifest": {
            "research_run_id": f"research-{research_day.strftime('%Y%m%d')}",
            "collected_at": collected.isoformat(),
            "queries": sorted({_text(query) for query in queries if _text(query)}),
            "input_count": len(records),
            "deduplicated_count": len(unique),
            "source_count": len(kept),
            "creator_cap_dropped_source_ids": [_text(item.get("source_id")) for item in dropped],
            "previous_packet_digests": sorted(previous_digests),
            "novelty_rate": round(novelty_rate, 6),
            "tool_versions": {"python": sys.version.split()[0], "collector": "daily_research_v1"},
        },
        "sources": kept,
        "ranked_angles": angles,
    }
    digest = compute_research_digest(packet)
    packet["manifest"]["research_digest"] = digest
    top_angle = angles[0] if angles else {}
    script_brief = {
        "research_run_id": packet["manifest"]["research_run_id"],
        "research_digest": digest,
        "angle_id": top_angle.get("angle_id"),
        "supporting_source_ids": (top_angle.get("supporting_source_ids") or [])[:5],
        "primary_mechanic_source_id": top_angle.get("primary_mechanic_source_id"),
        "hook_pattern": top_angle.get("hook_pattern"),
        "first_frame_plan": top_angle.get("first_frame_plan"),
        "beat_pattern": top_angle.get("beat_pattern") or [],
        "copy": top_angle.get("copy") or [],
        "avoid": top_angle.get("avoid") or [],
    }
    gate = validate_packet(packet, now=collected, previous_digests=previous_digests, thresholds=thresholds)
    return packet, gate, script_brief


def write_daily_artifacts(
    packet: Mapping[str, Any],
    gate: Mapping[str, Any],
    script_brief: Mapping[str, Any],
    *,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Path]:
    folder = output_root / _text(packet.get("research_date"))
    folder.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "daily_research": folder / "daily_research.json",
        "quality_gate": folder / "quality_gate.json",
        "ranked_angles": folder / "ranked_angles.json",
        "script_brief": folder / "script_brief.json",
    }
    payloads = {
        "daily_research": packet,
        "quality_gate": gate,
        "ranked_angles": {
            "research_run_id": (packet.get("manifest") or {}).get("research_run_id"),
            "research_digest": (packet.get("manifest") or {}).get("research_digest"),
            "angles": packet.get("ranked_angles") or [],
        },
        "script_brief": script_brief,
    }
    for name, path in artifacts.items():
        path.write_text(json.dumps(payloads[name], indent=2, ensure_ascii=False), encoding="utf-8")
    return artifacts


def discover_youtube(
    query: str,
    *,
    limit: int = 10,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    timeout_sec: int = 90,
) -> list[dict[str, Any]]:
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--dump-json",
        "--skip-download",
        "--no-warnings",
        "--playlist-end",
        str(max(1, limit)),
        f"ytsearch{max(1, limit)}:{query}",
    ]
    completed = runner(command, capture_output=True, text=True, timeout=timeout_sec, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "yt-dlp search failed").strip().splitlines()[-1]
        raise RuntimeError(detail[:500])
    records: list[dict[str, Any]] = []
    for rank, line in enumerate(completed.stdout.splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        records.append(
            {
                **raw,
                "platform": "youtube",
                "query": query,
                "discovery_surface": "yt-dlp-search",
                "result_rank": rank,
                "canonical_url": raw.get("webpage_url")
                or raw.get("original_url")
                or (f"https://www.youtube.com/watch?v={raw.get('id')}" if raw.get("id") else raw.get("url")),
            }
        )
    return records


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_packets(paths: Sequence[Path]) -> list[Mapping[str, Any]]:
    packets: list[Mapping[str, Any]] = []
    for path in paths:
        value = _read_json(path)
        if isinstance(value, Mapping):
            packets.append(value)
    return packets


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a trustworthy daily Signal research packet.")
    parser.add_argument("--input", type=Path, help="JSON list or object containing a sources list.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--date", help="Research date as YYYYMMDD; defaults to collection date.")
    parser.add_argument("--collected-at", help="ISO-8601 collection timestamp; defaults to now.")
    parser.add_argument("--previous-packet", action="append", type=Path, default=[])
    parser.add_argument("--youtube-query", action="append", default=[])
    parser.add_argument("--youtube-limit", type=int, default=10)
    parser.add_argument("--youtube-fixture", type=Path, help="Offline JSON map from query to source lists.")
    parser.add_argument("--allow-failed-gate", action="store_true", help="Write artifacts and return zero even when the gate fails.")
    args = parser.parse_args(argv)

    if not args.input and not args.youtube_query:
        raise SystemExit("Provide --input, at least one --youtube-query, or both.")
    payload = _read_json(args.input) if args.input else []
    records = payload.get("sources", []) if isinstance(payload, Mapping) else payload
    if not isinstance(records, list):
        raise SystemExit("Input must be a JSON list or an object with a sources list.")
    queries = list(args.youtube_query)
    if isinstance(payload, Mapping):
        queries.extend(_string_list(payload.get("queries")))
    if args.youtube_fixture:
        fixtures = _read_json(args.youtube_fixture)
        if not isinstance(fixtures, Mapping):
            raise SystemExit("YouTube fixture must map each query to a list of source records.")
        for query in args.youtube_query:
            discovered = fixtures.get(query, [])
            if not isinstance(discovered, list):
                raise SystemExit(f"YouTube fixture value for {query!r} must be a list.")
            records.extend(discovered)
    else:
        for query in args.youtube_query:
            records.extend(discover_youtube(query, limit=args.youtube_limit))

    collected = parse_datetime(args.collected_at) or datetime.now(timezone.utc)
    research_day = datetime.strptime(args.date, "%Y%m%d").date() if args.date else collected.date()
    packet, gate, brief = build_daily_packet(
        records,
        research_date=research_day,
        collected_at=collected,
        queries=queries,
        previous_packets=_load_packets(args.previous_packet),
    )
    paths = write_daily_artifacts(packet, gate, brief, output_root=args.output_root)
    print(
        json.dumps(
            {
                "passed": gate["passed"],
                "researchDigest": packet["manifest"]["research_digest"],
                "failures": gate["failures"],
                "artifacts": {name: str(path) for name, path in paths.items()},
            },
            indent=2,
        )
    )
    return 0 if gate["passed"] or args.allow_failed_gate else 2


if __name__ == "__main__":
    raise SystemExit(main())
