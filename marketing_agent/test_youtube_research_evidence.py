import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from marketing_agent.daily_research import normalize_source
from marketing_agent.youtube_research_evidence import (
    ANALYSIS_FIELDS,
    CaptionPayload,
    FixtureStore,
    apply_reviewed_observation,
    bound_sources,
    capture_visual_evidence,
    clean_rolling_captions,
    collect,
    collect_source_evidence,
    discover_query,
    download_bounded_preview,
    main,
    normalize_metadata,
    parse_vtt,
    sha256_file,
)


NOW = datetime(2026, 7, 9, 18, 0, tzinfo=timezone.utc)
ROLLING_VTT = """WEBVTT

00:00:00.000 --> 00:00:01.000
This resume

00:00:00.500 --> 00:00:02.000
This resume looks fine

00:00:01.500 --> 00:00:03.000
resume looks fine but

00:00:02.500 --> 00:00:09.500
looks fine but it hides the proof
"""


def metadata(video_id: str, creator: str = "creator-1", **overrides):
    value = {
        "id": video_id,
        "webpage_url": f"https://youtube.com/shorts/{video_id}?si=tracking",
        "title": f"Resume teardown {video_id}",
        "channel_id": creator,
        "channel": f"Creator {creator}",
        "upload_date": "20260701",
        "duration": 24,
        "view_count": 100_000,
        "like_count": 5_000,
        "comment_count": 200,
        "subtitles": {"en": [{"ext": "vtt", "url": "https://captions.invalid"}]},
    }
    value.update(overrides)
    return value


