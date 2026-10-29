import assert from "node:assert/strict";
import test from "node:test";
import { createBoardResponseAdapter } from "../reconstruction/market-board-response/response.mjs";

function adapter(ports = {}) {
  return createBoardResponseAdapter({
    nowMs: () => 1000000,
    isEvmRecord: ({ chainId }) => chainId === "eip155:1",
    retainChainId: (chain) =>
      ["eip155:1", "ton:-239", "near:mainnet"].includes(chain),
    ...ports,
  });
}
const packet = (entries, serverTs = 1000000, board = "movers") => ({
  entries,
  serverTs,
  board,
});

test("missing arrays are empty, served order is preserved, and entries are not DTO validated", () => {
  const a = adapter({
    nowMs: () => {
      throw Error("unexpected clock");
    },
  });
  for (const value of [null, undefined, {}, { entries: null }, { entries: {} }])
    assert.deepEqual(a.mapCoins(value), []);
  assert.deepEqual(
    a
      .mapCoins(packet([{ m: "z", n: "second alphabetically" }, { m: "a" }]))
      .map((c) => c.mint),
    ["z", "a"],
  );
  assert.throws(() => a.mapCoins(packet([null])), TypeError);
  const sparse = a.mapCoins(packet(Array(2)));
  assert.equal(sparse.length, 2);
  assert.equal(0 in sparse, false);
});

test("coin projection preserves observed defaults and conditional fields without inventing validation", () => {
  const source = {
    m: "mint",
    n: "Name",
    t: "SYM",
    i: "ipfs://image",
    age: 2,
    gd: 1,
    pl: "platform",
    dw: "creator",
    lv: true,
    desc: "description",
    vid: "video",
    mc: Infinity,
    nh: -1,
    ic: true,
    hr: true,
    rid: "id",
    ms: "active",
    mp: true,
    lp: "launchpad",
  };
  const before = structuredClone(source);
  const [coin] = adapter().mapCoins(packet([source]));
  assert.deepEqual(source, before);
  assert.equal(coin.created_timestamp, 998000);
  assert.equal(coin.usd_market_cap, Infinity); // typeof-number check is not finite validation.
  assert.equal(coin.complete, true);
  assert.equal(coin.holder_count, -1);
  assert.equal(coin.is_charity, true);
  assert.equal(coin.is_holder_reward, true);
  assert.equal(coin.rec_id, "id");
  assert.equal(coin.mayhem_state, "active");
  assert.equal(coin.mayhem_is_multiplayer, true);
  assert.equal(coin.board_launchpad, "launchpad");
  assert.equal(coin.associated_bonding_curve, "");
  assert.equal(coin.total_supply, 0);
  assert.equal(coin.market_cap, 0);
  assert.equal(coin.hidden, null);
  assert.equal("rec_rank" in coin, false);
  assert.equal("chain_id" in coin, false);
  const [empty] = adapter().mapCoins(packet([{}]));
  assert.equal(empty.created_timestamp, null);
  assert.equal(empty.mint, "");
  assert.equal(empty.holder_count, undefined);
  for (const key of [
    "is_charity",
    "is_holder_reward",
    "rec_id",
    "mayhem_state",
    "mayhem_is_multiplayer",
    "board_launchpad",
    "followed_holders",
  ])
    assert.equal(key in empty, false, key);
});

test("response board selects program fallback and injected classification/retention stay explicit", () => {
  for (const pg of [
    "pump",
    "meteora_dbc",
    "raydium_launchpad",
    "raydium_launchpad_bonk",
    "loadout",
    "meme_fun",
    "stonkfun",
    "raydium_cpmm",
  ])
    assert.equal(
      adapter().mapCoins(packet([{ pg }], 1, "trending"))[0].program,
      pg,
    );
  for (const pg of [undefined, "", "pump_amm"])
    assert.equal(
      adapter().mapCoins(packet([{ pg }], 1, "trending"))[0].program,
      "pump",
    );
  assert.equal(
    adapter().mapCoins(packet([{ pg: "unknown" }], 1, "trending"))[0].program,
    "non_launchpad",
  );
  assert.equal(
    adapter().mapCoins(packet([{ pg: "unknown" }], 1))[0].program,
    "pump",
  );
  const [evm] = adapter().mapCoins(
    packet([{ pg: "unknown", c: "eip155:1", nh: 0 }], 1, "trending"),
  );
  assert.equal(evm.program, "pump");
  assert.equal(evm.protocol, "unknown");
  assert.equal(evm.chain_id, "eip155:1");
  assert.equal(evm.holder_count, undefined);
  assert.equal(adapter().mapCoins(packet([{ nh: 0 }]))[0].holder_count, 0);
});

