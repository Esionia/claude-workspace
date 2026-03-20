import React from "react";
import { Composition, registerRoot } from "remotion";

// 注入 Google Fonts: Poppins (英文) + Noto Sans SC (中文)
if (typeof document !== "undefined") {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = "https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&family=Noto+Sans+SC:wght@400;500;600;700&display=swap";
  document.head.appendChild(link);
}
// import { DialogueVideo } from "./DialogueVideo";
// import type { DialogueVideoProps } from "./DialogueVideo";
import { TeachingVideo } from "./TeachingVideo";
// import { ShortVideo } from "./ShortVideo";
// import { TtsVideo } from "./TtsVideo";
// import type { VideoProps } from "./TtsVideo";
// import { VisualDialogueVideo } from "./VisualDialogueVideo";
import type { TeachingScript } from "@/lib/script-types";
// import type { ShortVideoProps, ShortVideoScript } from "@/lib/short-video-types";
// import type { DialogueLine, DialogueRole } from "@/lib/dialogue-types";
import { VIDEO_FPS } from "./shared";

// Remotion 4 的 Composition 泛型要求 Props extends Record<string, unknown>，
// 但具体组件的 props 接口有必需字段导致类型不兼容。
// 用 LooseComponent 包装避免 as any，同时保持 defaultProps 类型安全。
type LooseComponent<P> = React.FC<P> & React.FC<Record<string, unknown>>;

// 默认的教学脚本（用于 Remotion Studio 预览）
const defaultTeachingScript: TeachingScript = {
  id: "preview",
  topic: "Preview Teaching",
  description: "Preview teaching video for Remotion Studio",
  targetAudience: "beginners",
  totalDuration: 30,
  scenes: [
    {
      id: "scene-1",
      type: "cover",
      durationSeconds: 5,
      narration: "欢迎来到教学视频预览",
      narrationLang: "zh",
      content: {
        type: "cover",
        word: "Preview",
        translation: "预览",
      },
    },
  ],
  createdAt: new Date().toISOString(),
};

const RemotionRoot: React.FC = () => {
  // const dialogueDefaultProps: DialogueVideoProps = {
  //   dialogue: defaultDialogue,
  //   audioUrls: {},
  //   audioDurations: {},
  //   showChinese: true,
  // };

  const teachingDefaultProps = {
    script: defaultTeachingScript,
    audioUrls: {},
  };

  // const defaultShortVideoScript: ShortVideoScript = {
  //   id: "preview-short",
  //   topic: "Coffee Shop",
  //   category: "daily",
  //   cover: {
  //     title: "Coffee Chat",
  //     subtitle: "咖啡店日常对话",
  //     imagePrompt: "Two friends chatting in a cozy coffee shop",
  //   },
  //   roles: [
  //     { id: "A", name: "Emma", nameZh: "艾玛", voice: "en-US-JennyNeural", characterPrompt: "young woman with brown hair" },
  //     { id: "B", name: "Jack", nameZh: "杰克", voice: "en-US-GuyNeural", characterPrompt: "young man with short black hair" },
  //   ],
  //   lines: [
  //     { id: "line-1", roleId: "A", english: "Hi! What would you like to order?", chinese: "嗨！你想点什么？", scenePrompt: "coffee shop counter" },
  //     { id: "line-2", roleId: "B", english: "I'll have a latte, please.", chinese: "请给我一杯拿铁。", scenePrompt: "ordering at counter" },
  //   ],
  //   ending: {
  //     keyPhrases: [
  //       { english: "What would you like to order?", chinese: "你想点什么？" },
  //       { english: "I'll have a latte", chinese: "我要一杯拿铁" },
  //     ],
  //     callToAction: "Follow for more English tips!",
  //   },
  //   estimatedDuration: 30,
  // };

  // const shortVideoDefaultProps: ShortVideoProps = {
  //   script: defaultShortVideoScript,
  //   audioUrls: {},
  //   audioDurations: {},
  //   coverImageUrl: "",
  //   sceneVideoUrls: {},
  // };

  // const ttsDefaultProps: VideoProps = {
  //   text: "Hello, how are you?",
  //   lang: "en",
  //   audioUrl: undefined,
  // };

  // const visualDialogueDefaultProps = {
  //   lines: [
  //     { id: "1", roleId: "a", english: "Hello!", chinese: "你好！" },
  //     { id: "2", roleId: "b", english: "Hi there!", chinese: "嗨！" },
  //   ] as DialogueLine[],
  //   roles: [
  //     { id: "a", name: "Person A", nameZh: "角色A", avatar: "👤", voice: "en-US-JennyNeural" },
  //     { id: "b", name: "Person B", nameZh: "角色B", avatar: "👥", voice: "en-US-GuyNeural" },
  //   ] as DialogueRole[],
  //   audioUrls: {},
  //   audioDurations: {},
  // };

  return (
    <>
      {/* <Composition
        id="DialogueVideo"
        component={DialogueVideo as LooseComponent<DialogueVideoProps>}
        durationInFrames={300}
        fps={VIDEO_FPS}
        width={1920}
        height={1080}
        defaultProps={dialogueDefaultProps}
      /> */}
      <Composition
        id="TeachingVideo"
        component={TeachingVideo as LooseComponent<{script: TeachingScript; audioUrls?: Record<string, string>; backgroundMusicUrl?: string; backgroundMusicVolume?: number}>}
        durationInFrames={150}
        fps={VIDEO_FPS}
        width={1920}
        height={1080}
        defaultProps={teachingDefaultProps}
      />
      {/* <Composition
        id="ShortVideo"
        component={ShortVideo as LooseComponent<ShortVideoProps>}
        durationInFrames={300}
        fps={VIDEO_FPS}
        width={1080}
        height={1920}
        defaultProps={shortVideoDefaultProps}
      />
      <Composition
        id="TtsVideo"
        component={TtsVideo as LooseComponent<VideoProps>}
        durationInFrames={150}
        fps={VIDEO_FPS}
        width={1920}
        height={1080}
        defaultProps={ttsDefaultProps}
      />
      <Composition
        id="VisualDialogueVideo"
        component={VisualDialogueVideo as LooseComponent<typeof visualDialogueDefaultProps>}
        durationInFrames={300}
        fps={VIDEO_FPS}
        width={1920}
        height={1080}
        defaultProps={visualDialogueDefaultProps}
      /> */}
    </>
  );
};

registerRoot(RemotionRoot);
