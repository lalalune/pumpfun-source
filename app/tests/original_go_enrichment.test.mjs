import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import {
  mkdtemp,
  mkdir,
  link,
  copyFile,
  readFile,
  writeFile,
  rm,
} from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createBountyEnrichment } from "../reconstruction/go-enrichment/client.mjs";
import {
  verify,
  APP_ROOT,
  DIRECTORY,
} from "../scripts/original-go-enrichment.mjs";
const require = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const React = require("react"),
  { renderToString } = require("react-dom/server"),
  { c: memoCache } = require("react/compiler-runtime");
const SOL = "So11111111111111111111111111111111111111112",
  USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
export function bounty(patch = {}) {
  return {
    taskId: "synthetic-task",
    title: "Synthetic title",
    bodyMarkdown: " First line\nsecond line\n\n Next paragraph ",
    criteria: [
      { order: 2, text: "second" },
      { order: 1, text: "first" },
    ],
    rewardLegs: [],
    status: "OPEN",
    createdAt: "2026-01-01T00:00:00.000Z",
    creatorAddress: "synthetic-creator",
    coinAddress: "synthetic-coin",
    counts: { submissionCount: 3 },
    likeCount: 4,
    viewerLiked: false,
    ...patch,
  };
}
function setup({
  viewer = "synthetic-viewer",
  coinResult = {},
  profileResult = {},
  nowMs = () => Date.parse("2026-01-02T00:00:00.000Z"),
} = {}) {
  const calls = { coins: [], profiles: [], viewer: 0, prefix: 0 };
  const ports = {
    memoCache,
    useViewerSnapshot: () => {
      calls.viewer++;
      return { address: viewer };
    },
    useBatchProfiles: (arg) => {
      calls.profiles.push(arg);
      return profileResult;
    },
    useCoinQuery: (...args) => {
      calls.coins.push(args);
      return coinResult;
    },
    useIpfsPrefix: () => {
      calls.prefix++;
      return { ipfsPrefix: "https://synthetic.invalid/ipfs/" };
    },
    nowMs,
  };
  const adapter = createBountyEnrichment(ports);
  return {
    adapter,
    ports,
    calls,
    render(rows, kind = "useEnrichedBounties") {
      let result;
      function App() {
        result = adapter[kind](rows);
        return React.createElement("output", null, "synthetic");
      }
      renderToString(React.createElement(App));
      return result;
    },
  };
}
test("complete selected source authenticates15physical variants, actual caller, memo/query ports and accepted normalizer", async () => {
  const p = await verify();
  assert.deepEqual(
    p.groups.map((g) => [g.id, g.proofs.length]),
    [
      [260095, 1],
      [242663, 2],
      [609252, 9],
      [462024, 2],
      [456647, 1],
    ],
  );
  for (const g of p.groups)
    for (const op of g.proofs[0].operations)
      assert.equal(
        new Set(
          g.proofs.map(
            (x) =>
              x.operations.find((o) => o.name === op.name).normalizedSha256,
          ),
        ).size,
        1,
      );
  assert.equal(p.caller.factory.id, 851373);
  assert.equal(p.ports.useCoinQuery.factory.id, 689943);
  assert.equal(p.ports.memoCache.target.id, 532815);
  assert.match(p.caller.credit, /OPEN1854/);
  assert.match(p.credit.join(" "), /1812/);
});
test("all query/viewer/compiler/clock ports are explicit and no transport default is installed", () => {
  const h = setup();
  for (const name of Object.keys(h.ports))
    assert.throws(
      () => createBountyEnrichment({ ...h.ports, [name]: undefined }),
      /Explicit enrichment capability/,
    );
  assert.deepEqual(Object.keys(h.adapter), [
    "useEnrichedBounties",
    "useBountyTokens",
    "mapBounty",
  ]);
  assert.deepEqual(h.calls.coins, []);
  assert.deepEqual(h.calls.profiles, []);
});
test("actual display mapper preserves markdown, copied criterion ordering, nullable/passthrough fields and expiry", () => {
  const row = bounty({
      attachments: [],
      rewardDistribution: "synthetic-distribution",
      moderationStatus: "NONE",
      isNsfw: true,
      rewardTotalUsd: 7,
      rewardLegsUsd: [7],
      rewardPricedAt: "synthetic-price-time",
    }),
    before = structuredClone(row);
  const result = setup().adapter.mapBounty(row);
  assert.equal(result.id, row.taskId);
  assert.equal(result.title, row.title);
  assert.equal(result.summary, "First line");
  assert.deepEqual(result.description, [
    "First line\nsecond line",
    "Next paragraph",
  ]);
  assert.equal(result.descriptionMarkdown, row.bodyMarkdown.trim());
  assert.deepEqual(result.deliverables, ["first", "second"]);
  assert.equal(result.expiresAt, "2026-01-08T00:00:00.000Z");
  assert.equal(result.createdAt, row.createdAt);
  assert.equal(result.submissionCount, 3);
  assert.equal(result.likeCount, 4);
  assert.equal(result.viewerLiked, false);
  assert.strictEqual(result.attachments, row.attachments);
  assert.equal(result.rewardDistribution, row.rewardDistribution);
  assert.equal(result.rewardTotalUsd, 7);
  assert.strictEqual(result.rewardLegsUsd, row.rewardLegsUsd);
  assert.equal(result.isNsfw, true);
  assert.deepEqual(row, before);
  const long = setup().adapter.mapBounty(
    bounty({ bodyMarkdown: "x".repeat(161) }),
  );
  assert.equal(long.summary, "x".repeat(157) + "…");
  const empty = setup().adapter.mapBounty(bounty({ bodyMarkdown: " \n " }));
  assert.equal(empty.summary, "");
  assert.deepEqual(empty.description, []);
  assert.equal(
    setup().adapter.mapBounty(bounty({ createdAt: "invalid" })).expiresAt,
    "invalid",
  );
});
test("display dates preserve nullish precedence rather than inventing an epoch or freshness clock", () => {
  const map = setup().adapter.mapBounty;
  const r = map(bounty({ expiresAt: "", publishedAt: "", fundedAt: "later" }));
  assert.equal(r.expiresAt, "");
  assert.equal(r.createdAt, "");
  assert.equal(
    map(bounty({ publishedAt: null, fundedAt: "funded" })).createdAt,
    "funded",
  );
  assert.equal(
    map(bounty({ publishedAt: "published", fundedAt: "funded" })).createdAt,
    "published",
  );
});
test("reward fields are exact source display conversions, including digit admission, fallback and Number precision loss", () => {
  const map = setup().adapter.mapBounty;
  for (const [mint, decimals, amount, value, currency] of [
    [SOL, 9, "1234567890", 1.23456789, "SOL"],
    [USDC, 6, "0000123456", 0.123456, "USDC"],
    ["synthetic-token", 2, "1200", 12, "USDC"],
    [
      "synthetic-token",
      0,
      "9007199254740993",
      Number("9007199254740993"),
      "USDC",
    ],
  ]) {
    const r = map(
      bounty({
        rewardLegs: [
          {
            mintAddress: mint,
            amountAtomic: amount,
            decimalsSnapshot: decimals,
            symbolSnapshot: "SYN",
          },
        ],
      }),
    );
    assert.equal(r.reward, value);
    assert.equal(r.currency, currency);
    assert.equal(r.rewardTokenAmount, value);
    assert.equal(r.rewardBreakdown[0].amount, value);
    if (mint === "synthetic-token") {
      assert.equal(r.rewardToken.mint, mint);
      assert.equal(r.rewardToken.symbol, "SYN");
    }
  }
  for (const bad of [
    "-1",
    "1e2",
    "1.2",
    "Infinity",
    "not-digits",
    "9".repeat(400),
  ]) {
    const r = map(
      bounty({
        rewardLegs: [
          { mintAddress: USDC, amountAtomic: bad, decimalsSnapshot: 0 },
        ],
      }),
    );
    assert.equal(r.reward, 0);
    assert.deepEqual(r.rewardBreakdown, []);
  }
  const absent = map(bounty());
  assert.equal(absent.reward, 0);
  assert.equal(absent.currency, "USDC");
  assert.equal(absent.rewardTokenAmount, undefined);
  const ordered = map(
    bounty({
      rewardLegs: [
        { mintAddress: SOL, amountAtomic: "0", decimalsSnapshot: 9 },
        { mintAddress: USDC, amountAtomic: "1", decimalsSnapshot: 0 },
        { mintAddress: USDC, amountAtomic: "2", decimalsSnapshot: 0 },
      ],
    }),
  );
  assert.equal(ordered.currency, "SOL");
  assert.equal(ordered.reward, 0);
  assert.deepEqual(
    ordered.rewardBreakdown.map((x) => x.amount),
    [1, 2],
  );
});
test("submission and mutation flags retain separate status/resolution/moderation/expiry guards with one explicit clock", () => {
  const map = setup().adapter.mapBounty;
  for (const [patch, status, accept, mutate] of [
    [{}, "open", true, true],
    [{ expiresAt: "2026-01-02T00:00:00.000Z" }, "open", false, true],
    [{ expiresAt: "invalid" }, "open", true, true],
    [{ moderationStatus: "PENDING_REVIEW" }, "open", false, true],
    [{ resolution: { outcomeType: "REFUND" } }, "open", false, false],
    [
      { resolution: { outcomeType: "REFUND" }, payoutMode: "WINNER_BY_WINNER" },
      "open",
      true,
      true,
    ],
    [
      { status: "CLOSED", resolution: { outcomeType: "WINNER_PAYOUT" } },
      "done",
      false,
      false,
    ],
    [
      { status: "CLOSED", resolution: { outcomeType: "SPLIT" } },
      "done",
      false,
      false,
    ],
    [
      { status: "CLOSED", resolution: { outcomeType: "REFUND" } },
      "closed",
      false,
      false,
    ],
  ]) {
    const r = map(bounty(patch));
    assert.equal(r.status, status);
    assert.equal(r.acceptsSubmissions, accept);
    assert.equal(r.allowsSubmissionMutations, mutate);
  }
});
test("winner count uses unique submission/mint pairs and first duplicate claimed truthiness", () => {
  const map = setup().adapter.mapBounty;
  const resolution = {
    winners: [
      { submissionId: "s", mintAddress: "m", claimedAt: 0 },
      { submissionId: "s", mintAddress: "m", claimedAt: 1 },
      { submissionId: "s", mintAddress: "n", claimedAt: "yes" },
      { submissionId: "t", mintAddress: "n", claimedAt: null },
    ],
  };
  let r = map(bounty({ resolution }));
  assert.equal(r.winnerCount, 3);
  assert.equal(r.claimedWinnerCount, 1);
  r = map(bounty({ resolution: { ...resolution, winnerCount: 0 } }));
  assert.equal(r.winnerCount, 0);
  assert.equal(r.claimedWinnerCount, 1);
  r = map(bounty({ resolution: { winnerCount: 9, winners: [] } }));
  assert.equal(r.winnerCount, 9);
  assert.equal(r.claimedWinnerCount, 0);
});
test("viewer/refund/profile/token projection is display-only and preserves case/nullish/empty-string distinctions", () => {
  const map = setup().adapter.mapBounty,
    row = bounty({
      creatorAddress: "Creator",
      resolution: {
        outcomeType: "SPLIT",
        refundClaims: [{ depositor: "cREATOR" }],
      },
    });
  const r = map(row, {
    viewerAddress: "CREATOR",
    creatorUser: {
      address: "profile-address",
      userId: "profile-id",
      username: " \t ",
      profile_image: null,
    },
    coinMeta: { name: "", symbol: "", imageUri: "" },
  });
  assert.equal(r.viewerIsCreator, true);
  assert.equal(r.refundStatus, "claimed");
  assert.deepEqual(r.creator, {
    address: "Creator",
    id: "profile-address",
    creatorUserId: "profile-id",
    username: null,
    profileImage: "",
    rating: 0,
  });
  assert.equal(r.token.name, "");
  assert.equal(r.token.symbol, "");
  assert.equal(r.token.imageUri, "");
  assert.equal(map(row, { viewerAddress: "other" }).refundStatus, "none");
  assert.equal(
    map(
      { ...row, resolution: { outcomeType: "REFUND" } },
      { viewerAddress: "creator" },
    ).refundStatus,
    "pending",
  );
  assert.equal(
    map(
      { ...row, resolution: { outcomeType: "WINNER_PAYOUT" } },
      { viewerAddress: "creator" },
    ).refundStatus,
    "none",
  );
  assert.equal(map({ ...row, coinAddress: "" }).token, undefined);
});
test("real React SSR composes all three memo frames with ordered native-excluding token and unique creator inputs", () => {
  const row = bounty({
      creatorAddress: "A",
      rewardLegs: [
        { mintAddress: SOL, amountAtomic: "1", decimalsSnapshot: 9 },
        {
          mintAddress: "reward-token",
          amountAtomic: "12",
          decimalsSnapshot: 1,
        },
        { mintAddress: USDC, amountAtomic: "1", decimalsSnapshot: 6 },
        {
          mintAddress: "synthetic-coin",
          amountAtomic: "1",
          decimalsSnapshot: 0,
        },
      ],
    }),
    second = bounty({
      taskId: "second",
      creatorAddress: "A",
      coinAddress: "another-coin",
    });
  const raw = {
    mint: "synthetic-coin",
    name: "  LIVE  ",
    symbol: " LIVE ",
    image_uri: "https://synthetic.invalid/image",
    usd_market_cap: 0,
    market_cap: 12,
    total_supply: "1000000",
    base_decimals: 6,
    created_at: 123,
  };
  const h = setup({
      viewer: "a",
      coinResult: { data: [raw], isLoading: false, error: null },
      profileResult: {
        data: [
          { address: "A", username: "first" },
          { address: "A", username: " last " },
        ],
        isPending: false,
      },
    }),
    result = h.render([row, second]);
  assert.deepEqual(h.calls.profiles, [{ userAddresses: ["A"] }]);
  assert.equal(h.calls.coins.length, 1);
  assert.deepEqual(h.calls.coins[0][0], [
    "synthetic-coin",
    "reward-token",
    "another-coin",
  ]);
  assert.deepEqual(h.calls.coins[0][1], {
    limit: 50,
    offset: 0,
    sort: "market_cap",
    order: "DESC",
    includeNsfw: false,
    disabled: false,
  });
  assert.deepEqual(
    [...result.liveTokens.keys()],
    ["synthetic-coin", "reward-token", "another-coin"],
  );
  const t = result.liveTokens.get("synthetic-coin");
  assert.equal(t.liveMarketCap, 12);
  assert.equal(t.livePriceUsd, 12);
  assert.equal(t.liveName, "LIVE");
  assert.equal(t.liveSymbol, "LIVE");
  assert.equal(result.bounties[0].creator.username, "last");
  assert.equal(result.bounties[0].viewerIsCreator, true);
  assert.equal(result.bounties[0].token.name, "LIVE");
  assert.equal(result.bounties[1].token.name, "another-coin");
  assert.equal(result.isEnriching, false);
  assert.equal(raw.created_timestamp, 123); // credited493025 mutation, not copied DTO validation
});
test("empty inputs still call source query hooks with disabled/empty inputs but do not report enrichment loading", () => {
  const h = setup({
      coinResult: { isLoading: true, error: "opaque error" },
      profileResult: { isPending: true },
    }),
    r = h.render([]);
  assert.deepEqual(r.bounties, []);
  assert.equal(r.liveTokens.size, 0);
  assert.equal(r.isEnriching, false);
  assert.deepEqual(h.calls.profiles, [{ userAddresses: [] }]);
  assert.deepEqual(h.calls.coins[0][0], []);
  assert.equal(h.calls.coins[0][1].disabled, true);
  const busy = setup({
    coinResult: { isLoading: true },
    profileResult: { isPending: false },
  }).render([bounty()]);
  assert.equal(busy.isEnriching, true);
});
test("separate actual token hook reuses projection without acquiring viewer or profiles; null differs from undefined query data", () => {
  const h = setup({ coinResult: { data: [], isLoading: false } }),
    r = h.render(
      [bounty({ coinAddress: USDC, rewardLegs: [{ mintAddress: "token" }] })],
      "useBountyTokens",
    );
  assert.ok(r instanceof Map);
  assert.deepEqual([...r.keys()], ["token"]);
  assert.equal(h.calls.viewer, 0);
  assert.equal(h.calls.profiles.length, 0);
  assert.doesNotThrow(() =>
    setup({ coinResult: { data: undefined } }).render([bounty()]),
  );
  assert.throws(() => setup({ coinResult: { data: null } }).render([bounty()]));
});

