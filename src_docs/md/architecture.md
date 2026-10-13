# Architecture

`vexy-vid` is a small Python package in `src/vexy_vid/`. The command-line
interface is a thin layer over two functions, `crop()` and `trim()`. Each one
measures the input, builds an ffmpeg filter string and hands it to the encoder.

## Data flow

```text
vexy-vid trim --Letterbox -i movie.mp4
        │
        ▼
cli.main()            fire.Fire({"crop": crop, "trim": trim})
        │
        ▼
trim.trim()           get_input_path() → get_video_info()  (ffprobe: 640x480)
        │             detect_letterbox_ffmpeg()             (top=64, bottom=64)
        │             validate_crop_parameters()
        │             generate_output_path()                (movie_trim_llb.mp4)
        ▼
video filter          "crop=640:352:0:64"
        │
        ▼
encoder.process_video_with_hardware_encoding()
                      HardwareEncoderDetector.get_best_encoder()  (libx265)
                      ffmpeg -i movie.mp4 -vf crop=640:352:0:64 -c:v libx265 -acodec copy ...
```

## Modules

| Module | Contents |
|--------|----------|
| `cli.py` | `main()`, the console entry point. Configures `loguru` and exposes `crop` and `trim` through Fire. |
| `crop.py` | `crop()`: computes the window size and offset and builds `crop=W:H:X:Y`, optionally followed by `scale=W:H`. |
| `trim.py` | `trim()`: runs detection, combines detected and manual trims, validates the result and builds the filter. |
| `utils.py` | `parse_size()`, `parse_dimension()`, `get_video_info()`, `get_input_path()`, `generate_output_path()`, `validate_crop_parameters()` and the `VideoAnalysisCache` class. |
| `analysis.py` | `detect_letterbox_ffmpeg()`, `detect_letterbox_opencv_parallel()`, `detect_subtitles_morphological_parallel()`, `detect_subtitles_brightness_fast()`, and the Numba-compiled pixel loops. |
| `frames.py` | `extract_frame_fast()`: decodes one frame with PyAV, with an ffmpeg command-line fallback. |
| `pipeline.py` | `VideoProcessingPipeline` (a reader thread and up to four worker threads) and `FrameBufferPool`. |
| `encoder.py` | `HardwareEncoderDetector` and `process_video_with_hardware_encoding()`. |
| `constants.py` | Detection thresholds, pool and queue sizes, and the encoder priority lists. |

## Frame analysis pipeline

The OpenCV letterbox fallback and the subtitle shape analysis use
`VideoProcessingPipeline.process_frames_parallel()`:

1. A reader thread calls `extract_frame_fast()` for each requested frame index
   and puts `(index, frame)` pairs on an input queue.
2. Up to four worker threads take frames from the queue, run the analysis
   function on each, and put `(index, result)` pairs on an output queue.
3. When the reader finishes, it puts one `None` sentinel on the input queue.
   Each worker that receives it puts it back before exiting, so every worker
   sees it.
4. The collector gathers results until every worker has signalled the end, then
   returns the results in the original frame order. Frames that failed give
   `None`.

The per-pixel loops (`calculate_row_luminance`, `find_black_borders`,
`count_bright_pixels_per_row`) are compiled with Numba's `@jit(nopython=True)`.
Two of them use `parallel=True` to spread rows across CPU cores.

## Using vexy-vid from Python

The command functions are plain Python functions. Their keyword arguments match
the command-line flags:

```python
from vexy_vid.crop import crop
from vexy_vid.trim import trim

crop(input="movie.mp4", crop="16:9", Valign=100)
trim(input="movie.mp4", Letterbox=True, output="movie-clean.mp4")
```

Both functions return `None`, write the output file, and raise an exception on
failure.

The size parser is useful on its own:

```python
from vexy_vid.utils import parse_size

parse_size("16:9", 1440, 1080)      # (1440, 810)
parse_size("50%x720", 1920, 1080)   # (960, 720)
```

The installed version is available as `vexy_vid.__version__`:

```python
import vexy_vid
print(vexy_vid.__version__)
```

## Design notes

- **ffmpeg filters go in through the output stage.** The crop and scale chain
  is passed to `ffmpeg-python` as the `vf` output option, and global flags such
  as `-loglevel` are attached with `.global_args()`.
- **`cropdetect` needs `info` logging.** The detector captures ffmpeg's
  standard error and runs at `-loglevel info` (or `verbose` with `--verbose`),
  because `cropdetect` prints its results at that level.
- **Import order.** `av` is imported before `cv2`. Both bundle their own
  `libavdevice` on macOS; see [Troubleshooting](troubleshooting.md).
- **Capitalised parameters.** `Halign`, `Valign` and `Letterbox` keep their
  capital letters because Fire uses parameter names as flag names. Renaming
  them would change the command-line interface.
