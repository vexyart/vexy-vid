"""End-to-end tests that exercise the real ffmpeg pipeline.

Every test here needs the ffmpeg binary and generates its own synthetic clip,
so the whole module is skipped cleanly when ffmpeg is not installed.

this_file: tests/test_integration.py
"""

import shutil
import subprocess

import pytest

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg binary not installed"
)


@pytest.fixture
def letterboxed_clip(tmp_path):
    """A 1-second 320x240 clip with 40px black bars top and bottom.

    Built by rendering a 320x160 color pattern and padding it to 320x240, which
    is exactly the letterbox shape the detector should recover.
    """
    out = tmp_path / "letterbox.mp4"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=size=320x160:rate=10:duration=1",
        "-vf",
        "pad=320:240:0:40:black",
        "-pix_fmt",
        "yuv420p",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    assert out.exists() and out.stat().st_size > 0
    return out


def test_probe_reports_padded_dimensions(letterboxed_clip):
    from vexy_vid.utils import get_video_info

    width, height = get_video_info(str(letterboxed_clip))
    assert (width, height) == (320, 240)


def test_ffmpeg_cropdetect_finds_bars(letterboxed_clip):
    from vexy_vid.analysis import detect_letterbox_ffmpeg

    x, y, crop_w, crop_h = detect_letterbox_ffmpeg(str(letterboxed_clip), duration=1)
    # The 40px bars should be detected: content height ~160, offset ~40.
    assert crop_w == 320
    assert 140 <= crop_h <= 180
    assert 30 <= y <= 50


def test_crop_command_writes_output(letterboxed_clip, tmp_path):
    from vexy_vid.crop import crop
    from vexy_vid.utils import get_video_info

    out = tmp_path / "cropped.mp4"
    crop(input=str(letterboxed_clip), output=str(out), crop="160x120", quality=0)
    assert out.exists() and out.stat().st_size > 0
    assert get_video_info(str(out)) == (160, 120)


def test_trim_letterbox_removes_bars(letterboxed_clip, tmp_path):
    from vexy_vid.trim import trim
    from vexy_vid.utils import get_video_info

    out = tmp_path / "trimmed.mp4"
    trim(input=str(letterboxed_clip), output=str(out), Letterbox=True, quality=0)
    assert out.exists() and out.stat().st_size > 0
    # The 40px bars top and bottom should be gone: 240 - 80 == 160.
    _, height = get_video_info(str(out))
    assert 150 <= height <= 170


def test_trim_explicit_edges(letterboxed_clip, tmp_path):
    from vexy_vid.trim import trim
    from vexy_vid.utils import get_video_info

    out = tmp_path / "edged.mp4"
    trim(input=str(letterboxed_clip), output=str(out), top="40", bottom="40", quality=0)
    assert get_video_info(str(out)) == (320, 160)


def test_extract_frame_fast_returns_array(letterboxed_clip):
    from vexy_vid.frames import extract_frame_fast

    frame = extract_frame_fast(str(letterboxed_clip), 0, downscale_width=160)
    assert frame is not None
    assert frame.shape[1] == 160  # downscaled width


def test_opencv_letterbox_pipeline(letterboxed_clip):
    from vexy_vid.analysis import detect_letterbox_opencv_parallel

    top, bottom = detect_letterbox_opencv_parallel(str(letterboxed_clip), sample_frames=4)
    # Bars are 40px at source scale; allow slack for median/rounding.
    assert top >= 20
    assert bottom >= 20
