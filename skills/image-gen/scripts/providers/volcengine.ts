import type { CliArgs } from "../types";

export function getDefaultModel(): string {
  return process.env.VOLCENGINE_IMAGE_MODEL || "doubao-seedream-5-0-260128";
}

function getApiKey(): string | null {
  return process.env.VOLCENGINE_API_KEY || null;
}

function getBaseUrl(): string {
  const base = process.env.VOLCENGINE_BASE_URL || "https://ark.cn-beijing.volces.com";
  return base.replace(/\/+$/g, "");
}

function parseAspectRatio(ar: string): { width: number; height: number } | null {
  const match = ar.match(/^(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)$/);
  if (!match) return null;
  const w = parseFloat(match[1]!);
  const h = parseFloat(match[2]!);
  if (w <= 0 || h <= 0) return null;
  return { width: w, height: h };
}

function getSizeFromAspectRatio(ar: string | null, quality: CliArgs["quality"]): string {
  const baseSize = quality === "2k" ? 2048 : 1024;

  if (!ar) return `${baseSize}x${baseSize}`;

  const parsed = parseAspectRatio(ar);
  if (!parsed) return `${baseSize}x${baseSize}`;

  const ratio = parsed.width / parsed.height;

  if (Math.abs(ratio - 1) < 0.1) {
    return `${baseSize}x${baseSize}`;
  }

  if (ratio > 1) {
    const w = Math.round(baseSize * ratio);
    return `${w}x${baseSize}`;
  }

  const h = Math.round(baseSize / ratio);
  return `${baseSize}x${h}`;
}

export async function generateImage(
  prompt: string,
  model: string,
  args: CliArgs
): Promise<Uint8Array> {
  const apiKey = getApiKey();
  if (!apiKey) throw new Error("VOLCENGINE_API_KEY is required");

  const size = args.size || getSizeFromAspectRatio(args.aspectRatio, args.quality);
  const url = `${getBaseUrl()}/api/v3/images/generations`;

  const body = {
    model,
    prompt,
    size,
    n: args.n || 1,
  };

  console.log(`Generating image with Volcengine (${model})...`, { size });

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Volcengine API error (${res.status}): ${err}`);
  }

  const result = await res.json() as {
    data?: Array<{ url?: string; b64_json?: string }>;
    output?: {
      images?: Array<{ url?: string; b64_json?: string }>;
    };
  };

  let imageData: string | null = null;

  // Try different response formats
  if (result.data?.[0]?.b64_json) {
    imageData = result.data[0].b64_json;
  } else if (result.data?.[0]?.url) {
    imageData = result.data[0].url;
  } else if (result.output?.images?.[0]?.b64_json) {
    imageData = result.output.images[0].b64_json;
  } else if (result.output?.images?.[0]?.url) {
    imageData = result.output.images[0].url;
  }

  if (!imageData) {
    console.error("Response:", JSON.stringify(result, null, 2));
    throw new Error("No image in response");
  }

  if (imageData.startsWith("http://") || imageData.startsWith("https://")) {
    const imgRes = await fetch(imageData);
    if (!imgRes.ok) throw new Error("Failed to download image");
    const buf = await imgRes.arrayBuffer();
    return new Uint8Array(buf);
  }

  return Uint8Array.from(Buffer.from(imageData, "base64"));
}
