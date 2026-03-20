#!/usr/bin/env python3
"""
语音克隆 + 数字人合成客户端

功能:
1. 语音克隆 - 将文本转换为克隆语音
2. 数字人合成 - 生成数字人视频（自动包含语音克隆）

使用方式:
    # 1. 登录获取 token (首次使用)
    python voice_clone.py login <email> <password>

    # 或者手动设置 token
    python voice_clone.py set-token <your_token>

    # 2. 克隆语音 (仅音频)
    python voice_clone.py clone "要转换的文本" "参考音频OSS_URL" --speed 1.0 --output audio.wav

    # 3. 数字人合成 (视频)
    python voice_clone.py digital-human "要转换的文本" "参考音频OSS_URL" "数字人视频URL" --output video.mp4

    # 4. 查看数字人列表
    python voice_clone.py list-digital-humans

    # 5. 查看帮助
    python voice_clone.py --help
"""

import argparse
import json
import os
import sys
import time
import requests
from pathlib import Path

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
API_BASE_URL = "https://dapi.qingyu.club/api"
TOKEN_FILE = os.path.expanduser("~/.aigc_voice_token")
CREDENTIALS_FILE = os.path.expanduser("~/.aigc_voice_credentials")

# 从配置文件加载默认配置
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.env')
DEFAULT_VOICE_URL = None
DEFAULT_DIGITAL_HUMAN_URL = None
DEFAULT_EMAIL = None
DEFAULT_PASSWORD = None

def _load_config():
    """从 config.env 加载默认配置"""
    global DEFAULT_VOICE_URL, DEFAULT_DIGITAL_HUMAN_URL, DEFAULT_EMAIL, DEFAULT_PASSWORD
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip()
                        if key == 'VOICE_URL' and value:
                            DEFAULT_VOICE_URL = value
                        elif key == 'DIGITAL_HUMAN_URL' and value:
                            DEFAULT_DIGITAL_HUMAN_URL = value
                        elif key == 'EMAIL' and value:
                            DEFAULT_EMAIL = value
                        elif key == 'PASSWORD' and value:
                            DEFAULT_PASSWORD = value
        except Exception as e:
            print(f"⚠️ 配置文件加载失败: {e}")

_load_config()


