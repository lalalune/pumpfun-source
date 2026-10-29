export const NATIVE_FEED_DATA_SOURCE = "synthetic-home-feed-local-v1";
export const NATIVE_FEED_COMPATIBILITY = "local-unqualified";
export const NATIVE_FEED_LIVE_SUBJECT =
  "local.reconstruction.realtime-unavailable";

const CHAINS = new Set([
  "solana",
  "ethereum",
  "base",
  "bsc",
  "robinhood",
  "hyperevm",
  "ink",
  "arc",
  "megaeth",
  "xlayer",
  "monad",
  "polygon",
  "ton",
]);
const ASSET_CLASSES = new Set([
  "ASSET_CLASS_TOKEN",
  "ASSET_CLASS_PERPETUAL",
  "ASSET_CLASS_NFT_LIKE",
]);
const CURSOR = /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/u;
const CONTROL_CHARACTERS = /[\u0000-\u001f\u007f]/u;
const MAX_COINS = 50;

type UnknownRecord = Record<string, unknown>;

export type NativeFeedKind = "ranked" | "newest";

export type NativeCallout = {
  id: string;
  coinMint: string;
  coinName: string;
  symbol: string;
  chain: string;
  assetClass: string;
  authorId: string;
  authorName: string;
  thesis: string;
  calloutTimestamp: string;
  marketCapUsd: number;
  calledOutAtMarketCapUsd: number;
  costBasisUsd: number;
  multiple: number;
};

export type NativeFeedPage = {
  kind: NativeFeedKind;
  coins: NativeCallout[];
  nextPageToken?: string;
  headToken?: string | null;
  liveSubject?: typeof NATIVE_FEED_LIVE_SUBJECT;
};

export type NativeNewCount = {
  newCount: number;
  capped: boolean;
  headToken: string;
};

export class NativeFeedDataError extends Error {
  override name = "NativeFeedDataError";
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function record(value: unknown, label: string): UnknownRecord {
  if (!isRecord(value)) {
    throw new NativeFeedDataError(`${label} must be an object`);
  }
  return value;
}

function hasWellFormedUnicode(value: string): boolean {
  for (let index = 0; index < value.length; index += 1) {
    const unit = value.charCodeAt(index);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) return false;
      index += 1;
    } else if (unit >= 0xdc00 && unit <= 0xdfff) {
      return false;
    }
  }
  return true;
}

function safeString(value: unknown, label: string, maximum: number): string {
  if (
    typeof value !== "string" ||
    value.trim().length === 0 ||
    value.length > maximum ||
    CONTROL_CHARACTERS.test(value) ||
    !hasWellFormedUnicode(value)
  ) {
    throw new NativeFeedDataError(`${label} must be a bounded safe string`);
  }
  return value;
}

function finiteNonnegative(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new NativeFeedDataError(
      `${label} must be a finite non-negative number`,
    );
  }
  return value;
}

function nullable(value: unknown, label: string): void {
  if (value !== null) {
    throw new NativeFeedDataError(`${label} must remain unavailable`);
  }
}

function cursor(value: unknown, label: string): string {
  const parsed = safeString(value, label, 512);
  if (!CURSOR.test(parsed)) {
    throw new NativeFeedDataError(
      `${label} has an unsupported opaque cursor shape`,
    );
  }
  return parsed;
}

function optionalCursor(value: unknown, label: string): string | undefined {
  return value === undefined ? undefined : cursor(value, label);
}

function timestamp(value: unknown, label: string): string {
  const parsed = safeString(value, label, 64);
  const milliseconds = Date.parse(parsed);
  if (
    !Number.isFinite(milliseconds) ||
    new Date(milliseconds).toISOString() !== parsed
  ) {
    throw new NativeFeedDataError(`${label} must be a canonical ISO timestamp`);
  }
  return parsed;
}

function exactKeys(
  value: UnknownRecord,
  required: readonly string[],
  optional: readonly string[],
  label: string,
): void {
  const allowed = new Set([...required, ...optional]);
  const unexpected = Object.keys(value).find((key) => !allowed.has(key));
  const missing = required.find((key) => !(key in value));
  if (unexpected || missing) {
    throw new NativeFeedDataError(
      `${label} has ${unexpected ? `an unexpected ${unexpected} field` : `no ${missing} field`}`,
    );
  }
}

