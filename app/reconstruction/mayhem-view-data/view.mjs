// Editable reconstruction of captured 457065's pure data boundary. Public names
// and the snapshot facade are local; provider acquisition and React scheduling
// are deliberately not implemented here. See README.md and PROVENANCE.json.
export const MAYHEM_MODES = ['auto', 'manual'];

// This complete update callback retains the original bindings, statements and
// key-enumeration behavior. `e` is the owning store's set capability, not a new
// store implementation. It receives either the old root or { byMint }.
export function createMayhemUpdate(e) {
  return (t, n) => e((e) => {
    let a = e.byMint[t],
      s = { state: n.state ?? a?.state, mode: n.mode ?? a?.mode };
    if (a && a.state === s.state && a.mode === s.mode) return e;
    let i = {};
    for (let n in e.byMint) n !== t && (i[n] = e.byMint[n]);
    i[t] = s;
    let r = Object.keys(i);
    if (r.length > 500)
      for (let e of r.slice(0, r.length - 500)) delete i[e];
    return { byMint: i };
  });
}

// Complete event callback, with the actual update capability supplied explicitly.
export function createMayhemEvent(e) {
  return (t) => { t?.mint && e(t.mint, { state: t.state, mode: t.mode }); };
}

export const isMayhemMode = (e) => void 0 !== e && MAYHEM_MODES.includes(e);
export function mayhemMint(e) { return e.mint; }
export function previousMayhemPage(e) { return Math.max(0, e - 1); }
export function newestMayhemFirst(e, t) {
  return (t.created_timestamp ?? 0) - (e.created_timestamp ?? 0);
}
export function largestMayhemFirst(e, t) {
  return (t.usd_market_cap ?? 0) - (e.usd_market_cap ?? 0);
}

// Each call is an explicit provider snapshot. Hydrated coins are the output of
// 609252.f (which already uses the separately recovered 493025.f normalizer).
// `marketActivity` is 849812.b's delivered by-mint record. `coinState` is the
// 653805 live store snapshot, and `byMint` is the mode/state store snapshot.
// The owning captured page supplies nonnegative integer pageIndex values.
export function deriveMayhemView({ data, hydratedCoins, marketActivity, byMint,
  coinState, sort, pageIndex, isLoading, isError, paused }) {
  const coins = data ?? [];
  const mints = coins.map(mayhemMint);
  const hydrationLimit = Math.max(1, mints.length), hydrationDisabled = 0 === mints.length;
  const hydration = { mints, limit: hydrationLimit, includeNsfw: true, disabled: hydrationDisabled };
  let modes;
  for (let coin of ((modes = new Map()), hydratedCoins)) {
    let mode = coin.mayhem?.mode;
    coin.mint && isMayhemMode(mode) && modes.set(coin.mint, mode);
  }
  const volume = (coin) => marketActivity[coin.mint]?.['24h']?.volumeUSD ?? 0;
  let ordered;
  switch (sort) {
    case 'volume': ordered = coins.toSorted((left, right) => volume(right) - volume(left)); break;
    case 'mcap': ordered = coins.toSorted(largestMayhemFirst); break;
    case 'newest': ordered = coins.toSorted(newestMayhemFirst); break;
    default: ordered = coins;
  }
  const pageCount = Math.max(1, Math.ceil(ordered.length / 10));
  const pageIndexCorrection = pageIndex > pageCount - 1 ? pageCount - 1 : undefined;
  const currentPage = Math.min(pageIndex, pageCount - 1);
  const pageCoins = ordered.slice(10 * currentPage, 10 * currentPage + 10);
  const visibleMints = pageCoins.map(mayhemMint);
  const body = isLoading ? 'loading' : isError ? 'error' : 0 === ordered.length ? 'empty' : 'rows';
  // G is invoked only in the rows branch. The subscription handoff above still
  // uses the computed page even when loading/error takes display precedence.
  const rows = body === 'rows' ? pageCoins.map((coin, index) => {
    const change = marketActivity[coin.mint]?.['24h'];
    const live = byMint[coin.mint];
    const liveMarketCap = coinState.coins[coin.mint]?.usdMarketCap;
    const marketCap = void 0 !== liveMarketCap ? liveMarketCap : (coin.usd_market_cap ?? 0);
    const modeFallback = modes.get(coin.mint);
    const mode = live?.mode ?? modeFallback;
    return {
      coin, rank: 10 * currentPage + index + 1, change, modeFallback,
      state: live?.state ?? coin.mayhem_state, mode, marketCap,
      marketCapPositive: marketCap > 0,
      modeTranslationKey: !mode ? undefined : mode === 'manual'
        ? 'web.mayhem.agent_mode_manual' : 'web.mayhem.agent_mode_auto',
      volumePresent: change?.volumeUSD != null,
      volumeUSD: change?.volumeUSD,
      createdTimestamp: coin.created_timestamp ?? 0,
      trendClass: (change?.priceChangePercent ?? 0) >= 0 ? 'text-gain' : 'text-loss',
      // Actual G telemetry uses the base response, not the live display cap.
      telemetryMarketCap: coin.usd_market_cap ?? 0,
    };
  }) : [];
  return {
    coins, mints, hydration, modes, ordered, pageCount, currentPage,
    pageIndexCorrection, pageCoins, visibleMints, subscribeVisible: visibleMints.length > 0,
    body, rows, refetchInterval: !paused && 10000,
    pagination: { visible: !(isLoading || isError || !(ordered.length > 10)),
      previousDisabled: currentPage === 0, nextDisabled: currentPage >= pageCount - 1 },
  };
}

// Captured next-button state updater closes over that render's page count.
export function nextMayhemPage(pageCount, index) { return Math.min(pageCount - 1, index + 1); }
