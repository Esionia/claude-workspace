@echo off
REM 单词教学视频生成器 - 依赖安装脚本
REM 运行此脚本安装所有需要的依赖

echo ============================================
echo 单词教学视频生成器 - 依赖安装
echo ============================================

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo [✓] Python 已安装

REM 安装 Python 依赖
echo.
echo [1/3] 安装 Python 依赖...
pip install edge-tts requests --quiet
if errorlevel 1 (
    echo [错误] Python 依赖安装失败
    pause
    exit /b 1
)
echo [✓] Python 依赖已安装

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到 Node.js，跳过 Remotion 安装
    echo         如需视频渲染功能，请安装 Node.js
    goto :skip_node
)

echo [2/3] 检查 Node.js 依赖...
REM 检查是否有 node_modules
if not exist "node_modules" (
    echo [注意] 未找到 node_modules，如需视频渲染功能请确保
    echo        此脚本放在包含 node_modules 的目录下运行
)

:skip_node

REM 创建输出目录
echo [3/3] 创建输出目录...
if not exist "public" mkdir public
if not exist "public\videos" mkdir public\videos
if not exist "public\audio" mkdir public\audio
if not exist "public\audio\tts" mkdir public\audio\tts
if not exist "tmp" mkdir tmp
echo [✓] 目录已创建

echo.
echo ============================================
echo 安装完成！
echo ============================================
echo.
echo 下一步：
echo 1. 复制 .env 文件到当前目录（包含 API keys）
echo 2. 运行: python generate_vocab_video.py --word creativity
echo.
pause
