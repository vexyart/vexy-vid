## TODO

### Completed

- [x] Rename `clip` to `crop` in dev/vidcrop.py
- [x] Change `--size` to `--crop` in dev/vidcrop.py
- [x] Add optional `--scale` to both `crop` and `trim` operations
- [x] Refactor into full `vexy-vid` Python package with `vexy-vid crop` and `vexy-vid trim` CLI commands
- [x] Use hatch & uv for building & publishing with hatch-vcs for gittag-based semver
- [x] Ensure uv/pip installation installs all necessary dependencies
- [x] Write AGENTS.md
- [x] Write README.md
- [x] Write TODO.md
- [x] Implement the package (all 10 modules)
- [x] Smoketest: `uv pip install -e .` and `vexy-vid crop --help` / `vexy-vid trim --help`

### Known Issues

- [ ] PyAV and opencv-python dylib conflict on macOS (objc warnings) — cosmetic only, no functional impact. See issues/001.md
- [ ] `dev/` directory is gitignored — source script is not tracked in version control. See issues/002.md

### Future

- [ ] Add unit tests for utils.py (parse_dimension, parse_size, generate_output_path)
- [ ] Add integration tests (requires ffmpeg + sample video)
- [ ] Create git tag `v0.1.0` for first hatch-vcs release
- [ ] Publish to PyPI
- [ ] Consider opencv-python-headless to reduce dylib conflicts
- [ ] Add `--preview` flag to show crop/trim preview without encoding
