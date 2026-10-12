import os
import unittest
from unittest.mock import Mock, patch

import run_v2


class FacebookAdapterTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "META_FB_PAGE_ID": "page-123",
            "META_FB_PAGE_ACCESS_TOKEN": "page-token",
            "META_GRAPH_VERSION": "v26.0",
        },
        clear=False,
    )
    @patch("run_v2.requests.post")
    def test_facebook_hosted_reel_flow(self, post):
        start = Mock(ok=True, status_code=200)
        start.json.return_value = {
            "video_id": "video-456",
            "upload_url": "https://upload.facebook.test/reel",
        }
        upload = Mock(ok=True, status_code=200)
        upload.json.return_value = {"success": True}
        finish = Mock(ok=True, status_code=200)
        finish.json.return_value = {"success": True}
        post.side_effect = [start, upload, finish]

        result = run_v2.publish_facebook(
            "https://example.com/video.mp4",
            {"caption": "Test Reel", "title": "Test"},
        )

        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["external_id"], "video-456")
        self.assertEqual(post.call_count, 3)
        self.assertIn("v26.0/page-123/video_reels", post.call_args_list[0].args[0])
        self.assertEqual(
            post.call_args_list[1].kwargs["headers"]["file_url"],
            "https://example.com/video.mp4",
        )
        self.assertEqual(
            post.call_args_list[2].kwargs["data"]["video_state"], "PUBLISHED"
        )

    @patch.dict(
        os.environ,
        {
            "META_FB_PAGE_ID": "page-123",
            "META_FB_PAGE_ACCESS_TOKEN": "page-token",
            "META_GRAPH_VERSION": "v26.0",
        },
        clear=False,
    )
    @patch("run_v2.requests.post")
    def test_incomplete_start_is_not_published(self, post):
        start = Mock(ok=True, status_code=200)
        start.json.return_value = {"video_id": "video-456"}
        post.return_value = start

        with self.assertRaises(run_v2.core.PublishError):
            run_v2.publish_facebook("https://example.com/video.mp4", {})
        self.assertEqual(post.call_count, 1)


if __name__ == "__main__":
    unittest.main()
