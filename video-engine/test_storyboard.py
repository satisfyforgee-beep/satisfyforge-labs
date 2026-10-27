import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from storyboard import (check_voiceover_duration, prepare_plan, render_story,
                        scene_command)


def example():
    return {
        "title": "Research mystery: documented facts vs theories",
        "claims": [
            {"id": "agency", "text": "Official agency mission", "kind": "verified",
             "source_url": "https://www.darpa.mil/"},
            {"id": "unknown", "text": "A hypothetical question", "kind": "speculation"},
        ],
        "voiceover": "narration.wav",
        "captions": "captions.srt",
        "scenes": [
            {"id": "hook", "asset": "clips/opening.mp4", "license": "owned",
             "rights_note": "Original studio B-roll", "duration_seconds": 3,
             "visual_direction": "Fast opening, clean light and movement", "narration": "What do we know?",
             "claim_ids": ["agency"]},
            {"id": "question", "asset": "stills/illustration.png", "license": "licensed",
             "rights_note": "Permission retained", "duration_seconds": 4,
             "visual_direction": "Gentle moving crop", "narration": "What is speculation?",
             "claim_ids": ["unknown"], "uncertainty_disclosure": "Illustration, not evidence"},
        ],
    }


class StoryboardTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.manifest = self.base / "story.json"
        self.data = example()

    def save(self):
        self.manifest.write_text(json.dumps(self.data), encoding="utf-8")

    def test_plan_requires_facts_rights_and_disclosure(self):
        self.save()
        plan = prepare_plan(self.manifest)
        self.assertEqual(plan["duration_seconds"], 7)
        self.assertEqual(plan["scene_count"], 2)
        self.assertFalse(plan["rendered"])
        self.assertEqual(plan["timeline"][1]["start_seconds"], 3)
        self.assertEqual(plan["claims"][0]["source_url"], "https://www.darpa.mil/")
        self.data["scenes"][1].pop("uncertainty_disclosure")
        self.save()
        with self.assertRaisesRegex(ValueError, "disclosure"):
            prepare_plan(self.manifest)
        self.data["scenes"][1]["uncertainty_disclosure"] = "Hypothetical"
        self.data["scenes"][0].pop("rights_note")
        self.save()
        with self.assertRaisesRegex(ValueError, "rights"):
            prepare_plan(self.manifest)

    def test_reject_escaped_path_and_bad_durations(self):
        self.data["scenes"][0]["asset"] = "../../private-video.mp4"
        self.save()
        with self.assertRaisesRegex(ValueError, "escapes"):
            prepare_plan(self.manifest)
        self.data["scenes"][0]["asset"] = "clips/opening.mp4"
        self.data["scenes"][0]["duration_seconds"] = float("nan")
        self.save()
        with self.assertRaisesRegex(ValueError, "1–30"):
            prepare_plan(self.manifest)

    def test_no_fake_local_asset_and_unverified_source_claim(self):
        self.save()
        with self.assertRaises(FileNotFoundError):
            prepare_plan(self.manifest, require_files=True)
        self.data["claims"][0].pop("source_url")
        self.save()
        with self.assertRaisesRegex(ValueError, "HTTPS source"):
            prepare_plan(self.manifest)

    def test_scene_commands_keep_audio_out_of_assets(self):
        video = scene_command("ffmpeg", Path("footage.mp4"), Path("segment.mp4"), 2.5,
                              width=1080, height=1920)
        image = scene_command("ffmpeg", Path("photo.png"), Path("still.mp4"), 2.5,
                              width=2160, height=3840)
        self.assertIn("-stream_loop", video)
        self.assertIn("-loop", image)
        self.assertTrue(any("scale=2160:3840" in part for part in image))
        self.assertIn("-an", video)

    def test_voiceover_length_gate(self):
        completed = mock.Mock(stdout='{"format":{"duration":"7.2"}}')
        with mock.patch("storyboard.require_binary", return_value="ffprobe"), \
             mock.patch("storyboard.subprocess.run", return_value=completed):
            check_voiceover_duration(Path("narration.wav"), 7)
            with self.assertRaisesRegex(ValueError, "does not match"):
                check_voiceover_duration(Path("narration.wav"), 12)

    def test_render_does_not_publish(self):
        for filename in ("clips/opening.mp4", "stills/illustration.png", "narration.wav", "captions.srt"):
            path = self.base / "assets" / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        self.save()
        fake_qa = {"ok": True, "facts": {"codec": "h264"}}
        with mock.patch("storyboard.require_binary", return_value="ffmpeg"), \
             mock.patch("storyboard.check_voiceover_duration"), \
             mock.patch("storyboard.subprocess.run") as runner, \
             mock.patch("storyboard.render", return_value=fake_qa):
            result = render_story(self.manifest, self.base / "preview.mp4")
        self.assertTrue(result["rendered"])
        self.assertFalse(result["publication_authorized"])
        self.assertEqual(runner.call_count, 3)  # two cuts + one local concat

    @unittest.skipUnless(os.environ.get("SF_RUN_VIDEO_INTEGRATION") == "1"
                         and shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Optional real FFmpeg smoke; run with SF_RUN_VIDEO_INTEGRATION=1")
    def test_real_two_scene_media_assembly(self):
        """Generates synthetic test media in a temp directory, never a public post."""
        assets = self.base / "assets"
        assets.mkdir()
        moving = assets / "opening.mp4"
        still = assets / "illustration.png"
        narration = assets / "narration.wav"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "testsrc2=size=160x284:rate=30:duration=1", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", str(moving)], check=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "color=c=blue:size=160x284:rate=1", "-frames:v", "1", str(still)], check=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                        "-i", "sine=frequency=330:duration=2", str(narration)], check=True)
        self.data["scenes"][0]["asset"] = moving.name
        self.data["scenes"][1]["asset"] = still.name
        self.data["scenes"][0]["duration_seconds"] = 1
        self.data["scenes"][1]["duration_seconds"] = 1
        self.data.pop("captions")
        self.save()
        output = self.base / "smoke.mp4"
        result = render_story(self.manifest, output)
        self.assertTrue(output.is_file())
        self.assertTrue(result["technical_qa"]["ok"])
        self.assertTrue(1.5 < result["technical_qa"]["facts"]["duration_seconds"] < 2.5)


if __name__ == "__main__":
    unittest.main()
