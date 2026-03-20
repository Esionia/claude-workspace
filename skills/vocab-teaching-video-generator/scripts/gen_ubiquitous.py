#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词教学视频生成器（简化版）
直接从 .env 读取配置生成视频

用法:
    python gen_ubiquitous.py --word creativity

注意: 推荐使用 generate_vocab_video.py 作为入口脚本
"""
import sys
import json
import re
import requests
import uuid
import asyncio
import edge_tts
import os
import argparse
from pathlib import Path

# ========== 从 .env 加载配置 ==========
def load_env():
    """从 .env 文件加载配置"""
    script_dir = Path(__file__).parent
    env_paths = [
        script_dir / ".env",
        script_dir.parent / ".env",
        Path.cwd() / ".env",
    ]
    env_file = None
    for p in env_paths:
        if p.exists():
            env_file = p
            break

    config = {}
    if env_file:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip().strip('"').strip("'")
    return config

env_config = load_env()
LLM_API_KEY = env_config.get("LLM_API_KEY")
LLM_BASE_URL = env_config.get("LLM_BASE_URL", "https://api.minimax.chat/v1")
LLM_MODEL = env_config.get("LLM_MODEL", "MiniMax-M2.5-highspeed")
PEXELS_API_KEY = env_config.get("PEXELS_API_KEY")
# ========== 配置结束 ==========

VOCABULARY_SYSTEM_PROMPT = """你是一个专业的英语教学视频脚本生成助手。

【必须严格遵守】词汇教学场景顺序：
1. cover - 视频封面，展示单词和中文翻译
2. title - 介绍要学习的单词
3. vocabulary-card - 展示单词卡片（词性、释义）
4. highlight - 词根词缀讲解
5. example - 例句演示（需要2个例句）
6. summary - 要点总结

场景必须按照上述 1→2→3→4→5→6 的顺序生成，不得调换顺序！

重要要求：
1. cover场景：
   - word: 英文单词
   - translation: 中文翻译
   - narration: 简短开场白（不超过10字）
2. vocabulary-card场景（推荐使用定义模式）：
   - **定义模式**（推荐）：展示单词、词性、多个释义，不包含例句
   - 不要生成 phraseAudioUrl、exampleAudioUrl、phraseAudioDuration 等音频字段
3. highlight场景：必须讲解词根词缀、构词法或记忆方法
4. example场景（必须2个）：
   - narration格式："[英文句子]. 意思是：[中文翻译]"
   - 必须在highlights数组中标注目标词汇
5. summary的points必须是字符串数组，包含3-4个要点
6. 每个场景的narration要详细，不要过于简短
7. ⚠️ 所有 narration 必须使用中文！

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

