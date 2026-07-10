import csv
import argparse
import json
import tempfile
import unittest
import wave
from pathlib import Path

from PIL import Image

from marketing_agent import signal_growth_pipeline as pipeline
from marketing_agent.signal_growth_pipeline import (
    creative_qa,
    create_surface_fit_previews,
    required_quality_gate_names,
    human_review_flow_blockers,
    plate_qa,
    read_quality_gate,
    validate_no_credit_creative_gate,
    validate_surface_fit_manifest,
    write_quality_gate,
)


CYBERSECURITY_SCRIPT = """## Voiceover Script

Alright, this is Jordan. He's applying for junior cybersecurity.

I'm checking for Sentinel, CrowdStrike, phishing triage, and alert volume.

His resume says, "Monitored security alerts and supported investigations."

Sounds professional. Means nothing.

Lower down, the proof is there: 120 alerts a month, phishing escalations, false positives down 22%.

So delete this and write: "Triaged 120+ Sentinel and CrowdStrike alerts, cutting false positives 22%."

Need your resume or cover letter fixed to match the job? Use the link below before you apply.
"""

MEDICAL_BILLING_SCRIPT = """## Voiceover Script

Alright, this is Alyssa. She is applying for medical billing.

I'm checking for Epic, ICD-10, claim volume, and denials.

Her resume says: 'Handled billing tasks and helped resolve payment issues.'

That sounds responsible. It is still too vague.

Lower down, she has the proof: 60 claims a day, ICD-10 codes, insurer follow-ups, denials down 15%.

So delete the soft line and write: 'Processed 60+ daily claims in Epic using ICD-10 codes, reducing denials 15%.'

Need your resume or cover letter fixed to match the job? Use the link below before you apply.
"""

NETWORK_ADMIN_SCRIPT = """## Voiceover Script

Here's Jordan. He's applying for a network admin role at a healthcare group.

Resume's not awful. It's written like a help desk ticket.

First bullet: responsible for IT support and fixing network issues.

The job wants VLANs, Cisco switching, VPN, incident response.

Jordan has proof lower down.

Signal pulls it up: resolved a VLAN issue across 11 clinic workstations and cut repeat tickets 42%.

That's a real network admin bullet.

Need your resume fixed? Upload it to Signal before you apply.
"""

APPROVED_SCRIPTS = (
    CYBERSECURITY_SCRIPT,
    MEDICAL_BILLING_SCRIPT,
    NETWORK_ADMIN_SCRIPT,
)


