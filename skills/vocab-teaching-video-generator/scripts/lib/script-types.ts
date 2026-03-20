// 分镜脚本数据结构

// 场景类型
export type SceneType =
  | "title"           // 标题场景
  | "text-animation"  // 文字动画
  | "highlight"       // 高亮讲解
  | "comparison"      // 对比分屏
  | "example"         // 例句展示
  | "grammar-chart"   // 语法图表
  | "practice"        // 练习题
  | "summary"         // 总结
  | "vocabulary-card"; // 词汇卡片

// 单个分镜
export interface Scene {
  id: string;
  type: SceneType;
  title?: string;
  content: SceneContent;
  narration: string;        // 旁白文案
  narrationLang: "zh" | "en";
  durationSeconds: number;
  audioUrl?: string;        // TTS 生成的音频 URL
  audioDuration?: number;   // 音频时长（秒）
}

// 场景内容（根据类型不同）
export type SceneContent =
  | TitleContent
  | TextAnimationContent
  | HighlightContent
  | ComparisonContent
  | ExampleContent
  | GrammarChartContent
  | PracticeContent
  | SummaryContent
  | VocabularyCardContent;

// 标题场景
export interface TitleContent {
  type: "title";
  mainTitle: string;
  subtitle?: string;
}

// 文字动画场景
export interface TextAnimationContent {
  type: "text-animation";
  text: string;
  highlightWords?: string[];
  animation: "typewriter" | "fade-in" | "slide-up";
}

// 高亮讲解场景
export interface HighlightContent {
  type: "highlight";
  sentence: string;
  highlights: {
    text: string;
    color: string;
    label?: string;
  }[];
  // 场景相关图片（可选）
  images?: {
    url: string;           // 图片URL（支持本地路径或网络URL）
    alt: string;           // 图片描述
    position?: "top" | "center" | "bottom" | "left" | "right"; // 图片位置（默认 right）
    size?: "small" | "medium" | "large"; // 图片大小（默认 medium）
  }[];
  // 词根词缀详细信息（可选）
  rootAffix?: {
    root: string;           // 词根/词缀文本
    meaning: string;        // 含义
    label?: string;         // 类型标签："词根" | "前缀" | "后缀"（可选，不提供则自动判断）
    narration?: string;     // 该词根的讲解旁白（单独一句话）
    audioUrl?: string;      // 该词根讲解的音频 URL
    audioDuration?: number; // 该词根讲解的音频时长（秒）
    relatedWords: {         // 相关词汇
      word: string;         // 单词
      meaning: string;      // 含义
      highlight?: string;   // 需要高亮的部分（通常是词根）
      narration?: string;   // 该单词的讲解旁白（格式："[单词] 意思是 [中文含义]"）
      audioUrl?: string;    // 该单词讲解的音频 URL
      audioDuration?: number; // 该单词讲解的音频时长（秒）
    }[];
  }[];
}

// 对比分屏场景
export interface ComparisonContent {
  type: "comparison";
  left: {
    title: string;
    content: string;
    isCorrect?: boolean;
  };
  right: {
    title: string;
    content: string;
    isCorrect?: boolean;
  };
}

// 例句展示场景
export interface ExampleContent {
  type: "example";
  english: string;
  chinese: string;
  grammar?: string;
  // 高亮配置（用于突出目标词汇）
  highlights?: {
    text: string;        // 要高亮的文本
    color?: string;      // 颜色（默认 #FFD93D）
    effect?: "bounce" | "pulse" | "underline" | "glow"; // 动画效果（默认 bounce）
  }[];
  // 英文例句朗读音频（pocket-tts 生成）
  englishAudioUrl?: string;
  englishAudioDuration?: number;
  // 场景相关图片（可选）
  images?: {
    url: string;           // 图片URL（支持本地路径或网络URL）
    alt: string;           // 图片描述
    position?: "top" | "center" | "bottom" | "left" | "right"; // 图片位置（默认 bottom）
    size?: "small" | "medium" | "large"; // 图片大小（默认 medium）
  }[];
}

