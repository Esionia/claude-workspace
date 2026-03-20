import type { CliArgs } from "../types";

export function getDefaultModel(): string {
  return (
    process.env.CLOUDFLARE_IMAGE_MODEL ||
    "@cf/black-forest-labs/flux-1-schnell"
  );
}

function getAccountId(): string {
  const id = process.env.CLOUDFLARE_ACCOUNT_ID;
  if (!id) throw new Error("CLOUDFLARE_ACCOUNT_ID is required");
  return id;
}

function getApiToken(): string {
  const token = process.env.CLOUDFLARE_API_TOKEN;
  if (!token) throw new Error("CLOUDFLARE_API_TOKEN is required");
  return token;
}

export async function generateImage(
  prompt: string,
  model: string,
  args: CliArgs
): Promise<Uint8Array> {
  const accountId = getAccountId();
  const token = getApiToken();

  const url = `https://api.cloudflare.com/client/v4/accounts/${accountId}/ai/run/${model}`;

  const body = JSON.stringify({ prompt });

  console.log(`Generating image with Cloudflare (${model})...`);

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body,
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Cloudflare API error (${res.status}): ${err}`);
  }

  const result = (await res.json()) as {
    result?: { image?: string };
    errors?: unknown[];
  };

  const imageData = result.result?.image;
  if (!imageData) {
    console.error("Response:", JSON.stringify(result, null, 2));
    throw new Error("No image in Cloudflare response");
  }

  // Image is base64-encoded
  return Uint8Array.from(Buffer.from(imageData, "base64"));
}
