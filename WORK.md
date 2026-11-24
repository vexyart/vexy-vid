---
this_file: WORK.md
---

# Work log

- PyPI 1.0.7 wheel provenance identifies `vexyart/vexy-vid`, `release.yml` and environment `pypi`. Its encoder, analysis and pipeline modules match tag `v1.0.7`.
- The suite passed all 49 tests, including seven ffmpeg integration tests (63% coverage). Both CLI commands returned exit 1 for empty stdin, missing input, audio-only input, an empty file, invalid geometry and failed encoding.
- `actionlint .github/workflows/release.yml`, `bash -n publish.sh` and the strict documentation build (`./build.sh docs`) passed.
