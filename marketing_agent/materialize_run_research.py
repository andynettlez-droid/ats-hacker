"""Create human-readable creative research artifacts from a passing packet."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


COLUMNS = (
    "source_id",
    "platform",
    "creator",
    "url",
    "published_at",
    "views",
    "duration_sec",
    "topic",
    "hook_text",
    "first_visual_frame",
    "beat_by_beat_breakdown",
    "narration_style",
    "caption_style",
    "visual_style",
    "why_it_works",
    "what_signal_should_copy",
    "what_signal_should_avoid",
    "evidence_strength",
    "transcript_status",
    "contact_sheet_path",
    "angle_id",
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Research packet must be a JSON object.")
    return payload


def evidence_strength(source: Mapping[str, Any]) -> str:
    if source.get("access_state") == "browser_observed":
        return "browser_observed_social"
    if source.get("platform") == "youtube" and source.get("transcript_status") == "valid":
        return "verified_youtube_metadata"
    if source.get("contact_sheet_path"):
        return "bounded_visual_review"
    return "metadata_only"


def beat_text(source: Mapping[str, Any]) -> str:
    beats: list[str] = []
    for beat in source.get("beat_breakdown") or []:
        if not isinstance(beat, Mapping):
            continue
        start = beat.get("start_sec")
        end = beat.get("end_sec")
        description = str(beat.get("description") or "").strip()
        if description:
            beats.append(f"{start:g}-{end:g}s {description}" if end is not None else f"{start:g}s {description}")
    return " | ".join(beats)


def source_row(source: Mapping[str, Any]) -> dict[str, Any]:
    first_frame = str(source.get("first_frame_observation") or "")
    mechanic = str(source.get("visual_mechanic") or "")
    return {
        "source_id": source.get("source_id"),
        "platform": source.get("platform"),
        "creator": source.get("creator_name"),
        "url": source.get("canonical_url"),
        "published_at": source.get("published_at"),
        "views": source.get("views"),
        "duration_sec": source.get("duration_sec"),
        "topic": source.get("human_premise"),
        "hook_text": source.get("hook_0_3"),
        "first_visual_frame": first_frame,
        "beat_by_beat_breakdown": beat_text(source),
        "narration_style": source.get("hook_0_8"),
        "caption_style": source.get("caption_style"),
        "visual_style": mechanic,
        "why_it_works": f"The first frame makes the premise legible and the format uses {mechanic.lower() or 'one visible mechanic'}.",
        "what_signal_should_copy": source.get("copy"),
        "what_signal_should_avoid": source.get("avoid"),
        "evidence_strength": evidence_strength(source),
        "transcript_status": source.get("transcript_status"),
        "contact_sheet_path": source.get("contact_sheet_path"),
        "angle_id": source.get("angle_id"),
    }


def write_artifacts(packet: Mapping[str, Any], run_dir: Path) -> dict[str, Path]:
    manifest = packet.get("manifest") if isinstance(packet.get("manifest"), Mapping) else {}
    sources = [source for source in packet.get("sources") or [] if isinstance(source, Mapping)]
    shorts = [source for source in sources if source.get("format_kind") == "short"]
    angles = [angle for angle in packet.get("ranked_angles") or [] if isinstance(angle, Mapping)]
    run_dir.mkdir(parents=True, exist_ok=True)

    matrix = run_dir / "exemplar_matrix.csv"
    with matrix.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(source_row(source) for source in shorts)

    enriched = run_dir / "exemplar_matrix_enriched.csv"
    with enriched.open("w", encoding="utf-8", newline="") as handle:
        fields = (*COLUMNS, "score", "claim_risk", "observation_basis")
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for source in shorts:
            writer.writerow(
                {
                    **source_row(source),
                    "score": source.get("score"),
                    "claim_risk": source.get("claim_risk"),
                    "observation_basis": json.dumps(source.get("observation_basis") or {}, sort_keys=True),
                }
            )

    angle_lines: list[str] = []
    for index, angle in enumerate(angles, start=1):
        angle_lines.extend(
            [
                f"## {index}. {str(angle.get('angle_id') or '').replace('-', ' ').title()}",
                "",
                f"Platforms: {', '.join(angle.get('platforms') or [])}",
                f"Evidence: {len(angle.get('supporting_source_ids') or [])} reviewed shorts",
                f"Hook pattern: {angle.get('hook_pattern') or 'n/a'}",
                f"First frame: {angle.get('first_frame_plan') or 'n/a'}",
                "",
                "Copy:",
                *[f"- {item}" for item in angle.get("copy") or []],
                "",
                "Avoid:",
                *[f"- {item}" for item in angle.get("avoid") or []],
                "",
            ]
        )

    swipe = run_dir / "viral_resume_swipe_file.md"
    swipe.write_text(
        "\n".join(
            [
                "# Viral Resume Swipe File",
                "",
                f"Research date: {packet.get('research_date')}",
                f"Research digest: `{manifest.get('research_digest')}`",
                f"Reviewed short sources: {len(shorts)}",
                "",
                "## Creative Conclusion",
                "",
                "The strongest trustworthy lane is a human resume teardown: show the real document immediately, make one plain-spoken judgment, reveal proof already on the page, and perform one visible rewrite. Open-loop AI-hack clips can attract views, but their guaranteed-outcome language and comment-gated resources create the exact distrust Signal must avoid.",
                "",
                "## Production Rules Extracted From Evidence",
                "",
                "- Put the weak line or job-search pain in frame one.",
                "- Let the resume remain the visual subject; a presenter is optional context, not the payoff.",
                "- Use one believable professional mistake, not a cartoonishly bad resume.",
                "- Explain the missing tool, volume, or outcome before revealing the rewrite.",
                "- Keep captions subordinate to the document.",
                "- Reject guaranteed outcomes, unexplained scores, fake testimonials, and comment bait.",
                "",
                *angle_lines,
            ]
        ),
        encoding="utf-8",
    )

    research = run_dir / "research.md"
    research.write_text(
        "\n".join(
            [
                "# Research Record",
                "",
                f"Bound research run: `{manifest.get('research_run_id')}`",
                f"Bound digest: `{manifest.get('research_digest')}`",
                f"Sources after deduplication and creator cap: {manifest.get('source_count')}",
                "",
                "The CSV matrix preserves source URLs, hooks, visual observations, beat notes, copy guidance, avoid guidance, transcript status, and local evidence paths. The selected production direction must cite this digest and use the human-resume-teardown lane.",
            ]
        ),
        encoding="utf-8",
    )
    return {"swipe": swipe, "matrix": matrix, "enriched": enriched, "research": research}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize creative research files for one Signal run.")
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    paths = write_artifacts(read_json(args.packet), args.run_dir)
    print(json.dumps({name: str(path) for name, path in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
