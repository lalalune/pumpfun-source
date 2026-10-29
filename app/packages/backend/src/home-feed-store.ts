import { createHash, timingSafeEqual } from "node:crypto";
import seedData from "./home-feed-seed.json" with { type: "json" };

export const HOME_FEED_DATA_SOURCE = "synthetic-home-feed-local-v1";
export const HOME_FEED_SEED_CANONICAL_SHA256 =
  "3482fa9ed2f690d6002a4e9fe7932c6d7ce2d0258c9094cb9e438cfae0a5644e";
export const LOCAL_LIVE_SUBJECT = "local.reconstruction.realtime-unavailable";

export const FEED_CHAINS = [
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
] as const;

export const FEED_ASSET_CLASSES = ["coin", "stock", "perp", "pack"] as const;

export type FeedChain = (typeof FEED_CHAINS)[number];
export type FeedAssetClass = (typeof FEED_ASSET_CLASSES)[number];

export interface HomeFeedSeedRecord {
  recordId: string;
  calloutId: string;
  coinMint: string;
  coinName: string;
  symbol: string;
  chain: FeedChain;
  assetClass: FeedAssetClass;
  createdAt: string;
  localRank: number;
  marketCapUsd: number;
  calledOutAtMarketCapUsd: number;
  costBasisUsd: number;
  authorId: string;
  authorName: string;
  thesis: string;
  deleted: boolean;
  hidden: boolean;
}

export interface HomeFeedSeed {
  datasetId: string;
  observedAt: string;
  records: HomeFeedSeedRecord[];
}

export interface HomeFeedFilters {
  chains: readonly FeedChain[];
  assetClasses: readonly FeedAssetClass[];
  minMarketCapUsd?: number;
  maxMarketCapUsd?: number;
  minCostBasisUsd?: number;
  maxCostBasisUsd?: number;
  minCalloutMarketCapUsd?: number;
  maxCalloutMarketCapUsd?: number;
}

export interface RankedFeedRequest {
  filters: HomeFeedFilters;
  page: number;
  pageSize: number;
  pageToken?: string;
}

export interface NewFeedRequest {
  filters: HomeFeedFilters;
  pageSize: number;
  pageToken?: string;
}

export interface NewCountRequest {
  filters: HomeFeedFilters;
  since: string;
}

export interface HomeFeedCoin {
  coinMint: string;
  coinName: string;
  coinImage: null;
  symbol: string;
  coinDescription: null;
  marketCap: number;
  protocol: null;
  platform: null;
  program: null;
  chain: FeedChain;
  narrative: null;
  position: {
    userId: string;
    userName: string;
    profileImage: null;
    walletAddress: null;
    isVerified: false;
    verifiedBadgeVisible: false;
    resolvedAvatarDecoration: null;
    accountKind: "person";
    followerCount: null;
    xUsername: null;
    xProfileImage: null;
    totalCallouts: number;
    amountHeld: number;
    valueUsd: null;
    pnlUsd: null;
    pnlPercentage: null;
    realizedPnlUsd: number;
    tokenPriceUsd: null;
    costBasisAmount: number;
    costBasisUsd: number;
    amountBoughtUsd: null;
    amountBought: null;
    callout: {
      calloutId: string;
      chain: FeedChain;
      assetClass:
        | "ASSET_CLASS_TOKEN"
        | "ASSET_CLASS_PERPETUAL"
        | "ASSET_CLASS_NFT_LIKE";
      calledOutAtMcap: number;
      multiple: number;
      thesis: string;
      mediaUrl: null;
      calloutTimestamp: string;
      likes: number;
      hasLiked: null;
      updates: [];
      updateCount: number;
      commentCount: number;
      replyCount: number;
      maxMultiplier: null;
      maxMultiplierAt: null;
      calloutPrice: number;
      repostCount: number;
      quoteCount: number;
      hasReposted: null;
      actingUserId: string;
      actingUser: null;
      quotedCallout: null;
    };
    contentKind: "callout";
    quote: null;
  };
  followedHolders: null;
}