test("finite positive serverTs bypasses fallback; fallback is called per visited entry before classification", () => {
  const calls = [];
  const a = adapter({
    nowMs: () => (calls.push("clock"), 900000),
    isEvmRecord: () => (calls.push("evm"), false),
    retainChainId: () => (calls.push("chain"), false),
  });
  assert.equal(
    a.mapCoins(packet([{ age: 1 }], 1234))[0].created_timestamp,
    234,
  );
  assert.deepEqual(calls.splice(0), ["evm", "chain"]);
  for (const invalid of [0, -1, "1234", NaN, Infinity, undefined]) {
    a.mapCoins({ entries: [{ age: 1 }, {}], serverTs: invalid });
    assert.deepEqual(calls.splice(0), [
      "clock",
      "evm",
      "chain",
      "clock",
      "evm",
      "chain",
    ]);
  }
  assert.throws(
    () =>
      adapter({
        nowMs: () => {
          throw Error("clock failed");
        },
      }).mapCoins({ entries: [{}] }),
    /clock failed/,
  );
});

test("timestamp cache reuses strictly below60s, replaces at60s, and keys only on original mint", () => {
  const a = adapter();
  const at = (time, c) =>
    a.mapCoins(packet([{ m: "same", age: 0, c }], time))[0].created_timestamp;
  assert.equal(at(1000000), 1000000);
  assert.equal(at(1059999, "eip155:1"), 1000000);
  assert.equal(at(1060000), 1060000);
  assert.equal(at(1000001), 1060000); // Absolute difference, not monotonicity.
  assert.equal(
    a.mapCoins(packet([{ m: "SAME", age: 0 }], 1060001))[0].created_timestamp,
    1060001,
  );
});

test("seeding accepts positive finite timestamps once and does not replace a known mint", () => {
  const a = adapter();
  a.seedTimestamps([
    { mint: "seeded", created_timestamp: 1000010 },
    { mint: "zero", created_timestamp: 0 },
    { mint: "nan", created_timestamp: NaN },
    { mint: "negative", created_timestamp: -1 },
  ]);
  a.seedTimestamps([{ mint: "seeded", created_timestamp: 1000020 }]);
  const rows = a.mapCoins(
    packet(["seeded", "zero", "nan", "negative"].map((m) => ({ m, age: 0 }))),
  );
  assert.deepEqual(
    rows.map((c) => c.created_timestamp),
    [1000010, 1000000, 1000000, 1000000],
  );
});

test("4000-entry cache keeps insertion order on hits and evicts before replacement", () => {
  const fill = (a) =>
    a.mapCoins(
      packet(Array.from({ length: 4000 }, (_, i) => ({ m: `m${i}`, age: 0 }))),
    );
  const a = adapter();
  fill(a);
  a.mapCoins(packet([{ m: "m0", age: 0 }], 1000001)); // Hit does not refresh insertion order.
  a.mapCoins(packet([{ m: "new", age: 0 }], 1000002));
  assert.equal(
    a.mapCoins(packet([{ m: "m0", age: 0 }], 1000003))[0].created_timestamp,
    1000003,
  );
  const b = adapter();
  fill(b);
  b.mapCoins(packet([{ m: "m100", age: 0 }], 1060000)); // Evicts m0 before replacing m100.
  assert.equal(
    b.mapCoins(packet([{ m: "m0", age: 0 }], 1000001))[0].created_timestamp,
    1000001,
  );
});

test("followed holders preserve null and explicit false/empty fields, defaulting only nullish values", () => {
  const holders = [
    { userId: "a" },
    { verifiedBadgeVisible: false, walletAddress: "" },
  ];
  const original = structuredClone(holders);
  const [nullRow, row] = adapter().mapCoins(
    packet([{ fh: null }, { fh: { totalCount: 8, holders } }]),
  );
  assert.equal(nullRow.followed_holders, null);
  assert.deepEqual(row.followed_holders, {
    totalCount: 8,
    holders: [
      { userId: "a", verifiedBadgeVisible: true, walletAddress: null },
      ...holders.slice(1),
    ],
  });
  assert.deepEqual(holders, original);
  assert.throws(() => adapter().mapCoins(packet([{ fh: {} }])), TypeError);
});

test("rank offset is opt-in and no coercion policy is invented; all ports are required", () => {
  assert.deepEqual(
    adapter()
      .mapCoins(packet([{ m: "b" }, { m: "a" }]), 4)
      .map((c) => c.rec_rank),
    [5, 6],
  );
  assert.equal(adapter().mapCoins(packet([{}]), "2")[0].rec_rank, "201");
  assert.throws(() => createBoardResponseAdapter({}), /ports are required/);
});
