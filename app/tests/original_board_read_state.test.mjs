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
import { createBoardCoinHook } from "../reconstruction/board-read-state/client.mjs";
import { createSearchCache } from "../reconstruction/search-session/session.mjs";
import {
  verify,
  APP_ROOT,
  DIRECTORY,
} from "../scripts/original-board-read-state.mjs";
const require = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const React = require("react"),
  { renderToString } = require("react-dom/server");
const input = {
  sort: "featured",
  offset: 0,
  limit: 2,
  includeNsfw: false,
  order: "DESC",
};
function setup({
  variant = "social-terminal",
  seed = () => {},
  initialCoins,
  options = {},
} = {}) {
  const calls = { seed: [], poll: [], fetch: [], identity: [], debounce: [] };
  const nowMs = () => 1000;
  const ports = {
    React,
    cache: createSearchCache({ now: nowMs }),
    baseUrl: "http://127.0.0.1:1",
    fetchResponse: (...args) => {
      calls.fetch.push(args);
      throw Error("SSR must not fetch");
    },
    parseBoard: () => {
      throw Error("SSR must not parse a response");
    },
    seedBoardCoins: (...args) => {
      calls.seed.push(args);
      return seed(...args);
    },
    nowMs,
    AbortController,
    useViewerSnapshot: () => ({
      address: undefined,
      userId: undefined,
      authReady: false,
    }),
    useSessionSnapshot: () => ({ sessionData: undefined }),
    usePrimarySessionIdSnapshot: () => undefined,
    useVariant: () => variant,
    useExposure: () => ({}),
    useIpfsPrefix: () => ({ ipfsPrefix: "https://synthetic.invalid/ipfs/" }),
    requestIdentity: (...args) => {
      calls.identity.push(args);
      return { deviceId: "synthetic-device" };
    },
    debounce: (callback, ms) => {
      calls.debounce.push(ms);
      const result = (...args) => callback(...args);
      result.cancel = () => {};
      return result;
    },
    useLivePollInterval: (ms, enabled) => {
      calls.poll.push([ms, enabled]);
      return false;
    },
    timers: {
      setInterval: () => assert.fail("no board interval"),
      clearInterval: () => {},
    },
    logger: { error: () => assert.fail("no SSR private search") },
  };
  const hook = createBoardCoinHook(ports);
  let result;
  const props = {
    ...input,
    ...options,
    ...(initialCoins === undefined ? {} : { initialCoins }),
  };
  function App() {
    result = hook(props);
    return React.createElement(
      "output",
      null,
      JSON.stringify({ loading: result.loading, error: result.error }),
    );
  }
  return {
    ports,
    calls,
    props,
    render: () => {
      renderToString(React.createElement(App));
      return result;
    },
  };
}
test("source closes all four full owning frames, actual caller and reused accepted operations", async () => {
  const c = await verify();
  assert.equal(c.sourceProofs.length, 4);
  assert.equal(new Set(c.sourceProofs.map((p) => p.normalizedSha256)).size, 1);
  assert.equal(
    c.frameNormalizedSha256,
    "e8ca2155704036850744b4091f7c03486ed6a656d663f6365aa6c0ab684642b8",
  );
  assert.equal(c.providerConstants.length, 4);
  assert.equal(c.pauseSources.length, 2);
  assert.equal(c.dependencies.length, 3);
  assert.match(c.responsePorts.dependency, /OPEN PR1761/);
  assert.match(c.caller.qualification, /not reconstructed/);
});
test("real React SSR preserves undefined, empty and populated seed state for both admitted sorts and variants", () => {
  for (const variant of ["social-terminal", "other"])
    for (const sort of ["featured", "trending"])
      for (const initialCoins of [
        undefined,
        [],
        [{ mint: "synthetic-a", created_timestamp: 10 }],
      ]) {
        const h = setup({ variant, initialCoins, options: { sort } }),
          result = h.render();
        assert.equal(result.loading, !initialCoins);
        assert.equal(result.error, false);
        assert.equal(
          result.rowsRequestKey,
          initialCoins ? result.requestKey : null,
        );
        assert.equal(result.hasMorePages, false);
        if (initialCoins) assert.strictEqual(result.coins, initialCoins);
        else assert.deepEqual(result.coins, []);
        if (initialCoins && sort === "trending")
          assert.strictEqual(result.servedCoins, initialCoins);
        else assert.deepEqual(result.servedCoins, []);
        assert.equal(
          h.calls.seed.length,
          initialCoins && variant === "social-terminal" ? 1 : 0,
        );
        if (h.calls.seed.length) {
          assert.equal(h.calls.seed[0].length, 1);
          assert.strictEqual(h.calls.seed[0][0], initialCoins);
        }
        assert.deepEqual(h.calls.poll, [[60000, false]]);
        assert.deepEqual(h.calls.debounce, [1000]);
        assert.equal(h.calls.fetch.length, 0);
        assert.equal(h.calls.identity.length, 0);
      }
});
test("the actual 11-slot render key trims the search slot and preserves its fixed null filter slot", () => {
  const h = setup({
    options: {
      sort: "trending",
      offset: 3,
      limit: 4,
      order: "ASC",
      includeNsfw: true,
      searchTerm: "  synthetic  ",
      chain: "solana",
      creator: "synthetic-creator",
      filterParams: { notRead: true },
    },
  });
  assert.deepEqual(JSON.parse(h.render().requestKey), [
    "trending",
    "ASC",
    3,
    4,
    true,
    false,
    "synthetic",
    "solana",
    null,
    "synthetic-creator",
    "1h",
  ]);
});
test("seed failure propagates only through the actual social-terminal truthy-initial gate", () => {
  const error = Error("synthetic seed failure");
  assert.throws(
    () =>
      setup({
        initialCoins: [],
        seed: () => {
          throw error;
        },
      }).render(),
    (e) => e === error,
  );
  assert.doesNotThrow(() =>
    setup({
      variant: "other",
      initialCoins: [],
      seed: () => {
        throw error;
      },
    }).render(),
  );
});
test("board-used return view and local admission do not expose private search/other-sort operations", () => {
  const h = setup(),
    result = h.render();
  assert.deepEqual(Object.keys(result), [
    "coins",
    "loading",
    "error",
    "hasMorePages",
    "fetchCoins",
    "refetch",
    "requestKey",
    "rowsRequestKey",
    "servedCoins",
    "setCoins",
  ]);
  assert.equal(typeof result.fetchCoins, "function");
  assert.equal(typeof result.refetch, "function");
  assert.equal(typeof result.setCoins, "function");
  assert.throws(
    () => setup({ options: { sort: "live" } }).render(),
    /Only non-search/,
  );
  assert.throws(
    () => setup({ options: { isSearchMode: true } }).render(),
    /Only non-search/,
  );
  assert.equal(h.calls.fetch.length, 0);
});
test("no implicit destination, response decoder, identity/provider, React or shared cache capabilities", () => {
  const { ports } = setup();
  for (const name of [
    "fetchResponse",
    "parseBoard",
    "seedBoardCoins",
    "nowMs",
    "requestIdentity",
    "useViewerSnapshot",
    "useSessionSnapshot",
    "usePrimarySessionIdSnapshot",
    "useVariant",
    "useExposure",
    "useIpfsPrefix",
    "debounce",
    "useLivePollInterval",
  ])
    assert.throws(
      () => createBoardCoinHook({ ...ports, [name]: undefined }),
      /Explicit board capability/,
    );
  assert.throws(
    () => createBoardCoinHook({ ...ports, cache: undefined }),
    /cache/,
  );
  assert.throws(
    () => createBoardCoinHook({ ...ports, baseUrl: undefined }),
    /destination/,
  );
  assert.throws(() => createBoardCoinHook({ ...ports, React: {} }), /React/);
});
test("source gate rejects a wrong real state-port bridge and noncanonical contract bytes", async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), "board-frame-source-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const manifest = JSON.parse(
    await readFile(path.join(APP_ROOT, "evidence/web/manifest.json")),
  );
  async function copy(name, immutable = false) {
    const to = path.join(root, name);
    await mkdir(path.dirname(to), { recursive: true });
    if (immutable) {
      try {
        await link(path.join(APP_ROOT, name), to);
        return;
      } catch (e) {
        if (e.code !== "EXDEV") throw e;
      }
    }
    await copyFile(path.join(APP_ROOT, name), to);
  }
  for (const name of [
    "evidence/web/manifest.json",
    "recovered/modules.json",
    "reconstruction/search-session/session.mjs",
    "reconstruction/search-planner/planner.mjs",
    "reconstruction/market-boards/request.mjs",
    "contracts/market-board-bindings.json",
  ])
    await copy(name);
  for (const record of manifest.records)
    if (record.status === 200) await copy(record.path, true);
  const clientPath = DIRECTORY + "/client.mjs",
    contractPath = DIRECTORY + "/contract.json";
  await copy(clientPath);
  await copy(contractPath);
  const client = await readFile(path.join(root, clientPath), "utf8");
  assert.ok(client.includes("setCoins: B"));
  await writeFile(
    path.join(root, clientPath),
    client.replace("setCoins: B", "setCoins: V"),
  );
  await assert.rejects(verify(root), /module differs/);
  await writeFile(path.join(root, clientPath), client);
  const contract = JSON.parse(
    await readFile(path.join(root, contractPath), "utf8"),
  );
  await writeFile(path.join(root, contractPath), JSON.stringify(contract));
  await assert.rejects(verify(root), /contract bytes differ/);
});
