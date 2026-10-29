import {
  closeSync,
  constants,
  fstatSync,
  lstatSync,
  openSync,
  readSync,
} from "node:fs";

/** Local inputs shaped like the declared response rows; not a recovered database schema. */
export interface HolderRewardsAccrued {
  quoteMintAddress: string;
  quote: string | null;
  usdAtTrade: string | null;
  usdNow: string | null;
  numTrades: number;
  firstTradeAt: string | null;
  lastTradeAt: string | null;
}
export interface HolderRewardsPayouts {
  quoteMintAddress: string | null;
  paidToHolders: string | null;
  paidToHoldersQuote: string | null;
  paidToHoldersUsd: string | null;
  opsCharge: string | null;
  payoutCount: number;
  recipientCount: number;
  lastPayoutAt: string | null;
}
export interface HolderRewardsCoin {
  mint: string;
  holderRewardsPda: string;
  name: string | null;
  symbol: string | null;
  imageUri: string | null;
  createdAt: string | null;
  lastTradeAt: string | null;
  marketCapUsd: number | null;
  athMarketCapUsd: number | null;
  isGraduated: boolean;
  isLive: boolean;
  isNsfw: boolean;
  quoteMintAddress: string | null;
  socials: {
    twitter: string | null;
    telegram: string | null;
    website: string | null;
  };
  accrued: HolderRewardsAccrued | null;
  payouts: HolderRewardsPayouts | null;
}
export interface HolderRewardsQuote {
  mint: string;
  decimals: number | null;
  usdPrice: number | null;
  symbol: string | null;
  name: string | null;
  imageUri: string | null;
}
export interface HolderRewardsTotals {
  coinCount: number;
  payingCount: number;
  accruedUsdAtTrade: string;
  accruedUsdNow: string;
  unpricedCoinCount: number;
  walletsRewarded: number;
  walletsRewardedDistinct: number;
  payoutCount: number;
}
export interface HolderRewardsByQuote {
  quoteMintAddress: string;
  coinCount: number;
  payingCount: number;
  accrued: string;
  accruedUsdAtTrade: string | null;
  paid: string;
}
export interface HolderRewardsDataset {
  schemaVersion: 1;
  dataSource: "synthetic" | "local-materialized";
  observedAt: string;
  generatedAt: string;
  coins: HolderRewardsCoin[];
  quotes: Record<string, HolderRewardsQuote>;
  totals: HolderRewardsTotals;
  byQuote: HolderRewardsByQuote[];
}
export interface HolderRewardsPage {
  generatedAt: string;
  coins: HolderRewardsCoin[];
  next: null;
  quotes: Record<string, HolderRewardsQuote>;
  totals: HolderRewardsTotals;
  matchingCount: number;
  offset: number;
  byQuote: HolderRewardsByQuote[];
}
/** Page-mode sorts computable from supplied rows; accruedNow/distributed need current marks. */
export type HolderRewardsSort =
  | "accrued"
  | "lastPayout"
  | "wallets"
  | "trades"
  | "lastTrade";
export interface HolderRewardsPageQuery {
  sort?: HolderRewardsSort;
  direction?: "asc" | "desc";
  quote?: string;
  payingOnly?: boolean;
  page?: number;
  limit?: number;
}

