#!/usr/bin/env python3
"""
单词教学视频生成器（完整版）
调用 LLM 生成完整教学脚本 + 搜索图片 + TTS + 渲染视频

用法:
    python generate_vocab_video.py --word creativity
    python generate_vocab_video.py --word creativity --env ./remotion-tts-web/.env
"""
import sys
import subprocess
import importlib

# 检查并安装依赖
def check_dependencies():
    """检查并安装必要的依赖"""
    required_packages = ['edge_tts', 'requests']
    missing = []

    for pkg in required_packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg.replace('_', '-'))

    if missing:
        print(f"[INFO] 正在自动安装缺失的依赖: {', '.join(missing)}")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing,
                         check=True, capture_output=True)
            print(f"[✓] 依赖安装成功")
        except Exception as e:
            print(f"[错误] 自动安装依赖失败: {e}")
            print(f"       请手动运行: pip install {' '.join(missing)}")
            return False
    return True

# 启动时检查依赖
if not check_dependencies():
    sys.exit(1)

# Windows 下解决中文输出编码问题
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import asyncio
import json
import ast
import os
import uuid
from pathlib import Path
from typing import Optional

# 配置 - 与项目保持一致
DEFAULT_CHINESE_VOICE = "zh-CN-XiaoxiaoNeural"  # 中文旁白用
DEFAULT_ENGLISH_VOICE = "alba"  # 英文例句用 pocket-tts
DEFAULT_OUTPUT = "public/videos"

