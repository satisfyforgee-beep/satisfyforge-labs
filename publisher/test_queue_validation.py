import unittest

import run


def item(item_id="story-v1", publish_at="2026-10-13T14:00:00Z"):
    return {
        "id": item_id,
        "publish_at": publish_at,
        "video_url": "https://cdn.example.com/story.mp4",
        "platforms": {
            "instagram": {
                "enabled": True,
                "caption": "Original factual story",
            }
        },
    }


class QueueValidationTests(unittest.TestCase):
    def test_valid_queue_passes(self):
        run.validate_queue({"items": [item()]})

    def test_duplicate_id_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate queue item id"):
            run.validate_queue({"items": [item(), item()]})

    def test_exact_duplicate_job_fails_closed(self):
        second = item(item_id="story-v2")
        with self.assertRaisesRegex(ValueError, "exact duplicate publish job"):
            run.validate_queue({"items": [item(), second]})

    def test_same_asset_at_different_time_is_allowed(self):
        second = item(item_id="story-v2", publish_at="2026-10-20T14:00:00Z")
        run.validate_queue({"items": [item(), second]})

    def test_timezone_is_required(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            run.validate_queue({"items": [item(publish_at="2026-10-13T14:00:00")]})

    def test_unsupported_platform_fails_closed(self):
        queued = item()
        queued["platforms"] = {"mystery_network": {"enabled": True}}
        with self.assertRaisesRegex(ValueError, "unsupported platform"):
            run.validate_queue({"items": [queued]})

    def test_no_enabled_platform_fails_closed(self):
        queued = item()
        queued["platforms"]["instagram"]["enabled"] = False
        with self.assertRaisesRegex(ValueError, "at least one platform"):
            run.validate_queue({"items": [queued]})


if __name__ == "__main__":
    unittest.main()
