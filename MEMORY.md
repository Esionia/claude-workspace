# MEMORY.md - Learning Notes

## 2026-03-17

### Vocab Video Generator Learning

**问题:** vocab-teaching-video-generator 之前多次失败

**原因分析:**
1. 音频文件名不匹配 - config 期望的名称与实际生成的不同
2. 音频文件大小为 0 - edge-tts 生成失败但脚本没检测到
3. Remotion 渲染时找不到音频文件 (404 错误)

**最终成功的关键:**
- 等待脚本完整运行完成（包括 Remotion 渲染）
- 脚本内部有 "已同步 tts 目录到 scripts/public" 的步骤
- 最终成功生成了 6.6MB 的视频

### Chinese TTS Learning

**正确用法:**
1. 使用 edge-tts 生成 MP3
2. 用 ffmpeg 转换为 Opus 格式
3. 通过 message 工具发送，asVoice=true
4. 文件必须保存在 workspace 目录，不能用 /tmp

### OpenMAIC Skill

- 已安装到 workspace-english/skills/openmaic
- 用户选择了 "local" 模式安装

---

## 历史记录

- 2026-03-16: 首次对话，创建了 English learning assistant (小英)
- 2026-03-16: 安装了 clawhub, openmaic 技能
- 2026-03-16: 移动 openmaic 到 workspace-english/skills/
