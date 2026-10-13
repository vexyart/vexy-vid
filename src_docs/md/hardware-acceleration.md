# Hardware acceleration

`vexy-vid` encodes on the GPU when ffmpeg can. It does not assume that a GPU
exists: it tests each encoder against your ffmpeg build and uses only the ones
that work.

## How the encoder is chosen

The first time a `vexy-vid` process encodes, it tests each encoder in turn by
asking ffmpeg to encode one 64×64 black frame with it. An encoder that finishes
within 5 seconds with exit status 0 is available. The results are kept for the
rest of the process.

Hardware encoders are tested in this priority order:

| Priority | Encoder | Backend |
|----------|---------|---------|
| 1 | `hevc_nvenc` | NVIDIA NVENC (H.265) |
| 2 | `h264_nvenc` | NVIDIA NVENC (H.264) |
| 3 | `hevc_qsv` | Intel Quick Sync (H.265) |
| 4 | `h264_qsv` | Intel Quick Sync (H.264) |
| 5 | `hevc_amf` | AMD AMF (H.265) |
| 6 | `h264_amf` | AMD AMF (H.264) |

Then the software encoders: `libx265`, then `libx264`.

`vexy-vid` picks the first available encoder in this combined list. On a
machine without a supported GPU encoder, that is `libx265` if your ffmpeg has
it, otherwise `libx264`. If no encoder passes the test, `libx264` is used.

The log shows the result:

```text
Detected 2 available encoders: ['libx265', 'libx264']...
Using encoder: libx265 (quality: balanced)
```

!!! note "Apple VideoToolbox"
    The VideoToolbox encoders on macOS (`h264_videotoolbox`,
    `hevc_videotoolbox`) are not in the list. On a Mac, `vexy-vid` encodes
    with `libx265` or `libx264`.

## Fallback when a hardware encode fails

If ffmpeg fails while encoding with a hardware encoder, `vexy-vid` logs the
error and runs the same job again with `libx264`:

```text
Hardware encoding failed with hevc_nvenc: ...
Falling back to software encoding...
```

If the software encode also fails, or if the failed encoder was already a
software encoder, the error is raised and the command exits with status 1.

## Quality levels

`--quality` takes `0`, `1` or `2`. Each level maps to settings for each
encoder family:

| Encoder | `0` fast | `1` balanced (default) | `2` quality |
|---------|----------|------------------------|-------------|
| `hevc_nvenc`, `h264_nvenc` | `preset=p1 tune=ll` | `preset=p4 cq=20` | `preset=p7 cq=18` |
| `hevc_qsv`, `h264_qsv` | `preset=veryfast global_quality=22` | `preset=medium global_quality=20` | `preset=slow global_quality=18` |
| `hevc_amf`, `h264_amf` | `quality=speed rc=cqp qp_i=22` | `quality=balanced rc=cqp qp_i=20` | `quality=quality rc=cqp qp_i=18` |
| `libx265`, `libx264` | `preset=faster crf=22` | `preset=medium crf=20` | `preset=slow crf=18` |

Lower `crf`, `cq`, `global_quality` and `qp_i` values mean higher quality and
larger files.

Levels `0` and `1` ask for a hardware encoder first. Level `2` asks for the
first available encoder without that preference; because hardware encoders come
first in the list, this is still a hardware encoder when one is available.

## The ffmpeg build decides

Which encoders are available depends on how your ffmpeg was compiled and on
the drivers installed. A typical Homebrew ffmpeg on Apple Silicon has no NVENC,
Quick Sync or AMF support, so `vexy-vid` uses `libx265`. That is expected.

To see which encoders your ffmpeg reports:

```bash
ffmpeg -hide_banner -encoders | grep -E 'nvenc|qsv|amf|libx26'
```

An encoder can appear in this list and still fail the test, for example when
the GPU driver is missing. `vexy-vid` only uses encoders that pass the test.