// 语法图表场景
export interface GrammarChartContent {
  type: "grammar-chart";
  title: string;
  rows: {
    label: string;
    formula: string;
    example?: string;
  }[];
}

// 练习题场景
export interface PracticeContent {
  type: "practice";
  question: string;
  options?: string[];
  answer: string;
  explanation?: string;
}

// 总结场景
export interface SummaryContent {
  type: "summary";
  points: string[];
}

// 词汇卡片场景（支持两种模式）
export interface VocabularyCardContent {
  type: "vocabulary-card";
  phrase: string;              // 短语/单词
  meaning: string;             // 中文释义（主要释义）

  // 定义模式（新增，替代 text-animation）
  partOfSpeech?: string;       // 词性：n. v. adj. 等
  definitions?: string[];      // 多个释义（用于定义模式）

  // 完整模式（现有，包含例句）
  example?: string;            // 英文例句
  exampleChinese?: string;     // 例句中文翻译

  // 音频支持
  phraseAudioUrl?: string;        // 短语发音音频
  phraseAudioDuration?: number;   // 短语音频时长（秒）
  exampleAudioUrl?: string;       // 例句朗读音频（仅在有 example 时使用）
  exampleAudioDuration?: number;  // 例句音频时长（秒）

  // 背景音乐（新增）
  backgroundMusicUrl?: string;    // 背景音乐 URL
  backgroundMusicVolume?: number; // 背景音乐音量（0-1，默认 0.3）
}

// 完整的教学视频脚本
export interface TeachingScript {
  id: string;
  topic: string;
  description: string;
  targetAudience: string;
  totalDuration: number;
  scenes: Scene[];
  createdAt: string;
}

// 示例脚本
export const exampleScript: TeachingScript = {
  id: "example-1",
  topic: "英语虚拟语气",
  description: "讲解英语中虚拟语气的用法",
  targetAudience: "高中生/大学生",
  totalDuration: 120,
  scenes: [
    {
      id: "scene-1",
      type: "title",
      content: {
        type: "title",
        mainTitle: "英语虚拟语气",
        subtitle: "Subjunctive Mood"
      },
      narration: "欢迎来到英语虚拟语气课程",
      narrationLang: "zh",
      durationSeconds: 5
    },
    {
      id: "scene-2",
      type: "text-animation",
      content: {
        type: "text-animation",
        text: "虚拟语气用于表达假设、愿望或与事实相反的情况",
        animation: "typewriter"
      },
      narration: "虚拟语气是英语中一种重要的语法结构，用于表达假设、愿望或与事实相反的情况。",
      narrationLang: "zh",
      durationSeconds: 8
    },
    {
      id: "scene-3",
      type: "comparison",
      content: {
        type: "comparison",
        left: {
          title: "真实条件句",
          content: "If it rains, I will stay home.",
          isCorrect: true
        },
        right: {
          title: "虚拟条件句",
          content: "If it rained, I would stay home.",
          isCorrect: true
        }
      },
      narration: "让我们对比一下真实条件句和虚拟条件句的区别。",
      narrationLang: "zh",
      durationSeconds: 10
    },
    {
      id: "scene-4",
      type: "highlight",
      content: {
        type: "highlight",
        sentence: "If I were you, I would study harder.",
        highlights: [
          { text: "were", color: "#FF6B6B", label: "过去式" },
          { text: "would", color: "#4ECDC4", label: "情态动词" }
        ]
      },
      narration: "注意这里用的是 were 而不是 was，这是虚拟语气的特殊用法。",
      narrationLang: "zh",
      durationSeconds: 10
    },
    {
      id: "scene-5",
      type: "grammar-chart",
      content: {
        type: "grammar-chart",
        title: "虚拟语气公式",
        rows: [
          { label: "与现在相反", formula: "If + 过去式, would + 动词原形", example: "If I had money, I would buy it." },
          { label: "与过去相反", formula: "If + had done, would have done", example: "If I had known, I would have helped." },
          { label: "与将来相反", formula: "If + should/were to, would + 动词原形", example: "If it should rain, we would cancel." }
        ]
      },
      narration: "这是虚拟语气的三种基本公式，分别对应与现在、过去和将来相反的情况。",
      narrationLang: "zh",
      durationSeconds: 15
    },
    {
      id: "scene-6",
      type: "summary",
      content: {
        type: "summary",
        points: [
          "虚拟语气表达假设或与事实相反",
          "与现在相反：If + 过去式",
          "与过去相反：If + had done",
          "注意 be 动词用 were"
        ]
      },
      narration: "让我们总结一下今天学习的内容。",
      narrationLang: "zh",
      durationSeconds: 10
    }
  ],
  createdAt: new Date().toISOString()
};