export interface RankedFeedResponse {
  coins: HomeFeedCoin[];
  nextPageToken?: string;
}

export interface NewFeedResponse extends RankedFeedResponse {
  headToken: string | null;
  liveSubject: typeof LOCAL_LIVE_SUBJECT;
}

export interface NewCountResponse {
  newCount: number;
  capped: boolean;
  headToken: string;
}

type CursorKind = "rank" | "new" | "head";
type CursorKey = [number, string, string];

interface CursorPayload {
  v: 1;
  k: CursorKind;
  d: string;
  c: string;
  x: CursorKey;
}

const CURSOR_DOMAIN = "pump-local-home-feed-cursor-v1\0";
const NEW_WINDOW_MS = 24 * 60 * 60 * 1000;
const LOCAL_MEMO_DEPTH = 25;
const SAFE_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]*$/u;
const UUID = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/u;

export class HomeFeedSeedError extends Error {
  override name = "HomeFeedSeedError";
}

export class HomeFeedCursorError extends Error {
  override name = "HomeFeedCursorError";
}

export function isWellFormedUnicode(value: string): boolean {
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function safeString(value: unknown, label: string, maximum: number): string {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.length > maximum ||
    /[\u0000-\u001f\u007f]/u.test(value) ||
    !isWellFormedUnicode(value)
  ) {
    throw new HomeFeedSeedError(`${label} must be a bounded safe string`);
  }
  return value;
}

function finiteNonnegative(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new HomeFeedSeedError(`${label} must be a non-negative number`);
  }
  return value;
}

function parseTimestamp(value: unknown, label: string): string {
  const timestamp = safeString(value, label, 64);
  const milliseconds = Date.parse(timestamp);
  if (
    !Number.isFinite(milliseconds) ||
    new Date(milliseconds).toISOString() !== timestamp
  ) {
    throw new HomeFeedSeedError(`${label} must be a canonical ISO timestamp`);
  }
  return timestamp;
}

function validateRecord(
  value: unknown,
  index: number,
  observedAt: number,
): HomeFeedSeedRecord {
  if (!isRecord(value)) {
    throw new HomeFeedSeedError(`records[${index}] must be an object`);
  }
  const recordId = safeString(value.recordId, `records[${index}].recordId`, 64);
  const calloutId = safeString(
    value.calloutId,
    `records[${index}].calloutId`,
    64,
  );
  if (!SAFE_ID.test(recordId) || !UUID.test(calloutId)) {
    throw new HomeFeedSeedError(`records[${index}] has an invalid identity`);
  }
  const chain = safeString(value.chain, `records[${index}].chain`, 32);
  const assetClass = safeString(
    value.assetClass,
    `records[${index}].assetClass`,
    16,
  );
  if (!FEED_CHAINS.includes(chain as FeedChain)) {
    throw new HomeFeedSeedError(`records[${index}] has an unsupported chain`);
  }
  if (!FEED_ASSET_CLASSES.includes(assetClass as FeedAssetClass)) {
    throw new HomeFeedSeedError(
      `records[${index}] has an unsupported asset class`,
    );
  }
  const createdAt = parseTimestamp(
    value.createdAt,
    `records[${index}].createdAt`,
  );
  if (Date.parse(createdAt) > observedAt) {
    throw new HomeFeedSeedError(
      `records[${index}] is newer than the observation time`,
    );
  }
  const localRank = finiteNonnegative(
    value.localRank,
    `records[${index}].localRank`,
  );
  if (!Number.isSafeInteger(localRank) || localRank < 1) {
    throw new HomeFeedSeedError(
      `records[${index}].localRank must be a positive safe integer`,
    );
  }
  if (typeof value.deleted !== "boolean" || typeof value.hidden !== "boolean") {
    throw new HomeFeedSeedError(
      `records[${index}] visibility flags must be booleans`,
    );
  }
  return {
    recordId,
    calloutId,
    coinMint: safeString(value.coinMint, `records[${index}].coinMint`, 128),
    coinName: safeString(value.coinName, `records[${index}].coinName`, 200),
    symbol: safeString(value.symbol, `records[${index}].symbol`, 32),
    chain: chain as FeedChain,
    assetClass: assetClass as FeedAssetClass,
    createdAt,
    localRank,
    marketCapUsd: finiteNonnegative(
      value.marketCapUsd,
      `records[${index}].marketCapUsd`,
    ),
    calledOutAtMarketCapUsd: finiteNonnegative(
      value.calledOutAtMarketCapUsd,
      `records[${index}].calledOutAtMarketCapUsd`,
    ),
    costBasisUsd: finiteNonnegative(
      value.costBasisUsd,
      `records[${index}].costBasisUsd`,
    ),
    authorId: safeString(value.authorId, `records[${index}].authorId`, 64),
    authorName: safeString(
      value.authorName,
      `records[${index}].authorName`,
      100,
    ),
    thesis: safeString(value.thesis, `records[${index}].thesis`, 2_000),
    deleted: value.deleted,
    hidden: value.hidden,
  };
}

