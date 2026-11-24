# PLAN

## Correctness and coverage

- Test the subtitle detectors with clips that have a subtitle band and clips that do not.
- Force a hardware encode to fail and verify the software fallback produces a usable file.
- Add an audio-bearing fixture and check that cropping and trimming copy its audio stream.
- Property-test `parse_size` and `parse_dimension` against generated specifications.

## CLI

- Add `--preview` to display the computed geometry and `--dry-run` to emit it as JSON. Both should skip encoding.
- Accept a glob or a list of input paths on stdin for batch processing.
- Expose the `cropdetect` settings `limit` and `round` as flags.
- Give zero-length clips a clear input error. Check both commands with an empty file and a zero-duration video.

## Maintenance

- Compare the macOS startup warning and package size with `opencv-python-headless`. See [issue 001](issues/001.md).
- Decide whether to track or archive the original `dev/` references, or keep them ignored. See [issue 002](issues/002.md).
