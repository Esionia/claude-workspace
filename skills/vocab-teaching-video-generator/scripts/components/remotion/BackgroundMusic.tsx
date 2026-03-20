import React from "react";
import { Audio } from "remotion";

interface BackgroundMusicProps {
  src?: string;
  volume?: number;
}

export const BackgroundMusic: React.FC<BackgroundMusicProps> = ({
  src,
  volume = 0.1,
}) => {
  if (!src) return null;
  return <Audio src={src} volume={volume} startFrom={0} />;
};
