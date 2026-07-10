import copy
import json
from pathlib import Path
import tempfile
import unittest

from marketing_agent import creative_council as council


WEAK_LINE = "Monitored security alerts and helped with investigations."
REWRITE = "Triaged 28 weekly phishing tickets in Splunk and documented escalation notes."
CTA = "Need yours fixed? Link below."

RESUME_BRIEF = {
    "format": "screen_recording_teardown",
    "candidateName": "Lena Brooks",
    "targetRole": "Junior Cybersecurity Analyst",
    "weakBullet": WEAK_LINE,
    "weakReason": "The line hides the searchable tools, ticket volume, and analyst work.",
    "hiddenProof": "28 phishing tickets a week, Splunk alerts, disabled accounts",
    "rewrite": REWRITE,
    "cta": CTA,
    "searchTerms": [
        "Splunk",
        "phishing tickets",
        "account lockouts",
        "incident notes",
    ],
    "targetJobLanguage": [
        "Splunk",
        "phishing tickets",
        "account lockouts",
        "incident notes",
    ],
    "summary": "Junior cybersecurity analyst with phishing triage and Splunk alert review experience.",
    "skills": ["Splunk", "Phishing Triage", "Account Lockouts", "Incident Notes"],
    "existingBullets": [
        "Reviewed Splunk alerts for account lockouts, suspicious sign-ins, and phishing reports.",
        "Triaged 28 phishing tickets a week, disabled compromised accounts, and documented escalation notes.",
    ],
    "proofLines": [
        "28 phishing tickets a week",
        "Splunk alerts",
        "disabled compromised accounts",
    ],
}


def script_with_reaction(reaction: str) -> str:
    return (
        "Lena's applying for junior cybersecurity analyst. "
        "I'm checking for Splunk, phishing tickets, account lockouts, and incident notes. "
        f'Her resume says, "{WEAK_LINE}" '
        f"{reaction} "
        "The proof is lower down: 28 phishing tickets a week, Splunk alerts, disabled accounts. "
        f'Replace it with: "{REWRITE}" '
        f"{CTA}"
    )


VALID_SCRIPTS = [
    script_with_reaction("Too vague."),
    script_with_reaction("Sounds professional. Still too vague."),
    script_with_reaction("That sounds safe, but it says almost nothing."),
    script_with_reaction("It is not wrong. It is just too blurry."),
    script_with_reaction("That line hides the work a recruiter needs."),
]

APPROVED_EXAMPLES = f'''# Approved Human Reviewer Script Examples

## Example 1 - Cybersecurity Analyst

"Lena is applying for junior cybersecurity. Her resume says, '{WEAK_LINE}'
The proof is lower down. Replace it with: '{REWRITE}' {CTA}"

### Why This Passes

- It follows the human reviewer proof flow.
'''


