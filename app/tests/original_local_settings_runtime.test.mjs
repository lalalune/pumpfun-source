import assert from "node:assert/strict";
import { test } from "node:test";
import { createRequire } from "node:module";
import {
  mkdtemp,
  mkdir,
  link,
  copyFile,
  writeFile,
  readFile,
  rm,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { verify } from "../scripts/original-local-settings-runtime.mjs";
import {
  createLocalKeyRuntime,
  createLegacyInitializer,
  createSettingsRuntime,
  createFeedAnimationsDefinition,
  createSettingsSwitch,
} from "../reconstruction/local-settings-runtime/client.mjs";
import {
  syntheticSettingsWindow,
  SyntheticStorageEvent,
} from "./fixtures/local-settings-ports.mjs";

const require = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const React = require("react");
const { renderToString } = require("react-dom/server");
const { c: useMemoCache } = require("react/compiler-runtime");
const jsx = require("react/jsx-runtime");
const key = "home.show-animations";
function harness(initial = {}) {
  const browser = syntheticSettingsWindow(initial);
  const local = createLocalKeyRuntime({
    window: browser.window,
    StorageEvent: SyntheticStorageEvent,
  });
  const definition = createFeedAnimationsDefinition(local);
  const registry = { [definition.id]: definition };
  const runtime = createSettingsRuntime({
    registry,
    initializeLegacy: createLegacyInitializer({ window: browser.window }),
    useMemoCache,
    useSyncExternalStore: React.useSyncExternalStore,
  });
  return { ...browser, local, definition, registry, runtime };
}
const stub = () => {
  throw Error("Unprovided private confirmation control");
};
function switchFor(h, hydrated = true) {
  return createSettingsSwitch({
    ...jsx,
    useMemoCache,
    useState: React.useState,
    useTranslation: () => ({ t: (key) => key }),
    translateKey: (t, key) => t(key),
    Switch: (props) =>
      React.createElement("button", {
        role: "switch",
        "aria-label": props["aria-label"],
        "aria-checked": props.isChecked,
        disabled: props.isDisabled,
      }),
    Button: stub,
    confirmation: { N: stub, K: stub, c: stub, $: "primary", Z: "secondary" },
    useHydrated: () => hydrated,
    settings: h.runtime,
  });
}

test("complete source/dispatcher/registry binding authenticates retained original ASTs", async () => {
  const contract = await verify();
  assert.equal(contract.selectedIndexEntries.length, 7);
  assert.ok(
    contract.retained.some((entry) =>
      entry.label.includes("complete setting pair"),
    ),
  );
  assert.ok(
    contract.retained.some((entry) =>
      entry.label.includes("complete actual Settings switch"),
    ),
  );
  assert.equal(contract.callerWitnesses.length, 3);
});

test("source gate rejects semantically equivalent noncanonical contract bytes and changed client logic", async () => {
  const root = await mkdtemp(
    path.join(os.tmpdir(), "synthetic-local-setting-source-"),
  );
  const app = new URL("..", import.meta.url);
  const contract = await verify();
  try {
    const immutable = [
      "evidence/web/manifest.json",
      "recovered/modules.json",
      ...new Set(contract.provenance.map((entry) => entry.source)),
    ];
    for (const name of immutable) {
      const destination = path.join(root, name);
      await mkdir(path.dirname(destination), { recursive: true });
      try {
        await link(new URL(name, app), destination);
      } catch (error) {
        if (error.code !== "EXDEV") throw error;
        await copyFile(new URL(name, app), destination);
      }
    }
    const directory = path.join(root, "reconstruction/local-settings-runtime");
    await mkdir(directory, { recursive: true });
    const client = new URL(
      "reconstruction/local-settings-runtime/client.mjs",
      app,
    );
    await copyFile(client, path.join(directory, "client.mjs"));
    await writeFile(
      path.join(directory, "contract.json"),
      JSON.stringify(contract),
    );
    await assert.rejects(verify(root), /Expected values to be strictly equal/);
    await writeFile(
      path.join(directory, "contract.json"),
      JSON.stringify(contract, null, 2) + "\n",
    );
    await writeFile(
      path.join(directory, "client.mjs"),
      (await readFile(client, "utf8")) + "\n// unreviewed edit\n",
    );
    await assert.rejects(verify(root), /Expected values to be strictly equal/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("actual safe descriptor is device-local strict-false/default-true JSON", () => {
  const h = harness();
  assert.equal(h.definition.id, "feed.showAnimations");
  assert.equal(h.definition.scope, "device");
  assert.equal(h.definition.default, true);
  for (const raw of [undefined, null, 0, "false", {}, []])
    assert.equal(h.definition.coerce(raw), true);
  assert.equal(h.definition.coerce(false), false);
  h.runtime.writeSetting(h.definition.id, false);
  assert.equal(h.values.get(key), "false");
  assert.equal(h.runtime.readSetting(h.definition.id), false);
});

test("raw Object.is caching returns the same coerced object and distinguishes signed zero", () => {
  const h = harness();
  let raw = NaN,
    coercions = 0;
  h.registry.synthetic = {
    default: "server",
    adapter: { read: () => raw, subscribe: () => () => {} },
    coerce: (value) => ({ value, sequence: ++coercions }),
  };
  const first = h.runtime.readSetting("synthetic");
  assert.equal(h.runtime.readSetting("synthetic"), first);
  assert.equal(coercions, 1);
  raw = 0;
  const zero = h.runtime.readSetting("synthetic");
  raw = -0;
  const negativeZero = h.runtime.readSetting("synthetic");
  assert.notEqual(zero, negativeZero);
  assert.equal(Object.is(negativeZero.value, -0), true);
});

test("cache belongs to descriptor identity, not the registry ID string", () => {
  const h = harness();
  let n = 0;
  const create = () => ({
    default: 0,
    coerce: () => ({ n: ++n }),
    adapter: { read: () => 1, subscribe: () => () => {} },
  });
  const first = create();
  h.registry.synthetic = first;
  const value = h.runtime.readSetting("synthetic");
  h.registry.synthetic = create();
  assert.notEqual(h.runtime.readSetting("synthetic"), value);
  h.registry.synthetic = first;
  assert.equal(h.runtime.readSetting("synthetic"), value);
});

test("original cache updates raw sentinel before coercion throws; later same raw returns prior cached value", () => {
  const h = harness();
  let raw = "good",
    count = 0;
  h.registry.synthetic = {
    default: null,
    adapter: { read: () => raw, subscribe: () => () => {} },
    coerce(value) {
      count++;
      if (value === "bad") throw Error("synthetic coercion");
      return { value };
    },
  };
  const good = h.runtime.readSetting("synthetic");
  raw = "bad";
  assert.throws(() => h.runtime.readSetting("synthetic"), /synthetic coercion/);
  assert.equal(h.runtime.readSetting("synthetic"), good);
  assert.equal(count, 2); // Preserved source quirk, not a new failure policy.
});

test("direct setter coerces then writes without snapshot-reading and returns undefined", () => {
  const h = harness(),
    log = [];
  h.registry.synthetic = {
    default: null,
    coerce: (v) => (log.push(["coerce", v]), v + 1),
    adapter: {
      read: () => {
        throw Error("must not read");
      },
      write: (v) => log.push(["write", v]),
    },
  };
  assert.equal(h.runtime.writeSetting("synthetic", 4), undefined);
  assert.deepEqual(log, [
    ["coerce", 4],
    ["write", 5],
  ]);
});

test("actual React setter reads latest snapshot even for literal updates, then function updates observe prior writes", () => {
  const h = harness({ [key]: "true" });
  let setter;
  function Probe() {
    setter = h.runtime.useSetter(h.definition.id);
    return null;
  }
  renderToString(React.createElement(Probe));
  h.calls.length = 0;
  setter(false);
  assert.equal(h.calls[0][0], "read");
  setter((v) => !v);
  setter((v) => !v);
  assert.equal(h.values.get(key), "false");
  assert.deepEqual(
    h.calls.filter((entry) => entry[0] === "write").map((entry) => entry[2]),
    ["false", "true", "false"],
  );
});

test("throwing functional updater propagates after its latest-value read and writes nothing", () => {
  const h = harness();
  let setter;
  function Probe() {
    setter = h.runtime.useSetter(h.definition.id);
    return null;
  }
  renderToString(React.createElement(Probe));
  h.calls.length = 0;
  assert.throws(
    () =>
      setter(() => {
        throw Error("synthetic updater");
      }),
    /synthetic updater/,
  );
  assert.equal(h.calls.filter((entry) => entry[0] === "read").length, 1);
  assert.equal(h.calls.filter((entry) => entry[0] === "write").length, 0);
});

test("real React SSR uses the uncoerced server default without browser reads", () => {
  const h = harness({ [key]: "false" });
  const Switch = switchFor(h);
  const html = renderToString(
    React.createElement(Switch, {
      definition: h.definition,
      label: "Synthetic animation setting",
    }),
  );
  assert.match(html, /aria-checked="true"/);
  assert.deepEqual(h.calls, []);
});

test("explicit SSR override is returned unchanged, including false, without initializer or read", () => {
  const h = harness();
  let result;
  function Probe() {
    result = h.runtime.useSetting(h.definition.id, { serverValue: false });
    return null;
  }
  renderToString(React.createElement(Probe));
  assert.equal(result, false);
  assert.deepEqual(h.calls, []);
});

test("actual renderer checks strict true and disables only exact first-paint-sensitive while unhydrated", () => {
  const h = harness();
  const Switch = switchFor(h, false);
  const synthetic = {
    ...h.definition,
    id: "synthetic",
    default: "truthy",
    firstPaintSensitive: true,
  };
  h.registry.synthetic = synthetic;
  const html = renderToString(
    React.createElement(Switch, {
      definition: synthetic,
      label: "Synthetic guard only",
    }),
  );
  assert.match(html, /aria-checked="false"/);
  assert.match(html, /disabled=""/);
  const safe = renderToString(
    React.createElement(Switch, {
      definition: h.definition,
      label: "Safe actual descriptor",
    }),
  );
  assert.doesNotMatch(safe, /disabled=/);
});

test("full JSON adapter preserves parsed object identity, malformed/missing reads and raw codec", () => {
  const h = harness({ synthetic: '{"n":1}', invalid: "{" });
  const a = h.local.localKey({ key: "synthetic", codec: "json" });
  const first = a.read();
  assert.equal(a.read(), first);
  assert.equal(
    h.local.localKey({ key: "invalid", codec: "json" }).read(),
    undefined,
  );
  assert.equal(
    h.local.localKey({ key: "missing", codec: "json" }).read(),
    undefined,
  );
  assert.equal(
    h.local.localKey({ key: "synthetic", codec: "raw" }).read(),
    first,
  ); // Cache is keyed by storage key, not codec.
});

test("failed storage write still notifies and updates framework snapshot via module fallback; new lifetime reads old durable value", () => {
  const h = harness({ [key]: "true" });
  let notifications = 0;
  h.definition.adapter.subscribe(() => notifications++);
  h.failures.write = true;
  h.runtime.writeSetting(h.definition.id, false);
  assert.equal(h.runtime.readSetting(h.definition.id), false);
  assert.equal(h.values.get(key), "true");
  assert.equal(notifications, 1);
  const next = createLocalKeyRuntime({
    window: h.window,
    StorageEvent: SyntheticStorageEvent,
  });
  assert.equal(next.localKey({ key, codec: "json" }).read(), true);
});

test("storage events do not clear fallback, subscriptions deduplicate and cleanup removes selected callback", () => {
  const h = harness();
  let count = 0;
  const listener = () => count++;
  const one = h.definition.adapter.subscribe(listener),
    two = h.definition.adapter.subscribe(listener);
  h.failures.write = true;
  h.runtime.writeSetting(h.definition.id, false);
  assert.equal(count, 1);
  h.values.set(key, "true");
  h.window.dispatchEvent(new SyntheticStorageEvent("storage", { key }));
  assert.equal(h.runtime.readSetting(h.definition.id), false);
  assert.equal(count, 2);
  one();
  h.window.dispatchEvent(new SyntheticStorageEvent("storage", { key }));
  assert.equal(count, 2);
  two();
  assert.deepEqual(
    h.calls.filter((entry) => entry[0] === "listen").map((entry) => entry[1]),
    ["storage", "local-storage"],
  );
});

test("failed removal clears fallback/cache but cannot fabricate durable deletion", () => {
  const h = harness({ [key]: "true" });
  h.failures.write = true;
  h.runtime.writeSetting(h.definition.id, false);
  h.failures.remove = true;
  h.definition.adapter.remove();
  assert.equal(h.runtime.readSetting(h.definition.id), true);
});

test("legacy adoption merges arrays/objects in order, writes coerced result before removals and honors strict-false retention", () => {
  const h = harness({
    "synthetic-old-a": '{"list":[2],"nested":{"b":3}}',
    "synthetic-old-b": '{"list":[4,5]}',
  });
  let persisted;
  const log = [];
  const definition = {
    default: { list: [0, 1, 9], nested: { a: 1 } },
    coerce: (v) => (log.push("coerce"), v),
    adapter: {
      read: () => persisted,
      write: (v) => {
        log.push("write");
        h.calls.push(["adopt-write"]);
        persisted = v;
      },
    },
    legacy: [
      { key: "synthetic-old-a", codec: "json", map: (v) => v },
      {
        key: "synthetic-old-b",
        codec: "json",
        map: (v) => v,
        removeAfterAdopt: false,
      },
    ],
  };
  const initialize = createLegacyInitializer({ window: h.window });
  initialize(definition);
  assert.deepEqual(persisted, { list: [4, 5, 9], nested: { a: 1, b: 3 } });
  assert.deepEqual(log, ["coerce", "write"]);
  assert.ok(
    h.calls.findIndex((entry) => entry[0] === "adopt-write") <
      h.calls.findIndex((entry) => entry[0] === "remove"),
  );
  assert.equal(h.values.has("synthetic-old-a"), false);
  assert.equal(h.values.has("synthetic-old-b"), true);
  initialize(definition);
  assert.equal(log.length, 2);
});

test("legacy initializer marks before failing write and does not silently retry the same definition", () => {
  const h = harness({ "synthetic-old": "raw" });
  let writes = 0;
  const definition = {
    default: null,
    coerce: (v) => v,
    adapter: {
      read: () => undefined,
      write() {
        writes++;
        throw Error("synthetic migration write");
      },
    },
    legacy: [{ key: "synthetic-old", codec: "raw", map: (v) => v }],
  };
  const initialize = createLegacyInitializer({ window: h.window });
  assert.throws(() => initialize(definition), /synthetic migration write/);
  initialize(definition);
  assert.equal(writes, 1);
  assert.equal(h.values.has("synthetic-old"), true);
});

test("legacy existing value prevents adoption, invalid JSON/throwing mapper are ignored, and removal errors are swallowed", () => {
  const h = harness({
    "synthetic-bad": "{",
    "synthetic-map": "1",
    "synthetic-good": "2",
  });
  let persisted = false,
    writes = 0;
  const definition = {
    default: 0,
    coerce: (v) => v,
    adapter: {
      read: () => persisted,
      write: (v) => {
        writes++;
        persisted = v;
      },
    },
    legacy: [
      { key: "synthetic-bad", codec: "json", map: (v) => v },
      {
        key: "synthetic-map",
        codec: "json",
        map() {
          throw Error("synthetic mapper");
        },
      },
      { key: "synthetic-good", codec: "json", map: (v) => v },
    ],
  };
  createLegacyInitializer({ window: h.window })(definition);
  assert.equal(writes, 0);
  persisted = undefined;
  h.failures.remove = true;
  createLegacyInitializer({ window: h.window })(definition);
  assert.equal(writes, 1);
  assert.equal(persisted, 2);
  assert.equal(h.values.get("synthetic-good"), "2");
});