class YouTubeResearchEvidenceTests(unittest.TestCase):
    def test_rolling_caption_overlap_is_removed_and_measured(self):
        raw = parse_vtt(ROLLING_VTT)
        cleaned, metrics = clean_rolling_captions(raw)
        self.assertEqual(
            " ".join(cue.text for cue in cleaned),
            "This resume looks fine but it hides the proof",
        )
        self.assertEqual(metrics["raw_token_count"], 17)
        self.assertEqual(metrics["clean_token_count"], 9)
        self.assertEqual(metrics["removed_overlap_token_count"], 8)
        self.assertEqual(metrics["duplicate_token_ratio"], 0.0)
        self.assertEqual(metrics["transcript_coverage_sec"], 9.5)

    def test_unknown_metrics_remain_nullable(self):
        record = normalize_metadata(
            metadata(
                "nullable",
                view_count=None,
                like_count="",
                comment_count="not-a-number",
                share_count=None,
                duration=None,
            ),
            query=None,
            result_rank=None,
            collected_at=NOW,
        )
        self.assertIsNone(record["views"])
        self.assertIsNone(record["likes"])
        self.assertIsNone(record["comments"])
        self.assertIsNone(record["shares"])
        self.assertIsNone(record["duration_sec"])

    def test_collector_never_invents_analysis(self):
        with tempfile.TemporaryDirectory() as folder:
            source = collect_source_evidence(
                metadata("no-analysis"),
                output_root=Path(folder),
                query="resume review",
                result_rank=1,
                collected_at=NOW,
                caption_payload=CaptionPayload("creator_captions", "en", ROLLING_VTT, "offline-fixture"),
                metadata_basis="offline-fixture",
            )
            for field in ANALYSIS_FIELDS:
                self.assertIn(source.get(field), (None, [], {}), field)
            self.assertEqual(source["observation_basis"], {})
            self.assertEqual(source["media_status"], "not_requested")
            self.assertEqual(source["evidence_provenance"]["metadata"]["basis"], "offline-fixture")
            self.assertEqual(source["evidence_provenance"]["transcript"]["basis"], "offline-fixture")
            self.assertEqual(source["transcript_status"], "valid")
            self.assertEqual(source["duplicate_token_ratio"], 0.0)
            self.assertEqual(sha256_file(Path(source["transcript_path"])), source["transcript_sha256"])

            compatible = normalize_source(
                source,
                collected_at=NOW,
                research_date=date(2026, 7, 9),
            )
            self.assertEqual(compatible["source_id"], "youtube-no-analysis")
            self.assertEqual(compatible["transcript_status"], "valid")
            self.assertIsNone(compatible["hook_0_3"])

    def test_only_supplied_reviewed_observations_populate_analysis(self):
        base = normalize_metadata(metadata("reviewed"), query=None, result_rank=None, collected_at=NOW)
        observation = {
            "hook_0_3": "This line hides the actual work.",
            "first_frame_observation": "The weak line is already boxed in red.",
            "beat_breakdown": [{"start_sec": 0, "end_sec": 3, "description": "Show the line."}],
            "copy": "Open on the exact resume mistake.",
            "observation_basis": {
                "hook_0_3": "transcript",
                "first_frame_observation": "contact_sheet",
                "beat_breakdown": "contact_sheet",
            },
            "reviewer": "human-reviewer",
            "reviewed_at": NOW.isoformat(),
        }
        reviewed = apply_reviewed_observation(base, observation)
        self.assertEqual(reviewed["hook_0_3"], observation["hook_0_3"])
        self.assertEqual(reviewed["first_frame_observation"], observation["first_frame_observation"])
        self.assertEqual(reviewed["observation_basis"], observation["observation_basis"])
        self.assertIsNone(reviewed["visual_mechanic"])
        self.assertEqual(
            reviewed["evidence_provenance"]["reviewed_observation"]["basis"],
            "supplied-reviewed-observations-json",
        )

    def test_source_and_creator_output_are_hard_bounded(self):
        candidates = []
        for index in range(5):
            candidates.append(
                normalize_metadata(
                    metadata(f"same-{index}", creator="same-creator"),
                    query="resume",
                    result_rank=index + 1,
                    collected_at=NOW,
                )
            )
        candidates.extend(
            [
                normalize_metadata(metadata("other-1", creator="other-a"), query=None, result_rank=None, collected_at=NOW),
                normalize_metadata(metadata("other-2", creator="other-b"), query=None, result_rank=None, collected_at=NOW),
                dict(candidates[0]),
            ]
        )
        kept, dropped = bound_sources(candidates, max_sources=3, creator_cap=2)
        self.assertEqual(len(kept), 3)
        self.assertEqual(sum(item["creator_id"] == "same-creator" for item in kept), 2)
        self.assertTrue(any(item["reason"] == "creator_cap" for item in dropped))
        self.assertTrue(any(item["reason"] in {"duplicate_source", "source_cap"} for item in dropped))

    def test_search_query_adapter_is_bounded_and_records_provenance(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            rows = [metadata("search-a"), metadata("search-b")]
            return subprocess.CompletedProcess(command, 0, stdout="\n".join(json.dumps(item) for item in rows), stderr="")

        found = discover_query("resume teardown", limit=2, runner=runner)
        self.assertEqual(len(found), 2)
        self.assertEqual(found[0]["query"], "resume teardown")
        self.assertEqual(found[0]["result_rank"], 1)
        self.assertIn("ytsearch2:resume teardown", calls[0])
        self.assertIn("--flat-playlist", calls[0])

    def test_bounded_preview_command_limits_time_resolution_and_bytes(self):
        commands = []

        def runner(command, **kwargs):
            commands.append(command)
            template = Path(command[command.index("-o") + 1])
            output = Path(str(template).replace("%(ext)s", "mp4"))
            output.write_bytes(b"bounded-fixture")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as folder:
            media, provenance = download_bounded_preview(
                "https://www.youtube.com/watch?v=bounded",
                Path(folder),
                runner=runner,
                max_megabytes=7,
                max_height=480,
                end_sec=4.2,
            )
            self.assertTrue(media.exists())
            command = commands[0]
            self.assertIn("--download-sections", command)
            self.assertIn("*0-4.200", command)
            self.assertIn("7M", command)
            self.assertIn("bestvideo[height<=480]/best[height<=480]", command)
            self.assertFalse(provenance["retained"])
            self.assertEqual(provenance["section_end_sec"], 4.2)

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg is required for exact frame evidence")
    def test_exact_early_frames_and_contact_sheet_have_hash_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            media = root / "source.mp4"
            command = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=180x320:rate=10:duration=4.2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(media),
            ]
            subprocess.run(command, check=True, capture_output=True)
            evidence = capture_visual_evidence(media, root / "visual")
            self.assertEqual(evidence["contact_sheet_times_sec"], [0.0, 0.5, 1.5, 3.0])
            self.assertEqual(len(evidence["provenance"]["frames"]), 4)
            for frame in evidence["provenance"]["frames"]:
                path = Path(frame["path"])
                self.assertTrue(path.exists())
                self.assertEqual(sha256_file(path), frame["sha256"])
            sheet = Path(evidence["contact_sheet_path"])
            self.assertTrue(sheet.exists())
            self.assertEqual(sha256_file(sheet), evidence["provenance"]["contact_sheet_sha256"])

    def test_offline_cli_fixture_uses_no_media_without_explicit_visual_flag(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fixture_path = root / "fixture.json"
            fixture_path.write_text(
                json.dumps(
                    {
                        "queries": {"resume review": ["fixture-video"]},
                        "sources": {
                            "fixture-video": {
                                "metadata": metadata("fixture-video"),
                                "vtt": ROLLING_VTT,
                                "caption_kind": "creator_captions",
                                "media_path": "deliberately-missing.mp4",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            output = root / "out"
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(
                    [
                        "--query",
                        "resume review",
                        "--query-limit",
                        "4",
                        "--max-sources",
                        "1",
                        "--fixture-json",
                        str(fixture_path),
                        "--output-dir",
                        str(output),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads((output / "youtube_evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["manifest"]["source_count"], 1)
            self.assertFalse(payload["manifest"]["capture_visuals"])
            source = payload["sources"][0]
            self.assertEqual(source["media_status"], "not_requested")
            self.assertIsNone(source["contact_sheet_path"])
            self.assertEqual(source["evidence_provenance"]["metadata"]["basis"], "offline-fixture")
            self.assertIsNone(source["hook_0_3"])

    def test_visual_failure_is_audited_without_discarding_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fixture_path = root / "fixture.json"
            fixture_path.write_text(
                json.dumps(
                    {
                        "sources": {
                            "visual-failure": {
                                "metadata": metadata("visual-failure"),
                                "media_path": "missing-source.mp4",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            payload = collect(
                urls=["https://youtube.com/shorts/visual-failure"],
                queries=[],
                output_dir=root / "out",
                capture_visuals=True,
                fixture=FixtureStore(fixture_path),
                collected_at=NOW,
            )
            self.assertEqual(payload["manifest"]["source_count"], 1)
            self.assertEqual(payload["sources"][0]["media_status"], "capture_failed")
            self.assertEqual(payload["sources"][0]["metadata_status"], "available")
            self.assertTrue(any(item.get("stage") == "visual" for item in payload["manifest"]["errors"]))


if __name__ == "__main__":
    unittest.main()
