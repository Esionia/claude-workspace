"use client";

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { ComparisonContent } from "@/lib/script-types";

interface Props {
  content: ComparisonContent;
}

export const ComparisonScene: React.FC<Props> = ({ content }) => {
  const frame = useCurrentFrame();

  const leftSlide = interpolate(frame, [0, 20], [-100, 0], {
    extrapolateRight: "clamp",
  });

  const rightSlide = interpolate(frame, [10, 30], [100, 0], {
    extrapolateRight: "clamp",
  });

  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const PanelStyle: React.CSSProperties = {
    flex: 1,
    padding: 40,
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    gap: 20,
  };

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
      }}
    >
      <div
        style={{
          display: "flex",
          width: "100%",
          height: "100%",
        }}
      >
        {/* 左侧 */}
        <div
          style={{
            ...PanelStyle,
            backgroundColor: "rgba(78, 205, 196, 0.1)",
            transform: `translateX(${leftSlide}%)`,
            opacity,
          }}
        >
          <div
            style={{
              fontSize: 32,
              color: "#4ECDC4",
              fontWeight: "bold",
              fontFamily: "'Microsoft YaHei', sans-serif",
            }}
          >
            {content.left.title}
          </div>
          <div
            style={{
              fontSize: 36,
              color: "#fff",
              textAlign: "center",
              fontFamily: "Arial, sans-serif",
              lineHeight: 1.6,
            }}
          >
            {content.left.content}
          </div>
          {content.left.isCorrect !== undefined && (
            <div
              style={{
                fontSize: 48,
                color: content.left.isCorrect ? "#4ECDC4" : "#FF6B6B",
              }}
            >
              {content.left.isCorrect ? "✓" : "✗"}
            </div>
          )}
        </div>

        {/* 分隔线 */}
        <div
          style={{
            width: 4,
            backgroundColor: "rgba(255,255,255,0.2)",
          }}
        />

        {/* 右侧 */}
        <div
          style={{
            ...PanelStyle,
            backgroundColor: "rgba(255, 107, 107, 0.1)",
            transform: `translateX(${rightSlide}%)`,
            opacity,
          }}
        >
          <div
            style={{
              fontSize: 32,
              color: "#FF6B6B",
              fontWeight: "bold",
              fontFamily: "'Microsoft YaHei', sans-serif",
            }}
          >
            {content.right.title}
          </div>
          <div
            style={{
              fontSize: 36,
              color: "#fff",
              textAlign: "center",
              fontFamily: "Arial, sans-serif",
              lineHeight: 1.6,
            }}
          >
            {content.right.content}
          </div>
          {content.right.isCorrect !== undefined && (
            <div
              style={{
                fontSize: 48,
                color: content.right.isCorrect ? "#4ECDC4" : "#FF6B6B",
              }}
            >
              {content.right.isCorrect ? "✓" : "✗"}
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
