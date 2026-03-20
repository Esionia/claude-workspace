/**
 * Remotion 组件共享常量与工具函数
 *
 * 所有视频组件统一使用这里的常量，避免分散硬编码。
 */

import { staticFile } from "remotion";

// ─── 全局常量 ───

export const VIDEO_FPS = 30;

/** 深蓝渐变主题色 */
export const THEME_COLORS = {
  bgPrimary: "#1a1a2e",
  bgSecondary: "#16213e",
  bgTertiary: "#0f3460",
  accentA: "#4ECDC4",
  accentB: "#FF6B6B",
  accentHighlight: "#FFD93D",
  accentNote: "#FFE66D",
  textPrimary: "#FFFFFF",
  textSecondary: "rgba(255,255,255,0.7)",
  textMuted: "rgba(255,255,255,0.5)",
} as const;

/** 默认背景渐变 */
export const BG_GRADIENT = `linear-gradient(135deg, ${THEME_COLORS.bgPrimary} 0%, ${THEME_COLORS.bgSecondary} 100%)`;

/** 角色配色 */
export const ROLE_COLORS: Record<string, { bg: string; text: string; bubble: string }> = {
  A: { bg: "#FF6B6B", text: "#FFFFFF", bubble: "rgba(255,107,107,0.92)" },
  B: { bg: "#4ECDC4", text: "#FFFFFF", bubble: "rgba(78,205,196,0.92)" },
};

// ─── 工具函数 ───

/** 统一处理音频/媒体路径：/ 开头的转为 staticFile */
export function resolveMediaSrc(url: string): string {
  if (!url) return "";
  return url.startsWith("/") ? staticFile(url.replace(/^\//, "")) : url;
}

/** resolveAudioSrc 别名，语义更明确 */
export const resolveAudioSrc = resolveMediaSrc;

/**
 * 估算单句对话的帧数
 * @param text 英文文本
 * @param audioDuration 音频时长（秒），可选
 * @param bufferSec 缓冲时间（秒），默认 1.5
 */
export function estimateLineDurationFrames(
  text: string,
  audioDuration?: number,
  bufferSec: number = 1.5,
): number {
  if (audioDuration && audioDuration > 0) {
    return Math.ceil((audioDuration + bufferSec) * VIDEO_FPS);
  }
  // 英语平均语速约 150 词/分钟，即 2.5 词/秒
  const wordCount = text.split(/\s+/).length;
  const estimatedSeconds = wordCount / 2.5 + 2;
  return Math.ceil(estimatedSeconds * VIDEO_FPS);
}
