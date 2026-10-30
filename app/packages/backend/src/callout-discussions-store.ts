/** Public, opt-in local discussion topology. No ranking, persistence or tombstone synthesis. */
import {
  closeSync,
  constants,
  fstatSync,
  openSync,
  readFileSync,
  readSync,
} from "node:fs";
import type { components, operations } from "./generated/developer-api.js";
import { CalloutsStore, assertCalloutJson } from "./callouts-store.js";
import { assertSchema, type SchemaNode } from "./schema-validator.js";

type Reply = components["schemas"]["Shared_3ba6ed1d0d06"];
type Chain =
  operations["get_callout_replies_by_replyId_chain"]["responses"][200]["content"]["application/json"];
type Author = Pick<
  Reply,
  "userId" | "userName" | "profileImage" | "walletAddress" | "accountKind"
>;
const authorKeys = [
  "userId",
  "userName",
  "profileImage",
  "walletAddress",
  "accountKind",
] as const;
const assembled = [
  "id",
  ...authorKeys,
  "parentMessageId",
  "rootMessageId",
  "directReplyCount",
  "threadReplyCount",
  "tombstone",
  "hasLiked",
  "viewerFollowsAuthor",
  "isQuote",
  "previewReplies",
  "authorReply",
] as const;
export type DiscussionFacts = Omit<Reply, (typeof assembled)[number]>;
export interface CalloutDiscussionsDataset {
  schemaVersion: 1;
  dataSource: "synthetic" | "local-materialized";
  observedAt: string;
  complete: true;
  /** Explicit local completeness boundary. Missing roots are unavailable, not known-empty. */
  calloutIds: string[];
  authors: Author[];
  replies: Array<{
    replyId: string;
    calloutId: string;
    parentReplyId: string | null;
    /** Only ordinary replies; quote threads require a separate materialization contract. */
    kind: "reply";
    hidden: boolean;
    deleted: boolean;
    /** Dead nodes carry topology only, never retained content or author identity. */
    authorId: string | null;
    facts: DiscussionFacts | null;
  }>;
}
type Row = CalloutDiscussionsDataset["replies"][number];
export class CalloutDiscussionError extends Error {
  constructor(
    readonly status: 400 | 501,
    readonly reason: string,
  ) {
    super(reason);
  }
}
const spec = JSON.parse(
  readFileSync(
    new URL("../../../contracts/developer.openapi.json", import.meta.url),
    "utf8",
  ),
);
const replySchema: SchemaNode = spec.components.schemas.Shared_3ba6ed1d0d06;
const authorSchema: SchemaNode = {
  type: "object",
  additionalProperties: false,
  properties: Object.fromEntries(
    authorKeys.map((key) => [key, replySchema.properties![key]]),
  ),
  required: [...authorKeys],
};
const factsSchema: SchemaNode = {
  ...replySchema,
  properties: Object.fromEntries(
    Object.entries(replySchema.properties!).filter(
      ([key]) => !(assembled as readonly string[]).includes(key),
    ),
  ),
  required: replySchema.required!.filter(
    (key) => !(assembled as readonly string[]).includes(key),
  ),
};
function invalid(message: string): never {
  throw new Error(`Invalid callout discussions: ${message}`);
}
function keys(
  value: unknown,
  allowed: readonly string[],
  label: string,
): asserts value is Record<string, unknown> {
  if (
    !value ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    Object.getPrototypeOf(value) !== Object.prototype ||
    Object.keys(value).some((key) => !allowed.includes(key))
  )
    invalid(`${label} fields`);
}
function id(value: unknown): asserts value is string {
  if (typeof value !== "string" || !value || /[\x00-\x1f\x7f]/.test(value))
    invalid("identity must be nonempty text");
}
function date(value: string): void {
  if (
    !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?Z$/.test(value) ||
    !Number.isFinite(Date.parse(value))
  )
    invalid("UTC instant");
  const padded = value.replace(
    /(?:\.(\d{1,3}))?Z$/,
    (_, fraction: string | undefined) => `.${(fraction ?? "").padEnd(3, "0")}Z`,
  );
  if (new Date(value).toISOString() !== padded) invalid("calendar date");
}
const live = (row: Row) => !row.hidden && !row.deleted;
const textOrder = (a: string, b: string) => (a === b ? 0 : a < b ? -1 : 1);
function newest(a: Row, b: Row): number {
  const at =
    a.facts?.createdAt == null ? -Infinity : Date.parse(a.facts.createdAt);
  const bt =
    b.facts?.createdAt == null ? -Infinity : Date.parse(b.facts.createdAt);
  return (at === bt ? 0 : at > bt ? -1 : 1) || textOrder(b.replyId, a.replyId);
}
function requestError(status: 400 | 501, reason: string): never {
  throw new CalloutDiscussionError(status, reason);
}
function integer(text: string, min: number): number {
  const value = Number(text);
  if (
    !/^(0|[1-9]\d*)$/.test(text) ||
    !Number.isSafeInteger(value) ||
    value < min
  )
    requestError(400, "CALLOUT_DISCUSSION_QUERY_INVALID");
  return value;
}
function parse(query: URLSearchParams) {
  const allowed = new Set([
    "limit",
    "beforeId",
    "page",
    "filter",
    "sort",
    "parentReplyId",
    "nestedLimit",
  ]);
  for (const key of query.keys()) {
    if (!allowed.has(key))
      requestError(501, "CALLOUT_DISCUSSION_QUERY_UNSUPPORTED");
    if (query.getAll(key).length !== 1)
      requestError(400, "CALLOUT_DISCUSSION_QUERY_INVALID");
  }
  const limit = integer(query.get("limit") ?? "30", 1);
  const nestedLimit = Math.min(10, integer(query.get("nestedLimit") ?? "0", 0));
  const filter = query.get("filter") ?? "ALL",
    sort = query.get("sort") ?? "RECENCY";
  if (
    !["ALL", "EXCLUDE_AUTHOR", "AUTHOR_ONLY"].includes(filter) ||
    !["RECENCY", "POSITION", "PNL"].includes(sort)
  )
    requestError(400, "CALLOUT_DISCUSSION_QUERY_INVALID");
  for (const key of ["beforeId", "parentReplyId"])
    if (query.has(key) && !query.get(key))
      requestError(400, "CALLOUT_DISCUSSION_QUERY_INVALID");
  if (sort !== "RECENCY" || query.has("page"))
    requestError(501, "CALLOUT_DISCUSSION_RANKING_UNAVAILABLE");
  return {
    limit,
    nestedLimit,
    filter,
    beforeId: query.get("beforeId"),
    parentReplyId: query.get("parentReplyId"),
  };
}