class VoiceCloneClient:
    def __init__(self, token=None):
        self.base_url = API_BASE_URL
        self.token = token or self._load_token()
        # 优先使用配置文件中的账号密码
        self._email = DEFAULT_EMAIL
        self._password = DEFAULT_PASSWORD
        # 如果配置文件没有，则尝试从凭据文件加载
        if not self._email or not self._password:
            self._load_credentials()

    def _load_token(self):
        """从文件加载 token"""
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                return f.read().strip()
        return None

    def _save_token(self, token):
        """保存 token 到文件"""
        with open(TOKEN_FILE, 'w') as f:
            f.write(token)
        print(f"✓ Token 已保存到 {TOKEN_FILE}")

    def _load_credentials(self):
        """加载保存的账号密码"""
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, 'r') as f:
                    data = json.load(f)
                    self._email = data.get('email')
                    self._password = data.get('password')
            except:
                pass

    def _save_credentials(self, email, password):
        """保存账号密码（用于自动重新登录）"""
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump({'email': email, 'password': password}, f)
        print(f"✓ 账号已保存到 {CREDENTIALS_FILE} (仅用于 token 失效时自动重新登录)")

    def _check_token_valid(self):
        """检查 token 是否有效"""
        if not self.token:
            return False
        url = f"{self.base_url}/users/profile"
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            return response.status_code == 200
        except:
            return False

    def _ensure_token_valid(self):
        """确保 token 有效，失效则尝试自动重新登录"""
        if self._check_token_valid():
            return True

        # Token 失效，尝试自动重新登录
        if self._email and self._password:
            print("⚠️ Token 已失效，尝试自动重新登录...")
            if self.login(self._email, self._password):
                return True
        return False

    def _get_headers(self):
        """获取请求头"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def login(self, email, password):
        """登录获取 token"""
        url = f"{self.base_url}/users/login"
        data = {"email": email, "password": password}

        print(f"正在登录...")
        response = requests.post(url, json=data, verify=False)
        result = response.json()

        if result.get('success'):
            token = result['data']['token']
            self._save_token(token)
            self.token = token
            # 保存凭据以便token失效时自动重新登录
            self._save_credentials(email, password)
            print(f"✓ 登录成功!")
            return True
        else:
            print(f"✗ 登录失败: {result.get('message', '未知错误')}")
            return False

    def set_token(self, token):
        """手动设置 token"""
        # 验证 token 是否有效
        url = f"{self.base_url}/users/profile"
        headers = {'Authorization': f'Bearer {token}'}

        try:
            response = requests.get(url, headers=headers, verify=False)
            if response.status_code == 200:
                self._save_token(token)
                self.token = token
                print(f"✓ Token 验证成功并已保存!")
                return True
            else:
                print(f"✗ Token 无效")
                return False
        except Exception as e:
            print(f"✗ Token 验证失败: {e}")
            return False

    def clone_voice(self, text, reference_audio_url, speed=1.0):
        """克隆语音 (V2 异步任务)"""
        # 确保token有效，失效则尝试自动重新登录
        if not self._ensure_token_valid():
            print("✗ 无法获取有效的 token，请重新登录:")
            print("   登录: python voice_clone.py login <email> <password>")
            print("   或设置 token: python voice_clone.py set-token <token>")
            return None

        url = f"{self.base_url}/voice-clone-v2/task"
        headers = self._get_headers()

        payload = {
            "text": text,
            "speaker_audio_url": reference_audio_url,
            "speed": speed
        }

        print(f"提交语音克隆任务...")
        print(f"  文本: {text[:50]}..." if len(text) > 50 else f"  文本: {text}")
        print(f"  参考音频: {reference_audio_url}")
        print(f"  语速: {speed}")

        try:
            response = requests.post(url, json=payload, headers=headers, verify=False, timeout=30)
            result = response.json()

            # 兼容两种响应格式: {"task_id": "..."} 或 {"success": true, "data": {"task_id": "..."}}
            task_id = result.get('task_id') or (result.get('data') or {}).get('task_id')

            if task_id:
                print(f"✓ 任务提交成功! Task ID: {task_id}")

                # 轮询任务状态
                return self._poll_voice_task(task_id)
            else:
                print(f"✗ 任务提交失败: {result.get('message', '未知错误')}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ 请求失败: {e}")
            return None

    def _poll_voice_task(self, task_id, timeout=300, interval=3):
        """轮询语音克隆任务直到完成"""
        url = f"{self.base_url}/voice-clone-v2/task"
        headers = self._get_headers()

        print(f"等待语音克隆完成... (超时 {timeout}秒)")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    url,
                    params={"task_id": task_id},
                    headers=headers,
                    verify=False,
                    timeout=30
                )
                result = response.json()

                if result.get('success'):
                    data = result['data']
                else:
                    data = result

                # 兼容两种字段名: status 或 state
                status = data.get('status') or data.get('state')

                if status == 'completed' or status == 'SUCCESS':
                    audio_url = data.get('audio_url')
                    print(f"✓ 语音克隆完成!")
                    print(f"  音频 URL: {audio_url}")
                    return audio_url
                elif status == 'failed' or status == 'FAILED':
                    error = data.get('error') or data.get('error_message', '未知错误')
                    print(f"✗ 任务失败: {error}")
                    return None
                else:
                    print(f"  状态: {status}... 等待中")

            except requests.exceptions.RequestException as e:
                print(f"  请求错误: {e}")

            time.sleep(interval)

        print(f"✗ 任务超时 ({timeout}秒)")
        return None

    # 默认数字人模板列表（从原软件中提取）
    DEFAULT_DIGITAL_HUMANS = [
        {"name": "示例1-绿幕", "url": "https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1764939140639_f6tv14.mp4"},
        {"name": "示例2-夜间", "url": "https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1764939161086_0bf1jf.mp4"},
        {"name": "示例3-百天", "url": "https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1764939180646_jzj1nv.mp4"},
        {"name": "示例4-白天", "url": "https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1764939209916_m5tyk1.mp4"},
        {"name": "中年男士1", "url": "https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1767510587441_uhewip.mp4"},
        {"name": "青年男1", "url": "https://static-1251729840.cos.ap-guangzhou.myqcloud.com/digital_human/2/video/1767514386275_4awehx.mp4"},
    ]

    def list_digital_humans(self):
        """获取数字人列表"""
        print("\n" + "=" * 60)
        print("可用数字人模板列表")
        print("=" * 60 + "\n")

        print(f"{'序号':<5} {'名称':<20} {'视频URL':<45}")
        print("-" * 70)
        for i, dh in enumerate(self.DEFAULT_DIGITAL_HUMANS, 1):
            url_short = dh["url"][:42] + "..." if len(dh["url"]) > 45 else dh["url"]
            print(f"{i:<5} {dh['name']:<20} {url_short:<45}")

        print("\n" + "=" * 60)
        print("使用示例")
        print("=" * 60)
        print(f"\n# 使用示例1-绿幕 合成数字人视频:")
        first_url = self.DEFAULT_DIGITAL_HUMANS[0]["url"]
        print(f'python voice_clone.py synthesize "今天天气真好" "参考音频URL" "{first_url}" -o video.mp4')
        print(f"\n# 或者使用其他数字人:")
        print(f'python voice_clone.py synthesize "你好" "参考音频URL" "数字人视频URL" -o output.mp4')

        return self.DEFAULT_DIGITAL_HUMANS

    def generate_digital_human(self, audio_url, avatar_video_url, model_version='V2'):
        """生成数字人视频"""
        # 确保token有效，失效则尝试自动重新登录
        if not self._ensure_token_valid():
            print("✗ 无法获取有效的 token，请重新登录:")
            print("   登录: python voice_clone.py login <email> <password>")
            print("   或设置 token: python voice_clone.py set-token <token>")
            return None

        url = f"{self.base_url}/tasks/task"
        headers = self._get_headers()

        payload = {
            "audio_url": audio_url,
            "video_url": avatar_video_url,
            "model_version": model_version
        }

        print(f"提交数字人生成任务...")
        print(f"  驱动音频: {audio_url}")
        print(f"  数字人模板: {avatar_video_url}")
        print(f"  模型版本: {model_version}")

        try:
            response = requests.post(url, json=payload, headers=headers, verify=False, timeout=30)
            result = response.json()

            if result.get('success'):
                task_data = result.get('data', {})
                task_id = task_data.get('taskId')
                print(f"✓ 任务提交成功! Task ID: {task_id}")

                # 轮询任务状态
                return self._poll_digital_human_task(task_id)
            else:
                print(f"✗ 任务提交失败: {result.get('message', '未知错误')}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ 请求失败: {e}")
            return None

    def _poll_digital_human_task(self, task_id, timeout=600, interval=3):
        """轮询数字人生成任务直到完成"""
        url = f"{self.base_url}/tasks/task/{task_id}/status"
        headers = self._get_headers()

        print(f"等待数字人生成完成... (超时 {timeout}秒)")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, headers=headers, verify=False, timeout=30)
                result = response.json()

                if result.get('success'):
                    data = result.get('data', {})
                    status = data.get('status')

                    if status == 'completed':
                        # 获取结果视频
                        result_data = data.get('result', {})
                        video_url = result_data.get('output_file')
                        print(f"✓ 数字人生成完成!")
                        print(f"  视频 URL: {video_url}")
                        return video_url
                    elif status == 'failed':
                        error = data.get('error', '未知错误')
                        print(f"✗ 任务失败: {error}")
                        return None
                    else:
                        print(f"  状态: {status}... 等待中")
                else:
                    print(f"✗ 查询失败: {result.get('message', '未知错误')}")

            except requests.exceptions.RequestException as e:
                print(f"  请求错误: {e}")

            time.sleep(interval)

        print(f"✗ 任务超时 ({timeout}秒)")
        return None

    def digital_human(self, text, reference_audio_url, avatar_video_url, speed=1.0, output_path=None):
        """一键数字人合成（自动完成语音克隆+视频生成）"""
        # 确保token有效，失效则尝试自动重新登录
        if not self._ensure_token_valid():
            print("✗ 无法获取有效的 token，请重新登录")
            return None

        print(f"\n{'='*50}")
        print(f"开始数字人合成流程")
        print(f"{'='*50}\n")

        # 步骤1: 克隆语音
        print(f"\n[步骤 1/2] 克隆语音...")
        audio_url = self.clone_voice(text, reference_audio_url, speed)
        if not audio_url:
            print("✗ 语音克隆失败，无法继续")
            return None

        # 步骤2: 生成数字人视频
        print(f"\n[步骤 2/2] 生成数字人视频...")
        video_url = self.generate_digital_human(audio_url, avatar_video_url)
        if not video_url:
            print("✗ 数字人视频生成失败")
            return None

        # 下载视频（如果指定了输出路径）
        if output_path:
            print(f"\n下载视频到 {output_path}...")
            success = self.download_file(video_url, output_path)
            if success:
                print(f"\n{'='*50}")
                print(f"✓ 数字人合成完成!")
                print(f"  视频文件: {output_path}")
                print(f"{'='*50}")
                return output_path
            return None

        print(f"\n{'='*50}")
        print(f"✓ 数字人合成完成!")
        print(f"  视频 URL: {video_url}")
        print(f"{'='*50}")
        return video_url

    def download_audio(self, audio_url, output_path):
        """下载音频文件"""
        print(f"下载音频到 {output_path}...")
        return self.download_file(audio_url, output_path)

    def download_file(self, file_url, output_path):
        """下载文件"""
        try:
            response = requests.get(file_url, verify=False, timeout=120)
            response.raise_for_status()

            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)

            # 获取文件大小
            size = os.path.getsize(output_path)
            size_kb = size / 1024
            size_mb = size_kb / 1024

            if size_mb >= 1:
                print(f"✓ 下载完成: {output_path} ({size_mb:.2f} MB)")
            else:
                print(f"✓ 下载完成: {output_path} ({size_kb:.2f} KB)")
            return True
        except Exception as e:
            print(f"✗ 下载失败: {e}")
            return False


def main():
    # 禁用 SSL 警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    parser = argparse.ArgumentParser(
        description='语音克隆 + 数字人合成客户端',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 登录
  python voice_clone.py login your@email.com password

  # 设置 token
  python voice_clone.py set-token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

  # 克隆语音（仅音频）
  python voice_clone.py clone "你好世界" "https://your-audio-url.wav" --output hello.wav
  python voice_clone.py clone "测试文本" "https://..." --speed 1.2 -o result.wav

  # 查看数字人列表
  python voice_clone.py list-digital-humans

  # 数字人合成（视频）
  python voice_clone.py digital-human "要转换的文本" "参考音频URL" "数字人视频URL" --output video.mp4

  # 一键数字人合成（自动语音克隆+视频生成）
  python voice_clone.py synthesize "要转换的文本" "参考音频OSS_URL" "数字人视频URL" --output video.mp4

  # 下载文件
  python voice_clone.py download "https://..." output.mp4
        """
    )
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # login
    login_parser = subparsers.add_parser('login', help='登录获取 token')
    login_parser.add_argument('email', help='邮箱')
    login_parser.add_argument('password', help='密码')

    # set-token
    token_parser = subparsers.add_parser('set-token', help='手动设置 token')
    token_parser.add_argument('token', help='API token')

    # clone - 语音克隆
    clone_parser = subparsers.add_parser('clone', help='克隆语音 (仅音频)')
    clone_parser.add_argument('text', help='要转换的文本')
    clone_parser.add_argument('reference_audio', help='参考音频 URL (OSS URL)')
    clone_parser.add_argument('--speed', type=float, default=1.0, help='语速 (默认 1.0, 范围 0.5-2.0)')
    clone_parser.add_argument('--output', '-o', help='输出文件路径 (可选)')

    # list-digital-humans
    list_parser = subparsers.add_parser('list-digital-humans', help='查看数字人列表')
    list_parser.add_argument('--page', type=int, default=1, help='页码')
    list_parser.add_argument('--page-size', type=int, default=20, help='每页数量')

    # digital-human - 数字人合成（已有音频）
    dh_parser = subparsers.add_parser('digital-human', help='数字人合成 (需要已有音频URL)')
    dh_parser.add_argument('audio_url', help='驱动音频 URL (OSS URL)')
    dh_parser.add_argument('avatar_video', help='数字人视频模板 URL (OSS URL)')
    dh_parser.add_argument('--model', default='V2', help='模型版本 (默认 V2)')
    dh_parser.add_argument('--output', '-o', help='输出文件路径 (可选)')

    # synthesize - 一键合成
    synthesize_parser = subparsers.add_parser('synthesize', help='一键数字人合成 (自动语音克隆+视频生成)')
    synthesize_parser.add_argument('text', help='要转换的文本')
    synthesize_parser.add_argument('reference_audio', nargs='?', default=None, help='参考音频 URL (可选，使用 config.env 中的默认值)')
    synthesize_parser.add_argument('avatar_video', nargs='?', default=None, help='数字人视频模板 URL (可选，使用 config.env 中的默认值)')
    synthesize_parser.add_argument('--speed', type=float, default=1.0, help='语速 (默认 1.0)')
    synthesize_parser.add_argument('--output', '-o', help='输出文件路径 (可选)')

    # download
    download_parser = subparsers.add_parser('download', help='下载文件')
    download_parser.add_argument('url', help='文件 URL')
    download_parser.add_argument('output', help='输出文件路径')

    args = parser.parse_args()

    client = VoiceCloneClient()

    if args.command == 'login':
        client.login(args.email, args.password)

    elif args.command == 'set-token':
        client.set_token(args.token)

    elif args.command == 'clone':
        audio_url = client.clone_voice(args.text, args.reference_audio, args.speed)
        if audio_url and args.output:
            client.download_audio(audio_url, args.output)

    elif args.command == 'list-digital-humans':
        client.list_digital_humans()

    elif args.command == 'digital-human':
        video_url = client.generate_digital_human(args.audio_url, args.avatar_video, args.model)
        if video_url and args.output:
            client.download_file(video_url, args.output)

    elif args.command == 'synthesize':
        # 使用配置文件中的默认值（如果参数为空）
        reference_audio = args.reference_audio or DEFAULT_VOICE_URL
        avatar_video = args.avatar_video or DEFAULT_DIGITAL_HUMAN_URL

        if not reference_audio:
            print("✗ 缺少参考音频 URL")
            print("   请在 config.env 中配置 VOICE_URL，或在命令行传入")
            return
        if not avatar_video:
            print("✗ 缺少数字人视频 URL")
            print("   请在 config.env 中配置 DIGITAL_HUMAN_URL，或在命令行传入")
            return

        client.digital_human(args.text, reference_audio, avatar_video, args.speed, args.output)

    elif args.command == 'download':
        client.download_file(args.url, args.output)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
