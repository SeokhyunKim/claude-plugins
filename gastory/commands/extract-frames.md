---
description: Extract frames from a video; optionally produce GIF and sprite-sheet PNG (uses ffmpeg + Pillow)
argument-hint: [--project P --action A] | <video-path> [--fps N] [--gif] [--spritesheet] [--cols N]
allowed-tools: Bash(python3 *)
---

The user wants to extract frames with these arguments:

$ARGUMENTS

Two invocation modes:
1. **Project mode** (preferred): `--action <name>` reads `gastory-output/<project>/animation/<name>.mp4` and writes outputs under `gastory-output/<project>/frames/`. Project resolved from `--project` flag or current project.
2. **Direct path mode**: positional video path; outputs go to legacy `gastory-output/frames/<basename>/`.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/extract-frames.py" $ARGUMENTS
```

Defaults:
- `--fps 10` (10 frames per second)
- No GIF, no spritesheet unless flagged

Common patterns:
- `--action attack` → extract just frames
- `--action attack --gif` → frames + GIF
- `--action attack --gif --spritesheet` → all three artifacts

When complete, report:
- Number of frames and the frames directory
- GIF path if `--gif`
- Spritesheet path with grid dimensions if `--spritesheet`

If ffmpeg or Pillow is missing, surface a clear install hint (`brew install ffmpeg`, `pip install --user Pillow`).
