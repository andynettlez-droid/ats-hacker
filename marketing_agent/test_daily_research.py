import json
import subprocess
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from marketing_agent.daily_research import (
    GateThresholds,
    apply_creator_cap,
    build_daily_packet,
    canonicalize_url,
    compute_research_digest,
    discover_youtube,
    normalize_source,
    validate_packet,
    write_daily_artifacts,
)


NOW = datetime(2026, 7, 9, 12, 0, tzinfo=timezone.utc)


def rich_source(index: int, platform: str = "youtube", angle: str = "resume-teardown") -> dict:
    if platform == "youtube":
        url = f"https://youtube.com/shorts/video{index}?si=tracking"
    elif platform == "tiktok":
        url = f"https://www.tiktok.com/@creator{index}/video/70{index}?utm_source=test"
    else:
        url = f"https://www.instagram.com/reel/reel{index}/?igsh=tracking"
    source = {
        "platform": platform,
        "url": url,
        "creator_id": f"creator-{platform}-{index}",
        "creator_name": f"Creator {platform} {index}",
        "title": f"Resume example {index}",
        "published_at": (NOW - timedelta(days=10 + index % 12)).isoformat(),
        "first_seen_at": NOW.isoformat(),
        "metrics_captured_at": NOW.isoformat(),
        "views": 100_000 + index * 1_000,
        "likes": 5_000 + index,
        "comments": 200 + index,
        "shares": 100 + index,
        "duration_sec": 35,
        "metadata_status": "available",
        "hook_0_3": f"This resume mistake costs interviews {index}",
        "hook_0_8": f"A recruiter fixes a believable resume mistake {index}",
        "first_frame_observation": "A professional resume fills the screen with one marked line.",
        "beat_breakdown": [
            {"start_sec": 0, "end_sec": 3, "description": "Show the resume mistake."},
            {"start_sec": 3, "end_sec": 12, "description": "Explain the missing proof."},
            {"start_sec": 12, "end_sec": 25, "description": "Rewrite the line visibly."},
        ],
        "caption_style": "small creator captions",
        "visual_mechanic": "controlled browser resume edit",
        "human_premise": "A recruiter fixes one realistic resume line.",
        "copy": "Use a specific line and explain why it fails.",
        "avoid": "Avoid random ATS scores and giant captions.",
        "angle_id": angle,
        "observation_basis": {
            "hook_0_3": "transcript" if platform == "youtube" else "browser",
            "first_frame_observation": "contact_sheet" if platform == "youtube" else "browser",
            "beat_breakdown": "transcript" if platform == "youtube" else "browser",
        },
    }
    if platform == "youtube":
        source.update(
            {
                "transcript_status": "valid",
                "transcript_kind": "creator_captions",
                "transcript_path": f"transcripts/video{index}.vtt",
                "transcript_sha256": f"sha-{index}",
                "transcript_coverage_sec": 34,
                "duplicate_token_ratio": 0.05,
                "media_status": "reviewed",
                "contact_sheet_path": f"contact_sheets/video{index}.png",
                "contact_sheet_times_sec": [0.5, 1.5, 3.0],
            }
        )
    else:
        source.update(
            {
                "access_state": "browser_observed",
                "observer": "researcher",
                "observed_at": NOW.isoformat(),
                "screenshot_paths": [f"screens/{platform}-{index}-0.png", f"screens/{platform}-{index}-3.png"],
                "visible_caption": "Resume review",
                "audio_observed": True,
            }
        )
    return source


def passing_sources() -> list[dict]:
    angles = ("screen-edit", "desk-roast", "recruiter-search")
    records = [rich_source(index, "youtube", angles[index % 3]) for index in range(16)]
    records.extend(
        [
            rich_source(100, "tiktok", "screen-edit"),
            rich_source(101, "tiktok", "recruiter-search"),
            rich_source(102, "instagram", "desk-roast"),
            rich_source(103, "instagram", "recruiter-search"),
        ]
    )
    return records


