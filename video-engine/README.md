# SatisfyForge Video Assembly Engine

Owned, zero-cost-first vertical video normalization and QA built on FFmpeg. The goal is to handle the repetitive technical work that creator subscriptions often charge for while keeping the media inputs and publishing decisions under SatisfyForge control.

## What v1.1 does

- Converts a source video to 1080x1920 vertical output by default, or optional
  2160x3840 vertical 4K (upscaling is not a substitute for true 4K source media).
- Forces constant 30 fps to reduce social-publisher frame-rate validation failures.
- Encodes H.264 with `yuv420p` and fast-start MP4 metadata.
- Preserves source audio when present or replaces it with an optional voiceover.
- Applies EBU-style loudness normalization to supplied voiceover.
- Burns optional SRT/ASS captions into the output.
- Uses ffprobe after rendering to fail closed when codec, pixel format, resolution, frame rate or duration are wrong.
- Requires no paid API.
- Accepts a scene-by-scene JSON research storyboard with verified/unverified/
  speculative claim tags, source-URL reminders, scene rights notes, and a
  timed shot list; a separate render mode stitches real licensed clips and
  stills under a pre-recorded human-reviewed narration track.

## Requirements

- Python 3.10+
- `ffmpeg` and `ffprobe` available on PATH **or** in the owned local runtime at `~/SatisfyForge/tools/media-runtime`
- Optional explicit overrides: `SATISFYFORGE_FFMPEG` and `SATISFYFORGE_FFPROBE`

## Owned local runtime

On the authorized Mac, SatisfyForge can use its private user-local media runtime without committing large binaries to Git. The resolver checks PATH first, then the explicit environment overrides, then the owned runtime. This keeps video rendering zero-cost and avoids requiring Homebrew or a paid editor.

The current local runtime is intentionally an **environment dependency**, not a repository artifact. Never commit FFmpeg binaries to this repo.

## Render

```bash
python video-engine/forge_video.py render \
  --input input.mp4 \
  --voiceover narration.wav \
  --captions captions.srt \
  --output publish-ready.mp4
```

To render a 4K vertical master when source quality and available hardware justify it,
add `--resolution 2160x3840`. Actual platform uploads may downsample it.

## Multi-scene research video (new)

The example [research mystery storyboard](examples/research-mystery-story.json)
is a **template**, not a complete researched episode: placeholder assets,
permissions, sourcing and spoken audio must be supplied and reviewed.

```bash
python3 video-engine/storyboard.py \
  --manifest video-engine/examples/research-mystery-story.json
```

This first command prepares and prints the scene timeline **without rendering,
paying, uploading or making brokerage calls**. It doesn't require the listed
media to exist yet. For actual rendering:

1. Place original/permissioned clips, stills, recorded narration and SRT/ASS
   captions under `video-engine/examples/assets/` or create a private manifest
   folder with its own `assets/` directory.
2. Replace example rights notes and audit the actual primary sources.
3. Review and time the narration to the summed scene durations (within 0.75s).
4. Run:

```bash
python3 video-engine/storyboard.py \
  --manifest /path/to/your-story/story.json \
  --render --output /path/to/your-story/preview.mp4
```

Optionally append `--resolution 2160x3840` for a 4K vertical output.
The renderer makes normalized silent scene clips, stitches them, maps and
normalizes the supplied narration, burns optional captions, then probes the
finished video. Scene timing, narration length, rights declarations, missing
assets and path traversal are validated. This does **not** independently prove
copyright permissions, factual accuracy, a natural voice, or good pacing.
Perform `quality --strict` plus a human watch/listen pass before considering
any specific platform publication approval.

## Validate an existing file

```bash
python video-engine/forge_video.py validate --input publish-ready.mp4
```

A successful validation exits `0`. A format problem exits non-zero and prints the exact failed checks.

## Deeper technical and creative review checks

```bash
python video-engine/forge_video.py quality --input publish-ready.mp4
python video-engine/forge_video.py quality --input publish-ready.mp4 --strict
```

The `quality` command also runs FFmpeg black-frame, frozen-scene and audio-silence
detectors. It includes time-coded intervals in JSON output. In normal mode,
detected intervals are review warnings because deliberate dramatic pauses,
static footage and black transitions may be legitimate. `--strict` fails on
any detected segment. An FFmpeg filter failure is always an error, not a pass.

This improves technical screening but cannot judge storytelling, narration
naturalness, factual accuracy, licensing, audience retention, or visual taste.
**Listen and watch the completed preview before publishing.**

## Scope boundary

This tool assembles and validates media. It does not source copyrighted footage, impersonate creators, bypass platform rules, publish without authorization or claim that a post succeeded. Source media must be owned, licensed, public-domain or otherwise lawfully usable.

## Next additions

1. Original high-quality licensed assets and a truly compelling, fact-checked
   documentary episode with human-reviewed spoken delivery.
2. Caption generation/import and scene-aware sync automation.
3. Reusable motion graphics, lower-thirds/title cards and transitions.
4. Safe music ducking and background-bed mixing, with rights verification.
5. Thumbnail extraction and systematic creative/retention review.
6. Explicitly authorized platform publication after identity and dedupe checks.