export function validateHomeFeedSeed(value: unknown): HomeFeedSeed {
  if (!isRecord(value)) throw new HomeFeedSeedError("seed must be an object");
  const datasetId = safeString(value.datasetId, "datasetId", 64);
  if (!SAFE_ID.test(datasetId))
    throw new HomeFeedSeedError("datasetId is invalid");
  const observedAt = parseTimestamp(value.observedAt, "observedAt");
  if (!Array.isArray(value.records) || value.records.length > 500) {
    throw new HomeFeedSeedError("records must be a bounded array");
  }
  const observationMilliseconds = Date.parse(observedAt);
  const records = value.records.map((record, index) =>
    validateRecord(record, index, observationMilliseconds),
  );
  for (const [label, identities] of [
    ["recordId", records.map((record) => record.recordId)],
    ["calloutId", records.map((record) => record.calloutId)],
  ] as const) {
    if (new Set(identities).size !== identities.length) {
      throw new HomeFeedSeedError(`duplicate ${label} values are not allowed`);
    }
  }
  return { datasetId, observedAt, records };
}

function canonicalSeedHash(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function contextHash(filters: HomeFeedFilters): string {
  return createHash("sha256")
    .update(
      JSON.stringify({
        chains: [...filters.chains].sort(),
        assetClasses: [...filters.assetClasses].sort(),
        minMarketCapUsd: filters.minMarketCapUsd ?? null,
        maxMarketCapUsd: filters.maxMarketCapUsd ?? null,
        minCostBasisUsd: filters.minCostBasisUsd ?? null,
        maxCostBasisUsd: filters.maxCostBasisUsd ?? null,
        minCalloutMarketCapUsd: filters.minCalloutMarketCapUsd ?? null,
        maxCalloutMarketCapUsd: filters.maxCalloutMarketCapUsd ?? null,
      }),
    )
    .digest()
    .subarray(0, 16)
    .toString("base64url");
}

function cursorDigest(payload: string): Buffer {
  return createHash("sha256")
    .update(CURSOR_DOMAIN)
    .update(payload)
    .digest()
    .subarray(0, 16);
}

function cursorDatasetId(datasetId: string): string {
  return createHash("sha256")
    .update(datasetId)
    .digest()
    .subarray(0, 12)
    .toString("base64url");
}

function encodeCursor(payload: CursorPayload): string {
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `${body}.${cursorDigest(body).toString("base64url")}`;
}

function decodeBase64Url(value: string, label: string): Buffer {
  let bytes: Buffer;
  try {
    bytes = Buffer.from(value, "base64url");
  } catch {
    throw new HomeFeedCursorError(`${label} is not base64url`);
  }
  if (bytes.toString("base64url") !== value) {
    throw new HomeFeedCursorError(`${label} is not canonical base64url`);
  }
  return bytes;
}

function decodeCursor(
  token: string,
  expectedKind: CursorKind,
  datasetId: string,
  expectedContext: string,
): CursorPayload {
  const parts = token.split(".");
  if (parts.length !== 2 || parts.some((part) => part.length === 0)) {
    throw new HomeFeedCursorError("cursor envelope is malformed");
  }
  const body = decodeBase64Url(parts[0], "cursor body");
  const suppliedDigest = decodeBase64Url(parts[1], "cursor checksum");
  const expectedDigest = cursorDigest(parts[0]);
  if (
    suppliedDigest.length !== expectedDigest.length ||
    !timingSafeEqual(suppliedDigest, expectedDigest)
  ) {
    throw new HomeFeedCursorError("cursor checksum does not match");
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(body));
  } catch {
    throw new HomeFeedCursorError("cursor body is not canonical JSON data");
  }
  if (!isRecord(parsed))
    throw new HomeFeedCursorError("cursor body must be an object");
  if (
    Object.keys(parsed).sort().join(",") !== "c,d,k,v,x" ||
    parsed.v !== 1 ||
    parsed.k !== expectedKind ||
    parsed.d !== cursorDatasetId(datasetId) ||
    parsed.c !== expectedContext ||
    !Array.isArray(parsed.x) ||
    parsed.x.length !== 3 ||
    typeof parsed.x[0] !== "number" ||
    !Number.isSafeInteger(parsed.x[0]) ||
    typeof parsed.x[1] !== "string" ||
    !/^(0|-?[1-9]\d*)$/u.test(parsed.x[1]) ||
    typeof parsed.x[2] !== "string" ||
    !UUID.test(parsed.x[2])
  ) {
    throw new HomeFeedCursorError(
      "cursor does not belong to this operation or filter context",
    );
  }
  return parsed as unknown as CursorPayload;
}

