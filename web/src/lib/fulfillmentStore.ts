export type FulfillmentEnvelope = {
  createdAt: number;
  baseName: string;
  resumeData: unknown;
};

const FULFILLMENT_TTL_SECONDS = 30 * 24 * 60 * 60;
const memoryStore = new Map<string, FulfillmentEnvelope>();

function storeKey(sessionId: string): string {
  return `atshacker:fulfillment:${sessionId}`;
}

function redisConfig(): { url: string; token: string } | null {
  const url = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) return null;
  return { url: url.replace(/\/$/, ''), token };
}

async function redisCommand(command: unknown[]): Promise<unknown> {
  const config = redisConfig();
  if (!config) return null;

  const response = await fetch(`${config.url}/pipeline`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${config.token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify([command]),
  });

  if (!response.ok) {
    throw new Error(`Fulfillment store returned ${response.status}`);
  }

  const payload = await response.json() as Array<{ result?: unknown; error?: string }>;
  const first = payload[0];
  if (first?.error) throw new Error(first.error);
  return first?.result ?? null;
}

export function buildFulfillmentBaseName(fileName: unknown): string {
  const rawName = typeof fileName === 'string' && fileName.trim() ? fileName.trim() : 'optimized_resume.pdf';
  return rawName
    .replace(/\.[a-z0-9]+$/i, '')
    .replace(/[^\w.-]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 80) + '_ats_optimized';
}

export async function readFulfillment(sessionId: string): Promise<FulfillmentEnvelope | null> {
  const normalizedSessionId = sessionId.trim();
  const cached = memoryStore.get(normalizedSessionId);
  if (cached) return cached;

  try {
    const result = await redisCommand(['GET', storeKey(normalizedSessionId)]);
    if (typeof result !== 'string') return null;
    const parsed = JSON.parse(result) as FulfillmentEnvelope;
    if (!parsed || typeof parsed !== 'object' || !parsed.resumeData || typeof parsed.baseName !== 'string') {
      return null;
    }
    memoryStore.set(normalizedSessionId, parsed);
    return parsed;
  } catch (error) {
    console.warn('Fulfillment store read failed:', error);
    return null;
  }
}

export async function writeFulfillment(sessionId: string, envelope: FulfillmentEnvelope): Promise<void> {
  const normalizedSessionId = sessionId.trim();
  memoryStore.set(normalizedSessionId, envelope);

  try {
    await redisCommand([
      'SET',
      storeKey(normalizedSessionId),
      JSON.stringify(envelope),
      'EX',
      FULFILLMENT_TTL_SECONDS,
    ]);
  } catch (error) {
    console.warn('Fulfillment store write failed:', error);
  }
}