const MAX_FILE_BYTES = 64 * 1024 * 1024;
const DECIMAL = /^(?:0|[1-9][0-9]{0,77})(?:\.[0-9]{1,78})?$/;
const ATOMIC = /^(?:0|[1-9][0-9]{0,77})$/;
function invalid(field: string): never {
  throw new TypeError(`Invalid local holder-rewards dataset: ${field}`);
}
function record(value: unknown, keys: readonly string[], field: string) {
  if (
    !value ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    ![Object.prototype, null].includes(Object.getPrototypeOf(value))
  )
    invalid(field);
  const item = value as Record<string, unknown>;
  if (
    Object.keys(item).length !== keys.length ||
    keys.some((key) => !Object.hasOwn(item, key))
  )
    invalid(field);
  return item;
}
/** Declared z.string() display values; empty is allowed, control characters are not. */
function display(value: unknown, field: string): string {
  if (
    typeof value !== "string" ||
    value.length > 2048 ||
    /[\u0000-\u001f\u007f]/u.test(value)
  )
    invalid(field);
  return value;
}
/** Identifiers and keys: a non-empty display string. */
function text(value: unknown, field: string): string {
  const result = display(value, field);
  if (!result.length) invalid(field);
  return result;
}
function nullable<T>(
  value: unknown,
  parse: (value: unknown, field: string) => T,
  field: string,
): T | null {
  return value === null ? null : parse(value, field);
}
function matching(pattern: RegExp) {
  return (value: unknown, field: string): string => {
    if (typeof value !== "string" || !pattern.test(value)) invalid(field);
    return value;
  };
}
const decimal = matching(DECIMAL);
const atomic = matching(ATOMIC);
function count(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0)
    invalid(field);
  return value;
}
function finite(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) invalid(field);
  return value;
}
function flag(value: unknown, field: string): boolean {
  if (typeof value !== "boolean") invalid(field);
  return value;
}
function list(value: unknown, max: number, field: string): unknown[] {
  if (!Array.isArray(value) || value.length > max) invalid(field);
  for (let index = 0; index < value.length; index++) {
    if (!Object.hasOwn(value, index)) invalid(field);
  }
  return value;
}
function compare<T extends string | number | bigint>(
  left: T,
  right: T,
): number {
  return left < right ? -1 : left > right ? 1 : 0;
}
function deepFreeze<T>(value: T): T {
  if (value && typeof value === "object") {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}
/** Local definition: a coin pays when the index has a holder payout amount for it. */
function paying(coin: HolderRewardsCoin): boolean {
  return coin.payouts?.paidToHolders != null;
}

type SortKey = (coin: HolderRewardsCoin) => string | number | bigint | null;

/** Immutable, opt-in read model of one supplied book. No live data, prices, claims or writes. */
export class HolderRewardsStore {
  readonly dataSource: HolderRewardsDataset["dataSource"];
  readonly observedAt: string;
  readonly #generatedAt: string;
  readonly #coins: readonly HolderRewardsCoin[];
  readonly #quotes: Record<string, HolderRewardsQuote>;
  readonly #totals: HolderRewardsTotals;
  readonly #byQuote: readonly HolderRewardsByQuote[];
  readonly #keys: Record<HolderRewardsSort, SortKey>;
  // One sorted order per sort and direction, built on first use (at most ten).
  readonly #orders = new Map<string, readonly HolderRewardsCoin[]>();

  constructor(input: unknown) {
    const data = record(
      input,
      [
        "schemaVersion",
        "dataSource",
        "observedAt",
        "generatedAt",
        "coins",
        "quotes",
        "totals",
        "byQuote",
      ],
      "root",
    );
    if (
      data.schemaVersion !== 1 ||
      (data.dataSource !== "synthetic" &&
        data.dataSource !== "local-materialized")
    )
      invalid("version/source");
    this.dataSource = data.dataSource;
    const observedAt = this.#timestamp(data.observedAt, "observedAt", null);
    this.observedAt = observedAt;
    const at = (value: unknown, field: string) =>
      this.#timestamp(value, field, observedAt);
    this.#generatedAt = at(data.generatedAt, "generatedAt");

    const mints = new Set<string>();
    const coins = list(data.coins, 100_000, "coins").map(
      (value): HolderRewardsCoin => {
        const row = record(
          value,
          [
            "mint",
            "holderRewardsPda",
            "name",
            "symbol",
            "imageUri",
            "createdAt",
            "lastTradeAt",
            "marketCapUsd",
            "athMarketCapUsd",
            "isGraduated",
            "isLive",
            "isNsfw",
            "quoteMintAddress",
            "socials",
            "accrued",
            "payouts",
          ],
          "coin",
        );
        const mint = text(row.mint, "coin.mint");
        if (mints.has(mint)) invalid("duplicate coin mint");
        mints.add(mint);
        const socials = record(
          row.socials,
          ["twitter", "telegram", "website"],
          "coin.socials",
        );
        const accrued = nullable(
          row.accrued,
          (value) => {
            const item = record(
              value,
              [
                "quoteMintAddress",
                "quote",
                "usdAtTrade",
                "usdNow",
                "numTrades",
                "firstTradeAt",
                "lastTradeAt",
              ],
              "coin.accrued",
            );
            const result: HolderRewardsAccrued = {
              quoteMintAddress: text(
                item.quoteMintAddress,
                "accrued.quoteMintAddress",
              ),
              quote: nullable(item.quote, decimal, "accrued.quote"),
              usdAtTrade: nullable(
                item.usdAtTrade,
                decimal,
                "accrued.usdAtTrade",
              ),
              usdNow: nullable(item.usdNow, decimal, "accrued.usdNow"),
              numTrades: count(item.numTrades, "accrued.numTrades"),
              firstTradeAt: nullable(
                item.firstTradeAt,
                at,
                "accrued.firstTradeAt",
              ),
              lastTradeAt: nullable(
                item.lastTradeAt,
                at,
                "accrued.lastTradeAt",
              ),
            };
            if (
              result.firstTradeAt &&
              result.lastTradeAt &&
              result.firstTradeAt > result.lastTradeAt
            )
              invalid("accrued trade interval");
            return result;
          },
          "coin.accrued",
        );
        const payouts = nullable(
          row.payouts,
          (value): HolderRewardsPayouts => {
            const item = record(
              value,
              [
                "quoteMintAddress",
                "paidToHolders",
                "paidToHoldersQuote",
                "paidToHoldersUsd",
                "opsCharge",
                "payoutCount",
                "recipientCount",
                "lastPayoutAt",
              ],
              "coin.payouts",
            );
            return {
              quoteMintAddress: nullable(
                item.quoteMintAddress,
                text,
                "payouts.quoteMintAddress",
              ),
              paidToHolders: nullable(
                item.paidToHolders,
                atomic,
                "payouts.paidToHolders",
              ),
              paidToHoldersQuote: nullable(
                item.paidToHoldersQuote,
                decimal,
                "payouts.paidToHoldersQuote",
              ),
              paidToHoldersUsd: nullable(
                item.paidToHoldersUsd,
                decimal,
                "payouts.paidToHoldersUsd",
              ),
              // Declared as a nullable string with no unit; kept as opaque text.
              opsCharge: nullable(item.opsCharge, display, "payouts.opsCharge"),
              payoutCount: count(item.payoutCount, "payouts.payoutCount"),
              recipientCount: count(
                item.recipientCount,
                "payouts.recipientCount",
              ),
              lastPayoutAt: nullable(
                item.lastPayoutAt,
                at,
                "payouts.lastPayoutAt",
              ),
            };
          },
          "coin.payouts",
        );
        return {
          mint,
          holderRewardsPda: text(row.holderRewardsPda, "coin.holderRewardsPda"),
          name: nullable(row.name, display, "coin.name"),
          symbol: nullable(row.symbol, display, "coin.symbol"),
          imageUri: nullable(row.imageUri, display, "coin.imageUri"),
          createdAt: nullable(row.createdAt, at, "coin.createdAt"),
          lastTradeAt: nullable(row.lastTradeAt, at, "coin.lastTradeAt"),
          marketCapUsd: nullable(row.marketCapUsd, finite, "coin.marketCapUsd"),
          athMarketCapUsd: nullable(
            row.athMarketCapUsd,
            finite,
            "coin.athMarketCapUsd",
          ),
          isGraduated: flag(row.isGraduated, "coin.isGraduated"),
          isLive: flag(row.isLive, "coin.isLive"),
          isNsfw: flag(row.isNsfw, "coin.isNsfw"),
          quoteMintAddress: nullable(
            row.quoteMintAddress,
            text,
            "coin.quoteMintAddress",
          ),
          socials: {
            twitter: nullable(socials.twitter, display, "socials.twitter"),
            telegram: nullable(socials.telegram, display, "socials.telegram"),
            website: nullable(socials.website, display, "socials.website"),
          },
          accrued,
          payouts,
        };
      },
    );

    const byQuoteMints = new Set<string>();
    const byQuote = list(data.byQuote, 1_000, "byQuote").map(
      (value): HolderRewardsByQuote => {
        const item = record(
          value,
          [
            "quoteMintAddress",
            "coinCount",
            "payingCount",
            "accrued",
            "accruedUsdAtTrade",
            "paid",
          ],
          "byQuote",
        );
        const quoteMintAddress = text(
          item.quoteMintAddress,
          "byQuote.quoteMintAddress",
        );
        if (byQuoteMints.has(quoteMintAddress))
          invalid("duplicate byQuote mint");
        byQuoteMints.add(quoteMintAddress);
        const facet = {
          quoteMintAddress,
          coinCount: count(item.coinCount, "byQuote.coinCount"),
          payingCount: count(item.payingCount, "byQuote.payingCount"),
          accrued: atomic(item.accrued, "byQuote.accrued"),
          accruedUsdAtTrade: nullable(
            item.accruedUsdAtTrade,
            decimal,
            "byQuote.accruedUsdAtTrade",
          ),
          paid: atomic(item.paid, "byQuote.paid"),
        };
        if (
          facet.payingCount > facet.coinCount ||
          facet.coinCount > coins.length
        )
          invalid("byQuote counts");
        return facet;
      },
    );

    // Declared: every quote the coins accrued or paid in, and every byQuote mint.
    const referenced = new Set(byQuoteMints);
    for (const coin of coins) {
      if (coin.accrued) referenced.add(coin.accrued.quoteMintAddress);
      if (coin.payouts?.quoteMintAddress)
        referenced.add(coin.payouts.quoteMintAddress);
    }
    const quoteInput = record(
      data.quotes,
      Object.keys(data.quotes ?? {}),
      "quotes",
    );
    const quoteKeys = Object.keys(quoteInput);
    if (
      quoteKeys.length !== referenced.size ||
      quoteKeys.some((key) => !referenced.has(key))
    )
      invalid("quotes must list exactly the referenced quote mints");
    const quotes = Object.fromEntries(
      quoteKeys.map((key): [string, HolderRewardsQuote] => {
        const item = record(
          quoteInput[key],
          ["mint", "decimals", "usdPrice", "symbol", "name", "imageUri"],
          "quote",
        );
        if (item.mint !== key) invalid("quote key/mint");
        return [
          key,
          {
            mint: key,
            decimals: nullable(item.decimals, count, "quote.decimals"),
            usdPrice: nullable(item.usdPrice, finite, "quote.usdPrice"),
            symbol: nullable(item.symbol, display, "quote.symbol"),
            name: nullable(item.name, display, "quote.name"),
            imageUri: nullable(item.imageUri, display, "quote.imageUri"),
          },
        ];
      }),
    );
    for (const coin of coins) {
      // Declared: paidToHoldersUsd is null when the quote amount or USD price is unknown.
      const price = coin.payouts?.quoteMintAddress
        ? quotes[coin.payouts.quoteMintAddress].usdPrice
        : null;
      if (
        coin.payouts?.paidToHoldersUsd != null &&
        (coin.payouts.paidToHoldersQuote === null || price === null)
      )
        invalid(
          "payouts.paidToHoldersUsd without a known quote amount and price",
        );
    }

    const totalsInput = record(
      data.totals,
      [
        "coinCount",
        "payingCount",
        "accruedUsdAtTrade",
        "accruedUsdNow",
        "unpricedCoinCount",
        "walletsRewarded",
        "walletsRewardedDistinct",
        "payoutCount",
      ],
      "totals",
    );
    const totals: HolderRewardsTotals = {
      coinCount: count(totalsInput.coinCount, "totals.coinCount"),
      payingCount: count(totalsInput.payingCount, "totals.payingCount"),
      accruedUsdAtTrade: decimal(
        totalsInput.accruedUsdAtTrade,
        "totals.accruedUsdAtTrade",
      ),
      accruedUsdNow: decimal(totalsInput.accruedUsdNow, "totals.accruedUsdNow"),
      unpricedCoinCount: count(
        totalsInput.unpricedCoinCount,
        "totals.unpricedCoinCount",
      ),
      walletsRewarded: count(
        totalsInput.walletsRewarded,
        "totals.walletsRewarded",
      ),
      walletsRewardedDistinct: count(
        totalsInput.walletsRewardedDistinct,
        "totals.walletsRewardedDistinct",
      ),
      payoutCount: count(totalsInput.payoutCount, "totals.payoutCount"),
    };
    // Check the totals the declaration defines from rows; the USD sums stay producer-asserted.
    const sum = (pick: (coin: HolderRewardsCoin) => number) =>
      coins.reduce((total, coin) => total + pick(coin), 0);
    const widest = coins.reduce(
      (max, coin) => Math.max(max, coin.payouts?.recipientCount ?? 0),
      0,
    );
    if (
      totals.coinCount !== coins.length ||
      totals.payingCount !== coins.filter(paying).length ||
      totals.payoutCount !== sum((coin) => coin.payouts?.payoutCount ?? 0) ||
      totals.walletsRewarded !==
        sum((coin) => coin.payouts?.recipientCount ?? 0) ||
      totals.walletsRewardedDistinct > totals.walletsRewarded ||
      totals.walletsRewardedDistinct < widest ||
      totals.unpricedCoinCount > totals.coinCount
    )
      invalid("totals disagree with the supplied book");

    this.#coins = deepFreeze(coins);
    this.#quotes = deepFreeze(quotes);
    this.#totals = deepFreeze(totals);
    this.#byQuote = deepFreeze(byQuote);
    // Sort keys are local readings of the declared sort names. Decimals are parsed
    // once to integers at the book's widest scale, so comparison stays exact.
    const scale = coins.reduce(
      (max, coin) =>
        Math.max(max, coin.accrued?.usdAtTrade?.split(".")[1]?.length ?? 0),
      0,
    );
    const usdAtTrade = new Map(
      coins.map((coin) => {
        const value = coin.accrued?.usdAtTrade;
        if (value == null) return [coin, null] as const;
        const [whole, fraction = ""] = value.split(".");
        return [coin, BigInt(whole + fraction.padEnd(scale, "0"))] as const;
      }),
    );
    this.#keys = {
      accrued: (coin) => usdAtTrade.get(coin) ?? null,
      lastPayout: (coin) => coin.payouts?.lastPayoutAt ?? null,
      wallets: (coin) => coin.payouts?.recipientCount ?? null,
      trades: (coin) => coin.accrued?.numTrades ?? null,
      lastTrade: (coin) => coin.lastTradeAt,
    };
  }

  /** Non-null keys follow the direction; null keys sort last; ties use code-unit mint order. */
  #sorted(
    sort: HolderRewardsSort,
    direction: "asc" | "desc",
  ): readonly HolderRewardsCoin[] {
    const memo = `${sort} ${direction}`;
    let order = this.#orders.get(memo);
    if (!order) {
      const key = this.#keys[sort];
      const sign = direction === "asc" ? 1 : -1;
      order = [...this.#coins].sort((left, right) => {
        const a = key(left);
        const b = key(right);
        if (a === null || b === null)
          return a === b ? compare(left.mint, right.mint) : a === null ? 1 : -1;
        return sign * compare(a, b) || compare(left.mint, right.mint);
      });
      this.#orders.set(memo, order);
    }
    return order;
  }

  #timestamp(value: unknown, field: string, notAfter: string | null): string {
    const result = text(value, field);
    const ms = Date.parse(result);
    if (
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(result) ||
      !Number.isFinite(ms) ||
      new Date(ms).toISOString() !== result ||
      (notAfter !== null && result > notAfter)
    )
      invalid(field);
    return result;
  }

  page(options: HolderRewardsPageQuery = {}): HolderRewardsPage {
    const {
      sort = "accrued",
      direction = "desc",
      quote,
      payingOnly = false,
      page = 1,
      limit = 50,
    } = options;
    if (
      !Object.hasOwn(this.#keys, sort) ||
      (direction !== "asc" && direction !== "desc") ||
      !Number.isSafeInteger(page) ||
      page < 1 ||
      !Number.isSafeInteger(limit) ||
      limit < 1 ||
      limit > 2000
    )
      throw new RangeError("Invalid holder-rewards query");
    const offset = (page - 1) * limit;
    if (!Number.isSafeInteger(offset))
      throw new RangeError("Holder-rewards page offset out of range");
    // ponytail: one O(n) filter per request over a memoized order; index by quote if books outgrow 100k rows.
    const selected = this.#sorted(sort, direction).filter(
      (coin) =>
        (quote === undefined || coin.quoteMintAddress === quote) &&
        (!payingOnly || paying(coin)),
    );
    return {
      generatedAt: this.#generatedAt,
      coins: selected.slice(offset, offset + limit),
      next: null,
      quotes: this.#quotes,
      totals: this.#totals,
      matchingCount: selected.length,
      offset,
      byQuote: [...this.#byQuote],
    };
  }
}

