"use client";

import React, { useMemo } from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { TextAnimationContent } from "@/lib/script-types";

interface Props {
  content: TextAnimationContent;
}

/** 解析词汇释义文本结构 */
function parseVocabularyText(text: string) {
  // 匹配 "word (pos.) 1. xxx 2. xxx" 或 "word (pos.) xxx、xxx"
  const match = text.match(
    /^([a-zA-Z][a-zA-Z\s-]*?)\s*\(([^)]+)\)\s*(.+)$/s
  );
  if (!match) return null;

  const word = match[1].trim();
  const pos = match[2].trim();
  const rest = match[3].trim();

  // 按编号拆分释义: "1. xxx 2. xxx" 或直接作为整体
  const defs = rest.match(/\d+\.\s*[^0-9]+/g);
  const definitions = defs
    ? defs.map((d) => d.replace(/^\d+\.\s*/, "").trim())
    : [rest];

  return { word, pos, definitions };
}

export const TextAnimationScene: React.FC<Props> = ({ content }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const parsed = useMemo(() => parseVocabularyText(content.text), [content.text]);

  // ========== 词汇释义结构化展示 ==========
  if (parsed) {
    // 单词出现动画
    const wordScale = spring({ frame, fps, config: { damping: 12, stiffness: 80 } });
    const wordOpacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });

    // 词性标签动画（单词之后）
    const posOpacity = interpolate(frame, [15, 28], [0, 1], { extrapolateRight: "clamp" });
    const posX = interpolate(frame, [15, 28], [20, 0], { extrapolateRight: "clamp" });

    // 分隔线动画
    const lineWidth = interpolate(frame, [25, 45], [0, 100], { extrapolateRight: "clamp" });

    // 背景光晕脉动
    const glowPulse = Math.sin(frame * 0.03) * 0.15 + 0.85;

    return (
      <AbsoluteFill
        style={{
          background: "linear-gradient(135deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%)",
          justifyContent: "center",
          alignItems: "center",
          padding: 80,
        }}
      >
        {/* 背景装饰光晕 */}
        <div
          style={{
            position: "absolute",
            top: "20%",
            left: "50%",
            width: 600,
            height: 600,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(78,205,196,0.08) 0%, transparent 70%)",
            transform: `translate(-50%, -50%) scale(${glowPulse})`,
          }}
        />

        {/* 主内容区 */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 32, zIndex: 1 }}>
          {/* 单词 */}
          <div
            style={{
              fontSize: 80,
              fontWeight: 700,
              color: "#fff",
              fontFamily: "Arial, sans-serif",
              letterSpacing: 3,
              opacity: wordOpacity,
              transform: `scale(${wordScale})`,
              textShadow: "0 0 40px rgba(78,205,196,0.3)",
            }}
          >
            {parsed.word}
          </div>

          {/* 词性标签 */}
          <div
            style={{
              display: "inline-flex",
              padding: "8px 24px",
              borderRadius: 20,
              backgroundColor: "rgba(78,205,196,0.15)",
              border: "1px solid rgba(78,205,196,0.3)",
              opacity: posOpacity,
              transform: `translateX(${posX}px)`,
            }}
          >
            <span style={{ fontSize: 28, color: "#4ECDC4", fontFamily: "Arial, sans-serif", fontStyle: "italic" }}>
              {parsed.pos}
            </span>
          </div>

          {/* 分隔线 */}
          <div
            style={{
              width: `${lineWidth}%`,
              maxWidth: 400,
              height: 2,
              background: "linear-gradient(90deg, transparent, rgba(78,205,196,0.5), transparent)",
            }}
          />

          {/* 释义列表 */}
          <div style={{ display: "flex", flexDirection: "column", gap: 20, alignItems: "center" }}>
            {parsed.definitions.map((def, i) => {
              const defStart = 35 + i * 15;
              const defOpacity = interpolate(frame, [defStart, defStart + 18], [0, 1], { extrapolateRight: "clamp" });
              const defY = interpolate(frame, [defStart, defStart + 18], [25, 0], { extrapolateRight: "clamp" });

              return (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 16,
                    opacity: defOpacity,
                    transform: `translateY(${defY}px)`,
                  }}
                >
                  {/* 编号圆点 */}
                  <div
                    style={{
                      width: 36,
                      height: 36,
                      borderRadius: "50%",
                      backgroundColor: "rgba(78,205,196,0.2)",
                      border: "1px solid rgba(78,205,196,0.4)",
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      flexShrink: 0,
                    }}
                  >
                    <span style={{ fontSize: 20, color: "#4ECDC4", fontWeight: 600 }}>{i + 1}</span>
                  </div>
                  {/* 释义文字 */}
                  <span
                    style={{
                      fontSize: 40,
                      color: "#E0E0E0",
                      fontFamily: "'Microsoft YaHei', sans-serif",
                      lineHeight: 1.5,
                    }}
                  >
                    {def}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  // ========== 通用文本展示（非词汇释义）==========
  const cardOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const cardScale = interpolate(frame, [0, 15], [0.95, 1], { extrapolateRight: "clamp" });

  const textStyle: React.CSSProperties = {
    fontSize: 44,
    color: "#E8E8E8",
    fontFamily: "'Microsoft YaHei', sans-serif",
    textAlign: "center",
    lineHeight: 1.8,
    letterSpacing: 1,
  };

  // 打字机效果
  const renderTypewriter = () => {
    const charsToShow = Math.floor(frame / 2);
    const displayText = content.text.substring(0, charsToShow);
    return (
      <div style={textStyle}>
        {displayText}
        <span style={{ opacity: frame % 30 < 15 ? 1 : 0, color: "#4ECDC4" }}>|</span>
      </div>
    );
  };

  // 淡入效果
  const renderFadeIn = () => {
    const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
    return <div style={{ ...textStyle, opacity }}>{content.text}</div>;
  };

  // 上滑效果
  const renderSlideUp = () => {
    const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
    const translateY = interpolate(frame, [0, 20], [50, 0], { extrapolateRight: "clamp" });
    return (
      <div style={{ ...textStyle, opacity, transform: `translateY(${translateY}px)` }}>
        {content.text}
      </div>
    );
  };

  const renderContent = () => {
    switch (content.animation) {
      case "typewriter": return renderTypewriter();
      case "fade-in": return renderFadeIn();
      case "slide-up": return renderSlideUp();
      default: return renderFadeIn();
    }
  };

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%)",
        justifyContent: "center",
        alignItems: "center",
        padding: 80,
      }}
    >
      <div
        style={{
          position: "relative",
          backgroundColor: "rgba(255, 255, 255, 0.05)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: 20,
          padding: "48px 64px",
          maxWidth: 1200,
          opacity: cardOpacity,
          transform: `scale(${cardScale})`,
          boxShadow: "0 12px 40px rgba(0, 0, 0, 0.3)",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 0,
            top: "20%",
            bottom: "20%",
            width: 3,
            borderRadius: 2,
            background: "linear-gradient(180deg, #4ECDC4, transparent)",
          }}
        />
        {renderContent()}
      </div>
    </AbsoluteFill>
  );
};

