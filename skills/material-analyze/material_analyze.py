#!/usr/bin/env python3
"""
素材分析 + IP大脑工具

功能:
1. 视频内容分析 - 提取关键帧并用AI分析内容
2. 图片内容分析 - 用Vision模型分析图片
3. IP大脑 - 抖音链接分析，获取博主视频列表和内容

使用方式:
    # 1. 分析视频内容
    python material_analyze.py video "视频文件路径" --fps 2

    # 2. 分析图片内容
    python material_analyze.py image "图片文件路径"

    # 3. IP大脑 - 分析抖音博主
    python material_analyze.py ip-brain "抖音链接" --deep

    # 4. 查看IP档案列表
    python material_analyze.py list-archives

    # 5. 查看帮助
    python material_analyze.py --help
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import requests
from pathlib import Path

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import sys
import io
# 修复 Windows GBK 控制台编码问题
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except Exception:
    pass

# ============ 豆包API配置 (素材分析) ============
API_KEY = ''
BASE_URL = 'https://ark.cn-beijing.volces.com/api/v3'
VISION_MODEL = 'doubao-seed-1-6-250015'
FFMPEG_PATH = os.environ.get('FFMPEG_PATH', 'ffmpeg')

# ============ 视频解析API配置 (IP大脑) ============
VIDEO_PARSER_BASE_URL = 'https://sapi.qingyu.club/vp'
VIDEO_PARSER_TOKEN = 's1234567'

# 支持的平台
SUPPORTED_PLATFORMS = {
    'douyin': ['douyin.com', 'v.douyin.com', 'tiktok.com'],
    'kuaishou': ['kuaishou.com'],
    'xiaohongshu': ['xiaohongshu.com'],
    'weibo': ['weibo.com'],
    'bilibili': ['bilibili.com', 'b23.tv'],
    'youtube': ['youtube.com', 'youtu.be'],
    'local': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
}

# 配置文件
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.env')


def load_config():
    """从配置文件加载配置"""
    global API_KEY, BASE_URL, VISION_MODEL
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip()
                        if key == 'API_KEY' and value:
                            API_KEY = value
                        elif key == 'BASE_URL' and value:
                            BASE_URL = value
                        elif key == 'VISION_MODEL' and value:
                            VISION_MODEL = value
        except Exception as e:
            print(f"⚠️ 配置文件加载失败: {e}")


# ============ 素材分析功能 ============

def extract_frames(video_path, fps=0.5, output_dir=None):
    """提取视频关键帧"""
    if not os.path.exists(video_path):
        return None, f"视频文件不存在: {video_path}"

    if output_dir is None:
        output_dir = tempfile.mkdtemp()

    output_pattern = os.path.join(output_dir, 'frame_%04d.jpg')

    cmd = [
        FFMPEG_PATH,
        '-i', video_path,
        '-vf', f'fps={fps}',
        '-q:v', '2',
        '-y',
        output_pattern
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return None, f"FFmpeg错误: {result.stderr}"

        frames = sorted([f for f in os.listdir(output_dir) if f.endswith('.jpg')])
        if not frames:
            return None, "未能提取到帧"

        frame_paths = [os.path.join(output_dir, f) for f in frames]
        return frame_paths, None

    except subprocess.TimeoutExpired:
        return None, "视频处理超时"
    except Exception as e:
        return None, f"处理失败: {str(e)}"


def encode_image(image_path):
    """将图片编码为base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def analyze_with_doubao(image_path, prompt=None):
    """用豆包Vision模型分析图片"""
    if not API_KEY:
        return None, "未设置API_KEY，请在config.env中配置"

    if prompt is None:
        prompt = """分析这张图片。请按以下JSON格式返回：
{
  "description": "50-100字的内容描述"
}
要求：
1. description是完整流畅的描述（60-120字）
2. 只返回JSON，不要markdown代码块
3. 不要添加任何解释

立即返回JSON："""

    base64_image = encode_image(image_path)

    url = f"{BASE_URL}/chat/completions"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']

            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            return json.loads(content.strip()), None
        else:
            return None, f"API错误: {result}"

    except json.JSONDecodeError:
        return {"description": content[:200]}, None
    except Exception as e:
        return None, f"分析失败: {str(e)}"


