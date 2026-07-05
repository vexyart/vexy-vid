"""Tests for encoder selection config — the pure decision logic, no ffmpeg run.

this_file: tests/test_encoder.py
"""

from vexy_vid.encoder import HardwareEncoderDetector, get_encoder_detector


class TestEncoderConfig:
    def setup_method(self):
        self.detector = HardwareEncoderDetector()

    def test_nvenc_quality_uses_high_preset(self):
        cfg = self.detector.get_encoder_config("hevc_nvenc", quality=2)
        assert cfg["codec"] == "hevc_nvenc"
        assert cfg["preset"] == "p7"

    def test_nvenc_fast_uses_low_latency(self):
        cfg = self.detector.get_encoder_config("h264_nvenc", quality=0)
        assert cfg["preset"] == "p1"
        assert cfg["tune"] == "ll"

    def test_libx264_balanced_default(self):
        cfg = self.detector.get_encoder_config("libx264", quality=1)
        assert cfg == {"codec": "libx264", "preset": "medium", "crf": "20"}

    def test_qsv_quality_slow_preset(self):
        cfg = self.detector.get_encoder_config("hevc_qsv", quality=2)
        assert cfg["preset"] == "slow"

    def test_unknown_encoder_returns_codec_only(self):
        cfg = self.detector.get_encoder_config("mystery_codec", quality=1)
        assert cfg == {"codec": "mystery_codec"}


class TestDetectorSingleton:
    def test_get_encoder_detector_is_cached(self):
        assert get_encoder_detector() is get_encoder_detector()
