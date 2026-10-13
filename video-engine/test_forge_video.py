import unittest
from pathlib import Path

from forge_video import RenderSpec, analyze_probe, build_render_command, build_video_filter


class ForgeVideoTests(unittest.TestCase):
    def test_filter_normalizes_vertical_video(self):
        spec = RenderSpec(Path('in.mp4'), Path('out.mp4'))
        vf = build_video_filter(spec)
        self.assertIn('scale=1080:1920', vf)
        self.assertIn('crop=1080:1920', vf)
        self.assertIn('fps=30', vf)
        self.assertIn('format=yuv420p', vf)

    def test_voiceover_is_mapped_and_normalized(self):
        spec = RenderSpec(Path('in.mp4'), Path('out.mp4'), voiceover=Path('voice.wav'))
        cmd = build_render_command(spec)
        joined = ' '.join(cmd)
        self.assertIn('-map 1:a:0', joined)
        self.assertIn('loudnorm=I=-16:TP=-1.5:LRA=11', joined)
        self.assertIn('-shortest', cmd)

    def test_probe_passes_expected_publish_format(self):
        payload = {
            'streams': [
                {'codec_type': 'video', 'codec_name': 'h264', 'pix_fmt': 'yuv420p', 'width': 1080, 'height': 1920, 'avg_frame_rate': '30/1'},
                {'codec_type': 'audio', 'codec_name': 'aac'},
            ],
            'format': {'duration': '31.25'},
        }
        report = analyze_probe(payload)
        self.assertTrue(report['ok'])
        self.assertEqual(report['errors'], [])

    def test_probe_rejects_bad_frame_rate(self):
        payload = {
            'streams': [{'codec_type': 'video', 'codec_name': 'h264', 'pix_fmt': 'yuv420p', 'width': 1080, 'height': 1920, 'avg_frame_rate': '24000/1001'}],
            'format': {'duration': '20'},
        }
        report = analyze_probe(payload)
        self.assertFalse(report['ok'])
        self.assertTrue(any('frame rate' in err for err in report['errors']))


if __name__ == '__main__':
    unittest.main()
