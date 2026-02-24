"""Utility functions for video processing."""

import sys
import re
import json
import hashlib
from pathlib import Path
from typing import Any, Optional

import ffmpeg
import numpy as np
from loguru import logger

from vexy_vid.constants import ANALYSIS_FRAME_WIDTH, CACHE_DIR


def parse_dimension(value: str | int | float | None, reference: int, is_trim: bool = False) -> int:
    """
    Parse dimension value which can be pixels or percentage.

    Args:
        value: Dimension value (int/float for pixels, str with % for percentage)
        reference: Reference dimension (width or height)
        is_trim: If True, value represents pixels to remove

    Returns:
        Calculated dimension in pixels
    """
    if value is None:
        return 0 if is_trim else reference

    # Handle percentage
    if isinstance(value, str) and value.endswith("%"):
        percentage = float(value.rstrip("%"))
        pixels = int(reference * percentage / 100)
        return pixels

    # Handle absolute pixels
    return int(value)


def _parse_dim_component(component: str, reference: int) -> int:
    """
    Parse a single dimension component (width or height) from a size spec.

    Args:
        component: Dimension string — pixels ("1280"), percentage ("50%"), or empty
        reference: Original dimension in pixels for percentage calculation

    Returns:
        Resolved dimension in pixels
    """
    if not component:
        return reference  # Empty means 100% of original
    if component.endswith("%"):
        return int(reference * float(component.rstrip("%")) / 100)
    return int(component)


def parse_size(size_spec: str, orig_width: int, orig_height: int) -> tuple[int, int]:
    """
    Parse a size specification into (width, height) in pixels.

    Supported formats:
        RATIO:                16:9           — crop to aspect ratio
        PIXELSxPIXELS:        1280x720       — exact pixel dimensions
        PERCENT%xPERCENT%:    50%x50%        — percentage of original
        WIDTHx:               1280x / 50%x   — width only, height=100%
        xHEIGHT:              x720  / x50%   — height only, width=100%
        MIXED:                1280x50% / 50%x720

    Args:
        size_spec: Size specification string
        orig_width: Original video width
        orig_height: Original video height

    Returns:
        Tuple of (target_width, target_height) in pixels

    Raises:
        ValueError: If spec format is unrecognized
    """
    spec = size_spec.strip()

    # Ratio format: "16:9"
    if ":" in spec and "x" not in spec.lower():
        parts = spec.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid ratio format: {spec!r} (expected W:H)")
        ratio_w, ratio_h = float(parts[0]), float(parts[1])
        target_ratio = ratio_w / ratio_h
        orig_ratio = orig_width / orig_height
        if target_ratio > orig_ratio:
            # Wider target ratio — constrain by width, crop height
            return orig_width, int(orig_width / target_ratio)
        else:
            # Taller target ratio — constrain by height, crop width
            return int(orig_height * target_ratio), orig_height

    # Pixel / percent / mixed format: split on 'x' (case-insensitive)
    if "x" in spec.lower():
        idx = spec.lower().index("x")
        w_part = spec[:idx]
        h_part = spec[idx + 1 :]
        target_w = _parse_dim_component(w_part, orig_width)
        target_h = _parse_dim_component(h_part, orig_height)
        return target_w, target_h

    raise ValueError(
        f"Unrecognized size format: {spec!r}. "
        f"Expected RATIO (16:9), WxH (1280x720), or percent (50%x50%)"
    )


def get_video_info(input_path: str) -> tuple[int, int]:
    """Get video dimensions."""
    try:
        probe = ffmpeg.probe(input_path)
        video_stream = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)
        if not video_stream:
            raise ValueError("No video stream found")

        width = int(video_stream["width"])
        height = int(video_stream["height"])
        return width, height
    except ffmpeg.Error as e:
        logger.error(f"Error probing video: {e.stderr.decode()}")
        raise


def get_input_path(input: str | None = None) -> str:
    """Get input path from argument or stdin."""
    if input:
        return input

    # Read from stdin
    try:
        path = sys.stdin.readline().strip()
        if not path:
            raise ValueError("No input provided via stdin")
        return path
    except Exception as e:
        logger.error(f"Failed to read from stdin: {e}")
        raise


def generate_output_path(input_path: str, operation: str, params: dict) -> str:
    """Generate intelligent output filename."""
    path = Path(input_path)
    stem = path.stem
    suffix = path.suffix

    # Build operation description
    parts = [stem, operation]

    if operation == "trim":
        for edge, value in params.items():
            if value and value != "0":
                parts.append(f"{edge[0]}{value}")
    elif operation == "crop":
        if "crop" in params and params["crop"]:
            parts.append(params["crop"].replace(":", "-").replace("%", "p"))
    new_name = "_".join(parts) + suffix
    return str(path.parent / new_name)


def validate_crop_parameters(
    width: int, height: int, top: int, bottom: int, left: int, right: int
) -> bool:
    """
    Validate that crop parameters are reasonable.

    Returns:
        True if parameters are valid
    """
    final_width = width - left - right
    final_height = height - top - bottom

    # Check dimensions are positive
    if final_width <= 0 or final_height <= 0:
        return False

    # Check we're not removing too much (more than 50% in any dimension)
    if final_width < width * 0.5 or final_height < height * 0.5:
        logger.warning("Crop would remove more than 50% of video")
        return False

    # Check aspect ratio isn't too distorted
    original_aspect = width / height
    new_aspect = final_width / final_height
    aspect_change = abs(new_aspect - original_aspect) / original_aspect

    if aspect_change > 0.3:  # More than 30% aspect ratio change
        logger.warning(
            f"Crop would significantly change aspect ratio: "
            f"{original_aspect:.2f} -> {new_aspect:.2f}"
        )

    return True


class VideoAnalysisCache:
    """Cache for video analysis results to avoid reprocessing."""

    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.cache_file = CACHE_DIR / "analysis_cache.json"
        self.cache = self._load_cache()

    def _load_cache(self) -> dict[str, Any]:
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception:
            pass

    def get_video_hash(self, video_path: str) -> str:
        """Generate hash for video file based on path and modification time."""
        stat = Path(video_path).stat()
        hash_input = f"{video_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def get(self, video_path: str, analysis_type: str) -> dict[str, Any] | None:
        """Get cached analysis results."""
        video_hash = self.get_video_hash(video_path)
        cache_key = f"{video_hash}:{analysis_type}"
        return self.cache.get(cache_key)

    def set(self, video_path: str, analysis_type: str, results: dict[str, Any]):
        """Cache analysis results."""
        video_hash = self.get_video_hash(video_path)
        cache_key = f"{video_hash}:{analysis_type}"
        self.cache[cache_key] = results
        self._save_cache()
