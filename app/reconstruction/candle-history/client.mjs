// Editable 505835.Z/x history-client boundary. Destination and fetch capabilities
// are supplied by the host; this module has no production-network default.
export class CandleHistoryFetchError extends Error {
  status;
  fallback;
  constructor(message, status, fallback = null) {
    super(message);
    this.name = 'CandleHistoryFetchError'; this.status = status; this.fallback = fallback;
  }
}
export const HISTORY_COUNT_LIMIT = 300;
export const CAPTURED_RETRY_DELAYS = [300, 900]; // Exported source value, NOT the request default.
const bucket = (size) => (time) => Math.floor(time / size) * size;
export function utcWeekStart(time) {
  const date = new Date(time), day = date.getUTCDay();
  return Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()) - ((day + 6) % 7) * 86400000;
}
const direct = (res) => ({ res, bars: 1 });
export const INTERVALS = {
  '1s': direct('1s'), '15s': direct('15s'), '30s': direct('30s'), '1m': direct('1m'),
  '5m': direct('5m'), '15m': direct('15m'),
  '30m': { res: '15m', bars: 2, bucketStart: bucket(1800000) },
  '1h': direct('1h'), '4h': direct('4h'), '6h': direct('4h'),
  '12h': { res: '4h', bars: 3, bucketStart: bucket(43200000) },
  '24h': direct('1d'), '1d': direct('1d'),
  '1w': { res: '1d', bars: 7, bucketStart: utcWeekStart },
};
const beforeCursor = (value) => void 0 !== value && value > 0 ? Math.floor(value) - 1 : void 0;
const candlePath = (base, chain, address) => `${base.replace(/\/+$/, '')}/candles/${chain}/${encodeURIComponent(address)}`;

export function buildCandleUrl({ chainId, address, interval, measure, beforeTs,
  count = HISTORY_COUNT_LIMIT, baseUrl }) {
  const { res, bars } = INTERVALS[interval];
  const parts = [`res=${res}`, `count=${Math.min(Math.max(1, Math.ceil(count * bars)), HISTORY_COUNT_LIMIT)}`, `measure=${measure}`];
  const to = beforeCursor(beforeTs);
  if (void 0 !== to) parts.push(`to=${to}`);
  return `${candlePath(baseUrl, chainId, address)}?${parts.join('&')}`;
}
export function buildLineUrl({ chainId, address, res, count, maxPoints, measure, beforeTs, baseUrl }) {
  const parts = [`res=${res}`, `count=${Math.min(Math.max(1, Math.ceil(count)), HISTORY_COUNT_LIMIT)}`,
    `maxPoints=${Math.min(Math.max(2, Math.round(maxPoints)), 2000)}`, `measure=${measure}`];
  const to = beforeCursor(beforeTs);
  if (void 0 !== to) parts.push(`to=${to}`);
  return `${candlePath(baseUrl, chainId, address)}/line?${parts.join('&')}`;
}

export const isCandlePage = (value) => 'object' == typeof value && null !== value &&
  Array.isArray(value.candles) && 'boolean' == typeof value.hasOlder && 'string' == typeof value.served?.res;
export const isLinePage = (value) => 'object' == typeof value && null !== value &&
  Array.isArray(value.points) && 'string' == typeof value.served?.res;

async function attempt(url, fetchImpl, init, isBody) {
  let response, body, status;
  try { response = await fetchImpl(url, init); }
  catch (error) {
    if (error?.name === 'AbortError') throw error;
    return { ok: false, error: new CandleHistoryFetchError(error instanceof Error ? error.message : 'candle history fetch failed', null), retryable: true };
  }
  if (false === response.ok) return { ok: false,
    error: new CandleHistoryFetchError(`candle history responded ${response.status}`, response.status),
    retryable: 429 === (status = response.status) || status >= 500 };
  try { body = await response.json(); }
  catch { return { ok: false, error: new CandleHistoryFetchError('candle history body was not JSON', response.status), retryable: true }; }
  return isBody(body) ? { ok: true, body } : { ok: false,
    error: new CandleHistoryFetchError('candle history body was not a candle page', response.status), retryable: true };
}
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Complete retry/optional-relay operation. Explicit ports correspond to the
// captured fetch / relayFetchImpl capabilities; there is no ambient fetch here.
export async function requestHistory(url, isBody, { fetchImpl, init, relay = false,
  relayFetchImpl, retryDelaysMs = [], sleep = wait, onRelayServed }) {
  const relayUrl = relay ? (() => {
    let parsed;
    try { parsed = new URL(url); } catch { return; }
    return `/api/swap-api${parsed.pathname}${parsed.search}`;
  })() : undefined;
  let primaryError = null, relayError = null;
  for (let index = 0; index <= retryDelaysMs.length; index++) {
    if (index > 0) await sleep(retryDelaysMs[index - 1]);
    const primary = await attempt(url, fetchImpl, init, isBody);
    if (primary.ok) return primary.body;
    primaryError = primary.error;
    if (null === primary.error.status && relayUrl) {
      const fallback = await attempt(relayUrl, relayFetchImpl, init, isBody);
      if (fallback.ok) { onRelayServed?.({ attempt: index }); return fallback.body; }
      relayError = fallback.error;
    }
    if (!primary.retryable) break;
  }
  throw new CandleHistoryFetchError(primaryError?.message ?? 'candle history fetch failed', primaryError?.status ?? null,
    relayError ? { status: relayError.status, message: relayError.message } : null);
}

