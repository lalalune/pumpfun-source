import assert from "node:assert/strict";
import { test } from "node:test";
import { readFile, mkdtemp, writeFile, rm } from "node:fs/promises";
import { join, resolve, dirname, basename } from "node:path";
import { tmpdir } from "node:os";
import { spawnSync } from "node:child_process";
import { pathToFileURL, fileURLToPath } from "node:url";

const app = process.env.PUMP_CHAIN_IDENTITY_TEST_APP ?? fileURLToPath(new URL("../", import.meta.url));
const directory = process.env.PUMP_CHAIN_IDENTITY_TEST_DIRECTORY ?? join(app, "reconstruction/chain-identity");
const { createChainIdentity } = await import(pathToFileURL(join(directory, "client.mjs")));

test("complete chain identity source and ordinary Explore/Search consumers remain bound", async () => {
  const { buildChainIdentity } = await import(pathToFileURL(join(directory, "recover.mjs")));
  const generated = await buildChainIdentity(app);
  assert.equal(await readFile(join(directory, "client.mjs"), "utf8"), generated.client);
  assert.deepEqual(JSON.parse(await readFile(join(directory, "contract.json"), "utf8")), generated.contract);
  assert.equal(generated.contract.consumers.length, 5);
  assert.equal(generated.contract.exports.length, 24);
  assert.equal(generated.contract.source.sha256, "719f637fc436bde35bcaa1da5eac3057212d49b84331e27068450218041eb6c0");
});

test("chain names, namespaces, reverse EVM mapping and inherited-property quirks are preserved", () => {
  const m = createChainIdentity();
  assert.deepEqual(m.c, ["solana", "base", "bsc", "ethereum", "monad", "robinhood", "hyperevm", "ink", "arc", "megaeth", "xlayer", "polygon", "arbitrum"]);
  assert.deepEqual(m.l, [...m.c, "ton", "starknet", "near"]);
  assert.deepEqual([m.J, m.W, m.d, m.z, m.h, m.Q], ["ton:-239", "starknet:SN_MAIN", "near:mainnet", "ton", "starknet", "near"]);
  assert.equal(Object.keys(m.H).length, 12);
  for (const [chain, caip] of Object.entries(m.H)) {
    assert.equal(m.U(caip), chain);
    assert.equal(m.U(` ${caip.slice(7)} `), chain);
    assert.equal(m.U(` ${caip} `), chain);
  }
  for (const input of [undefined, null, 1, "", " ", "EIP155:1", "eip155:0001", "unknown", "solana"]) assert.equal(m.U(input), null);
  assert.equal(m.U("toString"), Object.prototype.toString);
  assert.equal(m.U("eip155:constructor"), Object);
  assert.equal(m.U("__proto__"), Object.prototype);
  // The original returned map/arrays are mutable and each module instance is independent.
  m.H.ethereum = "eip155:123";
  assert.equal(m.U("1"), "ethereum");
  assert.equal(m.U("123"), null);
  m.c.push("synthetic-test-chain");
  assert.equal(m.l.includes("synthetic-test-chain"), false);
  assert.equal(createChainIdentity().c.includes("synthetic-test-chain"), false);
});

test("Starknet canonicalization preserves trimming, padding, felt-shaped ceiling and EVM distinction", () => {
  const m = createChainIdentity();
  const canonical = `0x${"0".repeat(62)}ab`;
  assert.equal(m.Y(" 0xAB\n"), canonical);
  assert.equal(m.V(canonical), true);
  assert.equal(m.V("0xAB"), false);
  assert.equal(m.Y(`0x07${"f".repeat(62)}`), `0x07${"f".repeat(62)}`);
  assert.equal(m.Y(`0x08${"0".repeat(62)}`), null);
  assert.equal(m.Y(`0x1${"0".repeat(63)}`), null);
  assert.equal(m.Y(`0x${"f".repeat(65)}`), null);
  for (const input of [null, 1, "", "0X1", "0x", "0xg", "0x1 2"]) assert.equal(m.Y(input), null);
  const evm = `0x${"a".repeat(40)}`;
  assert.notEqual(m.Y(evm), null);
  assert.equal(m.M(evm), false);
  assert.equal(m.M("0xAB"), true);
  assert.equal(m.M(`0x08${"0".repeat(62)}`), false);
  // Exhaust every possible high byte: admission is the captured 0..7 heuristic,
  // not an added signature, checksum, field-prime or on-chain existence check.
  for (let byte = 0; byte < 256; byte++) {
    const value = `0x${byte.toString(16).padStart(2, "0")}${"0".repeat(62)}`;
    assert.equal(m.Y(value) !== null, byte <= 7);
    assert.equal(m.V(value), true);
  }
});

