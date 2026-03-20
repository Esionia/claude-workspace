#!/usr/bin/env python3
"""
Avatar Vocab Video Generator
单词教学视频 + 数字人 Anna 语音克隆 + 右下角 PIP

Pipeline:
1. LLM 生成脚本 → 不变
2. 图片搜索 → 不变
3. Anna per-scene 克隆 + 合并旁白克隆 → 获取 COS URL（Avatar 用）
4. Remotion 渲染 → 不变
5. Avatar 数字人（COS URL） + FFmpeg 合成
"""

import sys, os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import argparse, asyncio, http.server, json, math, shutil, subprocess
import threading, time, uuid
from pathlib import Path
from typing import Optional
import importlib

# ========== 依赖检查 ==========
def check_dependencies():
    required = ["requests"]
    missing = []
    for pkg in required:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[INFO] 安装缺失依赖: {', '.join(missing)}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True, capture_output=True)
        except Exception as e:
            print(f"[ERROR] 依赖安装失败: {e}")
            return False
    return True

if not check_dependencies():
    sys.exit(1)

import requests
from pydub import AudioSegment

# ========== 路径配置 ==========
SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
PUBLIC_DIR = SCRIPTS_DIR / "public"
AUDIO_DIR = PUBLIC_DIR / "audio" / "tts"
VIDEO_DIR = PUBLIC_DIR / "videos"
TMP_DIR = SCRIPTS_DIR / "tmp"

VT_SKILL = SKILL_DIR.parent / "vocab-teaching-video-generator"
VT_SCRIPTS = VT_SKILL / "scripts"
VT_PUBLIC = VT_SKILL / "public"

# ========== 数字人 API 配置 ==========
AIGC_API = "https://dapi.qingyu.club/api"
AIGC_TOKEN_FILE = Path.home() / ".aigc_voice_token"
AIGC_CREDS_FILE = Path.home() / ".aigc_voice_credentials"

DEFAULT_VOICE_URL = (
    "https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/3044/audio/1772783478839_nahh8q.wav"
)
DEFAULT_DIGITAL_HUMAN_URL = (
    "https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/3044/video/1773933921981_uzbdvw.mp4"
)

# ========== LLM Prompt（完全复制 vocab-teaching）==========
VOCABULARY_SYSTEM_PROMPT = """你是一个专业的英语教学视频脚本生成助手。

**【必须严格遵守】词汇教学场景顺序：**
1. **title** - 介绍要学习的单词
2. **vocabulary-card** - 展示单词卡片（词性、释义）
3. **highlight** - 词根词缀讲解
4. **example** - 例句演示（需要2个例句）
5. **summary** - 要点总结

⚠️ 场景必须按照上述 1→2→3→4→5 的顺序生成，不得调换顺序！

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

常见单词拆解示例：
- encourage = en- + cour + -age
- transportation = trans- + port + -ation
- important = im- + port + -ant

highlight场景的content结构：
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
    {"id": "scene_001", "type": "title", "content": {"type":"title","mainTitle":"单词","subtitle":"中文"}, "narration": "中文旁白", "narrationLang": "zh", "durationSeconds": 10},
    {"id": "scene_002", "type": "vocabulary-card", "content": {"type":"vocabulary-card","phrase":"单词","meaning":"中文","partOfSpeech":"adj.","definitions":["释义1","释义2"]}, "narration": "中文旁白", "narrationLang": "zh", "durationSeconds": 15},
    {"id": "scene_003", "type": "highlight", "content": {"type":"highlight","sentence":"单词","highlights":[{"text":"词根","color":"#FFD93D","label":"词根"}],"rootAffix":[{"root":"词根","meaning":"含义","label":"词根/后缀","narration":"该词根的详细讲解","relatedWords":[{"word":"相关词","meaning":"含义","highlight":"词根","narration":"词，含义"}]}]}, "narration": "简短的引导语", "narrationLang": "zh", "durationSeconds": 30},
    {"id": "scene_004", "type": "example", "content": {"type":"example","english":"英文例句1","chinese":"中文翻译1","highlights":[{"text":"单词","color":"#FFD93D"}]}, "narration": "英文例句1. 意思是：中文解释", "narrationLang": "zh", "durationSeconds": 8},
    {"id": "scene_005", "type": "example", "content": {"type":"example","english":"英文例句2","chinese":"中文翻译2","highlights":[{"text":"单词","color":"#FFD93D"}]}, "narration": "英文例句2. 意思是：中文解释", "narrationLang": "zh", "durationSeconds": 8},
    {"id": "scene_006", "type": "summary", "content": {"type":"summary","points":["要点1","要点2","要点3"]}, "narration": "总结旁白", "narrationLang": "zh", "durationSeconds": 20}
  ]
}"""


