import unittest

from marketing_agent.voice_lab import generate_voice_lab, normalize_alignment, prepare_voice_text, retime_words, score_take


class VoiceLabTests(unittest.TestCase):
    def test_prepares_known_pronunciation_risks(self):
        text = prepare_voice_text("Fix this resume for an ATS role using VPN and SQL.")
        self.assertIn("résumé", text)
        self.assertIn("A T S", text)
        self.assertIn("V P N", text)
        self.assertIn("S Q L", text)

    def test_normalizes_character_alignment(self):
        payload = {
            "normalized_alignment": {
                "characters": ["H", "i", " ", "A"],
                "character_start_times_seconds": [0, 0.1, 0.2, 0.3],
                "character_end_times_seconds": [0.1, 0.2, 0.3, 0.4],
            }
        }
        words = normalize_alignment(payload)
        self.assertEqual([item["word"] for item in words], ["Hi", "A"])

    def test_scores_natural_pacing_above_extreme_pacing(self):
        natural = [
            {"word": f"w{i}", "startSec": i * 0.36, "endSec": i * 0.36 + 0.2}
            for i in range(20)
        ]
        rushed = [
            {"word": f"w{i}", "startSec": i * 0.12, "endSec": i * 0.12 + 0.08}
            for i in range(20)
        ]
        self.assertGreater(score_take(natural).score, score_take(rushed).score)

    def test_retimes_alignment_for_mastered_creator_pace(self):
        words = [
            {"word": "one", "startSec": 0.0, "endSec": 0.4},
            {"word": "two", "startSec": 0.8, "endSec": 1.2},
        ]
        retimed = retime_words(words, 1.2)
        self.assertEqual(retimed[1]["startSec"], 0.667)
        self.assertEqual(retimed[1]["endSec"], 1.0)

    def test_voice_lab_defaults_do_not_force_time_compression(self):
        self.assertEqual(generate_voice_lab.__kwdefaults__["max_post_speed"], 1.0)
        self.assertEqual(generate_voice_lab.__kwdefaults__["target_wpm"], 145.0)


if __name__ == "__main__":
    unittest.main()
