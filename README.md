# Seokhyun's Claude Code Plugins

A personal collection of Claude Code plugins, packaged as a single marketplace.

## Install

Add the marketplace once, then install any plugin from it:

```
/plugin marketplace add SeokhyunKim/claude-plugins
/plugin install <plugin-name>@seokhyunkim
```

After install, run `/reload-plugins` (or restart Claude Code) to activate.

## Available plugins

### gastory

LLM-driven game asset generation pipeline. Turns text prompts into characters, animations, and sprite sheets:

```
/gastory:project <name>                    # set up a new project
/gastory:concept-art <description>         # generate concept art (auto-applies project style)
/gastory:concept-art --from idle <pose>    # image-to-image for character consistency
/gastory:animate --source <ref> <motion>   # image-to-video
/gastory:extract-frames --action <name> --gif --spritesheet
```

Built on OpenAI `gpt-image-2` / xAI `grok-imagine-image` for stills, fal.ai Seedance 2.0 for video, and ffmpeg + Pillow for local frame processing.

[Full docs →](./gastory/README.md)

## Updates

```
/plugin marketplace update seokhyunkim
/plugin update <plugin-name>@seokhyunkim
```
