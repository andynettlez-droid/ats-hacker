from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from marketing_agent.controlled_screen_sync import find_phrase, synchronize, tokens


SCRIPT = (
    "Here is Jordan, applying for a cybersecurity analyst role. The job keeps asking for Sentinel, "
    "CrowdStrike, and alert volume. His resume says, 'Monitored security alerts and supported "
    "investigations.' That sounds reasonable, but it hides the scale and tools. Lower down, the proof "
    "is already there: 120 monthly Sentinel alerts, CrowdStrike reviews, and 22 percent fewer false "
    "positives. So delete the soft line and write: 'Triaged 120 monthly Sentinel and CrowdStrike alerts, "
    "reducing false positives by 22 percent.' Now it actually matches the job. Need your resume or cover "
    "letter fixed to match the job? Use the link below before you apply."
)


def fake_alignment(script: str) -> dict:
    words = tokens(script)
    step = 20.0 / len(words)
    return {
        "words": [
            {"word": word, "startSec": round(index * step, 3), "endSec": round((index + 0.8) * step, 3)}
            for index, word in enumerate(words)
        ]
    }


def config() -> dict:
    return {
        "candidate": {
            "name": "Jordan Patel",
            "targetRole": "Cybersecurity Analyst",
            "contactLine": "Columbus, OH | jordan@example.com",
            "summary": "Cybersecurity analyst with endpoint and alert triage experience.",
            "skills": ["Sentinel", "CrowdStrike", "Phishing triage"],
            "experience": [
                {
                    "title": "Security Support Intern",
                    "companyLine": "Northstar Health | 2025 - Present",
                    "bullets": [
                        "Monitored security alerts and supported investigations.",
                        "Reviewed 120 monthly security alerts in Sentinel.",
                        "Used CrowdStrike during endpoint investigation reviews.",
                        "Reduced false positives by 22 percent through rule documentation.",
                    ],
                },
                {
                    "title": "IT Support Technician",
                    "companyLine": "MetroLink | 2023 - 2025",
                    "bullets": [
                        "Resolved account access requests for 180 staff.",
                        "Escalated suspicious sign-ins with evidence notes.",
                        "Documented recurring endpoint issues in Jira.",
                    ],
                },
            ],
            "education": ["A.A.S. Cybersecurity"],
            "certifications": ["CompTIA Security+"],
        },
        "edit": {
            "weakLine": "Monitored security alerts and supported investigations.",
            "rewriteLine": "Triaged 120 monthly Sentinel and CrowdStrike alerts, reducing false positives by 22 percent.",
            "proofRefs": [
                {"experienceIndex": 0, "bulletIndex": 1},
                {"experienceIndex": 0, "bulletIndex": 2},
                {"experienceIndex": 0, "bulletIndex": 3},
            ],
        },
        "review": {
            "searchTerms": ["Sentinel", "CrowdStrike", "alert volume"],
            "receiptRows": [
                {"label": "TOOLS", "value": "Sentinel + CrowdStrike"},
                {"label": "VOLUME", "value": "120 monthly alerts"},
                {"label": "RESULT", "value": "22 percent fewer false positives"},
            ],
            "cta": "Need your resume or cover letter fixed? Use the link below before you apply.",
        },
    }


class ControlledScreenSyncTests(unittest.TestCase):
    def test_rewrite_cue_can_use_unique_lead_when_number_is_spoken_as_words(self):
        words = [
            {"word": "Write", "startSec": 1.0, "endSec": 1.2},
            {"word": "Triaged", "startSec": 1.4, "endSec": 1.7},
            {"word": "one", "startSec": 1.8, "endSec": 1.9},
        ]
        found = find_phrase(
            words,
            ["Triaged 120+ monthly alerts", "Triaged"],
            start_after=1.0,
            minimum_tokens=1,
        )
        self.assertEqual(found, (1.4, 1.7))

    def test_sync_accepts_natural_reviewer_action_cue(self) -> None:
        natural_script = SCRIPT.replace(
            "So delete the soft line and write:",
            "I'd write:",
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config_path = root / "controlled_resume.json"
            alignment_path = root / "voice.mp3.alignment.json"
            script_path = root / "voice_full_script.txt"
            config_path.write_text(json.dumps(config()), encoding="utf-8")
            alignment_path.write_text(json.dumps(fake_alignment(natural_script)), encoding="utf-8")
            script_path.write_text(natural_script, encoding="utf-8")

            result = synchronize(
                config_path=config_path,
                alignment_path=alignment_path,
                script_path=script_path,
                audio_duration=20.0,
                output_config=root / "out.json",
                beat_map_path=root / "beats.json",
                evidence_path=root / "evidence.json",
            )

            self.assertGreater(result["timeline"]["type"], result["timeline"]["delete"])

    def test_sync_writes_timed_config_beat_map_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config_path = root / "controlled_resume.json"
            alignment_path = root / "voice.mp3.alignment.json"
            script_path = root / "voice_full_script.txt"
            out_config = root / "controlled_resume.synced.json"
            beat_map = root / "beat_visual_map.json"
            evidence = root / "evidence_ledger.json"
            config_path.write_text(json.dumps(config()), encoding="utf-8")
            alignment_path.write_text(json.dumps(fake_alignment(SCRIPT)), encoding="utf-8")
            script_path.write_text(SCRIPT, encoding="utf-8")

            result = synchronize(
                config_path=config_path,
                alignment_path=alignment_path,
                script_path=script_path,
                audio_duration=20.0,
                output_config=out_config,
                beat_map_path=beat_map,
                evidence_path=evidence,
            )

            synced = json.loads(out_config.read_text(encoding="utf-8"))
            beats = json.loads(beat_map.read_text(encoding="utf-8"))["beats"]
            ledger = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(result["durationSec"], 20.25)
            self.assertEqual(len(beats), 7)
            self.assertGreaterEqual(len(ledger["facts"]), 2)
            timeline = synced["timeline"]
            self.assertLess(timeline["proof"], timeline["select"])
            self.assertLess(timeline["type"], timeline["receipt"])
            self.assertLess(timeline["receipt"], timeline["cta"])

    def test_duration_outside_short_contract_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config_path = root / "controlled_resume.json"
            alignment_path = root / "voice.mp3.alignment.json"
            script_path = root / "voice_full_script.txt"
            config_path.write_text(json.dumps(config()), encoding="utf-8")
            alignment_path.write_text(json.dumps(fake_alignment(SCRIPT)), encoding="utf-8")
            script_path.write_text(SCRIPT, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected 18.0-27.6"):
                synchronize(
                    config_path=config_path,
                    alignment_path=alignment_path,
                    script_path=script_path,
                    audio_duration=31.0,
                    output_config=root / "out.json",
                    beat_map_path=root / "beats.json",
                    evidence_path=root / "evidence.json",
                )


if __name__ == "__main__":
    unittest.main()
