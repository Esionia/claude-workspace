---
name: image-gen
description: AI image generation with Volcengine and Cloudflare APIs. Supports text-to-image, aspect ratios. Sequential by default. Auto-selects Cloudflare first, then Volcengine. Use when user asks to generate, create, or draw images.
---

# Image Generation (AI SDK)

Official API-based image generation. Supports **Cloudflare (Flux Schnell)** and **Volcengine (火山引擎 / Doubao Seedream)** providers.

## Script Directory

**Agent Execution**:
1. `SKILL_DIR` = this SKILL.md file's directory
2. Script path = `${SKILL_DIR}/scripts/main.ts`

## Step 0: Load Preferences ⛔ BLOCKING

**CRITICAL**: This step MUST complete BEFORE any image generation. Do NOT skip or defer.

Check EXTEND.md existence (priority: project → user):

```bash
test -f .baoyu-skills/image-gen/EXTEND.md && echo "project"
test -f "$HOME/.baoyu-skills/image-gen/EXTEND.md" && echo "user"
```

| Result | Action |
|--------|--------|
| Found | Load, parse, apply settings. If `default_model.[provider]` is null → ask model only (Flow 2) |
| Not found | ⛔ Run first-time setup ([references/config/first-time-setup.md](references/config/first-time-setup.md)) → Save EXTEND.md → Then continue |

**CRITICAL**: If not found, complete the full setup (provider + model + quality + save location) using AskUserQuestion BEFORE generating any images. Generation is BLOCKED until EXTEND.md is created.

| Path | Location |
|------|----------|
| `.baoyu-skills/image-gen/EXTEND.md` | Project directory |
| `$HOME/.baoyu-skills/image-gen/EXTEND.md` | User home |

Schema: `references/config/preferences-schema.md`

## Usage

```bash
# Auto-detect (Cloudflare → Volcengine)
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A cat" --image cat.png

# With aspect ratio
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A landscape" --image out.png --ar 16:9

# High quality
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A cat" --image out.png --quality 2k

# From prompt files
npx -y bun ${SKILL_DIR}/scripts/main.ts --promptfiles system.md content.md --image out.png

# Explicit provider
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A cat" --image out.png --provider cloudflare
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "一只可爱的猫" --image out.png --provider volcengine

# Custom model
npx -y bun ${SKILL_DIR}/scripts/main.ts --prompt "A cat" --image out.png --provider cloudflare --model @cf/black-forest-labs/flux-1-dev
```

## Options

| Option | Description |
|--------|-------------|
| `--prompt <text>`, `-p` | Prompt text |
| `--promptfiles <files...>` | Read prompt from files (concatenated) |
| `--image <path>` | Output image path (required) |
| `--provider volcengine\|cloudflare` | Force provider (auto-detect by default) |
| `--model <id>`, `-m` | Model ID |
| `--ar <ratio>` | Aspect ratio (e.g., `16:9`, `1:1`, `4:3`) |
| `--size <WxH>` | Size (e.g., `1024x1024`) |
| `--quality normal\|2k` | Quality preset (default: 2k) |
| `--n <count>` | Number of images |
| `--json` | JSON output |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `VOLCENGINE_API_KEY` | Volcengine API key (火山引擎) |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Account ID |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Token |
| `VOLCENGINE_IMAGE_MODEL` | Volcengine model override (default: doubao-seedream-5-0-260128) |
| `CLOUDFLARE_IMAGE_MODEL` | Cloudflare model override (default: @cf/black-forest-labs/flux-1-schnell) |
| `VOLCENGINE_BASE_URL` | Custom Volcengine endpoint |

**Load Priority**: CLI args > EXTEND.md > env vars > `<cwd>/.baoyu-skills/.env` > `~/.baoyu-skills/.env`

## Provider Selection

1. `--provider` specified → use it
2. Only one API key available → use that provider
3. Multiple available → **Cloudflare → Volcengine**

## Provider Details

### Cloudflare (Recommended)

- Default model: `@cf/black-forest-labs/flux-1-schnell` (fast, free tier available)
- Other models: `@cf/black-forest-labs/flux-1-dev`, `@cf/lykon/dreamshaper-8`
- Aspect ratio: Not supported (uses model default)
- Reference images: Not supported

### Volcengine (火山引擎)

- Default model: `doubao-seedream-5-0-260128` (good for Chinese content)
- Other models: `doubao-seedream-3-0`
- Aspect ratio: Supported via size mapping
- Reference images: Not supported

## Quality Presets

| Preset | Volcengine Size | Use Case |
|--------|-----------------|----------|
| `normal` | 1024×1024 | Quick previews |
| `2k` (default) | 2048×2048 | Covers, illustrations, infographics |

**Cloudflare**: Uses fixed model defaults; quality preset has no effect.

## Aspect Ratio

Supported ratios: `1:1`, `16:9`, `9:16`, `4:3`, `3:4`

- **Volcengine**: Converts to W×H based on ratio
- **Cloudflare**: Not supported

## Error Handling

- Missing API key → error with setup instructions
- Generation failure → auto-retry once
- Invalid aspect ratio → warning, proceed with default

## Extension Support

Custom configurations via EXTEND.md. See **Preferences** section for paths and supported options.