def analyze_video(video_path, fps=0.5):
    """分析视频内容"""
    print(f"📹 正在提取视频帧 (FPS={fps})...")

    frames, error = extract_frames(video_path, fps)
    if error:
        return None, error

    print(f"✓ 提取了 {len(frames)} 帧")

    descriptions = []
    for i, frame in enumerate(frames):
        print(f"  分析第 {i+1}/{len(frames)} 帧...")
        result, error = analyze_with_doubao(frame)
        if result and 'description' in result:
            descriptions.append(result['description'])
        elif error:
            print(f"  ⚠️ 帧 {i+1} 分析失败: {error}")

    if not descriptions:
        return None, "所有帧分析失败"

    final_description = " | ".join(descriptions)

    return {
        "description": final_description,
        "frame_count": len(frames),
        "frames": descriptions
    }, None


def analyze_image(image_path):
    """分析单张图片"""
    print("🖼️ 正在分析图片...")
    result, error = analyze_with_doubao(image_path)
    if error:
        return None, error
    return result, None


# ============ IP大脑功能 ============

def extract_and_convert_douyin_url(url):
    """转换抖音短链接为PC端链接"""
    try:
        # 使用浏览器User-Agent来获取正确的重定向
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, allow_redirects=True, headers=headers, timeout=10)
        final_url = response.url

        # 清理URL，移除末尾的斜杠等
        final_url = final_url.rstrip('/')

        print(f"  原始链接: {url}")
        print(f"  转换后: {final_url}")

        # 如果是用户主页链接，提取用户ID
        if 'www.douyin.com/user/' in final_url:
            return final_url

        return final_url
    except Exception as e:
        print(f"  ⚠️ 链接转换失败: {e}")
        return url


