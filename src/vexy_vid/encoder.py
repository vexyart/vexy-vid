"""Hardware encoder detection and video encoding with hardware acceleration."""

import os
import subprocess
from typing import Any, Dict, List, Optional

import ffmpeg
from loguru import logger
from rich.console import Console

from vexy_vid.constants import HARDWARE_ENCODERS, SOFTWARE_ENCODERS

console = Console()


class HardwareEncoderDetector:
    """
    Detects available hardware encoders and provides optimal encoder selection.
    Implements fallback strategy from hardware to software encoders.
    """

    def __init__(self):
        """Initialize hardware encoder detector."""
        self._available_encoders = None
        self._detection_cache = {}

    def detect_available_encoders(self) -> List[str]:
        """
        Detect all available hardware and software encoders.

        Returns:
            List of available encoder names in priority order
        """
        if self._available_encoders is not None:
            return self._available_encoders

        available = []

        # Test hardware encoders first (highest priority)
        for encoder in HARDWARE_ENCODERS:
            if self._test_encoder(encoder):
                available.append(encoder)
                logger.debug(f"Hardware encoder available: {encoder}")

        # Add software encoders as fallbacks
        for encoder in SOFTWARE_ENCODERS:
            if self._test_encoder(encoder):
                available.append(encoder)
                logger.debug(f"Software encoder available: {encoder}")

        self._available_encoders = available
        logger.info(f"Detected {len(available)} available encoders: {available[:3]}...")
        return available

    def _test_encoder(self, encoder_name: str) -> bool:
        """
        Test if a specific encoder is available.

        Args:
            encoder_name: Name of encoder to test

        Returns:
            True if encoder is available and functional
        """
        if encoder_name in self._detection_cache:
            return self._detection_cache[encoder_name]

        try:
            # Test encoding a single black frame
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-s",
                "64x64",
                "-r",
                "1",
                "-i",
                "/dev/null" if os.name != "nt" else "NUL",
                "-c:v",
                encoder_name,
                "-frames:v",
                "1",
                "-f",
                "null",
                "-",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=5,
                input=b"\x00" * (64 * 64 * 3),  # Single black frame
            )

            available = result.returncode == 0
            self._detection_cache[encoder_name] = available
            return available

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self._detection_cache[encoder_name] = False
            return False

    def get_best_encoder(self, prefer_hardware: bool = True) -> str:
        """
        Get the best available encoder based on preferences.

        Args:
            prefer_hardware: Whether to prefer hardware encoders

        Returns:
            Name of best available encoder
        """
        available = self.detect_available_encoders()

        if not available:
            # Fallback to basic H.264 if nothing detected
            return "libx264"

        if prefer_hardware:
            # Return first available hardware encoder
            for encoder in available:
                if encoder in HARDWARE_ENCODERS:
                    return encoder

        # Return first available encoder (hardware or software)
        return available[0]

    def get_encoder_config(self, encoder_name: str, quality: int = 1) -> Dict[str, Any]:
        """
        Get optimized configuration for specific encoder.

        Args:
            encoder_name: Name of encoder
            quality: 0 (fast), 1 (balanced), 2 (quality)

        Returns:
            Dictionary of encoder configuration parameters
        """
        config = {"codec": encoder_name}

        # Hardware encoder configurations
        if encoder_name in ["hevc_nvenc", "h264_nvenc"]:
            if quality == 0:
                config.update({"preset": "p1", "tune": "ll"})
            elif quality == 2:
                config.update({"preset": "p7", "cq": "18"})
            else:
                config.update({"preset": "p4", "cq": "20"})

        elif encoder_name in ["hevc_qsv", "h264_qsv"]:
            if quality == 0:
                config.update({"preset": "veryfast", "global_quality": "22"})
            elif quality == 2:
                config.update({"preset": "slow", "global_quality": "18"})
            else:
                config.update({"preset": "medium", "global_quality": "20"})

        elif encoder_name in ["hevc_amf", "h264_amf"]:
            if quality == 0:
                config.update({"quality": "speed", "rc": "cqp", "qp_i": "22"})
            elif quality == 2:
                config.update({"quality": "quality", "rc": "cqp", "qp_i": "18"})
            else:
                config.update({"quality": "balanced", "rc": "cqp", "qp_i": "20"})

        # Software encoder configurations
        elif encoder_name == "libx265":
            if quality == 0:
                config.update({"preset": "faster", "crf": "22"})
            elif quality == 2:
                config.update({"preset": "slow", "crf": "18"})
            else:
                config.update({"preset": "medium", "crf": "20"})

        elif encoder_name == "libx264":
            if quality == 0:
                config.update({"preset": "faster", "crf": "22"})
            elif quality == 2:
                config.update({"preset": "slow", "crf": "18"})
            else:
                config.update({"preset": "medium", "crf": "20"})

        return config


