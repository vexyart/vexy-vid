# Contributing

`vexy-vid` lives at
[github.com/vexyart/vexy-vid](https://github.com/vexyart/vexy-vid). Bug reports
and pull requests are welcome.

## Set up a development environment

Prerequisites: Python 3.10 or newer, `uv`, `git` and ffmpeg.

1. Clone the repository:

    ```bash
    git clone https://github.com/vexyart/vexy-vid.git
    cd vexy-vid
    ```

2. Create a virtual environment and install the package with the development
   extras:

    ```bash
    uv venv
    uv pip install -e ".[dev]"
    ```

## Run the tests

```bash
pytest tests/
```

The suite has two kinds of tests:

- **Unit tests** (`test_utils.py`, `test_analysis.py`, `test_encoder.py`,
  `test_smoke.py`) need no ffmpeg. They cover size parsing, output names, trim
  validation, the Numba kernels on synthetic frames and the encoder settings.
- **Integration tests** (`test_integration.py`) build a 320×240 test clip with
  40-pixel black bars using ffmpeg's `testsrc` and `pad` filters, then run
  `crop`, `trim` and letterbox detection on it end to end. The whole module is
  skipped when `ffmpeg` is not on `PATH`.

For a coverage report:

```bash
pytest tests/ --cov=vexy_vid --cov-report=term-missing
```

## Lint and format

The project uses `ruff` with a line length of 100 and a Python 3.10 target:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

The `pyproject.toml` contains targeted ignores for the capitalised `Halign`,
`Valign` and `Letterbox` parameters, which are part of the command-line
interface.

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request to `main`. It
installs ffmpeg, then runs `ruff check`, `ruff format --check` and `pytest` on
Python 3.10, 3.11 and 3.12.

`.github/workflows/docs.yml` rebuilds this documentation site into `docs/`
when files under `src_docs/` change on `main`.

## Build the documentation

The documentation source is in `src_docs/md/`, and the configuration is
`src_docs/mkdocs.yml`. To build the site into `docs/`:

```bash
src_docs/build.sh
```

To preview it at `http://127.0.0.1:8000` while you edit:

```bash
src_docs/build.sh serve
```

## Build the package

```bash
./build.sh package
```

This removes `dist/`, runs `uv build` and checks the result with
`twine check`. `./build.sh` with no argument builds the documentation and the
package.

## Versioning and releases

The version comes from the git tag through `hatch-vcs`; there is no version
number in `pyproject.toml`. During a build, `hatch-vcs` writes
`src/vexy_vid/_version.py`, which is not tracked by git.

Maintainers release with `./publish.sh`. It runs `gitnextver` to commit, tag the
next `vX.Y.Z` version and push, then builds the package and uploads it with
`uv publish`. Pushing a `v*` tag also triggers `.github/workflows/release.yml`,
which builds the package, publishes it to PyPI with trusted publishing (skipping
files that already exist) and creates a GitHub release.
