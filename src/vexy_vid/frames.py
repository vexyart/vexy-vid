"""Frame extraction using PyAV with FFmpeg fallback."""

from typing import Optional, Tuple

import av
import ffmpeg
import numpy as np
from loguru import logger

from vexy_vid.constants import ANALYSIS_FRAME_WIDTH, DECODE_THREADS


def extract_frame_fast(
    video_path: str, frame_number: int, downscale_width: int = ANALYSIS_FRAME_WIDTH
) -> np.ndarray | None:
    """
    Extract a single frame from video using PyAV (50-100% faster than FFmpeg CLI).
    Optionally downscale for faster processing.

    Args:
        video_path: Path to video file
        frame_number: Frame number to extract
        downscale_width: Target width for downscaling (0 to disable)

    Returns:
        Frame as numpy array or None if extraction fails
    """
    try:
        # Open video with PyAV using multi-threaded decoding
        container = av.open(video_path, options={"thread_count": str(DECODE_THREADS)})
        video_stream = container.streams.video[0]

        # Calculate timestamp for seeking
        fps = float(video_stream.average_rate)
        timestamp = frame_number / fps

        # Seek to approximate position (faster than frame-by-frame)
        container.seek(int(timestamp * av.time_base_q.denominator))

        # Decode frames until we reach the target
        target_pts = int(timestamp * video_stream.time_base.denominator)
        for frame in container.decode(video_stream):
            if frame.pts >= target_pts:
                # Convert frame to numpy array
                if downscale_width > 0:
                    # Calculate scaled dimensions
                    aspect_ratio = frame.height / frame.width
                    height = int(downscale_width * aspect_ratio)

                    # Resize frame using PyAV's built-in scaling (faster than OpenCV)
                    frame = frame.reformat(width=downscale_width, height=height, format="bgr24")
                else:
                    # Convert to BGR format for OpenCV compatibility
                    frame = frame.reformat(format="bgr24")

                # Convert to numpy array
                frame_array = frame.to_ndarray()

                container.close()
                return frame_array

        container.close()
        return None

    except Exception as e:
        logger.debug(f"Failed to extract frame {frame_number} with PyAV: {e}")
        # Fallback to original FFmpeg method
        return _extract_frame_ffmpeg_fallback(video_path, frame_number, downscale_width)


def _extract_frame_ffmpeg_fallback(
    video_path: str, frame_number: int, downscale_width: int = ANALYSIS_FRAME_WIDTH
) -> np.ndarray | None:
    """
    Fallback frame extraction using FFmpeg CLI when PyAV fails.

    Args:
        video_path: Path to video file
        frame_number: Frame number to extract
        downscale_width: Target width for downscaling (0 to disable)

    Returns:
        Frame as numpy array or None if extraction fails
    """
    try:
        # Get video info for frame rate
        probe = ffmpeg.probe(video_path)
        video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
        fps = eval(video_stream["r_frame_rate"])
        timestamp = frame_number / fps

        # Build FFmpeg command
        stream = ffmpeg.input(video_path, ss=timestamp)

        # Add scaling if requested
        if downscale_width > 0:
            stream = stream.filter("scale", downscale_width, -1)

        # Extract frame
        out, _ = stream.output("pipe:", format="rawvideo", pix_fmt="bgr24", vframes=1).run(
            capture_stdout=True, quiet=True
        )

        # Calculate dimensions
        if downscale_width > 0:
            width = downscale_width
            height = int(video_stream["height"] * downscale_width / video_stream["width"])
        else:
            width = int(video_stream["width"])
            height = int(video_stream["height"])

        # Convert to numpy array
        frame = np.frombuffer(out, np.uint8).reshape([height, width, 3])
        return frame

    except Exception as e:
        logger.debug(f"Failed to extract frame {frame_number} with FFmpeg: {e}")
        return None
