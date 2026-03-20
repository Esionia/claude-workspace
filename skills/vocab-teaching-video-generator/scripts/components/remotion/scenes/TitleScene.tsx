"use client";

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Audio, staticFile } from "remotion";
import { TitleContent } from "@/lib/script-types";

interface Props {
  content: TitleContent;
  audioUrl?: string;
}

export const TitleScene: React.FC<Props> = ({ content, audioUrl }) => {
  const frame = useCurrentFrame();

  const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  const titleScale = interpolate(frame, [0, 20], [0.8, 1], {
    extrapolateRight: "clamp",
  });

  const subtitleOpacity = interpolate(frame, [15, 35], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <>
      {audioUrl && <Audio src={staticFile(audioUrl.replace(/^\//, ""))} />}
      <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        gap: 20,
      }}
    >
      <div
        style={{
          fontSize: 72,
          fontWeight: "bold",
          color: "#4ECDC4",
          fontFamily: "'Microsoft YaHei', sans-serif",
          opacity: titleOpacity,
          transform: `scale(${titleScale})`,
          textAlign: "center",
        }}
      >
        {content.mainTitle}
      </div>

      {content.subtitle && (
        <div
          style={{
            fontSize: 36,
            color: "#888",
            fontFamily: "Arial, sans-serif",
            opacity: subtitleOpacity,
          }}
        >
          {content.subtitle}
        </div>
      )}
    </AbsoluteFill>
    </>
  );
};