# ========== 数字人客户端 ==========
class AIGCClient:
    def __init__(self, voice_url=None, avatar_url=None):
        self.base_url = AIGC_API
        self.voice_url = voice_url or DEFAULT_VOICE_URL
        self.avatar_url = avatar_url or DEFAULT_DIGITAL_HUMAN_URL
        self.token = self._load_token()
        self._email, self._password = self._load_creds()

    def _load_token(self):
        if AIGC_TOKEN_FILE.exists():
            return AIGC_TOKEN_FILE.read_text().strip()
        return None

    def _load_creds(self):
        if AIGC_CREDS_FILE.exists():
            try:
                data = json.loads(AIGC_CREDS_FILE.read_text())
                return data.get("email"), data.get("password")
            except:
                pass
        env_file = SKILL_DIR.parent / "ai-avatar" / "config.env"
        if env_file.exists():
            email, password = None, None
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    v = v.strip()
                    if k == "EMAIL" and not email:
                        email = v
                    elif k == "PASSWORD" and not password:
                        password = v
            if email and password:
                return email, password
        return None, None

    def _save_creds(self, email, password):
        AIGC_CREDS_FILE.write_text(json.dumps({"email": email, "password": password}))

    def _save_token(self, token):
        AIGC_TOKEN_FILE.write_text(token)

    def login(self, email, password):
        r = requests.post(
            f"{self.base_url}/users/login",
            json={"email": email, "password": password},
            verify=False, timeout=30
        )
        result = r.json()
        if result.get("success"):
            self.token = result["data"]["token"]
            self._save_token(self.token)
            self._save_creds(email, password)
            print(f"[OK] AIGC 登录成功")
            return True
        print(f"[ERR] AIGC 登录失败: {result.get('message', '未知')}")
        return False

    def _ensure_token(self):
        if not self.token:
            if self._email and self._password:
                self.login(self._email, self._password)
            else:
                raise RuntimeError("请先运行: python generate.py --login <email> <password>")
        return self.token

    def _get_duration(self, path):
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", path],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0 and r.stdout.strip():
                return float(r.stdout.strip())
        except:
            pass
        return 5.0

    def _download_file(self, url, path):
        for attempt in range(3):
            try:
                r = requests.get(url, verify=False, timeout=120, stream=True)
                r.raise_for_status()
                path.write_bytes(r.content)
                return True
            except Exception as e:
                if attempt == 2:
                    raise RuntimeError(f"下载失败: {e}")
                time.sleep(5)
        return False

    def clone_voice(self, text, speed=1.0):
        """克隆单段语音，返回 (本地文件路径, 时长)"""
        token = self._ensure_token()
        url = f"{self.base_url}/voice-clone-v2/task"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "text": text,
            "speaker_audio_url": self.voice_url,
            "speed": speed,
        }
        print(f"    [Anna] 提交克隆: {text[:30]}...")
        r = requests.post(url, json=payload, headers=headers, verify=False, timeout=60)
        result = r.json()

        # 解析 task_id（API 返回格式不稳定，尝试多种方式）
        task_id = (
            result.get("task_id")
            or (result.get("data") or {}).get("task_id")
            or (result.get("data") or {}).get("taskId")
        )
        if not task_id:
            raise RuntimeError(f"克隆任务提交失败: {result.get('message', result)}")

        print(f"    [Anna] 等待克隆 (task={task_id[:16]}...)")
        for _ in range(200):
            r2 = requests.get(url, params={"task_id": task_id}, headers=headers, verify=False, timeout=30)
            data = r2.json().get("data") or r2.json()
            state = data.get("state") or data.get("status")
            if state in ("SUCCESS", "completed", "success"):
                audio_url = data.get("audio_url")
                if not audio_url:
                    audio_url = data.get("result", {}).get("audio_url")
                if not audio_url:
                    # voice clone 返回格式可能不同
                    audio_url = data.get("audio_url") or data.get("url")
                print(f"    [Anna] 克隆完成!")
                return self._download_and_save(audio_url)
            elif state in ("FAILED", "failed"):
                raise RuntimeError(f"克隆失败: {data.get('error_message') or data.get('error')}")
            print(f"    [Anna] {state}...")
            time.sleep(3)
        raise RuntimeError("克隆超时")

    def _download_and_save(self, audio_url):
        """下载音频到本地，返回 (路径, 时长)"""
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"anna_{uuid.uuid4().hex[:8]}.wav"
        path = AUDIO_DIR / filename
        print(f"    [Anna] 下载: {audio_url[:50]}...")
        if not self._download_file(audio_url, path):
            raise RuntimeError("下载失败")
        duration = self._get_duration(str(path))
        print(f"    [Anna] 保存: {filename} ({duration:.1f}s)")
        return str(path), duration

    def clone_voice_merged(self, text, speed=1.0):
        """克隆合并旁白，返回 (COS URL, 本地文件路径)"""
        # voice clone API 返回的 audio_url 是 COS URL，可直接用于 Avatar
        token = self._ensure_token()
        url = f"{self.base_url}/voice-clone-v2/task"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "text": text,
            "speaker_audio_url": self.voice_url,
            "speed": speed,
        }
        print(f"    [Anna] 提交合并克隆...")
        r = requests.post(url, json=payload, headers=headers, verify=False, timeout=60)
        result = r.json()

        task_id = (
            result.get("task_id")
            or (result.get("data") or {}).get("task_id")
            or (result.get("data") or {}).get("taskId")
        )
        if not task_id:
            raise RuntimeError(f"合并克隆任务提交失败: {result.get('message', result)}")

        print(f"    [Anna] 等待合并克隆 (task={task_id[:16]}...)")
        for _ in range(200):
            r2 = requests.get(url, params={"task_id": task_id}, headers=headers, verify=False, timeout=30)
            data = r2.json().get("data") or r2.json()
            state = data.get("state") or data.get("status")
            if state in ("SUCCESS", "completed", "success"):
                audio_url = (
                    data.get("audio_url")
                    or data.get("result", {}).get("audio_url")
                    or data.get("url")
                )
                if not audio_url:
                    raise RuntimeError(f"合并克隆完成但未返回 URL: {data}")
                print(f"    [Anna] 合并克隆完成! COS URL: {audio_url[:60]}...")

                # 下载到本地
                filename = f"merged_narration_{uuid.uuid4().hex[:8]}.wav"
                path = AUDIO_DIR / filename
                self._download_file(audio_url, path)
                duration = self._get_duration(str(path))
                print(f"    [Anna] 本地: {filename} ({duration:.1f}s)")
                return audio_url, str(path)
            elif state in ("FAILED", "failed"):
                raise RuntimeError(f"合并克隆失败: {data.get('error_message') or data.get('error')}")
            print(f"    [Anna] {state}...")
            time.sleep(3)
        raise RuntimeError("合并克隆超时")

    def generate_digital_human(self, audio_url, video_url=None, model_version="V2"):
        """生成数字人视频（通过公开 URL）"""
        token = self._ensure_token()
        url = f"{self.base_url}/tasks/task"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "audio_url": audio_url,
            "video_url": video_url or self.avatar_url,
            "model_version": model_version,
        }
        print(f"    [Anna] 提交数字人任务...")
        r = requests.post(url, json=payload, headers=headers, verify=False, timeout=60)
        result = r.json()

        task_id = (
            result.get("data", {}).get("taskId")
            or result.get("task_id")
        )
        if not task_id:
            raise RuntimeError(f"数字人任务失败: {result.get('message', result)}")

        print(f"    [Anna] 等待数字人 (task={task_id[:16]}...)")
        status_url = f"{self.base_url}/tasks/task/{task_id}/status"
        for _ in range(200):
            r2 = requests.get(status_url, headers=headers, verify=False, timeout=30)
            data = r2.json().get("data") or r2.json()
            status = data.get("status") or data.get("state")
            if status == "completed":
                v_url = (
                    data.get("result", {}).get("output_file")
                    or data.get("video_url")
                    or data.get("output_file")
                )
                if not v_url:
                    v_url = data.get("result", {}).get("url")
                print(f"    [Anna] 数字人完成!")
                return self._download_video(v_url)
            elif status == "failed":
                err = (
                    data.get("result", {}).get("error")
                    or data.get("error")
                    or data.get("message")
                    or str(data)
                )
                raise RuntimeError(f"数字人失败: {err}")
            print(f"    [Anna] {status}...")
            time.sleep(3)
        raise RuntimeError("数字人超时")

    def _download_video(self, url):
        VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"avatar_{uuid.uuid4().hex[:8]}.mp4"
        path = VIDEO_DIR / filename
        print(f"    [Anna] 下载视频: {filename}")
        if not self._download_file(url, path):
            raise RuntimeError("视频下载失败")
        size = path.stat().st_size / 1024 / 1024
        print(f"    [Anna] 保存: {filename} ({size:.1f}MB)")
        return str(path)