const positive = (value) => { const n = Number(value); return Number.isFinite(n) && n > 0 ? n : null; };
const parseSupplyUsed = (value) => {
  if (typeof value !== 'string' || value.trim() === '') return;
  const n = Number(value); return Number.isFinite(n) && n > 0 ? n : undefined;
};
// Actual 771073.Z delivery decoder, including volumeUsd's distinct fallback.
export function decodeCandle(value) {
  const open = positive(value.open), high = positive(value.high), low = positive(value.low), close = positive(value.close);
  return null !== open && null !== high && null !== low && null !== close && Number.isFinite(value.openTimeMs)
    ? { timestamp: value.openTimeMs, open, high, low, close, volume: Number(value.volumeUsd) || 0 } : null;
}
export function normalizeCandlePage(page, interval) {
  const { res, bucketStart } = INTERVALS[interval], servedRes = page.served.res;
  const supply = parseSupplyUsed(page.supplyUsed);
  if (servedRes !== res) return { candles: [], hasOlder: false, servedRes, intervalMismatch: true, supplyUsed: supply };
  const byTime = new Map();
  for (const raw of page.candles) { const candle = decodeCandle(raw); if (candle) byTime.set(candle.timestamp, candle); }
  const ordered = Array.from(byTime.values()).sort((a, b) => a.timestamp - b.timestamp);
  if (!bucketStart) return { candles: ordered, hasOlder: page.hasOlder, servedRes, intervalMismatch: false, supplyUsed: supply };
  const grouped = new Map();
  for (const candle of [...ordered].sort((a, b) => a.timestamp - b.timestamp)) {
    const time = bucketStart(candle.timestamp), existing = grouped.get(time);
    if (!existing) { grouped.set(time, { ...candle, timestamp: time }); continue; }
    existing.high = Math.max(existing.high, candle.high); existing.low = Math.min(existing.low, candle.low);
    existing.close = candle.close; existing.volume = Number(existing.volume) + Number(candle.volume);
  }
  const candles = Array.from(grouped.values()).sort((a, b) => a.timestamp - b.timestamp);
  return { candles: page.hasOlder && candles.length > 1 ? candles.slice(1) : candles,
    hasOlder: page.hasOlder, servedRes, intervalMismatch: false, supplyUsed: supply };
}
export function normalizeLinePage(page, expectedRes) {
  const servedRes = page.served.res, barCount = page.points.length;
  return servedRes !== expectedRes ? { points: [], barCount, servedRes, intervalMismatch: true } : {
    points: page.points.flatMap((point) => {
      const price = Number(point.price);
      return Number.isFinite(point.time) && Number.isFinite(price) && price > 0 ? [{ time: point.time, price }] : [];
    }).sort((a, b) => a.time - b.time), barCount, servedRes, intervalMismatch: false,
  };
}

// Complete Z/x read operations on an explicitly configured input. Z reads the
// interval again after awaiting delivery, just as the captured operation does.
export async function readCandleHistory(input) {
  return normalizeCandlePage(await requestHistory(buildCandleUrl(input), isCandlePage, input), input.interval);
}
export async function readLineHistory({ chainId, address, res, count, maxPoints, measure, beforeTs, baseUrl, ...rest }) {
  return normalizeLinePage(await requestHistory(buildLineUrl({ baseUrl, chainId, address, res, count, maxPoints,
    measure, beforeTs }), isLinePage, rest), res);
}

// Local host facade: a caller-selected destination and BOTH fetch capabilities
// replace the source's ambient origin/global fetch defaults. Per-call source
// options retain their semantics; undefined selects these explicit host ports.
export function createCandleHistoryClient({ baseUrl, fetchImpl, relayFetchImpl }) {
  if (typeof baseUrl !== 'string' || typeof fetchImpl !== 'function' || typeof relayFetchImpl !== 'function')
    throw new TypeError('explicit baseUrl, fetchImpl and relayFetchImpl are required');
  const ports = (options) => ({ ...options,
    baseUrl: options.baseUrl === undefined ? baseUrl : options.baseUrl,
    fetchImpl: options.fetchImpl === undefined ? fetchImpl : options.fetchImpl,
    relayFetchImpl: options.relayFetchImpl === undefined ? relayFetchImpl : options.relayFetchImpl });
  return {
    candles: (options) => readCandleHistory(ports(options)),
    line: (options) => readLineHistory(ports(options)),
  };
}
