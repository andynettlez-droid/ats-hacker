import unittest
from datetime import datetime, timedelta, timezone

from marketing_agent.social_metrics_collector import (
    collect_candidates,
    collect_metrics,
    merge_metrics,
    snapshot_window,
)


class SocialMetricsCollectorTests(unittest.TestCase):
    def test_snapshot_windows(self):
        self.assertEqual(snapshot_window(1.9), "early")
        self.assertEqual(snapshot_window(2), "2h")
        self.assertEqual(snapshot_window(25), "24h")
        self.assertEqual(snapshot_window(80), "72h")

    def test_collects_successful_post_results(self):
        posts = [
            {
                "title": "Test",
                "file": "videos/test.mp4",
                "postedAt": "2026-07-09T10:00:00Z",
                "landingUrl": "https://example.test/?utm_content=video-123&utm_source=youtube",
                "uploadStatus": {
                    "results": [
                        {"platform": "youtube", "success": True, "post_url": "https://youtu.be/abc", "platform_post_id": "abc"},
                        {"platform": "tiktok", "success": False, "post_url": "https://tiktok.test/nope"},
                    ]
                },
            }
        ]
        candidates = collect_candidates(posts)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["utmContent"], "video-123")

    def test_normalizes_and_preserves_history(self):
        now = datetime(2026, 7, 9, 14, tzinfo=timezone.utc)
        candidate = {
            "title": "Test",
            "file": "videos/test.mp4",
            "platform": "youtube",
            "postUrl": "https://youtu.be/abc",
            "platformPostId": "abc",
            "publishedAt": (now - timedelta(hours=4)).isoformat(),
            "utmContent": "video-123",
        }
        records = collect_metrics([candidate], lambda _url: {"view_count": 100, "like_count": 8, "comment_count": 2}, now)
        self.assertEqual(records[0]["window"], "2h")
        self.assertEqual(records[0]["engagementRate"], 0.1)
        self.assertIsNone(records[0]["shares"])
        merged = merge_metrics({}, records)
        self.assertEqual(merged["youtube:videos/test.mp4"]["views"], 100)
        self.assertEqual(len(merged["youtube:videos/test.mp4"]["history"]), 1)

    def test_records_lookup_failure_without_zeroing_metrics(self):
        candidate = {"file": "videos/test.mp4", "platform": "instagram", "postUrl": "https://instagram.test/x"}

        def fail(_url):
            raise RuntimeError("login required")

        records = collect_metrics([candidate], fail)
        self.assertEqual(records[0]["error"], "login required")
        self.assertEqual(merge_metrics({"instagram:videos/test.mp4": {"views": 7}}, records)["instagram:videos/test.mp4"]["views"], 7)


if __name__ == "__main__":
    unittest.main()
