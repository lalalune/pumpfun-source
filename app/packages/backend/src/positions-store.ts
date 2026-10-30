/** Independently implemented spot-position read model; never a PnL/indexing engine. */
import {
  readFileSync,
  openSync,
  closeSync,
  fstatSync,
  readSync,
  constants,
} from "node:fs";
import type { operations } from "./generated/developer-api.js";
import { assertSchema, type SchemaNode } from "./schema-validator.js";

export type Position =
  operations["get_user_positions_by_userId"]["responses"][200]["content"]["application/json"]["positions"][number];
export type Callout = NonNullable<Position["callout"]>;
export type PositionCoin = NonNullable<Position["coin"]>;
export type CalloutUpdate = Callout["updates"][number];
export type PositionFacts = Omit<
  Position,
  | "callout"
  | "coin"
  | "potentialSpam"
  | "userMarkedNonSpam"
  | "dustFloorFiltered"
  | "groupHolders"
>;
export interface PositionRecord {
  facts: PositionFacts;
  calloutId?: string;
  /** Public security verdict only. No owner's private spam/rescue marks. */
  publicSpam?: boolean;
}
export interface PositionsDataset {
  schemaVersion: 1;
  dataSource: "synthetic" | "local-materialized";
  observedAt: string;
  subjects: Array<{
    kind: "person";
    id: string;
    aliases: string[];
    positions: PositionRecord[];
  }>;
  coins: Array<{
    coinMint: string;
    chainId: number | null;
    chain?: string;
    coin: PositionCoin;
  }>;
  callouts: Array<{
    authorId: string;
    updatesComplete: boolean;
    body: Callout;
  }>;
  updates: Array<{
    calloutId: string;
    authorId: string;
    deleted: boolean;
    hidden: boolean;
    body: CalloutUpdate;
  }>;
}
export interface PortfolioOptions {
  filter?: "OPEN" | "CLOSED" | "ALL";
  sortBy?: "PNL" | "POSITION_SIZE" | "RECENCY";
  page?: number;
  pageSize?: number;
  chainId?: number;
  totalsOnly?: boolean;
  filterSpam?: boolean;
  spamOnly?: boolean;
}

const spec = JSON.parse(
  readFileSync(
    new URL("../../../contracts/developer.openapi.json", import.meta.url),
    "utf8",
  ),
);
const positionSchema: SchemaNode =
  spec.paths["/user-positions/{userId}"].get.responses["200"].content[
    "application/json"
  ].schema.properties.positions.items;
const calloutSchema: SchemaNode = spec.components.schemas.Shared_fceda4efe6cd;
const updateSchema: SchemaNode = calloutSchema.properties!.updates.items!;
const coinSchema: SchemaNode = positionSchema.properties!.coin;
const own = (value: object, key: string) => Object.hasOwn(value, key);
const clone = <T>(value: T): T => structuredClone(value);
const orderText = (a: string, b: string) => (a === b ? 0 : a < b ? -1 : 1);
const key = (row: {
  coinMint: string;
  chainId: number | null;
  chain?: string;
}) => JSON.stringify([row.coinMint, row.chain ?? null, row.chainId]);
const timestamp = (value: string | null | undefined) =>
  value == null ? null : Date.parse(value);
const desc = (a: number | null | undefined, b: number | null | undefined) =>
  a == null ? (b == null ? 0 : 1) : b == null ? -1 : b - a;

