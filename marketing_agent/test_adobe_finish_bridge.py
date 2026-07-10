from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import marketing_agent.adobe_finish_bridge as bridge


def source_probe() -> dict:
    return {
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1080,
                "height": 1920,
                "pix_fmt": "yuv420p",
                "sample_aspect_ratio": "1:1",
                "avg_frame_rate": "30/1",
                "r_frame_rate": "30/1",
                "time_base": "1/15360",
                "start_pts": 0,
                "duration_ts": 307200,
                "nb_frames": "600",
                "nb_read_frames": "600",
            },
            {
                "index": 1,
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "channels": 2,
                "channel_layout": "stereo",
                "time_base": "1/48000",
                "start_pts": 0,
                "duration_ts": 960000,
            },
        ],
        "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "20.000000"},
    }


def audio_provenance() -> dict:
    return {
        "codec": "aac",
        "sampleRate": 48000,
        "channels": 2,
        "packetCount": 939,
        "packetPayloadSha256": "a" * 64,
        "relativeTimingSha256": "b" * 64,
        "firstPacketPts": "0/1",
    }


def beat_map() -> dict:
    return {
        "beats": [
            {"label": "Opening resume problem", "audioSec": 0.0, "visualSec": 0.0},
            {"label": "Proof found", "audioSec": 5.0, "visualSec": 5.1},
            {"label": "Evidence-backed rewrite", "audioSec": 11.0, "visualSec": 11.0},
            {"label": "Service CTA", "audioSec": 17.5, "visualSec": 17.5},
        ]
    }


class AdobeFinishBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bin = self.root / "Adobe After Effects 2026" / "Support Files"
        self.bin.mkdir(parents=True)
        self.afterfx = self.bin / "AfterFX.exe"
        self.aerender = self.bin / "aerender.exe"
        self.ffprobe = self.root / "ffprobe.exe"
        self.ffmpeg = self.root / "ffmpeg.exe"
        for executable in (self.afterfx, self.aerender, self.ffprobe, self.ffmpeg):
            executable.write_bytes(b"test executable")

        self.tools = bridge.detect_tools(
            afterfx_path=self.afterfx,
            aerender_path=self.aerender,
            ffprobe_path=self.ffprobe,
            ffmpeg_path=self.ffmpeg,
        )
        self.source = self.root / "controlled_short.mp4"
        self.source.write_bytes(b"synthetic H.264/AAC fixture")
        self.beats = self.root / "beat_map.json"
        self.beats.write_text(json.dumps(beat_map()), encoding="utf-8")
        self.manifest_path = self.root / "adobe_finish_manifest.json"
        self.adobe_video = self.root / "adobe_video_only.mov"
        self.final_video = self.root / "adobe_finished.mp4"

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def fake_probe(_path: Path, _tool: str) -> dict:
        return copy.deepcopy(source_probe())

    @staticmethod
    def fake_fingerprint(_path: Path, _tool: str, _summary: dict) -> dict:
        return copy.deepcopy(audio_provenance())

    def prepare(self, *, dry_run: bool) -> dict:
        return bridge.prepare_manifest(
            source=self.source,
            beat_map=self.beats,
            manifest_path=self.manifest_path,
            adobe_video_path=self.adobe_video,
            final_path=self.final_video,
            dry_run=dry_run,
            tools=self.tools,
            probe_func=self.fake_probe,
            fingerprint_func=self.fake_fingerprint,
        )

    def test_detects_matching_adobe_install_and_fails_closed_when_missing(self) -> None:
        self.assertTrue(self.tools["ready"])
        self.assertTrue(self.tools["sameAdobeInstall"])
        self.assertEqual(Path(self.tools["afterEffects"]["path"]), self.afterfx.resolve())
        self.assertEqual(Path(self.tools["aerender"]["path"]), self.aerender.resolve())

        missing = bridge.detect_tools(
            afterfx_path=self.root / "missing-AfterFX.exe",
            aerender_path=self.aerender,
            ffprobe_path=self.ffprobe,
            ffmpeg_path=self.ffmpeg,
        )
        self.assertFalse(missing["ready"])
        self.assertIn("After Effects is unavailable", missing["blockers"])

    def test_installed_adobe_discovery_uses_case_insensitive_windows_environment(self) -> None:
        program_files = self.root / "Program Files"
        support_files = program_files / "Adobe" / "Adobe After Effects 2026" / "Support Files"
        support_files.mkdir(parents=True)
        (support_files / "AfterFX.exe").write_bytes(b"AfterFX")
        (support_files / "aerender.exe").write_bytes(b"aerender")

        discovered = bridge.detect_tools(
            ffprobe_path=self.ffprobe,
            ffmpeg_path=self.ffmpeg,
            environ={"PROGRAMFILES": str(program_files)},
            which=lambda _name: None,
            system_name="Windows",
        )
        self.assertTrue(discovered["ready"])
        self.assertEqual(Path(discovered["afterEffects"]["path"]), (support_files / "AfterFX.exe").resolve())
        self.assertEqual(Path(discovered["aerender"]["path"]), (support_files / "aerender.exe").resolve())

    def test_dry_run_writes_nothing_and_locks_the_finish_contract(self) -> None:
        result = self.prepare(dry_run=True)
        self.assertTrue(result["ready"])
        self.assertTrue(result["dryRun"])
        self.assertFalse(result["written"])
        self.assertFalse(self.manifest_path.exists())

        manifest = result["manifest"]
        contract = manifest["finishContract"]
        self.assertFalse(manifest["toolchain"]["directProjectGeneration"]["enabled"])
        self.assertFalse(contract["layers"]["newTextLayersAllowed"])
        self.assertFalse(contract["audio"]["importIntoAdobe"])
        self.assertFalse(contract["audio"]["retimingAllowed"])
        self.assertEqual(contract["composition"]["sourceTransform"]["scalePercent"], 100)
        self.assertFalse(contract["composition"]["sourceTransform"]["keyframesAllowed"])
        self.assertEqual(
            tuple(effect["id"] for effect in contract["allowedEffects"]),
            bridge.ALLOWED_EFFECT_IDS,
        )
        self.assertEqual(manifest["publishing"]["allowed"], False)
        self.assertNotIn("label", json.dumps(manifest["inputs"]["beatMap"]["events"]))

    def test_prepare_fails_closed_when_adobe_is_unavailable(self) -> None:
        unavailable = copy.deepcopy(self.tools)
        unavailable["ready"] = False
        unavailable["afterEffects"] = {"found": False, "path": None, "source": "not_found"}
        unavailable["sameAdobeInstall"] = False
        unavailable["blockers"] = ["After Effects is unavailable"]
        preview = bridge.prepare_manifest(
            source=self.source,
            beat_map=self.beats,
            manifest_path=self.manifest_path,
            adobe_video_path=self.adobe_video,
            final_path=self.final_video,
            dry_run=True,
            tools=unavailable,
            probe_func=self.fake_probe,
            fingerprint_func=self.fake_fingerprint,
        )
        self.assertFalse(preview["ready"])
        self.assertFalse(self.manifest_path.exists())

        with self.assertRaisesRegex(bridge.ReadinessError, "After Effects is unavailable"):
            bridge.prepare_manifest(
                source=self.source,
                beat_map=self.beats,
                manifest_path=self.manifest_path,
                adobe_video_path=self.adobe_video,
                final_path=self.final_video,
                tools=unavailable,
                probe_func=self.fake_probe,
                fingerprint_func=self.fake_fingerprint,
            )

    def test_prepare_writes_hash_bound_manifest_and_refuses_overwrite(self) -> None:
        result = self.prepare(dry_run=False)
        self.assertTrue(result["written"])
        loaded = bridge.load_manifest(self.manifest_path)
        self.assertEqual(loaded["manifestSha256"], result["manifest"]["manifestSha256"])

        with self.assertRaisesRegex(bridge.ReadinessError, "will not overwrite"):
            self.prepare(dry_run=False)

    def test_beat_map_must_be_ordered_and_within_half_a_second(self) -> None:
        payload = beat_map()
        payload["beats"][2]["visualSec"] = 11.501
        self.beats.write_text(json.dumps(payload), encoding="utf-8")
        report = bridge.assess_readiness(
            source=self.source,
            beat_map=self.beats,
            tools=self.tools,
            probe_func=self.fake_probe,
            fingerprint_func=self.fake_fingerprint,
        )
        self.assertFalse(report["ready"])
        self.assertTrue(any("exceeds 0.5 seconds" in blocker for blocker in report["blockers"]))

    def test_adobe_intermediate_must_be_video_only_with_exact_timing(self) -> None:
        manifest = self.prepare(dry_run=True)["manifest"]
        valid = source_probe()
        valid["streams"] = [valid["streams"][0]]
        valid["streams"][0]["codec_name"] = "prores"
        self.assertEqual(bridge.adobe_intermediate_blockers(manifest, valid), [])

        with_audio = source_probe()
        blockers = bridge.adobe_intermediate_blockers(manifest, with_audio)
        self.assertTrue(any("video-only" in blocker for blocker in blockers))

        wrong_timing = copy.deepcopy(valid)
        wrong_timing["streams"][0]["nb_frames"] = "599"
        wrong_timing["streams"][0]["nb_read_frames"] = "599"
        wrong_timing["streams"][0]["duration_ts"] = 306688
        blockers = bridge.adobe_intermediate_blockers(manifest, wrong_timing)
        self.assertTrue(any("frame count differs" in blocker for blocker in blockers))
        self.assertTrue(any("duration differs" in blocker for blocker in blockers))

        wrong_dimensions = copy.deepcopy(valid)
        wrong_dimensions["streams"][0]["width"] = 1078
        blockers = bridge.adobe_intermediate_blockers(manifest, wrong_dimensions)
        self.assertTrue(any("dimensions" in blocker for blocker in blockers))

        hidden_subtitle = copy.deepcopy(valid)
        hidden_subtitle["streams"].append({"codec_type": "subtitle", "codec_name": "mov_text"})
        blockers = bridge.adobe_intermediate_blockers(manifest, hidden_subtitle)
        self.assertTrue(any("subtitle" in blocker for blocker in blockers))

        variable_rate = copy.deepcopy(valid)
        variable_rate["streams"][0]["r_frame_rate"] = "60/1"
        variable_rate["streams"][0]["sample_aspect_ratio"] = "4:3"
        blockers = bridge.adobe_intermediate_blockers(manifest, variable_rate)
        self.assertTrue(any("constant frame rate" in blocker for blocker in blockers))
        self.assertTrue(any("square pixels" in blocker for blocker in blockers))

    def test_final_output_requires_original_aac_packets_and_offset(self) -> None:
        manifest = self.prepare(dry_run=True)["manifest"]
        self.assertEqual(
            bridge.final_output_blockers(manifest, source_probe(), audio_provenance()),
            [],
        )

        reencoded = audio_provenance()
        reencoded["packetPayloadSha256"] = "c" * 64
        blockers = bridge.final_output_blockers(manifest, source_probe(), reencoded)
        self.assertTrue(any("packetPayloadSha256" in blocker for blocker in blockers))

        shifted = audio_provenance()
        shifted["firstPacketPts"] = "1/100"
        blockers = bridge.final_output_blockers(manifest, source_probe(), shifted)
        self.assertTrue(any("narration offset differs" in blocker for blocker in blockers))

        wrong_media = source_probe()
        wrong_media["streams"][0]["height"] = 1918
        wrong_media["streams"][0]["nb_frames"] = "599"
        wrong_media["streams"][0]["nb_read_frames"] = "599"
        wrong_media["streams"][0]["duration_ts"] = 306688
        blockers = bridge.final_output_blockers(manifest, wrong_media, audio_provenance())
        self.assertTrue(any("dimensions" in blocker for blocker in blockers))
        self.assertTrue(any("frame count differs" in blocker for blocker in blockers))
        self.assertTrue(any("duration differs" in blocker for blocker in blockers))

    def test_project_review_is_explicit_and_hash_bound(self) -> None:
        self.prepare(dry_run=False)
        project = self.root / "controlled_finish.aep"
        project.write_bytes(b"reviewed project")
        review = bridge.create_project_review(
            manifest_path=self.manifest_path,
            project_path=project,
            reviewed_by="Test Reviewer",
            confirm_contract=True,
        )
        manifest = bridge.load_manifest(self.manifest_path)
        self.assertEqual(bridge.validate_project_review(manifest)["reviewSha256"], review["reviewSha256"])

        project.write_bytes(b"changed after review")
        with self.assertRaisesRegex(bridge.ContractError, "hash has changed"):
            bridge.validate_project_review(manifest)

    def test_commands_cannot_generate_projects_retime_audio_or_publish(self) -> None:
        manifest = self.prepare(dry_run=True)["manifest"]
        review = {"projectPath": str(self.root / "reviewed.aep")}
        aerender_command = bridge.build_aerender_command(manifest, review)
        self.assertEqual(aerender_command[0], str(self.aerender.resolve()))
        self.assertNotIn(str(self.afterfx.resolve()), aerender_command)
        self.assertEqual(aerender_command[aerender_command.index("-comp") + 1], bridge.REVIEW_COMP_NAME)

        command = bridge.build_finalize_command(manifest, temporary_output=self.root / "partial.mp4")
        audio_codec_index = command.index("-c:a")
        self.assertEqual(command[audio_codec_index + 1], "copy")
        self.assertNotIn("-shortest", command)
        self.assertNotIn("publish", " ".join(command).casefold())
        self.assertEqual(command[command.index("-fps_mode") + 1], "passthrough")

    def test_manifest_contract_tampering_is_rejected(self) -> None:
        manifest = self.prepare(dry_run=True)["manifest"]
        manifest["finishContract"]["layers"]["newTextLayersAllowed"] = True
        manifest["manifestSha256"] = bridge._manifest_digest(manifest)
        blockers = bridge.manifest_blockers(manifest)
        self.assertTrue(any("locked production contract" in blocker for blocker in blockers))

        malformed = copy.deepcopy(manifest)
        malformed["inputs"]["sourceShort"]["media"].pop("video")
        malformed["manifestSha256"] = bridge._manifest_digest(malformed)
        blockers = bridge.manifest_blockers(malformed)
        self.assertTrue(any("source media is incomplete" in blocker for blocker in blockers))

    def test_manifest_schema_file_is_valid_json(self) -> None:
        schema = (
            Path(__file__).resolve().parents[1]
            / "marketing"
            / "adobe"
            / "after_effects"
            / "controlled_screen_finish_manifest.schema.json"
        )
        payload = json.loads(schema.read_text(encoding="utf-8"))
        self.assertEqual(payload["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(payload["properties"]["publishing"]["properties"]["allowed"]["const"], False)


if __name__ == "__main__":
    unittest.main()
