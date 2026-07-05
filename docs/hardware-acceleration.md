---
title: Hardware acceleration
layout: default
nav_order: 3
---

# Hardware acceleration

`vexy-vid` encodes on the GPU when it can. It never assumes a GPU is there — it
tests each encoder against your ffmpeg build and falls back the moment one is
missing.

## How the encoder is chosen

On the first encode, `vexy-vid` probes ffmpeg for each hardware encoder by
asking it to encode a single black frame. The ones that succeed are kept, in
this priority order:

| Priority | Encoder | Backend |
|----------|---------|---------|
| 1 | `hevc_nvenc` | NVIDIA NVENC (H.265) |
| 2 | `h264_nvenc` | NVIDIA NVENC (H.264) |
| 3 | `hevc_qsv` | Intel Quick Sync (H.265) |
| 4 | `h264_qsv` | Intel Quick Sync (H.264) |
| 5 | `hevc_amf` | AMD VCE (H.265) |
| 6 | `h264_amf` | AMD VCE (H.264) |

If none pass the probe, `vexy-vid` uses software encoding — `libx265`, then
`libx264`. A hardware encode that fails at runtime is also retried in software,
so a job never dies just because the GPU said no.

## Quality and the preset it maps to

`--quality` picks the speed/size trade-off. Each level maps to encoder-specific
presets and a constant-quality target:

| `--quality` | Intent | Example (libx264) |
|-------------|--------|-------------------|
| `0` | Fast | `preset=faster crf=22` |
| `1` | Balanced (default) | `preset=medium crf=20` |
| `2` | Quality | `preset=slow crf=18` |

Levels `0` and `1` prefer hardware; level `2` prefers software, where the
constant-rate-factor controls give finer control over the final quality.

## The ffmpeg dependency

ffmpeg is a system binary, not a Python package. Install it separately:

```bash
brew install ffmpeg          # macOS
sudo apt install ffmpeg      # Debian / Ubuntu
```

Which hardware encoders exist depends entirely on how that ffmpeg was built —
a stock Homebrew ffmpeg on Apple Silicon, for instance, exposes no NVENC, so
`vexy-vid` will land on `libx265`/`libx264`. That is expected, and correct.