function fail(message: string): never {
  throw new Error(`Invalid positions materialization: ${message}`);
}
function object(
  value: unknown,
  keys: string[],
  label: string,
): asserts value is Record<string, unknown> {
  if (
    !value ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    Object.getPrototypeOf(value) !== Object.prototype
  )
    fail(`${label} must be a JSON object`);
  if (Object.keys(value).some((k) => !keys.includes(k)))
    fail(`${label} has unsupported fields`);
}
function list(value: unknown, label: string): asserts value is unknown[] {
  if (!Array.isArray(value)) fail(`${label} must be an array`);
}
function text(value: unknown, label: string): asserts value is string {
  if (typeof value !== "string" || !value || /[\x00-\x1f\x7f]/.test(value))
    fail(`${label} must be nonempty text`);
}
function iso(value: unknown, label: string): asserts value is string {
  if (
    typeof value !== "string" ||
    !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?Z$/.test(value) ||
    !Number.isFinite(Date.parse(value))
  )
    fail(`${label} must be a UTC ISO instant`);
  const canonical = value.replace(
    /(?:\.(\d{1,3}))?Z$/,
    (_match, fraction: string | undefined) =>
      `.${(fraction ?? "").padEnd(3, "0")}Z`,
  );
  if (new Date(value).toISOString() !== canonical)
    fail(`${label} has an invalid calendar date`);
}
function plainJson(value: unknown, depth = 0): void {
  if (depth > 40) fail("nested input exceeds the local limit");
  if (value === null || typeof value === "string" || typeof value === "boolean")
    return;
  if (typeof value === "number" && Number.isFinite(value)) return;
  if (Array.isArray(value)) {
    for (const item of value) plainJson(item, depth + 1);
    return;
  }
  if (
    value &&
    typeof value === "object" &&
    Object.getPrototypeOf(value) === Object.prototype
  ) {
    for (const [name, child] of Object.entries(value)) {
      if (["__proto__", "constructor", "prototype"].includes(name))
        fail("prototype-related field");
      plainJson(child, depth + 1);
    }
    return;
  }
  fail("input must contain finite plain JSON values only");
}
const spotChain = /^(solana:[A-Za-z0-9]+|eip155:[1-9]\d*)$/;
const enrichmentCounters = new Set([
  "likes",
  "likeCount",
  "updateCount",
  "commentCount",
  "replyCount",
  "repostCount",
  "quoteCount",
  "viewCount",
  "xFollowerCount",
]);
const enrichmentDates = new Set([
  "calloutTimestamp",
  "maxMultiplierAt",
  "createdAt",
]);
/** Additional local admission rules apply recursively to every emitted enrichment. */
function publicCallout(value: unknown, quoteDepth = 0): void {
  if (!value || typeof value !== "object") return;
  for (const [field, child] of Object.entries(value)) {
    if (field === "updates" && Array.isArray(child) && child.length > 0)
      fail("callout updates must come from the separate update relation");
    if (["hasLiked", "hasReposted"].includes(field) && child !== null)
      fail("viewer-specific callout state is not public");
    if (["perp", "collectible"].includes(field) && child !== null)
      fail("non-spot enrichment is not supported");
    if (field === "assetClass" && child !== "ASSET_CLASS_TOKEN")
      fail("non-token enrichment is not supported");
    if (
      field === "chain" &&
      child !== null &&
      (typeof child !== "string" || !spotChain.test(child))
    )
      fail("unsupported enrichment chain");
    if (enrichmentDates.has(field) && child !== null) iso(child, field);
    if (
      enrichmentCounters.has(field) &&
      (!Number.isSafeInteger(child) || (child as number) < 0)
    )
      fail("social counters must be nonnegative safe integers");
    const nestedQuote = field === "quotedCallout" && child !== null;
    if (nestedQuote && quoteDepth > 0)
      fail("quoted callouts may be expanded only one level");
    publicCallout(child, quoteDepth + (nestedQuote ? 1 : 0));
  }
}
function spot(row: {
  chainId: number | null;
  chain?: string;
  assetClass?: string;
  coinMint: string;
}): void {
  if (row.chain !== undefined && typeof row.chain !== "string")
    fail("chain must be a string");
  if (
    (row.assetClass !== undefined && row.assetClass !== "ASSET_CLASS_TOKEN") ||
    row.coinMint.startsWith("hlcore:") ||
    (row.chain !== undefined && !spotChain.test(row.chain))
  )
    fail("only materialized Solana/EVM spot-token rows are supported");
  if (row.chainId !== null && !Number.isSafeInteger(row.chainId))
    fail("chainId must be a safe integer or null");
}

/**
 * Snapshot facts are supplied by an operator-owned adapter, not by HTTP clients.
 * Selection, joins, projection, ordering and pagination are computed here.
 * Missing subjects are unknown (404), not fabricated empty wallets.
 */
