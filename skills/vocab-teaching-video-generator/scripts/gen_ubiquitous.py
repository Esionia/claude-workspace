#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import re
import requests
import uuid
import asyncio
import edge_tts
import os

# 配置
LLM_API_KEY = 'sk-cp-gdGTi4HzW2-ylk3C987WKCgdAo_iDFzwpGJtW6mB7J4oYfXcczI_nj5zLntBP-Z9l1SSqlIsfBw2ZUAx2Pc2XSfjscQUPZh_SBkDok3SqXERDFbzIb0mOzU'
LLM_BASE_URL = 'https://api.minimax.chat/v1'
LLM_MODEL = 'MiniMax-M2.5-highspeed'
PEXELS_API_KEY = 'Dshxi5xWpb66eycODl7Es8D5hyX8vkKqeBZIdvt34isCVRXr67SHu0A2'

VOCABULARY_SYSTEM_PROMPT = """你是一个专业的英语教学视频脚本生成助手。

【必须严格遵守】词汇教学场景顺序：
1. title - 介绍要学习的单词
2. vocabulary-card - 展示单词卡片（词性、释义）
3. highlight - 词根词缀讲解
4. example - 例句演示（需要2个例句）
5. summary - 要点总结

场景必须按照上述 1→2→3→4→5 的顺序生成，不得调换顺序！

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
拆解原则：
1. 词根/词缀必须真实存在于目标单词中
2. 拆解必须完整覆盖整个单词
3. 词根含义必须与单词意思相关
4. 相关单词必须包含相同的词根/词缀

## 输出 JSON 结构
{
  "id": "video_script_单词_001",
  "topic": "英语词汇教学：单词",
  "description": "通过词根词缀法讲解...",
  "targetAudience": "英语学习者",
  "totalDuration": 180,
  "scenes": [
    {"id": "scene_001", "type": "title", "content": {"type":"title","mainTitle":"单词","subtitle":"中文"}, "narration": "中文旁白", "narrationLang": "zh", "durationSeconds": 10},
    {"id": "scene_002", "type": "vocabulary-card", "content": {"type":"vocabulary-card","phrase":"单词","meaning":"中文","partOfSpeech":"adj.","definitions":["释义1","释义2"]}, "narration": "中文旁白", "narrationLang": "zh", "durationSeconds": 15},
    {"id": "scene_003", "type": "highlight", "content": {"type":"highlight","sentence":"单词","highlights":[{"text":"词根","color":"#FFD93D","label":"词根"}],"rootAffix":[{"root":"词根","meaning":"含义","label":"词根/后缀","narration":"该词根的详细讲解","relatedWords":[{"word":"相关词","meaning":"含义","highlight":"词根","narration":"词，含义"}]}]}, "narration": "简短的引导语", "narrationLang": "zh", "durationSeconds": 30},
    {"id": "scene_004", "type": "example", "content": {"type":"example","english":"英文例句1","chinese":"中文翻译1","highlights":[{"text":"单词","color":"#FFD93D"}]}, "narration": "英文例句1. 意思是：中文解释", "narrationLang": "zh", "durationSeconds": 8},
    {"id": "scene_005", "type": "example", "content": {"type":"example","english":"英文例句2","chinese":"中文翻译2","highlights":[{"text":"单词","color":"#FFD93D"}]}, "narration": "英文例句2. 意思是：中文解释", "narrationLang": "zh", "durationSeconds": 8},
    {"id": "scene_006", "type": "summary", "content": {"type":"summary","points":["要点1","要点2","要点3"]}, "narration": "总结旁白", "narrationLang": "zh", "durationSeconds": 20}
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
