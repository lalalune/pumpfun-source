import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { once } from "node:events";
import {
  createHomeFeedRead,
  normalizerVariants,
  helperContexts,
} from "../reconstruction/home-feed-state/client.mjs";
import { derive, verify } from "../scripts/original-home-feed-state.mjs";
import { fileURLToPath } from "node:url";

const unused = () => {
  throw Error("This semantic check does not invoke a React runtime");
};
function boundary(normalizerVariant, helperContext, overrides = {}) {
  return createHomeFeedRead({
    normalizerVariant,
    helperContext,
    React: {},
    useMemoCache: unused,
    useQuery: unused,
    useHomeFeedSeed: unused,
    fetchHomeFeed: unused,
    decodeBase58: () => new Uint8Array(32),
    ...overrides,
  });
}
function row() {
  return {
    coinMint: "mint",
    chain: "Solana",
    chain_id: "near:mainnet",
    coinName: "Coin",
    symbol: "COIN",
    position: {
      userId: "cc-user",
      walletAddress: "Wallet",
      userName: " Alice ",
      callout: {
        calloutId: "callout",
        thesis: " note ",
        calloutTimestamp: "2026-10-28T00:00:00Z",
      },
    },
  };
}

test("entire maintained hook, normalizers and binding packet reproduce from inert captured ASTs", async () => {
  assert.deepEqual(await verify(), {
    normalizerVariants: 6,
    witnesses: 61,
    mounted: false,
    productionOperationsQualified: 0,
  });
});

test("actual verifier rejects changed identity cache, timer, retirement cap, variant and dependency evidence", async () => {
  const root = fileURLToPath(new URL("../", import.meta.url));
  const original = await derive(root);
  const mutations = [
    (value) => {
      value.code = value.code.replace("new WeakMap()", "new Map()");
    },
    (value) => {
      value.code = value.code.replace("i.slice(0, 40)", "i.slice(0, 41)");
    },
    (value) => {
      value.code = value.code.replace("2500", "250");
    },
    (value) => {
      value.contract.normalizationVariants.pop();
    },
    (value) => {
      value.contract.acceptedRequestBoundary.sha256 = "0".repeat(64);
    },
    (value) => {
      value.contract.witnesses[0].sha256 = "0".repeat(64);
    },
  ];
  for (const mutate of mutations) {
    const changed = structuredClone(original);
    mutate(changed);
    assert.notDeepEqual(changed, original);
    await assert.rejects(verify(root, changed));
  }
});

for (const { sha256: variant } of normalizerVariants)
  for (const context of helperContexts) {
    test(`${variant.slice(0, 12)} / ${context.slice(-19)}: row, author, updates and holder aggregation`, () => {
      const { normalizeRow } = boundary(variant, context);
      const raw = row();
      raw.position.amountHeld = 0;
      raw.position.callout.updates = [
        { id: "later", content: "later", createdAt: "2026-10-29T00:00:00Z" },
        {
          id: "nested",
          parentMessageId: "root",
          content: "nested",
          createdAt: "2026-10-27T00:00:00Z",
        },
        {
          id: "unknown",
          parentMessageId: null,
          content: "unknown",
          createdAt: "bad",
        },
        {
          id: "earlier",
          content: "earlier",
          createdAt: "2026-10-28T00:00:00Z",
          likeCount: 0,
        },
      ];
      raw.position.callout.updateCount = 7;
      raw.position.callout.likes = 0;
      raw.position.callout.hasLiked = false;
      raw.followedHolders = {
        holders: [{ userId: "cc-user" }, { userId: "other" }],
        totalCount: 5,
      };
      const result = normalizeRow(raw);
      assert.equal(result.key, "cid:callout");
      assert.equal(result.userId, "Wallet");
      assert.equal(result.authorCcUserId, "cc-user");
      assert.equal(result.username, " Alice ");
      assert.equal(result.note, "note");
      assert.equal(result.coinChain, "near:mainnet");
      assert.equal(result.positionId, "solana:Wallet:mint");
      assert.equal(result.likeCount, 0);
      assert.equal(result.likedByViewer, false);
      assert.deepEqual(
        result.updates.map((x) => x.id),
        ["earlier", "later", "unknown"],
      );
      assert.equal(result.updates[2].createdAt, 0);
      assert.equal(result.updates[0].likedByViewer, false);
      assert.equal(result.updateCount, 6);
      assert.equal(result.positionPnl.amountHeld, 0);
      assert.deepEqual(result.followedHolders, {
        holders: [{ userId: "other" }],
        totalCount: 4,
      });
      assert.equal(raw.followedHolders.holders.length, 2);
      const unchanged = { holders: [{ userId: "other" }], totalCount: 1 };
      raw.followedHolders = unchanged;
      assert.equal(normalizeRow(raw).followedHolders, unchanged);
    });
    test(`${variant.slice(0, 12)} / ${context.slice(-19)}: quote precedence, tombstones and optional values`, () => {
      const { normalizeRow } = boundary(variant, context);
      const raw = row();
      raw.position.contentKind = "quote";
      raw.position.quote = {
        reply: {
          id: "reply",
          content: "quoted reply",
          createdAt: null,
          tombstone: false,
        },
        parent: {
          id: "parent",
          userName: " Parent ",
          walletAddress: "",
          content: " parent text ",
          tombstone: false,
        },
        callout: {
          userName: "Callout author",
          walletAddress: "other",
          callout: { calloutId: "older", thesis: "other text" },
        },
      };
      let result = normalizeRow(raw);
      assert.deepEqual(result.quote.quoted, {
        authorName: "Parent",
        authorAddress: "",
        text: "parent text",
        deleted: false,
      });
      assert.equal(result.quote.quotedContentId, "parent");
      assert.equal(result.quote.calloutId, "older");
      raw.position.quote.parent.tombstone = true;
      assert.deepEqual(normalizeRow(raw).quote.quoted, { deleted: true });
      raw.position.quote.parent = null;
      assert.equal(normalizeRow(raw).quote.quoted.authorName, "Callout author");
      raw.position.quote.reply.tombstone = true;
      assert.equal(Object.hasOwn(normalizeRow(raw), "quote"), false);
      raw.position.walletAddress = "";
      assert.equal(normalizeRow(raw).userId, "");
      assert.equal(normalizeRow({ ...raw, position: null }), null);
      raw.position.callout.calloutId = null;
      assert.equal(normalizeRow(raw), null);
      raw.position.callout.calloutId = undefined;
      assert.equal(normalizeRow(raw).key, "cid:undefined"); // no invented response admission
    });
  }

