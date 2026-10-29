/** Source-adapted 503774.q/d/$ boundary; no fetch, clock service or DTO validation. */
const PROGRAMS = new Set([
  "pump",
  "meteora_dbc",
  "raydium_launchpad",
  "raydium_launchpad_bonk",
  "loadout",
  "meme_fun",
  "stonkfun",
  "raydium_cpmm",
]);

export function createBoardResponseAdapter({
  nowMs,
  isEvmRecord,
  retainChainId,
}) {
  if (
    [nowMs, isEvmRecord, retainChainId].some(
      (port) => typeof port !== "function",
    )
  )
    throw new TypeError(
      "Explicit clock, EVM-classification and chain-retention ports are required",
    );
  // One instance models one captured module lifetime, including its shared cache.
  const timestamps = new Map();
  function evictOldest() {
    if (timestamps.size >= 4000) {
      const first = timestamps.keys().next().value;
      if (first !== undefined) timestamps.delete(first);
    }
  }
  function createdAt(entry, clock) {
    if (typeof entry.age !== "number" || !Number.isFinite(entry.age))
      return null;
    const value = clock - 1000 * entry.age;
    const mint = entry.m;
    if (!mint) return value;
    const previous = timestamps.get(mint);
    if (previous !== undefined && Math.abs(previous - value) < 60000)
      return previous;
    // Preserve eviction BEFORE deleting/replacing this mint, even at capacity.
    evictOldest();
    timestamps.delete(mint);
    timestamps.set(mint, value);
    return value;
  }
  function programFor(raw, evm, board) {
    if (PROGRAMS.has(raw)) return raw;
    if (raw === undefined || raw === "" || raw === "pump_amm") return "pump";
    return evm || board !== "trending" ? "pump" : "non_launchpad";
  }
  function holderCount(raw, evm) {
    const value =
      typeof raw === "number" && Number.isFinite(raw) ? raw : undefined;
    return evm && !value ? undefined : value;
  }
  function coin(entry, options) {
    // The captured fallback clock is evaluated even when age will be invalid.
    const created = createdAt(entry, options.nowMs ?? nowMs());
    const evm = isEvmRecord({ mint: entry.m ?? "", chainId: entry.c });
    const result = {
      mint: entry.m ?? "",
      name: entry.n ?? "",
      symbol: entry.t ?? "",
      image_uri: entry.i ?? "",
      usd_market_cap: typeof entry.mc === "number" ? entry.mc : 0,
      created_timestamp: created,
      complete: (entry.gd ?? 0) > 0,
      platform: entry.pl,
      creator: entry.dw ?? "",
      is_currently_live: entry.lv === true,
      description: entry.desc ?? "",
      video_uri: entry.vid ?? "",
      associated_bonding_curve: "",
      bonding_curve: "",
      hidden: null,
      hide_banner: false,
      is_banned: false,
      last_trade_timestamp: null,
      livestream_ban_expiry: 0,
      market_cap: 0,
      metadata_uri: "",
      nsfw: false,
      program: programFor(entry.pg, evm, options.board),
      board_program: entry.pg ?? "",
      holder_count: holderCount(entry.nh, evm),
      raydium_pool: "",
      show_name: true,
      total_supply: 0,
      virtual_sol_reserves: 0,
      virtual_token_reserves: 0,
    };
    if (entry.ic === true) result.is_charity = true;
    if (entry.hr === true) result.is_holder_reward = true;
    if (entry.rid) result.rec_id = entry.rid;
    if (options.servedRank !== undefined) result.rec_rank = options.servedRank;
    if (entry.ms) result.mayhem_state = entry.ms;
    if (entry.mp === true) result.mayhem_is_multiplayer = true;
    if (retainChainId(entry.c)) result.chain_id = entry.c;
    if (entry.pg && evm) result.protocol = entry.pg;
    if (entry.lp) result.board_launchpad = entry.lp;
    if (entry.fh !== undefined) {
      const followed = entry.fh;
      result.followed_holders =
        followed === null
          ? null
          : {
              totalCount: followed.totalCount,
              holders: followed.holders.map((holder) => ({
                ...holder,
                verifiedBadgeVisible: holder.verifiedBadgeVisible ?? true,
                walletAddress: holder.walletAddress ?? null,
              })),
            };
    }
    return result;
  }
  return {
    mapCoins(response, servedRankOffset) {
      if (!response || !Array.isArray(response.entries)) return [];
      const serverTime =
        typeof response.serverTs === "number" &&
        Number.isFinite(response.serverTs) &&
        response.serverTs > 0
          ? response.serverTs
          : undefined;
      return response.entries.map((entry, index) =>
        coin(entry, {
          nowMs: serverTime,
          board: response.board,
          servedRank:
            servedRankOffset === undefined
              ? undefined
              : servedRankOffset + index + 1,
        }),
      );
    },
    seedTimestamps(coins) {
      for (const entry of coins) {
        const created = entry.created_timestamp;
        if (
          entry.mint &&
          !timestamps.has(entry.mint) &&
          typeof created === "number" &&
          Number.isFinite(created) &&
          created > 0
        ) {
          evictOldest();
          timestamps.set(entry.mint, created);
        }
      }
    },
  };
}
