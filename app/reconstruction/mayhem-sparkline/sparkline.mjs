// Captured Mayhem sparkline's recomputed data path, with explicit clock/query/
// history/render inputs. This facade does not recreate React memo scheduling or
// install a history service. Provider ports are the normalized 505835 deliveries.
export const CHART_DEFAULTS = { candleInterval: '1m', candleLimit: 60, timeframe: '1w', width: 72 };

export function isYoungCoin(e, t = Date.now()) {
  return !!Number.isFinite(e) && !(e <= 0) && 3600000 >= Math.max(0, t - e);
}
export function youngCandleWindow(e, t = Date.now()) {
  let i = Math.max(0, t - e);
  return i < 300000 ? { interval: '1s', limit: 300 }
    : i < 900000 ? { interval: '15s', limit: 65 }
      : i < 1800000 ? { interval: '30s', limit: 65 } : { interval: '1m', limit: 65 };
}
export function defaultLineWindow(e, t = Date.now()) {
  return {
    timeframe: (() => {
      if (!Number.isFinite(e) || e <= 0) return CHART_DEFAULTS.timeframe;
      let i = Math.max(0, t - e);
      return i < 300000 ? '1m' : i < 900000 ? '5m' : i < 3600000 ? '15m'
        : i < 21600000 ? '30m' : i < 86400000 ? '6h' : i < 172800000 ? '24h' : '1w';
    })(),
    width: (() => {
      if (!Number.isFinite(e) || e <= 0) return CHART_DEFAULTS.width;
      let i = Math.max(0, t - e);
      return i < 300000 ? 24 : i < 900000 ? 28 : i < 1800000 ? 32 : i < 3600000 ? 52
        : i < 21600000 ? 64 : i < 86400000 ? 68 : i < 172800000 ? 72 : CHART_DEFAULTS.width;
    })(),
  };
}

const durations = { s: 1000, m: 60000, h: 3600000, d: 86400000,
  w: 604800000, mo: 2592000000, y: 31536000000 };
const resolutions = { '1s': 1000, '15s': 15000, '30s': 30000, '1m': 60000,
  '5m': 300000, '15m': 900000, '1h': 3600000, '4h': 14400000, '1d': 86400000 };
export function lineParameters({ createdTs, timeframe, width, nowMs = Date.now() }) {
  const match = /^(\d+)\s*(mo|[smhdwy])$/i.exec(timeframe.trim());
  const unit = match ? durations[match[2].toLowerCase()] : undefined;
  const window = match && unit ? Number(match[1]) * unit : null;
  if (window === null) return null;
  const span = nowMs - Math.max(nowMs - window, Number.isFinite(createdTs) && createdTs > 0 ? createdTs : 0);
  const res = Object.keys(resolutions).find((key) => span / resolutions[key] <= 300) ?? '1d';
  return { res, count: Math.min(300, Math.max(1, Math.ceil(span / resolutions[res]))),
    maxPoints: Math.min(2000, Math.max(2, Number.isFinite(width) ? Math.round(width) : 0)) };
}

// The two history capabilities are actual 505835.Z/x normalized return shapes,
// not HTTP response objects: { candles } and { points }. resolveChain is U.
export function createSparklineReader({ resolveChain, readCandleHistory, readLineHistory, now = Date.now }) {
  async function readCandles({ coinAddress, chainId, fetchOptions,
    interval = CHART_DEFAULTS.candleInterval, limit = CHART_DEFAULTS.candleLimit, to }) {
    const chain = resolveChain({ mint: coinAddress, chainId });
    if (!chain) throw Error('Failed to fetch coin candles');
    return (await readCandleHistory({ chainId: chain, address: coinAddress, interval,
      measure: 'price_usd', count: limit,
      beforeTs: void 0 !== to ? Math.floor(to) + 1 : void 0, init: fetchOptions,
    })).candles.map((e) => ({ timestamp: e.timestamp, open: String(e.open), high: String(e.high),
      low: String(e.low), close: String(e.close), volume: String(e.volume) }));
  }
  async function readLine({ coinAddress, coinCreatedTimestamp, chainId, fetchOptions,
    timeframe = CHART_DEFAULTS.timeframe, width = CHART_DEFAULTS.width }) {
    const chain = resolveChain({ mint: coinAddress, chainId });
    const params = lineParameters({ createdTs: coinCreatedTimestamp, timeframe, width, nowMs: now() });
    if (!chain || !params) throw Error(`Failed to fetch coin line chart: ${timeframe}`);
    return (await readLineHistory({ chainId: chain, address: coinAddress, ...params,
      measure: 'price_usd', init: fetchOptions })).points;
  }
  return async ({ coinAddress, coinCreatedTimestamp, chainId, fetchOptions,
    timeframe, width, youngCoinSource = 'candles' }) => {
    if ('candles' === youngCoinSource && isYoungCoin(coinCreatedTimestamp, now())) {
      const { interval, limit } = youngCandleWindow(coinCreatedTimestamp, now());
      const candles = readCandles({ coinAddress, coinCreatedTimestamp, chainId, interval, limit, fetchOptions });
      return (await candles).map((e) => ({ time: e.timestamp, price: Number(e.close) }))
        .filter((e) => Number.isFinite(e.time) && Number.isFinite(e.price) && e.price >= 0);
    }
    const defaults = defaultLineWindow(coinCreatedTimestamp, now());
    return readLine({ coinAddress, coinCreatedTimestamp, chainId, fetchOptions,
      timeframe: timeframe ?? defaults.timeframe, width: width ?? defaults.width });
  };
}

