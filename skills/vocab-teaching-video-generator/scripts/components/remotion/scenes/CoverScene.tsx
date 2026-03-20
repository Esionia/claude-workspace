"use client";

import React from "react";
import { AbsoluteFill, Audio, interpolate, useCurrentFrame, spring, staticFile } from "remotion";
import { VIDEO_FPS } from "../shared";

interface CoverSceneProps {
  word: string;          // 英文单词
  translation: string;    // 中文翻译
  subtitle?: string;     // 副标题，默认"英语词汇课堂"
  audioUrl?: string;     // 旁白音频
}

export const CoverScene: React.FC<CoverSceneProps> = ({
  word,
  translation,
  subtitle = "英语词汇课堂",
  audioUrl,
}) => {
  const frame = useCurrentFrame();
  const fps = VIDEO_FPS;

  // 主标题单词：弹入动画
  const wordSpring = spring({
    frame,
    fps,
    from: 0,
    to: 1,
    config: { damping: 12, stiffness: 100 },
  });

  // 单词发光脉冲效果
  const glowPulse = Math.sin(frame * 0.08) * 0.3 + 0.7;

  // 中文翻译：淡入 + 上移
  const transSpring = spring({
    frame,
    fps,
    from: 0,
    to: 1,
    delay: 25,
    config: { damping: 14, stiffness: 80 },
  });

  // 副标题：淡入
  const subSpring = spring({
    frame,
    fps,
    from: 0,
    to: 1,
    delay: 40,
    config: { damping: 14, stiffness: 80 },
  });

  // 装饰圆环旋转
  const ring1Rotate = interpolate(frame, [0, 300], [0, 30], {
    extrapolateRight: "extend",
  });
  const ring2Rotate = interpolate(frame, [0, 300], [0, -20], {
    extrapolateRight: "extend",
  });

  // 装饰圆点淡入
  const dotSpring = spring({
    frame,
    fps,
    from: 0,
    to: 1,
    delay: 50,
    config: { damping: 15, stiffness: 90 },
  });

  // 装饰圆点位置数据
  const dots = [
    { x: 200, y: 180, r: 8, color: "#FFD93D" },
    { x: 1720, y: 150, r: 6, color: "#4ECDC4" },
    { x: 150, y: 750, r: 10, color: "#FF6B9D" },
    { x: 1780, y: 820, r: 7, color: "#FFD93D" },
    { x: 400, y: 100, r: 5, color: "#95E1D3" },
    { x: 1600, y: 950, r: 9, color: "#4ECDC4" },
    { x: 960, y: 80, r: 4, color: "#FF6B9D" },
    { x: 100, y: 500, r: 6, color: "#4ECDC4" },
    { x: 1820, y: 480, r: 8, color: "#FFD93D" },
    { x: 600, y: 970, r: 5, color: "#95E1D3" },
    { x: 1320, y: 970, r: 6, color: "#FF6B9D" },
  ];

  return (
    <>
      {audioUrl && (
        <Audio src={staticFile(audioUrl.replace(/^\//, ""))} startFrom={0} volume={1} />
      )}
      <AbsoluteFill
        style={{
          background: "linear-gradient(135deg, #0f0c29 0%, #1a1a3e 40%, #24243e 100%)",
          justifyContent: "center",
          alignItems: "center",
          overflow: "hidden",
          fontFamily: "'Poppins', 'Noto Sans SC', sans-serif",
        }}
      >
        {/* 背景光晕 */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: 800,
            height: 800,
            background:
              "radial-gradient(circle, rgba(78,205,196,0.15) 0%, transparent 70%)",
            borderRadius: "50%",
            pointerEvents: "none",
          }}
        />

        {/* 装饰圆环 1 */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: 600,
            height: 600,
            transform: `translate(-50%, -50%) rotate(${ring1Rotate}deg)`,
            borderRadius: "50%",
            border: "1px solid rgba(78,205,196,0.2)",
            pointerEvents: "none",
          }}
        />

        {/* 装饰圆环 2 */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: 750,
            height: 750,
            transform: `translate(-50%, -50%) rotate(${ring2Rotate}deg)`,
            borderRadius: "50%",
            border: "1px dashed rgba(255,217,61,0.15)",
            pointerEvents: "none",
          }}
        />

        {/* 装饰圆点 */}
        {dots.map((dot, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              left: dot.x,
              top: dot.y,
              width: dot.r * 2,
              height: dot.r * 2,
              borderRadius: "50%",
              backgroundColor: dot.color,
              opacity: dotSpring * 0.6,
              boxShadow: `0 0 ${dot.r * 2}px ${dot.color}`,
              pointerEvents: "none",
            }}
          />
        ))}

        {/* 顶部装饰线 */}
        <div
          style={{
            position: "absolute",
            top: 100,
            left: "50%",
            transform: `translateX(-50%) scaleX(${subSpring})`,
            width: 200,
            height: 2,
            background: "linear-gradient(90deg, transparent, #4ECDC4, transparent)",
            opacity: 0.6,
          }}
        />

        {/* 主标题单词 */}
        <div
          style={{
            fontSize: 160,
            fontWeight: 800,
            color: "#fff",
            letterSpacing: 8,
            textShadow: `
              0 0 20px rgba(78,205,196,${glowPulse * 0.8}),
              0 0 40px rgba(78,205,196,${glowPulse * 0.4}),
              0 0 80px rgba(78,205,196,${glowPulse * 0.2})
            `,
            transform: `scale(${wordSpring})`,
            opacity: wordSpring,
            lineHeight: 1,
          }}
        >
          {word}
        </div>

        {/* 中文翻译 */}
        <div
          style={{
            fontSize: 56,
            fontWeight: 600,
            color: "#4ECDC4",
            marginTop: 20,
            fontFamily: "'Noto Sans SC', 'Microsoft YaHei', sans-serif",
            transform: `translateY(${(1 - transSpring) * 30}px)`,
            opacity: transSpring,
            letterSpacing: 4,
            textShadow: "0 0 20px rgba(78,205,196,0.5)",
          }}
        >
          {translation}
        </div>

        {/* 副标题 */}
        <div
          style={{
            position: "absolute",
            bottom: 80,
            fontSize: 28,
            color: "rgba(255,255,255,0.4)",
            fontFamily: "'Noto Sans SC', sans-serif",
            letterSpacing: 6,
            transform: `translateY(${(1 - subSpring) * 20}px)`,
            opacity: subSpring,
          }}
        >
          {subtitle}
        </div>

        {/* 底部装饰线 */}
        <div
          style={{
            position: "absolute",
            bottom: 130,
            left: "50%",
            transform: `translateX(-50%) scaleX(${subSpring})`,
            width: 200,
            height: 2,
            background: "linear-gradient(90deg, transparent, #FFD93D, transparent)",
            opacity: 0.4,
          }}
        />

        {/* 单词底部装饰线 */}
        <div
          style={{
            position: "absolute",
            top: "58%",
            left: "50%",
            transform: `translateX(-50%) scaleX(${transSpring})`,
            width: 500,
            height: 2,
            background: "linear-gradient(90deg, transparent, rgba(78,205,196,0.5), transparent)",
          }}
        />
      </AbsoluteFill>
    </>
  );
};
