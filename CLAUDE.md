# CLAUDE.md — vexy-vid

Guidance for AI agents (and humans) working in this repo. For the user-facing
description see `README.md`; for architecture and conventions see `AGENTS.md`.

## What this is

A Python CLI that crops and trims video with automatic letterbox/subtitle
detection and hardware-accelerated encoding. It wraps the `ffmpeg` binary; the
binary is a required system dependency and is **not** pip-installable.

## Source files (`this_file` map)

- `src/vexy_vid/__init__.py` — version export
- `src/vexy_vid/cli.py` — `fire` entry point (`crop`, `trim`)
- `src/vexy_vid/constants.py` — thresholds, pool sizes, encoder priority lists
- `src/vexy_vid/utils.py` — size/dimension parsing, probing, output paths, cache
- `src/vexy_vid/encoder.py` — hardware-encoder detection + the encode call
- `src/vexy_vid/pipeline.py` — producer/consumer frame-processing pipeline
- `src/vexy_vid/frames.py` — PyAV frame extraction (with ffmpeg fallback)
- `src/vexy_vid/analysis.py` — Numba/OpenCV letterbox + subtitle detection
- `src/vexy_vid/crop.py` — `crop` command
- `src/vexy_vid/trim.py` — `trim` command
- `tests/` — unit tests (no ffmpeg) + ffmpeg-gated integration tests

## Working here

- Setup: `uv venv && uv pip install -e ".[dev]"`.
- Test: `pytest tests/` — unit tests run anywhere; integration tests skip
  cleanly when `ffmpeg` is not on `PATH`.
- Lint/format: `ruff check src/ tests/ && ruff format src/ tests/`.
- Import order matters: `import av` before `import cv2` (macOS dylib clash).

## Load-bearing details (do not regress)

- The encode path talks to `ffmpeg-python` through the **output** stage: filters
  go in as the `-vf` option and global flags via `.global_args(...)`. The
  `stream.video.filter_complex(...)` and `run(global_args=...)` forms do not
  exist in the pinned `ffmpeg-python` and were live bugs — see `CHANGELOG.md`.
- `cropdetect` output only appears at ffmpeg `-loglevel info` or higher. The
  detection subprocess captures stderr, so raising the level is free.
- The parallel pipeline uses one sentinel that each worker must re-post before
  exiting. Removing that re-post reintroduces a deadlock.
- `--Halign`, `--Valign`, `--Letterbox` are intentionally capitalized: `fire`
  turns them into those exact flags. Renaming breaks the CLI. Ruff ignores are
  configured for this in `pyproject.toml`.
