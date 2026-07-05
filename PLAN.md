# PLAN

Future work for `vexy-vid`, in rough priority order. The 2026-07-05
modernization pass (CI, tests, bug fixes, docs) is complete — see `CHANGELOG.md`.

## Correctness and coverage

- Raise coverage on `analysis.py` subtitle detection (`detect_subtitles_*`) and
  the encoder software-fallback branch with dedicated fixtures.
- Add a fixture clip that carries an audio stream, so `-acodec copy` on the
  encode path is exercised (current synthetic clips are video-only).
- Property-test `parse_size` / `parse_dimension` against random specs.

## Features

- `--preview` flag: print the computed crop/trim geometry and exit without
  encoding (dry run).
- `--dry-run` JSON output for scripting.
- Batch mode: accept a glob or a list of files on stdin and process each.
- Expose `cropdetect` sensitivity (`limit`, `round`) as flags.

## Robustness

- Handle inputs with no video stream and zero-length clips with a clear error
  rather than a probe exception.
- Consider `opencv-python-headless` to shrink the dependency and drop the
  macOS dylib clash entirely.
- Propagate a non-zero exit code from the CLI on failure (fire currently
  swallows some paths).

## Packaging / docs

- Publish to PyPI once the encode fixes ship (the pre-fix releases could not
  encode against current `ffmpeg-python`).
- Build the Jekyll docs in CI to catch broken links.