export class CalloutDiscussionsStore {
  readonly dataSource: CalloutDiscussionsDataset["dataSource"];
  readonly observedAt: string;
  private readonly roots = new Set<string>();
  private readonly authors = new Map<string, Author>();
  private readonly rows = new Map<string, Row>();
  private readonly children = new Map<string, Row[]>();
  private readonly top = new Map<string, Row[]>();
  private readonly rootReply = new Map<string, string>();
  private readonly descendantCounts = new Map<string, number>();
  constructor(
    input: unknown,
    private readonly callouts: CalloutsStore,
  ) {
    assertCalloutJson(input);
    keys(
      input,
      [
        "schemaVersion",
        "dataSource",
        "observedAt",
        "complete",
        "calloutIds",
        "authors",
        "replies",
      ],
      "dataset",
    );
    if (
      input.schemaVersion !== 1 ||
      input.complete !== true ||
      input.dataSource !== callouts.dataSource ||
      input.observedAt !== callouts.observedAt
    )
      invalid(
        "complete schemaVersion 1 graph and matching callout source/observation required",
      );
    for (const name of ["calloutIds", "authors", "replies"])
      if (!Array.isArray(input[name])) invalid(`${name} must be an array`);
    const data = structuredClone(input) as unknown as CalloutDiscussionsDataset;
    this.dataSource = data.dataSource;
    this.observedAt = data.observedAt;
    for (const calloutId of data.calloutIds) {
      id(calloutId);
      if (
        this.roots.has(calloutId) ||
        callouts.discussionContext(calloutId).kind === "unknown"
      )
        invalid("duplicate or unresolved callout");
      this.roots.add(calloutId);
    }
    for (const author of data.authors) {
      assertSchema(author, authorSchema, "discussion author", spec);
      id(author.userId);
      if (author.walletAddress !== null) id(author.walletAddress);
      if (author.accountKind === "group" && author.walletAddress !== null)
        invalid("group reply authors are walletless");
      if (this.authors.has(author.userId)) invalid("duplicate author");
      this.authors.set(author.userId, author);
    }
    for (const row of data.replies) {
      keys(
        row,
        [
          "replyId",
          "calloutId",
          "parentReplyId",
          "kind",
          "hidden",
          "deleted",
          "authorId",
          "facts",
        ],
        "reply",
      );
      id(row.replyId);
      id(row.calloutId);
      if (row.parentReplyId !== null) id(row.parentReplyId);
      if (
        row.kind !== "reply" ||
        typeof row.hidden !== "boolean" ||
        typeof row.deleted !== "boolean"
      )
        invalid("explicit ordinary-reply kind/visibility required");
      if (!this.roots.has(row.calloutId) || this.rows.has(row.replyId))
        invalid("unmaterialized callout or duplicate reply");
      if (live(row)) {
        id(row.authorId);
        if (!this.authors.has(row.authorId)) invalid("unresolved reply author");
        assertSchema(row.facts, factsSchema, "discussion facts", spec);
        if (row.facts!.createdAt !== null) date(row.facts!.createdAt);
        for (const key of [
          "positionAmountHeld",
          "positionValueUsd",
          "positionCostBasisAmount",
          "positionCostBasisUsd",
          "positionAmountBoughtUsd",
          "positionAmountBought",
          "positionAvgEntryMcapUsd",
        ] as const) {
          const value = row.facts![key];
          if (value !== null && value < 0)
            invalid("spot amount/value facts must be nonnegative");
        }
        for (const key of ["likeCount", "repostCount", "viewCount"] as const) {
          const count = row.facts![key];
          if (
            count !== undefined &&
            (!Number.isSafeInteger(count) || count < 0)
          )
            invalid("unsafe counter");
        }
      } else if (row.facts !== null || row.authorId !== null)
        invalid("dead rows must carry topology only");
      this.rows.set(row.replyId, row);
    }
    for (const row of this.rows.values()) {
      if (row.parentReplyId !== null) {
        const parent = this.rows.get(row.parentReplyId);
        if (!parent || parent.calloutId !== row.calloutId)
          invalid("dangling or cross-callout parent");
        const children = this.children.get(parent.replyId) ?? [];
        children.push(row);
        this.children.set(parent.replyId, children);
      } else {
        const top = this.top.get(row.calloutId) ?? [];
        top.push(row);
        this.top.set(row.calloutId, top);
      }
    }
    // Iterative ancestry checking avoids stack exhaustion on adversarially deep input.
    const ordered: Row[] = [],
      complete = new Set<string>();
    for (const row of this.rows.values()) {
      const path: Row[] = [],
        seen = new Set<string>();
      let current: Row | undefined = row;
      while (current && !complete.has(current.replyId)) {
        if (seen.has(current.replyId)) invalid("reply cycle");
        seen.add(current.replyId);
        path.push(current);
        current =
          current.parentReplyId === null
            ? undefined
            : this.rows.get(current.parentReplyId);
      }
      for (const item of path.reverse()) {
        this.rootReply.set(
          item.replyId,
          item.parentReplyId === null
            ? item.replyId
            : this.rootReply.get(item.parentReplyId)!,
        );
        complete.add(item.replyId);
        ordered.push(item);
      }
    }
    for (const row of ordered.reverse()) {
      const count = (this.children.get(row.replyId) ?? []).reduce(
        (n, child) =>
          n +
          Number(live(child)) +
          (this.descendantCounts.get(child.replyId) ?? 0),
        0,
      );
      this.descendantCounts.set(row.replyId, count);
    }
    for (const rows of [...this.top.values(), ...this.children.values()])
      rows.sort(newest);
  }
  private context(calloutId: string) {
    if (!this.roots.has(calloutId))
      requestError(501, "CALLOUT_DISCUSSION_UNAVAILABLE");
    return this.callouts.discussionContext(calloutId);
  }
  private project(
    row: Row,
    authorId: string | undefined,
    nestedLimit: number,
    hydrateAuthor = true,
  ): Reply {
    if (!live(row))
      requestError(501, "CALLOUT_DISCUSSION_TOMBSTONES_UNAVAILABLE");
    const children = (this.children.get(row.replyId) ?? []).filter(live);
    // Unknown times sort last locally; earliest known author child wins, ties use ascending IDs.
    const candidates = children
      .filter((child) => child.authorId === authorId)
      .sort((a, b) => {
        const at =
          a.facts!.createdAt === null
            ? Infinity
            : Date.parse(a.facts!.createdAt);
        const bt =
          b.facts!.createdAt === null
            ? Infinity
            : Date.parse(b.facts!.createdAt);
        return (
          (at === bt ? 0 : at < bt ? -1 : 1) || textOrder(a.replyId, b.replyId)
        );
      });
    const authorReply = hydrateAuthor ? candidates[0] : undefined;
    return {
      ...row.facts!,
      ...this.authors.get(row.authorId!)!,
      id: row.replyId,
      parentMessageId: row.parentReplyId,
      rootMessageId:
        row.parentReplyId === null ? null : this.rootReply.get(row.replyId)!,
      directReplyCount: children.length,
      threadReplyCount:
        row.parentReplyId === null
          ? this.descendantCounts.get(row.replyId)!
          : null,
      tombstone: false,
      hasLiked: null,
      viewerFollowsAuthor: null,
      isQuote: false,
      authorReply: authorReply
        ? this.project(authorReply, authorId, 0, false)
        : null,
      previewReplies: children
        .filter((child) => child !== authorReply)
        .slice(0, nestedLimit)
        .map((child) => this.project(child, authorId, 0, false)),
    };
  }
  list(calloutId: string, query = new URLSearchParams()): { replies: Reply[] } {
    const options = parse(query),
      context = this.context(calloutId);
    if (context.kind !== "visible")
      requestError(501, "CALLOUT_DISCUSSION_CALLOUT_UNAVAILABLE");
    let rows: Row[];
    if (options.parentReplyId !== null) {
      const parent = this.rows.get(options.parentReplyId);
      if (!parent || parent.calloutId !== calloutId)
        requestError(400, "CALLOUT_DISCUSSION_PARENT_INVALID");
      if (!live(parent))
        requestError(501, "CALLOUT_DISCUSSION_TOMBSTONES_UNAVAILABLE");
      rows = this.children.get(parent.replyId) ?? [];
    } else rows = this.top.get(calloutId) ?? [];
    // Do not silently remove the bridge to live descendants or fabricate redacted DTO defaults.
    if (
      options.filter === "ALL" &&
      rows.some(
        (row) => !live(row) && this.descendantCounts.get(row.replyId)! > 0,
      )
    )
      requestError(501, "CALLOUT_DISCUSSION_TOMBSTONES_UNAVAILABLE");
    rows = rows.filter(
      (row) =>
        live(row) &&
        (options.filter === "ALL" ||
          (row.authorId === context.authorId) ===
            (options.filter === "AUTHOR_ONLY")),
    );
    let start = 0;
    if (options.beforeId !== null) {
      const index = rows.findIndex((row) => row.replyId === options.beforeId);
      if (index < 0) requestError(400, "CALLOUT_DISCUSSION_CURSOR_INVALID");
      start = index + 1;
    }
    return structuredClone({
      replies: rows
        .slice(start, start + options.limit)
        .map((row) => this.project(row, context.authorId, options.nestedLimit)),
    });
  }
  chain(replyId: string): Chain {
    const row = this.rows.get(replyId);
    if (!row) requestError(501, "CALLOUT_DISCUSSION_REPLY_UNAVAILABLE");
    const context = this.context(row.calloutId);
    if (
      context.kind === "unknown" ||
      context.kind === "unmapped" ||
      (context.kind === "visible" && !context.callout)
    )
      requestError(501, "CALLOUT_DISCUSSION_CONTEXT_UNAVAILABLE");
    const authorId = context.kind === "visible" ? context.authorId : undefined;
    const ancestors: Row[] = [];
    let current = row.parentReplyId;
    while (current !== null) {
      const parent = this.rows.get(current)!;
      ancestors.push(parent);
      current = parent.parentReplyId;
    }
    if (!live(row) || ancestors.some((parent) => !live(parent)))
      requestError(501, "CALLOUT_DISCUSSION_TOMBSTONES_UNAVAILABLE");
    return structuredClone({
      callout: context.kind === "visible" ? context.callout : null,
      ancestors: ancestors
        .reverse()
        .map((parent) => this.project(parent, authorId, 0)),
      reply: this.project(row, authorId, 0),
    });
  }
}

export function loadCalloutDiscussionsStore(
  path: string,
  callouts: CalloutsStore,
): CalloutDiscussionsStore {
  const fd = openSync(path, constants.O_RDONLY | constants.O_NONBLOCK);
  try {
    const stat = fstatSync(fd);
    if (!stat.isFile() || stat.size > 8 * 1024 * 1024)
      invalid("file must be regular UTF-8 JSON at most 8 MiB");
    const bytes = Buffer.alloc(stat.size + 1);
    let size = 0;
    while (size < bytes.length) {
      const count = readSync(fd, bytes, size, bytes.length - size, null);
      if (!count) break;
      size += count;
    }
    if (size !== stat.size) invalid("file changed during read");
    return new CalloutDiscussionsStore(
      JSON.parse(
        new TextDecoder("utf-8", { fatal: true }).decode(
          bytes.subarray(0, size),
        ),
      ),
      callouts,
    );
  } finally {
    closeSync(fd);
  }
}
