"use client";

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Audio, staticFile } from "remotion";
import { SummaryContent } from "@/lib/script-types";
import { VIDEO_FPS } from "../shared";

const FPS = VIDEO_FPS;

interface Props {
  content: SummaryContent;
  audioDurationInFrames?: number; // 语音时长（帧数）
  audioUrl?: string; // 旁白音频 URL
}

export const SummaryScene: React.FC<Props> = ({ content, audioDurationInFrames = 60, audioUrl }) => {
  const frame = useCurrentFrame();

  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 防御性检查：确保 points 存在且是数组
  const points = Array.isArray(content.points) ? content.points : [];

  // 计算每个要点的平均语音时长（帧数）
  const avgPointDuration = points.length > 0 ? Math.floor(audioDurationInFrames / points.length) : 60;
  const pointsStartFrame = 20;

  return (
    <>
      {audioUrl && <Audio src={staticFile(audioUrl.replace(/^\//, ""))} />}
      <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        justifyContent: "center",
        alignItems: "center",
        padding: 80,
      }}
    >
      <div
        style={{
          width: "80%",
          maxWidth: 1000,
        }}
      >
        {/* 标题 */}
        <div
          style={{
            fontSize: 48,
            color: "#4ECDC4",
            fontWeight: "bold",
            fontFamily: "'Microsoft YaHei', sans-serif",
            textAlign: "center",
            marginBottom: 50,
            opacity: titleOpacity,
          }}
        >
          📝 总结
        </div>

        {/* 要点列表 */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 24,
          }}
        >
          {points.length === 0 ? (
            <div
              style={{
                fontSize: 28,
                color: "#FF6B6B",
                textAlign: "center",
                fontFamily: "'Microsoft YaHei', sans-serif",
              }}
            >
              ⚠️ 总结内容格式错误，请重新生成
            </div>
          ) : (
            points.map((point, index) => {
              // 每个要点的开始时间 = 前面所有要点的时长总和
              const pointStart = pointsStartFrame + index * avgPointDuration;
              const typewriterDuration = 30; // 打字机效果持续 1 秒

              const pointOpacity = interpolate(
                frame,
                [pointStart, pointStart + 10],
                [0, 1],
                { extrapolateRight: "clamp" }
              );

              // 打字机效果：逐字显示
              const charsToShow = Math.floor(
                interpolate(
                  frame,
                  [pointStart, pointStart + typewriterDuration],
                  [0, point.length],
                  { extrapolateRight: "clamp" }
                )
              );
              const displayText = point.slice(0, charsToShow);

              return (
                  <div
                  key={index}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 20,
                    opacity: pointOpacity,
                  }}
                >
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: "50%",
                      backgroundColor: "#4ECDC4",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 20,
                      fontWeight: "bold",
                      color: "#1a1a2e",
                      flexShrink: 0,
                    }}
                  >
                    {index + 1}
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      color: "#fff",
                      fontFamily: "'Microsoft YaHei', sans-serif",
                    }}
                  >
                    {displayText}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </AbsoluteFill>
    </>
  );
};
