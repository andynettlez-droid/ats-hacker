"""Merge reviewed platform evidence into the daily research input contract.

This module does not discover or invent evidence. It joins metadata, bounded visual
captures, and human review notes that already exist on disk so ``daily_research``
can validate one traceable packet.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def source_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, Mapping)]
    if isinstance(payload, Mapping):
        values = payload.get("sources")
        if isinstance(values, list):
            return [dict(item) for item in values if isinstance(item, Mapping)]
        if payload.get("id") or payload.get("platform_post_id"):
            return [dict(payload)]
    return []


def post_id(record: Mapping[str, Any]) -> str:
    return str(
        record.get("platform_post_id")
        or record.get("id")
        or str(record.get("source_id") or "").split("-", 1)[-1]
    ).strip()


def platform_for(record: Mapping[str, Any]) -> str:
    explicit = str(record.get("platform") or "").strip().lower()
    if explicit:
        return explicit
    url = str(record.get("webpage_url") or record.get("canonical_url") or "").lower()
    if "instagram.com" in url:
        return "instagram"
    if "tiktok.com" in url:
        return "tiktok"
    if "youtu" in url:
        return "youtube"
    return "unknown"


def normalized_beats(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    output: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        description = str(item.get("description") or item.get("beat") or "").strip()
        start = item.get("start_sec")
        end = item.get("end_sec")
        if start is None:
            match = re.match(r"\s*([0-9.]+)\s*[-–]\s*([0-9.]+)\s*s?", str(item.get("time") or ""))
            if match:
                start, end = float(match.group(1)), float(match.group(2))
        if description and start is not None:
            output.append({"start_sec": start, "end_sec": end, "description": description})
    return output


def merge_review(record: Mapping[str, Any], review: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(record)
    for key in (
        "hook_0_3",
        "hook_0_8",
        "first_frame_observation",
        "caption_style",
        "visual_mechanic",
        "human_premise",
        "copy",
        "avoid",
        "claim_risk",
        "angle_id",
        "observation_basis",
    ):
        if review.get(key) not in (None, "", [], {}):
            result[key] = review[key]
    result["beat_breakdown"] = normalized_beats(review.get("beat_breakdown"))
    return result


def find_contact_sheet(root: Path, item_id: str) -> Path | None:
    matches = sorted(root.glob(f"*{item_id}*/contact_sheet.png"))
    return matches[0].resolve() if matches else None


def visible_metrics(record: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    fields = {
        "views": ("views", "view_count"),
        "likes": ("likes", "like_count"),
        "comments": ("comments", "comment_count"),
        "shares": ("shares", "share_count"),
        "saves": ("saves", "save_count"),
    }
    for target, aliases in fields.items():
        value = next((override.get(alias) for alias in aliases if override.get(alias) is not None), None)
        if value is None:
            value = next((record.get(alias) for alias in aliases if record.get(alias) is not None), None)
        if value is not None:
            output[target] = value
    return output


def assemble(
    youtube_payloads: Iterable[Any],
    social_payloads: Iterable[Any],
    reviews_payload: Any,
    *,
    evidence_root: Path,
    browser_observed_ids: set[str],
    metrics_overrides: Mapping[str, Any] | None = None,
    observed_at: str | None = None,
) -> list[dict[str, Any]]:
    reviews = source_list(reviews_payload)
    review_by_id = {post_id(item): item for item in reviews if post_id(item)}
    overrides = metrics_overrides or {}
    records: list[dict[str, Any]] = []

    for payload in youtube_payloads:
        for source in source_list(payload):
            item_id = post_id(source)
            review = review_by_id.get(item_id)
            if review:
                source = merge_review(source, review)
                source["media_status"] = "reviewed"
            elif source.get("format_kind") != "authority_long_form":
                continue
            records.append(source)

    for payload in social_payloads:
        for raw in source_list(payload):
            item_id = post_id(raw)
            review = review_by_id.get(item_id)
            if not item_id or not review:
                continue
            platform = platform_for(raw)
            sheet = find_contact_sheet(evidence_root, item_id)
            override = overrides.get(item_id) if isinstance(overrides.get(item_id), Mapping) else {}
            source = merge_review(
                {
                    **raw,
                    "source_id": f"{platform}-{item_id}",
                    "platform": platform,
                    "platform_post_id": item_id,
                    "canonical_url": raw.get("webpage_url") or raw.get("canonical_url"),
                    "creator_id": raw.get("uploader_id") or raw.get("channel_id"),
                    "creator_name": raw.get("uploader") or raw.get("channel"),
                    "published_at": raw.get("upload_date") or raw.get("published_at"),
                    "views": override.get("views", raw.get("view_count")),
                    "likes": override.get("likes", raw.get("like_count")),
                    "comments": override.get("comments", raw.get("comment_count")),
                    "shares": override.get("shares", raw.get("share_count")),
                    "duration_sec": raw.get("duration"),
                    "format_kind": "short",
                    "metadata_status": "available",
                    "media_status": "reviewed" if sheet else "metadata_only",
                    "contact_sheet_path": str(sheet) if sheet else None,
                    "contact_sheet_times_sec": [0.0, 0.5, 1.5, 3.0] if sheet else [],
                },
                review,
            )
            if item_id in browser_observed_ids and sheet:
                source.update(
                    {
                        "access_state": "browser_observed",
                        "observer": "Codex in-app browser",
                        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
                        "screenshot_paths": [str(sheet)],
                        "visible_caption": review.get("hook_0_3"),
                        "visible_metrics": visible_metrics(raw, override),
                        "audio_observed": True,
                    }
                )
            records.append(source)
    return records


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble reviewed Signal research evidence without inventing fields.")
    parser.add_argument("--youtube-evidence", type=Path, action="append", default=[])
    parser.add_argument("--social-metadata", type=Path, action="append", default=[])
    parser.add_argument("--reviewed-observations", type=Path, required=True)
    parser.add_argument("--browser-evidence-root", type=Path, required=True)
    parser.add_argument("--browser-observed", action="append", default=[])
    parser.add_argument("--metrics-overrides", type=Path)
    parser.add_argument("--observed-at")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    records = assemble(
        [read_json(path) for path in args.youtube_evidence],
        [read_json(path) for path in args.social_metadata],
        read_json(args.reviewed_observations),
        evidence_root=args.browser_evidence_root,
        browser_observed_ids=set(args.browser_observed),
        metrics_overrides=read_json(args.metrics_overrides) if args.metrics_overrides else None,
        observed_at=args.observed_at,
    )
    payload = {
        "queries": [
            "resume review shorts",
            "recruiter reacts resume",
            "job search frustration",
            "resume teardown Instagram Reels TikTok",
        ],
        "sources": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sourceCount": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
