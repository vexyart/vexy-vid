# Dependencies

Why each dependency is here. Keep this current when `pyproject.toml` changes.

## System (not pip-installable)

- **ffmpeg** — the encode engine and the letterbox detector (`cropdetect`).
  Install with `brew install ffmpeg` or `apt install ffmpeg`. Every encode and
  the primary letterbox detection shell out to it.

## Runtime

| Package | Why |
|---------|-----|
| `fire` | Builds the CLI from function signatures; no argparse boilerplate. |
| `ffmpeg-python` | Constructs and runs the ffmpeg encode command. |
| `av` (PyAV) | Fast single-frame extraction for analysis (imported before cv2). |
| `opencv-python` | Frame thresholding/morphology for subtitle detection. |
| `numpy` | Array math shared across analysis and pipeline. |
| `numba` | JIT-compiles the per-pixel luminance/brightness kernels. |
| `loguru` | Structured logging with a `--verbose` switch. |
| `rich` | Console status spinner during encodes. |
| `psutil` | System introspection used when sizing workers. |

## Development

| Package | Why |
|---------|-----|
| `pytest` | Test runner. |
| `pytest-cov` | Coverage reporting. |
| `ruff` | Lint + format. |

## Notes

- `numba` bundles LLVM through `llvmlite`; no separate system dependency.
- First-run Numba JIT compilation can take a few seconds; results are cached.
- PyAV and opencv-python ship conflicting `libav*` dylibs on macOS. Importing
  `av` before `cv2` avoids the objc warning; it is cosmetic either way.
