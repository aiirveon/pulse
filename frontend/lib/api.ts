const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

export async function classifyPost(content: string) {
  const res = await fetch(`${BASE_URL}/api/classify`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error(`Classify failed: ${res.status}`);
  return res.json();
}

export async function startFeed() {
  const res = await fetch(`${BASE_URL}/api/feed/start`, { method: "POST" });
  if (!res.ok) throw new Error(`Feed start failed: ${res.status}`);
  return res.json();
}

export async function getNextBatch(batchSize = 3) {
  const res = await fetch(`${BASE_URL}/api/feed/next?batch_size=${batchSize}`);
  if (!res.ok) throw new Error(`Feed next failed: ${res.status}`);
  return res.json();
}

export async function getStats() {
  const res = await fetch(`${BASE_URL}/api/stats`);
  if (!res.ok) throw new Error(`Stats failed: ${res.status}`);
  return res.json();
}