function createdAtMicros(record: HomeFeedSeedRecord): string {
  return (BigInt(Date.parse(record.createdAt)) * 1_000n).toString();
}

function rankKey(record: HomeFeedSeedRecord): CursorKey {
  return [record.localRank, createdAtMicros(record), record.calloutId];
}

function chronologicalKey(record: HomeFeedSeedRecord): CursorKey {
  return [0, createdAtMicros(record), record.calloutId];
}

function compareRanked(
  left: HomeFeedSeedRecord,
  right: HomeFeedSeedRecord,
): number {
  return (
    left.localRank - right.localRank ||
    Date.parse(right.createdAt) - Date.parse(left.createdAt) ||
    left.calloutId.localeCompare(right.calloutId)
  );
}

function compareChronological(
  left: HomeFeedSeedRecord,
  right: HomeFeedSeedRecord,
): number {
  return (
    Date.parse(right.createdAt) - Date.parse(left.createdAt) ||
    left.calloutId.localeCompare(right.calloutId)
  );
}

function sameKey(left: CursorKey, right: CursorKey): boolean {
  return left[0] === right[0] && left[1] === right[1] && left[2] === right[2];
}

function projectAssetClass(
  assetClass: FeedAssetClass,
): HomeFeedCoin["position"]["callout"]["assetClass"] {
  if (assetClass === "perp") return "ASSET_CLASS_PERPETUAL";
  if (assetClass === "pack") return "ASSET_CLASS_NFT_LIKE";
  return "ASSET_CLASS_TOKEN";
}

