---
title: Home
layout: default
nav_order: 1
---

# vexy-vid

Black bars steal pixels. `vexy-vid` takes them back — and trims, crops, or
rescales the frame in one pass, at hardware speed.

It is a command-line tool. Point it at a video, name a shape, and it hands you a
smaller file with the content intact. When you do not know the shape, it finds
the letterbox bars or the subtitle band for you.

```bash
uv pip install vexy-vid   # ffmpeg must already be on your PATH
vexy-vid trim --Letterbox --input movie.mp4
```

## What it does

- **Crop** to exact pixels, an aspect ratio, or a percentage.
- **Trim** edges like reversed CSS padding — top, bottom, left, right.
- **Detect** letterbox bars (via ffmpeg `cropdetect`, with an OpenCV fallback).
- **Detect** the subtitle band and trim it away.
- **Scale** the result in the same command.
- **Encode** on the GPU when one is present (NVENC, Quick Sync, AMF), falling
  back to `libx265` / `libx264` when it is not.

## Requirements

- Python 3.10 or newer.
- The **ffmpeg** binary, installed separately: `brew install ffmpeg` on macOS,
  `apt install ffmpeg` on Debian/Ubuntu. It is not a pip package.

## Next steps

- [Usage](usage.md) — every command, flag, and size-spec format.
- [Hardware acceleration](hardware-acceleration.md) — how the encoder is chosen.

Source and issues live at
[github.com/vexyart/vexy-vid](https://github.com/vexyart/vexy-vid).
