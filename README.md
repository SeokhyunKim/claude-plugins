# Seokhyun's Claude Code Plugins

A personal Claude Code marketplace. Each plugin lives in its own repository; this repo holds only the marketplace manifest.

## Install

Add the marketplace once, then install any plugin from it:

```
/plugin marketplace add SeokhyunKim/claude-plugins
/plugin install <plugin-name>@seokhyunkim
```

After install, run `/reload-plugins` (or restart Claude Code) to activate.

## Available plugins

### [gastory](https://github.com/SeokhyunKim/gastory)

Short for **G**ame **A**sset Fac**tory**. LLM-driven game asset generation pipeline that turns text prompts into characters, animations, and sprite sheets. Built on OpenAI `gpt-image-2` / xAI `grok-imagine-image` for stills, fal.ai Seedance 2.0 for video, and ffmpeg + Pillow for local frame processing.

```
/plugin install gastory@seokhyunkim
```

### [code-wiki](https://github.com/SeokhyunKim/code-wiki)

Hierarchical, LLM-maintained wiki for codebases. Mirrors the source tree as markdown, synthesizes bottom-up (leaves → parents), and lazy-generates topic pages for cross-cutting concerns. Following [Karpathy's llm-wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) adapted to source code.

```
/plugin install code-wiki@seokhyunkim
```

## Updates

```
/plugin marketplace update seokhyunkim
/plugin update <plugin-name>@seokhyunkim
```
