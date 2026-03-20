---
name: preferences-schema
description: EXTEND.md YAML schema for image-gen user preferences
---

# Preferences Schema

## Full Schema

```yaml
---
version: 1

default_provider: null      # volcengine|cloudflare|null (null = auto-detect)

default_quality: null       # normal|2k|null (null = use default: 2k)

default_aspect_ratio: null  # "16:9"|"1:1"|"4:3"|"3:4"|null

default_model:
  volcengine: null         # e.g., "doubao-seedream-5-0-260128"
  cloudflare: null         # e.g., "@cf/black-forest-labs/flux-1-schnell"
---
```

## Field Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | int | 1 | Schema version |
| `default_provider` | string\|null | null | Default provider (null = auto-detect) |
| `default_quality` | string\|null | null | Default quality (null = 2k) |
| `default_aspect_ratio` | string\|null | null | Default aspect ratio |
| `default_model.volcengine` | string\|null | null | Volcengine default model |
| `default_model.cloudflare` | string\|null | null | Cloudflare default model |

## Examples

**Minimal**:
```yaml
---
version: 1
default_provider: cloudflare
default_quality: 2k
---
```

**Full**:
```yaml
---
version: 1
default_provider: cloudflare
default_quality: 2k
default_aspect_ratio: "16:9"
default_model:
  volcengine: "doubao-seedream-5-0-260128"
  cloudflare: "@cf/black-forest-labs/flux-1-schnell"
---
```
