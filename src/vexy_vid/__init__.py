"""vexy-vid: High-performance video cropping and trimming CLI.

Two subcommands:

- ``crop`` — crop to exact pixels, aspect ratio, or percentage.
  Alignment flags (``--Halign``, ``--Valign``) position the crop window.
- ``trim`` — remove edges (reversed CSS padding). Pass pixel counts or
  percentages. ``--Letterbox`` auto-detects and removes black bars;
  ``--subtitles`` auto-detects the subtitle region at the bottom.

Both support ``--scale`` to resize after the crop/trim operation and
hardware-accelerated encoding with automatic CPU fallback.

Frame analysis uses PyAV for extraction (50–100 % faster than OpenCV) and
Numba-optimised pixel routines for letterbox/subtitle detection (10–50×
faster than pure NumPy).

System requirement: an ``ffmpeg`` binary in ``$PATH`` (``brew install ffmpeg``
or ``apt install ffmpeg``). Not installable via pip.
"""

try:
    from vexy_vid._version import __version__, __version_tuple__
except ImportError:
    __version__ = "0.0.1"
    __version_tuple__ = (0, 0, 1)

__all__ = ["__version__", "__version_tuple__"]
