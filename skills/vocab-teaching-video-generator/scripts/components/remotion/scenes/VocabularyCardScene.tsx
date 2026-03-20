"use client";

import React from "react";
import { AbsoluteFill, Audio, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from "remotion";

interface VocabularyCardSceneProps {
  phrase: string;
  meaning: string;
  // 定义模式（新增）
  partOfSpeech?: string;
  definitions?: string[];
  // 完整模式（现有）
  example?: string;
  exampleChinese?: string;
  // 音频支持
  phraseAudioUrl?: string;        // 短语发音音频
  phraseAudioDuration?: number;   // 短语音频时长（秒）
  exampleAudioUrl?: string;       // 例句朗读音频
  exampleAudioDuration?: number;  // 例句音频时长（秒）
  // 旁白音频（narration）
  audioUrl?: string;
  // 背景音乐
  backgroundMusicUrl?: string;    // 背景音乐 URL
  backgroundMusicVolume?: number; // 背景音乐音量（0-1，默认 0.3）
}

export const VocabularyCardScene: React.FC<VocabularyCardSceneProps> = ({
  phrase,
  meaning,
  partOfSpeech,
  definitions,
  example,
  exampleChinese,
  phraseAudioUrl,
  phraseAudioDuration,
  exampleAudioUrl,
  exampleAudioDuration,
  audioUrl,
  backgroundMusicUrl = "/audio/bgm/spark-of-inspiration.mp3",
  backgroundMusicVolume = 0.25,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 判断模式：没有例句 = 定义模式
  const isDefinitionMode = !example;

  // ========== 音频时间线计算 ==========
  // 短语音频播放时长（帧数）
  const phraseAudioFrames = phraseAudioDuration ? Math.round(phraseAudioDuration * fps) : 0;
  // 例句音频播放时长（帧数）
  const exampleAudioFrames = exampleAudioDuration ? Math.round(exampleAudioDuration * fps) : 0;

  // ========== 动画时间线（根据模式和音频动态调整）==========
  // 阶段1：短语出现（0-30帧，1秒）
  const phraseSlideX = interpolate(frame, [0, 30], [-100, 0], {
    extrapolateRight: "clamp",
  });
  const phraseScale = spring({
    frame,
    fps,
    from: 0.8,
    to: 1,
    config: { damping: 10, stiffness: 100 },
  });
  const phraseOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 阶段2：中文释义/词性标签淡入（短语出现后）
  const meaningStart = 30;
  const meaningOpacity = interpolate(frame, [meaningStart, meaningStart + 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 定义模式的额外动画
  const posOpacity = interpolate(frame, [meaningStart + 15, meaningStart + 28], [0, 1], {
    extrapolateRight: "clamp",
  });
  const posSlideX = interpolate(frame, [meaningStart + 15, meaningStart + 28], [20, 0], {
    extrapolateRight: "clamp",
  });

  // 分隔线动画（在释义出现后）
  const lineWidth = interpolate(frame, [meaningStart + 10, meaningStart + 30], [0, 100], {
    extrapolateRight: "clamp",
  });

  if (isDefinitionMode) {
    // ========== 定义模式时间线 ==========
    // 使用 definitions 数组（CoverScene 已展示中文释义，定义模式只展示释义列表）
    const definitionList = definitions && definitions.length > 0 ? definitions : [];

    // 渲染定义列表（逐个淡入）
    const renderDefinitions = () => {
      return definitionList.map((def, index) => {
        const defStart = meaningStart + 40 + index * 30; // 每个定义间隔 1 秒
        const defOpacity = interpolate(frame, [defStart, defStart + 20], [0, 1], {
          extrapolateRight: "clamp",
        });
        const defY = interpolate(frame, [defStart, defStart + 20], [25, 0], {
          extrapolateRight: "clamp",
        });

        return (
          <div
            key={index}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 20,
              opacity: defOpacity,
              transform: `translateY(${defY}px)`,
              justifyContent: "center",
            }}
          >
            {/* 编号圆点 */}
            <div
              style={{
                minWidth: 40,
                height: 40,
                borderRadius: "50%",
                border: "2px solid #4ECDC4",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                fontSize: 22,
                color: "#4ECDC4",
                fontWeight: "bold",
                flexShrink: 0,
              }}
            >
              {index + 1}
            </div>
            {/* 释义文本 */}
            <div
              style={{
                fontSize: 44,
                color: "#F0F0F0",
                fontFamily: "'Segoe UI', 'Microsoft YaHei', sans-serif",
                fontWeight: 500,
                lineHeight: 1.5,
                textAlign: "left",
              }}
            >
              {def}
            </div>
          </div>
        );
      });
    };

    return (
      <>
        {/* 播放旁白音频（narration） */}
        {audioUrl && (
          <Audio
            src={staticFile(audioUrl.replace(/^\//, ""))}
            startFrom={0}
            volume={1}
          />
        )}
      <AbsoluteFill
        style={{
          background: "linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%)",
          justifyContent: "center",
          alignItems: "center",
          padding: 80,
        }}
      >
        {/* 播放短语发音音频 */}
        {phraseAudioUrl && (
          <Audio
            src={staticFile(phraseAudioUrl.replace(/^\//, ""))}
            startFrom={0}
            volume={1}
          />
        )}

        {/* 主卡片容器 */}
        <div
          style={{
            width: "85%",
            maxWidth: 1400,
            backgroundColor: "rgba(255, 255, 255, 0.08)",
            borderRadius: 24,
            padding: "60px 80px",
            boxShadow: "0 20px 60px rgba(0, 0, 0, 0.4)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            display: "flex",
            flexDirection: "column",
            gap: 40,
            alignItems: "center",
          }}
        >
          {/* 短语（大字体，弹性动画） */}
          <div
            style={{
              fontSize: 80,
              fontWeight: "bold",
              color: "#fff",
              fontFamily: "Arial, sans-serif",
              textAlign: "center",
              opacity: phraseOpacity,
              transform: `translateX(${phraseSlideX}px) scale(${phraseScale})`,
              textShadow: "0 4px 20px rgba(0, 0, 0, 0.3)",
              letterSpacing: 2,
            }}
          >
            {phrase}
          </div>

          {/* 词性标签（如果有） */}
          {partOfSpeech && (
            <div
              style={{
                fontSize: 28,
                color: "#4ECDC4",
                fontFamily: "Arial, sans-serif",
                textAlign: "center",
                opacity: posOpacity,
                transform: `translateX(${posSlideX}px)`,
                backgroundColor: "rgba(78, 205, 196, 0.15)",
                padding: "8px 24px",
                borderRadius: 20,
                border: "2px solid rgba(78, 205, 196, 0.3)",
              }}
            >
              {partOfSpeech}
            </div>
          )}

          {/* 分隔线 */}
          <div
            style={{
              width: `${lineWidth}%`,
              height: 2,
              background: "linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent)",
            }}
          />

          {/* 释义列表（居中显示） */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 28,
              width: "100%",
              maxWidth: 900,
            }}
          >
            {renderDefinitions()}
          </div>
        </div>
      </AbsoluteFill>
      </>
    );
  }

  // ========== 完整模式时间线（保持现有逻辑）==========
  // 阶段3：例句开始（释义出现后，如果有短语音频则等音频播放完）
  const exampleStart = phraseAudioFrames > 0 ? Math.max(60, phraseAudioFrames + 15) : 60;

  // 例句打字机效果（根据例句音频时长调整速度）
  const typewriterDuration = exampleAudioFrames > 0 ? exampleAudioFrames : 90;
  const exampleCharsToShow = Math.floor(
    interpolate(frame, [exampleStart, exampleStart + typewriterDuration], [0, example!.length], {
      extrapolateRight: "clamp",
    })
  );
  const displayExample = example!.slice(0, exampleCharsToShow);

  // 阶段4：中文翻译淡入（例句音频播放完后）
  const chineseStart = exampleStart + (exampleAudioFrames > 0 ? exampleAudioFrames + 15 : typewriterDuration);
  const chineseOpacity = interpolate(frame, [chineseStart, chineseStart + 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  // ========== 高亮短语逻辑 ==========
  const renderExampleWithHighlight = () => {
    // 在例句中查找短语（不区分大小写）
    const lowerExample = example!.toLowerCase();
    const lowerPhrase = phrase.toLowerCase();
    const highlightIndex = lowerExample.indexOf(lowerPhrase);

    if (highlightIndex === -1 || exampleCharsToShow <= highlightIndex) {
      // 未找到短语或打字机还未显示到短语位置
      return displayExample;
    }

    const beforeHighlight = example!.slice(0, highlightIndex);
    const highlightText = example!.slice(
      highlightIndex,
      highlightIndex + phrase.length
    );
    const afterHighlight = example!.slice(highlightIndex + phrase.length);

    // 计算当前显示的各部分
    const displayBefore = displayExample.slice(0, highlightIndex);
    const displayHighlight = displayExample.slice(
      highlightIndex,
      Math.min(displayExample.length, highlightIndex + phrase.length)
    );
    const displayAfter = displayExample.slice(highlightIndex + phrase.length);

    return (
      <>
        <span>{displayBefore}</span>
        {displayHighlight && (
          <span
            style={{
              color: "#FFD700",
              fontWeight: "bold",
              textShadow: "0 0 10px rgba(255, 215, 0, 0.5)",
            }}
          >
            {displayHighlight}
          </span>
        )}
        <span>{displayAfter}</span>
      </>
    );
  };

  return (
    <>
      {/* 播放旁白音频（narration） */}
      {audioUrl && (
        <Audio
          src={staticFile(audioUrl.replace(/^\//, ""))}
          startFrom={0}
          volume={1}
        />
      )}
      <AbsoluteFill
        style={{
          background: "linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%)",
          justifyContent: "center",
          alignItems: "center",
          padding: 80,
        }}
      >
        {/* 播放短语发音音频 */}
        {phraseAudioUrl && (
          <Audio
            src={staticFile(phraseAudioUrl.replace(/^\//, ""))}
            startFrom={0}
            volume={1}
          />
        )}

        {/* 播放例句朗读音频（在例句开始显示时播放） */}
        {exampleAudioUrl && (
          <Audio
            src={staticFile(exampleAudioUrl.replace(/^\//, ""))}
            startFrom={exampleStart}
            volume={1}
          />
        )}

        {/* 主卡片容器 */}
        <div
          style={{
            width: "85%",
            maxWidth: 1400,
            backgroundColor: "rgba(255, 255, 255, 0.08)",
            borderRadius: 24,
            padding: "60px 80px",
            boxShadow: "0 20px 60px rgba(0, 0, 0, 0.4)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            display: "flex",
            flexDirection: "column",
            gap: 40,
          }}
        >
          {/* 短语（大字体，弹性动画） */}
          <div
            style={{
              fontSize: 80,
              fontWeight: "bold",
              color: "#fff",
              fontFamily: "Arial, sans-serif",
              textAlign: "center",
              opacity: phraseOpacity,
              transform: `translateX(${phraseSlideX}px) scale(${phraseScale})`,
              textShadow: "0 4px 20px rgba(0, 0, 0, 0.3)",
              letterSpacing: 2,
            }}
          >
            {phrase}
          </div>

          {/* 中文释义（淡入） */}
          <div
            style={{
              fontSize: 48,
              color: "#D1D5DB",
              fontFamily: "'Microsoft YaHei', sans-serif",
              textAlign: "center",
              opacity: meaningOpacity,
            }}
          >
            {meaning}
          </div>

          {/* 分隔线 */}
          <div
            style={{
              width: `${lineWidth}%`,
              height: 2,
              background: "linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent)",
              margin: "0 auto",
            }}
          />

          {/* 例句（打字机效果，关键词高亮） */}
          <div
            style={{
              fontSize: 36,
              color: "#fff",
              fontFamily: "Arial, sans-serif",
              lineHeight: 1.6,
              textAlign: "center",
              minHeight: 100,
            }}
          >
            {renderExampleWithHighlight()}
            {/* 打字机光标 */}
            {exampleCharsToShow < example!.length && (
              <span
                style={{
                  opacity: frame % 20 < 10 ? 1 : 0,
                  color: "#FFD700",
                  marginLeft: 4,
                }}
              >
                |
              </span>
            )}
          </div>

          {/* 中文翻译（延迟淡入） */}
          <div
            style={{
              fontSize: 32,
              color: "#9CA3AF",
              fontFamily: "'Microsoft YaHei', sans-serif",
              textAlign: "center",
              lineHeight: 1.6,
              opacity: chineseOpacity,
            }}
          >
            {exampleChinese}
          </div>
        </div>
      </AbsoluteFill>
    </>
  );
};
