"""vexy-vid: High-performance video cropping and trimming CLI tool."""

try:
    from vexy_vid._version import __version__, __version_tuple__
except ImportError:
    __version__ = "0.0.1"
    __version_tuple__ = (0, 0, 1)

__all__ = ["__version__", "__version_tuple__"]