/** Startup-only, bounded regular-file read. No writes, reloads or network. */
export function loadHolderRewardsStore(
  path: string | undefined,
): HolderRewardsStore | undefined {
  if (!path) return undefined;
  // O_NOFOLLOW is undefined on Windows, so the open flag alone does not reject
  // a symlinked path there. Check the path itself and bind the opened handle to it.
  const linkStat = lstatSync(path, { bigint: true });
  if (linkStat.isSymbolicLink() || !linkStat.isFile())
    invalid("file type/size");
  const fd = openSync(
    path,
    constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK,
  );
  try {
    const opened = fstatSync(fd, { bigint: true });
    if (
      opened.dev !== linkStat.dev ||
      opened.ino !== linkStat.ino ||
      !opened.isFile() ||
      opened.size > BigInt(MAX_FILE_BYTES)
    )
      invalid("file type/size");
    const buffer = Buffer.alloc(MAX_FILE_BYTES + 1);
    let size = 0;
    while (size < buffer.length) {
      const read = readSync(fd, buffer, size, buffer.length - size, null);
      if (read === 0) break;
      size += read;
    }
    if (size > MAX_FILE_BYTES) invalid("file size");
    return new HolderRewardsStore(
      JSON.parse(
        new TextDecoder("utf-8", { fatal: true }).decode(
          buffer.subarray(0, size),
        ),
      ),
    );
  } finally {
    closeSync(fd);
  }
}