# ========== 主生成器 ==========
class AvatarVocabVideoGenerator:

    def __init__(self, env_path=None):
        self.audio_dir = AUDIO_DIR
        self.video_dir = VIDEO_DIR
        self.tmp_dir = TMP_DIR
        self.public_dir = PUBLIC_DIR
        self.llm_api_key = None
        self.llm_base_url = None
        self.llm_model = None
        self.pexels_key = None
        self._load_env(env_path)
        for d in [self.audio_dir, self.video_dir, self.tmp_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _load_env(self, env_path=None):
        if env_path:
            env_file = Path(env_path)
        else:
            candidates = [SKILL_DIR / ".env", SCRIPTS_DIR / ".env", VT_SKILL / ".env"]
            env_file = None
            for p in candidates:
                if p.exists():
                    env_file = p
                    break
        if env_file and env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                if k == "LLM_API_KEY":
                    self.llm_api_key = self.llm_api_key or v
                elif k == "LLM_BASE_URL":
                    self.llm_base_url = self.llm_base_url or v
                elif k == "LLM_MODEL":
                    self.llm_model = self.llm_model or v
                elif k == "PEXELS_API_KEY":
                    self.pexels_key = v

    # ---- LLM ----
    def call_llm(self, word):
        if not self.llm_api_key or not self.llm_base_url:
            raise RuntimeError("LLM API 未配置，请检查 .env")
        prompt = f"请为以下英语词汇生成教学视频脚本：\n\n词汇：{word}\n\n请基于以上信息生成完整的教学脚本 JSON。"
        is_minimax = "minimax" in (self.llm_base_url or "").lower()
        api_url = (
            f"{self.llm_base_url}/text/chatcompletion_v2"
            if is_minimax
            else f"{self.llm_base_url}/chat/completions"
        )
        request_json = {
            "model": self.llm_model or "gpt-4o",
            "messages": [
                {"role": "system", "content": VOCABULARY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 8000,
        }
        if not is_minimax:
            request_json["response_format"] = {"type": "json_object"}

        print(f"    [LLM] {self.llm_base_url}")
        r = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {self.llm_api_key}", "Content-Type": "application/json"},
            json=request_json, timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        content = (
            data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if is_minimax
            else data["choices"][0]["message"]["content"]
        )
        if not content:
            raise RuntimeError(f"LLM 返回为空: {data}")

        import re
        content = content.replace("```json", "").replace("```", "").strip()
        content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', content)
        content = content.replace("：", ":").replace("，", ",").replace("。", ".")
        content = content.replace("（", "(").replace("）", ")")
        content = content.replace("【", "[").replace("】", "]")

        try:
            script = json.loads(content)
        except json.JSONDecodeError as e:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                script = json.loads(content[start:end])
            else:
                raise RuntimeError(f"JSON 解析失败: {e}\n{content[:300]}")

        print(f"    [LLM] 生成 {len(script.get('scenes', []))} 个场景")
        return script

    # ---- 图片搜索 ----
    def search_image(self, query):
        if self.pexels_key:
            try:
                r = requests.get(
                    "https://api.pexels.com/v1/search",
                    headers={"Authorization": self.pexels_key},
                    params={"query": query, "per_page": 1}, timeout=10,
                )
                if r.ok and r.json().get("photos"):
                    photo = r.json()["photos"][0]
                    return {"url": photo["src"]["large"], "alt": photo.get("alt", query)}
            except Exception as e:
                print(f"    [IMG] 失败: {e}")
        return None

    def add_images(self, script, word):
        for scene in script.get("scenes", []):
            stype = scene.get("type")
            content = scene.get("content", {})
            if stype == "highlight":
                img = self.search_image(word)
                if img:
                    content["images"] = [{"url": img["url"], "alt": img["alt"], "position": "right", "size": "medium"}]
            elif stype == "example":
                eng = content.get("english", "")
                if eng:
                    keywords = " ".join(eng.split()[:5])
                    img = self.search_image(keywords)
                    if img:
                        content["images"] = [{"url": img["url"], "alt": img["alt"], "position": "center", "size": "medium"}]
        return script

    # ---- Anna per-scene 克隆 ----
    def generate_annas_audio(self, script, aigc: AIGCClient):
        """Anna 克隆每个场景音频 + 克隆合并旁白获取 COS URL"""
        audio_urls = {}  # {key: absolute_path}
        all_narrations = []  # 收集所有旁白文本用于合并克隆

        for scene in script.get("scenes", []):
            sid = scene.get("id", "")
            stype = scene.get("type", "")
            content = scene.get("content", {})

            # 1. 场景 narration
            narration = scene.get("narration", "").strip()
            if narration:
                all_narrations.append(narration)
                filename = f"narration_{sid}_{uuid.uuid4().hex[:6]}.wav"
                audio_path = self.audio_dir / filename
                print(f"    [Anna] narration: {sid} ({len(narration)}字)")
                src_path, dur = aigc.clone_voice(narration)
                shutil.copy2(src_path, str(audio_path))
                scene["audioUrl"] = f"/audio/tts/{filename}"
                scene["audioDuration"] = round(dur, 1)
                audio_urls[f"{sid}_narration"] = str(audio_path)
                print(f"    [Anna] → {filename} ({dur:.1f}s)")

            # 2. highlight: 词根 + 相关词
            if stype == "highlight" and content.get("rootAffix"):
                n_roots = len(content["rootAffix"])
                for root_item in content["rootAffix"]:
                    root_key = root_item.get("root", "unknown")
                    root_narr = root_item.get("narration", "").strip()
                    if root_narr:
                        all_narrations.append(root_narr)
                        rf = f"root_{root_key}_{uuid.uuid4().hex[:4]}.wav"
                        rp = self.audio_dir / rf
                        print(f"    [Anna] root: {root_key}")
                        src_path, dur = aigc.clone_voice(root_narr)
                        shutil.copy2(src_path, str(rp))
                        root_item["audioUrl"] = f"/audio/tts/{rf}"
                        root_item["audioDuration"] = round(dur, 1)
                        audio_urls[f"{sid}_root_{root_key}"] = str(rp)

                    for rw in root_item.get("relatedWords", []):
                        rw_word = rw.get("word", "word")
                        rw_narr = rw.get("narration", "").strip()
                        if rw_narr:
                            all_narrations.append(rw_narr)
                            rwf = f"rw_{rw_word}_{uuid.uuid4().hex[:4]}.wav"
                            rwp = self.audio_dir / rwf
                            print(f"    [Anna] rw: {rw_word}")
                            src_path, dur = aigc.clone_voice(rw_narr)
                            shutil.copy2(src_path, str(rwp))
                            rw["audioUrl"] = f"/audio/tts/{rwf}"
                            rw["audioDuration"] = round(dur, 1)
                            audio_urls[f"{sid}_rw_{rw_word}"] = str(rwp)

                # highlight 时长计算
                top_animation = (25 + (n_roots - 1) * 20 + 15 + 30) / 30.0
                intro_audio = scene.get("audioDuration", 2)
                roots_total = 0
                for ri in content["rootAffix"]:
                    roots_total += ri.get("audioDuration", 3)
                    for rj in ri.get("relatedWords", []):
                        roots_total += rj.get("audioDuration", 1.5)
                total_dur = int(top_animation + intro_audio + roots_total + 1)
                scene["durationSeconds"] = max(scene.get("durationSeconds", 0), total_dur)
                print(f"    [Anna] highlight时长: {scene['durationSeconds']}s")

            # 3. example: 英文音频
            elif stype == "example" and content.get("english"):
                eng_text = content.get("english", "").strip()
                if eng_text:
                    all_narrations.append(eng_text)
                    ef = f"example_en_{sid}_{uuid.uuid4().hex[:6]}.wav"
                    ep = self.audio_dir / ef
                    print(f"    [Anna] english: {sid}")
                    src_path, dur = aigc.clone_voice(eng_text)
                    shutil.copy2(src_path, str(ep))
                    content["englishAudioUrl"] = f"/audio/tts/{ef}"
                    content["englishAudioDuration"] = round(dur, 1)
                    audio_urls[f"{sid}_english"] = str(ep)
                    narration_dur = scene.get("audioDuration", 0)
                    total_audio = dur + narration_dur + 1.0
                    scene["durationSeconds"] = max(scene.get("durationSeconds", 0), int(total_audio))
                    print(f"    [Anna] example时长: {scene['durationSeconds']}s")

            # 4. title/vocabulary-card: ceil(audio + 0.5)
            if stype in ("title", "vocabulary-card") and scene.get("audioDuration"):
                scene["durationSeconds"] = math.ceil(scene["audioDuration"] + 0.5)
                print(f"    [Anna] {stype}时长: {scene['durationSeconds']}s")

            # 5. summary: 每要点 3s + 标题 1s + 结尾 2s
            if stype == "summary" and content.get("points"):
                points = content["points"] if isinstance(content["points"], list) else []
                n_points = len(points)
                audio_dur = scene.get("audioDuration", 0)
                per_point = max(3, audio_dur / n_points if n_points > 0 else 2)
                total = 1 + n_points * per_point + 2
                scene["durationSeconds"] = min(int(total), 30)
                print(f"    [Anna] summary时长: {scene['durationSeconds']}s")

        # 额外：克隆合并旁白 → 获取 COS URL（用于 Avatar 数字人）
        merged_text = " ".join(all_narrations)
        print(f"\n    [Anna] 克隆合并旁白获取 COS URL ({len(merged_text)}字)...")
        cos_url, merged_wav = aigc.clone_voice_merged(merged_text)
        print(f"    [Anna] COS URL: {cos_url[:60]}...")
        print(f"    [Anna] 合并音频: {Path(merged_wav).stat().st_size / 1024 / 1024:.1f}MB ({aigc._get_duration(merged_wav):.1f}s)")

        return audio_urls, str(merged_wav), cos_url

    # ---- Remotion 渲染 ----
    def render_remotion(self, script, audio_urls):
        video_id = uuid.uuid4().hex[:8]

        # 同步音频到 vocab-teaching 目录
        vt_tts = VT_PUBLIC / "audio" / "tts"
        vt_tts.mkdir(parents=True, exist_ok=True)
        for key, src_path in audio_urls.items():
            dst = vt_tts / Path(src_path).name
            shutil.copy2(src_path, str(dst))
        print(f"    [Sync] 已同步 {len(audio_urls)} 个音频到 vocab-teaching")

        # 构造配置
        config = {
            "script": script,
            "audioUrls": audio_urls,
            "outputPath": str(self.video_dir / f"avatar-vocab-{video_id}.mp4"),
        }
        config_path = self.tmp_dir / f"render-config-{video_id}.json"
        config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

        # 找 render 脚本
        render_script = SCRIPTS_DIR / "render-avatar.mjs"
        if not render_script.exists():
            render_script = VT_SCRIPTS / "render-teaching.mjs"
        if not render_script.exists():
            raise RuntimeError("找不到渲染脚本")

        print(f"    [Remotion] 渲染中...")
        result = subprocess.run(
            ["node", str(render_script), str(config_path)],
            capture_output=True, text=True, timeout=600,
            encoding="utf-8", errors="ignore",
            cwd=str(render_script.parent),
        )
        if result.returncode != 0:
            raise RuntimeError(f"Remotion 失败: {result.stderr[:500]}")

        output_path = config["outputPath"]
        if Path(output_path).exists():
            size = Path(output_path).stat().st_size / 1024 / 1024
            print(f"    [Remotion] 完成: {size:.1f}MB")
        return output_path

    # ---- FFmpeg PIP 合成 ----
    def ffmpeg_composite(self, base_video, avatar_video, output_path):
        output_path = str(output_path)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", base_video],
            capture_output=True, text=True, timeout=10
        )
        if probe.returncode == 0 and probe.stdout.strip():
            w, h = probe.stdout.strip().split("x")
            width, height = int(w), int(h)
        else:
            width, height = 1920, 1080

        # PIP: 右下角，宽度 22%，圆形
        pip_w = int(width * 0.22)
        pip_r = pip_w // 2
        pip_cx = pip_w // 2
        pip_cy = pip_w // 2
        margin = int(width * 0.03)
        pip_x = width - pip_w - margin
        pip_y = height - pip_w - margin

        # 用 geq 创建圆形蒙版，注意逗号需要反斜杠转义以免被 FFmpeg 当作 filter separator
        fc = (
            f"[1:v]scale={pip_w}:{pip_w},format=yuva420p[pip];"
            f"[pip][0:v]overlay={pip_x}:{pip_y}:"
            f"alpha=if(lte(hypot(X-{pip_cx}\\,Y-{pip_cy})\\,{pip_r})\\,1\\,0)[with_pip]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", base_video,
            "-i", avatar_video,
            "-filter_complex", fc,
            "-map", "[with_pip]",
            "-map", "0:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"[FFmpeg] stderr: {result.stderr[:500]}")
            raise RuntimeError(f"FFmpeg 失败: {result.stderr[:200]}")
        size = Path(output_path).stat().st_size / 1024 / 1024
        print(f"[OK] 保存: {output_path} ({size:.1f}MB)")
        return output_path

    # ---- 主流程 ----
    def generate_single(self, word, aigc: AIGCClient, skip_avatar=False):
        print(f"\n{'='*50}")
        print(f"[{word}] Avatar 单词教学视频生成")
        print(f"{'='*50}")

        # Step 1: LLM 生成脚本
        print("\n[1/5] LLM 生成脚本...")
        script = self.call_llm(word)

        # Step 2: 图片搜索
        print("\n[2/5] 搜索图片...")
        script = self.add_images(script, word)

        # Step 3: Anna 克隆音频 + COS URL
        print("\n[3/5] Anna 克隆音频...")
        audio_urls, merged_wav, cos_url = self.generate_annas_audio(script, aigc)

        # Step 4: Remotion 渲染
        print("\n[4/5] Remotion 渲染...")
        base_video = self.render_remotion(script, audio_urls)

        if skip_avatar:
            print(f"\n[SKIP] 跳过 Avatar")
            return base_video

        # Step 5: Avatar 数字人 + FFmpeg 合成
        print("\n[5/5] Avatar 数字人 + 合成...")
        # cos_url 是 Tencent COS URL，QingYu 服务器可以访问
        print(f"    [Anna] Avatar 音频 URL: {cos_url[:60]}...")
        avatar_video = aigc.generate_digital_human(cos_url)

        # FFmpeg 合成
        video_id = uuid.uuid4().hex[:8]
        final_path = self.video_dir / f"final-{word}-{video_id}.mp4"
        self.ffmpeg_composite(base_video, avatar_video, final_path)

        print(f"\n{'='*50}")
        print(f"[OK] {word} 完成!")
        print(f"[OK] {final_path}")
        print(f"{'='*50}")
        return str(final_path)

    def generate(self, words, aigc: AIGCClient, skip_avatar=False):
        results = []
        for word in words:
            word = word.strip()
            if not word:
                continue
            try:
                path = self.generate_single(word, aigc, skip_avatar=skip_avatar)
                results.append({"word": word, "success": True, "path": path})
            except Exception as e:
                print(f"[ERROR] {word}: {e}")
                results.append({"word": word, "success": False, "error": str(e)})
        return results


# ========== 入口 ==========
def main():
    parser = argparse.ArgumentParser(description="Avatar 单词教学视频生成器")
    parser.add_argument("-w", "--word", help="单个单词")
    parser.add_argument("-l", "--words", help="单词列表（逗号分隔）")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("--avatar-url", help="数字人模板视频 URL")
    parser.add_argument("--voice-url", help="Anna 参考音频 URL")
    parser.add_argument("--env", help=".env 文件路径")
    parser.add_argument("--skip-avatar", action="store_true", help="跳过 Avatar PIP（仅测试动画）")
    parser.add_argument("--login", nargs=2, metavar=("EMAIL", "PASSWORD"), help="登录数字人 API")
    args = parser.parse_args()

    if args.login:
        email, password = args.login
        client = AIGCClient()
        if client.login(email, password):
            print("登录成功")
        else:
            print("登录失败")
        return

    words = []
    if args.word:
        words = [args.word]
    elif args.words:
        words = [w.strip() for w in args.words.split(",")]
    else:
        parser.print_help()
        return

    aigc = AIGCClient(voice_url=args.voice_url, avatar_url=args.avatar_url)
    gen = AvatarVocabVideoGenerator(env_path=args.env)

    results = gen.generate(words, aigc, skip_avatar=args.skip_avatar)

    print(f"\n{'='*50}")
    print("生成结果:")
    for r in results:
        if r["success"]:
            print(f"  OK  {r['word']}: {r['path']}")
        else:
            print(f"  FAIL {r['word']}: {r['error']}")


if __name__ == "__main__":
    main()
