import { createHash } from "node:crypto";

export const CAPTURED_COIN_ENDPOINT =
  "https://frontend-api-v3.pump.fun/coins?offset=0&limit=1";
export const CAPTURED_COIN_PATH = "evidence/web/objects/cd3f926d4d318056";
export const CAPTURED_COIN_SHA256 =
  "b41a41c70fb4b2548dfc166e9c31e1b5b9dfd73d233cf94ee384a9c5d75e017d";
export const CAPTURED_COIN_BYTES = 1813;

export type HistoricalCoin = {
  mint: string;
  name: string;
  symbol: string;
  imageUri?: string;
  createdTimestamp?: number;
  lastTradeTimestamp?: number;
  marketCap?: number;
  marketCapUsd?: number;
  quoteMint?: string;
  complete?: boolean;
  creator?: string;
  protocol?: string;
  verified?: boolean;
};

export type CoinSnapshot = {
  capturedAt: string;
  endpoint: string;
  sha256: string;
  coins: HistoricalCoin[];
};

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requiredIdentity(
  record: UnknownRecord,
  field: "mint" | "name" | "symbol",
): string {
  const value = record[field];
  if (
    typeof value !== "string" ||
    value.trim().length === 0 ||
    /[\u0000-\u001f\u007f]/u.test(value)
  ) {
    throw new ValueError(`Coin ${field} must be a non-empty safe string`);
  }
  return value;
}

function optionalString(
  record: UnknownRecord,
  field: string,
): string | undefined {
  const value = record[field];
  if (value === undefined || value === null) return undefined;
  if (typeof value !== "string" || /[\u0000-\u001f\u007f]/u.test(value)) {
    throw new ValueError(`Coin ${field} must be a safe string when present`);
  }
  return value;
}

function optionalHttpUrl(
  record: UnknownRecord,
  field: string,
): string | undefined {
  const value = optionalString(record, field);
  if (value === undefined) return undefined;
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new ValueError(`Coin ${field} must be an absolute URL when present`);
  }
  if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
    throw new ValueError(`Coin ${field} uses an unsupported URL scheme`);
  }
  return value;
}

function optionalBoolean(
  record: UnknownRecord,
  field: string,
): boolean | undefined {
  const value = record[field];
  if (value === undefined || value === null) return undefined;
  if (typeof value !== "boolean") {
    throw new ValueError(`Coin ${field} must be a boolean when present`);
  }
  return value;
}

function optionalNumber(
  record: UnknownRecord,
  field: string,
  integer = false,
): number | undefined {
  const value = record[field];
  if (value === undefined || value === null) return undefined;
  if (
    typeof value !== "number" ||
    !Number.isFinite(value) ||
    value < 0 ||
    (integer && !Number.isSafeInteger(value))
  ) {
    throw new ValueError(
      `Coin ${field} must be a non-negative${integer ? " integer" : " finite number"} when present`,
    );
  }
  return value;
}

export class ValueError extends Error {
  override name = "ValueError";
}

export function validateCoinDataset(input: unknown): HistoricalCoin[] {
  if (!Array.isArray(input)) {
    throw new ValueError("Captured coin response must be an array");
  }

  const seenMints = new Set<string>();
  return Array.from(input, (value, index) => {
    if (!isRecord(value)) {
      throw new ValueError(`Coin record ${index} must be an object`);
    }
    const mint = requiredIdentity(value, "mint");
    if (seenMints.has(mint)) {
      throw new ValueError(`Coin record ${index} repeats a mint identity`);
    }
    seenMints.add(mint);

    return {
      mint,
      name: requiredIdentity(value, "name"),
      symbol: requiredIdentity(value, "symbol"),
      imageUri: optionalHttpUrl(value, "image_uri"),
      createdTimestamp: optionalNumber(value, "created_timestamp", true),
      lastTradeTimestamp: optionalNumber(value, "last_trade_timestamp", true),
      marketCap: optionalNumber(value, "market_cap"),
      marketCapUsd: optionalNumber(value, "market_cap_usd"),
      quoteMint: optionalString(value, "quote_mint"),
      complete: optionalBoolean(value, "complete"),
      creator: optionalString(value, "creator"),
      protocol: optionalString(value, "protocol"),
      verified: optionalBoolean(value, "verified"),
    };
  });
}

export function sha256(bytes: Uint8Array): string {
  return createHash("sha256").update(bytes).digest("hex");
}

export function parseCoinSnapshotBytes(
  bytes: Uint8Array,
  expectedSha256 = CAPTURED_COIN_SHA256,
): HistoricalCoin[] {
  const actualSha256 = sha256(bytes);
  if (actualSha256 !== expectedSha256) {
    throw new ValueError(
      `Captured coin response SHA-256 mismatch: expected ${expectedSha256}, received ${actualSha256}`,
    );
  }

  let decoded: unknown;
  try {
    decoded = JSON.parse(
      new TextDecoder("utf-8", { fatal: true }).decode(bytes),
    );
  } catch (error) {
    throw new ValueError(
      `Captured coin response is not valid UTF-8 JSON: ${error instanceof Error ? error.message : "unknown parse failure"}`,
    );
  }
  return validateCoinDataset(decoded);
}

export function verifySnapshotProvenance(
  bytes: Uint8Array,
  probes: unknown,
  manifest: unknown,
): CoinSnapshot {
  if (!Array.isArray(probes)) {
    throw new ValueError("API probe inventory must be an array");
  }
  const probe = probes.find(
    (value): value is UnknownRecord =>
      isRecord(value) && value.url === CAPTURED_COIN_ENDPOINT,
  );
  if (!probe) throw new ValueError("Captured coin API probe is missing");
  if (
    probe.final_url !== CAPTURED_COIN_ENDPOINT ||
    probe.status !== 200 ||
    probe.path !== CAPTURED_COIN_PATH ||
    probe.bytes !== CAPTURED_COIN_BYTES ||
    probe.sha256 !== CAPTURED_COIN_SHA256
  ) {
    throw new ValueError("Captured coin API probe provenance does not match");
  }
  if (bytes.byteLength !== CAPTURED_COIN_BYTES) {
    throw new ValueError("Captured coin response byte length does not match");
  }
  if (!isRecord(manifest) || typeof manifest.captured_at !== "string") {
    throw new ValueError("Capture manifest timestamp is missing");
  }
  const capturedAt = new Date(manifest.captured_at);
  if (!Number.isFinite(capturedAt.getTime())) {
    throw new ValueError("Capture manifest timestamp is invalid");
  }

  return {
    capturedAt: manifest.captured_at,
    endpoint: CAPTURED_COIN_ENDPOINT,
    sha256: CAPTURED_COIN_SHA256,
    coins: parseCoinSnapshotBytes(bytes),
  };
}

function comparable(value: string): string {
  return value.normalize("NFKC").toLocaleLowerCase("en-US");
}

function compareText(left: string, right: string): number {
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

export function searchHistoricalCoins(
  coins: readonly HistoricalCoin[],
  query: string,
): HistoricalCoin[] {
  const normalizedQuery = comparable(query.trim());
  const matches = normalizedQuery
    ? coins.filter((coin) =>
        [coin.name, coin.symbol, coin.mint].some((value) =>
          comparable(value).includes(normalizedQuery),
        ),
      )
    : [...coins];

  return matches.sort((left, right) => {
    const name = compareText(comparable(left.name), comparable(right.name));
    if (name !== 0) return name;
    const symbol = compareText(
      comparable(left.symbol),
      comparable(right.symbol),
    );
    return symbol || compareText(left.mint, right.mint);
  });
}