# Global instance for reuse
_encoder_detector = None


def get_encoder_detector() -> HardwareEncoderDetector:
    """Get or create global encoder detector instance."""
    global _encoder_detector
    if _encoder_detector is None:
        _encoder_detector = HardwareEncoderDetector()
    return _encoder_detector


def process_video_with_hardware_encoding(
    input_path: str, output_path: str, video_filter: str, quality: int = 1, verbose: bool = False
) -> None:
    """
    Process video using optimal hardware-accelerated encoding.

    Args:
        input_path: Input video file path
        output_path: Output video file path
        video_filter: FFmpeg video filter string (e.g., crop filter)
        quality: 0 (fast), 1 (balanced), 2 (quality)
        verbose: Enable verbose logging
    """
    encoder_detector = get_encoder_detector()

    QUALITY_LABELS = {0: "fast", 1: "balanced", 2: "quality"}
    quality_label = QUALITY_LABELS.get(quality, "balanced")
    prefer_hardware = quality <= 1
    encoder_name = encoder_detector.get_best_encoder(prefer_hardware=prefer_hardware)

    # Get encoder configuration
    encoder_config = encoder_detector.get_encoder_config(encoder_name, quality)

    logger.info(f"Using encoder: {encoder_name} (quality: {quality_label})")

    global_args = ["-loglevel", "error" if not verbose else "info"]

    try:
        # Build FFmpeg command with hardware encoding
        input_stream = ffmpeg.input(input_path)

        # Apply video filter
        if video_filter:
            input_stream = input_stream.video.filter_complex(video_filter)

        # Build output arguments
        output_args = {
            "acodec": "copy",  # Copy audio without re-encoding
        }

        # Add encoder-specific arguments
        output_args["c:v"] = encoder_name
        output_args.update(encoder_config)
        if "codec" in output_args:
            del output_args["codec"]  # Remove redundant codec key

        # Create output stream
        output_stream = ffmpeg.output(input_stream, output_path, **output_args)

        # Run encoding
        with console.status(f"Processing video with {encoder_name}..."):
            ffmpeg.run(
                output_stream,
                global_args=global_args,
                overwrite_output=True,
                capture_stdout=True,
                capture_stderr=True,
            )

        logger.success(f"Video processed successfully with {encoder_name}: {output_path}")

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"Hardware encoding failed with {encoder_name}: {error_msg}")

        # Fallback to software encoding
        if encoder_name in HARDWARE_ENCODERS:
            logger.info("Falling back to software encoding...")
            fallback_encoder = "libx264"
            fallback_config = encoder_detector.get_encoder_config(fallback_encoder, quality)

            try:
                # Retry with software encoder
                input_stream = ffmpeg.input(input_path)

                if video_filter:
                    input_stream = input_stream.video.filter_complex(video_filter)

                output_args = {
                    "acodec": "copy",
                    "c:v": fallback_encoder,
                }
                output_args.update(fallback_config)
                if "codec" in output_args:
                    del output_args["codec"]

                output_stream = ffmpeg.output(input_stream, output_path, **output_args)

                with console.status(f"Processing video with {fallback_encoder} (fallback)..."):
                    ffmpeg.run(
                        output_stream,
                        global_args=global_args,
                        overwrite_output=True,
                        capture_stdout=True,
                        capture_stderr=True,
                    )

                logger.success(
                    f"Video processed successfully with fallback {fallback_encoder}: {output_path}"
                )

            except ffmpeg.Error as fallback_error:
                logger.error(f"Fallback encoding also failed: {fallback_error.stderr.decode()}")
                raise
        else:
            raise