function projectCoin(record: HomeFeedSeedRecord): HomeFeedCoin {
  return {
    coinMint: record.coinMint,
    coinName: record.coinName,
    coinImage: null,
    symbol: record.symbol,
    coinDescription: null,
    marketCap: record.marketCapUsd,
    protocol: null,
    platform: null,
    program: null,
    chain: record.chain,
    narrative: null,
    position: {
      userId: record.authorId,
      userName: record.authorName,
      profileImage: null,
      walletAddress: null,
      isVerified: false,
      verifiedBadgeVisible: false,
      resolvedAvatarDecoration: null,
      accountKind: "person",
      followerCount: null,
      xUsername: null,
      xProfileImage: null,
      totalCallouts: 1,
      amountHeld: 0,
      valueUsd: null,
      pnlUsd: null,
      pnlPercentage: null,
      realizedPnlUsd: 0,
      tokenPriceUsd: null,
      costBasisAmount: 0,
      costBasisUsd: record.costBasisUsd,
      amountBoughtUsd: null,
      amountBought: null,
      callout: {
        calloutId: record.calloutId,
        chain: record.chain,
        assetClass: projectAssetClass(record.assetClass),
        calledOutAtMcap: record.calledOutAtMarketCapUsd,
        multiple: 1,
        thesis: record.thesis,
        mediaUrl: null,
        calloutTimestamp: record.createdAt,
        likes: 0,
        hasLiked: null,
        updates: [],
        updateCount: 0,
        commentCount: 0,
        replyCount: 0,
        maxMultiplier: null,
        maxMultiplierAt: null,
        calloutPrice: 0,
        repostCount: 0,
        quoteCount: 0,
        hasReposted: null,
        actingUserId: record.authorId,
        actingUser: null,
        quotedCallout: null,
      },
      contentKind: "callout",
      quote: null,
    },
    followedHolders: null,
  };
}

export class HomeFeedStore {
  readonly datasetId: string;
  readonly observedAt: string;
  readonly dataSource: string;
  private readonly records: readonly HomeFeedSeedRecord[];

  constructor(
    source: unknown = seedData,
    options: { verifyDefaultHash?: boolean; dataSource?: string } = {},
  ) {
    const verifyDefaultHash = options.verifyDefaultHash ?? source === seedData;
    if (
      verifyDefaultHash &&
      canonicalSeedHash(source) !== HOME_FEED_SEED_CANONICAL_SHA256
    ) {
      throw new HomeFeedSeedError("default Home Feed seed hash does not match");
    }
    const seed = validateHomeFeedSeed(source);
    this.datasetId = seed.datasetId;
    this.observedAt = seed.observedAt;
    this.dataSource = options.dataSource ?? HOME_FEED_DATA_SOURCE;
    this.records = Object.freeze(
      seed.records.map((record) => Object.freeze({ ...record })),
    );
  }

  private select(
    filters: HomeFeedFilters,
    newWindowOnly: boolean,
  ): HomeFeedSeedRecord[] {
    const cutoff = Date.parse(this.observedAt) - NEW_WINDOW_MS;
    return this.records.filter((record) => {
      if (record.deleted || record.hidden) return false;
      if (newWindowOnly && Date.parse(record.createdAt) < cutoff) return false;
      if (filters.chains.length > 0 && !filters.chains.includes(record.chain))
        return false;
      if (
        filters.assetClasses.length > 0 &&
        !filters.assetClasses.includes(record.assetClass)
      ) {
        return false;
      }
      if (
        filters.minMarketCapUsd !== undefined &&
        record.marketCapUsd < filters.minMarketCapUsd
      ) {
        return false;
      }
      if (
        filters.maxMarketCapUsd !== undefined &&
        record.marketCapUsd > filters.maxMarketCapUsd
      ) {
        return false;
      }
      if (
        filters.minCostBasisUsd !== undefined &&
        record.costBasisUsd < filters.minCostBasisUsd
      ) {
        return false;
      }
      if (
        filters.maxCostBasisUsd !== undefined &&
        record.costBasisUsd > filters.maxCostBasisUsd
      ) {
        return false;
      }
      if (
        filters.minCalloutMarketCapUsd !== undefined &&
        record.calledOutAtMarketCapUsd < filters.minCalloutMarketCapUsd
      ) {
        return false;
      }
      if (
        filters.maxCalloutMarketCapUsd !== undefined &&
        record.calledOutAtMarketCapUsd > filters.maxCalloutMarketCapUsd
      ) {
        return false;
      }
      return true;
    });
  }