function parseCallout(value: unknown, index: number): NativeCallout {
  const coin = record(value, `coins[${index}]`);
  const position = record(coin.position, `coins[${index}].position`);
  const callout = record(position.callout, `coins[${index}].position.callout`);

  nullable(coin.coinImage, `coins[${index}].coinImage`);
  nullable(position.profileImage, `coins[${index}].position.profileImage`);
  nullable(position.walletAddress, `coins[${index}].position.walletAddress`);
  nullable(callout.mediaUrl, `coins[${index}].position.callout.mediaUrl`);

  const chain = safeString(coin.chain, `coins[${index}].chain`, 32);
  const calloutChain = safeString(
    callout.chain,
    `coins[${index}].position.callout.chain`,
    32,
  );
  if (!CHAINS.has(chain) || calloutChain !== chain) {
    throw new NativeFeedDataError(
      `coins[${index}] has an unsupported or inconsistent chain`,
    );
  }
  const assetClass = safeString(
    callout.assetClass,
    `coins[${index}].position.callout.assetClass`,
    64,
  );
  if (!ASSET_CLASSES.has(assetClass)) {
    throw new NativeFeedDataError(
      `coins[${index}] has an unsupported asset class`,
    );
  }
  if (position.contentKind !== "callout") {
    throw new NativeFeedDataError(
      `coins[${index}].position.contentKind must be callout`,
    );
  }
  if (
    position.isVerified !== false ||
    position.verifiedBadgeVisible !== false
  ) {
    throw new NativeFeedDataError(
      `coins[${index}] must not invent a verified author`,
    );
  }

  return {
    id: safeString(callout.calloutId, `coins[${index}].calloutId`, 64),
    coinMint: safeString(coin.coinMint, `coins[${index}].coinMint`, 128),
    coinName: safeString(coin.coinName, `coins[${index}].coinName`, 200),
    symbol: safeString(coin.symbol, `coins[${index}].symbol`, 32),
    chain,
    assetClass,
    authorId: safeString(
      position.userId,
      `coins[${index}].position.userId`,
      64,
    ),
    authorName: safeString(
      position.userName,
      `coins[${index}].position.userName`,
      100,
    ),
    thesis: safeString(
      callout.thesis,
      `coins[${index}].position.callout.thesis`,
      2_000,
    ),
    calloutTimestamp: timestamp(
      callout.calloutTimestamp,
      `coins[${index}].position.callout.calloutTimestamp`,
    ),
    marketCapUsd: finiteNonnegative(
      coin.marketCap,
      `coins[${index}].marketCap`,
    ),
    calledOutAtMarketCapUsd: finiteNonnegative(
      callout.calledOutAtMcap,
      `coins[${index}].position.callout.calledOutAtMcap`,
    ),
    costBasisUsd: finiteNonnegative(
      position.costBasisUsd,
      `coins[${index}].position.costBasisUsd`,
    ),
    multiple: finiteNonnegative(
      callout.multiple,
      `coins[${index}].position.callout.multiple`,
    ),
  };
}

export function validateNativeFeedPage(
  value: unknown,
  kind: NativeFeedKind,
): NativeFeedPage {
  const response = record(value, `${kind} response`);
  exactKeys(
    response,
    kind === "newest" ? ["coins", "headToken", "liveSubject"] : ["coins"],
    ["nextPageToken"],
    `${kind} response`,
  );
  if (!Array.isArray(response.coins) || response.coins.length > MAX_COINS) {
    throw new NativeFeedDataError(
      `${kind} response coins must be a bounded array`,
    );
  }
  const coins = Array.from(response.coins, parseCallout);
  const identities = new Set(coins.map((coin) => coin.id));
  if (identities.size !== coins.length) {
    throw new NativeFeedDataError(
      `${kind} response repeats a callout identity`,
    );
  }
  const page: NativeFeedPage = {
    kind,
    coins,
    nextPageToken: optionalCursor(
      response.nextPageToken,
      `${kind} response nextPageToken`,
    ),
  };
  if (kind === "newest") {
    page.headToken =
      response.headToken === null
        ? null
        : cursor(response.headToken, "newest response headToken");
    if (response.liveSubject !== NATIVE_FEED_LIVE_SUBJECT) {
      throw new NativeFeedDataError(
        "newest response liveSubject must preserve the local unavailable boundary",
      );
    }
    page.liveSubject = NATIVE_FEED_LIVE_SUBJECT;
  }
  return page;
}

export function validateNativeNewCount(value: unknown): NativeNewCount {
  const response = record(value, "new-count response");
  exactKeys(
    response,
    ["newCount", "capped", "headToken"],
    [],
    "new-count response",
  );
  if (
    typeof response.newCount !== "number" ||
    !Number.isSafeInteger(response.newCount) ||
    response.newCount < 0 ||
    response.newCount > 25 ||
    typeof response.capped !== "boolean"
  ) {
    throw new NativeFeedDataError(
      "new-count response has invalid count fields",
    );
  }
  return {
    newCount: response.newCount,
    capped: response.capped,
    headToken: cursor(response.headToken, "new-count response headToken"),
  };
}

export function validateNativeCursorInput(
  value: string | undefined,
  label: string,
): string | undefined {
  return value === undefined ? undefined : cursor(value, label);
}
