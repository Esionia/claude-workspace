---
name: vocab-teaching-video-generator
description: 英语单词教学视频生成器。调用 LLM 生成完整教学脚本 + 搜索图片 + TTS + Remotion 渲染视频。
---

# Vocab Teaching Video Generator

独立运行的单词教学视频生成工具，无需启动前端项目，直接调用 Python 脚本即可生成完整视频。

## 触发条件

当用户说以下内容时触发：
- "生成单词教学视频"
- "生成 vocabulary 视频"
- "帮我制作单词视频"
- "create vocabulary teaching video"
- "generate word video"

## 文件结构

```
vocab-teaching-video-generator/
├── SKILL.md
├── .gitignore
├── .env                          # API 密钥配置（不提交）
├── evals/evals.json              # 评测用例
└── scripts/
    ├── generate_vocab_video.py   # 主入口脚本（推荐）
    ├── gen_ubiquitous.py        # 简化版脚本
    ├── render-teaching.mjs       # Remotion 渲染脚本
    ├── install.bat               # 依赖安装
    ├── env.example              # 配置示例
    ├── package.json
    ├── components/              # Remotion 场景组件
    │   └── remotion/
    │       ├── TeachingVideo.tsx
    │       ├── shared.ts
    │       └── scenes/
    │           ├── TitleScene.tsx
    │           ├── VocabularyCardScene.tsx
    │           ├── HighlightScene.tsx
    │           ├── ExampleScene.tsx
    │           ├── SummaryScene.tsx
    │           └── ...
    ├── lib/script-types.ts
    └── public/
        ├── audio/bgm/           # 背景音乐
        └── ...
```

## 使用方法

### 1. 配置 .env

```bash
cp scripts/env.example .env
# 编辑 .env，填入 API keys
```

`.env` 内容：
```bash
# LLM API（必须）
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.minimax.chat/v1
LLM_MODEL=MiniMax-M2.5-highspeed

# 图片搜索（可选）
PEXELS_API_KEY=your_pexels_key
```

### 2. 运行脚本

```bash
cd skills/vocab-teaching-video-generator/scripts
python generate_vocab_video.py --word creativity
python generate_vocab_video.py --words creativity,imagination,ephemeral
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|-----|------|------|-------|
| --word | -w | 单个单词 | - |
| --words | -l | 单词列表（逗号分隔） | - |
| --output | -o | 输出目录 | public/videos |
| --chinese-voice | -c | 中文旁白语音 | zh-CN-XiaoxiaoNeural |
| --english-voice | -e | 英文例句语音 | alba |
| --env | | .env 文件路径 | 自动查找 |

## 工作流程

```
1. 读取 .env 配置
2. LLM 生成教学脚本（title → vocabulary-card → highlight → example×2 → summary）
3. 搜索图片（Pexels / Pixabay）
4. 生成 TTS（edge-tts 中文 + pocket-tts 英文）
5. 渲染 MP4（Remotion）
```

## 输出路径

```
public/videos/teaching-{word}-{id}.mp4
```

## 依赖安装

```bash
cd scripts
install.bat
# 或手动: pip install edge-tts requests
```

## 技术栈

| 功能 | 技术 |
|------|------|
| LLM 脚本生成 | MiniMax / OpenAI Compatible API |
| 中文 TTS | edge-tts |
| 英文 TTS | pocket-tts |
| 图片搜索 | Pexels / Pixabay |
| 视频渲染 | Remotion |