  ranked(request: RankedFeedRequest): RankedFeedResponse {
    const selected = this.select(request.filters, false).sort(compareRanked);
    const context = contextHash(request.filters);
    let start = request.page * request.pageSize;
    if (request.pageToken) {
      const cursor = decodeCursor(
        request.pageToken,
        "rank",
        this.datasetId,
        context,
      );
      const index = selected.findIndex((record) =>
        sameKey(rankKey(record), cursor.x),
      );
      if (index < 0)
        throw new HomeFeedCursorError("rank cursor boundary is unavailable");
      start = index + 1;
    }
    const page = selected.slice(start, start + request.pageSize);
    const response: RankedFeedResponse = { coins: page.map(projectCoin) };
    if (start + page.length < selected.length && page.length > 0) {
      response.nextPageToken = encodeCursor({
        v: 1,
        k: "rank",
        d: cursorDatasetId(this.datasetId),
        c: context,
        x: rankKey(page.at(-1)!),
      });
    }
    return response;
  }

  newest(request: NewFeedRequest): NewFeedResponse {
    const selected = this.select(request.filters, true).sort(
      compareChronological,
    );
    const context = contextHash(request.filters);
    let start = 0;
    if (request.pageToken) {
      const cursor = decodeCursor(
        request.pageToken,
        "new",
        this.datasetId,
        context,
      );
      const index = selected.findIndex((record) =>
        sameKey(chronologicalKey(record), cursor.x),
      );
      if (index < 0)
        throw new HomeFeedCursorError(
          "new-feed cursor boundary is unavailable",
        );
      start = index + 1;
    }
    const page = selected.slice(start, start + request.pageSize);
    const response: NewFeedResponse = {
      coins: page.map(projectCoin),
      headToken:
        start === 0 && selected[0]
          ? encodeCursor({
              v: 1,
              k: "head",
              d: cursorDatasetId(this.datasetId),
              c: context,
              x: chronologicalKey(selected[0]),
            })
          : null,
      liveSubject: LOCAL_LIVE_SUBJECT,
    };
    if (start + page.length < selected.length && page.length > 0) {
      response.nextPageToken = encodeCursor({
        v: 1,
        k: "new",
        d: cursorDatasetId(this.datasetId),
        c: context,
        x: chronologicalKey(page.at(-1)!),
      });
    }
    return response;
  }

  countNew(request: NewCountRequest): NewCountResponse {
    const context = contextHash(request.filters);
    const since = decodeCursor(request.since, "head", this.datasetId, context);
    const selected = this.select(request.filters, true).sort(
      compareChronological,
    );
    const sinceKey = since.x;
    const newer = selected.filter((record) => {
      const key = chronologicalKey(record);
      if (key[1] !== sinceKey[1]) return BigInt(key[1]) > BigInt(sinceKey[1]);
      return key[2].localeCompare(sinceKey[2]) < 0;
    });
    const explicitChains = request.filters.chains;
    let newCount: number;
    let capped: boolean;
    if (explicitChains.length > 1) {
      const counts = explicitChains.map(
        (chain) => newer.filter((record) => record.chain === chain).length,
      );
      newCount = counts.reduce(
        (total, count) => total + Math.min(count, LOCAL_MEMO_DEPTH),
        0,
      );
      capped = counts.some((count) => count > LOCAL_MEMO_DEPTH);
    } else {
      newCount = Math.min(newer.length, LOCAL_MEMO_DEPTH);
      capped = newer.length > LOCAL_MEMO_DEPTH;
    }
    const head = selected[0];
    const headIsNewer = head
      ? BigInt(createdAtMicros(head)) > BigInt(sinceKey[1]) ||
        (createdAtMicros(head) === sinceKey[1] &&
          head.calloutId.localeCompare(sinceKey[2]) < 0)
      : false;
    return {
      newCount,
      capped,
      headToken:
        head && headIsNewer
          ? encodeCursor({
              v: 1,
              k: "head",
              d: cursorDatasetId(this.datasetId),
              c: context,
              x: chronologicalKey(head),
            })
          : request.since,
    };
  }

  snapshotRecords(): HomeFeedSeedRecord[] {
    return this.records.map((record) => ({ ...record }));
  }
}

export const defaultHomeFeedStore = new HomeFeedStore();