// 词汇教学示例脚本（带词根词缀讲解）
export const vocabularyExampleScript: TeachingScript = {
  id: "vocab-example-1",
  topic: "单词 transportation 的学习",
  description: "通过词根词缀法学习 transportation",
  targetAudience: "高中生/大学生",
  totalDuration: 60,
  scenes: [
    {
      id: "scene-1",
      type: "title",
      content: {
        type: "title",
        mainTitle: "Transportation",
        subtitle: "运输、交通"
      },
      narration: "今天我们来学习单词 transportation",
      narrationLang: "zh",
      durationSeconds: 3
    },
    {
      id: "scene-2",
      type: "text-animation",
      content: {
        type: "text-animation",
        text: "transportation (n.) 运输、交通工具",
        animation: "fade-in"
      },
      narration: "transportation 是一个名词，表示运输或交通工具。",
      narrationLang: "zh",
      durationSeconds: 4
    },
    {
      id: "scene-3",
      type: "highlight",
      content: {
        type: "highlight",
        sentence: "transportation = trans- + port + -ation",
        highlights: [
          { text: "trans-", color: "#FFD93D", label: "前缀" },
          { text: "port", color: "#4ECDC4", label: "词根" },
          { text: "-ation", color: "#FF6B6B", label: "后缀" }
        ],
        rootAffix: [
          {
            root: "trans-",
            meaning: "穿过、转移",
            label: "前缀",
            relatedWords: [
              { word: "transfer", meaning: "转移、调动", highlight: "trans" },
              { word: "transform", meaning: "转变、改造", highlight: "trans" },
              { word: "translate", meaning: "翻译", highlight: "trans" }
            ]
          },
          {
            root: "port",
            meaning: "携带、运输",
            label: "词根",
            relatedWords: [
              { word: "export", meaning: "出口", highlight: "port" },
              { word: "import", meaning: "进口", highlight: "port" },
              { word: "portable", meaning: "便携的", highlight: "port" }
            ]
          }
        ]
      },
      narration: "这个单词由前缀 trans-、词根 port 和后缀 -ation 组成。trans- 表示穿过、转移，port 表示携带、运输，-ation 是名词后缀。让我们看看其他使用这些词根的单词。",
      narrationLang: "zh",
      durationSeconds: 12
    },
    {
      id: "scene-4",
      type: "example",
      content: {
        type: "example",
        english: "Public transportation is very convenient in this city.",
        chinese: "这个城市的公共交通非常便利。"
      },
      narration: "Public transportation is very convenient in this city. 意思是：这个城市的公共交通非常便利。",
      narrationLang: "zh",
      durationSeconds: 6
    },
    {
      id: "scene-5",
      type: "summary",
      content: {
        type: "summary",
        points: [
          "transportation = trans-(穿过) + port(运输) + -ation(名词后缀)",
          "记住词根 trans- 和 port 可以帮助记忆很多单词",
          "例如：transfer, export, import, portable"
        ]
      },
      narration: "让我们总结一下今天学习的内容。",
      narrationLang: "zh",
      durationSeconds: 8
    }
  ],
  createdAt: new Date().toISOString()
};
