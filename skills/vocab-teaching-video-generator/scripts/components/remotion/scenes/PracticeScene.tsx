"use client";

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PracticeContent } from "@/lib/script-types";

interface Props {
  content: PracticeContent;
}

export const PracticeScene: React.FC<Props> = ({ content }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // 英文句子淡入
  const sentenceOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 中文翻译延迟淡入
  const translationOpacity = interpolate(frame, [30, 50], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 答案揭示（场景 75% 时显示）
  const answerRevealFrame = Math.floor(durationInFrames * 0.75);
  const showAnswer = frame >= answerRevealFrame;

  // 将填空处的下划线替换为答案（高亮显示）
  // 同时去掉中文提示前缀（如"请用 request 完成句子："）
  const renderQuestion = () => {
    // 去掉中文提示前缀：匹配 "请用...：" 或 "请用...:" 等模式
    let questionText = content.question.replace(/^[^A-Za-z]*[:：]\s*/, "");
    // 如果去掉后为空，保留原文
    if (!questionText.trim()) questionText = content.question;

    const parts = questionText.split(/(_+)/);
    return parts.map((part, index) => {
      if (part.match(/^_+$/)) {
        // 这是填空处
        return (
          <span key={index}>
            {showAnswer ? (
              <span style={{ color: "#4ECDC4", fontWeight: "bold" }}>
                {content.answer}
              </span>
            ) : (
              <span style={{ color: "rgba(255,255,255,0.3)" }}>
                {part}
              </span>
            )}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        padding: 80,
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          justifyContent: "center",
          alignItems: "center",
          gap: 60,
        }}
      >
        {/* 英文填空句子 */}
        <div
          style={{
            fontSize: 48,
            color: "#fff",
            fontFamily: "'Microsoft YaHei', Arial, sans-serif",
            textAlign: "center",
            maxWidth: "90%",
            lineHeight: 1.6,
            opacity: sentenceOpacity,
          }}
        >
          {renderQuestion()}
        </div>

        {/* 中文翻译 */}
        {content.explanation && (
          <div
            style={{
              fontSize: 32,
              color: "#4ECDC4",
              fontFamily: "'Microsoft YaHei', Arial, sans-serif",
              textAlign: "center",
              maxWidth: "90%",
              lineHeight: 1.6,
              opacity: translationOpacity,
            }}
          >
            {content.explanation}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