# VOCABULARY_SYSTEM_PROMPT - 直接复制自 remotion-tts-web 项目
VOCABULARY_SYSTEM_PROMPT = """你是一个专业的英语教学视频脚本生成助手。

**【必须严格遵守】词汇教学场景顺序：**
1. **cover** - 视频封面，展示单词和中文翻译
2. **title** - 介绍要学习的单词
3. **vocabulary-card** - 展示单词卡片（词性、释义）
4. **highlight** - 词根词缀讲解
5. **example** - 例句演示（需要2个例句）
6. **summary** - 要点总结

⚠️ 场景必须按照上述 1→2→3→4→5→6 的顺序生成，不得调换顺序！

重要要求：
1. vocabulary-card场景（推荐使用定义模式）：
   - **定义模式**（推荐）：展示单词、词性、多个释义，不包含例句
   - 不要生成 phraseAudioUrl、exampleAudioUrl、phraseAudioDuration 等音频字段
2. highlight场景：必须讲解词根词缀、构词法或记忆方法
3. example场景（必须2个）：
   - narration格式："[英文句子]. 意思是：[中文翻译]"
   - 必须在highlights数组中标注目标词汇
4. summary的points必须是字符串数组，包含3-4个要点
5. 每个场景的narration要详细，不要过于简短
6. ⚠️ 所有 narration 必须使用中文！

【词根词缀拆解的严格规则】

⚠️ **违反以下规则将导致拆解错误，必须严格遵守：**

1. **词根/词缀必须是真实的标准词素**：
   - 必须是拉丁/希腊语系中真实存在的词根、前缀、后缀
   - ❌ 错误：`crea`（不是标准词根）、`tivity`（不是标准后缀）、`cour`（不是词根）
   - ✅ 正确：`cre-`（拉丁 creare=创造）、`-ative`（形容词后缀）、`-ity`（名词后缀）

2. **词素必须是单词中最小的有意义单元**：
   - 不要合并多个词素，如不要把 `-ative + -ity` 合并成 `tivity`
   - 不要截取不完整的词根，如不要把 `cre-` 写成 `crea`
   - 每个词素在相关单词中必须能独立识别

3. **拆解必须完整且逻辑自洽**：
   - 所有词素组合起来必须能解释单词的整体含义
   - 词素数量一般为 2-4 个，过于零散反而难记

4. **相关单词必须包含相同的词素**：
   - 如果词根是 `cre-`，相关词必须包含 `cre-`
   - 如果后缀是 `-ive`，相关词必须包含 `-ive`

**正确拆解示例：**
- creativity = cre-（创造）+ -ative（具有...性质的）+ -ity（性质/状态）→ 创造的性质 → 创造力
- emergency = emerg-（emergere=出现）+ -ency（名词后缀）→ 出现的状态 → 紧急情况
- transport = trans-（跨越）+ port-（携带）→ 携带跨越 → 运输

**错误拆解示例（必须避免）：**
- ❌ creativity = crea + tivity（crea不是词根，tivity不是标准后缀）
- ❌ encourage = en + cour + age（cour不是词根，courage才是整体词根）
- ❌ unhappy = un + hap + py（hap不是标准词根，happy是整体）

5. **highlight场景的content结构：**
{
  "type": "highlight",
  "sentence": "目标单词及其解释",
  "highlights": [{"text": "词根或词缀", "color": "#FFD93D", "label": "词根/前缀/后缀"}],
  "images": [{"url": "图片URL或描述", "alt": "图片说明", "position": "right", "size": "medium"}],
  "rootAffix": [
    {
      "root": "词根/词缀文本",
      "meaning": "含义",
      "label": "词根/前缀/后缀",
      "narration": "该词根的讲解旁白（单独一句话）",
      "relatedWords": [
        {"word": "相关单词1", "meaning": "含义", "highlight": "词根部分", "narration": "单词，含义"},
        {"word": "相关单词2", "meaning": "含义", "highlight": "词根部分", "narration": "单词，含义"},
        {"word": "相关单词3", "meaning": "含义", "highlight": "词根部分", "narration": "单词，含义"}
      ]
    }
  ]
}

重要：narration 字段必须按照 rootAffix 数组顺序生成
- 每个 rootAffix 元素必须包含 narration 字段
- ⚠️ **场景的 narration 字段必须是简短的引导语，不超过10个字**
- ⚠️ **场景的 narration 不能包含词根的具体含义！**
- 每个词根的详细讲解放在对应的 rootAffix[i].narration 中

相关单词的 narration 格式："单词，含义"（例如："transfer，转移"）

## 输出 JSON 结构
{
  "id": "video_script_单词_001",
  "topic": "英语词汇教学：单词",
  "description": "通过词根词缀法讲解...",
  "targetAudience": "英语学习者",
  "totalDuration": 180,
  "scenes": [
    {"id": "scene_001", "type": "cover", "content": {"type":"cover","word":"单词","translation":"中文释义"}, "narration": "简短的开场白", "narrationLang": "zh", "durationSeconds": 5},
    {"id": "scene_002", "type": "title", "content": {"type":"title","mainTitle":"单词","subtitle":"中文"}, "narration": "中文旁白", "narrationLang": "zh", "durationSeconds": 10},
    {"id": "scene_003", "type": "vocabulary-card", "content": {"type":"vocabulary-card","phrase":"单词","meaning":"中文","partOfSpeech":"adj.","definitions":["释义1","释义2"]}, "narration": "中文旁白", "narrationLang": "zh", "durationSeconds": 15},
    {"id": "scene_004", "type": "highlight", "content": {"type":"highlight","sentence":"单词","highlights":[{"text":"词根","color":"#FFD93D","label":"词根"}],"rootAffix":[{"root":"词根","meaning":"含义","label":"词根/后缀","narration":"该词根的详细讲解","relatedWords":[{"word":"相关词","meaning":"含义","highlight":"词根","narration":"词，含义"}]}]}, "narration": "简短的引导语", "narrationLang": "zh", "durationSeconds": 30},
    {"id": "scene_005", "type": "example", "content": {"type":"example","english":"英文例句1","chinese":"中文翻译1","highlights":[{"text":"单词","color":"#FFD93D"}]}, "narration": "英文例句1. 意思是：中文解释", "narrationLang": "zh", "durationSeconds": 8},
    {"id": "scene_006", "type": "example", "content": {"type":"example","english":"英文例句2","chinese":"中文翻译2","highlights":[{"text":"单词","color":"#FFD93D"}]}, "narration": "英文例句2. 意思是：中文解释", "narrationLang": "zh", "durationSeconds": 8},
    {"id": "scene_007", "type": "summary", "content": {"type":"summary","points":["要点1","要点2","要点3"]}, "narration": "总结旁白", "narrationLang": "zh", "durationSeconds": 20}
  ],
  "createdAt": "2024-01-01"
}
"""