class CreativeCouncilTests(unittest.TestCase):
    def write_run(
        self,
        folder: Path,
        scripts: list[str],
        selected_option: int = 1,
        brief: dict | None = None,
        exceptions: dict[int, str] | None = None,
    ) -> Path:
        exceptions = exceptions or {}
        blocks = []
        for number, script in enumerate(scripts, start=1):
            exception = (
                f"\n\nWord Count Exception: {exceptions[number]}"
                if number in exceptions
                else ""
            )
            blocks.append(
                f"## Option {number} - Variant {number}\n\n"
                f"{script}{exception}\n\n"
                "### Read-Aloud Review\n\n"
                "Pass candidate; council still decides."
            )
        (folder / "script_options.md").write_text("\n\n".join(blocks), encoding="utf-8")

        selected_exception = (
            f"\n\nWord Count Exception: {exceptions[selected_option]}"
            if selected_option in exceptions
            else ""
        )
        (folder / "selected_script.md").write_text(
            "# Selected Production Script\n\n"
            "## Voiceover Script\n\n"
            f"{scripts[selected_option - 1]}{selected_exception}\n\n"
            "## Why This Passes\n\n"
            "The council report is the source of truth.",
            encoding="utf-8",
        )
        (folder / "resume_brief.json").write_text(
            json.dumps(brief or RESUME_BRIEF, indent=2),
            encoding="utf-8",
        )
        approved_path = folder / "approved_human_reviewer_examples.md"
        approved_path.write_text(APPROVED_EXAMPLES, encoding="utf-8")
        return approved_path

    def test_five_valid_options_pass_and_selected_file_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            approved_path = self.write_run(folder, VALID_SCRIPTS, selected_option=3)

            report = council.review_creative_council(folder, approved_path)

            self.assertTrue(report["passed"])
            self.assertEqual(report["decision"], "PASS")
            self.assertEqual(report["selected_option"], 3)
            self.assertEqual(report["passing_options"], [1, 2, 3, 4, 5])
            self.assertTrue(all(option["passed"] for option in report["options"]))

            json_path = folder / "creative_council_review.json"
            markdown_path = folder / "creative_council_review.md"
            self.assertTrue(json_path.exists())
            self.assertTrue(markdown_path.exists())
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), report)
            self.assertIn("**Verdict:** PASS", markdown_path.read_text(encoding="utf-8"))

            first_json = json_path.read_bytes()
            first_markdown = markdown_path.read_bytes()
            council.review_creative_council(folder, approved_path)
            self.assertEqual(json_path.read_bytes(), first_json)
            self.assertEqual(markdown_path.read_bytes(), first_markdown)

    def test_all_failed_options_select_none_and_list_banned_phrase(self) -> None:
        bad_scripts = [
            script.replace(CTA, "Same person. Better signal.") for script in VALID_SCRIPTS
        ]
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            approved_path = self.write_run(folder, bad_scripts, selected_option=2)

            report = council.review_creative_council(folder, approved_path)

            self.assertFalse(report["passed"])
            self.assertIsNone(report["selected_option"])
            self.assertEqual(report["passing_options"], [])
            self.assertIn("All five options failed", report["selection_reason"])
            self.assertTrue(
                all(not option["checks"]["banned_phrases"]["passed"] for option in report["options"])
            )
            self.assertTrue(
                any(
                    "same person, better signal" in reason
                    for reason in report["options"][0]["rejection_reasons"]
                )
            )

    def test_invented_metric_and_tool_fail_evidence_fidelity(self) -> None:
        bad_rewrite = (
            "Triaged 99 weekly phishing tickets in Tableau and documented escalation notes."
        )
        brief = copy.deepcopy(RESUME_BRIEF)
        brief["rewrite"] = bad_rewrite
        scripts = [script.replace(REWRITE, bad_rewrite) for script in VALID_SCRIPTS]

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            approved_path = self.write_run(folder, scripts, brief=brief)

            report = council.review_creative_council(folder, approved_path)

            self.assertIsNone(report["selected_option"])
            evidence = report["options"][0]["checks"]["evidence_fidelity"]
            self.assertFalse(evidence["passed"])
            self.assertTrue(any("99" in reason for reason in evidence["reasons"]))
            self.assertTrue(any("tableau" in reason for reason in evidence["reasons"]))

    def test_explicit_specific_exception_allows_earned_long_read(self) -> None:
        long_script = VALID_SCRIPTS[0].replace(
            "The proof is lower down:",
            "Honestly, the useful experience is already sitting right there. The proof is lower down:",
        )
        self.assertGreater(council.count_words(long_script), council.TARGET_MAX_WORDS)

        without_exception = council.evaluate_script(long_script, RESUME_BRIEF)
        with_exception = council.evaluate_script(
            long_script,
            RESUME_BRIEF,
            exception_reason=(
                "The complete source proof needs one extra spoken beat for a natural read."
            ),
        )
        self.assertFalse(without_exception["checks"]["word_count"]["passed"])
        self.assertTrue(with_exception["passed"])
        self.assertTrue(with_exception["checks"]["word_count"]["exception_used"])

        scripts = [long_script, *VALID_SCRIPTS[1:]]
        reason = "The complete source proof needs one extra spoken beat for a natural read."
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            approved_path = self.write_run(
                folder,
                scripts,
                selected_option=1,
                exceptions={1: reason},
            )
            report = council.review_creative_council(folder, approved_path)
            self.assertTrue(report["passed"])
            self.assertEqual(report["selected_option"], 1)
            self.assertTrue(report["options"][0]["checks"]["word_count"]["exception_used"])

    def test_flow_order_and_missing_cta_are_independent_failures(self) -> None:
        normal = VALID_SCRIPTS[0]
        proof_sentence = (
            "The proof is lower down: 28 phishing tickets a week, Splunk alerts, disabled accounts. "
        )
        broken_order = normal.replace(proof_sentence, "")
        weak_sentence = f'Her resume says, "{WEAK_LINE}" '
        broken_order = broken_order.replace(weak_sentence, proof_sentence + weak_sentence)

        order_review = council.evaluate_script(broken_order, RESUME_BRIEF)
        self.assertFalse(order_review["checks"]["human_spoken_flow"]["passed"])
        self.assertTrue(
            any(
                "weak line must come before proof" in reason
                for reason in order_review["checks"]["human_spoken_flow"]["reasons"]
            )
        )

        missing_cta = normal.replace(CTA, "That is the stronger line.")
        cta_review = council.evaluate_script(missing_cta, RESUME_BRIEF)
        self.assertFalse(cta_review["checks"]["cta"]["passed"])
        self.assertTrue(any("CTA" in reason for reason in cta_review["checks"]["cta"]["reasons"]))

    def test_believable_mistake_rejects_cartoon_first_person_line(self) -> None:
        cartoon_line = "I did stuff and worked hard."
        brief = copy.deepcopy(RESUME_BRIEF)
        brief["weakBullet"] = cartoon_line
        script = VALID_SCRIPTS[0].replace(WEAK_LINE, cartoon_line)

        review = council.evaluate_script(script, brief)

        mistake_check = review["checks"]["believable_mistake"]
        self.assertFalse(mistake_check["passed"])
        self.assertTrue(any("cartoonishly bad" in reason for reason in mistake_check["reasons"]))
        self.assertTrue(any("first-person" in reason for reason in mistake_check["reasons"]))


if __name__ == "__main__":
    unittest.main()
