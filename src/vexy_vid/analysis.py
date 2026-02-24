"""Video analysis: letterbox detection, subtitle detection (Numba-optimized)."""

import re
import subprocess

import cv2
import ffmpeg
import numpy as np
from loguru import logger
from numba import jit, prange

from vexy_vid.constants import (
    ANALYSIS_FRAME_WIDTH,
    BLACK_THRESHOLD,
    MAX_SUBTITLE_HEIGHT_RATIO,
    MIN_SUBTITLE_WIDTH_RATIO,
    MORPH_KERNEL_HEIGHT,
    MORPH_KERNEL_WIDTH,
    SUBTITLE_BRIGHTNESS_THRESHOLD,
)
from vexy_vid.frames import extract_frame_fast
from vexy_vid.pipeline import get_processing_pipeline
from vexy_vid.utils import VideoAnalysisCache


@jit(nopython=True, parallel=True, cache=True)
def calculate_row_luminance(gray_frame: np.ndarray) -> np.ndarray:
    height, width = gray_frame.shape
    row_means = np.zeros(height, dtype=np.float32)
    for y in prange(height):
        row_sum = 0.0
        for x in range(width):
            row_sum += gray_frame[y, x]
        row_means[y] = row_sum / width
    return row_means


@jit(nopython=True, cache=True)
def find_black_borders(
    row_means: np.ndarray, threshold: float = BLACK_THRESHOLD
) -> tuple[int, int]:
    height = len(row_means)
    top_border = 0
    for y in range(height // 3):
        if row_means[y] > threshold:
            break
        top_border = y + 1
    bottom_border = 0
    for y in range(height - 1, 2 * height // 3, -1):
        if row_means[y] > threshold:
            break
        bottom_border = height - y
    return top_border, bottom_border


@jit(nopython=True, parallel=True, cache=True)
def count_bright_pixels_per_row(
    gray_frame: np.ndarray, threshold: int = SUBTITLE_BRIGHTNESS_THRESHOLD
) -> np.ndarray:
    height, width = gray_frame.shape
    bright_counts = np.zeros(height, dtype=np.int32)
    for y in prange(height):
        count = 0
        for x in range(width):
            if gray_frame[y, x] > threshold:
                count += 1
        bright_counts[y] = count
    return bright_counts


def process_frame_for_letterbox(frame: np.ndarray) -> tuple[int, int]:
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame
    row_means = calculate_row_luminance(gray)
    return find_black_borders(row_means, BLACK_THRESHOLD)


def process_frame_for_subtitles(frame: np.ndarray) -> int | None:
    height, width = frame.shape[:2]
    roi_height = int(height * 0.3)
    roi_y = height - roi_height
    roi = frame[roi_y:, :]
    if len(roi.shape) == 3:
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    else:
        gray_roi = roi
    _, binary = cv2.threshold(gray_roi, SUBTITLE_BRIGHTNESS_THRESHOLD, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (MORPH_KERNEL_WIDTH, MORPH_KERNEL_HEIGHT))
    dilated = cv2.dilate(binary, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    valid_tops = []
    for contour in contours:
        _, y, w, h = cv2.boundingRect(contour)
        if (
            w > width * MIN_SUBTITLE_WIDTH_RATIO
            and h > 10
            and h < roi_height * MAX_SUBTITLE_HEIGHT_RATIO
        ):
            valid_tops.append(roi_y + y)
    return min(valid_tops) if valid_tops else None


def detect_letterbox_ffmpeg(
    input_path: str, duration: int = 60, verbose: bool = False
) -> tuple[int, int, int, int]:
    cache = VideoAnalysisCache()
    cached_result = cache.get(input_path, f"letterbox_ffmpeg_{duration}")
    if cached_result:
        logger.debug("Using cached letterbox detection result")
        return tuple(cached_result["crop"])
    logger.debug(f"Running cropdetect on {input_path} for {duration}s")
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        input_path,
        "-t",
        str(duration),
        "-vf",
        "cropdetect=24:16:0",
        "-f",
        "null",
        "-",
    ]
    if not verbose:
        cmd.extend(["-loglevel", "error"])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        crop_matches = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", result.stderr)
        if not crop_matches:
            logger.warning("No letterbox detected by cropdetect")
            return 0, 0, 0, 0
        width, height, x, y = map(int, crop_matches[-1])
        logger.info(f"Detected letterbox crop: {width}x{height} at ({x},{y})")
        cache.set(
            input_path,
            f"letterbox_ffmpeg_{duration}",
            {"crop": [x, y, width, height]},
        )
        return x, y, width, height
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg cropdetect failed: {e}")
        return 0, 0, 0, 0


def detect_letterbox_opencv_parallel(
    input_path: str, sample_frames: int = 10, verbose: bool = False
) -> tuple[int, int]:
    cache = VideoAnalysisCache()
    cached_result = cache.get(input_path, f"letterbox_pipeline_{sample_frames}")
    if cached_result:
        logger.debug("Using cached pipeline letterbox result")
        return cached_result["top"], cached_result["bottom"]
    logger.debug(f"Analyzing letterbox with pipeline on {sample_frames} frames")
    cap = cv2.VideoCapture(input_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    frame_indices = np.linspace(0, frame_count - 1, sample_frames, dtype=int).tolist()
    pipeline = get_processing_pipeline()

    def progress_callback(processed: int, total: int):
        if verbose:
            logger.debug(f"Letterbox analysis: {processed}/{total} frames processed")

    results = pipeline.process_frames_parallel(
        video_path=input_path,
        frame_indices=frame_indices,
        processor_func=process_frame_for_letterbox,
        processor_args=(),
        progress_callback=progress_callback,
    )
    valid_results = [r for r in results if r is not None]
    if not valid_results:
        logger.warning("No frames could be analyzed")
        return 0, 0
    tops, bottoms = zip(*valid_results)
    top_trim = int(np.median(tops))
    bottom_trim = int(np.median(bottoms))
    probe = ffmpeg.probe(input_path)
    video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    original_width = int(video_stream["width"])
    scale_factor = original_width / ANALYSIS_FRAME_WIDTH
    top_trim = int(top_trim * scale_factor)
    bottom_trim = int(bottom_trim * scale_factor)
    logger.info(f"Pipeline letterbox detection: top={top_trim}, bottom={bottom_trim}")
    cache.set(
        input_path,
        f"letterbox_pipeline_{sample_frames}",
        {"top": top_trim, "bottom": bottom_trim},
    )
    return top_trim, bottom_trim


def detect_subtitles_morphological_parallel(
    input_path: str, sample_frames: int = 20, verbose: bool = False
) -> int:
    cache = VideoAnalysisCache()
    cached_result = cache.get(input_path, f"subtitles_pipeline_{sample_frames}")
    if cached_result:
        logger.debug("Using cached pipeline subtitle detection result")
        return cached_result["bottom_trim"]
    logger.debug(
        f"Detecting subtitles with pipeline morphological analysis on {sample_frames} frames"
    )
    cap = cv2.VideoCapture(input_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    start_frame = int(frame_count * 0.1)
    end_frame = int(frame_count * 0.9)
    frame_indices = np.linspace(start_frame, end_frame, sample_frames, dtype=int).tolist()
    probe = ffmpeg.probe(input_path)
    video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    original_width = int(video_stream["width"])
    scale_factor = original_width / ANALYSIS_FRAME_WIDTH
    pipeline = get_processing_pipeline()

    def progress_callback(processed: int, total: int):
        if verbose:
            logger.debug(f"Subtitle analysis: {processed}/{total} frames processed")

    results = pipeline.process_frames_parallel(
        video_path=input_path,
        frame_indices=frame_indices,
        processor_func=process_frame_for_subtitles,
        processor_args=(),
        progress_callback=progress_callback,
    )
    subtitle_tops = []
    for result in results:
        if result is not None:
            subtitle_top = int(result * scale_factor)
            subtitle_tops.append(subtitle_top)
    if not subtitle_tops:
        logger.warning("No subtitles detected")
        return 0
    highest_subtitle = min(subtitle_tops)
    margin = 20
    bottom_trim = height - highest_subtitle + margin
    logger.info(f"Pipeline detected subtitle region: trim bottom {bottom_trim}px")
    cache.set(input_path, f"subtitles_pipeline_{sample_frames}", {"bottom_trim": bottom_trim})
    return bottom_trim


def detect_subtitles_brightness_fast(
    input_path: str, sample_frames: int = 30, verbose: bool = False
) -> int:
    cache = VideoAnalysisCache()
    cached_result = cache.get(input_path, f"subtitles_bright_{sample_frames}")
    if cached_result:
        logger.debug("Using cached brightness subtitle result")
        return cached_result["bottom_trim"]
    logger.debug(f"Detecting subtitles with brightness analysis on {sample_frames} frames")
    probe = ffmpeg.probe(input_path)
    video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    height = int(video_stream["height"])
    frame_count = int(video_stream.get("nb_frames", 0))
    if frame_count == 0:
        cap = cv2.VideoCapture(input_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
    frame_indices = np.linspace(frame_count * 0.1, frame_count * 0.9, sample_frames, dtype=int)
    bottom_region_height = int(height * 0.25)
    brightness_accumulator = np.zeros(bottom_region_height, dtype=np.float64)
    frame_counts = np.zeros(bottom_region_height, dtype=np.int32)
    processed = 0
    for idx in frame_indices:
        frame = extract_frame_fast(input_path, idx, ANALYSIS_FRAME_WIDTH)
        if frame is None:
            continue
        scaled_height = frame.shape[0]
        scaled_bottom_height = int(scaled_height * 0.25)
        bottom_region = frame[scaled_height - scaled_bottom_height :, :]
        if len(bottom_region.shape) == 3:
            gray_bottom = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2GRAY)
        else:
            gray_bottom = bottom_region
        bright_counts = count_bright_pixels_per_row(gray_bottom, SUBTITLE_BRIGHTNESS_THRESHOLD)
        for y, count in enumerate(bright_counts):
            if count > 50:
                brightness_accumulator[y] += count
                frame_counts[y] += 1
        processed += 1
        if verbose and processed % 5 == 0:
            logger.debug(f"Processed {processed}/{sample_frames} frames")
    if processed == 0:
        logger.warning("No frames could be processed")
        return 0
    avg_brightness = np.divide(brightness_accumulator, frame_counts + 1e-6)
    threshold = np.max(avg_brightness) * 0.3
    subtitle_rows = np.where(avg_brightness > threshold)[0]
    if len(subtitle_rows) > 0:
        top_subtitle_row = subtitle_rows[0]
        bottom_trim = bottom_region_height - top_subtitle_row + 10
        logger.info(f"Brightness analysis: subtitle region detected, trim bottom {bottom_trim}px")
        cache.set(
            input_path,
            f"subtitles_bright_{sample_frames}",
            {"bottom_trim": bottom_trim},
        )
        return bottom_trim
    logger.warning("No subtitles detected via brightness analysis")
    return 0
