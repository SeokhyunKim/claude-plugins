---
description: Show, set, or clear the art style (visual concept) for the current gastory project
argument-hint: [setup | show | clear | --preset <name>]
allowed-tools: Bash(*), Read, Write, Skill
---

The user invoked the style management command with these arguments:

$ARGUMENTS

Resolve the current project from `--project` flag, `GASTORY_PROJECT` env, or `./gastory-output/.current`. If none, tell the user to run `/gastory:project <name>` first.

Then dispatch by interpreting `$ARGUMENTS`:

- Empty or `show` → invoke `gastory:art-concept` skill with `args="show"`
- `setup` → invoke `gastory:art-concept` skill with `args="setup"` (walks user through preset selection or custom description, overwrites existing)
- `clear` → invoke `gastory:art-concept` skill with `args="clear"` (asks for confirmation, then deletes)
- `--preset <name>` → invoke skill with `args="setup preset=<name>"` (skill loads the named preset directly, asks for theme/notes refinement, saves)

Use the Skill tool to invoke `gastory:art-concept`. The skill knows the full setup/show/clear workflow and how to write `gastory-output/<project>/art-concept.json`.

When the skill returns, summarize what happened to the user (saved, cleared, or shown).
