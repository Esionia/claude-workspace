---
name: vocab-teaching-video-generator
description: 单词教学视频生成器。调用 LLM 生成完整教学脚本 + 搜索图片 + TTS + 渲染视频，无需启动项目。
---

# Vocab Teaching Video Generator

直接生成单词教学视频的独立工具，完整复现 remotion-tts-web 项目的词汇视频生成流程。

## 触发条件

当用户说以下内容时触发：
- "生成单词教学视频"
- "生成 vocabulary 视频"
- "帮我制作单词视频"
- "create vocabulary teaching video"
- "generate word video"

## 使用方法

### 1. 准备工作

项目需要以下文件：
- `.env` - 包含 LLM API 和图片搜索 API 配置
- `scripts/render-teaching.mjs` - Remotion 渲染脚本
- `public/audio/tts/` - TTS 音频目录

### 2. 运行脚本

```bash
# 在项目目录下运行
python scripts/generate_vocab_video.py --word creativity
python scripts/generate_vocab_video.py --words creativity,imagination
```

### 3. 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|-------|
| --word | -w | 单个单词 | - |
| --words | -l | 单词列表（逗号分隔） | - |
| --output | -o | 输出目录 | public/videos |
| --voice | -v | 英语发音人 | en-US-JennyNeural |
| --env | -e | .env 文件路径 | 自动查找 |

## 工作流程

1. **读取配置** - 从项目 `.env` 加载 API keys
2. **LLM 生成脚本** - 调用本地 LLM API 生成完整教学脚本
   - title - 介绍单词
   - vocabulary-card - 单词卡片（词性、释义）
   - highlight - 词根词缀讲解
   - example - 例句演示
   - summary - 要点总结
3. **搜索图片** - 为 highlight 和 example 场景搜索图片（Pexels/Pixabay）
4. **生成 TTS** - 为每个场景的 narration 生成语音
5. **渲染视频** - 调用 Remotion 渲染 MP4

## 输出路径

```
public/videos/teaching-{word}-{id}.mp4
```

例如：`public/videos/teaching-creativity-b2bcf160.mp4`

## 示例

```
用户: 帮我生成 creativity 的教学视频

Skill:
============================================================
🎬 单词教学视频生成器（完整版）
============================================================
📚 单词: creativity
📁 输出: public/videos
🔊 发音: en-US-JennyNeural
   加载配置: E:\remotion-projects\remotion-tts-web\.env

📹 生成视频: creativity
==================================================

🎯 调用 AI 生成教学脚本...
   调用 LLM API: http://127.0.0.1:15721/v1/chat/completions
   模型: claude-sonnet-4-5-20250929
   LLM 生成脚本成功，场景数: 8

🖼️ 搜索图片...
   图片来源: Pexels
   ...

🔊 生成场景旁白 TTS...
   生成 TTS: 欢迎来到今天的英语学习课程...
   ...

📝 生成视频配置...
   配置已保存: tmp\config-creativity-b2bcf160.json
   预计时长: 180 秒

🎬 渲染视频...
   使用脚本: scripts/render-teaching.mjs
✅ 视频生成成功!
   路径: public\videos\teaching-creativity-b2bcf160.mp4
   大小: 11.1 MB

============================================================
📊 生成结果
============================================================
✅ creativity: public\videos\teaching-creativity-b2bcf160.mp4
============================================================
```

## 依赖安装

### 方式一：一键安装（推荐）

```bash
cd scripts
install.bat
```

### 方式二：手动安装

```bash
# 1. 安装 Python 依赖
pip install edge-tts requests

# 2. 确保有 Node.js 环境（用于视频渲染）

# 3. 配置 .env 文件
# 复制示例配置并填入你的 API keys
```

## 依赖

- **Python**: edge-tts, requests
- **Node.js**: 用于运行 Remotion 渲染脚本
- **LLM API**: OPENAI_API_KEY / LLM_API_KEY
- **图片 API**: PEXELS_API_KEY / PIXABAY_API_KEY
