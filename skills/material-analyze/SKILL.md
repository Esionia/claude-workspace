---
name: material-analyze
description: 素材分析+IP大脑工具。对视频或图片进行AI内容分析，提取关键帧并用豆包Vision模型分析内容。还能分析抖音博主主页，提取视频列表和热门内容。当用户想要：分析视频内容、分析图片、分析素材、提取视频帧、用AI理解图片内容、分析抖音博主、学习IP风格、提取网红文案时触发此skill。
compatibility: Python 3.x, requests库, FFmpeg
---

# 素材分析 + IP大脑 Skill

## 功能

这个 skill 提供四大功能：

### 1. 素材分析 (基于豆包Vision API)
- 视频内容分析 - 提取关键帧并分析视频内容
- 图片内容分析 - 用Vision模型分析图片

### 2. IP大脑 (抖音博主分析)
- 从抖音链接分析博主信息
- 获取视频列表和热度数据
- 深度分析Top热门视频内容

### 3. 通用视频解析 (多平台)
- 支持抖音、快手、小红书、B站、微博、TikTok等
- 自动识别平台并解析视频内容
- 提取视频文案/字幕

## 使用方式

### 前置要求

1. 安装 FFmpeg 并添加到系统 PATH
2. 设置 OpenAI API Key

### 安装FFmpeg

```bash
# Windows (使用 Chocolatey)
choco install ffmpeg

# Windows (使用 winget)
winget install FFmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### 设置API Key

方式1: 环境变量
```bash
export OPENAI_API_KEY=your-api-key
```

方式2: 配置文件
```bash
# 复制配置文件
cp config.env.example config.env
# 编辑 config.env 填入你的API Key
```

### 命令行使用

```bash
# 1. 分析视频内容
python material_analyze.py video "视频路径" --fps 0.5

# 2. 分析图片内容
python material_analyze.py image "图片路径"

# 3. IP大脑 - 分析抖音博主
python material_analyze.py ip-brain "抖音链接"

# 4. IP大脑 - 深度分析 (Top 3热门视频)
python material_analyze.py ip-brain "抖音链接" --deep

# 5. 解析任意平台视频 (抖音/快手/小红书/B站/微博等)
python material_analyze.py parse "视频链接"

# 6. 保存结果到文件
python material_analyze.py video "视频路径" -o result.json
```

## 参数说明

### video - 视频分析
| 参数 | 说明 | 示例 |
|------|------|------|
| path | 视频文件路径 | "/path/to/video.mp4" |
| fps | 每秒提取帧数 | 0.5 (每2秒1帧) |
| output | 输出JSON文件 | result.json |

### image - 图片分析
| 参数 | 说明 | 示例 |
|------|------|------|
| path | 图片文件路径 | "/path/to/image.jpg" |
| output | 输出JSON文件 | result.json |

### ip-brain - IP大脑
| 参数 | 说明 | 示例 |
|------|------|------|
| url | 抖音主页链接 | "https://v.douyin.com/xxx" |
| deep | 深度分析 | --deep (分析Top 3) |
| output | 输出JSON文件 | result.json |

### parse - 通用视频解析
| 参数 | 说明 | 示例 |
|------|------|------|
| url | 视频链接 | 抖音/快手/小红书/B站等 |
| output | 输出JSON文件 | result.json |

## 支持的平台

| 平台 | 命令 | 说明 |
|------|------|------|
| 抖音 | ip-brain, parse | 主页分析 + 视频解析 |
| 快手 | parse | 视频解析 |
| 小红书 | parse | 视频解析 |
| B站 | parse | 视频解析 |
| 微博 | parse | 视频解析 |
| TikTok | parse | 视频解析 |
| output | 输出JSON文件 | result.json |

## 工作流程

### 视频分析流程
```
输入视频
    ↓
FFmpeg 提取关键帧 (按FPS)
    ↓
GPT-4V 分析每帧
    ↓
合并描述 → 返回JSON
```

### 图片分析流程
```
输入图片
    ↓
Base64 编码
    ↓
GPT-4V 分析
    ↓
返回JSON描述
```

## 输出格式

```json
{
  "description": "视频/图片的内容描述",
  "frame_count": 10,
  "frames": ["帧1描述", "帧2描述", ...]
}
```

## 配置文件说明

### config.env

使用软件中相同的豆包API配置：

| 变量 | 说明 | 必填 | 示例 |
|------|------|------|------|
| API_KEY | 豆包API Key | 是 | `fbbd25083...` |
| BASE_URL | API端点 | 是 | `https://ark.cn-beijing.volces.com/api/v3` |
| VISION_MODEL | 视觉模型 | 是 | `doubao-seed-1-6-250015` |
| FFMPEG_PATH | FFmpeg路径 | 否 | `C:/ffmpeg/bin/ffmpeg.exe` |

### 获取配置

配置已保存在 `config.env` 中，与软件保持一致。

## 文件结构

```
skills/material-analyze/
├── SKILL.md              # 本文件
├── material_analyze.py   # Python分析脚本
├── config.env.example    # 配置模板
└── evals/
    └── evals.json       # 测试用例
```

## 示例

### 分析视频
```bash
$ python material_analyze.py video tutorial.mp4 --fps 0.5
📹 正在提取视频帧 (FPS=0.5)...
✓ 提取了 15 帧
  分析第 1/15 帧...
  ...
============================================================
分析结果
============================================================

描述: 视频展示了一个办公室场景...

帧数: 15

✓ 结果已保存到: tutorial_analysis.json
```

### 分析图片
```bash
$ python material_analyze.py image photo.jpg
🖼️ 正在分析图片...
============================================================
分析结果
============================================================

描述: 这是一张城市街景照片...
```

## 注意事项

- 视频分析会消耗较多API配额 (每帧一次API调用)
- 建议FPS设置在0.25-1之间，平衡准确度和成本
- 图片支持 JPG、PNG 格式
- 确保FFmpeg已正确安装并可访问
- **使用豆包Vision API**，与软件保持一致
- 如遇网络问题，可能需要配置代理 (设置 `HTTPS_PROXY` 环境变量)
