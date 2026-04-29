---
description: Generate an animation video from a concept image (image-to-video) via fal.ai Seedance 2.0 or xAI grok-imagine-video
argument-hint: [--project P] [--source N] [--action A] [--provider fal-seedance|xai] [--free-camera] [--no-concept | --concept "..."] <motion prompt>
allowed-tools: Bash(python3 *), Read, Write, Skill
---

The user wants to generate an animation video with these arguments:

$ARGUMENTS

## Step 1: Apply art concept hint (unless overridden)

Animation prompts are about motion, not style — but a brief style hint helps keep the video consistent with the concept art. Determine the final motion prompt:

- If `$ARGUMENTS` contains `--no-concept` → use the motion prompt verbatim. Strip `--no-concept` before passing to the script.
- If `$ARGUMENTS` contains `--concept "<custom>"` → invoke `gastory:art-concept` skill with `args='apply for=animate override-concept="<custom>"'`.
- Otherwise → invoke skill with `args='apply for=animate'`. The skill will:
  - Read `art-concept.json` (if missing, just use motion prompt as-is — do NOT trigger setup mid-animate; setup belongs to concept-art's flow)
  - Append `render_style` only as a brief hint (no background/framing — those are baked into the input image)

## Step 2: Run the animator

Project resolution:
- `--project` flag wins
- Else current project from `/gastory:project`

Source image:
- `--source <name>` → uses `gastory-output/<project>/concept/<name>.png`
- `--image <path>` → explicit override
- Neither → most recent PNG in `gastory-output/<project>/concept/`

Output:
- `--action <name>` → writes to `gastory-output/<project>/animation/<name>.mp4`
- Without `--action` → name derived from a slug of the motion prompt

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/animate.py" [flags...] "<merged motion prompt, properly shell-escaped>"
```

Strip art-concept-related flags before passing to the script.

Notes:
- `FAL_KEY` (default provider) or `XAI_API_KEY` must be in `~/.config/gastory/.env`
- Generation takes 1–3 minutes; the script polls and prints status updates
- fal.ai Seedance 2.0 Fast tier 720p costs ~24 cents per second of generated video (a 5-sec video ≈ 1.20 USD)
- Audio is disabled by default (game asset use case); pass `--audio` to enable
- **Camera/composition lock is applied by default** — the script automatically appends a directive to keep the camera fixed (no zoom/pan), the character at constant size and screen position, gaze direction preserved. This matches the game-asset use case. Pass `--free-camera` to disable when you actually want camera movement (cinematics, cutscenes).

## Step 3: Report

Report the MP4 and JSON paths. On error:
- Missing key → point to `~/.config/gastory/.env`
- "Exhausted balance" on fal → suggest topping up at https://fal.ai/dashboard/billing
- "content_policy_violation" → unusual without audio; suggest tweaking the motion prompt
- Timeout → suggest retrying or reducing `--duration`
- "현재 프로젝트가 설정되지 않았습니다" → suggest `/gastory:project <name>`
