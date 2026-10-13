# vexy-vid

`vexy-vid` is a command-line tool that crops, trims and rescales video files.
It can find letterbox bars and the subtitle band on its own, and it encodes the
result with a hardware encoder when your ffmpeg build has one.

![vexy-vid icon](assets/icon.png){ width="160" }

## What goes in, what comes out

You give `vexy-vid` one video file and a description of the frame you want.
It builds an ffmpeg filter chain (`crop`, optionally followed by `scale`),
re-encodes the video stream, copies the audio stream unchanged, and writes a new
file next to the original.

```bash
vexy-vid trim --Letterbox --input movie.mp4
```

For a 640×480 clip with 64-pixel black bars at the top and bottom, this command:

1. Runs ffmpeg's `cropdetect` filter over the first 60 seconds.
2. Reads the detected content area, `640x352` at offset `(0,64)`.
3. Removes 64 pixels from the top and 64 pixels from the bottom.
4. Writes `movie_trim_llb.mp4`, a 640×352 video.

## Two commands

| Command | Use it to | Example |
|---------|-----------|---------|
| `crop` | Keep a window of a given size and discard the rest | `vexy-vid crop --crop 16:9 --input video.mp4` |
| `trim` | Remove a number of pixels or a percentage from each edge | `vexy-vid trim --top 100 --bottom 50 --input video.mp4` |

Both commands accept `--scale` to resize the result in the same pass, and
`--quality` to choose between fast and high-quality encoding.

## Features

- Crop to exact pixels (`1280x720`), an aspect ratio (`16:9`) or a percentage
  (`50%x50%`), with `--Halign` and `--Valign` to place the crop window.
- Trim edges like reversed CSS padding: `--top`, `--right`, `--bottom`, `--left`.
- Detect letterbox bars with ffmpeg `cropdetect`, with an OpenCV fallback.
- Detect the subtitle band at the bottom of the frame and trim it away.
- Encode with NVIDIA NVENC, Intel Quick Sync or AMD AMF when ffmpeg supports
  them, and fall back to `libx265` or `libx264` when it does not.
- Cache detection results so a second run on the same file skips the analysis.

## Requirements

- Python 3.10 or newer.
- The `ffmpeg` binary on your `PATH`. It is a system program, not a Python
  package. See [Installation](installation.md).

## Where to go next

- [Installation](installation.md): install `vexy-vid` and ffmpeg.
- [Quick start](quickstart.md): crop and trim your first file.
- [CLI reference](cli.md): every command, flag and size format.
- [Automatic detection](detection.md): how letterbox and subtitle detection work.
- [Hardware acceleration](hardware-acceleration.md): how the encoder is chosen.
- [Architecture](architecture.md): the modules and the Python API.
- [Troubleshooting](troubleshooting.md): common errors and what they mean.

Source code and issues: [github.com/vexyart/vexy-vid](https://github.com/vexyart/vexy-vid).