export class PositionsStore {
  readonly dataSource: PositionsDataset["dataSource"];
  readonly observedAt: string;
  private subjects = new Map<string, PositionsDataset["subjects"][number]>();
  private coins = new Map<string, PositionCoin>();
  private callouts = new Map<string, PositionsDataset["callouts"][number]>();
  private updates = new Map<string, PositionsDataset["updates"]>();

  constructor(input: unknown) {
    plainJson(input);
    object(
      input,
      [
        "schemaVersion",
        "dataSource",
        "observedAt",
        "subjects",
        "coins",
        "callouts",
        "updates",
      ],
      "dataset",
    );
    if (
      input.schemaVersion !== 1 ||
      !["synthetic", "local-materialized"].includes(input.dataSource as string)
    )
      fail("schemaVersion/dataSource");
    iso(input.observedAt, "observedAt");
    for (const field of ["subjects", "coins", "callouts", "updates"])
      list(input[field], field);
    const data = clone(input) as unknown as PositionsDataset;
    this.dataSource = data.dataSource;
    this.observedAt = data.observedAt;
    for (const item of data.callouts) {
      object(item, ["authorId", "updatesComplete", "body"], "callout");
      text(item.authorId, "authorId");
      assertSchema(item.body, calloutSchema, "callout", spec);
      if (typeof item.updatesComplete !== "boolean")
        fail("callout updates completeness must be explicit");
      if (item.body.assetClass && item.body.assetClass !== "ASSET_CLASS_TOKEN")
        fail("non-spot callout");
      publicCallout(item.body);
      text(item.body.calloutId, "calloutId");
      if (this.callouts.has(item.body.calloutId)) fail("duplicate callout");
      this.callouts.set(item.body.calloutId, item);
    }
    const updateIds = new Set<string>();
    for (const item of data.updates) {
      object(
        item,
        ["calloutId", "authorId", "deleted", "hidden", "body"],
        "update",
      );
      text(item.calloutId, "update.calloutId");
      text(item.authorId, "update.authorId");
      if (typeof item.deleted !== "boolean" || typeof item.hidden !== "boolean")
        fail("update visibility");
      assertSchema(item.body, updateSchema, "update", spec);
      text(item.body.id, "update.id");
      publicCallout(item.body);
      if (item.body.createdAt !== null)
        iso(item.body.createdAt, "update.createdAt");
      if (updateIds.has(item.body.id)) fail("duplicate update id");
      updateIds.add(item.body.id);
      if (!this.callouts.has(item.calloutId))
        fail("update references missing callout");
      const rows = this.updates.get(item.calloutId) ?? [];
      rows.push(item);
      this.updates.set(item.calloutId, rows);
    }
    for (const item of data.coins) {
      object(item, ["coinMint", "chainId", "chain", "coin"], "coin");
      text(item.coinMint, "coinMint");
      if (!own(item, "chainId")) fail("coin.chainId is required");
      spot(item);
      if (item.coin === null) fail("coin metadata must be an object");
      assertSchema(item.coin, coinSchema, "coin", spec);
      if (item.coin.collectible !== undefined)
        fail("collectible metadata is not supported");
      if (this.coins.has(key(item))) fail("duplicate coin identity");
      this.coins.set(key(item), item.coin);
    }
    for (const subject of data.subjects) {
      object(subject, ["kind", "id", "aliases", "positions"], "subject");
      text(subject.id, "subject.id");
      if (subject.kind !== "person")
        fail("group aggregation is not implemented");
      list(subject.aliases, "aliases");
      list(subject.positions, "positions");
      const identities = [subject.id, ...subject.aliases];
      for (const id of identities) {
        text(id, "identity");
        if (this.subjects.has(id))
          fail("duplicate or ambiguous subject identity");
        this.subjects.set(id, subject);
      }
      const rowKeys = new Set<string>();
      for (const record of subject.positions) {
        object(record, ["facts", "calloutId", "publicSpam"], "position record");
        if (
          record.publicSpam !== undefined &&
          typeof record.publicSpam !== "boolean"
        )
          fail("publicSpam must be boolean");
        const facts = record.facts;
        if (!facts || typeof facts !== "object" || Array.isArray(facts))
          fail("facts must be an object");
        for (const forbidden of [
          "callout",
          "coin",
          "potentialSpam",
          "userMarkedNonSpam",
          "dustFloorFiltered",
          "groupHolders",
          "perp",
          "collectible",
        ])
          if (own(facts, forbidden)) fail(`facts may not contain ${forbidden}`);
        assertSchema(
          { ...facts, callout: null },
          positionSchema,
          "position",
          spec,
        );
        text(facts.coinMint, "coinMint");
        spot(facts);
        if (facts.isExited && own(facts, "openedAt"))
          fail("exited rows cannot carry openedAt");
        if (facts.updatedAt != null) iso(facts.updatedAt, "updatedAt");
        for (const instant of [facts.updatedAt, facts.openedAt]) {
          if (instant != null && Date.parse(instant) > Date.parse(this.observedAt)) fail("position timestamp exceeds observedAt");
        }
        if (facts.openedAt !== undefined) iso(facts.openedAt, "openedAt");
        if (
          facts.lastSlotIndexId !== undefined &&
          !/^\d{26}$/.test(facts.lastSlotIndexId)
        )
          fail("lastSlotIndexId must be 26 digits");
        if ((facts.isNative === true) !== (facts.coinMint === "native"))
          fail("native rows use the bare native mint");
        if (
          record.calloutId !== undefined &&
          !this.callouts.has(record.calloutId)
        )
          fail("position references missing callout");
        if (
          record.calloutId !== undefined &&
          this.callouts.get(record.calloutId)!.authorId !== subject.id
        )
          fail("callout belongs to another subject");
        if (rowKeys.has(key(facts))) fail("duplicate position identity");
        rowKeys.add(key(facts));
      }
    }
  }