test("position keys preserve codec boundary, EVM case handling and absent-chain fallback", () => {
  const variant = normalizerVariants[0].sha256,
    context = helperContexts[0];
  const seen = [];
  const { normalizeRow } = boundary(variant, context, {
    decodeBase58: (mint) => {
      seen.push(mint);
      return new Uint8Array(mint === "solana-mint" ? 32 : 31);
    },
  });
  const raw = row();
  raw.chain = "";
  raw.coinMint = "solana-mint";
  assert.equal(normalizeRow(raw).positionId, "solana:Wallet:solana-mint");
  raw.coinMint = "other";
  assert.equal(normalizeRow(raw).positionId, "unknown:Wallet:other");
  raw.chain = "EVM";
  raw.coinMint = "0XABC";
  raw.position.walletAddress = "0xDEF";
  assert.equal(normalizeRow(raw).positionId, "evm:0xdef:0xabc");
  assert.deepEqual(seen, ["solana-mint", "other"]);
  const failing = boundary(variant, context, {
    decodeBase58: () => {
      throw Error("bad base58");
    },
  });
  raw.chain = "";
  assert.equal(failing.normalizeRow(raw).positionId, "unknown:0xdef:0xabc");
});

test("matching prefetch/query callback reaches one real local HTTP response without a cursor request", async (t) => {
  const requests = [];
  const server = http.createServer((request, response) => {
    requests.push({ method: request.method, url: request.url });
    response.setHeader("Content-Type", "application/json");
    response.end(JSON.stringify({ coins: [row()] }));
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  t.after(() => new Promise((resolve) => server.close(resolve)));
  const address = server.address();
  const signal = new AbortController().signal;
  let options,
    calls = 0;
  const read = boundary(normalizerVariants[0].sha256, helperContexts[0], {
    fetchHomeFeed: async (input) => {
      calls++;
      assert.deepEqual(input, {
        pageSize: 150,
        chain: "all",
        includeFollowedHolders: false,
        viewerAddress: null,
        signal,
      });
      return (
        await fetch(
          `http://127.0.0.1:${address.port}/synthetic-ranked-snapshot`,
          { signal: input.signal },
        )
      ).json();
    },
  });
  const result = await read.prefetchHomeFeed({
    prefetchQuery: async (value) => {
      options = value;
      return value.queryFn({ signal });
    },
  });
  assert.deepEqual(options.queryKey, [
    "callouts",
    "home-feed",
    "all",
    150,
    false,
    null,
  ]);
  assert.equal(options.staleTime, 15000);
  assert.equal(options.retry, 3);
  assert.equal(calls, 1);
  assert.deepEqual(requests, [
    { method: "GET", url: "/synthetic-ranked-snapshot" },
  ]);
  assert.equal(read.normalizeRow(result.coins[0]).calloutId, "callout");
});
