import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  CAPTURED_COIN_ENDPOINT,
  CAPTURED_COIN_PATH,
  CAPTURED_COIN_SHA256,
  parseCoinSnapshotBytes,
  searchHistoricalCoins,
  sha256,
  validateCoinDataset,
  verifySnapshotProvenance,
  type HistoricalCoin,
} from "../packages/frontend/src/app/explore/coin-data.ts";

const capturedObject = new URL(
  "../evidence/web/objects/cd3f926d4d318056",
  import.meta.url,
);
const apiProbes = new URL("../evidence/api-probes.json", import.meta.url);
const manifest = new URL("../evidence/web/manifest.json", import.meta.url);

async function realSnapshot() {
  const [bytes, probes, capturedManifest] = await Promise.all([
    readFile(capturedObject),
    readFile(apiProbes, "utf8").then(JSON.parse),
    readFile(manifest, "utf8").then(JSON.parse),
  ]);
  return { bytes, probes, capturedManifest };
}

function coin(overrides: Partial<HistoricalCoin> = {}): HistoricalCoin {
  return {
    mint: "11111111111111111111111111111111",
    name: "Alpha Coin",
    symbol: "ALPHA",
    ...overrides,
  };
}

test("authenticates and validates the exact captured one-record response", async () => {
  const { bytes, probes, capturedManifest } = await realSnapshot();
  assert.equal(bytes.byteLength, 1813);
  assert.equal(sha256(bytes), CAPTURED_COIN_SHA256);

  const snapshot = verifySnapshotProvenance(bytes, probes, capturedManifest);
  assert.equal(snapshot.endpoint, CAPTURED_COIN_ENDPOINT);
  assert.equal(snapshot.coins.length, 1);
  assert.equal(
    snapshot.coins[0]?.mint,
    "FwgY7679unGLV64cDpzYyfCtzocr7N2NNfbPnZhepump",
  );
  assert.equal(snapshot.coins[0]?.name, "MotoCross");
  assert.equal(snapshot.coins[0]?.symbol, "MotoCrose");
  assert.equal(snapshot.coins[0]?.marketCapUsd, 3300.025664965192);
});

test('Explore provenance requires one probe and the recorded capture checkpoint', async () => {
  const { bytes, probes, capturedManifest } = await realSnapshot();
  const probe = probes.find((record: { url?: string }) => record.url === CAPTURED_COIN_ENDPOINT);
  for (const duplicate of [probe, { ...probe, status: 503 }]) {
    assert.throws(() => verifySnapshotProvenance(bytes, [...probes, duplicate], capturedManifest), /not unique/);
  }
  for (const captured_at of ['2026-10-29T10:48:45.546100+00:00', '2026-02-30T10:48:45Z', '2026-10-28T10:48:45']) {
    assert.throws(() => verifySnapshotProvenance(bytes, probes, { ...capturedManifest, captured_at }), /timestamp/);
  }
  assert.equal(verifySnapshotProvenance(bytes, probes, capturedManifest).capturedAt, capturedManifest.captured_at);
});

test("preserves exact identity while allowing omitted optional fields", () => {
  const input = {
    mint: "MiXeDCaseMint123",
    name: "猫 & Coin",
    symbol: "猫币",
  };
  const [validated] = validateCoinDataset([input]);
  assert.deepEqual(validated, {
    ...input,
    imageUri: undefined,
    createdTimestamp: undefined,
    lastTradeTimestamp: undefined,
    marketCap: undefined,
    marketCapUsd: undefined,
    quoteMint: undefined,
    complete: undefined,
    creator: undefined,
    protocol: undefined,
    verified: undefined,
  });
});

test("rejects missing identity and invalid numeric fields", () => {
  for (const input of [
    { name: "Missing mint", symbol: "MISS" },
    { mint: "mint", name: "", symbol: "EMPTY" },
    { mint: "mint", name: "Bad symbol", symbol: null },
    { mint: "mint", name: "Negative", symbol: "NEG", market_cap_usd: -1 },
    { mint: "mint", name: "NaN", symbol: "NAN", market_cap: Number.NaN },
    {
      mint: "mint",
      name: "Infinite",
      symbol: "INF",
      market_cap_usd: Number.POSITIVE_INFINITY,
    },
    { mint: "mint", name: "Fraction", symbol: "TIME", created_timestamp: 1.5 },
    {
      mint: "mint",
      name: "Unsafe image",
      symbol: "URI",
      image_uri: "javascript:alert(1)",
    },
  ]) {
    assert.throws(() => validateCoinDataset([input]), /Coin/);
  }
});

test("rejects duplicate identities, wrong response shape and altered bytes", async () => {
  assert.throws(
    () => validateCoinDataset([coin(), coin({ name: "Duplicate" })]),
    /repeats a mint identity/,
  );
  assert.throws(() => validateCoinDataset({ coins: [] }), /must be an array/);

  const { bytes } = await realSnapshot();
  const corrupted = Buffer.from(bytes);
  corrupted[0] ^= 1;
  assert.throws(() => parseCoinSnapshotBytes(corrupted), /SHA-256 mismatch/);
});

test("rejects altered API provenance and manifest metadata", async () => {
  const { bytes, probes, capturedManifest } = await realSnapshot();
  const changedProbes = structuredClone(probes);
  const probe = changedProbes.find(
    (value: { url?: string }) => value.url === CAPTURED_COIN_ENDPOINT,
  );
  probe.path = "evidence/web/objects/not-the-capture";
  assert.throws(
    () => verifySnapshotProvenance(bytes, changedProbes, capturedManifest),
    /provenance does not match/,
  );
  assert.throws(
    () =>
      verifySnapshotProvenance(bytes, probes, { captured_at: "not-a-date" }),
    /timestamp is invalid/,
  );
  assert.equal(
    probes.find(
      (value: { url?: string }) => value.url === CAPTURED_COIN_ENDPOINT,
    ).path,
    CAPTURED_COIN_PATH,
  );
});

test("searches name, symbol and mint case-insensitively", () => {
  const coins = [coin()];
  assert.equal(searchHistoricalCoins(coins, "alpha coin").length, 1);
  assert.equal(searchHistoricalCoins(coins, "aLpHa").length, 1);
  assert.equal(searchHistoricalCoins(coins, "11111111").length, 1);
  assert.equal(searchHistoricalCoins(coins, "missing").length, 0);
});

test("normalizes Unicode, preserves special characters and treats whitespace as empty", () => {
  const coins = [
    coin({ mint: "unicode-mint", name: "Café 猫 & Friends", symbol: "猫币" }),
  ];
  assert.equal(searchHistoricalCoins(coins, "cafe\u0301").length, 1);
  assert.equal(searchHistoricalCoins(coins, "猫").length, 1);
  assert.equal(searchHistoricalCoins(coins, "& friends").length, 1);
  assert.equal(searchHistoricalCoins(coins, " \t\n ").length, 1);
});

test("orders multiple synthetic matches deterministically without mutating input", () => {
  const coins = [
    coin({ mint: "mint-z", name: "Zulu", symbol: "Z" }),
    coin({ mint: "mint-a2", name: "Alpha", symbol: "B" }),
    coin({ mint: "mint-a1", name: "Alpha", symbol: "A" }),
  ];
  const original = coins.map(({ mint }) => mint);
  assert.deepEqual(
    searchHistoricalCoins(coins, "").map(({ mint }) => mint),
    ["mint-a1", "mint-a2", "mint-z"],
  );
  assert.deepEqual(
    coins.map(({ mint }) => mint),
    original,
  );
});