test("source binding rejects a wrong actual mapper token constant and noncanonical contract bytes", async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), "go-enrichment-source-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  async function copy(name, immutable = false) {
    const target = path.join(root, name);
    await mkdir(path.dirname(target), { recursive: true });
    if (immutable) {
      try {
        await link(path.join(APP_ROOT, name), target);
        return;
      } catch (e) {
        if (e.code !== "EXDEV") throw e;
      }
    }
    await copyFile(path.join(APP_ROOT, name), target);
  }
  for (const name of [
    "evidence/web/manifest.json",
    "recovered/modules.json",
    "reconstruction/search-session/session.mjs",
    "reconstruction/batch-profile-query/client.mjs",
    "reconstruction/batch-profile-query/contract.json",
  ])
    await copy(name);
  const manifest = JSON.parse(
    await readFile(path.join(APP_ROOT, "evidence/web/manifest.json"), "utf8"),
  );
  for (const record of manifest.records)
    if (record.status === 200) await copy(record.path, true);
  await copy(DIRECTORY + "/client.mjs");
  await copy(DIRECTORY + "/contract.json");
  const name = path.join(root, DIRECTORY, "client.mjs"),
    client = await readFile(name, "utf8");
  assert.ok(client.includes("let r = t.i.SOL.mint;"));
  await writeFile(
    name,
    client.replace("let r = t.i.SOL.mint;", "let r = t.i.USDC.mint;"),
  );
  await assert.rejects(verify(root), /module differs/);
  await writeFile(name, client);
  const contract = path.join(root, DIRECTORY, "contract.json");
  await writeFile(
    contract,
    JSON.stringify(JSON.parse(await readFile(contract, "utf8"))),
  );
  await assert.rejects(verify(root), /contract bytes differ/);
});
