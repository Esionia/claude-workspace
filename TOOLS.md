# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS (飞书中文语音)

- Preferred voice: "晓伊" (zh-CN-XiaoxiaoNeural, 微软 Edge TTS)
- Provider: chinese-tts (飞书内置)
- 使用场景: 故事朗读、电影简介、"故事时间"环节

### 在 OpenClaw 中使用 TTS (正确方法)

**方法1: 使用 feishu_tts 工具 (如果有)**

**方法2: 手动生成 + message 发送**
```bash
# 1. 生成 MP3
edge-tts --voice zh-CN-YunxiNeural --text "你的文本" --write-media voice.mp3

# 2. 转换为 Opus 格式 (飞书语音需要 Opus)
ffmpeg -i voice.mp3 -c:a libopus -b:a 64k -ar 48000 voice.opus -y

# 3. 通过 message 工具发送 asVoice=true
```

**关键点:**
- 必须转换为 Opus 格式，MP3 会变成文件附件而不是语音
- 保存到 workspace 目录，不要用 /tmp

## Vocab Video Generator (单词教学视频)

- 技能位置: `workspace-english/skills/vocab-teaching-video-generator`
- 运行命令: `python scripts/generate_vocab_video.py --word {单词}`
- 输出目录: `public/videos/`
- 成功关键: 需要等脚本完整运行完成，包括 Remotion 渲染

### 常见问题
- 首次运行可能需要下载 Chrome Headless Shell
- 渲染时间约 1-2 分钟
- 视频生成成功后会返回 .mp4 文件


```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
