---
name: art-concept
description: Manages art concept (visual style) for gastory game asset projects. Sets up a project's visual style on first use through preset selection or free-form description, then automatically applies it to /gastory:concept-art and /gastory:animate prompts to ensure consistency. Also handles direct /gastory:style management. Invoke before generating any concept art or animation, and whenever the user runs /gastory:style.
---

# Art Concept Skill

Use this skill to manage the visual style ("art concept") of a gastory project. The art concept lives at `gastory-output/<project>/art-concept.json` and gets auto-applied to all asset generation commands within that project.

## Args

The caller passes one of these mode strings via `args`:

- `apply for=concept-art prompt="..."` — apply concept to a concept-art prompt
- `apply for=animate prompt="..."` — apply concept to an animate motion prompt
- `setup` — explicit full setup (overwrites existing)
- `show` — display current concept
- `clear` — delete the concept file (with user confirmation)

If args is empty or unclear, default to inferring from context (apply for whichever command is in flight, or setup if file is missing).

## Project resolution

Every step needs the current project name. Resolve in this order:
1. `--project` flag in the active slash command's `$ARGUMENTS`
2. `GASTORY_PROJECT` environment variable
3. Content of `./gastory-output/.current`

If none, abort: tell the user to run `/gastory:project <name>`.

## Phase 1: Setup (when file missing or `setup` mode)

### Step 1: Show preset options

Read `${CLAUDE_PLUGIN_ROOT}/skills/art-concept/presets.md` and present a numbered list:
1. **2d-anime** — 2D 애니메이션, lineart, 흰 배경
2. **2d-pixel** — 픽셀 아트, 16-bit 레트로, 투명 배경
3. **2d-painterly** — 페인터리 일러스트, 부드러운 브러시
4. **3d-render** — 3D 렌더, 모던 게임 에셋
5. **cartoon** — 카툰, 굵은 라인, 단순 셰이딩
6. **custom** — 직접 묘사

Briefly mention each preset's recommended use case (from `presets.md`).

### Step 2: Get user choice

Wait for user to pick. Accept either preset number/name or free-form description (treated as `custom`).

### Step 3: Refine

Once the preset is chosen, build the field set:

- For known presets: read fields from `presets.md` (render_style, background_default, framing_default, quality_keywords)
- For custom: use the user's text as `render_style`; ask for any missing pieces (background, framing) with sensible defaults like "plain white background" and "full body shot"

Then ask if the user wants to add anything theme-specific (e.g., "cyberpunk", "fantasy", "post-apocalyptic"). If so, add to `additional_notes`.

Detect contradictions and flag (e.g., user picks `2d-anime` but adds "photorealistic" → ask which they meant).

### Step 4: Save

Write to `gastory-output/<project>/art-concept.json` with this structure:

```json
{
  "preset": "<preset name or 'custom'>",
  "render_style": "...",
  "background": "...",
  "framing_default": "...",
  "quality_keywords": "...",
  "additional_notes": "...",
  "set_at": "<ISO 8601 timestamp>"
}
```

Confirm to the user with a summary of what's saved.

### Step 5: Continue

Return control to the calling command (concept-art or animate) by applying Phase 2 immediately on the user's original prompt.

## Phase 2: Apply (when file exists, mode = `apply`)

### Step 1: Read concept

Read `gastory-output/<project>/art-concept.json`.

### Step 2: Build merged prompt

**For `for=concept-art`** — full merge:

```
<user prompt>. Style: <render_style>. Background: <background>. Framing: <framing_default>. <quality_keywords>. <additional_notes>.
```

Skip any field that is empty. Don't double-include if the user already mentioned the same thing in their prompt.

**For `for=animate`** — partial merge (motion is the focus):

```
<user motion prompt>. Style hint: <render_style>.
```

Do NOT add background or framing — those are baked into the input image. Quality keywords and additional_notes also generally skipped (motion prompts don't benefit much).

### Step 3: Return merged prompt

The merged prompt becomes the input to the bin script. The slash command markdown is responsible for actually invoking the script with this merged prompt.

## Override flags (passed in caller's `$ARGUMENTS`)

The caller's slash command should detect these and pass appropriate args to the skill (or skip skill invocation entirely):

- `--no-concept` → caller skips the skill entirely; user prompt used as-is
- `--concept "<custom>"` → caller invokes skill with `args='apply prompt="..." override-concept="<custom>"'`; skill applies the override style without saving
- `--preset <name>` → caller invokes skill with `args='apply prompt="..." override-preset=<name>'`; skill loads named preset, applies, doesn't save

## Other modes

- **`show`**: cat `art-concept.json`, present nicely formatted
- **`clear`**: confirm with user, then delete the file

## Edge cases

- art-concept.json malformed → tell user, suggest running `/gastory:art-concept setup` to redo
- User says "nevermind" or interrupts setup → don't save partial state; tell user the next call will ask again
- No project set → halt with `/gastory:project <name>` suggestion
- File exists but missing fields → fill defaults silently, save back, continue
