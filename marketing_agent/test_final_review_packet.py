import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from marketing_agent.final_review_packet import (
    _value_present,
    build_review_packet,
    sha256_file,
    validate_beat_map,
    validate_evidence_ledger,
)


FFMPEG_AVAILABLE = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


class FinalReviewPacketUnitTests(unittest.TestCase):
    def test_sha256_file_hashes_exact_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.bin"
            payload = b"Signal final review packet\n"
            path.write_bytes(payload)
            self.assertEqual(sha256_file(path), hashlib.sha256(payload).hexdigest())

    def test_beat_map_enforces_half_second_delta(self):
        passing = validate_beat_map(
            {"beats": [{"label": "Rewrite", "audioSec": 7.0, "visualSec": 7.5}]}
        )
        failing = validate_beat_map(
            {"beats": [{"label": "Rewrite", "audioSec": 7.0, "visualSec": 7.501}]}
        )
        self.assertTrue(passing["passed"])
        self.assertFalse(failing["passed"])
        self.assertIn("exceeds 0.5s", failing["blockers"][0])

    def test_evidence_ledger_rejects_exact_value_mismatch(self):
        report = validate_evidence_ledger(
            {
                "facts": [
                    {
                        "id": "ticket-volume",
                        "value": "35+",
                        "occurrences": {
                            "proof": "35+ tickets weekly",
                            "rewrite": "Resolved 35+ weekly tickets",
                            "receipt": "12,000 rows",
                        },
                    }
                ]
            }
        )
        self.assertFalse(report["passed"])
        self.assertIn("receipt", report["blockers"][0])

    def test_evidence_values_cannot_match_inside_larger_numbers(self):
        report = validate_evidence_ledger(
            {
                "facts": [
                    {
                        "id": "ticket-volume",
                        "value": "35",
                        "occurrences": {"proof": "35 tickets", "rewrite": "Resolved 350 tickets"},
                    }
                ]
            }
        )
        self.assertFalse(report["passed"])
        self.assertIn("rewrite", report["blockers"][0])

    def test_evidence_values_allow_normal_sentence_punctuation(self):
        self.assertTrue(_value_present("22%", "Cut false positives 22%."))
        self.assertTrue(_value_present("alerts", "Triaged Sentinel alerts, cutting noise."))
        self.assertFalse(_value_present("35", "Resolved 350 tickets."))
        self.assertFalse(_value_present("35", "Resolved 35+ tickets."))

    def test_score_receipt_must_reproduce_totals(self):
        report = validate_evidence_ledger(
            {
                "scores": {
                    "before": 20,
                    "after": 80,
                    "rows": [
                        {"before": 10, "after": 30},
                        {"before": 10, "after": 40},
                    ],
                }
            }
        )
        self.assertFalse(report["passed"])
        self.assertIn("row sums", report["blockers"][0])


@unittest.skipUnless(FFMPEG_AVAILABLE, "ffmpeg and ffprobe are required for the integration fixture")
class FinalReviewPacketIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.video = cls.root / "fixture.mp4"
        cls.script = cls.root / "selected_script.md"
        cls.timeline = cls.root / "beat_map.json"
        cls.ledger = cls.root / "evidence_ledger.json"
        cls.script.write_text("The proof is 35+ tickets. Replace it with 35+ tickets.\n", encoding="utf-8")
        cls.timeline.write_text(
            json.dumps(
                {
                    "beats": [
                        {
                            "label": "Weak line",
                            "audioSec": 2.0,
                            "visualSec": 2.2,
                            "cropBox": {"x": 0.1, "y": 0.2, "width": 0.8, "height": 0.2, "normalized": True},
                        },
                        {"label": "Rewrite", "audioSec": 8.0, "visualSec": 8.3},
                    ]
                }
            ),
            encoding="utf-8",
        )
        cls.ledger.write_text(
            json.dumps(
                {
                    "facts": [
                        {
                            "id": "ticket-volume",
                            "value": "35+",
                            "occurrences": {
                                "proof": "35+",
                                "rewrite": "35+",
                                "receipt": "35+",
                            },
                        }
                    ],
                    "scores": {
                        "before": 20,
                        "after": 80,
                        "rows": [
                            {"before": 10, "after": 40},
                            {"before": 10, "after": 40},
                        ],
                    },
                }
            ),
            encoding="utf-8",
        )
        command = [
            shutil.which("ffmpeg"),
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x172033:s=1080x1920:r=30:d=18.1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=18.1",
            "-t",
            "18.1",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-tune",
            "stillimage",
            "-crf",
            "45",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "64k",
            "-movflags",
            "+faststart",
            str(cls.video),
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_manifest_and_gate_contract(self):
        work_dir = self.root / "packet"
        result = build_review_packet(
            work_dir=work_dir,
            video=self.video,
            script=self.script,
            beat_map=self.timeline,
            evidence_ledger=self.ledger,
            run_id="fixture-run",
        )
        manifest = json.loads(result["manifestPath"].read_text(encoding="utf-8"))
        gate = json.loads(result["gatePath"].read_text(encoding="utf-8"))

        self.assertTrue(gate["passed"], gate["blockers"])
        self.assertTrue(gate["humanWatchRequired"])
        self.assertFalse(gate["publishingAttempted"])
        self.assertFalse(gate["stateTransitioned"])
        self.assertEqual(manifest["runId"], "fixture-run")
        self.assertTrue(manifest["humanWatchRequired"])
        self.assertFalse(manifest["humanWatchCompleted"])
        self.assertRegex(manifest["hashes"]["videoSha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(manifest["hashes"]["scriptSha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(manifest["hashes"]["audioSha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(len(manifest["artifacts"]["literalFrames"]), 4)
        self.assertTrue(Path(manifest["artifacts"]["contactSheet"]["path"]).exists())
        self.assertEqual(manifest["artifacts"]["contactSheet"]["frameCount"], 6)
        self.assertEqual(len(manifest["artifacts"]["fullResolutionCrops"]), 1)
        self.assertTrue(manifest["audioQa"]["silence"]["checked"])
        self.assertTrue(manifest["audioQa"]["peak"]["checked"])
        self.assertEqual(manifest["approval"]["status"], "DETERMINISTIC_QA_PASSED_AWAITING_HUMAN_WATCH")


if __name__ == "__main__":
    unittest.main()