  private project(
    record: PositionRecord,
    portfolio: boolean,
    updatesLimit: number,
  ): Position {
    const row: Position = { ...clone(record.facts), callout: null };
    const callout =
      record.calloutId === undefined
        ? undefined
        : this.callouts.get(record.calloutId);
    if (callout) {
      row.callout = clone(callout.body);
      if (updatesLimit > 0 && callout.updatesComplete)
        row.callout.updates = (this.updates.get(callout.body.calloutId) ?? [])
          .filter(
            (update) =>
              update.authorId === callout.authorId &&
              !update.deleted &&
              !update.hidden &&
              update.body.parentMessageId === callout.body.calloutId,
          )
          .sort(
            (a, b) =>
              desc(timestamp(a.body.createdAt), timestamp(b.body.createdAt)) ||
              orderText(a.body.id, b.body.id),
          )
          .slice(0, updatesLimit)
          .map((update) => clone(update.body));
    }
    if (portfolio) {
      if (record.publicSpam !== undefined)
        row.potentialSpam = record.publicSpam && !callout;
      row.userMarkedNonSpam = false;
      row.dustFloorFiltered = false;
      if (!row.isNative) row.coin = clone(this.coins.get(key(row)) ?? null);
    } else {
      delete row.isNative;
    }
    return row;
  }

  positions(
    id: string,
    mints: string[],
    updatesLimit = 5,
  ): { positions: Position[] } | null {
    if (
      mints.length > 200 ||
      !mints.every((mint) => typeof mint === "string") ||
      !Number.isInteger(updatesLimit) ||
      updatesLimit < 0 ||
      updatesLimit > 20
    )
      throw new RangeError("Invalid positions selection");
    const subject = this.subjects.get(id);
    if (!subject) return null;
    const result: Position[] = [];
    for (const mint of new Set(mints)) {
      const candidates = subject.positions.filter(
        (record) => !record.facts.isNative && record.facts.coinMint === mint,
      );
      // No chain selector is declared on this endpoint. Never pick an arbitrary chain.
      if (candidates.length > 1) throw new AmbiguousPositionError();
      if (candidates[0]) {
        const calloutId = candidates[0].calloutId;
        if (
          updatesLimit > 0 &&
          calloutId !== undefined &&
          !this.callouts.get(calloutId)!.updatesComplete
        )
          throw new UnavailableUpdatesError();
        result.push(this.project(candidates[0], false, updatesLimit));
      }
    }
    return { positions: result };
  }

