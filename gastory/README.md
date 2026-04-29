# gastory

**gastory** (**G**ame **A**sset Fac**tory**) — LLM-driven game asset generation pipeline for Claude Code. Generates concept art, animation videos, frames, GIFs, and sprite sheets — all organized by project with automatic style consistency.

## Install

```
/plugin marketplace add SeokhyunKim/claude-plugins
/plugin install gastory@seokhyunkim
```

Run `/reload-plugins` after install.

## Setup: API keys

Keys are resolved in this priority order: env var → `~/.config/gastory/.env` → `./.env`.

The recommended setup (one-time, applies across all projects):

```bash
mkdir -p ~/.config/gastory
cat > ~/.config/gastory/.env <<'EOF'
OPENAI_API_KEY=sk-...
XAI_API_KEY=xai-...
FAL_KEY=...
EOF
chmod 600 ~/.config/gastory/.env
```

You only need the keys for the providers you use:

| Provider | Used for | Where to get |
|----------|----------|--------------|
| `OPENAI_API_KEY` | `gpt-image-2` concept art | https://platform.openai.com/api-keys (note: image models require organization verification) |
| `XAI_API_KEY` | `grok-imagine-image` concept art, `grok-imagine-video` | https://x.ai/api |
| `FAL_KEY` | Seedance 2.0 image-to-video | https://fal.ai/dashboard |

## Workflow

### 1. Create a project

A project is a working directory for a single asset bundle (e.g., one character with all their poses and animations).

```
/gastory:project swordman-1
```

Subsequent commands use this as the current project until you switch with `/gastory:project <other>`. List projects with `/gastory:project --list`.

### 2. Set the art style (optional but recommended)

The first time you run `/gastory:concept-art` in a new project, the `art-concept` skill walks you through preset selection (anime, pixel, cartoon, painterly, 3D, or custom). The chosen style auto-applies to all subsequent prompts in that project.

```
/gastory:style                            # show current
/gastory:style setup                      # rerun setup (overwrites)
/gastory:style --preset 2d-anime          # apply a preset directly
/gastory:style clear                      # remove
```

### 3. Generate concept art

```
/gastory:concept-art --name idle "검사가 검을 어깨에 걸친 채 여유롭게 서있는 자세"
```

Output: `gastory-output/<project>/concept/idle.png` + `idle.json` (prompt/model metadata).

For **character consistency** across multiple poses, use the first concept as a reference image:

```
/gastory:concept-art --from idle --name run "달리는 자세"
/gastory:concept-art --from idle --name attack "검을 휘두르는 자세"
```

This switches to image-to-image edit mode (default: OpenAI `gpt-image-2`; xAI is also supported via `--provider xai`), preserving the character's appearance from the reference while applying the new pose. Single-image consistency is typically 70–85%.

Override flags:
- `--no-concept` — skip the project art style for this call
- `--concept "<custom>"` — apply a one-off style without saving
- `--preset <name>` — use a different preset just this once
- `--provider {openai,xai}` — override default provider

### 4. Generate animation video

```
/gastory:animate --source attack --action attack "검을 휘두르는 모션"
```

Output: `gastory-output/<project>/animation/attack.mp4` (5 sec, 720p).

Uses fal.ai Seedance 2.0 Fast tier by default (~$0.24/sec, ~$1.20 for a 5-sec video). Generation takes 1–3 minutes. Audio is disabled by default (game asset use case); pass `--audio` to enable.

Override:
- `--provider xai` — use xAI `grok-imagine-video` instead
- `--duration N` — 4–15 seconds (default 5)
- `--resolution {480p,720p}` — default 720p
- `--free-camera` — disable the default camera/composition lock (use when you actually want camera movement)

By default, animate appends a camera-lock directive to your motion prompt — keeps the camera static, the character at constant size and screen position, and gaze direction preserved. This matches the game-asset use case. Pass `--free-camera` for cinematics or cutscenes that need camera movement.

### 5. Extract frames + GIF + sprite sheet

```
/gastory:extract-frames --action attack --gif --spritesheet
```

Output:

```
gastory-output/<project>/frames/
├── attack/                    # 50 PNG frames at 10 fps
│   ├── frame_001.png
│   └── ...
├── attack.gif                 # animated GIF (palettegen for quality)
└── attack_spritesheet.png     # grid (8 cols by default)
```

Tweaks:
- `--fps N` — extraction rate (default 10)
- `--cols N` — sprite-sheet column count
- `--gif-scale 320:-1` — GIF resize spec (ffmpeg syntax)

Requires `ffmpeg` and Pillow:
```bash
brew install ffmpeg
python3 -m pip install --user Pillow
```

## Project layout

```
gastory-output/
├── .current                       # active project (managed by /gastory:project)
└── <project>/
    ├── art-concept.json           # style settings (auto-applied)
    ├── concept/
    │   ├── <name>.png             # concept image
    │   └── <name>.json            # prompt + metadata sidecar
    ├── animation/
    │   ├── <action>.mp4
    │   └── <action>.json
    └── frames/
        ├── <action>/              # individual PNG frames
        ├── <action>.gif
        └── <action>_spritesheet.png
```

## End-to-end example

```bash
# One-time API key setup
mkdir -p ~/.config/gastory && printf 'XAI_API_KEY=...\nFAL_KEY=...\n' > ~/.config/gastory/.env

# In Claude Code:
/gastory:project swordman-1
/gastory:concept-art --name idle "검사 캐릭터, 검을 어깨에 걸친 자세"
# (style setup skill runs the first time — pick "2d-anime", add theme like "medieval fantasy")

/gastory:concept-art --from idle --name attack "검을 휘두르는 자세"
/gastory:animate --source attack --action attack "검을 휘두르는 모션"
/gastory:extract-frames --action attack --gif --spritesheet
```

## Direct script invocation

All slash commands wrap Python scripts you can also call directly:

```bash
python3 "$CLAUDE_PLUGIN_ROOT/bin/generate-concept-art.py" --help
python3 "$CLAUDE_PLUGIN_ROOT/bin/animate.py" --help
python3 "$CLAUDE_PLUGIN_ROOT/bin/extract-frames.py" --help
python3 "$CLAUDE_PLUGIN_ROOT/bin/project.py" --help
```

## Requirements

- Python 3.9+ (no third-party deps for image generation; `Pillow` only for sprite-sheet composition)
- `ffmpeg` (for video frame extraction and GIF composition)
- API keys for the providers you intend to use

## Plugin components

- **slash commands** in `commands/`: `/gastory:project`, `/gastory:style`, `/gastory:concept-art`, `/gastory:animate`, `/gastory:extract-frames`
- **skill** in `skills/art-concept/`: walks first-time setup and merges style into prompts
- **scripts** in `bin/`: API callers and local processing
