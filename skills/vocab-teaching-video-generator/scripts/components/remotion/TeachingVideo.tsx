"use client";

import React, { useMemo } from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import {
  Scene,
  TeachingScript,
  TitleContent,
  TextAnimationContent,
  HighlightContent,
  ComparisonContent,
  GrammarChartContent,
  SummaryContent,
  ExampleContent,
  PracticeContent,
  VocabularyCardContent,
} from "@/lib/script-types";
import { TitleScene } from "./scenes/TitleScene";
import { TextAnimationScene } from "./scenes/TextAnimationScene";
import { HighlightScene } from "./scenes/HighlightScene";
import { ComparisonScene } from "./scenes/ComparisonScene";
import { GrammarChartScene } from "./scenes/GrammarChartScene";
import { SummaryScene } from "./scenes/SummaryScene";
import { ExampleScene } from "./scenes/ExampleScene";
import { PracticeScene } from "./scenes/PracticeScene";
import { VocabularyCardScene } from "./scenes/VocabularyCardScene";
import { BackgroundMusic } from "./BackgroundMusic";
import { VIDEO_FPS, THEME_COLORS, resolveAudioSrc } from "./shared";

interface Props {
  script: TeachingScript;
  audioUrls?: Record<string, string>;
  backgroundMusicUrl?: string;    // 全局背景音乐 URL
  backgroundMusicVolume?: number; // 背景音乐音量（0-1）
}

export const FPS = VIDEO_FPS;

const DEFAULT_BGM = "audio/bgm/spark-of-inspiration.mp3";
const DEFAULT_BGM_VOLUME = 0.09;

// 渲染单个场景（利用判别联合类型，无 as any）
const renderScene = (scene: Scene, durationInFrames: number) => {
  const c = scene.content;
  switch (scene.type) {
    case "title":
      return <TitleScene content={c as TitleContent} audioUrl={scene.audioUrl} />;
    case "text-animation":
      return <TextAnimationScene content={c as TextAnimationContent} />;
    case "highlight": {
      const audioDur = scene.audioDuration || scene.durationSeconds || 5;
      return <HighlightScene content={c as HighlightContent} audioDurationInFrames={Math.round(audioDur * FPS)} />;
    }
    case "comparison":
      return <ComparisonScene content={c as ComparisonContent} />;
    case "grammar-chart":
      return <GrammarChartScene content={c as GrammarChartContent} />;
    case "summary": {
      const sc = c as SummaryContent;
      const audioDuration = scene.audioDuration || 3;
      return <SummaryScene content={sc} audioDurationInFrames={Math.round(audioDuration * FPS)} audioUrl={scene.audioUrl} />;
    }
    case "example": {
      const ec = c as ExampleContent;
      return <ExampleScene content={ec} englishAudioDuration={ec.englishAudioDuration} />;
    }
    case "practice":
      return <PracticeScene content={c as PracticeContent} />;
    case "vocabulary-card": {
      const vc = c as VocabularyCardContent;
      return (
        <VocabularyCardScene
          phrase={vc.phrase}
          meaning={vc.meaning}
          partOfSpeech={vc.partOfSpeech}
          definitions={vc.definitions}
          example={vc.example}
          exampleChinese={vc.exampleChinese}
          phraseAudioUrl={vc.phraseAudioUrl}
          phraseAudioDuration={vc.phraseAudioDuration}
          exampleAudioUrl={vc.exampleAudioUrl}
          exampleAudioDuration={vc.exampleAudioDuration}
          backgroundMusicUrl={vc.backgroundMusicUrl}
          backgroundMusicVolume={vc.backgroundMusicVolume}
          audioUrl={scene.audioUrl}
        />
      );
    }
    default:
      return (
        <AbsoluteFill
          style={{
            background: THEME_COLORS.bgPrimary,
            justifyContent: "center",
            alignItems: "center",
            color: "#fff",
            fontSize: 36,
          }}
        >
          未知场景类型: {scene.type}
        </AbsoluteFill>
      );
  }
};

export const TeachingVideo: React.FC<Props> = ({
  script,
  audioUrls = {},
  backgroundMusicUrl = DEFAULT_BGM,
  backgroundMusicVolume = DEFAULT_BGM_VOLUME,
}) => {
  // 用 useMemo 预计算帧偏移，避免 render 中 let 累加
  const sequences = useMemo(() => {
    let offset = 0;
    const result = script.scenes.map((scene) => {
      const startFrame = offset;
      const durationInFrames = Math.round((scene.durationSeconds || 5) * FPS);
      offset += durationInFrames;
      return { scene, startFrame, durationInFrames };
    });
    return result;
  }, [script.scenes]);

  return (
    <AbsoluteFill>
      {/* 全局背景音乐（贯穿所有场景，带淡入淡出） */}
      {backgroundMusicUrl && (
        <BackgroundMusic
          src={staticFile(backgroundMusicUrl)}
          volume={backgroundMusicVolume}
        />
      )}

      {sequences.map(({ scene, startFrame, durationInFrames }) => {
        // 检查是否为带英文音频的 example 场景
        const exContent =
          scene.type === 'example' && scene.content.type === 'example'
            ? (scene.content as ExampleContent)
            : null;
        const englishAudioUrl = exContent?.englishAudioUrl ?? null;
        const englishAudioDuration = exContent?.englishAudioDuration ?? 0;
        // 旁白延迟帧数 = 英文音频时长 + 0.5秒缓冲
        const narrationDelay = englishAudioUrl
          ? Math.round((englishAudioDuration + 0.5) * FPS)
          : 0;

        return (
          <Sequence
            key={scene.id}
            from={startFrame}
            durationInFrames={durationInFrames}
          >
            {renderScene(scene, durationInFrames)}

            {/* 英文例句朗读音频（场景开头播放） */}
            {englishAudioUrl && (
              <Audio src={resolveAudioSrc(englishAudioUrl)} />
            )}

            {/* 旁白音频（example 场景延迟播放，其他场景立即播放） */}
            {/* 优先使用 scene.audioUrl（TTS 生成器存储的），其次使用 audioUrls prop */}
            {(() => {
              const audioUrl = scene.audioUrl || audioUrls[scene.id];
              if (!audioUrl) return null;

              // Highlight 场景的引导语音频在场景开头播放
              // 每个词根的音频由 HighlightScene 组件内部控制
              if (scene.type === 'highlight') {
                return <Audio src={resolveAudioSrc(audioUrl)} />;
              }

              // Example 场景延迟播放旁白
              if (narrationDelay > 0) {
                return (
                  <Sequence from={narrationDelay}>
                    <Audio src={resolveAudioSrc(audioUrl)} />
                  </Sequence>
                );
              }

              // 其他场景立即播放
              return <Audio src={resolveAudioSrc(audioUrl)} />;
            })()}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

// 计算总帧数
export const calculateTotalFrames = (script: TeachingScript): number => {
  return script.scenes.reduce(
    (total, scene) => total + Math.round((scene.durationSeconds || 5) * FPS),
    0
  );
};

export default TeachingVideo;