  portfolio(id: string, options: PortfolioOptions = {}) {
    const filter = options.filter ?? "OPEN",
      sortBy = options.sortBy ?? "PNL";
    const page = options.page ?? 0,
      pageSize = options.pageSize ?? 50;
    if (
      !["OPEN", "CLOSED", "ALL"].includes(filter) ||
      !["PNL", "POSITION_SIZE", "RECENCY"].includes(sortBy) ||
      !Number.isSafeInteger(page) ||
      page < 0 ||
      !Number.isSafeInteger(pageSize) ||
      pageSize < 1 ||
      pageSize > 200 ||
      (options.chainId !== undefined &&
        !Number.isSafeInteger(options.chainId)) ||
      [options.totalsOnly, options.filterSpam, options.spamOnly].some(value => value !== undefined && typeof value !== "boolean") ||
      (options.filterSpam && options.spamOnly)
    )
      throw new RangeError("Invalid portfolio selection");
    const subject = this.subjects.get(id);
    if (!subject) return null;
    const rows = subject.positions
      .filter(
        (record) =>
          (filter === "ALL" ||
            record.facts.isExited === (filter === "CLOSED")) &&
          (options.chainId === undefined ||
            record.facts.chainId === options.chainId),
      )
      .map((record) => this.project(record, true, 5))
      .filter((row) => {
        const spam =
          row.potentialSpam === true && row.userMarkedNonSpam !== true;
        return options.filterSpam ? !spam : options.spamOnly ? spam : true;
      });
    rows.sort((a, b) => {
      const metric =
        sortBy === "RECENCY"
          ? desc(timestamp(a.updatedAt), timestamp(b.updatedAt))
          : sortBy === "POSITION_SIZE"
            ? desc(a.valueUsd, b.valueUsd)
            : desc(a.pnlUsd, b.pnlUsd);
      return metric || orderText(key(a), key(b));
    });
    // Avoid unsafe page*pageSize arithmetic; a distant valid page is simply empty.
    const start =
      page > Math.floor(Number.MAX_SAFE_INTEGER / pageSize)
        ? rows.length
        : page * pageSize;
    const positions = options.totalsOnly
      ? []
      : rows.slice(start, start + pageSize);
    const updatesApplied = positions.every(
      (row) =>
        !row.callout ||
        this.callouts.get(row.callout.calloutId)!.updatesComplete,
    );
    return {
      positions,
      summary: { positionCount: rows.length },
      updatesApplied,
    };
  }
}

export class AmbiguousPositionError extends Error {
  constructor() {
    super(
      "A mint resolves to more than one chain in the local materialization",
    );
  }
}

export class UnavailableUpdatesError extends Error {
  constructor() {
    super(
      "The local materialization does not establish callout update completeness",
    );
  }
}

/** Bounded startup-only import from a server-owned local file, never a request URL. */
export function loadPositionsStore(path: string): PositionsStore {
  const limit = 16 * 1024 * 1024;
  const fd = openSync(path, constants.O_RDONLY | constants.O_NONBLOCK);
  try {
    const stat = fstatSync(fd);
    if (!stat.isFile() || stat.size > limit)
      fail("POSITIONS_FILE must be a regular file of at most 16 MiB");
    const buffer = Buffer.alloc(limit + 1);
    let size = 0;
    while (size < buffer.length) {
      const read = readSync(fd, buffer, size, buffer.length - size, null);
      if (read === 0) break;
      size += read;
    }
    if (size > limit) fail("POSITIONS_FILE exceeds 16 MiB");
    const source = new TextDecoder("utf-8", { fatal: true }).decode(
      buffer.subarray(0, size),
    );
    return new PositionsStore(JSON.parse(source));
  } finally {
    closeSync(fd);
  }
}
