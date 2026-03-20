---
name: avatar-vocab-video-generator
description: 单词教学视频 + 数字人 Anna 语音克隆融合技能。保留原有动画内容，声音替换为 Anna 克隆音色，右下角 PIP 显示 Anna 数字人。
---

# Avatar Vocab Video Generator

## 概述

融合 `vocab-teaching-video-generator` 和 `ai-avatar` 的能力：
- LLM 生成教学脚本（不变）
- 图片搜索（不变）
- Remotion 动画视频渲染（不变）
- **语音替换为 Anna 克隆音色**
- **右下角圆形 PIP 显示 Anna 数字人**

## 核心变化

| 对比项 | 原 vocab-teaching | 新 avatar-vocab |
|--------|-----------------|----------------|
| 语音 | edge-tts (微软) | Anna 语音克隆 |
| 视频 | 纯动画 | 动画 + Anna PIP |
| 数字人 | 无 | 右下角圆形小窗 |

## 工作流程

```
1. LLM 生成教学脚本 (vocab-teaching 逻辑)
   ↓
2. 图片搜索 (vocab-teaching 逻辑)
   ↓
3. 克隆语音: 调用 VoiceCloneClient.clone_voice()
   - 合并所有 narration 为一段文本
   - 用 Anna 的参考音频克隆 → 得到一整段音频
   ↓
4. 音频切分: pydub 按 narration 字数比例切分为 per-scene 片段
   - scene_audio = {scene_id: clip_path}
   - 这些片段用于 Remotion 时间轴同步
   ↓
5. Remotion 渲染动画视频
   - per-scene 音频片段传给 Remotion → 动画时间轴与音频同步
   - Remotion 渲染完成后，视频已含 per-scene 音频
   ↓
6. Anna 数字人视频生成
   - 用完整克隆音频 → 数字人 API 生成唇音同步视频
   - 输出含 Anna 画面 + Anna 声音
   ↓
7. FFmpeg 合成:
   - 底层动画视频（丢弃其音频）
   - 右下角圆形 PIP：Anna 数字人视频
   - 音频：使用 Avatar 视频自带音频（Anna 声音 + 唇音）
   ↓
8. 输出最终 MP4
```

**音画同步原理：**
- Remotion 用 per-scene 音频片段驱动动画时间轴（每个 scene 的 duration 由对应音频片段决定）
- FFmpeg 最终输出使用 Avatar 视频音频作为 narration（避免双音频回声）
- Avatar 音频与 per-scene 片段总时长相同（均来自同一克隆音频），理论上完全同步

## 用法

```bash
# 单个单词
python scripts/generate.py --word creativity

# 多个单词
python scripts/generate.py --words "creativity,imagination"

# 自定义输出
python scripts/generate.py --word creativity --output ./videos/

# 使用特定数字人模板
python scripts/generate.py --word creativity --avatar-url <avatar_video_url>
```

## 配置

参考 `ai-avatar/config.env` 中的账号和 Anna 配置：
- `EMAIL` / `PASSWORD` — 数字人 API 登录
- `VOICE_URL` — Anna 的参考音频 URL
- `DIGITAL_HUMAN_URL` — Anna 的数字人视频模板

也可在 `.env` 文件中覆盖：
```
# 克隆音色
VOICE_URL=https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/3044/audio/xxx.wav

# 数字人模板
DIGITAL_HUMAN_URL=https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/3044/video/xxx.mp4

# LLM API (可选，默认使用 MiniMax)
LLM_API_KEY=xxx
LLM_BASE_URL=https://api.minimaxi.com
LLM_MODEL=MiniMax-M2.5
```

## 依赖

- Python: `requests`
- Node.js: Remotion (`@remotion/renderer`)
- FFmpeg: 视频合成
- 数字人 API: `https://dapi.qingyu.club/api`
