# Troubleshooting

`vexy-vid` reports problems as Python exceptions. The last line of the traceback
names the problem. This page lists the common ones.

## `ffprobe error (see stderr output for detail)`

```text
ffmpeg._run.Error: ffprobe error (see stderr output for detail)
```

`vexy-vid` reads the video dimensions with `ffprobe` before doing anything else.
This error means `ffprobe` could not read the input. Check that:

1. The path passed to `--input` exists and is spelled correctly.
2. The file is a video that ffmpeg can open: `ffprobe movie.mp4`.
3. `ffprobe` is on your `PATH`: `ffprobe -version`.

If `ffprobe` itself is missing, the error is `FileNotFoundError` instead.
Install ffmpeg as described in [Installation](installation.md).

## `ValueError: No input provided via stdin`

You did not pass `--input`, so `vexy-vid` read a line from standard input and
the line was empty. Pass the path with `--input` (or `-i`), or pipe it in:

```bash
echo movie.mp4 | vexy-vid trim --Letterbox
```

If you run `vexy-vid crop` in a terminal without `--input` and without a pipe,
it waits for you to type a path and press Return.

## `ValueError: Trim values too large or invalid`

The requested trims would remove more than half of the width or height, or
leave nothing at all. `trim` checks this before encoding. Reduce the values.

For example, `--top 60%` on its own removes 60 % of the height and fails. A
combined `--top 30% --bottom 30%` also fails, because together they remove 60 %.

## `ValueError: Unrecognized size format`

The value of `--crop` or `--scale` is not one of the supported formats. Use
`16:9`, `1280x720`, `50%x50%`, `50%`, `1280x`, `x720` or a mix such as
`1280x50%`. See [Size formats](cli.md#size-formats).

## `No letterbox detected`

Neither `cropdetect` nor the frame analysis found black bars. Possible reasons:

- The bars are not black enough. The frame analysis treats rows with a mean
  brightness above 30 (out of 255) as picture.
- The bars are on the sides (pillarbox). Letterbox detection only trims the top
  and bottom. Use `--left` and `--right`.
- The first 60 seconds of the video differ from the rest, for example a
  full-frame intro. `cropdetect` only looks at the first 60 seconds.

Pass explicit values with `--top` and `--bottom` in these cases.

## `No subtitles detected`

Subtitle detection looks for bright text (above 200 out of 255) in the bottom
part of the frame. It does not find dark or coloured subtitles, and it cannot
see soft subtitles stored as a separate stream. Use `--bottom` with a fixed
value instead.

## A detection result looks wrong after the file changed

Detection results are cached in `~/.cache/vidcrop/analysis_cache.json`, keyed
by path, size and modification time. If you replaced a file with another of the
same size while keeping its modification time, the old result is reused. Delete
the cache file to force a new analysis.

## `objc[...]: Class AVFFrameReceiver is implemented in both ...`

On macOS, PyAV and `opencv-python` each ship their own copy of FFmpeg's
`libavdevice` library, and the Objective-C runtime warns about the duplicate
classes at start-up. The warning has had no functional effect in testing; the
output is correct. It does not appear on Linux or Windows.

## The encode uses `libx265` even though the machine has a GPU

`vexy-vid` supports NVIDIA NVENC, Intel Quick Sync and AMD AMF only, and only
when your ffmpeg build includes them and the encoder passes a test encode. Apple
VideoToolbox is not supported. Run with `--verbose` to see which encoders were
found. See [Hardware acceleration](hardware-acceleration.md).

## Getting more detail

Add `--verbose` to any command. It switches logging to debug level and raises
ffmpeg's log level from `error` to `info`, so the encoder's own messages appear.

```bash
vexy-vid trim --Letterbox --input movie.mp4 --verbose
```

If the problem persists, open an issue at
[github.com/vexyart/vexy-vid/issues](https://github.com/vexyart/vexy-vid/issues)
with the command, the full output, and the output of `ffmpeg -version`.