class VocabVideoGenerator:
    """单词教学视频生成器"""

    def __init__(self, output_dir: str = DEFAULT_OUTPUT, chinese_voice: str = DEFAULT_CHINESE_VOICE,
                 english_voice: str = DEFAULT_ENGLISH_VOICE, env_path: str = None):
        # 动态查找 remotion-tts-web 项目目录
        script_dir = Path(__file__).parent.parent
        possible_project_dirs = [
            script_dir,  # 使用 skill 目录本身
            script_dir / "../../remotion-projects/remotion-tts-web",
            script_dir / "../remotion-tts-web",
            Path("e:/remotion-projects/remotion-tts-web"),
            Path("."),
        ]

        self.project_dir = None
        for p in possible_project_dirs:
            if p.exists() and (p / "package.json").exists():
                self.project_dir = p
                break

        if not self.project_dir:
            # 如果找不到 remotion-tts-web 项目，使用 skill 目录本身
            self.project_dir = script_dir

        # 输出到项目目录
        self.output_dir = self.project_dir / "public/videos"
        self.audio_dir = self.project_dir / "public/audio/tts"
        self.tmp_dir = self.project_dir / "tmp"
        self.chinese_voice = chinese_voice
        self.english_voice = english_voice
        self.env_path = env_path

        # 使用固定 ID 而非随机 UUID，确保文件名可预测
        # video_id 在 generate_single 中生成
        self.video_id = None

        # 创建目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        # 加载环境变量
        self._load_env()

    def _load_env(self):
        """从 .env 文件加载配置"""
        if self.env_path:
            env_file = Path(self.env_path)
        else:
            # 优先查找 skill 目录的 .env
            skill_dir = Path(__file__).parent.parent
            possible_paths = [
                skill_dir / ".env",  # 优先：skill 目录
                Path.cwd() / ".env",
                Path.cwd() / "remotion-tts-web" / ".env",
                Path(__file__).parent.parent.parent / "remotion-tts-web" / ".env",
            ]
            env_file = None
            for p in possible_paths:
                if p.exists():
                    env_file = p
                    break

        self.llm_api_key = None
        self.llm_base_url = None
        self.llm_model = None
        self.pexels_api_key = None
        self.pixabay_api_key = None

        # 优先读取 LLM_* 配置（兼容各种 API）
        if env_file and env_file.exists():
            print(f"   加载配置: {env_file}")
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            value = value.strip().strip('"').strip("'")
                            # 优先 LLM_* 配置
                            if key == "LLM_API_KEY":
                                self.llm_api_key = value
                            elif key == "LLM_BASE_URL":
                                self.llm_base_url = value
                            elif key == "LLM_MODEL":
                                self.llm_model = value
                            # 其次兼容 OPENAI_* 配置
                            elif key == "OPENAI_API_KEY" and not self.llm_api_key:
                                self.llm_api_key = value
                            elif key == "OPENAI_BASE_URL" and not self.llm_base_url:
                                self.llm_base_url = value
                            elif key == "OPENAI_MODEL" and not self.llm_model:
                                self.llm_model = value
                            elif key == "PEXELS_API_KEY":
                                self.pexels_api_key = value
                            elif key == "PIXABAY_API_KEY":
                                self.pixabay_api_key = value
        else:
            print(f"   警告: 未找到 .env 文件，使用默认配置")

    async def call_llm(self, word: str, custom_content: dict = None) -> dict:
        """调用 LLM API 生成教学脚本"""
        import requests

        if not self.llm_api_key or not self.llm_base_url:
            raise Exception("LLM API 未配置，请检查 .env 文件")

        prompt = f"""请为以下英语词汇生成教学视频脚本：

词汇：{word}

"""

        if custom_content:
            if custom_content.get("definition"):
                prompt += f"释义：{custom_content['definition']}\n"
            if custom_content.get("examples"):
                prompt += f"例句：{'\\n'.join(custom_content['examples'])}\n"
            if custom_content.get("notes"):
                prompt += f"备注：{custom_content['notes']}\n"

        prompt += "\n请基于以上信息生成完整的教学脚本 JSON。"

        print(f"   调用 LLM API: {self.llm_base_url}")
        print(f"   模型: {self.llm_model}")

        # MiniMax API 格式不同于 OpenAI
        is_minimax = "minimax" in self.llm_base_url.lower()
        if is_minimax:
            # MiniMax 专用端点
            api_url = f"{self.llm_base_url}/text/chatcompletion_v2"
        else:
            api_url = f"{self.llm_base_url}/chat/completions"

        # 构建请求参数
        request_json = {
            "model": self.llm_model,
            "messages": [
                {"role": "system", "content": VOCABULARY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 8000,
        }
        # 只有非 MiniMax 才添加 response_format
        if not is_minimax:
            request_json["response_format"] = {"type": "json_object"}

        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {self.llm_api_key}",
                "Content-Type": "application/json",
            },
            json=request_json,
            timeout=120,
        )

        if not response.ok:
            raise Exception(f"LLM API 错误: {response.status_code} - {response.text}")

        data = response.json()
        print(f"   API 响应: {str(data)[:200]}...")

        # 处理不同 API 的响应格式
        if is_minimax:
            # MiniMax 格式
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            # OpenAI 格式
            content = data["choices"][0]["message"]["content"]

        if not content:
            raise Exception(f"API 返回内容为空: {data}")

        # 移除 markdown 代码块
        content = content.replace("```json", "").replace("```", "").replace("```python", "").replace("```", "").strip()

        # 打印原始内容用于调试
        print(f"   📄 LLM 原始返回长度: {len(content)} 字符")
        print(f"   📄 LLM 原始返回前 500 字符:\n{content[:500]}")

        # 清理控制字符
        import re
        content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', content)

        # 预先修复中文标点符号问题（在解析之前）
        # 中文冒号 → 英文冒号
        content = content.replace('：', ':')
        # 中文逗号 → 英文逗号
        content = content.replace('，', ',')
        # 中文句号 → 英文句号
        content = content.replace('。', '.')
        # 中文引号 → 英文引号
        content = content.replace('\u201c', '"').replace('\u201d', '"')
        content = content.replace('\u2018', "'").replace('\u2019', "'")
        content = content.replace('"', '"').replace('"', '"')
        content = content.replace(''', "'").replace(''', "'")
        # 中文方括号 → 英文方括号
        content = content.replace('【', '[').replace('】', ']')
        content = content.replace('〔', '[').replace('〕', ']')
        # 中文括号 → 英文括号
        content = content.replace('（', '(').replace('）', ')')
        # 中文破折号 → 英文短横线
        content = content.replace('—', '-').replace('–', '-')
        # 中文省略号 → 英文三个点
        content = content.replace('…', '...')
        # 处理嵌套引号问题
        content = re.sub(r'""([^"]+)""', r'"\1"', content)
        # 移除可能的尾部逗号
        content = re.sub(r',(\s*[}\]])', r'\1', content)

        script = None  # 预先定义变量
        try:
            script = json.loads(content)
        except json.JSONDecodeError as e:
            # 如果 JSON 解析失败，尝试修复常见问题后重试
            print(f"   ⚠️ JSON 解析失败，尝试修复: {e}")
            # 先尝试 ast.literal_eval 解析 Python dict 格式（单引号）
            try:
                script = ast.literal_eval(content)
                print(f"   ✅ 用 ast.literal_eval 成功解析 Python dict 格式")
                return script
            except Exception as le:
                print(f"   ⚠️ ast.literal_eval 失败: {le}")
                # 尝试提取后再用 ast
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    extracted = content[start_idx:end_idx+1]
                    try:
                        script = ast.literal_eval(extracted)
                        print(f"   ✅ 用 ast.literal_eval 从提取内容成功解析")
                        return script
                    except Exception as le2:
                        print(f"   ⚠️ 提取后再 ast 也失败: {le2}")
            # 移除可能的尾部逗号
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            # 修复中文冒号等常见问题
            content = content.replace('：', ':')
            # 修复中文引号 - 最简单的方法：把中文引号直接替换为单引号
            content = content.replace('\u201c', "'").replace('\u201d', "'")
            content = content.replace('\u2018', "'").replace('\u2019', "'")
            # 处理嵌套引号问题：将连续的中文引号 ""xxx"" 替换为单引号 'xxx'
            content = re.sub(r'""([^"]+)""', r"'\1'", content)
            # 修复单引号问题：把 'xxx' 替换为 "xxx"（只在JSON字符串内部）
            content = re.sub(r"'([^']*)'", r'"\1"', content)
            # 修复英文双引号嵌套: 在字符串中的 "xxx" 改为 'xxx'
            # 查找 "xxx"yyy" 模式，替换为 "xxx'yyy"
            content = re.sub(r'"([^"]+)"([^"]+)"', r"'\1'\2'", content)
            # 移除多余的控制字符
            content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', content)

            # 打印错误位置附近的字符，帮助调试
            if e.pos is not None:
                start = max(0, e.pos - 30)
                end = min(len(content), e.pos + 30)
                print(f"   📄 错误位置 (pos={e.pos}) 附近: {content[start:end]}")

            # 尝试再次解析
            try:
                script = json.loads(content)
            except json.JSONDecodeError as e2:
                # 如果还是失败，尝试更激进的修复
                import re
                print(f"   ⚠️ 再次解析失败: {e2}")

                # 尝试提取 JSON 部分
                import re
                # 查找第一个 { 和最后一个 }
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    extracted = content[start_idx:end_idx+1]
                    print(f"   📄 尝试提取 JSON: {extracted[:200]}...")
                    try:
                        script = json.loads(extracted)
                        print(f"   ✅ 成功从提取内容解析 JSON")
                    except:
                        pass

                if script is None:
                    # 如果所有修复都失败，抛出异常
                    raise Exception(f"JSON 解析失败，无法修复: {content[:500]}")

        # 验证 script 变量已正确赋值
        if not script:
            raise Exception(f"JSON 解析失败，script 变量未正确赋值")

        print(f"   LLM 生成脚本成功，场景数: {len(script.get('scenes', []))}")
        return script

    async def search_image(self, query: str) -> Optional[dict]:
        """搜索图片"""
        import requests

        # 尝试 Pexels
        if self.pexels_api_key:
            try:
                response = requests.get(
                    "https://api.pexels.com/v1/search",
                    headers={"Authorization": self.pexels_api_key},
                    params={"query": query, "per_page": 1},
                    timeout=10,
                )
                if response.ok:
                    data = response.json()
                    if data.get("photos") and len(data["photos"]) > 0:
                        photo = data["photos"][0]
                        print(f"   图片来源: Pexels")
                        return {
                            "url": photo["src"]["large"],
                            "alt": photo.get("alt", query),
                        }
            except Exception as e:
                print(f"   Pexels 搜索失败: {e}")

        # 尝试 Pixabay
        if self.pixabay_api_key:
            try:
                response = requests.get(
                    "https://pixabay.com/api/",
                    params={
                        "key": self.pixabay_api_key,
                        "q": query,
                        "per_page": 1,
                    },
                    timeout=10,
                )
                if response.ok:
                    data = response.json()
                    if data.get("hits") and len(data["hits"]) > 0:
                        hit = data["hits"][0]
                        print(f"   图片来源: Pixabay")
                        return {
                            "url": hit["largeImageURL"],
                            "alt": hit.get("tags", query).split(",")[0],
                        }
            except Exception as e:
                print(f"   Pixabay 搜索失败: {e}")

        print(f"   未找到图片: {query}")
        return None

    async def generate_audio_edge(self, text: str, filename: str, voice: str) -> tuple[str, float]:
        """使用 edge-tts 生成音频"""
        import edge_tts
        import subprocess

        audio_path = self.audio_dir / filename

        if audio_path.exists():
            print(f"   音频已存在: {filename}")
            # 尝试获取实际时长
            actual_duration = self._get_audio_duration(str(audio_path))
            if actual_duration:
                return str(audio_path), actual_duration
            duration = self._estimate_duration(text)
            return str(audio_path), duration

        print(f"   生成 edge-tts: {text[:30]}...")
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(audio_path))
        except Exception as e:
            # 如果 edge-tts 失败，尝试用 subprocess
            print(f"   edge-tts 失败，尝试命令行: {e}")
            try:
                subprocess.run(
                    ["edge-tts", "-t", text, "-f", str(audio_path), "-v", voice],
                    check=True, capture_output=True, timeout=30
                )
            except Exception as e2:
                raise Exception(f"TTS 生成失败: {e2}")

        # 获取实际音频时长
        actual_duration = self._get_audio_duration(str(audio_path))
        if actual_duration:
            return str(audio_path), actual_duration

        duration = self._estimate_duration(text)
        return str(audio_path), duration

    async def generate_audio_pocket(self, text: str, filename: str, voice: str = "alba") -> tuple[str, float]:
        """使用 pocket-tts 生成英文音频"""
        import subprocess
        import shutil

        audio_path = self.audio_dir / filename

        if audio_path.exists():
            print(f"   音频已存在: {filename}")
            # 尝试获取实际时长
            actual_duration = self._get_audio_duration(str(audio_path))
            if actual_duration:
                return str(audio_path), actual_duration
            duration = self._estimate_duration(text)
            return str(audio_path), duration

        # 检查 pocket-tts 是否可用
        if not shutil.which("pocket-tts"):
            raise Exception("pocket-tts 未安装。请运行: pip install pocket-tts")

        print(f"   生成 pocket-tts: {text[:30]}...")

        try:
            result = subprocess.run(
                ["pocket-tts", "generate", "--voice", voice, "--text", text,
                 "--output-path", str(audio_path), "-q"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                raise Exception(f"pocket-tts 失败: {result.stderr}")
        except FileNotFoundError:
            raise Exception("pocket-tts 命令未找到，请确保已安装并配置 PATH")

        # 获取实际音频时长
        actual_duration = self._get_audio_duration(str(audio_path))
        if actual_duration:
            return str(audio_path), actual_duration

        duration = self._estimate_duration(text)
        return str(audio_path), duration

    def _estimate_duration(self, text: str) -> float:
        """估算音频时长"""
        words = len(text.split())
        # 中文约 0.4 秒/字，英文约 0.3 秒/词
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            return words * 0.4
        return words * 0.3

    def _get_audio_duration(self, audio_path: str) -> float:
        """使用 ffprobe 获取实际音频时长"""
        import subprocess
        import shutil

        # 检查 ffprobe 是否可用
        if not shutil.which("ffprobe"):
            print(f"   ⚠️ ffprobe 不可用，使用估算时长")
            return None

        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                print(f"   ✅ 实际音频时长: {duration:.2f}秒")
                return duration
        except Exception as e:
            print(f"   ⚠️ ffprobe 获取时长失败: {e}")

        return None

    async def generate_audio_for_scene(self, scene: dict, word: str) -> dict:
        """为场景生成 TTS - 完全对齐 remotion-tts-web 项目逻辑：
        - 所有场景的 narration 都会生成 audioUrl (edge-tts)
        - Example 场景额外生成 englishAudioUrl (pocket-tts)
        - Highlight 场景特殊处理：为词根/相关词生成单独 TTS
        - 时长计算完全对齐项目
        """
        scene_type = scene.get("type")
        content = scene.get("content", {})

        # 0. 所有场景的 narration 都会生成 TTS（edge-tts）
        if scene.get("narration"):
            narration = scene["narration"]
            # 根据 narrationLang 选择语音
            narration_lang = scene.get("narrationLang", "zh")
            if narration_lang == "zh":
                voice = self.chinese_voice
            else:
                voice = "en-US-JennyNeural"

            narration_filename = f"narration_{scene['id']}_{uuid.uuid4().hex[:6]}.wav"
            try:
                narration_path, narration_duration = await self.generate_audio_edge(
                    narration, narration_filename, voice
                )
                scene["audioUrl"] = f"/audio/tts/{os.path.basename(narration_path)}"
                scene["audioDuration"] = round(narration_duration, 1)
                print(f"   ✅ 场景 {scene['id']} narration TTS: {narration_duration:.1f}秒")
            except Exception as e:
                print(f"   ❌ narration TTS 失败: {e}")
                raise

        # 1. Highlight 场景：额外为词根/相关词生成 TTS
        if scene_type == "highlight" and content.get("rootAffix"):
            print(f"   🎯 Highlight 场景: 为 {len(content['rootAffix'])} 个词根生成 TTS")

            for root_item in content["rootAffix"]:
                # 词根 narration TTS
                if root_item.get("narration"):
                    root_filename = f"root_{root_item.get('root', 'unknown')}_{uuid.uuid4().hex[:4]}.wav"
                    try:
                        root_path, root_duration = await self.generate_audio_edge(
                            root_item["narration"], root_filename, self.chinese_voice
                        )
                        root_item["audioUrl"] = f"/audio/tts/{os.path.basename(root_path)}"
                        root_item["audioDuration"] = round(root_duration, 1)
                        print(f"   ✅ 词根 '{root_item.get('root')}' TTS: {root_duration:.1f}秒")
                    except Exception as e:
                        print(f"   ❌ 词根 TTS 失败: {e}")
                        raise

                # 相关单词 TTS - 与项目保持一致：用和词根一样的中文语音（edge-tts）
                if root_item.get("relatedWords"):
                    for rw in root_item["relatedWords"]:
                        if rw.get("narration"):
                            rw_filename = f"rw_{rw.get('word', 'word')}_{uuid.uuid4().hex[:4]}.wav"
                            try:
                                # 项目逻辑：relatedWords 用和 rootItem 一样的语音
                                rw_path, rw_duration = await self.generate_audio_edge(
                                    rw["narration"], rw_filename, self.chinese_voice
                                )
                                rw["audioUrl"] = f"/audio/tts/{os.path.basename(rw_path)}"
                                rw["audioDuration"] = round(rw_duration, 1)
                                print(f"   ✅ 相关词 '{rw.get('word')}' TTS: {rw_duration:.1f}秒")
                            except Exception as e:
                                print(f"   ❌ 相关单词 TTS 失败: {e}")
                                raise

            # 计算 Highlight 场景时长（与项目完全一致）
            n_roots = len(content["rootAffix"])
            # 顶部动画 = (25 + (n-1)*20 + 15 + 30) / 30
            top_animation = (25 + (n_roots - 1) * 20 + 15 + 30) / 30.0
            # 引导语时长
            intro_audio = scene.get("audioDuration", 2)
            # 词根总时长
            roots_total = 0
            for root_item in content["rootAffix"]:
                roots_total += root_item.get("audioDuration", 3)
                if root_item.get("relatedWords"):
                    for rw in root_item["relatedWords"]:
                        roots_total += rw.get("audioDuration", 1.5)
            # 脚本的 top_animation 已经包含了组件的 30 帧缓冲(1秒)，再加1秒给用户看完整内容
            buffer_time = 1
            total_duration = int(top_animation + intro_audio + roots_total + buffer_time)
            scene["durationSeconds"] = max(scene.get("durationSeconds", 0), total_duration)
            print(f"   📊 Highlight 场景时长: 顶部动画={top_animation:.1f}秒 + 引导语={intro_audio:.1f}秒 + 词根={roots_total:.1f}秒 + 缓冲={buffer_time}秒 = {total_duration}秒")

        # 2. Example 场景：额外生成 englishAudioUrl（pocket-tts）
        if scene_type == "example" and content.get("english"):
            english_text = content["english"]
            english_filename = f"example_en_{scene['id']}_{uuid.uuid4().hex[:6]}.wav"

            try:
                eng_path, eng_duration = await self.generate_audio_pocket(
                    english_text, english_filename, self.english_voice
                )
                content["englishAudioUrl"] = f"/audio/tts/{os.path.basename(eng_path)}"
                content["englishAudioDuration"] = round(eng_duration, 1)
                print(f"   ✅ 例句英文 TTS: {eng_duration:.1f}秒")

                # 时长 = max(原时长, 英文 + 旁白 + 1.0)
                narration_duration = scene.get("audioDuration", 0)
                total_audio = eng_duration + narration_duration + 1.0
                scene["durationSeconds"] = max(scene.get("durationSeconds", 0), int(total_audio))
                print(f"   📊 Example 场景时长: max({scene.get('durationSeconds', 0)}, 英文{eng_duration:.1f}+旁白{narration_duration:.1f}+1.0) = {scene['durationSeconds']}秒")
            except Exception as e:
                print(f"   ❌ 例句英文 TTS 失败: {e}")
                raise

        # 3. 其他场景（title/vocabulary-card）：时长 = ceil(音频 + 0.5) 与项目保持一致
        if scene_type in ("title", "vocabulary-card") and scene.get("audioDuration"):
            import math
            scene["durationSeconds"] = math.ceil(scene["audioDuration"] + 0.5)

        # 4. Summary 场景：需要为每个要点分配足够时间
        # 组件会把 audioDuration 平均分配给每个要点依次显示
        # 人的观看逻辑：标题出现 → 要点1出现并阅读 → 要点2出现并阅读 → ... → 全部显示完停留
        if scene_type == "summary" and content.get("points"):
            import math
            points = content["points"] if isinstance(content["points"], list) else []
            n_points = len(points)
            audio_dur = scene.get("audioDuration", 0)

            if n_points > 0:
                # 每个要点需要的时间：至少3秒阅读时间 + 音频平均分配时间
                per_point_reading = 3  # 阅读时间
                per_point_audio = audio_dur / n_points if audio_dur > 0 else 2
                per_point_total = max(per_point_reading, per_point_audio)

                # 总时长 = 标题(1秒) + 每个要点时间 + 结尾停留(2秒)
                title_time = 1
                end_buffer = 2
                total = title_time + n_points * per_point_total + end_buffer

                # 最多30秒
                scene["durationSeconds"] = min(int(total), 30)
                print(f"   📊 Summary 场景: 标题{title_time}秒 + 要点{n_points}个×{per_point_total:.1f}秒 + 结尾{end_buffer}秒 = {scene['durationSeconds']}秒")

        return scene

    async def add_images_to_script(self, script: dict, word: str) -> dict:
        """为脚本添加图片"""
        print("   搜索图片...")

        # 找到 highlight 和 example 场景
        for scene in script.get("scenes", []):
            scene_type = scene.get("type")
            content = scene.get("content", {})

            if scene_type == "highlight":
                # 为词根场景添加单词图片
                query = word
                image = await self.search_image(query)
                if image:
                    if "images" not in content:
                        content["images"] = []
                    content["images"].append({
                        "url": image["url"],
                        "alt": image["alt"],
                        "position": "right",
                        "size": "medium",
                    })

            elif scene_type == "example":
                # 为例句场景添加图片
                english = content.get("english", "")
                if english:
                    # 用英文句子中的一些关键词搜索
                    keywords = " ".join(english.split()[:5])
                    image = await self.search_image(keywords)
                    if image:
                        if "images" not in content:
                            content["images"] = []
                        content["images"].append({
                            "url": image["url"],
                            "alt": image["alt"],
                            "position": "center",
                            "size": "medium",
                        })

        return script

    async def generate_single(self, word: str) -> dict:
        """生成单个单词视频"""
        print(f"\n📹 生成视频: {word}")
        print("=" * 50)

        # 1. 调用 LLM 生成教学脚本
        print("\n🎯 调用 AI 生成教学脚本...")
        try:
            script = await self.call_llm(word)
        except Exception as e:
            print(f"❌ LLM 调用失败: {e}")
            return {"word": word, "success": False, "error": str(e)}

        # 2. 搜索图片
        print("\n🖼️ 搜索图片...")
        script = await self.add_images_to_script(script, word)

        # 3. 为每个场景生成 TTS
        print("\n🔊 生成场景旁白 TTS...")
        updated_scenes = []
        for scene in script.get("scenes", []):
            scene = await self.generate_audio_for_scene(scene, word)
            updated_scenes.append(scene)
        script["scenes"] = updated_scenes

        # 4. 计算总时长
        total_duration = sum(s.get("durationSeconds", 5) for s in script.get("scenes", []))

        # 5. 收集所有音频文件路径到 audioUrls（修复：渲染脚本需要这个字段）
        audio_urls = {}
        for scene in script.get("scenes", []):
            scene_id = scene.get("id", "")
            # 场景的 narration 音频
            if scene.get("audioUrl"):
                audio_urls[f"{scene_id}_narration"] = str(self.audio_dir / scene["audioUrl"].split("/")[-1])
            # highlight 场景的词根音频
            if scene.get("type") == "highlight":
                content = scene.get("content", {})
                if content.get("rootAffix"):
                    for root_item in content["rootAffix"]:
                        if root_item.get("audioUrl"):
                            root_name = root_item.get("root", "root")
                            audio_urls[f"{scene_id}_root_{root_name}"] = str(self.audio_dir / root_item["audioUrl"].split("/")[-1])
                        if root_item.get("relatedWords"):
                            for rw in root_item["relatedWords"]:
                                if rw.get("audioUrl"):
                                    word_name = rw.get("word", "word")
                                    audio_urls[f"{scene_id}_rw_{word_name}"] = str(self.audio_dir / rw["audioUrl"].split("/")[-1])
            # example 场景的英文音频
            if scene.get("type") == "example":
                content = scene.get("content", {})
                if content.get("englishAudioUrl"):
                    audio_urls[f"{scene_id}_english"] = str(self.audio_dir / content["englishAudioUrl"].split("/")[-1])

        # 6. 生成配置文件
        print("\n📝 生成视频配置...")
        video_id = uuid.uuid4().hex[:8]
        config = {
            "script": script,
            "audioUrls": audio_urls,  # 修复：填充 audioUrls
            "outputPath": str(self.output_dir / f"teaching-{word}-{video_id}.mp4")
        }

        config_path = self.tmp_dir / f"config-{word}-{video_id}.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"   配置已保存: {config_path}")
        print(f"   预计时长: {total_duration} 秒")

        # 6. 渲染视频
        print("\n🎬 渲染视频...")
        success = self.render_video(str(config_path))

        if success:
            video_path = Path(config["outputPath"])
            if video_path.exists():
                size = video_path.stat().st_size / 1024 / 1024
                print(f"✅ 视频生成成功!")
                print(f"   路径: {video_path}")
                print(f"   大小: {size:.1f} MB")
                return {"word": word, "success": True, "path": str(video_path)}

        print(f"❌ 视频渲染失败")
        return {"word": word, "success": False, "error": "渲染失败"}

    def render_video(self, config_path: str) -> bool:
        """调用 Remotion 渲染视频"""
        import subprocess

        # 优先使用项目的渲染脚本（因为有 node_modules）
        # skill 的脚本用于组件定义，但渲染需要项目环境
        project_root = self.project_dir.parent

        # 优先检查项目脚本
        possible_paths = [
            self.project_dir / "render-teaching.mjs",  # skill 目录本身
            self.project_dir / "scripts/render-teaching.mjs",
            project_root / "remotion-tts-web/scripts/render-teaching.mjs",
        ]

        render_script = None
        render_cwd = None  # 工作目录
        for p in possible_paths:
            if isinstance(p, Path) and p.exists():
                render_script = str(p)
                # 工作目录设为脚本所在目录
                render_cwd = str(p.parent)
                print(f"   使用项目渲染脚本: {render_script}")
                print(f"   工作目录: {render_cwd}")
                break

        if not render_script:
            print("⚠️ 未找到 render-teaching.mjs，跳过渲染")
            return False

        try:
            # 设置工作目录为项目目录
            result = subprocess.run(
                ["node", render_script, config_path],
                capture_output=True,
                text=True,
                timeout=600,
                encoding='utf-8',
                errors='ignore',
                cwd=render_cwd
            )

            # 打印所有输出以便调试
            if result.stdout:
                print(f"   stdout: {result.stdout[:500]}")
            if result.stderr:
                print(f"   stderr: {result.stderr[:500]}")

            if result.returncode == 0:
                return True
            else:
                print(f"   渲染错误: {result.stderr[:500]}")
                return False

        except subprocess.TimeoutExpired:
            print("   ❌ 渲染超时")
            return False
        except FileNotFoundError:
            print("   ❌ 未找到 Node.js")
            return False

    async def generate(self, words: list[str]) -> list[dict]:
        """生成多个单词视频"""
        results = []
        for word in words:
            word = word.strip()
            if not word:
                continue

            try:
                result = await self.generate_single(word)
                results.append(result)
            except Exception as e:
                print(f"❌ 生成失败: {e}")
                results.append({"word": word, "success": False, "error": str(e)})

        return results


async def main():
    parser = argparse.ArgumentParser(description="单词教学视频生成器")
    parser.add_argument("-w", "--word", help="单个单词")
    parser.add_argument("-l", "--words", help="单词列表（逗号分隔）")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="输出目录")
    parser.add_argument("-c", "--chinese-voice", default=DEFAULT_CHINESE_VOICE, help="中文旁白语音 (edge-tts)")
    parser.add_argument("-e", "--english-voice", default=DEFAULT_ENGLISH_VOICE, help="英文例句语音 (pocket-tts)")
    parser.add_argument("--env", default=None, help=".env 文件路径")

    args = parser.parse_args()

    words = []
    if args.word:
        words = [args.word]
    elif args.words:
        words = [w.strip() for w in args.words.split(",")]
    else:
        print("错误: 请提供 --word 或 --words 参数")
        parser.print_help()
        sys.exit(1)

    print("=" * 60)
    print("🎬 单词教学视频生成器（完整版）")
    print("=" * 60)
    print(f"📚 单词: {', '.join(words)}")
    print(f"📁 输出: {args.output}")
    print(f"🔊 中文旁白: {args.chinese_voice} (edge-tts)")
    print(f"🔊 英文例句: {args.english_voice} (pocket-tts)")

    generator = VocabVideoGenerator(
        args.output,
        chinese_voice=args.chinese_voice,
        english_voice=args.english_voice,
        env_path=args.env
    )
    results = await generator.generate(words)

    print("\n" + "=" * 60)
    print("📊 生成结果")
    print("=" * 60)

    for r in results:
        if r.get("success"):
            print(f"✅ {r['word']}: {r['path']}")
        else:
            print(f"❌ {r['word']}: {r.get('error', '未知错误')}")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
