#!/usr/bin/env node
/**
 * 教学视频渲染脚本
 * 通过命令行参数接收渲染配置，调用 Remotion 渲染 TeachingVideo
 */

import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs/promises";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// skill 独立的根目录
const projectRoot = __dirname;
// 使用 scripts/public 作为 publicDir（包含 bgm 等资源）
const publicDir = path.join(projectRoot, "public");

// 修复：在渲染前将新的 tts 文件复制到 scripts/public（Remotion 需要）
async function ensureAudioFiles(audioUrls) {
  const skillPublicDir = path.join(projectRoot, "..", "public");
  const scriptsPublicDir = path.join(projectRoot, "public");

  try {
    // 复制 tts 目录（新增的音频文件）
    const ttsSrc = path.join(skillPublicDir, "audio", "tts");
    const ttsDest = path.join(scriptsPublicDir, "audio", "tts");
    await fs.mkdir(ttsDest, { recursive: true });
    await fs.cp(ttsSrc, ttsDest, { recursive: true });
    console.error(`[DEBUG] 已同步 tts 目录到 scripts/public`);
  } catch (err) {
    console.error(`[DEBUG] 同步文件时出错: ${err.message}`);
  }
}

async function main() {
  const configPath = process.argv[2];
  if (!configPath) {
    console.error(JSON.stringify({ error: "缺少配置文件路径" }));
    process.exit(1);
  }

  try {
    console.error(`[DEBUG] 读取配置: ${configPath}`);
    const configContent = await fs.readFile(configPath, "utf-8");
    const config = JSON.parse(configContent);
    const { script, audioUrls, outputPath } = config;

    if (!script || !script.scenes || !outputPath) {
      console.error(JSON.stringify({ error: "配置文件缺少必要字段: script, outputPath" }));
      process.exit(1);
    }

    // 修复：在渲染前复制音频文件
    await ensureAudioFiles(audioUrls);

    const entryPoint = path.join(projectRoot, "components", "remotion", "RemotionRoot.tsx");

    console.error(`[DEBUG] 开始打包 Remotion 组件...`);
    const bundleLocation = await bundle({
      entryPoint,
      webpackOverride: (config) => ({
        ...config,
        resolve: {
          ...config.resolve,
          alias: {
            ...config.resolve?.alias,
            "@": projectRoot,
          },
        },
      }),
      publicDir,
    });
    console.error(`[DEBUG] 打包完成: ${bundleLocation}`);

    const relativeAudioUrls = {};
    if (audioUrls) {
      for (const [sceneId, absolutePath] of Object.entries(audioUrls)) {
        if (typeof absolutePath === "string") {
          const normalizedPath = absolutePath.replace(/\\/g, "/");
          const publicIndex = normalizedPath.indexOf("/public/");
          if (publicIndex !== -1) {
            const relativePath = normalizedPath.substring(publicIndex + 7);
            relativeAudioUrls[sceneId] = "/" + relativePath;
          } else {
            relativeAudioUrls[sceneId] = absolutePath;
          }
        }
      }
    }

    const FPS = 30;
    const durationInFrames = script.scenes.reduce(
      (sum, scene) => sum + (scene.durationSeconds || 5) * FPS,
      0
    );
    const totalDurationSeconds = durationInFrames / FPS;
    console.error(`[DEBUG] 总时长: ${totalDurationSeconds}秒, ${durationInFrames}帧`);

    console.error(`[DEBUG] 选择 Composition...`);
    let composition = await selectComposition({
      serveUrl: bundleLocation,
      id: "TeachingVideo",
      inputProps: { script, audioUrls: relativeAudioUrls },
    });

    composition = { ...composition, durationInFrames };

    console.error(`[DEBUG] 开始渲染视频到: ${outputPath}`);
    
    // 确保输出目录存在
    const outputDir = path.dirname(outputPath);
    await fs.mkdir(outputDir, { recursive: true });

    const renderResult = await renderMedia({
      composition,
      serveUrl: bundleLocation,
      codec: "h264",
      outputLocation: outputPath,
      inputProps: { script, audioUrls: relativeAudioUrls },
      chromiumOptions: {
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--enable-gpu',  // 启用 GPU 加速
          '--use-gl=angle',
          '--use-angle=swiftshader',
        ],
      },
      timeoutInMilliseconds: 300000,
      onProgress: ({ progress, renderedFrames, encodedFrames }) => {
        console.error(`[PROGRESS] ${(progress * 100).toFixed(1)}% - 渲染: ${renderedFrames}, 编码: ${encodedFrames}`);
      },
    });

    console.error(`[DEBUG] renderMedia 返回:`, JSON.stringify(renderResult));
    
    // 等待文件写入
    await new Promise(resolve => setTimeout(resolve, 1000));

    // 验证输出文件
    try {
      const stats = await fs.stat(outputPath);
      console.error(`[DEBUG] 输出文件大小: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
      if (stats.size === 0) {
        throw new Error(`输出文件大小为 0`);
      }
    } catch (err) {
      console.error(`[ERROR] 文件验证失败: ${err.message}`);
      throw new Error(`渲染完成但输出文件不存在或无效: ${outputPath} - ${err.message}`);
    }

    console.log(JSON.stringify({ success: true, outputPath, duration: totalDurationSeconds }));
  } catch (error) {
    console.error(`[ERROR] ${error.message}`);
    console.error(`[ERROR] Stack: ${error.stack}`);
    console.error(JSON.stringify({ error: error.message, stack: error.stack }));
    process.exit(1);
  }
}

main();
