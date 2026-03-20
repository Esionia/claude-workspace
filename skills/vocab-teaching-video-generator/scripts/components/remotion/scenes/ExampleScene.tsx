"use client";

import React from "react";
import { AbsoluteFill, Audio, interpolate, useCurrentFrame, staticFile, Sequence } from "remotion";
import { ExampleContent } from "@/lib/script-types";
import { VIDEO_FPS } from "../shared";

interface Props {
  content: ExampleContent;
  englishAudioDuration?: number;
  narrationAudioUrl?: string;
  narrationAudioDuration?: number;
}

const FPS = VIDEO_FPS;

export const ExampleScene: React.FC<Props> = ({ content, englishAudioDuration, narrationAudioUrl, narrationAudioDuration }) => {
  const frame = useCurrentFrame();

  // Chinese translation appears after English audio finishes + 0.5s buffer
  // Use the English audio duration passed from parent (actual value)
  const engDuration = englishAudioDuration || 3;
  const audioDelayFrames = Math.round((engDuration + 0.5) * FPS);

  // 英文句子动画
  const englishOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  const englishY = interpolate(frame, [0, 20], [30, 0], {
    extrapolateRight: "clamp",
  });

  // 中文翻译动画（有音频时延迟到英文朗读结束后）
  const chineseStart = audioDelayFrames || 25;
  const chineseOpacity = interpolate(frame, [chineseStart, chineseStart + 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  const chineseY = interpolate(frame, [chineseStart, chineseStart + 20], [20, 0], {
    extrapolateRight: "clamp",
  });

  // 语法标注动画（中文翻译之后）
  const grammarStart = chineseStart + 25;
  const grammarOpacity = interpolate(frame, [grammarStart, grammarStart + 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  const grammarScale = interpolate(frame, [grammarStart, grammarStart + 20], [0.8, 1], {
    extrapolateRight: "clamp",
  });

  // 高亮词汇的跳动动画（在英文句子出现后开始）
  const highlightBounce = interpolate(
    frame,
    [30, 40, 50, 60],
    [0, -8, 0, -5],
    {
      extrapolateRight: "clamp",
    }
  );

  // 波浪下划线动画
  const underlineProgress = interpolate(frame, [30, 60], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 图片动画
  const imageOpacity = interpolate(frame, [60, 80], [0, 1], {
    extrapolateRight: "clamp",
  });

  const imageScale = interpolate(frame, [60, 80], [0.8, 1], {
    extrapolateRight: "clamp",
  });

  // 渲染场景图片
  const renderImages = () => {
    if (!content.images || content.images.length === 0) {
      return null;
    }

    return (
      <div
        style={{
          marginTop: 40,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          opacity: imageOpacity,
          transform: `scale(${imageScale})`,
        }}
      >
        {content.images.map((image, index) => {
          const size = image.size || "medium";
          const sizeMap = {
            small: 200,
            medium: 300,
            large: 400,
          };

          return (
            <div key={index} style={{ textAlign: "center" }}>
              <img
                src={image.url}
                alt={image.alt}
                style={{
                  width: sizeMap[size],
                  height: "auto",
                  borderRadius: 16,
                  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
                  border: "3px solid rgba(255, 255, 255, 0.2)",
                  objectFit: "cover",
                }}
              />
              {image.alt && (
                <div
                  style={{
                    marginTop: 12,
                    fontSize: 18,
                    color: "#A8DADC",
                    fontWeight: "500",
                    maxWidth: sizeMap[size],
                  }}
                >
                  {image.alt}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  // 渲染带高亮的英文句子
  const renderEnglishWithHighlights = () => {
    if (!content.highlights || content.highlights.length === 0) {
      return content.english;
    }

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    // 按照出现顺序查找并高亮
    content.highlights.forEach((highlight, idx) => {
      const text = highlight.text;
      const index = content.english.indexOf(text, lastIndex);

      if (index === -1) return;

      // 添加高亮前的普通文本
      if (index > lastIndex) {
        parts.push(
          <span key={`text-${idx}`}>
            {content.english.substring(lastIndex, index)}
          </span>
        );
      }

      // 添加高亮文本
      const color = highlight.color || "#FFD93D";
      const effect = highlight.effect || "bounce";

      parts.push(
        <span
          key={`highlight-${idx}`}
          style={{
            color: color,
            fontWeight: "bold",
            display: "inline-block",
            position: "relative",
            transform:
              effect === "bounce"
                ? `translateY(${highlightBounce}px)`
                : effect === "pulse"
                ? `scale(${1 + Math.sin(frame * 0.1) * 0.05})`
                : "none",
            textShadow:
              effect === "glow"
                ? `0 0 20px ${color}, 0 0 30px ${color}`
                : "none",
          }}
        >
          {text}
          {/* 波浪下划线 */}
          {effect === "underline" && (
            <svg
              style={{
                position: "absolute",
                left: 0,
                bottom: -8,
                width: "100%",
                height: 6,
                overflow: "visible",
              }}
            >
              <path
                d={`M 0 3 Q ${underlineProgress * 10} 0, ${
                  underlineProgress * 20
                } 3 T ${underlineProgress * 40} 3`}
                stroke={color}
                strokeWidth="3"
                fill="none"
                strokeLinecap="round"
              />
            </svg>
          )}
          {/* 默认下划线（bounce/pulse/glow 效果） */}
          {effect !== "underline" && (
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                bottom: -4,
                height: 3,
                background: color,
                borderRadius: 2,
                opacity: interpolate(frame, [30, 45], [0, 0.8], {
                  extrapolateRight: "clamp",
                }),
              }}
            />
          )}
        </span>
      );

      lastIndex = index + text.length;
    });

    // 添加剩余的普通文本
    if (lastIndex < content.english.length) {
      parts.push(
        <span key="text-end">{content.english.substring(lastIndex)}</span>
      );
    }

    return parts;
  };

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        justifyContent: "center",
        alignItems: "center",
        padding: "60px 80px",
      }}
    >
      {/* 播放英文例句音频（立即） */}
      {content.englishAudioUrl && (
        <Audio
          src={staticFile(content.englishAudioUrl.replace(/^\//, ""))}
          startFrom={0}
          volume={1}
        />
      )}

      {/* 播放中文旁白（延迟到英文结束后） */}
      {narrationAudioUrl && (
        <Sequence from={audioDelayFrames}>
          <Audio
            src={staticFile(narrationAudioUrl.replace(/^\//, ""))}
            startFrom={0}
            volume={1}
          />
        </Sequence>
      )}

      {/* 整体内容容器 */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 40,
          maxWidth: 1200,
        }}
      >
        {/* 上部：英文例句 + 中文翻译 + 语法标注 */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 24,
          }}
        >
        {/* 英文例句（带智能高亮） */}
        <div
          style={{
            fontSize: 52,
            color: "#fff",
            fontFamily: "Arial, sans-serif",
            textAlign: "center",
            lineHeight: 1.6,
            opacity: englishOpacity,
            transform: `translateY(${englishY}px)`,
          }}
        >
          {renderEnglishWithHighlights()}
        </div>

        {/* 中文翻译 */}
        <div
          style={{
            fontSize: 36,
            color: "#4ECDC4",
            fontFamily: "'Microsoft YaHei', sans-serif",
            textAlign: "center",
            lineHeight: 1.6,
            opacity: chineseOpacity,
            transform: `translateY(${chineseY}px)`,
          }}
        >
          {content.chinese}
        </div>

        {/* 语法标注 */}
        {content.grammar && (
          <div
            style={{
              marginTop: 20,
              padding: "16px 32px",
              backgroundColor: "rgba(255, 107, 107, 0.15)",
              borderRadius: 12,
              border: "2px solid rgba(255, 107, 107, 0.3)",
              opacity: grammarOpacity,
              transform: `scale(${grammarScale})`,
            }}
          >
            <div
              style={{
                fontSize: 28,
                color: "#FF6B6B",
                fontFamily: "'Microsoft YaHei', sans-serif",
                textAlign: "center",
              }}
            >
              📝 {content.grammar}
            </div>
          </div>
        )}
      </div>

      {/* 中下部：场景图片 */}
      {renderImages()}
      </div>
    </AbsoluteFill>
  );
};
