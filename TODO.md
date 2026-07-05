## TODO

Flat view of `PLAN.md`. Completed items are recorded in `CHANGELOG.md`.

### Next

- [ ] Add subtitle-detection fixtures to raise `analysis.py` coverage
- [ ] Add an audio-bearing fixture clip to exercise `-acodec copy`
- [ ] `--preview` / `--dry-run` flag (print geometry, skip encode)
- [ ] Batch mode (glob or stdin list)
- [ ] Expose `cropdetect` `limit`/`round` as flags
- [ ] Clear error on inputs with no video stream / zero-length clips
- [ ] Non-zero CLI exit code on failure
- [ ] Evaluate `opencv-python-headless` to drop the macOS dylib clash
- [ ] Publish to PyPI (post encode fixes)
- [ ] Build Jekyll docs in CI

### Known, low-priority

- [ ] PyAV/opencv-python `libav` dylib clash on macOS — cosmetic objc warning.
