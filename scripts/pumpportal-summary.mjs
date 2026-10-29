/**
 * pumpportal-summary.mjs
 *
 * Pure aggregation helpers for the PumpPortal capture packet. Kept separate
 * from the websocket capture script so the tally logic can be exercised
 * without a live connection.
 *
 * Event data arrives from an external stream, so `mint`, `txType` and
 * `method` are untrusted strings. They are used as keys of the aggregate
 * maps below, therefore every accumulator is created with a null prototype:
 * a plain `{}` would resolve names such as `constructor` or `toString` to
 * inherited `Object.prototype` members (dropping the real entry) and would
 * let a `__proto__` key mutate the object's prototype instead of adding a
 * key. A null-prototype map has no inherited keys, so every string is an
 * ordinary own key.
 */

// Count events by their type/method label.
export function countEventTypes(events) {
  const typeCounts = Object.create(null);
  for (const e of events) {
    const t = e.data?.txType || e.data?.method || "unknown";
    typeCounts[t] = (typeCounts[t] || 0) + 1;
  }
  return typeCounts;
}

// Build the per-token summary index.
export function buildTokenIndex(events) {
  const tokenIndex = Object.create(null);
  for (const e of events) {
    const mint = e.data?.mint;
    if (!mint) continue;
    if (!Object.hasOwn(tokenIndex, mint)) {
      tokenIndex[mint] = {
        mint,
        name: e.data?.name || null,
        symbol: e.data?.symbol || null,
        first_seen: e.receivedAt,
        last_seen: e.receivedAt,
        event_count: 0,
        creates: 0,
        buys: 0,
        sells: 0,
        total_sol_volume: 0,
      };
    }
    const ti = tokenIndex[mint];
    ti.last_seen = e.receivedAt;
    ti.event_count++;
    if (e.data?.txType === "create") ti.creates++;
    if (e.data?.txType === "buy") {
      ti.buys++;
      ti.total_sol_volume += e.data?.solAmount || 0;
    }
    if (e.data?.txType === "sell") {
      ti.sells++;
      ti.total_sol_volume += e.data?.solAmount || 0;
    }
  }
  return tokenIndex;
}

// One-shot aggregation used by the capture finaliser.
export function summariseCapture(events) {
  const typeCounts = countEventTypes(events);
  const tokenIndex = buildTokenIndex(events);
  return { typeCounts, tokenIndex };
}
