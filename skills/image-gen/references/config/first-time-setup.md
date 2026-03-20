---
name: first-time-setup
description: First-time setup and default model selection flow for image-gen
---

# First-Time Setup

## Overview

Triggered when:
1. No EXTEND.md found → full setup (provider + model + preferences)
2. EXTEND.md found but `default_model.[provider]` is null → model selection only

## Setup Flow

```
No EXTEND.md found          EXTEND.md found, model null
        │                            │
        ▼                            ▼
┌─────────────────────┐    ┌──────────────────────┐
│ AskUserQuestion     │    │ AskUserQuestion      │
│ (full setup)        │    │ (model only)         │
└─────────────────────┘    └──────────────────────┘
        │                            │
        ▼                            ▼
┌─────────────────────┐    ┌──────────────────────┐
│ Create EXTEND.md    │    │ Update EXTEND.md     │
└─────────────────────┘    └──────────────────────┘
        │                            │
        ▼                            ▼
    Continue                     Continue
```

## Flow 1: No EXTEND.md (Full Setup)

**Language**: Use user's input language or saved language preference.

Use AskUserQuestion with ALL questions in ONE call:

### Question 1: Default Provider

```yaml
header: "Provider"
question: "Default image generation provider?"
options:
  - label: "Cloudflare (Recommended)"
    description: "Flux Schnell - free tier available, fast generation, no API key needed for basic use"
  - label: "Volcengine"
    description: "火山引擎 - doubao-seedream, good for Chinese content"
```

### Question 2: Default Quality

```yaml
header: "Quality"
question: "Default image quality?"
options:
  - label: "2k (Recommended)"
    description: "2048px - covers, illustrations, infographics"
  - label: "normal"
    description: "1024px - quick previews, drafts"
```

### Question 3: Save Location

```yaml
header: "Save"
question: "Where to save preferences?"
options:
  - label: "Project (Recommended)"
    description: ".baoyu-skills/ (this project only)"
  - label: "User"
    description: "~/.baoyu-skills/ (all projects)"
```

### Save Locations

| Choice | Path | Scope |
|--------|------|-------|
| Project | `.baoyu-skills/image-gen/EXTEND.md` | Current project |
| User | `$HOME/.baoyu-skills/image-gen/EXTEND.md` | All projects |

### EXTEND.md Template

```yaml
---
version: 1
default_provider: [selected provider or null]
default_quality: [selected quality]
default_aspect_ratio: null
default_image_size: null
default_model:
  volcengine: null
  cloudflare: [selected cloudflare model or null]
---
```

## Flow 2: EXTEND.md Exists, Model Null

When EXTEND.md exists but `default_model.[current_provider]` is null, ask ONLY the model question for the current provider.

### Volcengine Model Selection

```yaml
header: "Volcengine Model"
question: "Choose a default Volcengine image generation model?"
options:
  - label: "doubao-seedream-5-0-260128 (Recommended)"
    description: "Doubao Seedream - good for Chinese content, high quality"
  - label: "doubao-seedream-3-0"
    description: "Doubao Seedream 3.0 - latest generation"
```

### Cloudflare Model Selection

```yaml
header: "Cloudflare Model"
question: "Choose a default Cloudflare image generation model?"
options:
  - label: "@cf/black-forest-labs/flux-1-schnell (Recommended)"
    description: "Fast generation, free tier available"
  - label: "@cf/black-forest-labs/flux-1-dev"
    description: "Higher quality, slower generation"
  - label: "@cf/lykon/dreamshaper-8"
    description: "Artistic style, good for illustrations"
```

### Update EXTEND.md

After user selects a model:

1. Read existing EXTEND.md
2. Update the provider-specific model key

Only set the selected provider's model; leave others as their current value or null.

## After Setup

1. Create directory if needed
2. Write/update EXTEND.md with frontmatter
3. Confirm: "Preferences saved to [path]"
4. Continue with image generation
