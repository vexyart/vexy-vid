"""Crop command — crop video to specific dimensions with alignment control."""

import sys

from loguru import logger

from vexy_vid.encoder import process_video_with_hardware_encoding
from vexy_vid.utils import (
    generate_output_path,
    get_input_path,
    get_video_info,
    parse_size,
)


def crop(
    input: str | None = None,
    output: str | None = None,
    crop: str | None = None,
    scale: str | None = None,
    Halign: str | int | float = 50,
    Valign: str | int | float = 50,
    quality: int = 1,
    verbose: bool = False,
) -> None:
    """
    Crop video to specific dimensions with alignment control and hardware acceleration.

    Args:
        input: Input video path (reads from stdin if not provided)
        output: Output video path (auto-generated if not provided)
        crop: Target crop size spec. Formats:
            RATIO:         16:9
            PIXELSxPIXELS: 1280x720
            PERCENT:       50%x50%
            WIDTH only:    1280x  or  50%x  (height=100%)
            HEIGHT only:   x720   or  x50%  (width=100%)
            MIXED:         1280x50%  or  50%x720
        scale: Target output size spec after cropping. Uses same formats as crop.
        Halign: Horizontal alignment (0=left, 50=center, 100=right)
        Valign: Vertical alignment (0=top, 50=center, 100=bottom)
        quality: 0 (fast), 1 (balanced), 2 (quality)
        verbose: Enable verbose logging
    """
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    halign = Halign
    valign = Valign

    input_path = get_input_path(input)
    logger.info(f"Processing: {input_path}")

    orig_width, orig_height = get_video_info(input_path)
    logger.debug(f"Original dimensions: {orig_width}x{orig_height}")

    if crop:
        target_width, target_height = parse_size(crop, orig_width, orig_height)
    else:
        target_width, target_height = orig_width, orig_height

    if target_width > orig_width:
        logger.warning(f"Target width {target_width} exceeds original {orig_width}, using original")
        target_width = orig_width
    if target_height > orig_height:
        logger.warning(
            f"Target height {target_height} exceeds original {orig_height}, using original"
        )
        target_height = orig_height

    logger.info(f"Target dimensions: {target_width}x{target_height}")

    h_align = float(str(halign).rstrip("%"))
    v_align = float(str(valign).rstrip("%"))

    max_x = orig_width - target_width
    max_y = orig_height - target_height

    x_offset = int(max_x * h_align / 100)
    y_offset = int(max_y * v_align / 100)

    logger.debug(f"Alignment: h={h_align}%, v={v_align}%")
    logger.debug(f"Crop offset: x={x_offset}, y={y_offset}")

    if not output:
        crop_spec = crop if crop else scale
        params = {"crop": crop_spec}
        output = generate_output_path(input_path, "crop", params)

    logger.info(f"Output: {output}")

    crop_filter = f"crop={target_width}:{target_height}:{x_offset}:{y_offset}"
    video_filter = crop_filter

    if scale:
        if crop:
            scale_w, scale_h = parse_size(scale, target_width, target_height)
            video_filter = f"{crop_filter},scale={scale_w}:{scale_h}"
        else:
            scale_w, scale_h = parse_size(scale, orig_width, orig_height)
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
