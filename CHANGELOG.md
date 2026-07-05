# Changelog

All notable changes to `vexy-vid` are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project uses
git-tag-driven semantic versioning via `hatch-vcs`.

## [Unreleased] — 2026-07-05 modernization pass

### Fixed

- **Encoding was broken against current `ffmpeg-python`.** `encoder.py` called
  `stream.video.filter_complex(...)`, which does not exist in the installed
  `ffmpeg-python`, so every `crop`/`trim` encode raised `AttributeError`. The
  crop/scale chain is now passed through as the `-vf` output option.
- **`ffmpeg.run(global_args=...)` is not a valid keyword** in the installed
  `ffmpeg-python` and raised `TypeError`. Global flags (`-loglevel`) are now
  attached to the stream via `.global_args(...)`.
- **Letterbox auto-detection always found nothing in the default mode.**
  `detect_letterbox_ffmpeg` ran ffmpeg at `-loglevel error`, but `cropdetect`
  prints its `crop=` result at `info` level — so the parser saw an empty log
  whenever `--verbose` was off. Detection now runs at `info` (captured
  internally, never shown to the user).
- **The parallel frame pipeline deadlocked.** The reader emitted a single
  `None` sentinel while up to four processor workers consumed the queue, so
  three workers looped forever and the collector hung. Each worker now re-posts
  the sentinel before exiting, so it propagates to every worker. This affected
  `trim --subtitles` and the OpenCV letterbox fallback.

### Added

- Test suite (`tests/`, 48 tests): unit tests for size/dimension parsing,
  output-path generation, crop validation, the Numba detection kernels, the
  OpenCV frame processors, and encoder config selection; ffmpeg-gated
  integration tests that generate a synthetic letterboxed clip and exercise
  `crop`, `trim` (explicit + `--Letterbox`), frame extraction, and the parallel
  pipeline end to end.
- `.github/workflows/ci.yml` — lint, format check, and tests on Python
  3.10/3.11/3.12 with ffmpeg installed.
- `.github/workflows/release.yml` — build and PyPI trusted publishing plus a
  GitHub release on `v*` tags.
- Jekyll documentation under `docs/` (home, usage, hardware acceleration) using
  the Just the Docs remote theme, plus a project icon at `docs/assets/icon.png`.
- `pytest`/`coverage` configuration, `pytest-cov` dev dependency, `CLAUDE.md`,
  `PLAN.md`, `DEPENDENCIES.md`.

### Changed

- `.gitignore` now covers `.DS_Store`, agent scratch dirs (`.swarm/`,
  `.opencode/`), and the Jekyll build output.
- `ruff` config records intentional CLI-flag capitalization (`--Halign`,
  `--Valign`, `--Letterbox`) via targeted per-file ignores instead of leaving
  lint errors.

## [1.0.4] and earlier

Initial package: `crop` and `trim` commands, PyAV frame extraction, Numba
pixel analysis, hardware-encoder detection, `hatch-vcs` packaging.
