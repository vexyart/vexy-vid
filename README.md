# vexy-vid

High-performance video cropping and trimming CLI tool with automatic detection.

## Features

- **Crop** — crop video to specific dimensions with alignment control
- **Trim** — remove edges from video (like reversed CSS padding)
- **Scale** — resize video after cropping/trimming
- Automatic letterbox (black bar) detection and removal
- Automatic subtitle region detection and removal
- Hardware-accelerated encoding with automatic fallback
- PyAV-based frame extraction (50-100% faster than OpenCV)
- Numba-optimized pixel analysis (10-50x speedup)
- Parallel frame processing with buffer pooling

## Requirements

- Python 3.10+
- **ffmpeg** binary installed on your system (`brew install ffmpeg` / `apt install ffmpeg`)

> **Note:** ffmpeg is a system dependency and cannot be installed via pip. All other dependencies are installed automatically.

## Installation

```bash
# Install with uv (recommended)
uv pip install vexy-vid

# Or with pip
pip install vexy-vid

# Development install
uv pip install -e ".[dev]"
```

## Usage

### Crop — crop to specific dimensions

```bash
# Crop to exact pixels
vexy-vid crop --crop 1280x720 --input video.mp4

# Crop to aspect ratio
vexy-vid crop --crop 16:9 --Halign 0 --Valign 100 --input video.mp4

# Crop to percentage
vexy-vid crop --crop 50%x50% --input video.mp4

# Crop and scale
vexy-vid crop --crop 16:9 --scale 1920x1080 --input video.mp4
```

### Trim — remove edges

```bash
# Remove pixels from edges
vexy-vid trim --top 100 --bottom 50 --input video.mp4

# Remove percentage from sides
vexy-vid trim --left 10% --right 10% --input video.mp4

# Auto-detect and remove letterbox bars
vexy-vid trim --Letterbox --input video.mp4

# Auto-detect and remove subtitle region
vexy-vid trim --subtitles --bottom 20 --input video.mp4

# Trim and scale
vexy-vid trim --Letterbox --scale 1920x1080 --input video.mp4
```

### Common flags

| Flag | Description |
|------|-------------|
| `--input` / `-i` | Input video path (or pipe via stdin) |
| `--output` / `-o` | Output video path (auto-generated if omitted) |
| `--quality` / `-q` | Encoding quality: 0 (fast), 1 (balanced), 2 (quality) |
| `--verbose` / `-v` | Enable verbose logging |

### Size spec formats (for `--crop` and `--scale`)

| Format | Example | Description |
|--------|---------|-------------|
| `WxH` | `1280x720` | Exact pixel dimensions |
| `W:H` | `16:9` | Aspect ratio |
| `P%xP%` | `50%x50%` | Percentage of original |
| `Wx` | `1280x` | Width only (height = 100%) |
| `xH` | `x720` | Height only (width = 100%) |
| Mixed | `1280x50%` | Pixels and percentage |

## Performance

Optimizations over the original implementation:

- **PyAV multi-threaded decoding** — 50-100% faster frame extraction
- **Hardware encoder detection** — 300-500% encoding speedup (NVENC, QSV, AMF)
- **Producer-consumer pipeline** — 200-400% parallel processing improvement
- **Buffer pool memory management** — 25-50% reduced allocation overhead
- **Numba SIMD pixel operations** — 10-50x analysis speedup
- **Intelligent caching** — instant reprocessing of identical videos

## License

[Apache License 2.0](LICENSE)