def fetch_douyin_user_videos(homepage_url, deep=False):
    """获取抖音用户视频列表"""
    print("🔍 正在获取抖音用户信息...")
    print(f"  原始链接: {homepage_url}")

    # 清理URL
    processed_url = homepage_url.strip().rstrip('/')

    # 检查URL格式
    if 'v.douyin.com' in processed_url:
        print("  ⚠️ 检测到短链接...")
        # 尝试本地转换（可能失败）
        converted = extract_and_convert_douyin_url(processed_url)
        if 'www.douyin.com/user/' in converted:
            processed_url = converted
            print(f"  ✓ 转换成功: {processed_url}")
        else:
            print("  ⚠️ 短链接转换失败，请使用完整的用户主页链接")
            print("  💡 请从抖音APP复制完整的个人主页链接")
            return None, "请提供完整的抖音用户主页链接（不是短链接）"

    # 调用API获取视频列表
    url = f"{VIDEO_PARSER_BASE_URL}/api/douyin/user-videos"
    payload = {
        "token": VIDEO_PARSER_TOKEN,
        "homepage_url": processed_url
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        result = response.json()

        # 检查API返回状态 (支持多种格式)
        is_success = (
            result.get('success') == True or
            result.get('status') == 'success' or
            result.get('code') == 0
        )

        if is_success:
            data = result.get('data', {})
            # 使用 aweme_list（与软件一致）
            video_list = data.get('aweme_list', []) or data.get('list', []) or data.get('video_list', [])

            if not video_list:
                return None, "该博主暂无视频"

            # 提取博主信息
            author_info = video_list[0] if video_list else {}
            author_name = author_info.get('nickname') or author_info.get('author', {}).get('nickname', '未知博主')

            print(f"✓ 获取到 {len(video_list)} 个视频")
            print(f"  博主: {author_name}")

            # 深度分析 (Top 3)
            if deep:
                print(f"\n🧠 进行深度分析 (Top 3)...")

                # 先过滤掉时长大于3分钟(180秒)的视频（与软件一致）
                filtered_videos = []
                for v in video_list:
                    duration = v.get('duration', 0)
                    if duration > 0 and duration <= 180000:  # 毫秒
                        filtered_videos.append(v)

                print(f"  过滤后视频数: {len(filtered_videos)}/{len(video_list)}")

                # 按热度排序
                sorted_videos = sorted(filtered_videos, key=lambda x: (x.get('digg_count', 0) + x.get('comment_count', 0)), reverse=True)
                top3 = sorted_videos[:3]

                deep_analysis = []
                for i, video in enumerate(top3):
                    print(f"  分析第 {i+1}/3 个热门视频...")
                    video_url = video.get('share_url') or video.get('video_url') or video.get('play_addr', {}).get('url_list', [None])[0]

                    if video_url:
                        # 解析视频内容
                        parse_result = parse_video_content(video_url)
                        if parse_result:
                            deep_analysis.append({
                                'title': video.get('title') or video.get('desc', ''),
                                'content': parse_result,
                                'stats': {
                                    '点赞': video.get('digg_count', 0),
                                    '评论': video.get('comment_count', 0)
                                }
                            })

                return {
                    "author_name": author_name,
                    "video_count": len(video_list),
                    "deep_analysis": deep_analysis
                }, None

            return {
                "author_name": author_name,
                "video_count": len(video_list),
                "videos": [
                    {
                        "title": v.get('title', v.get('desc', ''))[:50],
                        "digg_count": v.get('digg_count', 0),
                        "comment_count": v.get('comment_count', 0)
                    }
                    for v in video_list[:10]  # 只返回前10个
                ]
            }, None
        else:
            return None, result.get('message', '获取视频列表失败')

    except Exception as e:
        return None, f"请求失败: {str(e)}"


def parse_video_content(video_url):
    """解析单个视频内容"""
    print(f"  🔗 正在解析: {video_url[:50]}...")
    url = f"{VIDEO_PARSER_BASE_URL}/api/parse"
    payload = {
        "token": VIDEO_PARSER_TOKEN,
        "videoUrl": video_url
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        print(f"    API响应: {result}")

        # 检查API返回状态 (支持多种格式)
        is_success = (
            result.get('success') == True or
            result.get('status') == 'success' or
            result.get('code') == 0
        )

        if is_success:
            # 提取文案内容 (与软件一致，从text字段提取)
            # 优先使用 extractedContent, 然后是 text, 最后是 content
            data = result.get('data', {})
            content = (
                data.get('extractedContent') or
                data.get('text') or
                data.get('content') or
                result.get('text') or
                ''
            )

            if content:
                print(f"  ✓ 解析成功: {content[:50]}...")
                return content
            else:
                print(f"  ⚠️ 未能提取到文案内容")
                return None
        else:
            print(f"  ⚠️ 解析失败: {result.get('message', '未知错误')}")
            return None
    except Exception as e:
        print(f"  ⚠️ 请求失败: {str(e)}")
        return None


def detect_platform(url):
    """自动识别视频平台"""
    url_lower = url.lower()
    for platform, patterns in SUPPORTED_PLATFORMS.items():
        if platform == 'local':
            continue
        for pattern in patterns:
            if pattern in url_lower:
                return platform
    # 检查是否是本地文件
    for ext in SUPPORTED_PLATFORMS['local']:
        if url_lower.endswith(ext):
            return 'local'
    return 'unknown'


def parse_video(url):
    """通用视频解析 - 支持多平台"""
    platform = detect_platform(url)

    print(f"\n🎯 检测到平台: {platform}")
    print(f"  链接: {url[:60]}...")

    if platform == 'unknown':
        return None, "无法识别的平台，请检查链接是否正确"

    if platform == 'douyin':
        # 抖音 - 可以获取用户视频列表
        return fetch_douyin_user_videos(url, deep=False)

    # 其他平台 - 解析单个视频
    return parse_single_video(url, platform)


def parse_single_video(url, platform):
    """解析单个视频"""
    print(f"\n📊 解析 {platform} 视频...")

    content = parse_video_content(url)
    if not content:
        return None, "视频解析失败"

    return {
        "platform": platform,
        "url": url,
        "content": content,
        "type": "single_video"
    }, None


def main():
    load_config()

    parser = argparse.ArgumentParser(
        description='素材分析 + IP大脑工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析视频内容
  python material_analyze.py video /path/to/video.mp4 --fps 0.5

  # 分析图片
  python material_analyze.py image /path/to/image.jpg

  # IP大脑 - 分析抖音博主
  python material_analyze.py ip-brain "抖音链接"

  # IP大脑 - 深度分析
  python material_analyze.py ip-brain "抖音链接" --deep

  # 解析任意平台视频
  python material_analyze.py parse "视频链接"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # video
    video_parser = subparsers.add_parser('video', help='分析视频内容')
    video_parser.add_argument('path', help='视频文件路径')
    video_parser.add_argument('--fps', type=float, default=0.5, help='每秒提取帧数 (默认 0.5)')
    video_parser.add_argument('--output', '-o', help='输出JSON文件路径 (可选)')

    # image
    image_parser = subparsers.add_parser('image', help='分析图片内容')
    image_parser.add_argument('path', help='图片文件路径')
    image_parser.add_argument('--output', '-o', help='输出JSON文件路径 (可选)')

    # ip-brain
    ip_parser = subparsers.add_parser('ip-brain', help='IP大脑 - 分析抖音博主')
    ip_parser.add_argument('url', help='抖音主页链接')
    ip_parser.add_argument('--deep', action='store_true', help='深度分析 (Top 3热门视频)')
    ip_parser.add_argument('--output', '-o', help='输出JSON文件路径 (可选)')

    # parse - 通用视频解析
    parse_parser = subparsers.add_parser('parse', help='解析任意平台视频链接')
    parse_parser.add_argument('url', help='视频链接 (抖音/快手/小红书/B站/微博等)')
    parse_parser.add_argument('--output', '-o', help='输出JSON文件路径 (可选)')

    # list-archives (本地模拟)
    list_parser = subparsers.add_parser('list-archives', help='查看IP档案列表')

    args = parser.parse_args()

    if args.command == 'video':
        result, error = analyze_video(args.path, args.fps)
        if error:
            print(f"✗ 分析失败: {error}")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("分析结果")
        print("=" * 60)
        print(f"\n描述: {result['description']}")
        print(f"\n帧数: {result['frame_count']}")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n✓ 结果已保存到: {args.output}")

    elif args.command == 'image':
        result, error = analyze_image(args.path)
        if error:
            print(f"✗ 分析失败: {error}")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("分析结果")
        print("=" * 60)
        print(f"\n描述: {result['description']}")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n✓ 结果已保存到: {args.output}")

    elif args.command == 'ip-brain':
        result, error = fetch_douyin_user_videos(args.url, args.deep)
        if error:
            print(f"✗ 分析失败: {error}")
            sys.exit(1)

        print("\n" + "=" * 60)
        print(f"IP档案: {result['author_name']}")
        print("=" * 60)
        print(f"\n视频数量: {result['video_count']}")

        if 'deep_analysis' in result:
            print(f"\n深度分析 (Top 3):")
            for i, item in enumerate(result['deep_analysis'], 1):
                print(f"\n  [{i}] {item['title'][:50]}")
                print(f"      热度: 赞 {item['stats']['点赞']}, 评论 {item['stats']['评论']}")
                print(f"      内容: {item['content'][:100]}...")

        if 'videos' in result:
            print(f"\n热门视频:")
            for i, v in enumerate(result['videos'][:5], 1):
                print(f"  [{i}] {v['title'][:40]}")
                print(f"      赞: {v['digg_count']}, 评论: {v['comment_count']}")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n✓ 结果已保存到: {args.output}")

    elif args.command == 'parse':
        result, error = parse_video(args.url)
        if error:
            print(f"✗ 解析失败: {error}")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("解析结果")
        print("=" * 60)

        if 'author_name' in result:
            # 抖音用户
            print(f"\n博主: {result['author_name']}")
            print(f"视频数: {result['video_count']}")
            if 'videos' in result:
                print(f"\n热门视频:")
                for i, v in enumerate(result['videos'][:5], 1):
                    print(f"  [{i}] {v['title'][:40]}")
        elif 'content' in result:
            # 单视频
            print(f"\n平台: {result.get('platform', 'unknown')}")
            print(f"\n内容:")
            print(result['content'][:500])

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n✓ 结果已保存到: {args.output}")

    elif args.command == 'list-archives':
        print("📁 IP档案列表")
        print("\n提示: IP档案存储在软件数据库中")
        print("      请在软件中查看已创建的档案")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