## 输出 JSON 结构
{
  "id": "video_script_单词_001",
  "topic": "英语词汇教学：单词",
  "description": "通过词根词缀法讲解...",
  "targetAudience": "英语学习者",
  "totalDuration": 180,
  "scenes": [
    {"id": "scene_001", "type": "cover", "content": {"type":"cover","word":"单词","translation":"中文释义"}, "narration": "简短开场白", "narrationLang": "zh", "durationSeconds": 5},
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

# 设置输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

word = 'ubiquitous'
prompt = f"""请为以下英语词汇生成教学视频脚本：

词汇：{word}

请基于以上信息生成完整的教学脚本 JSON。"""

# 调用 LLM
api_url = f"{LLM_BASE_URL}/text/chatcompletion_v2"
request_json = {
    "model": LLM_MODEL,
    "messages": [
        {"role": "system", "content": VOCABULARY_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ],
    "max_tokens": 8000,
}

print("Calling LLM API...")
response = requests.post(
    api_url,
    headers={
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    },
    json=request_json,
    timeout=120,
)

data = response.json()
content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
print(f"LLM response length: {len(content)}")
print(f"LLM response preview: {content[:500]}")

# 清理JSON
content = content.replace('```json', '').replace('```', '').strip()

# 移除控制字符
content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', content)

# 提取JSON
start_idx = content.find('{')
end_idx = content.rfind('}')
if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
    content = content[start_idx:end_idx+1]

# 替换中文引号为英文引号
content = content.replace('\u201c', '"').replace('\u201d', '"')
content = content.replace('\u2018', "'").replace('\u2019', "'")

# 修复中文冒号
content = content.replace('：', ':')

# 移除可能的尾部逗号
content = re.sub(r',(\s*[}\]])', r'\1', content)

try:
    script = json.loads(content)
    print(f"JSON parsed successfully! Scenes: {len(script.get('scenes', []))}")
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
    # 最后尝试：提取JSON
    import re
    match = re.search(r'\{[\s\S]*\}', content)
    if match:
        try:
            script = json.loads(match.group())
            print("JSON parsed after extraction!")
        except:
            print("Failed to parse JSON")
            sys.exit(1)
    else:
        print("Failed to extract JSON")
        sys.exit(1)

# 搜索图片
def search_image(query):
    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 1},
            timeout=10,
        )
        if response.ok:
            data = response.json()
            if data.get('photos') and len(data['photos']) > 0:
                photo = data['photos'][0]
                return {
                    'url': photo['src']['large'],
                    'alt': photo.get('alt', query),
                }
    except Exception as e:
        print(f"Image search error: {e}")
    return None

# 添加图片
for scene in script.get('scenes', []):
    scene_type = scene.get('type')
    content = scene.get('content', {})
    if scene_type == 'highlight':
        image = search_image(word)
        if image and 'images' not in content:
            content['images'] = [{
                'url': image['url'],
                'alt': image['alt'],
                'position': 'right',
                'size': 'medium',
            }]
    elif scene_type == 'example':
        english = content.get('english', '')
        if english:
            keywords = ' '.join(english.split()[:5])
            image = search_image(keywords)
            if image and 'images' not in content:
                content['images'] = [{
                    'url': image['url'],
                    'alt': image['alt'],
                    'position': 'center',
                    'size': 'medium',
                }]

print("Images added")

# TTS生成
async def generate_tts():
    # 使用项目目录
    project_dir = r"E:\remotion-projects\remotion-tts-web"
    audio_dir = os.path.join(project_dir, 'public', 'audio', 'tts')
    os.makedirs(audio_dir, exist_ok=True)

    for scene in script.get('scenes', []):
        if scene.get('narration'):
            narration = scene['narration']
            filename = f'narration_{scene["id"]}_{uuid.uuid4().hex[:6]}.wav'
            filepath = os.path.join(audio_dir, filename)
            try:
                communicate = edge_tts.Communicate(narration, 'zh-CN-XiaoxiaoNeural')
                await communicate.save(filepath)
                scene['audioUrl'] = f'/audio/tts/{os.path.basename(filepath)}'
                print(f'Generated TTS: {filename}')
            except Exception as e:
                print(f'TTS error for {scene["id"]}: {e}')

        # Example场景的英文TTS
        if scene.get('type') == 'example' and scene.get('content', {}).get('english'):
            eng_text = scene['content']['english']
            eng_filename = f'example_en_{scene["id"]}_{uuid.uuid4().hex[:6]}.wav'
            eng_filepath = os.path.join(audio_dir, eng_filename)
            try:
                communicate = edge_tts.Communicate(eng_text, 'en-US-JennyNeural')
                await communicate.save(eng_filepath)
                scene['content']['englishAudioUrl'] = f'/audio/tts/{os.path.basename(eng_filepath)}'
                print(f'Generated English TTS: {eng_filename}')
            except Exception as e:
                print(f'English TTS error: {e}')

asyncio.run(generate_tts())

# 保存配置
video_id = uuid.uuid4().hex[:8]
config = {
    'script': script,
    'audioUrls': {},
    'outputPath': f'public/videos/teaching-{word}-{video_id}.mp4'
}

project_dir = r"E:\remotion-projects\remotion-tts-web"
tmp_dir = os.path.join(project_dir, 'tmp')
os.makedirs(tmp_dir, exist_ok=True)

config_path = os.path.join(tmp_dir, f'config-{word}-{video_id}.json')
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print(f"Config saved: {config_path}")
print(f"Total scenes: {len(script.get('scenes', []))}")
