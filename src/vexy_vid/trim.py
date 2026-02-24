"""Trim command — remove edges from video with automatic detection."""

import sys

from loguru import logger

from vexy_vid.analysis import (
    detect_letterbox_ffmpeg,
    detect_letterbox_opencv_parallel,
    detect_subtitles_brightness_fast,
    detect_subtitles_morphological_parallel,
)
from vexy_vid.encoder import process_video_with_hardware_encoding
from vexy_vid.utils import (
    generate_output_path,
    get_input_path,
    get_video_info,
    parse_dimension,
    parse_size,
    validate_crop_parameters,
)


def trim(
    input: str | None = None,
    output: str | None = None,
    top: str | int | None = None,
    right: str | int | None = None,
    bottom: str | int | None = None,
    left: str | int | None = None,
    scale: str | None = None,
    Letterbox: bool = False,
    subtitles: bool = False,
    quality: int = 1,
    verbose: bool = False,
) -> None:
    """
    Trim edges from video (like reversed CSS padding) with hardware acceleration.

    Args:
        input: Input video path (reads from stdin if not provided)
        output: Output video path (auto-generated if not provided)
        top: Pixels/percentage to remove from top
        right: Pixels/percentage to remove from right
        bottom: Pixels/percentage to remove from bottom
        left: Pixels/percentage to remove from left
        scale: Output size after trimming, as pixels or percentages (e.g., 1920x1080, 50%)
        Letterbox: Auto-detect and remove letterbox bars
        subtitles: Auto-detect and remove subtitle region
        quality: 0 (fast), 1 (balanced), 2 (quality)
        verbose: Enable verbose logging
    """
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    letterbox: bool = Letterbox

    input_path = get_input_path(input)
    logger.info(f"Processing: {input_path}")

    width, height = get_video_info(input_path)
    logger.debug(f"Original dimensions: {width}x{height}")

    letterbox_top = 0
    letterbox_bottom = 0
    subtitle_bottom = 0

    if letterbox:
        logger.info("Detecting letterbox bars...")
        _, y, crop_width, crop_height = detect_letterbox_ffmpeg(
            input_path, duration=60, verbose=verbose
        )
        if crop_width > 0 and crop_height > 0:
            letterbox_top = y
            letterbox_bottom = height - (y + crop_height)
            logger.info(
                f"Letterbox detected via FFmpeg: top={letterbox_top}, bottom={letterbox_bottom}"
            )
        else:
            letterbox_top, letterbox_bottom = detect_letterbox_opencv_parallel(
                input_path, sample_frames=10, verbose=verbose
            )
            if letterbox_top > 0 or letterbox_bottom > 0:
                logger.info(
                    f"Letterbox detected via OpenCV: top={letterbox_top}, bottom={letterbox_bottom}"
                )
            else:
                logger.warning("No letterbox detected")

    if subtitles:
        logger.info("Detecting subtitle region...")
        subtitle_bottom = detect_subtitles_morphological_parallel(
            input_path, sample_frames=20, verbose=verbose
        )
        if subtitle_bottom == 0:
            subtitle_bottom = detect_subtitles_brightness_fast(
                input_path, sample_frames=30, verbose=verbose
            )
        if subtitle_bottom > 0:
            logger.info(f"Subtitles detected: trim bottom {subtitle_bottom}px")
        else:
            logger.warning("No subtitles detected")

    trim_top = parse_dimension(top, height, is_trim=True)
    trim_bottom = parse_dimension(bottom, height, is_trim=True)
    trim_left = parse_dimension(left, width, is_trim=True)
    trim_right = parse_dimension(right, width, is_trim=True)

    trim_top = max(trim_top, letterbox_top)
    trim_bottom = max(trim_bottom, letterbox_bottom)

    if subtitle_bottom > 0:
        adjusted_height = height - letterbox_top - letterbox_bottom
        if subtitle_bottom > adjusted_height * 0.5:
            subtitle_bottom = int(adjusted_height * 0.3)
            logger.warning(f"Subtitle trim adjusted to {subtitle_bottom}px to preserve content")
        trim_bottom = max(trim_bottom, subtitle_bottom)

    if not validate_crop_parameters(width, height, trim_top, trim_bottom, trim_left, trim_right):
        logger.error("Invalid trim values - would result in unusable video")
        raise ValueError("Trim values too large or invalid")

    final_width = width - trim_left - trim_right
    final_height = height - trim_top - trim_bottom

    logger.info(
        f"Trimming: top={trim_top}, right={trim_right}, bottom={trim_bottom}, left={trim_left}"
    )
    logger.info(f"Result dimensions: {final_width}x{final_height}")

    if not output:
        params = {}
        if letterbox:
            params["letterbox"] = "lb"
        if subtitles:
            params["subtitles"] = "sub"
        if top and not letterbox:
            params["top"] = top
        if right:
            params["right"] = right
        if bottom and not (letterbox or subtitles):
            params["bottom"] = bottom
        if left:
            params["left"] = left
        if scale:
            params["scale"] = scale
        output = generate_output_path(input_path, "trim", params)

    logger.info(f"Output: {output}")

    has_trim = any(value > 0 for value in (trim_top, trim_right, trim_bottom, trim_left))
    crop_filter = f"crop={final_width}:{final_height}:{trim_left}:{trim_top}"
    video_filter = crop_filter

    if scale:
        scale_w, scale_h = parse_size(scale, final_width, final_height)
        if has_trim:
            video_filter = f"{crop_filter},scale={scale_w}:{scale_h}"
        else:
            video_filter = f"scale={scale_w}:{scale_h}"

    try:
        process_video_with_hardware_encoding(
            input_path=input_path,
            output_path=output,
            video_filter=video_filter,
            quality=quality,
            verbose=verbose,
        )
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        raise
