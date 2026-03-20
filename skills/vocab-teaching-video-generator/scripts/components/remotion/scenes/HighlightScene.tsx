"use client";

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Audio, staticFile, Sequence } from "remotion";
import { HighlightContent } from "@/lib/script-types";

interface Props {
  content: HighlightContent;
  audioDurationInFrames?: number;  // 语音旁白实际时长（帧数）
}

// 词根/词缀颜色（与 renderTopBreakdown 共享）
const ROOT_COLORS = ["#4ECDC4", "#FFD93D", "#FF6B9D", "#95E1D3", "#F38181"];

// 将 hex 颜色转为 rgba
const hexToRgba = (hex: string, alpha: number) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

// 帧率常量
import { VIDEO_FPS } from "../shared";
const FPS = VIDEO_FPS;

export const HighlightScene: React.FC<Props> = ({ content, audioDurationInFrames }) => {
  const frame = useCurrentFrame();

  const sentenceOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 当词根词缀出现时，句子向上移动到顶部
  const sentenceY = interpolate(frame, [50, 65], [0, -420], {
    extrapolateRight: "clamp",
  });

  const sentenceScale = interpolate(frame, [50, 65], [1, 0.65], {
    extrapolateRight: "clamp",
  });

  // 词根区域从下方进入
  const rootsY = interpolate(frame, [50, 65], [150, 0], {
    extrapolateRight: "clamp",
  });

  // 图片动画
  const imageOpacity = interpolate(frame, [30, 45], [0, 1], {
    extrapolateRight: "clamp",
  });

  const imageScale = interpolate(frame, [30, 45], [0.8, 1], {
    extrapolateRight: "clamp",
  });

  // 渲染词根分解说明
  const renderRootBreakdown = () => {
    if (!content.rootAffix || content.rootAffix.length === 0) {
      return null;
    }

    // 提取单词主体（去掉词性标记）
    const wordMatch = content.sentence.match(/^(\w+)/);
    const mainWord = wordMatch ? wordMatch[1] : "";

    const rootAffixList = content.rootAffix!;

    // 构建分解公式
    const rootParts = rootAffixList.map((item, index) => {
      const isLast = index === rootAffixList.length - 1;
      return (
        <React.Fragment key={index}>
          <span style={{ color: "#FFD93D", fontWeight: "bold" }}>
            {item.root}
          </span>
          <span style={{ color: "#A8DADC", margin: "0 8px" }}>
            ({item.meaning})
          </span>
          {!isLast && <span style={{ color: "#fff", margin: "0 8px" }}>+</span>}
        </React.Fragment>
      );
    });

    const breakdownOpacity = interpolate(frame, [15, 30], [0, 1], {
      extrapolateRight: "clamp",
    });

    return (
      <div
        style={{
          fontSize: 22,
          color: "#A8DADC",
          marginTop: 15,
          opacity: breakdownOpacity,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexWrap: "wrap",
          gap: "4px 8px",
        }}
      >
        <span style={{ color: "#4ECDC4", fontWeight: "bold" }}>
          {mainWord}
        </span>
        <span style={{ color: "#fff" }}>=</span>
        {rootParts}
      </div>
    );
  };

  // 解析句子，找出需要高亮的部分
  const renderSentence = () => {
    // 检查是否包含词性标记（�� "(n.)"）
    const hasPartOfSpeech = /\([a-z]+\.\)/.test(content.sentence);

    if (hasPartOfSpeech) {
      // 如果有词性标记，说明是单词定义格式，需要上下排列
      // 格式：emergency (n.) 紧急情况、突发事件
      const parts = content.sentence.split(/\s+/);
      const word = parts[0]; // emergency
      const rest = parts.slice(1).join(" "); // (n.) 紧急情况、突发事件

      return (
        <>
          <div style={{ fontSize: 48, fontWeight: "bold", marginBottom: 12 }}>
            {word}
          </div>
          <div style={{ fontSize: 28, color: "#A8DADC" }}>
            {rest}
          </div>
          {renderRootBreakdown()}
        </>
      );
    }

    // 否则使用原来的高亮逻辑
    let result: React.ReactNode[] = [];
    let remainingSentence = content.sentence;
    let keyIndex = 0;

    content.highlights.forEach((highlight, index) => {
      const highlightIndex = remainingSentence.indexOf(highlight.text);
      if (highlightIndex !== -1) {
        // 高亮前的文本
        if (highlightIndex > 0) {
          result.push(
            <span key={keyIndex++}>
              {remainingSentence.substring(0, highlightIndex)}
            </span>
          );
        }

        // 高亮动画延迟
        const highlightOpacity = interpolate(
          frame,
          [20 + index * 15, 35 + index * 15],
          [0.3, 1],
          { extrapolateRight: "clamp" }
        );

        const highlightScale = interpolate(
          frame,
          [20 + index * 15, 35 + index * 15],
          [1, 1.1],
          { extrapolateRight: "clamp" }
        );

        // 高亮文本
        result.push(
          <span
            key={keyIndex++}
            style={{
              color: highlight.color,
              fontWeight: "bold",
              opacity: highlightOpacity,
              display: "inline",
              position: "relative",
            }}
          >
            {highlight.text}
            {highlight.label && (
              <span
                style={{
                  position: "absolute",
                  top: -40,
                  left: "50%",
                  transform: "translateX(-50%)",
                  fontSize: 18,
                  color: highlight.color,
                  whiteSpace: "nowrap",
                  opacity: highlightOpacity,
                }}
              >
                {highlight.label}
              </span>
            )}
          </span>
        );

        remainingSentence = remainingSentence.substring(
          highlightIndex + highlight.text.length
        );
      }
    });

    // 剩余文本
    if (remainingSentence) {
      result.push(<span key={keyIndex++}>{remainingSentence}</span>);
    }

    return result;
  };

  // 渲染词根词缀详细信息（依次出现，颜色匹配顶部公式）
  const renderRootAffixDetails = () => {
    if (!content.rootAffix || content.rootAffix.length === 0) {
      return null;
    }

    const rootAffixList = content.rootAffix;

    // 计算精确的时间轴：基于每个词根的实际音频时长
    // 顶部公式动画：单词淡入(0-20帧) + 每个词根逐个出现(25 + index*20帧，持续15帧)
    const topFormulaEndFrame = 25 + (rootAffixList.length - 1) * 20 + 15;
    const bufferAfterFormula = 30; // 公式展示完后的缓冲时间
    // 详细区域起始帧 = 顶部公式结束后 + 缓冲 + 旁白结束后
    // 旁白 audioUrl 在父组件 Sequence 帧 0 开始播放，持续 audioDurationInFrames 帧
    // 因此详细区域从 audioDurationInFrames 开始，与旁白完全错开
    const blockStartBase = topFormulaEndFrame + bufferAfterFormula + (audioDurationInFrames || 0);

    // 构建每个词根块的时间轴（基于实际音频时长，包括相关单词）
    let currentFrame = blockStartBase;
    const blockTimeline = rootAffixList.map((item, index) => {
      const rootAudioDuration = item.audioDuration || 3; // 词根讲解音频时长
      const rootDurationInFrames = Math.ceil(rootAudioDuration * FPS);

      // 计算相关单词的总时长
      let wordsTotalFrames = 0;
      if (item.relatedWords && item.relatedWords.length > 0) {
        wordsTotalFrames = item.relatedWords.reduce((sum, word) => {
          const wordDuration = word.audioDuration || 1.5;
          return sum + Math.ceil(wordDuration * FPS);
        }, 0);
      }

      const totalDurationInFrames = rootDurationInFrames + wordsTotalFrames;
      const fadeInDuration = 20; // 淡入动画20帧
      const fadeOutDelay = 15; // 淡出延迟15帧

      const timeline = {
        startFrame: currentFrame,
        durationInFrames: totalDurationInFrames,
        rootDurationInFrames,
        wordsTotalFrames,
        fadeInDuration,
        fadeOutDelay,
        audioUrl: item.audioUrl,
      };

      currentFrame += totalDurationInFrames;
      return timeline;
    });

    // 所有块讲解完毕的时间点
    const allDoneFrame = currentFrame;
    const recoverDuration = 10; // 减少恢复动画时长，让场景更快结束

    return (
      <div
        style={{
          width: "90%",
          maxWidth: 1400,
          display: "flex",
          flexDirection: "column",
          gap: 20,
        }}
      >
        {rootAffixList.map((item, rootIndex) => {
          const color = ROOT_COLORS[rootIndex % ROOT_COLORS.length];
          const timeline = blockTimeline[rootIndex];

          // 播放该词根的音频
          const shouldPlayAudio = frame >= timeline.startFrame && frame < timeline.startFrame + timeline.durationInFrames;

          // 淡入动画
          const blockOpacity = interpolate(
            frame,
            [timeline.startFrame, timeline.startFrame + timeline.fadeInDuration],
            [0, 1],
            { extrapolateRight: "clamp" }
          );
          const blockY = interpolate(
            frame,
            [timeline.startFrame, timeline.startFrame + timeline.fadeInDuration],
            [30, 0],
            { extrapolateRight: "clamp" }
          );

          // 聚焦效果：当前块高亮，其他块降低透明度
          let focusOpacity = 1;
          if (frame >= blockStartBase && frame < allDoneFrame) {
            // 在讲解阶段
            const isCurrentBlock = frame >= timeline.startFrame && frame < timeline.startFrame + timeline.durationInFrames;
            focusOpacity = isCurrentBlock ? 1 : 0.35;
          } else if (frame >= allDoneFrame) {
            // 全部讲完后恢复高亮
            const recoverProgress = interpolate(
              frame,
              [allDoneFrame, allDoneFrame + recoverDuration],
              [0, 1],
              { extrapolateRight: "clamp" }
            );
            focusOpacity = 0.35 + (1 - 0.35) * recoverProgress;
          }

          const finalOpacity = blockOpacity * focusOpacity;

          return (
            <div
              key={rootIndex}
              style={{
                marginBottom: 15,
                opacity: finalOpacity,
                transform: `translateY(${blockY}px)`,
              }}
            >
              {/* 播放该词根的音频 */}
              {item.audioUrl && (
                <Sequence from={timeline.startFrame} durationInFrames={timeline.rootDurationInFrames}>
                  <Audio
                    src={staticFile(item.audioUrl.replace(/^\//, ''))}
                    volume={1}
                  />
                </Sequence>
              )}

              {/* 词根/词缀标题（使用对应颜色） */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: 12,
                  gap: 12,
                }}
              >
                <div
                  style={{
                    fontSize: 30,
                    fontWeight: "bold",
                    color: color,
                    padding: "6px 20px",
                    background: hexToRgba(color, 0.15),
                    borderRadius: 10,
                    border: `2px solid ${color}`,
                  }}
                >
                  {item.root}
                </div>
                <div
                  style={{
                    fontSize: 24,
                    color: "#A8DADC",
                  }}
                >
                  =
                </div>
                <div
                  style={{
                    fontSize: 26,
                    color: "#A8DADC",
                    fontWeight: "500",
                  }}
                >
                  {item.meaning}
                </div>
              </div>

              {/* 相关词汇列表 - 随块同时出现，逐词高亮 */}
              {item.relatedWords && item.relatedWords.length > 0 && (() => {
                const wordsCount = item.relatedWords.length;

                // 计算每个相关单词的时间轴（基于实际音频时长，顺序播放）
                // 词根音频播放完后，开始播放相关单词
                let wordCurrentFrame = timeline.startFrame + (timeline.rootDurationInFrames || 0);
                const wordTimelines = item.relatedWords.map((word) => {
                  const wordAudioDuration = word.audioDuration || 1.5; // 默认1.5秒
                  const wordDurationInFrames = Math.ceil(wordAudioDuration * FPS);

                  const wordTimeline = {
                    startFrame: wordCurrentFrame,
                    durationInFrames: wordDurationInFrames,
                    audioUrl: word.audioUrl,
                  };

                  wordCurrentFrame += wordDurationInFrames;
                  return wordTimeline;
                });

                return (
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "center",
                      gap: 12,
                      flexWrap: "wrap",
                    }}
                  >
                    {item.relatedWords.map((word, wordIndex) => {
                      const wordTimeline = wordTimelines[wordIndex];

                      // 所有单词随块一起出现（不逐个淡入）
                      const wordAppearOpacity = interpolate(
                        frame,
                        [timeline.startFrame + 15, timeline.startFrame + 30],
                        [0, 1],
                        { extrapolateRight: "clamp" }
                      );

                      // 当前词是否高亮（基于音频时长）
                      const blockEndFrame = timeline.startFrame + timeline.durationInFrames;
                      const isHighlighted = frame >= wordTimeline.startFrame && frame < wordTimeline.startFrame + wordTimeline.durationInFrames;

                      // 是否已进入逐词高亮阶段
                      const hlPhaseStarted = frame >= timeline.startFrame + 25 && frame < blockEndFrame;
                      // 全部讲完后恢复
                      const isAllDone = frame >= allDoneFrame;

                      // 透明度：逐词阶段非当前词暗显，其他时候正常
                      let dimFactor: number;
                      if (isAllDone) {
                        dimFactor = 1;
                      } else if (hlPhaseStarted) {
                        dimFactor = isHighlighted ? 1 : 0.5;
                      } else {
                        dimFactor = 1;
                      }

                      const wordFinalOpacity = wordAppearOpacity * dimFactor;
                      // 当前词轻微放大
                      const wordScale = (isHighlighted && hlPhaseStarted && !isAllDone) ? 1.05 : 1;
                      // 是否显示高亮样式
                      const showHlStyle = isHighlighted && hlPhaseStarted && !isAllDone;

                      return (
                        <div
                          key={wordIndex}
                          style={{
                            opacity: wordFinalOpacity,
                            transform: `scale(${wordScale})`,
                          }}
                        >
                          {/* 播放该相关单词的音频 */}
                          {word.audioUrl && (
                            <Sequence from={wordTimeline.startFrame}>
                              <Audio
                                src={staticFile(word.audioUrl.replace(/^\//, ''))}
                                volume={1}
                              />
                            </Sequence>
                          )}

                          <div
                            style={{
                              background: showHlStyle
                                ? hexToRgba(color, 0.12)
                                : "rgba(255, 255, 255, 0.08)",
                              border: showHlStyle
                                ? `2px solid ${color}`
                                : "2px solid rgba(255, 255, 255, 0.25)",
                              borderRadius: 10,
                              padding: "10px 16px",
                              display: "flex",
                              flexDirection: "column",
                              alignItems: "center",
                              gap: 4,
                              minWidth: 140,
                              maxWidth: 200,
                            }}
                          >
                            {/* 单词（高亮词根部分，使用对应颜色） */}
                            <div
                              style={{
                                fontSize: 22,
                                fontWeight: "bold",
                                color: "#fff",
                                textAlign: "center",
                              }}
                            >
                              {word.highlight ? (
                                <>
                                  {word.word.split(word.highlight).map((part, i, arr) => (
                                    <React.Fragment key={i}>
                                      {part}
                                      {i < arr.length - 1 && (
                                        <span style={{ color: color }}>
                                          {word.highlight}
                                        </span>
                                      )}
                                    </React.Fragment>
                                  ))}
                                </>
                              ) : (
                                word.word
                              )}
                            </div>

                            {/* 含义 */}
                            <div
                              style={{
                                fontSize: 16,
                                color: "#A8DADC",
                                textAlign: "center",
                              }}
                            >
                              {word.meaning}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              })()}
            </div>
          );
        })}
      </div>
    );
  };

  // 词根分解场景不显示图片（保持简洁）

  // 渲染顶部词根分解公式（带标签和动画）
  const renderTopBreakdown = () => {
    if (!content.rootAffix || content.rootAffix.length === 0) {
      return null;
    }

    // 提取单词主体（去掉词性标记）
    const wordMatch = content.sentence.match(/^(\w+)/);
    const mainWord = wordMatch ? wordMatch[1] : "";

    // 单词淡入动画
    const wordOpacity = interpolate(frame, [0, 20], [0, 1], {
      extrapolateRight: "clamp",
    });

    const wordY = interpolate(frame, [0, 20], [30, 0], {
      extrapolateRight: "clamp",
    });

    // 为不同词根/词缀分配不同颜色（使用共享常量）
    const rootAffixList = content.rootAffix!;

    // 构建分解公式（每个词根/词缀逐个出现）
    const rootParts = rootAffixList.map((item, index) => {
      const isLast = index === rootAffixList.length - 1;
      const color = ROOT_COLORS[index % ROOT_COLORS.length];

      // 每个词根/词缀的延迟动画
      const partDelay = 25 + index * 20;
      const partOpacity = interpolate(frame, [partDelay, partDelay + 15], [0, 1], {
        extrapolateRight: "clamp",
      });
      const partX = interpolate(frame, [partDelay, partDelay + 15], [30, 0], {
        extrapolateRight: "clamp",
      });

      // 判断类型标签（词根、前缀、后缀）
      const getLabel = (root: string) => {
        if (root.startsWith("-") && root.endsWith("-")) return "词根";
        if (root.startsWith("-")) return "后缀";
        if (root.endsWith("-")) return "前缀";
        return "词根";
      };

      return (
        <React.Fragment key={index}>
          {/* 加号 */}
          {index > 0 && (
            <span
              style={{
                color: "#fff",
                margin: "0 16px",
                fontSize: 48,
                opacity: partOpacity,
                transform: `translateX(${partX}px)`,
                display: "inline-block",
              }}
            >
              +
            </span>
          )}

          {/* 词根/词缀（带上方标签） */}
          <div
            style={{
              display: "inline-flex",
              flexDirection: "column",
              alignItems: "center",
              opacity: partOpacity,
              transform: `translateX(${partX}px)`,
              position: "relative",
            }}
          >
            {/* 上方小标签 */}
            <div
              style={{
                fontSize: 20,
                color: color,
                marginBottom: 8,
                fontWeight: "500",
              }}
            >
              {item.label || getLabel(item.root)}
            </div>

            {/* 词根/词缀文字 */}
            <span
              style={{
                color: color,
                fontWeight: "bold",
                fontSize: 56,
              }}
            >
              {item.root}
            </span>
          </div>
        </React.Fragment>
      );
    });

    return (
      <div
        style={{
          marginBottom: 80,
        }}
      >
        <div
          style={{
            fontSize: 48,
            color: "#A8DADC",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexWrap: "wrap",
            gap: "8px 0px",
          }}
        >
          {/* 单词 */}
          <span
            style={{
              color: "#FFD93D",
              fontWeight: "bold",
              fontSize: 64,
              opacity: wordOpacity,
              transform: `translateY(${wordY}px)`,
              display: "inline-block",
            }}
          >
            {mainWord}
          </span>

          {/* 等号 */}
          <span
            style={{
              color: "#fff",
              fontSize: 52,
              margin: "0 16px",
              opacity: wordOpacity,
              transform: `translateY(${wordY}px)`,
              display: "inline-block",
            }}
          >
            =
          </span>

          {/* 词根词缀部分 */}
          {rootParts}
        </div>
      </div>
    );
  };

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        justifyContent: "center",
        alignItems: "center",
        padding: 80,
        flexDirection: "column",
      }}
    >
      {/* 顶部：词根词缀分解公式 */}
      {renderTopBreakdown()}

      {/* 下方：词根词缀详细信息 */}
      {renderRootAffixDetails()}
    </AbsoluteFill>
  );
};
