import { test } from "node:test";
import assert from "node:assert/strict";
import {
  readFileSync,
  existsSync,
  mkdtempSync,
  writeFileSync,
  rmSync,
  truncateSync,
} from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { buildApp, type Fixture } from "../src/app.js";
import {
  CalloutsStore,
  type CalloutsDataset,
  type CalloutFacts,
  type QuoteFacts,
} from "../src/callouts-store.js";
import {
  CalloutDiscussionsStore,
  CalloutDiscussionError,
  loadCalloutDiscussionsStore,
  type CalloutDiscussionsDataset,
  type DiscussionFacts,
} from "../src/callout-discussions-store.js";
import { PositionsStore } from "../src/positions-store.js";
import { startWithLocalMedia } from "../src/local-media-runtime.js";
import { assertSchema } from "../src/schema-validator.js";
const now = "2026-10-29T00:01:00.000Z";
const headers = { authorization: `Bearer pf_live_${"a".repeat(49)}` };
const spec = JSON.parse(
  readFileSync(
    new URL("../../../contracts/developer.openapi.json", import.meta.url),
    "utf8",
  ),
);
const listSchema =
  spec.paths["/callout/{calloutId}/replies"].get.responses[200].content[
    "application/json"
  ].schema;
const chainSchema =
  spec.paths["/callout/replies/{replyId}/chain"].get.responses[200].content[
    "application/json"
  ].schema;
