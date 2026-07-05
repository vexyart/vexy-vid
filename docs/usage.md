---
title: Usage
layout: default
nav_order: 2
---

# Usage

Two commands: `crop` and `trim`. Both read a video, write a video, and take a
`--scale` to resize the result.

## crop — keep a shape, discard the rest

```bash
# Exact pixels
vexy-vid crop --crop 1280x720 --input video.mp4

# Aspect ratio, aligned to the bottom of the frame
vexy-vid crop --crop 16:9 --Halign 0 --Valign 100 --input video.mp4

# Half size
vexy-vid crop --crop 50%x50% --input video.mp4

# Crop then upscale
vexy-vid crop --crop 16:9 --scale 1920x1080 --input video.mp4
```

`--Halign` and `--Valign` place the crop window: `0` = left/top, `50` = center
(the default), `100` = right/bottom.

## trim — cut edges away

```bash
# Remove pixels from named edges
vexy-vid trim --top 100 --bottom 50 --input video.mp4

# Remove a percentage from the sides
vexy-vid trim --left 10% --right 10% --input video.mp4

# Find and remove letterbox bars
vexy-vid trim --Letterbox --input video.mp4

# Find and remove the subtitle band
vexy-vid trim --subtitles --input video.mp4

# Trim bars, then rescale
vexy-vid trim --Letterbox --scale 1920x1080 --input video.mp4
```

`--Letterbox` and `--subtitles` combine with explicit edge values — the larger
trim on each edge wins, so manual and automatic cuts never fight.

## Common flags

| Flag | Meaning |
|------|---------|
| `--input` / `-i` | Input path, or pipe a path via stdin |
| `--output` / `-o` | Output path (auto-named from the operation if omitted) |
| `--quality` / `-q` | `0` fast, `1` balanced (default), `2` quality |
| `--verbose` / `-v` | Verbose logging |

## Size-spec formats

Used by `--crop` and `--scale`.

| Format | Example | Meaning |
|--------|---------|---------|
| `WxH` | `1280x720` | Exact pixels |
| `W:H` | `16:9` | Aspect ratio |
| `P%xP%` | `50%x50%` | Percentage of original |
| `P%` | `50%` | Same percentage on both axes |
| `Wx` | `1280x` | Width only, height unchanged |
| `xH` | `x720` | Height only, width unchanged |
| Mixed | `1280x50%` | Pixels on one axis, percent on the other |
