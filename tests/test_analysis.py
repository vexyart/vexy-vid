"""Tests for detection primitives — Numba kernels and OpenCV frame processors.

These run on synthetic in-memory frames, so no ffmpeg or sample video is needed.

this_file: tests/test_analysis.py
"""

import numpy as np

from vexy_vid.analysis import (
    calculate_row_luminance,
    count_bright_pixels_per_row,
    find_black_borders,
    process_frame_for_letterbox,
    process_frame_for_subtitles,
)


def _letterboxed_frame(height=120, width=160, bar=20, fill=180):
    """A gray frame with `bar` rows of black at top and bottom (BGR)."""
    frame = np.full((height, width, 3), fill, dtype=np.uint8)
    frame[:bar] = 0
    frame[height - bar :] = 0
    return frame


class TestNumbaKernels:
    def test_row_luminance_matches_numpy_mean(self):
        gray = np.arange(6 * 4, dtype=np.uint8).reshape(6, 4)
        means = calculate_row_luminance(gray)
        expected = gray.mean(axis=1).astype(np.float32)
        assert np.allclose(means, expected)

    def test_find_black_borders_detects_bars(self):
        gray = np.full((120, 4), 180.0, dtype=np.float32)
        gray[:20] = 0.0
        gray[-20:] = 0.0
        row_means = gray.mean(axis=1)
        top, bottom = find_black_borders(row_means, threshold=30)
        assert top == 20
        assert bottom == 20

    def test_find_black_borders_none_when_bright(self):
        row_means = np.full(120, 200.0, dtype=np.float32)
        assert find_black_borders(row_means, threshold=30) == (0, 0)

    def test_count_bright_pixels(self):
        gray = np.zeros((3, 10), dtype=np.uint8)
        gray[1, :7] = 255  # 7 bright pixels in row 1
        counts = count_bright_pixels_per_row(gray, threshold=200)
        assert list(counts) == [0, 7, 0]


class TestFrameProcessors:
    def test_process_frame_for_letterbox_finds_black_bars(self):
        top, bottom = process_frame_for_letterbox(_letterboxed_frame())
        assert top == 20
        assert bottom == 20

    def test_process_frame_for_letterbox_grayscale_input(self):
        gray = np.full((120, 160), 180, dtype=np.uint8)
        gray[:15] = 0
        top, bottom = process_frame_for_letterbox(gray)
        assert top == 15

    def test_process_frame_for_subtitles_no_text_returns_none(self):
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        assert process_frame_for_subtitles(frame) is None

    def test_process_frame_for_subtitles_detects_bright_band(self):
        frame = np.zeros((200, 320, 3), dtype=np.uint8)
        # A wide bright band low in the frame mimics a subtitle line.
        frame[175:185, 40:280] = 255
        top = process_frame_for_subtitles(frame)
        assert top is not None
        assert 150 < top < 190