function calloutsData(): CalloutsDataset {
  const facts = (id: string): CalloutFacts => ({
    calloutId: id,
    userId: "synthetic-acting-wallet",
    coinMint: "synthetic-mint",
    marketCap: 10,
    calloutPrice: 0,
    calloutPriceUsd: 1,
    multiple: 1,
    createdAt: 0,
    maxPriceSol: 0,
    maxPriceUsd: 1,
    likes: 0,
    repostCount: 0,
    quoteCount: 0,
    updateCount: 0,
    commentCount: 0,
    replyCount: 0,
    maxMultiplier: null,
    maxMultiplierAt: null,
    mediaUrl: null,
    quotedCalloutId: null,
  });
  const quote = (id: string): QuoteFacts => ({
    calloutId: id,
    calledOutAtMcap: 10,
    multiple: 1,
    thesis: "public callout",
    mediaUrl: null,
    calloutTimestamp: now,
    likes: 0,
    updateCount: 0,
    commentCount: 0,
    replyCount: 0,
    maxMultiplier: null,
    maxMultiplierAt: null,
    calloutPrice: 1,
    repostCount: 0,
    quoteCount: 0,
    actingUserId: null,
    actingUser: null,
  });
  return {
    schemaVersion: 1,
    dataSource: "synthetic",
    observedAt: now,
    authors: [
      {
        authorId: "owner",
        userName: "Owner",
        profileImage: null,
        isVerified: false,
        verifiedBadgeVisible: false,
        accountKind: "person",
        xUsername: null,
        xFollowerCount: 0,
      },
    ],
    callouts: ["root", "empty", "other"].map((calloutId) => ({
      calloutId,
      authorId: "owner",
      hidden: false,
      deleted: false,
      facts: facts(calloutId),
      quoteFacts: quote(calloutId),
    })),
    updates: [],
  };
}
function facts(content: string, second: number | null): DiscussionFacts {
  return {
    content,
    createdAt:
      second === null
        ? null
        : `2026-10-29T00:00:${String(second).padStart(2, "0")}.000Z`,
    likeCount: 0,
    mediaUrl: null,
    repostCount: 0,
    positionAmountHeld: null,
    positionValueUsd: null,
    positionPnlUsd: null,
    positionPnlPercentage: null,
    positionCostBasisAmount: 0,
    positionCostBasisUsd: null,
    positionAmountBoughtUsd: null,
    positionAmountBought: null,
    positionRealizedPnlUsd: null,
    positionAvgEntryMcapUsd: null,
  };
}
function node(
  replyId: string,
  parentReplyId: string | null,
  authorId = "bob",
  second: number | null = 10,
): CalloutDiscussionsDataset["replies"][number] {
  return {
    replyId,
    calloutId: "root",
    parentReplyId,
    kind: "reply",
    hidden: false,
    deleted: false,
    authorId,
    facts: facts(`public ${replyId}`, second),
  };
}
function dataset(): CalloutDiscussionsDataset {
  return {
    schemaVersion: 1,
    dataSource: "synthetic",
    observedAt: now,
    complete: true,
    calloutIds: ["root", "empty", "other"],
    authors: [
      {
        userId: "owner",
        userName: "Owner",
        profileImage: null,
        walletAddress: "synthetic-owner-wallet",
        accountKind: "person",
      },
      {
        userId: "bob",
        userName: "Bob",
        profileImage: null,
        walletAddress: null,
        accountKind: "person",
      },
      {
        userId: "squad",
        userName: "Squad",
        profileImage: null,
        walletAddress: null,
        accountKind: "group",
      },
    ],
    replies: [
      node("top-a", null, "bob", 10),
      node("top-b", null, "owner", 20),
      node("old-owner", "top-a", "owner", 11),
      node("new-bob", "top-a", "bob", 12),
      node("new-owner", "top-a", "owner", 13),
      node("grandchild", "new-bob", "squad", 14),
    ],
  };
}
function store(data = dataset(), callouts = calloutsData()) {
  return new CalloutDiscussionsStore(data, new CalloutsStore(callouts));
}
const q = (text = "") => new URLSearchParams(text);
test('discussion file admission enforces its advertised observation checkpoint', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'discussion-checkpoint-'));
  const path = join(dir, 'discussions.json');
  try {
    for (const createdAt of [null, '2026-10-29T00:00:59.999Z', now, '2026-10-29T00:01:00.001Z']) {
      const data = dataset();
      data.replies = [node('checkpoint-reply', null)];
      data.replies[0].facts!.createdAt = createdAt;
      writeFileSync(path, JSON.stringify(data));
      const load = () => loadCalloutDiscussionsStore(path, new CalloutsStore(calloutsData()));
      if (createdAt !== null && Date.parse(createdAt) > Date.parse(now)) {
        assert.throws(load, /reply timestamp exceeds observedAt/);
        continue;
      }
      const app = buildApp([], { calloutDiscussionsStore: load() });
      try {
        const origin = await app.listen({ host: '127.0.0.1', port: 0 });
        const response = await fetch(`${origin}/v1/callout/root/replies`, { headers });
        assert.equal(response.status, 200);
        assert.equal(response.headers.get('x-reconstruction-observed-at'), now);
        assert.equal((await response.json() as { replies: { createdAt: string | null }[] }).replies[0].createdAt, createdAt);
      } finally {
        await app.close();
      }
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
function fails(fn: () => unknown, status: number, reason?: string) {
  assert.throws(
    fn,
    (e: unknown) =>
      e instanceof CalloutDiscussionError &&
      e.status === status &&
      (!reason || e.reason === reason),
  );
}

test("live discussion pages assemble canonical identities and local topology against the exact DTO", () => {
  const s = store(),
    result = s.list("root");
  assertSchema(result, listSchema, "list", spec);
  assert.deepEqual(
    result.replies.map((r) => r.id),
    ["top-b", "top-a"],
  );
  const a = result.replies[1];
  assert.equal(a.userId, "bob");
  assert.equal(a.userName, "Bob");
  assert.equal(a.parentMessageId, null);
  assert.equal(a.rootMessageId, null);
  assert.equal(a.directReplyCount, 3);
  assert.equal(a.threadReplyCount, 4);
  assert.equal(a.authorReply!.id, "old-owner");
  assert.deepEqual(a.previewReplies, []);
  assert.equal(a.hasLiked, null);
  assert.equal(a.viewerFollowsAuthor, null);
  assert.equal(a.tombstone, false);
  assert.equal(a.isQuote, false);
  assert.equal(Object.hasOwn(a, "viewCount"), false);
  assert.equal(a.positionValueUsd, null);
  assert.equal(a.positionCostBasisAmount, 0);
  assert.deepEqual(s.list("empty"), { replies: [] });
  assert.deepEqual(
    s.list("root", q("filter=AUTHOR_ONLY")).replies.map((r) => r.id),
    ["top-b"],
  );
  assert.deepEqual(
    s.list("root", q("filter=EXCLUDE_AUTHOR")).replies.map((r) => r.id),
    ["top-a"],
  );
});
test("direct-child selection, preview deduplication and ancestor order are separate projections", () => {
  const s = store(),
    result = s.list("root", q("nestedLimit=2"));
  assertSchema(result, listSchema, "nested", spec);
  const a = result.replies[1];
  assert.deepEqual(
    a.previewReplies.map((r) => r.id),
    ["new-owner", "new-bob"],
  );
  assert.equal(a.authorReply!.id, "old-owner");
  assert.ok(
    a.previewReplies.every(
      (r) => r.previewReplies.length === 0 && r.authorReply === null,
    ),
  );
  const children = s.list("root", q("parentReplyId=top-a"));
  assert.deepEqual(
    children.replies.map((r) => r.id),
    ["new-owner", "new-bob", "old-owner"],
  );
  assert.ok(
    children.replies.every(
      (r) =>
        r.rootMessageId === "top-a" &&
        r.parentMessageId === "top-a" &&
        r.threadReplyCount === null,
    ),
  );
  const chain = s.chain("grandchild");
  assertSchema(chain, chainSchema, "chain", spec);
  assert.deepEqual(
    chain.ancestors.map((r) => r.id),
    ["top-a", "new-bob"],
  );
  assert.equal(chain.callout!.userId, "owner");
  assert.equal(chain.callout!.walletAddress, "synthetic-acting-wallet");
  assert.equal(chain.reply.accountKind, "group");
  assert.equal(chain.reply.walletAddress, null);
  assert.equal(chain.reply.userId, "squad");
  assert.deepEqual(s.chain("top-a").ancestors, []);
});
test("pagination uses eligible reply IDs and deterministic null/tie order without invented ranking", () => {
  const data = dataset();
  data.replies.push(
    node("tie-c", null, "bob", 20),
    node("null-time", null, "bob", null),
  );
  const s = store(data);
  assert.deepEqual(
    s.list("root").replies.map((r) => r.id),
    ["top-b", "tie-c", "top-a", "null-time"],
  );
  const seen: string[] = [];
  const query = q("limit=1");
  for (let i = 0; i < 5; i++) {
    const page = s.list("root", query).replies;
    if (!page.length) break;
    seen.push(page[0].id);
    query.set("beforeId", page[0].id);
  }
  assert.deepEqual(seen, ["top-b", "tie-c", "top-a", "null-time"]);
  fails(
    () => s.list("root", q("beforeId=new-bob")),
    400,
    "CALLOUT_DISCUSSION_CURSOR_INVALID",
  );
  fails(() => s.list("root", q("filter=AUTHOR_ONLY&beforeId=top-a")), 400);
  fails(
    () => s.list("empty", q("parentReplyId=top-a")),
    400,
    "CALLOUT_DISCUSSION_PARENT_INVALID",
  );
});
test("nestedLimit caps at the captured10 and author preview uses earliest known child", () => {
  const data = dataset();
  for (let i = 0; i < 15; i++)
    data.replies.push(node(`more-${i}`, "top-a", "bob", i));
  data.replies.push(node("null-owner", "top-a", "owner", null));
  const result = store(data).list("root", q("nestedLimit=9007199254740991"))
    .replies[1];
  assert.equal(result.previewReplies.length, 10);
  assert.equal(result.authorReply!.id, "old-owner");
});
for (const query of [
  "sort=POSITION",
  "sort=PNL",
  "page=0",
  "sort=POSITION&beforeId=top-a",
])
  test(`ranking remains unavailable: ${query}`, () =>
    fails(
      () => store().list("root", q(query)),
      501,
      "CALLOUT_DISCUSSION_RANKING_UNAVAILABLE",
    ));
for (const query of [
  "limit=0",
  "limit=-1",
  "limit=01",
  "limit=1.5",
  "limit=1e2",
  "limit=9007199254740992",
  "limit=",
  "nestedLimit=-1",
  "nestedLimit=NaN",
  "nestedLimit=0.5",
  "filter=author",
  "sort=recency",
  "beforeId=",
  "parentReplyId=",
  "limit=1&limit=2",
  "beforeId=a&beforeId=b",
  "nestedLimit=1&nestedLimit=2",
  "filter=ALL&filter=AUTHOR_ONLY",
])
  test(`invalid query: ${query}`, () =>
    fails(() => store().list("root", q(query)), 400));
for (const query of ["viewer=x", "offset=1", "toString=x"])
  test(`unknown query: ${query}`, () =>
    fails(
      () => store().list("root", q(query)),
      501,
      "CALLOUT_DISCUSSION_QUERY_UNSUPPORTED",
    ));
test("unknown materialization is not known-empty or production not-found", () => {
  const data = dataset();
  data.calloutIds = data.calloutIds.filter((id) => id !== "empty");
  const s = store(data);
  fails(() => s.list("empty"), 501, "CALLOUT_DISCUSSION_UNAVAILABLE");
  fails(() => s.chain("missing"), 501, "CALLOUT_DISCUSSION_REPLY_UNAVAILABLE");
  fails(
    () => s.list("root", q("parentReplyId=missing")),
    400,
    "CALLOUT_DISCUSSION_PARENT_INVALID",
  );
});
test("a hidden/deleted callout body is null in a still-public live chain, not a private context leak", () => {
  for (const flag of ["hidden", "deleted"] as const) {
    const c = calloutsData();
    c.callouts[0][flag] = true;
    c.callouts[0].quoteFacts!.thesis = "private root body";
    const s = store(dataset(), c),
      result = s.chain("grandchild");
    assertSchema(result, chainSchema, "hidden root", spec);
    assert.equal(result.callout, null);
    assert.equal(JSON.stringify(result).includes("private root body"), false);
    assert.ok(result.ancestors.every((r) => r.authorReply === null));
    fails(() => s.list("root"), 501, "CALLOUT_DISCUSSION_CALLOUT_UNAVAILABLE");
  }
});
test("missing root projection is explicit unavailable, not falsely declared hidden", () => {
  const c = calloutsData();
  delete c.callouts[0].quoteFacts;
  const s = store(dataset(), c);
  assert.equal(s.list("root").replies.length, 2);
  fails(() => s.chain("top-a"), 501, "CALLOUT_DISCUSSION_CONTEXT_UNAVAILABLE");
  c.callouts[0].facts = null;
  const unmapped = store(dataset(), c);
  fails(() => unmapped.list("root"), 501);
  fails(() => unmapped.chain("top-a"), 501);
});
test("dead nodes retain topology only and required tombstone paths fail instead of guessing defaults", () => {
  const data = dataset();
  data.replies.push({
    ...node("dead-leaf", null),
    hidden: true,
    authorId: null,
    facts: null,
  });
  const s = store(data);
  assert.equal(s.list("root").replies.length, 2);
  fails(
    () => s.chain("dead-leaf"),
    501,
    "CALLOUT_DISCUSSION_TOMBSTONES_UNAVAILABLE",
  );
  data.replies.push(
    {
      ...node("dead-bridge", null),
      deleted: true,
      authorId: null,
      facts: null,
    },
    node("live-after-dead", "dead-bridge"),
  );
  const mixed = store(data);
  fails(
    () => mixed.list("root"),
    501,
    "CALLOUT_DISCUSSION_TOMBSTONES_UNAVAILABLE",
  );
  fails(
    () => mixed.chain("live-after-dead"),
    501,
    "CALLOUT_DISCUSSION_TOMBSTONES_UNAVAILABLE",
  );
  fails(
    () => mixed.list("root", q("parentReplyId=dead-bridge")),
    501,
    "CALLOUT_DISCUSSION_TOMBSTONES_UNAVAILABLE",
  );
  assert.deepEqual(
    mixed.list("root", q("filter=AUTHOR_ONLY")).replies.map((r) => r.id),
    ["top-b"],
  );
});
test("counts are the declared local graph's live descendants at all depths, including behind dead bridges", () => {
  const data = dataset();
  data.replies.push(
    {
      ...node("dead-bridge", "top-a"),
      hidden: true,
      authorId: null,
      facts: null,
    },
    node("live-after-dead", "dead-bridge"),
  );
  const s = store(data);
  const a = s.list("root").replies[1];
  assert.equal(a.directReplyCount, 3);
  assert.equal(a.threadReplyCount, 5);
  fails(() => s.list("root", q("parentReplyId=top-a")), 501);
  assert.equal(
    s.list("root", q("parentReplyId=top-a&filter=EXCLUDE_AUTHOR")).replies
      .length,
    1,
  );
});
test("supplied financial knowledge and zero are retained; neither ranking nor arithmetic is performed", () => {
  const data = dataset();
  Object.assign(data.replies[0].facts!, {
    positionPnlUsd: -4,
    positionAmountHeld: 0,
    positionCostBasisAmount: 5,
    viewCount: 0,
  });
  const r = store(data).list("root").replies[1];
  assert.equal(r.positionPnlUsd, -4);
  assert.equal(r.positionAmountHeld, 0);
  assert.equal(r.positionCostBasisAmount, 5);
  assert.equal(r.positionCostBasisUsd, null);
  assert.equal(r.viewCount, 0);
});
test("input, nested list and chain mutations cannot alter future reads", () => {
  const data = dataset(),
    c = calloutsData(),
    s = store(data, c),
    before = s.list("root", q("nestedLimit=2"));
  data.authors[0].userName = "mutated";
  data.replies[0].facts!.content = "mutated";
  c.callouts[0].hidden = true;
  const changed = s.list("root", q("nestedLimit=2"));
  changed.replies[1].authorReply!.content = "mutated";
  changed.replies[1].previewReplies[0].content = "mutated";
  const chain = s.chain("grandchild");
  chain.callout!.callout.thesis = "mutated";
  chain.ancestors[0].content = "mutated";
  assert.deepEqual(s.list("root", q("nestedLimit=2")), before);
  assert.equal(s.chain("grandchild").callout!.callout.thesis, "public callout");
});
for (const [name, change] of [
  ["unknown completeness", (d: any) => delete d.complete],
  ["duplicate reply", (d: any) => d.replies.push(d.replies[0])],
  ["duplicate author", (d: any) => d.authors.push(d.authors[0])],
  ["unknown root", (d: any) => d.calloutIds.push("missing")],
  ["duplicate root", (d: any) => d.calloutIds.push("root")],
  ["unmaterialized root", (d: any) => (d.replies[0].calloutId = "missing")],
  ["dangling parent", (d: any) => (d.replies[0].parentReplyId = "missing")],
  ["self cycle", (d: any) => (d.replies[0].parentReplyId = "top-a")],
  [
    "cycle",
    (d: any) => {
      d.replies[0].parentReplyId = "new-bob";
    },
  ],
  [
    "cross-callout parent",
    (d: any) => {
      d.replies[1].calloutId = "other";
      d.replies[0].parentReplyId = "top-b";
    },
  ],
  ["unresolved author", (d: any) => (d.replies[0].authorId = "missing")],
  [
    "group wallet",
    (d: any) => (d.authors[2].walletAddress = "private-admin-wallet"),
  ],
  ["dead content", (d: any) => (d.replies[0].hidden = true)],
  [
    "dead identity",
    (d: any) => {
      d.replies[0].hidden = true;
      d.replies[0].facts = null;
    },
  ],
  ["live null facts", (d: any) => (d.replies[0].facts = null)],
  ["live null author", (d: any) => (d.replies[0].authorId = null)],
  ["quote kind", (d: any) => (d.replies[0].kind = "quote")],
  ["implicit visibility", (d: any) => delete d.replies[0].hidden],
  ["viewer state", (d: any) => (d.replies[0].facts.hasLiked = true)],
  ["injected tree", (d: any) => (d.replies[0].facts.previewReplies = [])],
  ["invented count", (d: any) => (d.replies[0].facts.threadReplyCount = 99)],
  [
    "unsafe count",
    (d: any) => (d.replies[0].facts.likeCount = Number.MAX_SAFE_INTEGER + 1),
  ],
  [
    "negative spot amount",
    (d: any) => (d.replies[0].facts.positionAmountHeld = -1),
  ],
  [
    "nonfinite financial fact",
    (d: any) => (d.replies[0].facts.positionPnlUsd = Infinity),
  ],
  [
    "invalid date",
    (d: any) => (d.replies[0].facts.createdAt = "2026-02-30T00:00:00Z"),
  ],
  ["source mismatch", (d: any) => (d.dataSource = "local-materialized")],
  ["snapshot mismatch", (d: any) => (d.observedAt = "2026-10-29T01:00:00Z")],
  ["prototype field", (d: any) => (d.replies[0].facts.toString = "private")],
  [
    "accessor",
    (d: any) =>
      Object.defineProperty(d.replies[0].facts, "secret", {
        enumerable: true,
        get() {
          throw new Error("must never run");
        },
      }),
  ],
] as const)
  test(`admission rejects ${name}`, () => {
    const data = dataset();
    change(data);
    assert.throws(() => store(data));
  });
test("long ancestry is iterative and replies with prototype-named IDs remain inert", () => {
  const data = dataset();
  data.replies = [];
  for (let i = 0; i < 1000; i++)
    data.replies.push(node(`deep-${i}`, i === 0 ? null : `deep-${i - 1}`));
  const s = store(data);
  assert.equal(s.chain("deep-999").ancestors.length, 999);
  assert.equal(s.list("root").replies[0].threadReplyCount, 999);
  const inert = dataset();
  inert.replies = [node("toString", null), node("__proto__", "toString")];
  assert.equal(store(inert).chain("__proto__").ancestors[0].id, "toString");
});
test("optional regular-file loader bounds bytes and validates data without network or default seed", () => {
  const dir = mkdtempSync(join(tmpdir(), "callout-discussions-")),
    path = join(dir, "input.json"),
    c = new CalloutsStore(calloutsData());
  try {
    writeFileSync(path, JSON.stringify(dataset()));
    assert.equal(
      loadCalloutDiscussionsStore(path, c).list("root").replies.length,
      2,
    );
    writeFileSync(path, Buffer.from([0xff]));
    assert.throws(() => loadCalloutDiscussionsStore(path, c));
    writeFileSync(path, "{");
    assert.throws(() => loadCalloutDiscussionsStore(path, c));
    truncateSync(path, 8 * 1024 * 1024 + 1);
    assert.throws(() => loadCalloutDiscussionsStore(path, c));
    assert.throws(() => loadCalloutDiscussionsStore(dir, c));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
test("opt-in HTTP handlers preserve fixture mode, shape auth, explicit errors and source labels", async () => {
  const fixture: Fixture = {
    method: "GET",
    path: "/v1/callout/root/replies",
    status: 200,
    body: { stale: true },
    source: "synthetic fixture",
  };
  const disabled = buildApp([fixture]),
    enabled = buildApp([fixture], { calloutDiscussionsStore: store() });
  try {
    assert.deepEqual(
      (await disabled.inject({ url: fixture.path, headers })).json(),
      fixture.body,
    );
    assert.equal(
      (
        await disabled.inject({
          url: "/v1/callout/replies/top-a/chain",
          headers,
        })
      ).statusCode,
      501,
    );
    for (const url of [fixture.path, "/v1/callout/replies/grandchild/chain"]) {
      assert.equal((await enabled.inject({ url })).statusCode, 401);
      const response = await enabled.inject({ url, headers });
      assert.equal(response.statusCode, 200);
      assertSchema(
        response.json(),
        url === fixture.path ? listSchema : chainSchema,
        "HTTP",
        spec,
      );
      assert.equal(
        response.headers["x-reconstruction-data-source"],
        "synthetic",
      );
      assert.equal(response.headers["x-reconstruction-observed-at"], now);
      assert.equal(
        response.headers["x-reconstruction-compatibility"],
        "unqualified",
      );
    }
    for (const [suffix, status] of [
      ["?limit=1&limit=2", 400],
      ["?sort=POSITION", 501],
      ["?sort=RECENCY?ignored", 400],
      ["?viewer=x", 501],
    ] as const)
      assert.equal(
        (await enabled.inject({ url: fixture.path + suffix, headers }))
          .statusCode,
        status,
      );
    assert.equal(
      (
        await enabled.inject({
          url: "/v1/callout/replies/grandchild/chain?viewer=x",
          headers,
        })
      ).statusCode,
      501,
    );
    assert.equal(
      (await enabled.inject({ url: "/v1/callout/root/quotes", headers }))
        .statusCode,
      501,
    );
    const head = await enabled.inject({
      method: "HEAD",
      url: fixture.path,
      headers,
    });
    assert.equal(head.statusCode, 200);
    assert.equal(head.body, "");
  } finally {
    await disabled.close();
    await enabled.close();
  }
});

test("local default limit is30, with explicit max-safe limits and complete traversal", () => {
  const data = dataset();
  data.replies = Array.from({ length: 35 }, (_, i) =>
    node(`row-${i}`, null, "bob", i),
  );
  const s = store(data);
  assert.equal(s.list("root").replies.length, 30);
  assert.equal(s.list("root", q("limit=9007199254740991")).replies.length, 35);
  const first = s.list("root").replies;
  assert.equal(
    s.list("root", q(`beforeId=${first.at(-1)!.id}`)).replies.length,
    5,
  );
});
test("server rejects missing context or invalid discussion input before acquiring local media", () => {
  const dir = mkdtempSync(join(tmpdir(), "discussion-startup-"));
  try {
    const calloutPath = join(dir, "callouts.json"),
      discussionPath = join(dir, "discussions.json"),
      mediaPath = join(dir, "media");
    writeFileSync(calloutPath, JSON.stringify(calloutsData()));
    writeFileSync(
      discussionPath,
      JSON.stringify({ ...dataset(), complete: false }),
    );
    for (const withContext of [false, true]) {
      const result = spawnSync(
        process.execPath,
        ["--import", "tsx", "src/server.ts"],
        {
          cwd: fileURLToPath(new URL("../", import.meta.url)),
          encoding: "utf8",
          timeout: 10000,
          env: {
            PATH: process.env.PATH,
            CALLOUT_DISCUSSIONS_FILE: discussionPath,
            ...(withContext ? { CALLOUTS_FILE: calloutPath } : {}),
            LOCAL_MEDIA_DIRECTORY: mediaPath,
            LOCAL_MEDIA_TOKEN: "m".repeat(32),
            HOST: "127.0.0.1",
          },
        },
      );
      assert.equal(result.signal, null);
      assert.notEqual(result.status, 0);
      assert.match(
        result.stderr,
        withContext
          ? /Invalid callout discussions/
          : /CALLOUT_DISCUSSIONS_FILE requires CALLOUTS_FILE/,
      );
      assert.equal(existsSync(mediaPath), false);
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
test("discussion, callout, positions and media stores compose without weakening distinct gates", async () => {
  const dir = mkdtempSync(join(tmpdir(), "discussion-composed-"));
  try {
    const calloutsStore = new CalloutsStore(calloutsData());
    const positionsStore = new PositionsStore({
      schemaVersion: 1,
      dataSource: "synthetic",
      observedAt: now,
      subjects: [{ kind: "person", id: "person", aliases: [], positions: [] }],
      coins: [],
      callouts: [],
      updates: [],
    });
    const calloutDiscussionsStore = new CalloutDiscussionsStore(
      dataset(),
      calloutsStore,
    );
    const app = await startWithLocalMedia(
      { LOCAL_MEDIA_DIRECTORY: dir, LOCAL_MEDIA_TOKEN: "m".repeat(32) },
      async (localMedia) =>
        buildApp([], {
          calloutsStore,
          calloutDiscussionsStore,
          positionsStore,
          localMedia,
        }),
    );
    try {
      for (const url of [
        "/v1/callout/root",
        "/v1/callout/root/replies",
        "/v1/callout/replies/grandchild/chain",
        "/v1/user-positions/person?mints=synthetic-mint&updatesLimit=0",
      ]) {
        assert.equal((await app.inject({ url, headers })).statusCode, 200);
        assert.equal((await app.inject({ url })).statusCode, 401);
      }
      assert.equal(
        (
          await app.inject({
            method: "POST",
            url: "/__reconstruction/media/images",
            headers,
          })
        ).statusCode,
        401,
      );
    } finally {
      await app.close();
    }
    const reopened = await startWithLocalMedia(
      { LOCAL_MEDIA_DIRECTORY: dir, LOCAL_MEDIA_TOKEN: "m".repeat(32) },
      async (localMedia) => buildApp([], { localMedia }),
    );
    await reopened.close();
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
