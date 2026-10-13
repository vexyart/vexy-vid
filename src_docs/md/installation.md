# Installation

`vexy-vid` has two parts: the Python package, installed from PyPI, and the
`ffmpeg` binary, installed with your operating system's package manager.

## Prerequisites

- Python 3.10, 3.11, 3.12 or 3.13.
- [`uv`](https://docs.astral.sh/uv/) or `pip`.
- Permission to install system packages (for ffmpeg).

## Install ffmpeg

ffmpeg does the encoding and the primary letterbox detection. It cannot be
installed with `pip`.

=== "macOS"

    ```bash
    brew install ffmpeg
    ```

=== "Debian / Ubuntu"

    ```bash
    sudo apt install ffmpeg
    ```

Check that ffmpeg and ffprobe are on your `PATH`:

```bash
ffmpeg -version
ffprobe -version
```

`vexy-vid` calls both. It uses `ffprobe` (through `ffmpeg-python`) to read the
video dimensions before every operation.

## Install vexy-vid

1. Install the package:

    ```bash
    uv pip install vexy-vid
    ```

    Or with pip:

    ```bash
    pip install vexy-vid
    ```

2. Check that the command is available:

    ```bash
    vexy-vid --help
    ```

    The output lists the two commands, `crop` and `trim`.

To run it once without installing, use `uvx`:

```bash
uvx vexy-vid crop --help
```

## What gets installed

The package pulls in these Python dependencies automatically:

| Package | Role in vexy-vid |
|---------|------------------|
| `fire` | Builds the command-line interface from the `crop` and `trim` function signatures. |
| `ffmpeg-python` | Builds and runs the ffmpeg encode command and calls `ffprobe`. |
| `av` (PyAV) | Extracts single frames for analysis. |
| `opencv-python` | Thresholding and morphology for subtitle detection. |
| `numpy` | Array maths for frame analysis. |
| `numba` | Compiles the per-pixel luminance and brightness loops. |
| `loguru` | Log output and `--verbose` mode. |
| `rich` | The status spinner shown while a video encodes. |
| `psutil` | Listed as a dependency. |

`numba` compiles its functions the first time they run, so the first detection
run can take a few extra seconds. The compiled code is cached by Numba for later
runs.

## Development install

To work on `vexy-vid` itself, clone the repository and install it in editable
mode with the development extras:

```bash
git clone https://github.com/vexyart/vexy-vid.git
cd vexy-vid
uv venv
uv pip install -e ".[dev]"
```

The `dev` extra adds `pytest`, `pytest-cov` and `ruff`. See
[Contributing](contributing.md) for the test and lint commands.
