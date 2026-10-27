import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from forge_video import (RenderSpec, analyze_probe, build_render_command,
                         build_video_filter, parse_quality_intervals,
                         quality_scan, require_binary)


class ForgeVideoTests(unittest.TestCase):
    def test_filter_normalizes_vertical_video(self):
        spec = RenderSpec(Path('in.mp4'), Path('out.mp4'))
        vf = build_video_filter(spec)
        self.assertIn('scale=1080:1920', vf)
        self.assertIn('crop=1080:1920', vf)
        self.assertIn('setsar=1', vf)
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

    def test_probe_rejects_non_square_pixels(self):
        report = analyze_probe({'streams': [
            {'codec_type': 'video', 'codec_name': 'h264', 'pix_fmt': 'yuv420p',
             'sample_aspect_ratio': '3491:3492', 'width': 1080, 'height': 1920,
             'avg_frame_rate': '30/1'}], 'format': {'duration': '2'}})
        self.assertFalse(report['ok'])
        self.assertTrue(any('square pixels' in err for err in report['errors']))

    def test_4k_vertical_is_supported_without_changing_default(self):
        spec = RenderSpec(Path('in.mp4'), Path('out.mp4'), width=2160, height=3840)
        self.assertIn('scale=2160:3840', build_video_filter(spec))
        payload = {'streams': [
            {'codec_type': 'video', 'codec_name': 'h264', 'pix_fmt': 'yuv420p',
             'width': 2160, 'height': 3840, 'avg_frame_rate': '30/1'}],
            'format': {'duration': '45.0'}}
        self.assertTrue(analyze_probe(payload)['ok'])

    def test_owned_runtime_env_override(self):
        with tempfile.TemporaryDirectory() as td:
            binary = Path(td) / 'ffmpeg'
            binary.write_text('#!/bin/sh\nexit 0\n')
            binary.chmod(0o755)
            with mock.patch('shutil.which', return_value=None), mock.patch.dict(os.environ, {'SATISFYFORGE_FFMPEG': str(binary)}):
                self.assertEqual(require_binary('ffmpeg'), str(binary))

    def test_quality_parser_detects_black_freeze_and_silence(self):
        log = '''
        [blackdetect @ x] black_start:1.2 black_end:2.5 black_duration:1.3
        [freezedetect @ x] lavfi.freezedetect.freeze_start: 3.0
        [freezedetect @ x] lavfi.freezedetect.freeze_end: 5.4
        [silencedetect @ x] silence_start: 6.2
        [silencedetect @ x] silence_end: 8.5 | silence_duration: 2.3
        '''
        report = parse_quality_intervals(log)
        self.assertEqual(report['black'][0]['duration'], 1.3)
        self.assertAlmostEqual(report['freeze'][0]['duration'], 2.4)
        self.assertAlmostEqual(report['silence'][0]['duration'], 2.3)

    def test_unpaired_quality_events_are_not_misreported(self):
        report = parse_quality_intervals('silence_start: 4\nfreeze_start: 8')
        self.assertEqual(report, {'black': [], 'freeze': [], 'silence': []})
        eof = parse_quality_intervals('freeze_start: 0\nsilence_start: 4', duration_seconds=10)
        self.assertEqual(eof['freeze'][0]['duration'], 10)
        self.assertEqual(eof['silence'][0]['duration'], 6)

    @mock.patch('forge_video.probe_file')
    @mock.patch('forge_video.subprocess.run')
    def test_quality_scan_warns_and_strict_mode_fails(self, run, probe):
        probe.side_effect = lambda *args, **kwargs: {
            'ok': True, 'errors': [], 'warnings': [],
            'facts': {'has_audio': False, 'duration_seconds': 10},
        }
        run.return_value = mock.Mock(returncode=0, stderr=(
            '[blackdetect @ x] black_start:1 black_end:2 black_duration:1'))
        with mock.patch('forge_video.require_binary', return_value='ffmpeg'):
            report = quality_scan(Path('input.mp4'))
            strict = quality_scan(Path('input.mp4'), strict=True)
        self.assertTrue(report['ok'])
        self.assertEqual(len(report['warnings']), 1)
        self.assertFalse(strict['ok'])
        self.assertIn('Strict quality gate', strict['errors'][0])

    @mock.patch('forge_video.probe_file')
    @mock.patch('forge_video.subprocess.run')
    def test_quality_scan_checks_silence_when_audio_exists(self, run, probe):
        probe.return_value = {
            'ok': True, 'errors': [], 'warnings': [],
            'facts': {'has_audio': True, 'duration_seconds': 10},
        }
        run.return_value = mock.Mock(returncode=0, stderr='')
        with mock.patch('forge_video.require_binary', return_value='ffmpeg'):
            report = quality_scan(Path('input.mp4'))
        self.assertTrue(report['ok'])
        self.assertEqual(run.call_count, 2)
        self.assertTrue(any('silencedetect' in arg for arg in run.call_args_list[1].args[0]))


if __name__ == '__main__':
    unittest.main()
