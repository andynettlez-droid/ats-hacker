"""Collect public social metrics for Signal posts without weakening post approval.

YouTube, Instagram, and TikTok URLs are read from marketing/autopost/posts.json.
yt-dlp is used as the public metadata adapter. A failed/private platform lookup is
recorded in the snapshot instead of being silently treated as zero engagement.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POSTS = ROOT / "marketing" / "autopost" / "posts.json"
DEFAULT_METRICS = ROOT / "marketing" / "content_metrics.json"
DEFAULT_SNAPSHOTS = ROOT / "marketing" / "metrics_snapshots"
MILESTONES = (2, 24, 72)


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def snapshot_window(age_hours: float) -> str:
    reached = [hours for hours in MILESTONES if age_hours >= hours]
    return f"{max(reached)}h" if reached else "early"


def metric_key(platform: str, file_name: str) -> str:
    return f"{platform}:{file_name}"


def published_results(post: dict[str, Any]) -> list[dict[str, Any]]:
    status = post.get("uploadStatus")
    if not isinstance(status, dict):
        return []
    results = status.get("results")
    if not isinstance(results, list):
        return []
    return [item for item in results if isinstance(item, dict) and item.get("success") and item.get("post_url")]


def collect_candidates(posts: list[dict[str, Any]], platform: str | None = None) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for post in posts:
        file_name = str(post.get("file") or "").strip()
        if not file_name:
            continue
        for result in published_results(post):
            result_platform = str(result.get("platform") or "").strip().lower()
            if platform and result_platform != platform:
                continue
            candidates.append(
                {
                    "title": str(post.get("title") or post.get("youtubeTitle") or "Untitled"),
                    "file": file_name,
                    "utmContent": _utm_content(post),
                    "platform": result_platform,
                    "platformPostId": str(result.get("platform_post_id") or ""),
                    "postUrl": str(result.get("post_url") or ""),
                    "publishedAt": post.get("postedAt") or post.get("updatedAt"),
                }
            )
    return candidates


def _utm_content(post: dict[str, Any]) -> str:
    landing = str(post.get("landingUrl") or post.get("youtubeDescription") or "")
    marker = "utm_content="
    if marker not in landing:
        return ""
    value = landing.split(marker, 1)[1]
    return value.split("&", 1)[0].split()[0].strip()


def fetch_with_ytdlp(url: str, timeout_sec: int = 45) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--dump-single-json",
        "--skip-download",
        "--no-warnings",
        "--socket-timeout",
        str(timeout_sec),
        url,
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_sec + 15, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "yt-dlp lookup failed").strip().splitlines()[-1]
        raise RuntimeError(detail[:500])
    return json.loads(completed.stdout)


def normalize_metric(candidate: dict[str, Any], raw: dict[str, Any], now: datetime) -> dict[str, Any]:
    published = iso_datetime(candidate.get("publishedAt"))
    age_hours = max(0.0, (now - published).total_seconds() / 3600) if published else 0.0
    views = _nullable_number(raw.get("view_count"))
    likes = _nullable_number(raw.get("like_count"))
    comments = _nullable_number(raw.get("comment_count"))
    share_value = raw.get("repost_count") if raw.get("repost_count") is not None else raw.get("share_count")
    shares = _nullable_number(share_value)
    known_engagement = [value for value in (likes, comments, shares) if value is not None]
    engagement = sum(known_engagement) / views if views and known_engagement else None
    return {
        **candidate,
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "duration": _nullable_number(raw.get("duration")),
        "engagementRate": round(engagement, 6) if engagement is not None else None,
        "capturedAt": now.isoformat(),
        "ageHours": round(age_hours, 2),
        "window": snapshot_window(age_hours),
        "source": "yt-dlp-public-metadata",
    }


def _nullable_number(value: Any) -> int | float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return None


def collect_metrics(
    candidates: list[dict[str, Any]],
    fetcher: Callable[[str], dict[str, Any]],
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    captured = now or datetime.now(timezone.utc)
    records: list[dict[str, Any]] = []
    for candidate in candidates:
        try:
            records.append(normalize_metric(candidate, fetcher(candidate["postUrl"]), captured))
        except Exception as error:  # platform/network failures belong in the audit snapshot
            records.append(
                {
                    **candidate,
                    "capturedAt": captured.isoformat(),
                    "source": "yt-dlp-public-metadata",
                    "error": str(error)[:500],
                }
            )
    return records


def merge_metrics(existing: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    merged = dict(existing)
    for record in records:
        if record.get("error"):
            continue
        key = metric_key(str(record["platform"]), str(record["file"]))
        previous = merged.get(key) if isinstance(merged.get(key), dict) else {}
        history = previous.get("history") if isinstance(previous.get("history"), list) else []
        history_entry = {
            field: record.get(field)
            for field in ("capturedAt", "window", "views", "likes", "comments", "shares", "engagementRate")
        }
        deduped = [item for item in history if not (isinstance(item, dict) and item.get("capturedAt") == record.get("capturedAt"))]
        deduped.append(history_entry)
        merged[key] = {**previous, **record, "history": deduped[-30:]}
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect public metrics for posted Signal videos.")
    parser.add_argument("--posts", type=Path, default=DEFAULT_POSTS)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOTS)
    parser.add_argument("--platform", choices=["youtube", "instagram", "tiktok"])
    parser.add_argument("--max-posts", type=int, default=30)
    parser.add_argument("--fixture-json", type=Path, help="URL-keyed metadata fixture for tests/offline runs.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    posts = read_json(args.posts, [])
    if not isinstance(posts, list):
        raise SystemExit(f"Posts file must contain a JSON list: {args.posts}")
    candidates = collect_candidates(posts, args.platform)[-max(1, args.max_posts) :]

    if args.fixture_json:
        fixture = read_json(args.fixture_json, {})
        if not isinstance(fixture, dict):
            raise SystemExit("Fixture JSON must map post URLs to metadata objects.")

        def fetcher(url: str) -> dict[str, Any]:
            value = fixture.get(url)
            if not isinstance(value, dict):
                raise RuntimeError("No fixture metadata for URL")
            return value
    else:
        fetcher = fetch_with_ytdlp

    records = collect_metrics(candidates, fetcher)
    success_count = sum(1 for item in records if not item.get("error"))
    payload = {
        "capturedAt": datetime.now(timezone.utc).isoformat(),
        "candidateCount": len(candidates),
        "successCount": success_count,
        "errorCount": len(records) - success_count,
        "records": records,
    }

    if not args.dry_run:
        args.snapshot_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snapshot_path = args.snapshot_dir / f"social_metrics_{stamp}.json"
        snapshot_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        existing = read_json(args.metrics, {})
        args.metrics.parent.mkdir(parents=True, exist_ok=True)
        args.metrics.write_text(json.dumps(merge_metrics(existing if isinstance(existing, dict) else {}, records), indent=2), encoding="utf-8")
        payload["snapshotPath"] = str(snapshot_path)
        payload["metricsPath"] = str(args.metrics)

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
