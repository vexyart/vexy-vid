"""Tests for size/dimension parsing and path helpers — the pure core of vexy-vid.

this_file: tests/test_utils.py
"""

import pytest

from vexy_vid.utils import (
    generate_output_path,
    parse_dimension,
    parse_size,
    validate_crop_parameters,
)


class TestParseDimension:
    def test_none_returns_reference_for_crop(self):
        assert parse_dimension(None, 1080, is_trim=False) == 1080

    def test_none_returns_zero_for_trim(self):
        assert parse_dimension(None, 1080, is_trim=True) == 0

    def test_absolute_pixels(self):
        assert parse_dimension(100, 1080) == 100

    def test_percentage_of_reference(self):
        assert parse_dimension("50%", 1080) == 540

    def test_percentage_string_pixels(self):
        assert parse_dimension("200", 1080) == 200


class TestParseSize:
    def test_exact_pixels(self):
        assert parse_size("1280x720", 1920, 1080) == (1280, 720)

    def test_percentage_pair(self):
        assert parse_size("50%x50%", 1920, 1080) == (960, 540)

    def test_single_percentage(self):
        assert parse_size("50%", 1920, 1080) == (960, 540)

    def test_width_only_keeps_height(self):
        assert parse_size("1280x", 1920, 1080) == (1280, 1080)

    def test_height_only_keeps_width(self):
        assert parse_size("x720", 1920, 1080) == (1920, 720)

    def test_mixed_pixels_and_percent(self):
        assert parse_size("1280x50%", 1920, 1080) == (1280, 540)

    def test_ratio_wider_than_source_constrains_width(self):
        # 21:9 is wider than 16:9 source → keep width, shrink height
        w, h = parse_size("21:9", 1920, 1080)
        assert w == 1920
        assert h == int(1920 / (21 / 9))

    def test_ratio_taller_than_source_constrains_height(self):
        # 4:3 is taller than 16:9 source → keep height, shrink width
        w, h = parse_size("4:3", 1920, 1080)
        assert h == 1080
        assert w == int(1080 * (4 / 3))

    def test_invalid_spec_raises(self):
        with pytest.raises(ValueError):
            parse_size("garbage", 1920, 1080)

    def test_invalid_ratio_raises(self):
        with pytest.raises(ValueError):
            parse_size("16:9:3", 1920, 1080)


class TestGenerateOutputPath:
    def test_crop_encodes_spec_in_name(self):
        out = generate_output_path("/tmp/clip.mp4", "crop", {"crop": "16:9"})
        assert out == "/tmp/clip_crop_16-9.mp4"

    def test_crop_percentage_spec(self):
        out = generate_output_path("/tmp/clip.mp4", "crop", {"crop": "50%x50%"})
        assert out == "/tmp/clip_crop_50px50p.mp4"

    def test_trim_encodes_edges(self):
        out = generate_output_path("/tmp/clip.mkv", "trim", {"top": "100", "left": "20"})
        assert out.startswith("/tmp/clip_trim_")
        assert out.endswith(".mkv")
        assert "t100" in out and "l20" in out

    def test_trim_skips_zero_edges(self):
        out = generate_output_path("/tmp/clip.mp4", "trim", {"top": "0", "bottom": "50"})
        assert "t0" not in out
        assert "b50" in out


class TestValidateCropParameters:
    def test_reasonable_crop_is_valid(self):
        assert validate_crop_parameters(1920, 1080, 40, 40, 0, 0) is True

    def test_half_remaining_is_valid_boundary(self):
        # Removing 270+270 leaves exactly 540 (50% of 1080) → still valid
        assert validate_crop_parameters(1920, 1080, 270, 270, 0, 0) is True

    def test_negative_final_dimension_invalid(self):
        assert validate_crop_parameters(1920, 1080, 700, 500, 0, 0) is False

    def test_removing_everything_invalid(self):
        assert validate_crop_parameters(1920, 1080, 1080, 0, 0, 0) is False

    def test_removing_more_than_half_invalid(self):
        assert validate_crop_parameters(1920, 1080, 0, 0, 1000, 1000) is False