test("NEAR strict input classification and broad account-pattern predicates retain their differences", () => {
  const m = createChainIdentity();
  for (const value of ["alice.near", "alice.testnet", "alice", "a-b_c", "a".repeat(31), "a".repeat(64), "a".repeat(60) + ".near"]) {
    if (value.length <= 64) assert.equal(m.n(value), true);
  }
  for (const value of ["alice.near", "alice", "a-b_c", "f".repeat(64), "a".repeat(59) + ".near"]) assert.equal(m.R(value), true);
  for (const value of ["a", "A.near", " alice.near", "alice.near ", "a..near", "-alice", "alice-", "a__b", "0x1", "a".repeat(32), "a".repeat(65)]) assert.equal(m.R(value), false);
  assert.equal(m.n("0x1"), true);
  assert.equal(m.n("z".repeat(64)), true);
  assert.equal(m.R("z".repeat(64)), false);
  const coercible = { toString: () => "alice.near" };
  assert.equal(m.n(coercible), true);
  assert.equal(m.R(coercible), false);
});

test("TON shape, exact namespaces, coin predicates and code-unit labels stay faithful", () => {
  const m = createChainIdentity();
  const ton = "EQ" + "A_-9".repeat(11) + "AA";
  assert.equal(m.u(ton), true);
  for (const value of [ton.replace(/^EQ/, "UQ"), ton.toLowerCase(), ton + "A", ton.slice(1), null]) assert.equal(m.u(value), false);
  for (const namespace of [m.J, m.W, m.d]) assert.equal(m.C(namespace), true);
  for (const namespace of ["solana", "eip155:1", "ton", "near", "near:mainnet:", "TON:-239", undefined]) assert.equal(m.C(namespace), false);
  for (const [namespace, namespacePredicate, coinPredicate] of [[m.J, m.L, m.e], [m.W, m._, m.X], [m.d, m.B, m.a]]) {
    assert.equal(namespacePredicate(namespace), true);
    assert.equal(coinPredicate({ chain_id: namespace }), true);
    assert.equal(coinPredicate({ chainId: namespace }), false);
    assert.equal(coinPredicate({ chain_id: "solana" }), false);
    assert.throws(() => coinPredicate(null), TypeError);
  }
  assert.equal(m.f("abcdefghijkl"), "abcdefghijkl");
  assert.equal(m.f("abcdefghijklm"), "abcdef…jklm");
  assert.throws(() => m.f(null), TypeError);
});

test("actual pure algorithms compose a bounded ordinary coin identity projection without transport", () => {
  const m = createChainIdentity();
  const coins = [
    { mint: "native-mint", chain_id: "solana" },
    { mint: "EQ" + "A".repeat(46), chain_id: m.J },
    { mint: m.Y("0xAB"), chain_id: m.W },
    { mint: "alice.near", chain_id: m.d },
    { mint: "0x" + "a".repeat(40), chain_id: m.H.ethereum },
  ];
  const inputs = coins.map((coin) => ({ ...coin, typed: m.e(coin) ? "ton" : m.X(coin) ? "starknet" : m.a(coin) ? "near" : "ordinary" }));
  assert.deepEqual(inputs.map((coin) => coin.typed), ["ordinary", "ton", "starknet", "near", "ordinary"]);
  assert.equal(m.u(inputs[1].mint), true);
  assert.equal(m.V(inputs[2].mint), true);
  assert.equal(m.R(inputs[3].mint), true);
  assert.equal(m.U(inputs[4].chain_id), "ethereum");
  assert.deepEqual(inputs.filter((coin) => !m.C(coin.chain_id)).map((coin) => coin.mint), ["native-mint", "0x" + "a".repeat(40)]);
});

test("qualification refuses a semantically changed maintained ceiling without executing captured source", async () => {
  const temporary = await mkdtemp(join(tmpdir(), "chain-identity-adapter-"));
  try {
    const original = await readFile(join(directory, "client.mjs"), "utf8");
    const changed = original.replace('r[1] > "7"', 'r[1] > "8"');
    assert.notEqual(changed, original);
    await writeFile(join(temporary, "client.mjs"), changed);
    await writeFile(join(temporary, "contract.json"), await readFile(join(directory, "contract.json")));
    const mutation = await import(pathToFileURL(join(temporary, "client.mjs")));
    assert.notEqual(mutation.createChainIdentity().Y(`0x08${"0".repeat(62)}`), null);
    const result = spawnSync(process.execPath, [join(directory, "recover.mjs"), "--check"], {
      env: { ...process.env, PUMP_CHAIN_IDENTITY_APP: app, PUMP_CHAIN_IDENTITY_OUTPUT: temporary },
      encoding: "utf8",
    });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /AssertionError/);
  } finally {
    assert.equal(dirname(resolve(temporary)), resolve(tmpdir()));
    assert.ok(basename(temporary).startsWith("chain-identity-adapter-"));
    await rm(temporary, { recursive: true, force: true });
  }
});
