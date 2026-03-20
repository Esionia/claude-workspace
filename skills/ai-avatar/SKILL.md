---
name: ai-avatar
description: 语音克隆 + 数字人合成工具。基于超级IP智能体云端API，将文本转换为克隆语音或生成数字人视频。当用户想要：使用语音克隆功能、使用数字人合成功能、从文字生成克隆声音或数字人视频、制作AI主播视频、制作口播视频时触发此skill。
compatibility: Python 3.x, requests库
---

# Voice Clone & Digital Human Skill

## 触发条件

当用户想要：
- 使用语音克隆功能
- 使用数字人合成功能
- 从文字生成克隆声音或数字人视频

## 功能

这个 skill 提供独立的语音克隆和数字人合成功能，基于 `超级IP智能体` 的云端 API。

### 核心功能

1. **用户登录** - 获取 API 访问权限
2. **语音克隆** - 将文本转换为克隆语音（音频文件）
3. **数字人列表** - 查看可用的数字人模板
4. **数字人合成** - 生成数字人视频（需要音频 + 数字人模板）
5. **一键合成** - 自动完成语音克隆 + 数字人视频生成

## 使用方式

### 前置要求

1. 需要有 `超级IP智能体` 账号
2. 参考音频和数字人视频需要先上传到 OSS

### 命令行使用

```bash
# 1. 登录 (首次使用)
python skills/voice-clone/voice_clone.py login your@email.com yourpassword

# 2. 克隆语音（仅音频）
python skills/voice-clone/voice_clone.py clone "要转换的文本" "参考音频OSS_URL" --output audio.wav

# 3. 查看数字人列表
python skills/voice-clone/voice_clone.py list-digital-humans

# 4. 数字人合成（已有音频 URL）
python skills/voice-clone/voice_clone.py digital-human "音频URL" "数字人视频URL" --output video.mp4

# 5. 一键数字人合成（自动语音克隆+视频生成）
python skills/voice-clone/voice_clone.py synthesize "要转换的文本" "参考音频OSS_URL" "数字人视频URL" --output video.mp4
```

### 参数说明

#### clone - 语音克隆
| 参数 | 说明 | 示例 |
|------|------|------|
| text | 要转换的中文文本 | "你好世界" |
| reference_audio | 参考音频的 OSS URL | "https://..." |
| speed | 语速 (0.5-2.0) | 1.0 |
| output | 输出文件路径 | output.wav |

#### list-digital-humans - 数字人列表
无需参数，自动显示可用的默认数字人模板

#### digital-human - 数字人合成
| 参数 | 说明 | 示例 |
|------|------|------|
| audio_url | 驱动音频的 OSS URL | "https://..." |
| avatar_video | 数字人视频模板 OSS URL | "https://..." |
| model | 模型版本 | V2 |
| output | 输出文件路径 | output.mp4 |

#### synthesize - 一键合成
| 参数 | 说明 | 示例 |
|------|------|------|
| text | 要转换的中文文本 | "你好世界" |
| reference_audio | 参考音频的 OSS URL | "https://..." |
| avatar_video | 数字人视频模板 OSS URL | "https://..." |
| speed | 语速 (0.5-2.0) | 1.0 |
| output | 输出文件路径 | output.mp4 |

## 默认数字人模板

软件内置了 6 个默认数字人模板：

| 序号 | 名称 | 视频 URL |
|------|------|----------|
| 1 | 示例1-绿幕 | `https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1764939140639_f6tv14.mp4` |
| 2 | 示例2-夜间 | `https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1764939161086_0bf1jf.mp4` |
| 3 | 示例3-百天 | `https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1764939180646_jzj1nv.mp4` |
| 4 | 示例4-白天 | `https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1764939209916_m5tyk1.mp4` |
| 5 | 中年男士1 | `https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1767510587441_uhewip.mp4` |
| 6 | 青年男1 | `https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1767514386275_4awehx.mp4` |

## 工作流程

### 语音克隆流程
```
用户输入文本
    ↓
调用 voice-clone-v2 API
    ↓
轮询任务状态
    ↓
返回音频 URL / 下载音频文件
```

### 数字人合成流程
```
用户输入文本 + 参考音频 + 数字人模板
    ↓
步骤1: 语音克隆 → 获取音频 URL
    ↓
步骤2: 调用 tasks/task API → 提交合成任务
    ↓
轮询任务状态
    ↓
返回视频 URL / 下载视频文件
```

## 注意事项

- 参考音频和数字人视频需要通过原软件上传到 OSS，获取 URL 后使用
- 云端 API 基于 `https://dapi.qingyu.club/api`
- token 保存在 `~/.aigc_voice_token`
- 语音克隆超时: 300 秒
- 数字人合成超时: 600 秒

## 文件结构

```
skills/voice-clone/
├── SKILL.md              # 本文件 (skill定义)
├── voice_clone.py        # Python 客户端脚本
├── config.env            # 配置文件 (敏感信息)
├── config.env.example    # 配置文件模板
├── evals/
│   └── evals.json       # 测试用例
└── __pycache__/         # Python缓存 (自动生成)
```

## 配置文件说明

### config.env

| 变量 | 说明 | 必填 |
|------|------|------|
| EMAIL | 登录邮箱 | 是 |
| PASSWORD | 登录密码 | 是 |
| VOICE_URL | 参考音频OSS URL | 是 |
| DIGITAL_HUMAN_URL | 数字人视频OSS URL | 是 |

### 获取配置值的方法

1. **EMAIL/PASSWORD**: 超级IP智能体账号
2. **VOICE_URL**: 从软件训练声音后，数据库获取
   - 数据库位置: `%APPDATA%/aigc-human/data/aigc_human.db`
   - 表: `voice_models`
   - 字段: `audio_url`
3. **DIGITAL_HUMAN_URL**: 从软件上传数字人后获取

## 快速开始

```bash
# 登录
python skills/voice-clone/voice_clone.py login 609455967@qq.com "你的密码"

# 克隆语音
python skills/voice-clone/voice_clone.py clone "今天天气真好" "https://你的参考音频.wav" -o result.wav

# 查看数字人列表，获取视频模板 URL
python skills/voice-clone/voice_clone.py list-digital-humans

# 一键合成数字人视频
python skills/voice-clone/voice_clone.py synthesize "今天天气真好" "参考音频URL" "数字人视频URL" -o video.mp4
```

## 示例输出

```
==================================================
开始数字人合成流程
==================================================

[步骤 1/2] 克隆语音...
✓ 语音克隆完成!
  音频 URL: https://static-.../voice_clone/voice_xxx.wav

[步骤 2/2] 生成数字人生成...
✓ 数字人生成完成!
  视频 URL: https://static-.../digital_human/output/task_xxx.mp4

下载视频到 video.mp4...
✓ 下载完成: video.mp4 (3.25 MB)

==================================================
✓ 数字人合成完成!
  视频文件: video.mp4
==================================================
```
