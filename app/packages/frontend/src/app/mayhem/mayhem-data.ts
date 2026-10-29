export const MAYHEM_API_ORIGIN = "https://frontend-api-v3.pump.fun";
export const MAYHEM_API_PATH = "/coins/mayhem-mode";
export const MAYHEM_DEFAULT_LIMIT = 60;
export const MAYHEM_MAX_LIMIT = 60;
export const MAYHEM_MAX_OFFSET = 1000;

export const MAYHEM_FILTERS = ["all", "active", "paused", "ended"] as const;
export const MAYHEM_SORTS = ["lastTraded", "volume", "mcap", "newest"] as const;

export type MayhemFilter = (typeof MAYHEM_FILTERS)[number];
export type MayhemSort = (typeof MAYHEM_SORTS)[number];
export type MayhemState = "active" | "paused" | "completed";
export type MayhemMode = "auto" | "manual";

export type MayhemCoin = {
  mint: string;
  name: string;
  symbol: string;
  state?: MayhemState;
  mode?: MayhemMode;
  createdTimestamp?: number;
  lastTradeTimestamp?: number;
  marketCapUsd?: number;
  volumeUsd24h?: number;
};

export type MayhemResponse = {
  source: "synthetic-test";
  coins: MayhemCoin[];
};

type UnknownRecord = Record<string, unknown>;

export class MayhemDataError extends Error {
  override name = "MayhemDataError";
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function safeIdentity(
  record: UnknownRecord,
  field: "mint" | "name" | "symbol",
) {
  const value = record[field];
  if (
    typeof value !== "string" ||
    value.trim() === "" ||
    /[\u0000-\u001f\u007f]/u.test(value)
  ) {
    throw new MayhemDataError(`${field} must be a non-empty safe string`);
  }
  return value;
}

function optionalEnum<T extends string>(
  record: UnknownRecord,
  field: string,
  values: readonly T[],
): T | undefined {
  const value = record[field];
  if (value === undefined || value === null) return undefined;
  if (typeof value !== "string" || !values.includes(value as T)) {
    throw new MayhemDataError(`${field} is not a supported value`);
  }
  return value as T;
}

function optionalNumber(
  record: UnknownRecord,
  field: string,
): number | undefined {
  const value = record[field];
  if (value === undefined || value === null) return undefined;
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new MayhemDataError(`${field} must be a non-negative finite number`);
  }
  return value;
}

export function parseMayhemResponse(input: unknown): MayhemResponse {
  if (
    !isRecord(input) ||
    input.source !== "synthetic-test" ||
    !Array.isArray(input.coins) || input.coins.length > MAYHEM_MAX_LIMIT
  ) {
    throw new MayhemDataError("Mayhem response envelope is invalid or exceeds the 60-row page limit");
  }

  const mints = new Set<string>();
  const coins = Array.from(input.coins, (value, index) => {
    if (!isRecord(value))
      throw new MayhemDataError(`coin ${index} must be an object`);
    const mint = safeIdentity(value, "mint");
    if (mints.has(mint))
      throw new MayhemDataError(`coin ${index} repeats a mint identity`);
    mints.add(mint);
    return {
      mint,
      name: safeIdentity(value, "name"),
      symbol: safeIdentity(value, "symbol"),
      state: optionalEnum(value, "state", ["active", "paused", "completed"]),
      mode: optionalEnum(value, "mode", ["auto", "manual"]),
      createdTimestamp: optionalNumber(value, "createdTimestamp"),
      lastTradeTimestamp: optionalNumber(value, "lastTradeTimestamp"),
      marketCapUsd: optionalNumber(value, "marketCapUsd"),
      volumeUsd24h: optionalNumber(value, "volumeUsd24h"),
    } satisfies MayhemCoin;
  });

  return { source: "synthetic-test", coins };
}

export function normalizeMayhemFilter(
  value: string | string[] | undefined,
): MayhemFilter {
  const candidate = Array.isArray(value) ? value[0] : value;
  return MAYHEM_FILTERS.includes(candidate as MayhemFilter)
    ? (candidate as MayhemFilter)
    : "all";
}

export function normalizeMayhemSort(
  value: string | string[] | undefined,
): MayhemSort {
  const candidate = Array.isArray(value) ? value[0] : value;
  return MAYHEM_SORTS.includes(candidate as MayhemSort)
    ? (candidate as MayhemSort)
    : "lastTraded";
}

export function mayhemStateParameter(
  filter: MayhemFilter,
): MayhemState | undefined {
  if (filter === "all") return undefined;
  return filter === "ended" ? "completed" : filter;
}

function boundedInteger(value: number, name: string, maximum: number) {
  if (!Number.isSafeInteger(value) || value < 0 || value > maximum) {
    throw new MayhemDataError(
      `${name} must be an integer from 0 to ${maximum}`,
    );
  }
  return value;
}

export function buildMayhemQuery({
  filter,
  limit = MAYHEM_DEFAULT_LIMIT,
  offset = 0,
}: {
  filter: MayhemFilter;
  limit?: number;
  offset?: number;
}): URLSearchParams {
  boundedInteger(limit, "limit", MAYHEM_MAX_LIMIT);
  boundedInteger(offset, "offset", MAYHEM_MAX_OFFSET);
  if (limit === 0) throw new MayhemDataError("limit must be at least 1");

  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    includeNsfw: "false",
  });
  const state = mayhemStateParameter(filter);
  if (state) query.set("mayhemState", state);
  return query;
}

function descending(left: number | undefined, right: number | undefined) {
  if (left === undefined) return right === undefined ? 0 : 1;
  if (right === undefined) return -1;
  return right - left;
}

export function sortMayhemCoins(
  coins: readonly MayhemCoin[],
  sort: MayhemSort,
): MayhemCoin[] {
  const indexed = coins.map((coin, index) => ({ coin, index }));
  if (sort === "lastTraded") return indexed.map(({ coin }) => coin);

  return indexed
    .sort((left, right) => {
      const result =
        sort === "volume"
          ? descending(left.coin.volumeUsd24h, right.coin.volumeUsd24h)
          : sort === "mcap"
            ? descending(left.coin.marketCapUsd, right.coin.marketCapUsd)
            : descending(
                left.coin.createdTimestamp,
                right.coin.createdTimestamp,
              );
      return result || left.index - right.index;
    })
    .map(({ coin }) => coin);
}
