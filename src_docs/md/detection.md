# Automatic detection

`trim` can measure two things on its own: the black letterbox bars at the top
and bottom of the frame (`--Letterbox`), and the subtitle band near the bottom
(`--subtitles`). Each has a primary method and a fallback.

## Letterbox detection

### Primary method: ffmpeg `cropdetect`

`vexy-vid` runs ffmpeg with the `cropdetect=24:16:0` filter over the first 60
seconds of the input and discards the decoded output:

```bash
ffmpeg -hide_banner -i movie.mp4 -t 60 -vf cropdetect=24:16:0 -f null - -loglevel info
```

`cropdetect` prints lines such as `crop=640:352:0:64` while it runs. `vexy-vid`
reads the last of these lines and turns it into trims:

- top trim = the `y` offset (`64`)
- bottom trim = input height − (`y` + detected height) = 480 − (64 + 352) = `64`

Only the vertical values are used. The `x` offset and width are ignored, so
pillarbox bars on the sides are not removed.

### Fallback: frame analysis

If `cropdetect` reports nothing usable, `vexy-vid` samples 10 frames spread
evenly across the whole video and analyses each one:

1. The frame is decoded with PyAV and downscaled to 640 pixels wide.
2. It is converted to greyscale.
3. The mean brightness of every row is computed.
4. Rows are scanned from the top edge downward, through the top third of the
   frame, until a row's mean brightness is above 30 (on a 0–255 scale). The
   rows before it are the top bar.
5. The same scan runs from the bottom edge upward through the bottom third.

The median top and bottom values across all sampled frames are scaled back to
the original resolution and used as the trims. If no frame can be analysed, or
both values are zero, `trim` logs `No letterbox detected` and continues without
a letterbox trim.

## Subtitle detection

### Primary method: shape analysis

`vexy-vid` samples 20 frames between 10 % and 90 % of the video, skipping the
start and end where titles and credits often appear. For each frame:

1. The frame is downscaled to 640 pixels wide.
2. Only the bottom 30 % of the frame is kept.
3. Pixels brighter than 200 become white; all others become black.
4. The white areas are dilated with a 20×3 rectangle, twice, so that the
   letters of one line merge into one shape.
5. Each shape's bounding box is tested. A shape counts as subtitle text if it
   is wider than 10 % of the frame, taller than 10 pixels, and less than half
   the height of the bottom region.
6. The top edge of the highest qualifying shape is recorded.

The highest top edge across all frames is scaled to the original resolution.
The bottom trim is the distance from that edge to the bottom of the frame, plus
a 20-pixel margin.

### Fallback: brightness scan

If the shape analysis finds nothing, `vexy-vid` samples 30 frames between 10 %
and 90 % of the video and counts bright pixels (above 200) in each row of the
bottom quarter. Rows with more than 50 bright pixels contribute to an average.
The first row whose average is above 30 % of the maximum marks the top of the
subtitle band; the bottom trim is computed from it with a 10-pixel margin.

### Safety limit

Subtitle detection can mistake bright scenery for text. If the detected band is
taller than half of the content height (the height after letterbox trims),
`trim` reduces the subtitle trim to 30 % of the content height and logs:

```text
Subtitle trim adjusted to <N>px to preserve content
```

!!! tip
    Detection works best on videos with white or light subtitles burned into
    the picture. For yellow or dark subtitles, or for a known fixed band, pass
    `--bottom` with an explicit value instead.

## The analysis cache

Every detection result is stored in a JSON file:

```text
~/.cache/vidcrop/analysis_cache.json
```

Each entry is keyed by an MD5 hash of the file path, the file size and the
modification time, plus the analysis type and sample count. A second
`--Letterbox` or `--subtitles` run on an unchanged file reads the stored value
and skips the analysis. Log lines such as `Using cached letterbox detection
result` (visible with `--verbose`) show when this happens.

Editing or re-saving the file changes its size or modification time, so the
next run analyses it again. To clear all stored results, delete the file:

```bash
rm ~/.cache/vidcrop/analysis_cache.json
```

## Tuning values

The thresholds live in `src/vexy_vid/constants.py`. They are not exposed as
command-line flags.

| Constant | Value | Used for |
|----------|-------|----------|
| `BLACK_THRESHOLD` | `30` | Row brightness below which a row counts as black |
| `SUBTITLE_BRIGHTNESS_THRESHOLD` | `200` | Pixel brightness above which a pixel counts as text |
| `MORPH_KERNEL_WIDTH` / `MORPH_KERNEL_HEIGHT` | `20` / `3` | Dilation rectangle that joins letters |
| `MIN_SUBTITLE_WIDTH_RATIO` | `0.1` | Minimum text-shape width, as a fraction of the frame width |
| `MAX_SUBTITLE_HEIGHT_RATIO` | `0.5` | Maximum text-shape height, as a fraction of the bottom region |
| `ANALYSIS_FRAME_WIDTH` | `640` | Width that frames are downscaled to before analysis |
| `CACHE_DIR` | `~/.cache/vidcrop` | Location of the analysis cache |