class SignalGrowthGateTests(unittest.TestCase):
    def write_tiny_wav(self, path: Path, duration_sec: float = 0.25) -> None:
        sample_rate = 16000
        sample_count = int(sample_rate * duration_sec)
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(sample_rate)
            handle.writeframes(b"\x00\x00" * sample_count)

    def write_minimum_gate_files(self, folder: Path, selected_script: str = CYBERSECURITY_SCRIPT) -> None:
        (folder / "viral_resume_swipe_file.md").write_text("# Swipe\n\nCurrent source-backed patterns.", encoding="utf-8")
        (folder / "blunt_creative_review.md").write_text(
            """# Blunt Creative Review

Verdict: PASS

## Scroll-Stop / First-Frame Critique

The first frame shows the resume line already highlighted, so the viewer understands the problem with sound off.

## Human Creator Voice Critique

The read sounds like a real recruiter reacting to a line, not a product demo.

## Visual Payoff Critique

The payoff is the visible before/after transformation: vague line out, proof-backed line in.

## What Still Feels Weak / Failure Risk

The edit must stay sharp and fast. If the overlay floats or the captions dominate, the concept fails.
""",
            encoding="utf-8",
        )
        option_scripts = [
            CYBERSECURITY_SCRIPT,
            MEDICAL_BILLING_SCRIPT,
            NETWORK_ADMIN_SCRIPT,
            """Your first line should not make a recruiter hunt for the work. This is Noah, applying for hospital IT support. The role needs ServiceNow, Active Directory, and VPN support. His line says, 'Resolved technical issues for users.' That hides the scale. Lower down, he shows 35 weekly tickets and clinical staff support. Delete the soft line and write the proof plainly. Need your resume or cover letter fixed to match the job? Use the link below before you apply.""",
            """Watch one polished sentence waste a perfectly good operations career. Mia is applying for project coordination. The job asks for schedules, vendors, and delivery dates. Her resume says, 'Supported cross-functional initiatives.' Pleasant, but empty. The proof is lower: 14 vendors, a six-week launch, and every milestone delivered on time. Replace the fog with those facts. Need your resume or cover letter fixed to match the job? Use the link below before you apply.""",
        ]
        (folder / "script_options.md").write_text(
            "\n\n".join(
                [
                    f"## Option {index}\n\n{script}\n\n### Read-Aloud Review\n\nPass but parked."
                    for index, script in enumerate(option_scripts, start=1)
                ]
            )
            + "\n\nRejected: generic SaaS demo.",
            encoding="utf-8",
        )
        (folder / "selected_script.md").write_text(selected_script, encoding="utf-8")
        (folder / "storyboard_options.md").write_text(
            """# Storyboards

## Direction 1 - Screen Recording Teardown - SELECTED

Opening frame: overhead phone-shot composition of the resume editor with the weak line already red-highlighted. Rendering remains blocked until approval.

0-2s: Close-up resume line appears first, before any intro.
2-5s: Search terms appear in the side note.
5-9s: Weak line gets boxed in red.
9-14s: Proof lower on the resume is pulled into view.
14-20s: Visible edit deletes the weak line and types the stronger rewrite.
20-25s: Before/after transformation payoff shows the stronger line highlighted green.
25-28s: CTA appears as a small creator-style caption.

## Direction 2 - Tablet Desk Teardown

Deterministic readable overlay on a blank tablet plate.

## Direction 3 - Paper Desk Roast

Paper gets marked, tossed, and rebuilt.
""",
            encoding="utf-8",
        )
        with (folder / "exemplar_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
            fieldnames = [
                "id",
                "topic",
                "hook_text",
                "beat_by_beat_breakdown",
                "what_signal_should_copy",
                "what_signal_should_avoid",
                "evidence_strength",
                "visual_style",
            ]
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for index in range(1, 27):
                is_document = index <= 6
                writer.writerow(
                    {
                        "id": str(index),
                        "topic": "resume recruiter job-search document edit" if is_document else "resume recruiter job-search",
                        "hook_text": "This line sounds professional. That is the problem.",
                        "beat_by_beat_breakdown": "0-2s hook; 2-8s weak line; 8-16s proof; 16-24s edit; 24-28s CTA",
                        "what_signal_should_copy": "Show the real resume problem first.",
                        "what_signal_should_avoid": "Avoid product-demo language.",
                        "evidence_strength": "verified_youtube_metadata",
                        "visual_style": "screen recording document edit" if is_document else "recruiter resume review",
                    }
                )

    def test_human_review_flow_rejects_generic_saas_script(self) -> None:
        blockers = human_review_flow_blockers(
            "Signal helps job seekers unlock better opportunities with an optimized resume. "
            "Need your resume or cover letter fixed to match the job? Use the link below before you apply."
        )
        self.assertGreaterEqual(len(blockers), 5)
        self.assertTrue(any("candidate and role" in blocker for blocker in blockers))
        self.assertTrue(any("weak line" in blocker for blocker in blockers))

    def test_read_spoken_script_prefers_full_voice_script_over_stale_segments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "vo_hook.txt").write_text("Old rejected hook.", encoding="utf-8")
            (folder / "voice_full_script.txt").write_text("Approved full voice script.", encoding="utf-8")
            self.assertEqual(pipeline.read_spoken_script(folder), "Approved full voice script.")

    def test_screen_format_requires_voice_qa_for_final_qa(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "resume_brief.json").write_text(
                json.dumps({"format": "screen_recording_teardown"}),
                encoding="utf-8",
            )
            gates = required_quality_gate_names(folder)
            self.assertIn("screen_visual_qa", gates)
            self.assertIn("voice_qa", gates)
            self.assertNotIn("plate_qa", gates)

    def test_voice_qa_requires_human_review_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            audio = folder / "abby_voice_test_10s.wav"
            self.write_tiny_wav(audio)
            (folder / "voice_test_abby_10s.txt").write_text(
                "Need your resume or cover letter fixed to match the job?",
                encoding="utf-8",
            )

            with self.assertRaises(SystemExit):
                pipeline.voice_qa(
                    argparse.Namespace(
                        work_dir=str(folder),
                        run_id=None,
                        audio=str(audio),
                        script=None,
                        human_reviewed=False,
                        pronunciation_ok=False,
                        natural_read=False,
                        pacing_ok=False,
                        cta_ok=False,
                        max_duration=15.0,
                    )
                )

            report = read_quality_gate(folder, "voice_qa")
            self.assertIsNotNone(report)
            self.assertFalse(report["passed"])
            self.assertTrue(any("human-reviewed" in blocker for blocker in report["blockers"]))

    def test_voice_qa_passes_when_reviewed_and_natural(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            audio = folder / "abby_voice_test_10s.wav"
            self.write_tiny_wav(audio)
            (folder / "voice_test_abby_10s.txt").write_text(
                "Need your resume or cover letter fixed to match the job?",
                encoding="utf-8",
            )

            pipeline.voice_qa(
                argparse.Namespace(
                    work_dir=str(folder),
                    run_id=None,
                    audio=str(audio),
                    script=None,
                    human_reviewed=True,
                    pronunciation_ok=True,
                    natural_read=True,
                    pacing_ok=True,
                    cta_ok=True,
                    max_duration=15.0,
                )
            )

            report = read_quality_gate(folder, "voice_qa")
            self.assertTrue(report["passed"], report["blockers"])

    def test_voice_qa_passes_automatic_voice_lab_manifest_without_checkboxes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            audio = folder / "abby_voice_test_10s.wav"
            self.write_tiny_wav(audio)
            script = "Need your resume or cover letter fixed to match the job? Use the link below before you apply."
            script_path = folder / "voice_test_abby_10s.txt"
            script_path.write_text(script, encoding="utf-8")
            audio.with_suffix(audio.suffix + ".voice-lab.json").write_text(
                json.dumps(
                    {
                        "displayText": script,
                        "voiceText": script.replace("resume", "résumé"),
                        "takeCount": 3,
                        "selectedTake": 2,
                        "output": str(audio.resolve()),
                        "takes": [
                            {"take": 1, "wordsPerMinute": 155, "longPauseCount": 0},
                            {"take": 2, "wordsPerMinute": 166, "longPauseCount": 0},
                            {"take": 3, "wordsPerMinute": 175, "longPauseCount": 1},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            pipeline.voice_qa(
                argparse.Namespace(
                    work_dir=str(folder),
                    run_id=None,
                    audio=str(audio),
                    script=str(script_path),
                    human_reviewed=False,
                    pronunciation_ok=False,
                    natural_read=False,
                    pacing_ok=False,
                    cta_ok=False,
                    max_duration=15.0,
                )
            )
            report = read_quality_gate(folder, "voice_qa")
            self.assertTrue(report["passed"], report["blockers"])
            self.assertEqual(report["mode"], "voice_lab_automatic")

    def test_creative_gate_requires_human_reviewer_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_minimum_gate_files(
                folder,
                """## Voiceover Script

Signal helps job seekers unlock better opportunities with an optimized resume.

Need your resume or cover letter fixed to match the job? Use the link below before you apply.
""",
            )
            report = validate_no_credit_creative_gate(folder)
            self.assertFalse(report["passed"])
            self.assertTrue(any("human-review beat" in blocker for blocker in report["blockers"]))

    def test_creative_gate_accepts_source_backed_human_reviewer_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_minimum_gate_files(folder)
            report = validate_no_credit_creative_gate(folder)
            self.assertTrue(report["passed"], report["blockers"])
            self.assertEqual(report["sourceBackedExampleCount"], 26)
            self.assertEqual(report["hookRowCount"], 26)

    def test_creative_gate_rejects_duplicate_script_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_minimum_gate_files(folder)
            (folder / "script_options.md").write_text(
                "\n\n".join(
                    [
                        f"## Option {index}\n\n{CYBERSECURITY_SCRIPT}\n\n### Read-Aloud Review\n\nParked."
                        for index in range(1, 6)
                    ]
                )
                + "\n\nRejected: duplicates.",
                encoding="utf-8",
            )
            report = validate_no_credit_creative_gate(folder)
            self.assertFalse(report["passed"])
            joined = "\n".join(report["blockers"])
            self.assertIn("noun-swapped/repetitive", joined)
            self.assertIn("hook family", joined)

    def test_script_option_hook_family_ignores_voiceover_heading(self) -> None:
        options = pipeline.extract_script_options(
            """## Option 1 - Direct

### Voiceover Script

This line hides the work.

### Read-Aloud Review

Pass.

## Option 2 - Command

### Voiceover Script

Stop burying the evidence.

### Read-Aloud Review

Pass.
"""
        )
        self.assertEqual(pipeline.hook_family(options[0]), "judgment_first")
        self.assertEqual(pipeline.hook_family(options[1]), "command")

    def test_script_qa_rejects_unearned_numeric_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "resume_brief.json").write_text(
                json.dumps(
                    {
                        "candidateName": "Noah Reed",
                        "targetRole": "Hospital IT Support",
                        "weakBullet": "Resolved technical issues for users.",
                        "hiddenProof": "35 weekly ServiceNow tickets for clinical staff using Active Directory and VPN.",
                        "rewrite": "Resolved 35+ weekly ServiceNow tickets for clinical staff across Active Directory and VPN support.",
                        "scoreReceipt": ["keyword match", "tool match", "metric proof"],
                    }
                ),
                encoding="utf-8",
            )
            (folder / "voice_full_script.txt").write_text(
                """Alright, this is Noah, applying for hospital IT support. Recruiters search for ServiceNow, Active Directory, and VPN. His resume says, 'Resolved technical issues for users.' That could mean anything. Lower down, the proof is there: 35 weekly ServiceNow tickets for clinical staff using Active Directory and VPN. Delete the soft line and write those facts. His score goes from 42 to 89. Need your resume or cover letter fixed? Use the link below before you apply.""",
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit):
                pipeline.script_qa(
                    argparse.Namespace(
                        work_dir=str(folder),
                        run_id=None,
                        min_words=25,
                        max_words=96,
                        require_weak_quote=True,
                    )
                )
            report = read_quality_gate(folder, "script_qa")
            self.assertTrue(any("numeric score claim" in blocker for blocker in report["blockers"]))

    def test_creative_gate_rejects_shallow_review_and_untimed_storyboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_minimum_gate_files(folder)
            (folder / "blunt_creative_review.md").write_text(
                "# Review\n\nScreen edit is strongest.",
                encoding="utf-8",
            )
            (folder / "storyboard_options.md").write_text(
                """# Storyboards

## Direction 1 - Screen Recording Teardown - SELECTED

Resume visible, weak line highlighted, proof appears, edit happens in place. Rendering remains blocked until approval.

## Direction 2 - Tablet Desk Teardown

Deterministic readable overlay on a blank tablet plate.

## Direction 3 - Paper Desk Roast

Paper gets marked, tossed, and rebuilt.
""",
                encoding="utf-8",
            )
            report = validate_no_credit_creative_gate(folder)
            self.assertFalse(report["passed"])
            joined = "\n".join(report["blockers"])
            self.assertIn("Verdict: PASS", joined)
            self.assertIn("timestamped beats", joined)
            self.assertIn("first frame", joined)

    def test_creative_gate_accepts_all_approved_script_samples(self) -> None:
        for script in APPROVED_SCRIPTS:
            with self.subTest(script=script.splitlines()[2] if len(script.splitlines()) > 2 else "sample"):
                with tempfile.TemporaryDirectory() as tmp:
                    folder = Path(tmp)
                    self.write_minimum_gate_files(folder, script)
                    report = validate_no_credit_creative_gate(folder)
                    self.assertTrue(report["passed"], report["blockers"])

    def test_surface_fit_manifest_requires_readable_corner_pinned_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            Image.new("RGB", (1080, 1920), "#d6d3d1").save(folder / "tablet_plate.png")
            Image.new("RGBA", (780, 1100), (255, 255, 255, 255)).save(folder / "resume_overlay.png")
            manifest = folder / "surface_fit.json"
            manifest.write_text(
                json.dumps(
                    {
                        "surfaces": [
                            {
                                "surface": "tablet",
                                "frame": "tablet_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": {
                                    "tl": [160, 280],
                                    "tr": [940, 250],
                                    "br": [910, 1560],
                                    "bl": [140, 1510],
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            report = validate_surface_fit_manifest(folder, manifest)
            self.assertTrue(report["passed"], report["blockers"])
            self.assertGreater(report["surfaces"][0]["areaRatio"], 0.08)
            previews = create_surface_fit_previews(folder, manifest, folder / "surface_fit_previews")
            self.assertEqual(len(previews), 1)
            self.assertTrue(Path(previews[0]["out"]).exists())

            manifest.write_text(
                json.dumps(
                    {
                        "surfaces": [
                            {
                                "surface": "paper",
                                "frame": "tablet_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": [[20, 20], [80, 20], [80, 90], [20, 90]],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            small_report = validate_surface_fit_manifest(folder, manifest)
            self.assertFalse(small_report["passed"])
            self.assertTrue(any("too small" in blocker for blocker in small_report["blockers"]))

    def test_surface_fit_preview_clips_overlay_to_physical_quad(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            Image.new("RGB", (1080, 1920), "#000000").save(folder / "tablet_plate.png")
            Image.new("RGBA", (600, 800), (255, 0, 0, 255)).save(folder / "resume_overlay.png")
            manifest = folder / "surface_fit.json"
            manifest.write_text(
                json.dumps(
                    {
                        "surfaces": [
                            {
                                "surface": "tablet",
                                "frame": "tablet_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": {
                                    "tl": [240, 420],
                                    "tr": [840, 420],
                                    "br": [840, 1220],
                                    "bl": [240, 1220],
                                },
                                "blend": {"edgeFeatherPx": 0, "opacity": 1.0, "screenGlare": 0.0},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            previews = create_surface_fit_previews(folder, manifest, folder / "surface_fit_previews")
            with Image.open(previews[0]["out"]) as preview:
                self.assertLess(preview.getpixel((40, 40))[0], 5)
                self.assertGreater(preview.getpixel((540, 820))[0], 220)

    def test_surface_fit_review_packet_includes_plate_overlay_and_fitted_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            Image.new("RGB", (1080, 1920), "#111827").save(folder / "tablet_plate.png")
            Image.new("RGBA", (600, 800), (255, 255, 255, 255)).save(folder / "resume_overlay.png")
            manifest = folder / "surface_fit.json"
            manifest.write_text(
                json.dumps(
                    {
                        "surfaces": [
                            {
                                "surface": "tablet",
                                "frame": "tablet_plate.png",
                                "overlay": "resume_overlay.png",
                                "beat": "Tablet opens on resume edit.",
                                "corners": {
                                    "tl": [240, 420],
                                    "tr": [840, 420],
                                    "br": [840, 1220],
                                    "bl": [240, 1220],
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            pipeline.surface_fit_review_packet(
                argparse.Namespace(
                    work_dir=str(folder),
                    run_id=None,
                    manifest=None,
                    out_dir=None,
                    html_name=None,
                    host="192.168.2.10",
                    port=8798,
                    min_area_ratio=0.08,
                    max_area_ratio=0.92,
                )
            )

            html = (folder / "surface_fit_review.html").read_text(encoding="utf-8")
            self.assertIn("Source plate", html)
            self.assertIn("Resume overlay", html)
            self.assertIn("Fitted result", html)
            self.assertIn("surface_fit_previews/surface_01_tablet_plate_fit.png", html)

    def test_surface_format_requires_surface_fit_gate_for_final_qa(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "resume_brief.json").write_text(
                json.dumps({"format": "tablet_screen_edit_rebuild"}),
                encoding="utf-8",
            )
            gates = required_quality_gate_names(folder)
            self.assertIn("surface_fit_qa", gates)
            self.assertIn("plate_qa", gates)
            self.assertIn("voice_qa", gates)
            self.assertNotIn("screen_visual_qa", gates)

    def test_surface_build_plan_is_ready_but_waits_for_codex_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_minimum_gate_files(folder)
            (folder / "voice_full_script.txt").write_text(
                "Alright, this is Jordan. He is applying for junior cybersecurity.",
                encoding="utf-8",
            )
            (folder / "resume_brief.json").write_text(
                json.dumps({"format": "tablet_screen_edit_rebuild"}),
                encoding="utf-8",
            )
            (folder / "surface_fit.json").write_text(
                json.dumps(
                    {
                        "surfaces": [
                            {
                                "surface": "tablet",
                                "frame": "tablet_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": {
                                    "tl": [160, 280],
                                    "tr": [940, 250],
                                    "br": [910, 1560],
                                    "bl": [140, 1510],
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (folder / "blank_plate_generation_prompts.md").write_text(
                "# Blank Plate Prompts\n\nNo readable generated text.",
                encoding="utf-8",
            )
            write_quality_gate(folder, "creative_gate", {"passed": True, "blockers": [], "approvalPhrase": "APPROVE CREATIVE GATE test"})
            write_quality_gate(folder, "script_qa", {"passed": True, "blockers": [], "wordCount": 81})

            pipeline.surface_build_plan(
                argparse.Namespace(
                    run_id=None,
                    work_dir=str(folder),
                    host="192.168.2.10",
                    port=8798,
                    voice_text_name=None,
                    manifest_name=None,
                    prompt_name=None,
                    audio_name=None,
                    animatic_name=None,
                    final_name=None,
                    contact_sheet_name=None,
                )
            )

            report = json.loads((folder / "post_approval_surface_build_plan.json").read_text(encoding="utf-8"))
            self.assertTrue(report["readyAfterApproval"], report["blockers"])
            self.assertFalse(report["gates"]["surface_fit_qa"])
            self.assertTrue(any("surface_fit_qa still needs" in warning for warning in report["warnings"]))

    def test_creative_review_surface_packet_does_not_require_surface_fit_before_approval(self) -> None:
        old_runs_dir = pipeline.RUNS_DIR
        old_db_path = pipeline.DB_PATH
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pipeline.RUNS_DIR = tmp_path / "runs"
            pipeline.DB_PATH = tmp_path / "signal_growth_engine.sqlite"
            try:
                run_id = "test-surface-review"
                folder = pipeline.run_folder(run_id)
                self.write_minimum_gate_files(folder)
                (folder / "resume_brief.json").write_text(
                    json.dumps({"format": "tablet_screen_edit_rebuild"}),
                    encoding="utf-8",
                )
                (folder / "surface_fit.json").write_text(json.dumps({"surfaces": []}), encoding="utf-8")
                (folder / "surface_fit_animatic_contact_sheet.png").write_bytes(b"placeholder")
                conn = pipeline.db()
                now = pipeline.utc_now()
                metadata = {"creativeApprovalPhrase": f"APPROVE CREATIVE GATE {run_id}"}
                conn.execute(
                    """
                    INSERT INTO video_runs (
                      id, topic, title, status, landing_url, utm_source, utm_content,
                      metadata_json, created_at, updated_at
                    ) VALUES (?, ?, ?, 'AWAITING_CREATIVE_APPROVAL', ?, 'codex', ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        "surface review test",
                        "Surface Review Test",
                        "https://example.com",
                        run_id,
                        json.dumps(metadata),
                        now,
                        now,
                    ),
                )
                conn.commit()
                conn.close()
                write_quality_gate(folder, "creative_gate", {"passed": True, "blockers": [], "sourceCount": 26, "scriptOptionCount": 5})
                write_quality_gate(folder, "script_qa", {"passed": True, "blockers": [], "wordCount": 81})

                pipeline.creative_review_packet(argparse.Namespace(run_id=run_id, host="192.168.2.10", port=8798))

                packet = (folder / "codex_creative_gate_packet.md").read_text(encoding="utf-8")
                self.assertIn("Tablet/Paper Surface-Fit Teardown", packet)
                self.assertIn("not required before creative approval; required before final assembly", packet)
                self.assertIn(f"APPROVE CREATIVE GATE {run_id}", packet)
            finally:
                pipeline.RUNS_DIR = old_runs_dir
                pipeline.DB_PATH = old_db_path

    def test_creative_qa_accepts_surface_fit_overlays_without_shot_videos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_minimum_gate_files(folder)
            (folder / "script.md").write_text(CYBERSECURITY_SCRIPT, encoding="utf-8")
            (folder / "resume_brief.json").write_text(
                json.dumps(
                    {
                        "format": "tablet_screen_edit_rebuild",
                        "candidateName": "Jordan Patel",
                        "targetRole": "Junior Cybersecurity Analyst",
                        "weakBullet": "Monitored security alerts and supported investigations.",
                        "rewrite": "Triaged 120+ Sentinel and CrowdStrike alerts, cutting false positives 22%.",
                        "scoreReceipt": [
                            {"label": "Keyword match", "value": "phishing triage"},
                            {"label": "Tool match", "value": "Sentinel, CrowdStrike"},
                            {"label": "Metric proof", "value": "120+ alerts"},
                            {"label": "Outcome clarity", "value": "false positives down 22%"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            Image.new("RGB", (1080, 1920), "#d6d3d1").save(folder / "clean_tablet_plate.png")
            Image.new("RGBA", (780, 1100), (255, 255, 255, 255)).save(folder / "tablet_editor_overlay_jordan_before.png")
            (folder / "surface_fit.json").write_text(
                json.dumps(
                    {
                        "surfaces": [
                            {
                                "surface": "tablet",
                                "frame": "clean_tablet_plate.png",
                                "overlay": "tablet_editor_overlay_jordan_before.png",
                                "corners": {
                                    "tl": [160, 280],
                                    "tr": [940, 250],
                                    "br": [910, 1560],
                                    "bl": [140, 1510],
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            write_quality_gate(folder, "creative_gate", {"passed": True, "blockers": []})
            write_quality_gate(folder, "script_qa", {"passed": True, "blockers": [], "wordCount": 81})

            creative_qa(argparse.Namespace(work_dir=str(folder), run_id=None, format=None))

            report = read_quality_gate(folder, "creative_qa")
            self.assertTrue(report["passed"], report["blockers"])
            self.assertEqual(report["shotFiles"], [])
            self.assertEqual(len(report["surfaceOverlayPngs"]), 1)

    def test_plate_qa_accepts_visual_reviewed_surface_fit_image_plates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            Image.new("RGB", (1080, 1920), "#d6d3d1").save(folder / "clean_tablet_plate.png")
            Image.new("RGBA", (780, 1100), (255, 255, 255, 255)).save(folder / "resume_overlay.png")
            (folder / "surface_fit.json").write_text(
                json.dumps(
                    {
                        "surfaces": [
                            {
                                "surface": "tablet",
                                "frame": "clean_tablet_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": {
                                    "tl": [160, 280],
                                    "tr": [940, 250],
                                    "br": [910, 1560],
                                    "bl": [140, 1510],
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            plate_qa(
                argparse.Namespace(
                    work_dir=str(folder),
                    video=None,
                    run_id=None,
                    visual_reviewed=True,
                    generated_text_ok=False,
                )
            )

            report = read_quality_gate(folder, "plate_qa")
            self.assertTrue(report["passed"], report["blockers"])
            self.assertEqual(report["plates"][0]["type"], "image")

    def test_gold_readiness_reports_missing_clean_plates_and_pending_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write_minimum_gate_files(folder)
            (folder / "resume_brief.json").write_text(json.dumps({"format": "tablet_screen_edit_rebuild"}), encoding="utf-8")
            Image.new("RGBA", (780, 1100), (255, 255, 255, 255)).save(folder / "resume_overlay.png")
            (folder / "surface_fit.json").write_text(
                json.dumps(
                    {
                        "surfaces": [
                            {
                                "surface": "tablet",
                                "frame": "clean_tablet_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": {"tl": [160, 280], "tr": [940, 250], "br": [910, 1560], "bl": [140, 1510]},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            write_quality_gate(folder, "creative_gate", {"passed": True, "blockers": [], "approvalPhrase": "APPROVE CREATIVE GATE test"})
            write_quality_gate(folder, "script_qa", {"passed": True, "blockers": [], "wordCount": 81})
            write_quality_gate(folder, "creative_qa", {"passed": True, "blockers": []})

            pipeline.gold_readiness(
                argparse.Namespace(
                    run_id=None,
                    work_dir=str(folder),
                    manifest_name=None,
                    audio_name=None,
                    final_name=None,
                    contact_sheet_name=None,
                    json_name=None,
                    md_name=None,
                )
            )

            report = json.loads((folder / "gold_readiness_report.json").read_text(encoding="utf-8"))
            self.assertFalse(report["readyForFinalCodexReview"])
            self.assertTrue(any("clean plate missing" in blocker for blocker in report["blockers"]))
            self.assertIn("Generate or source clean blank", report["nextAction"])

    def test_prepare_plate_intake_lists_unique_plate_targets_and_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            Image.new("RGBA", (780, 1100), (255, 255, 255, 255)).save(folder / "resume_overlay.png")
            (folder / "blank_plate_generation_prompts.md").write_text(
                "# Prompts\n\nNo readable generated text.",
                encoding="utf-8",
            )
            (folder / "surface_fit.json").write_text(
                json.dumps(
                    {
                        "surfaces": [
                            {
                                "surface": "tablet",
                                "frame": "clean_tablet_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": {"tl": [160, 280], "tr": [940, 250], "br": [910, 1560], "bl": [140, 1510]},
                            },
                            {
                                "surface": "tablet",
                                "frame": "clean_tablet_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": {"tl": [160, 280], "tr": [940, 250], "br": [910, 1560], "bl": [140, 1510]},
                            },
                            {
                                "surface": "paper",
                                "frame": "clean_paper_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": {"tl": [160, 280], "tr": [940, 250], "br": [910, 1560], "bl": [140, 1510]},
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            pipeline.prepare_plate_intake(
                argparse.Namespace(
                    run_id=None,
                    work_dir=str(folder),
                    manifest_name=None,
                    prompt_name=None,
                    json_name=None,
                    md_name=None,
                    host="192.168.2.10",
                    port=8798,
                )
            )

            report = json.loads((folder / "plate_intake_checklist.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"], report["blockers"])
            self.assertEqual([item["filename"] for item in report["requiredPlateFiles"]], ["clean_tablet_plate.png", "clean_paper_plate.png"])
            md = (folder / "plate_intake_checklist.md").read_text(encoding="utf-8")
            self.assertIn("No readable generated text", md)
            self.assertIn("surface-fit-review", md)

    def test_ingest_plate_files_places_sources_into_manifest_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source_dir = folder / "sources"
            source_dir.mkdir()
            tablet_source = source_dir / "tablet_source.jpg"
            paper_source = source_dir / "paper_source.png"
            Image.new("RGB", (1080, 1920), "#1f2937").save(tablet_source)
            Image.new("RGB", (1080, 1920), "#f3efe7").save(paper_source)
            Image.new("RGBA", (780, 1100), (255, 255, 255, 255)).save(folder / "resume_overlay.png")
            (folder / "surface_fit.json").write_text(
                json.dumps(
                    {
                        "surfaces": [
                            {
                                "surface": "tablet",
                                "frame": "clean_tablet_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": {"tl": [160, 280], "tr": [940, 250], "br": [910, 1560], "bl": [140, 1510]},
                            },
                            {
                                "surface": "paper",
                                "frame": "clean_paper_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": {"tl": [160, 280], "tr": [940, 250], "br": [910, 1560], "bl": [140, 1510]},
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            pipeline.ingest_plate_files(
                argparse.Namespace(
                    run_id=None,
                    work_dir=str(folder),
                    manifest_name=None,
                    tablet_source=str(tablet_source),
                    paper_source=str(paper_source),
                    extract_time=2.0,
                    overwrite=False,
                    json_name=None,
                    host="192.168.2.10",
                    port=8798,
                )
            )

            self.assertTrue((folder / "clean_tablet_plate.png").exists())
            self.assertTrue((folder / "clean_paper_plate.png").exists())
            report = json.loads((folder / "plate_ingest_report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["passed"], report["blockers"])
            self.assertEqual([item["status"] for item in report["results"]], ["written", "written"])
            self.assertIn("surface-fit-review", "\n".join(report["nextCommands"]))

    def test_gold_readiness_can_report_ready_for_final_codex_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            Image.new("RGB", (1080, 1920), "#d6d3d1").save(folder / "clean_tablet_plate.png")
            Image.new("RGBA", (780, 1100), (255, 255, 255, 255)).save(folder / "resume_overlay.png")
            (folder / "surface_fit.json").write_text(
                json.dumps(
                    {
                        "surfaces": [
                            {
                                "surface": "tablet",
                                "frame": "clean_tablet_plate.png",
                                "overlay": "resume_overlay.png",
                                "corners": {"tl": [160, 280], "tr": [940, 250], "br": [910, 1560], "bl": [140, 1510]},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            for gate in ("creative_gate", "script_qa", "creative_qa", "plate_qa", "surface_fit_qa", "voice_qa"):
                write_quality_gate(folder, gate, {"passed": True, "blockers": []})
            (folder / "abby_voice_full.mp3").write_bytes(b"voice placeholder")
            (folder / "signal_gold_surface_teardown_v1.mp4").write_bytes(b"video placeholder")
            (folder / "signal_gold_surface_teardown_v1_contact_sheet.png").write_bytes(b"sheet placeholder")

            pipeline.gold_readiness(
                argparse.Namespace(
                    run_id=None,
                    work_dir=str(folder),
                    manifest_name=None,
                    audio_name=None,
                    final_name=None,
                    contact_sheet_name=None,
                    json_name=None,
                    md_name=None,
                )
            )

            report = json.loads((folder / "gold_readiness_report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["readyForFinalCodexReview"], report["blockers"])
            self.assertEqual(report["blockers"], [])

    def test_gold_readiness_for_screen_teardown_ignores_surface_plate_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "resume_brief.json").write_text(
                json.dumps({"format": "screen_recording_teardown"}),
                encoding="utf-8",
            )
            for gate in ("creative_gate", "script_qa", "screen_visual_qa", "voice_qa"):
                write_quality_gate(folder, gate, {"passed": True, "blockers": []})
            (folder / "abby_voice_full.mp3").write_bytes(b"voice placeholder")
            (folder / "signal_gold_screen_teardown_jordan_v1.mp4").write_bytes(b"video placeholder")
            (folder / "signal_gold_screen_teardown_jordan_v1_contact_sheet.png").write_bytes(b"sheet placeholder")

            pipeline.gold_readiness(
                argparse.Namespace(
                    run_id=None,
                    work_dir=str(folder),
                    manifest_name=None,
                    audio_name=None,
                    final_name=None,
                    contact_sheet_name=None,
                    json_name=None,
                    md_name=None,
                )
            )

            report = json.loads((folder / "gold_readiness_report.json").read_text(encoding="utf-8"))
            self.assertTrue(report["readyForFinalCodexReview"], report["blockers"])
            self.assertEqual(report["format"], "screen_recording_teardown")
            self.assertNotIn("plate_qa", report["gates"])


if __name__ == "__main__":
    unittest.main()
