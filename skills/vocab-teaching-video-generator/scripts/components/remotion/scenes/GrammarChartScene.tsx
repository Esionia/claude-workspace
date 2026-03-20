"use client";

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { GrammarChartContent } from "@/lib/script-types";

interface Props {
  content: GrammarChartContent;
}

export const GrammarChartScene: React.FC<Props> = ({ content }) => {
  const frame = useCurrentFrame();

  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        justifyContent: "center",
        alignItems: "center",
        padding: 60,
      }}
    >
      <div
        style={{
          width: "90%",
          maxWidth: 1400,
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
            marginBottom: 40,
            opacity: titleOpacity,
          }}
        >
          {content.title}
        </div>

        {/* 表格 */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          {content.rows.map((row, index) => {
            const rowOpacity = interpolate(
              frame,
              [15 + index * 10, 30 + index * 10],
              [0, 1],
              { extrapolateRight: "clamp" }
            );

            const rowSlide = interpolate(
              frame,
              [15 + index * 10, 30 + index * 10],
              [50, 0],
              { extrapolateRight: "clamp" }
            );

            return (
              <div
                key={index}
                style={{
                  display: "flex",
                  backgroundColor: "rgba(255,255,255,0.05)",
                  borderRadius: 12,
                  overflow: "hidden",
                  opacity: rowOpacity,
                  transform: `translateX(${rowSlide}px)`,
                }}
              >
                {/* 标签 */}
                <div
                  style={{
                    width: 200,
                    padding: 20,
                    backgroundColor: "rgba(78, 205, 196, 0.2)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <span
                    style={{
                      fontSize: 24,
                      color: "#4ECDC4",
                      fontWeight: "bold",
                      fontFamily: "'Microsoft YaHei', sans-serif",
                    }}
                  >
                    {row.label}
                  </span>
                </div>

                {/* 公式 */}
                <div
                  style={{
                    flex: 1,
                    padding: 20,
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "center",
                    gap: 8,
                  }}
                >
                  <div
                    style={{
                      fontSize: 28,
                      color: "#FFE66D",
                      fontFamily: "Consolas, monospace",
                    }}
                  >
                    {row.formula}
                  </div>
                  {row.example && (
                    <div
                      style={{
                        fontSize: 22,
                        color: "#888",
                        fontFamily: "Arial, sans-serif",
                        fontStyle: "italic",
                      }}
                    >
                      例: {row.example}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