class DailyResearchTests(unittest.TestCase):
    def test_canonicalizes_platform_urls(self):
        self.assertEqual(
            canonicalize_url("https://youtu.be/abc123?si=secret&utm_source=x"),
            "https://www.youtube.com/watch?v=abc123",
        )
        self.assertEqual(
            canonicalize_url("https://www.instagram.com/reel/XYZ/?utm_medium=copy&igsh=abc"),
            "https://www.instagram.com/reel/XYZ",
        )
        self.assertEqual(
            canonicalize_url("https://www.tiktok.com/@person/video/123?is_from_webapp=1&utm_source=x"),
            "https://www.tiktok.com/@person/video/123?is_from_webapp=1",
        )

    def test_unknown_metrics_remain_null_and_weights_rebalance(self):
        source = normalize_source(
            {
                "platform": "youtube",
                "url": "https://youtube.com/shorts/unknown",
                "creator_id": "creator",
                "views": None,
                "likes": "",
                "published_at": None,
                "hook_0_3": "A real hook",
            },
            collected_at=NOW,
            research_date=NOW.date(),
        )
        self.assertIsNone(source["views"])
        self.assertIsNone(source["views_per_day"])
        self.assertIsNone(source["engagement_rate"])
        self.assertIsNone(source["score_components"]["freshness"])
        self.assertIsNone(source["score_components"]["views_per_day"])
        self.assertGreater(source["score"], 0)

    def test_browser_observation_requires_real_evidence_fields(self):
        source = normalize_source(
            {
                "platform": "tiktok",
                "url": "https://www.tiktok.com/@person/video/123",
                "access_state": "browser_observed",
                "observer": "researcher",
                # A timestamp and screenshots are intentionally absent.
            },
            collected_at=NOW,
            research_date=NOW.date(),
        )
        self.assertEqual(source["access_state"], "not_observed")
        self.assertIsNone(source["observer"])
        self.assertEqual(source["screenshot_paths"], [])

    def test_digest_is_stable_across_input_order_and_derived_novelty(self):
        records = passing_sources()
        packet_a, gate_a, _ = build_daily_packet(records, research_date=NOW.date(), collected_at=NOW)
        packet_b, gate_b, _ = build_daily_packet(list(reversed(records)), research_date=NOW.date(), collected_at=NOW)
        self.assertTrue(gate_a["passed"], gate_a["failures"])
        self.assertTrue(gate_b["passed"], gate_b["failures"])
        self.assertEqual(compute_research_digest(packet_a), compute_research_digest(packet_b))
        self.assertEqual(packet_a["manifest"]["research_digest"], packet_b["manifest"]["research_digest"])

    def test_creator_cap_keeps_only_two_sources(self):
        records = []
        for index in range(4):
            source = rich_source(index)
            source["creator_id"] = "same-creator"
            normalized = normalize_source(source, collected_at=NOW, research_date=NOW.date())
            records.append(normalized)
        kept, dropped = apply_creator_cap(records, cap=2)
        self.assertEqual(len(kept), 2)
        self.assertEqual(len(dropped), 2)

    def test_copied_and_stale_packets_fail_the_gate(self):
        packet, gate, _ = build_daily_packet(passing_sources(), research_date=NOW.date(), collected_at=NOW)
        self.assertTrue(gate["passed"], gate["failures"])
        copied = validate_packet(
            packet,
            now=NOW,
            previous_digests={packet["manifest"]["research_digest"]},
        )
        self.assertFalse(copied["passed"])
        self.assertIn("not_copied", copied["failures"])
        stale = validate_packet(packet, now=NOW + timedelta(hours=25))
        self.assertFalse(stale["passed"])
        self.assertIn("packet_freshness", stale["failures"])

    def test_reused_sources_fail_novelty_even_when_date_changes(self):
        first, _, _ = build_daily_packet(passing_sources(), research_date=NOW.date(), collected_at=NOW)
        later = NOW + timedelta(days=1)
        copied, gate, _ = build_daily_packet(
            passing_sources(),
            research_date=later.date(),
            collected_at=later,
            previous_packets=[first],
        )
        self.assertEqual(copied["manifest"]["novelty_rate"], 0.0)
        self.assertFalse(gate["passed"])
        self.assertIn("novelty_rate", gate["failures"])

    def test_metadata_only_packet_fails_hard_evidence_gates(self):
        records = [
            {
                "platform": "youtube",
                "url": f"https://youtube.com/shorts/thin{index}",
                "creator_id": f"creator-{index}",
                "published_at": NOW.isoformat(),
                "views": 10_000,
            }
            for index in range(20)
        ]
        _, gate, _ = build_daily_packet(records, research_date=NOW.date(), collected_at=NOW)
        self.assertFalse(gate["passed"])
        self.assertIn("valid_youtube_transcripts", gate["failures"])
        self.assertIn("reviewed_youtube_contact_sheets", gate["failures"])
        self.assertIn("top_source_evidence", gate["failures"])
        self.assertIn("tiktok_browser_observed", gate["failures"])
        self.assertIn("instagram_browser_observed", gate["failures"])

    def test_deduplicates_urls_and_writes_all_artifacts(self):
        records = passing_sources()
        duplicate = dict(records[0])
        duplicate["url"] = "https://youtu.be/video0?si=another-tracker"
        records.append(duplicate)
        packet, gate, brief = build_daily_packet(records, research_date=NOW.date(), collected_at=NOW)
        self.assertEqual(packet["manifest"]["input_count"], 21)
        self.assertEqual(packet["manifest"]["deduplicated_count"], 20)
        self.assertTrue(gate["passed"], gate["failures"])
        with tempfile.TemporaryDirectory() as folder:
            paths = write_daily_artifacts(packet, gate, brief, output_root=Path(folder))
            self.assertEqual(set(paths), {"daily_research", "quality_gate", "ranked_angles", "script_brief"})
            for path in paths.values():
                self.assertTrue(path.exists())
                json.loads(path.read_text(encoding="utf-8"))

    def test_ytdlp_adapter_is_fixture_friendly(self):
        payload = {
            "id": "abc",
            "channel_id": "channel",
            "view_count": None,
        }

        def runner(command, **kwargs):
            self.assertIn("ytsearch2:resume teardown", command)
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload) + "\n", stderr="")

        records = discover_youtube("resume teardown", limit=2, runner=runner)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["platform"], "youtube")
        self.assertEqual(records[0]["query"], "resume teardown")
        self.assertEqual(records[0]["result_rank"], 1)
        self.assertEqual(records[0]["canonical_url"], "https://www.youtube.com/watch?v=abc")

    def test_malformed_research_date_fails_instead_of_crashing(self):
        packet, _, _ = build_daily_packet(passing_sources(), research_date=NOW.date(), collected_at=NOW)
        packet["research_date"] = "July ninth"
        gate = validate_packet(packet, now=NOW)
        self.assertFalse(gate["passed"])
        self.assertIn("research_date_format", gate["failures"])

    def test_thresholds_can_only_be_changed_explicitly(self):
        packet, _, _ = build_daily_packet([], research_date=NOW.date(), collected_at=NOW)
        gate = validate_packet(
            packet,
            now=NOW,
            thresholds=GateThresholds(
                min_short_sources=0,
                min_first_seen_today=0,
                min_recent_90d=0,
                min_youtube=0,
                min_browser_tiktok=0,
                min_browser_instagram=0,
                min_valid_youtube_transcripts=0,
                min_reviewed_youtube_contact_sheets=0,
                min_top_sources_with_full_evidence=0,
                min_novelty_rate=0,
                required_angle_count=0,
            ),
        )
        self.assertTrue(gate["passed"], gate["failures"])


if __name__ == "__main__":
    unittest.main()
