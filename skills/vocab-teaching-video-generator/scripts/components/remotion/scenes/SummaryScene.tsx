"use client";

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, spring, Audio, staticFile } from "remotion";
import { SummaryContent } from "@/lib/script-types";
import { VIDEO_FPS } from "../shared";

const FPS = VIDEO_FPS;

interface Props {
  content: SummaryContent;
  audioDurationInFrames?: number;
  audioUrl?: string;
}

export const SummaryScene: React.FC<Props> = ({ content, audioDurationInFrames = 60, audioUrl }) => {
  const frame = useCurrentFrame();
  const points = Array.isArray(content.points) ? content.points : [];

  // Title: spring scale + glow
  const titleSpring = spring({
    frame,
    fps: FPS,
    from: 0,
    to: 1,
    config: { damping: 12, stiffness: 100 },
  });
  const glowPulse = Math.sin(frame * 0.06) * 0.15 + 0.85;

  // Card: fade + slide up
  const cardSpring = spring({
    frame,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 20,
    config: { damping: 14, stiffness: 80 },
  });

  // Decorative ring rotation
  const ring1Rotate = interpolate(frame, [0, 300], [0, 25], { extrapolateRight: "extend" });
  const ring2Rotate = interpolate(frame, [0, 300], [0, -15], { extrapolateRight: "extend" });

  // Decorative dots
  const dots = [
    { x: 100, y: 120, r: 6, color: "#FFD93D" },
    { x: 1820, y: 180, r: 8, color: "#4ECDC4" },
    { x: 80, y: 900, r: 5, color: "#FF6B9D" },
    { x: 1750, y: 850, r: 7, color: "#FFD93D" },
    { x: 960, y: 50, r: 4, color: "#95E1D3" },
    { x: 1600, y: 950, r: 6, color: "#4ECDC4" },
  ];
  const dotSpring = spring({
    frame,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 30,
    config: { damping: 15, stiffness: 90 },
  });

  if (points.length === 0) {
    return (
      <>
        {audioUrl && <Audio src={staticFile(audioUrl.replace(/^\//, ""))} />}
        <AbsoluteFill
          style={{
            background: "linear-gradient(135deg, #0f0c29 0%, #1a1a3e 40%, #24243e 100%)",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <div style={{ fontSize: 28, color: "#FF6B6B", fontFamily: "'Noto Sans SC', sans-serif" }}>
            总结内容格式错误，请重新生成
          </div>
        </AbsoluteFill>
      </>
    );
  }

  return (
    <>
      {audioUrl && <Audio src={staticFile(audioUrl.replace(/^\//, ""))} />}
      <AbsoluteFill
        style={{
          background: "linear-gradient(135deg, #0f0c29 0%, #1a1a3e 40%, #24243e 100%)",
          justifyContent: "center",
          alignItems: "center",
          overflow: "hidden",
          fontFamily: "'Poppins', 'Noto Sans SC', sans-serif",
        }}
      >
        {/* Background glow */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: 700,
            height: 700,
            background: "radial-gradient(circle, rgba(78,205,196,0.1) 0%, transparent 70%)",
            borderRadius: "50%",
            pointerEvents: "none",
          }}
        />

        {/* Decorative ring 1 */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: 500,
            height: 500,
            transform: `translate(-50%, -50%) rotate(${ring1Rotate}deg)`,
            borderRadius: "50%",
            border: "1px solid rgba(78,205,196,0.15)",
            pointerEvents: "none",
          }}
        />

        {/* Decorative ring 2 */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: 680,
            height: 680,
            transform: `translate(-50%, -50%) rotate(${ring2Rotate}deg)`,
            borderRadius: "50%",
            border: "1px dashed rgba(255,217,61,0.1)",
            pointerEvents: "none",
          }}
        />

        {/* Decorative dots */}
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
              opacity: dotSpring * 0.5,
              boxShadow: `0 0 ${dot.r * 2}px ${dot.color}`,
              pointerEvents: "none",
            }}
          />
        ))}

        {/* Title */}
        <div
          style={{
            fontSize: 56,
            fontWeight: 700,
            color: "#4ECDC4",
            textAlign: "center",
            marginBottom: 40,
            transform: `scale(${titleSpring})`,
            opacity: titleSpring,
            textShadow: `0 0 20px rgba(78,205,196,${glowPulse * 0.6})`,
            letterSpacing: 8,
          }}
        >
          今日要点
        </div>

        {/* Card container */}
        <div
          style={{
            width: "75%",
            maxWidth: 1100,
            background: "rgba(255,255,255,0.05)",
            backdropFilter: "blur(10px)",
            borderRadius: 24,
            padding: "40px 50px",
            border: "1px solid rgba(255,255,255,0.1)",
            boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
            transform: `translateY(${(1 - cardSpring) * 30}px)`,
            opacity: cardSpring,
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {points.map((point, index) => {
              const pointSpring = spring({
                frame,
                fps: FPS,
                from: 0,
                to: 1,
                delay: 40 + index * 15,
                config: { damping: 13, stiffness: 90 },
              });

              const numSpring = spring({
                frame,
                fps: FPS,
                from: 0,
                to: 1,
                delay: 40 + index * 15,
                config: { damping: 10, stiffness: 120 },
              });

              return (
                <div
                  key={index}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 20,
                    transform: `translateX(${(1 - pointSpring) * -40}px)`,
                    opacity: pointSpring,
                  }}
                >
                  {/* Number badge */}
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: "50%",
                      background: "linear-gradient(135deg, #FFD93D 0%, #FF9A3C 100%)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 22,
                      fontWeight: 800,
                      color: "#1a1a2e",
                      flexShrink: 0,
                      transform: `scale(${numSpring})`,
                      boxShadow: "0 0 15px rgba(255,217,61,0.4)",
                    }}
                  >
                    {index + 1}
                  </div>

                  {/* Point text */}
                  <div
                    style={{
                      fontSize: 28,
                      color: "#fff",
                      fontFamily: "'Noto Sans SC', sans-serif",
                      fontWeight: 500,
                      lineHeight: 1.5,
                      opacity: pointSpring,
                    }}
                  >
                    {point}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom accent line */}
        <div
          style={{
            position: "absolute",
            bottom: 60,
            left: "50%",
            transform: `translateX(-50%) scaleX(${cardSpring})`,
            width: 300,
            height: 2,
            background: "linear-gradient(90deg, transparent, #FFD93D, transparent)",
            opacity: 0.5,
          }}
        />
      </AbsoluteFill>
    </>
  );
};
