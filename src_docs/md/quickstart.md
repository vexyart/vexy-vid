# Quick start

This page takes one file through the main operations. Each command writes a new
file next to the input and leaves the input unchanged.

## Prerequisites

- `vexy-vid` and `ffmpeg` installed. See [Installation](installation.md).
- A video file. The examples use `movie.mp4`, a 640×480 clip with 64-pixel
  black bars at the top and bottom.

## Remove letterbox bars

1. Run `trim` with `--Letterbox`:

    ```bash
    vexy-vid trim --Letterbox --input movie.mp4
    ```

2. Read the log. `vexy-vid` reports what it found and what it will do:

    ```text
    Detecting letterbox bars...
    Detected letterbox crop: 640x352 at (0,64)
    Letterbox detected via FFmpeg: top=64, bottom=64
    Crop would significantly change aspect ratio: 1.33 -> 1.82
    Trimming: top=64, right=0, bottom=64, left=0
    Result dimensions: 640x352
    Output: movie_trim_llb.mp4
    Using encoder: libx265 (quality: balanced)
    ```

The result is `movie_trim_llb.mp4`, 640×352 pixels. The aspect-ratio warning is
expected here: removing the bars changes the frame shape on purpose.

## Crop to an aspect ratio

1. Run `crop` with a ratio:

    ```bash
    vexy-vid crop --crop 16:9 --input movie.mp4
    ```

2. `vexy-vid` keeps the full width (640) and computes the height for 16:9
   (360). It centres the window vertically because `--Valign` defaults to `50`.

The result is `movie_crop_16-9.mp4`, 640×360 pixels.

To keep the bottom of the frame instead of the middle, set `--Valign 100`:

```bash
vexy-vid crop --crop 16:9 --Valign 100 --input movie.mp4
```

## Trim fixed amounts

```bash
vexy-vid trim --top 100 --bottom 50 --input movie.mp4
```

This removes 100 pixels from the top and 50 from the bottom. The result is
`movie_trim_t100_b50.mp4`, 640×330 pixels.

Use percentages for proportional trims:

```bash
vexy-vid trim --left 10% --right 10% --input movie.mp4
```

## Crop and scale in one pass

```bash
vexy-vid crop --crop 16:9 --scale 1920x1080 --input movie.mp4
```

`vexy-vid` crops to 16:9 first, then scales the cropped frame to 1920×1080. Both
steps run in the same ffmpeg filter chain, so the video is encoded only once.

## Choose the output name

Pass `--output` to set the file name yourself:

```bash
vexy-vid trim --Letterbox --input movie.mp4 --output movie-clean.mp4
```

An existing file at that path is overwritten without a prompt.

## Pass the input path on standard input

When `--input` is missing, `vexy-vid` reads one line from standard input and
uses it as the path:

```bash
echo movie.mp4 | vexy-vid crop --crop 50%x50%
```

## Next steps

- [CLI reference](cli.md) lists every flag and size format.
- [Automatic detection](detection.md) explains `--Letterbox` and `--subtitles`.
