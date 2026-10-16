import os
import unittest
from unittest.mock import patch

import run


def item(item_id="story-v1", publish_at="2026-10-13T14:00:00Z"):
    return {
        "id": item_id,
        "approved_for_direct_publish": True,
        "account_identity": "satisfyforge-business",
        "concept_key": item_id,
        "media_sha256": ("a" if item_id == "story-v1" else "b") * 64,
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
        run.validate_queue({"items": [item()]}, expected_account_identity="satisfyforge-business")

    def test_duplicate_id_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate queue item id"):
            run.validate_queue({"items": [item(), item()]})

    def test_exact_duplicate_job_fails_closed(self):
        second = item(item_id="story-v2")
        second["concept_key"] = "different-story"
        second["media_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "exact duplicate publish job"):
            run.validate_queue({"items": [item(), second]})

    def test_same_asset_at_different_time_fails_closed(self):
        second = item(item_id="story-v2", publish_at="2026-10-20T14:00:00Z")
        second["concept_key"] = "different-story"
        second["media_sha256"] = item()["media_sha256"]
        with self.assertRaisesRegex(ValueError, "duplicate queued media_sha256"):
            run.validate_queue({"items": [item(), second]})


    def test_concept_key_is_required(self):
        queued = item()
        queued["concept_key"] = ""
        with self.assertRaisesRegex(ValueError, "concept_key is required"):
            run.validate_queue({"items": [queued]})

    def test_media_sha256_is_required_and_valid(self):
        queued = item()
        queued["media_sha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "media_sha256"):
            run.validate_queue({"items": [queued]})

    def test_blocked_concept_fails_closed(self):
        queued = item()
        queued["concept_key"] = "Lake Nyos"
        history = {"blocked_concepts": ["lake-nyos"]}
        with self.assertRaisesRegex(ValueError, "permanently blocked"):
            run.validate_queue({"items": [queued]}, history=history)

    def test_completed_concept_fails_closed(self):
        queued = item()
        queued["concept_key"] = "First Computer Bug"
        history = {"completed_concepts": ["first-computer-bug"]}
        with self.assertRaisesRegex(ValueError, "already completed"):
            run.validate_queue({"items": [queued]}, history=history)

    def test_duplicate_queued_concept_fails_closed(self):
        first = item()
        second = item(item_id="story-v2", publish_at="2026-10-20T14:00:00Z")
        second["concept_key"] = first["concept_key"]
        second["media_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "duplicate queued concept"):
            run.validate_queue({"items": [first, second]})

    def test_completed_media_hash_fails_closed(self):
        queued = item()
        history = {"completed_media_sha256": [queued["media_sha256"]]}
        with self.assertRaisesRegex(ValueError, "media_sha256 is already completed"):
            run.validate_queue({"items": [queued]}, history=history)

    def test_explicit_item_approval_is_required(self):
        queued = item()
        queued["approved_for_direct_publish"] = False
        with self.assertRaisesRegex(ValueError, "approved_for_direct_publish"):
            run.validate_queue({"items": [queued]})

    def test_account_identity_is_required(self):
        queued = item()
        queued["account_identity"] = ""
        with self.assertRaisesRegex(ValueError, "account_identity is required"):
            run.validate_queue({"items": [queued]})

    def test_account_identity_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "does not match verified publisher identity"):
            run.validate_queue({"items": [item()]}, expected_account_identity="different-business")

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


class RuntimePublishGateTests(unittest.TestCase):
    def test_disabled_runtime_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(run.PublishError, "DIRECT_PUBLISHER_DISABLED"):
                run.require_runtime_publish_identity()

    def test_identity_verification_flag_is_required(self):
        with patch.dict(os.environ, {"SF_DIRECT_PUBLISHER_ENABLED": "true"}, clear=True):
            with self.assertRaisesRegex(run.PublishError, "PUBLISH_ACCOUNT_IDENTITY_NOT_VERIFIED"):
                run.require_runtime_publish_identity()

    def test_verified_identity_value_is_required(self):
        env = {
            "SF_DIRECT_PUBLISHER_ENABLED": "true",
            "SF_PUBLISH_ACCOUNT_IDENTITY_VERIFIED": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(run.PublishError, "PUBLISH_ACCOUNT_IDENTITY_MISSING"):
                run.require_runtime_publish_identity()

    def test_verified_runtime_returns_expected_identity(self):
        env = {
            "SF_DIRECT_PUBLISHER_ENABLED": "true",
            "SF_PUBLISH_ACCOUNT_IDENTITY_VERIFIED": "true",
            "SF_PUBLISH_ACCOUNT_IDENTITY": "satisfyforge-business",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(run.require_runtime_publish_identity(), "satisfyforge-business")


if __name__ == "__main__":
    unittest.main()
