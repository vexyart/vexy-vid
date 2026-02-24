"""CLI entry point for vexy-vid."""

import sys

import fire
from loguru import logger

from vexy_vid.crop import crop
from vexy_vid.trim import trim

# Set up logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
    level="INFO",
)


def main():
    """Main entry point."""
    fire.Fire({"crop": crop, "trim": trim})


if __name__ == "__main__":
    main()
