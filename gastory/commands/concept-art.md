---
description: Generate concept art (character, background, building, prop, etc.) using OpenAI gpt-image-2 or xAI grok-imagine-image. Supports image-to-image with --from <ref-name> for character consistency.
argument-hint: [--project P] [--name N] [--from <ref>] [--provider openai|xai] [--no-concept | --concept "..." | --preset <name>] <description>
allowed-tools: Bash(python3 *), Read, Write, Skill
---

The user wants to generate concept art with these arguments:

$ARGUMENTS

## Step 1: Apply art concept (unless overridden)

Before calling the script, determine the final prompt by handling the project's art concept:

- If `$ARGUMENTS` contains `--no-concept` → skip art concept entirely; use the user's prompt verbatim. Strip the `--no-concept` flag before passing to the script.
- If `$ARGUMENTS` contains `--concept "<custom>"` → invoke the `gastory:art-concept` skill with `args='apply for=concept-art override-concept="<custom>"'` so the skill applies the override without saving.
- If `$ARGUMENTS` contains `--preset <name>` → invoke skill with `args='apply for=concept-art override-preset=<name>'`.
- Otherwise → invoke skill with `args='apply for=concept-art'`. The skill will:
  - Check `gastory-output/<project>/art-concept.json`
  - If missing: walk the user through Phase 1 setup, save the concept
  - Then merge the saved concept into the user's prompt and return the merged prompt

## Step 2: Run the generator

Use the merged prompt (output of Step 1) as the actual prompt argument to the script.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/generate-concept-art.py" [other flags...] "<merged prompt, properly shell-escaped>"
```

The script defaults to `--provider openai` (`gpt-image-2`) for both generation and `--from` edits. Pass `--provider xai` only when the user explicitly requests it.

Strip `--no-concept`, `--concept`, `--preset` flags before passing to the script (the script doesn't know them). The `--from <name>` flag IS understood by the script — pass it through.

**`--from` mode (image-to-image)**: when the user passes `--from <ref-name>`, the script sends `gastory-output/<project>/concept/<ref-name>.png` as a reference image to the provider's edit endpoint (OpenAI `images/edits` by default, xAI `images/edits` if `--provider xai`). This preserves the character's appearance from the reference while applying the new prompt as the desired pose/scene.

## Step 3: Report

Output paths: `gastory-output/<project>/concept/<name>.png` plus a JSON sidecar.

On error:
- Missing API key → point to `~/.config/gastory/.env`
- "현재 프로젝트가 설정되지 않았습니다" → tell the user to run `/gastory:project <name>` first
- `billing_hard_limit_reached` or org/verification error on OpenAI → suggest retrying with `--provider xai` as a fallback
