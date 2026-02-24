"""Constants for video analysis and processing."""

import os
from pathlib import Path

# Detection algorithm thresholds
BLACK_THRESHOLD = 30  # Pixel value threshold for black detection
SUBTITLE_BRIGHTNESS_THRESHOLD = 200  # Threshold for bright subtitle text
MORPH_KERNEL_WIDTH = 20  # Width of morphological kernel for text grouping
MORPH_KERNEL_HEIGHT = 3  # Height of morphological kernel
MIN_SUBTITLE_WIDTH_RATIO = 0.1  # Minimum width ratio for valid subtitle region
MAX_SUBTITLE_HEIGHT_RATIO = 0.5  # Maximum height ratio for subtitle region
ANALYSIS_FRAME_WIDTH = 640  # Downscale frames to this width for faster analysis
CACHE_DIR = Path.home() / ".cache" / "vidcrop"

# Performance optimization constants
BUFFER_POOL_SIZE = 10  # Number of pre-allocated frame buffers
MAX_WORKERS = min(32, (os.cpu_count() or 1) + 4)  # Optimal worker count
QUEUE_SIZE = 200  # Pipeline queue size for frame processing
DECODE_THREADS = 4  # PyAV decoder thread count

# Hardware encoder priority order (fastest to slowest)
HARDWARE_ENCODERS = [
    "hevc_nvenc",  # NVIDIA NVENC H.265
    "h264_nvenc",  # NVIDIA NVENC H.264
    "hevc_qsv",  # Intel Quick Sync H.265
    "h264_qsv",  # Intel Quick Sync H.264
    "hevc_amf",  # AMD VCE H.265
    "h264_amf",  # AMD VCE H.264
]

# Software encoder fallbacks
SOFTWARE_ENCODERS = ["libx265", "libx264"]
