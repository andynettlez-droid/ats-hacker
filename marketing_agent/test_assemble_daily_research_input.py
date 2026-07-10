import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from marketing_agent.assemble_daily_research_input import assemble


class AssembleDailyResearchInputTests(unittest.TestCase):
    def test_joins_review_and_requires_real_browser_capture(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            evidence = root / "instagram-person-abc"
            evidence.mkdir()
            sheet = evidence / "contact_sheet.png"
            sheet.write_bytes(b"png")
            review = {
                "sources": [
                    {
                        "platform_post_id": "abc",
                        "hook_0_3": "A specific hook",
                        "first_frame_observation": "A resume fills the frame.",
                        "beat_breakdown": [{"time": "0-3s", "beat": "Show the mistake"}],
                        "angle_id": "human-resume-teardown",
                        "observation_basis": {
                            "hook_0_3": "browser",
                            "first_frame_observation": "contact_sheet",
                            "beat_breakdown": "browser",
                        },
                    }
                ]
            }
            social = {
                "id": "abc",
                "webpage_url": "https://www.instagram.com/reel/abc/",
                "uploader": "person",
                "upload_date": "20260701",
            }
            records = assemble(
                [],
                [[social]],
                review,
                evidence_root=root,
                browser_observed_ids={"abc"},
                observed_at="2026-07-09T12:00:00Z",
            )
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["access_state"], "browser_observed")
            self.assertEqual(records[0]["screenshot_paths"], [str(sheet.resolve())])
            self.assertEqual(records[0]["beat_breakdown"][0]["start_sec"], 0.0)


if __name__ == "__main__":
    unittest.main()