// One recomputation of 375676.f. In the captured hook, compiler memo caches
// decide when this computation runs; callers must not infer automatic age-based
// key changes or React scheduling from this explicit snapshot facade.
export function planSparklineQuery({ coinAddress, coinCreatedTimestamp, chainId,
  timeframe, width, queryOptions, youngCoinSource = 'candles' }, { readSparkline, now = Date.now }) {
  const young = 'candles' === youngCoinSource && isYoungCoin(coinCreatedTimestamp, now());
  const defaults = defaultLineWindow(coinCreatedTimestamp, now());
  const candles = young ? youngCandleWindow(coinCreatedTimestamp, now()) : null;
  const resolvedTimeframe = timeframe ?? defaults.timeframe, resolvedWidth = width ?? defaults.width;
  const eligible = !!coinAddress && (chainId === 'ton:-239' ||
    typeof coinCreatedTimestamp === 'number' && Number.isFinite(coinCreatedTimestamp) && coinCreatedTimestamp > 0);
  const { enabled, ...rest } = queryOptions ?? {};
  const queryFn = () => readSparkline({ coinAddress, coinCreatedTimestamp, chainId,
    timeframe: resolvedTimeframe, width: resolvedWidth, youngCoinSource });
  const queryKey = young
    ? ['coinCandles', coinAddress, coinCreatedTimestamp, candles.interval, candles.limit, 'sparklineLineChartPoints', chainId ?? null]
    : ['coinLineChart', coinAddress, coinCreatedTimestamp, resolvedTimeframe, resolvedWidth, 'sparklineLineChartPoints', chainId ?? null];
  return { queryFn, queryKey, ...rest, enabled: eligible && (enabled ?? true) };
}

export function sparklineRefetchInterval(e) { return (e.state.data?.length ?? 0) <= 1 && 10000; }

// Actual parent h inputs/options. Its clock is the adjusted 668487.t capability,
// distinct from the raw Date.now used by 693908/628731/provider planning above.
export function mayhemSparklineInput({ mint, createdTimestamp, chainId }, adjustedNow) {
  let timeframe;
  if (Number.isFinite(createdTimestamp) && createdTimestamp > 0) {
    const age = adjustedNow() - createdTimestamp;
    timeframe = age < 21600000 ? '6h' : age < 86400000 ? '24h' : '1w';
  }
  return { coinAddress: mint, coinCreatedTimestamp: createdTimestamp, chainId, timeframe,
    queryOptions: { enabled: createdTimestamp > 0, staleTime: 300000, gcTime: 600000, refetchInterval: sparklineRefetchInterval } };
}

// Complete SVG/placeholder data with the actual JSX and class-merge operations
// supplied as capabilities. The id is the owning React useId result; no ID or
// HTML serialization policy is invented here.
export function renderMayhemSparkline({ data, id, colorClassName, className }, { jsx, jsxs, mergeClassNames }) {
  let line;
  if (!data || data.length <= 1) line = null;
  else {
    const prices = data.map((e) => e.price), min = Math.min(...prices), range = Math.max(...prices) - min || 1;
    line = `M${prices.map((price, i) => `${i / (prices.length - 1) * 100},${100 - (price - min) / range * 80 - 10}`).join(' L')}`;
  }
  if (!line) return jsx('div', { className: mergeClassNames('h-12 w-full', className), 'aria-hidden': true });
  const fill = `${line} L100,100 L0,100 Z`;
  return jsxs('svg', { viewBox: '0 0 100 100', preserveAspectRatio: 'none',
    className: mergeClassNames('h-12 w-full', colorClassName, className), 'aria-hidden': true,
    children: [jsx('defs', { children: jsxs('linearGradient', { id, x1: '0', y1: '0', x2: '0', y2: '1',
      children: [jsx('stop', { offset: '0%', stopColor: 'currentColor', stopOpacity: 0.28 }),
        jsx('stop', { offset: '100%', stopColor: 'currentColor', stopOpacity: 0 })] }) }),
    jsx('path', { d: fill, fill: `url(#${id})`, stroke: 'none' }),
    jsx('path', { d: line, fill: 'none', stroke: 'currentColor', strokeWidth: 1.5, vectorEffect: 'non-scaling-stroke' })] });
}

// Local explicit recomputation composition, not a mounted React component.
// getQueryResult accepts the source query descriptor; useId runs even when the
// delivered data selects the placeholder. Neither capability is implemented here.
export function createMayhemSparkline({ adjustedNow, getQueryResult, useId, readSparkline,
  now = Date.now, jsx, jsxs, mergeClassNames }) {
  return (props) => {
    const input = mayhemSparklineInput(props, adjustedNow);
    const { data } = getQueryResult(planSparklineQuery(input, { readSparkline, now }));
    const id = useId();
    return renderMayhemSparkline({ data, id, className: props.className,
      colorClassName: props.colorClassName }, { jsx, jsxs, mergeClassNames });
  };
}
