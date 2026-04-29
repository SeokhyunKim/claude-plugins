---
description: Show, set, or clear the current gastory project (analogous to a working directory)
argument-hint: [<name>] | --clear | --list
allowed-tools: Bash(python3 *)
---

The user invoked the project management command with these arguments:

$ARGUMENTS

Run the gastory project script:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/project.py" $ARGUMENTS
```

Behavior:
- No arguments → print the current project (or message if none set)
- `<name>` → set current project (creates `gastory-output/<name>/` if missing)
- `--clear` → unset current project
- `--list` → list known projects (subdirs under `gastory-output/`)

The current project is stored in `./gastory-output/.current` and is used by `/gastory:concept-art`, `/gastory:animate`, and `/gastory:extract-frames` when their `--project` flag is not provided.
