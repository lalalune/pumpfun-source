import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import {
  recover,
  verify,
  verifyBrowserReceipt,
  verifyAppBrowserReceipt,
  outputPath,
  appBrowserDirectory,
} from "../scripts/original-privacy-external-links.mjs";
import {
  preferenceKey,
  privacyPreferenceRuntime,
  outboundConfirmation,
  normalizeOutboundUrl,
  isTrustedOutboundUrl,
} from "../reconstruction/privacy-external-links/client.mjs";
const root = fileURLToPath(new URL("..", import.meta.url));
const contract = await verify(root);
const hash = (v) => createHash("sha256").update(v).digest("hex");
class StorageSignal extends Event {
  constructor(type, { key } = {}) {
    super(type);
    this.key = key;
  }
}
function harness({
  values = new Map(),
  failRead = false,
  failWrite = false,
  failRemove = false,
} = {}) {
  const events = new EventTarget(),
    storage = {
      getItem(key) {
        if (failRead) throw Error("synthetic read denied");
        return values.get(key) ?? null;
      },
      setItem(key, value) {
        if (failWrite) throw Error("synthetic write denied");
        values.set(key, String(value));
      },
      removeItem(key) {
        if (failRemove) throw Error("synthetic remove denied");
        values.delete(key);
      },
    };
  const runtime = privacyPreferenceRuntime({
    getStorage: () => storage,
    events,
    createStorageEvent: (type, init) => new StorageSignal(type, init),
  });
  return { events, values, runtime, preference: runtime.preference() };
}

test("source binds selected device descriptor, all four hooks/three actual consumers and import variants", () => {
  assert.equal(contract.inventoryVariants, 5947);
  assert.equal(contract.sources.length, 13);
  assert.equal(contract.preference.key, preferenceKey);
  assert.equal(contract.preference.scope, "device");
  assert.equal(contract.preference.default, true);
  assert.equal(contract.preference.legacyAdoption, false);
  assert.equal(contract.outbound.hooks.length, 4);
  assert.equal(contract.consumer.variants.length, 3);
  assert.deepEqual(contract.outbound.trustedHosts, [
    "pump.fun",
    "terminal.pump.fun",
    "trade.padre.gg",
  ]);
  assert.equal(contract.compatibilityQualified, false);
  assert.equal(
    contract.outbound.persistenceAcknowledgementOrNavigationSuccessClaimed,
    false,
  );
  for (const m of contract.sources)
    for (const i of m.imports) assert.ok(i.variants.length > 0);
});

test("only decoded strict false disables; absent, malformed and other stored values retain default true", () => {
  for (const [raw, value] of [
    [null, true],
    ["false", false],
    ['"false"', true],
    ["true", true],
    ["null", true],
    ["0", true],
    ["[]", true],
    ["broken", true],
  ]) {
    const h = harness();
    if (raw !== null) h.values.set(preferenceKey, raw);
    assert.equal(h.preference.read(), value);
  }
  const h = harness({ failRead: true });
  assert.equal(h.preference.read(), true);
});

test("coerced writes persist/recreate, share one runtime and leave unrelated keys alone", () => {
  const h = harness();
  h.values.set("unrelated", "keep");
  h.preference.write(false);
  assert.equal(h.values.get(preferenceKey), "false");
  assert.equal(h.runtime.preference().read(), false);
  assert.equal(harness({ values: h.values }).preference.read(), false);
  h.preference.write(null);
  assert.equal(h.values.get(preferenceKey), "true");
  h.preference.remove();
  assert.equal(h.preference.read(), true);
  assert.equal(h.values.get("unrelated"), "keep");
});

test("failed writes use shared runtime fallback, not durable acknowledgement; external events do not clear it", () => {
  const h = harness({ failWrite: true });
  assert.equal(h.preference.write(false), undefined);
  assert.equal(h.preference.read(), false);
  assert.equal(h.runtime.preference().read(), false);
  assert.equal(h.values.has(preferenceKey), false);
  h.values.set(preferenceKey, "true");
  h.events.dispatchEvent(new StorageSignal("storage", { key: preferenceKey }));
  assert.equal(h.preference.read(), false);
  assert.equal(harness({ values: h.values }).preference.read(), true); // New module lifetime loses fallback.
  h.preference.remove();
  assert.equal(h.preference.read(), true);
});

test("failed remove clears fallback but cannot fabricate deletion of persisted old data", () => {
  const values = new Map([[preferenceKey, "false"]]),
    h = harness({ values, failWrite: true, failRemove: true });
  h.preference.write(true);
  assert.equal(h.preference.read(), true);
  h.preference.remove();
  assert.equal(h.preference.read(), false);
  assert.equal(values.get(preferenceKey), "false");
});

test("storage subscriptions use selected/global-clear keys, deduplicate callbacks and preserve cleanup semantics", () => {
  const h = harness();
  let calls = 0;
  const fn = () => calls++;
  const a = h.preference.subscribe(fn),
    b = h.runtime.preference().subscribe(fn);
  h.preference.write(false);
  assert.equal(calls, 1);
  h.events.dispatchEvent(new StorageSignal("storage", { key: "unrelated" }));
  assert.equal(calls, 1);
  h.events.dispatchEvent(new StorageSignal("storage", { key: null }));
  assert.equal(calls, 2);
  h.events.dispatchEvent(new StorageSignal("local-storage"));
  assert.equal(calls, 3);
  a();
  h.preference.write(true);
  assert.equal(calls, 3);
  b();
});

test("URL normalization preserves captured HTTPS-only and exact trusted-host decisions", () => {
  assert.equal(
    normalizeOutboundUrl(" example.invalid/path "),
    "https://example.invalid/path",
  );
  assert.equal(
    normalizeOutboundUrl("//example.invalid/path"),
    "https://example.invalid/path",
  );
  assert.equal(
    normalizeOutboundUrl("HTTPS://EXAMPLE.INVALID/path"),
    "https://example.invalid/path",
  );
  for (const value of [
    null,
    undefined,
    "",
    " ",
    "http://example.invalid",
    "HTTP://example.invalid",
    "https://[",
    "/",
  ])
    assert.equal(normalizeOutboundUrl(value), null);
  assert.throws(() => normalizeOutboundUrl(1), TypeError);
  for (const host of [
    "pump.fun",
    "www.pump.fun",
    "terminal.pump.fun",
    "trade.padre.gg",
  ])
    assert.equal(isTrustedOutboundUrl(host), true);
  for (const host of [
    "pump.fun.",
    "www.www.pump.fun",
    "sub.pump.fun",
    "pump.fun.example.invalid",
    "http://pump.fun",
  ])
    assert.equal(isTrustedOutboundUrl(host), false);
});

function controller({ hub = true, openWindow, ...options } = {}) {
  const h = harness(options),
    opened = [];
  const model = outboundConfirmation({
    preference: h.preference,
    settingsHubEnabled: hub,
    openWindow:
      openWindow ??
      ((...args) => {
        opened.push(args);
        return null;
      }),
  });
  return { ...h, model, opened };
}

test("default confirmation, cancel/checkbox reset and remember-on-confirm preserve actual state order", () => {
  const h = controller();
  h.model.requestNavigation("other.invalid/a");
  assert.deepEqual(h.model.getSnapshot(), {
    open: true,
    pendingUrl: "https://other.invalid/a",
    dontAskAgain: false,
    settingsHubEnabled: true,
  });
  h.model.setDontAskAgain(true);
  h.model.cancel();
  assert.equal(h.model.getSnapshot().pendingUrl, null);
  assert.equal(h.model.getSnapshot().dontAskAgain, true);
  assert.equal(h.preference.read(), true);
  h.model.requestNavigation("other.invalid/b");
  assert.equal(h.model.getSnapshot().dontAskAgain, false);
  h.model.setDontAskAgain(true);
  h.model.confirm();
  assert.equal(h.values.get(preferenceKey), "false");
  assert.deepEqual(h.opened, [
    ["https://other.invalid/b", "_blank", "noopener,noreferrer"],
  ]);
  assert.equal(h.model.getSnapshot().open, false);
  assert.equal(h.model.getSnapshot().pendingUrl, null);
  h.model.requestNavigation("other.invalid/c");
  assert.equal(h.opened.length, 2);
  assert.equal(h.model.getSnapshot().open, false);
  h.model.dispose();
});

test("settings-hub gate forces confirmation and prevents remember write even with persisted false", () => {
  const h = controller({
    hub: false,
    values: new Map([[preferenceKey, "false"]]),
  });
  h.model.requestNavigation("other.invalid");
  assert.equal(h.model.getSnapshot().open, true);
  h.model.setDontAskAgain(true);
  h.model.confirm();
  assert.equal(h.values.get(preferenceKey), "false");
  h.model.requestNavigation("other.invalid/again");
  assert.equal(h.model.getSnapshot().open, true);
  h.model.setSettingsHubEnabled(true);
  h.model.cancel();
  h.model.requestNavigation("other.invalid/third");
  assert.equal(h.model.getSnapshot().open, false);
  assert.equal(h.opened.length, 2);
  h.model.dispose();
});

test("trusted/direct requests and invalid requests do not silently clear an already open dialog", () => {
  const h = controller();
  h.model.requestNavigation("first.invalid");
  h.model.setDontAskAgain(true);
  h.model.requestNavigation("http://invalid.example");
  assert.equal(h.model.getSnapshot().pendingUrl, "https://first.invalid/");
  h.model.requestNavigation("pump.fun");
  assert.equal(h.opened.length, 1);
  assert.equal(h.model.getSnapshot().pendingUrl, "https://first.invalid/");
  h.preference.write(false);
  h.model.requestNavigation("second.invalid");
  assert.equal(h.opened.length, 2);
  assert.equal(h.model.getSnapshot().open, true);
  h.model.dispose();
});

test("source write happens before open; popup return is not a success acknowledgement", () => {
  const order = [],
    h = controller({
      openWindow: (...args) => {
        order.push(["open", ...args]);
        return null;
      },
    });
  h.preference.subscribe(() => order.push(["preference", h.preference.read()]));
  h.model.requestNavigation("other.invalid");
  h.model.setDontAskAgain(true);
  h.model.confirm();
  assert.deepEqual(order, [
    ["preference", false],
    ["open", "https://other.invalid/", "_blank", "noopener,noreferrer"],
  ]);
  assert.equal(h.model.getSnapshot().open, false);
  h.model.dispose();
});

test("failed storage remains in-memory only; failed open preserves pending dialog after the attempted preference write", () => {
  const h = controller({
    failWrite: true,
    openWindow: () => {
      throw Error("synthetic open failure");
    },
  });
  h.model.requestNavigation("other.invalid");
  h.model.setDontAskAgain(true);
  assert.throws(() => h.model.confirm(), /open failure/);
  assert.equal(h.preference.read(), false);
  assert.equal(h.values.has(preferenceKey), false);
  assert.equal(h.model.getSnapshot().open, true);
  assert.equal(h.model.getSnapshot().pendingUrl, "https://other.invalid/");
  h.model.dispose();
});

test("link click always prevents/stops before caller and navigation; caller exception aborts later effect", () => {
  const h = controller(),
    sequence = [],
    event = {
      preventDefault: () => sequence.push("prevent"),
      stopPropagation: () => sequence.push("stop"),
    };
  h.model.handleLinkClick(event, {
    href: "other.invalid",
    onClick: () => sequence.push("callback"),
  });
  assert.deepEqual(sequence, ["prevent", "stop", "callback"]);
  assert.equal(h.model.getSnapshot().open, true);
  h.model.cancel();
  sequence.length = 0;
  assert.throws(
    () =>
      h.model.handleLinkClick(event, {
        href: "other.invalid",
        onClick: () => {
          throw Error("synthetic caller failure");
        },
      }),
    /caller failure/,
  );
  assert.deepEqual(sequence, ["prevent", "stop"]);
  assert.equal(h.model.getSnapshot().open, false);
  h.model.dispose();
});

test("external preference events update the settled controller snapshot and disposal unsubscribes", () => {
  const h = controller();
  h.values.set(preferenceKey, "false");
  h.events.dispatchEvent(new StorageSignal("storage", { key: preferenceKey }));
  h.model.requestNavigation("other.invalid");
  assert.equal(h.opened.length, 1);
  let called = 0;
  h.model.subscribe(() => called++);
  h.model.dispose();
  h.preference.write(true);
  assert.equal(called, 0);
});

async function temporary() {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "pump-privacy-source-"));
  const files = new Set([
    "recovered/modules.json",
    "evidence/web/manifest.json",
    outputPath,
    ...contract.sources.map((s) => s.source.source),
  ]);
  for (const f of files) {
    await fs.mkdir(path.dirname(path.join(dir, f)), { recursive: true });
    await fs.copyFile(path.join(root, f), path.join(dir, f));
  }
  return { dir, close: () => fs.rm(dir, { recursive: true, force: true }) };
}
async function reseal(dir, id, change) {
  const p = path.join(dir, "recovered/modules.json"),
    index = JSON.parse(await fs.readFile(p));
  const entry = index.modules.find((m) => m.ids.includes(id)),
    origin = entry.origins[0],
    file = path.join(dir, origin.source),
    source = await fs.readFile(file, "utf8");
  const old = source.slice(origin.start, origin.end),
    next = change(old);
  assert.notEqual(next, old);
  assert.equal(next.length, old.length);
  await fs.writeFile(
    file,
    source.slice(0, origin.start) + next + source.slice(origin.end),
  );
  entry.sha256 = hash(next);
  await fs.writeFile(p, JSON.stringify(index));
  const mp = path.join(dir, "evidence/web/manifest.json"),
    manifest = JSON.parse(await fs.readFile(mp));
  for (const r of manifest.records)
    if (r.path === origin.source) r.sha256 = hash(await fs.readFile(file));
  await fs.writeFile(mp, JSON.stringify(manifest));
}
test("resealed storage/fallback/gate/consumer changes cannot keep stale source claims", async () => {
  for (const [id, old, next] of [
    [654506, '"local-storage"', '"local-storagx"'],
    [225641, '"pump.fun"', '"pumx.fun"'],
    [402732, "WEB_SETTINGS_HUB", "WEB_SETTINGS_HUX"],
    [634557, "preventDefault", "preventDefauls"],
  ]) {
    const t = await temporary();
    try {
      await reseal(t.dir, id, (s) => s.replace(old, next));
      await assert.rejects(recover(t.dir), /Privacy recovery:/);
    } finally {
      await t.close();
    }
  }
});
test("raw corruption, missing variant and invented persistence/owner metadata fail closed", async () => {
  for (const mutation of ["raw", "variant", "contract"]) {
    const t = await temporary();
    try {
      if (mutation === "raw")
        await fs.appendFile(
          path.join(t.dir, contract.sources[0].source.source),
          " ",
        );
      if (mutation === "variant") {
        const p = path.join(t.dir, "recovered/modules.json"),
          value = JSON.parse(await fs.readFile(p));
        value.modules = value.modules.filter(
          (m) => m.sha256 !== contract.outbound.hooks[0].source.sha256,
        );
        await fs.writeFile(p, JSON.stringify(value));
      }
      if (mutation === "contract") {
        const p = path.join(t.dir, outputPath),
          value = JSON.parse(await fs.readFile(p));
        value.preference.scope = "account";
        value.outbound.persistenceAcknowledgementOrNavigationSuccessClaimed = true;
        await fs.writeFile(p, JSON.stringify(value));
      }
      await assert.rejects(verify(t.dir));
    } finally {
      await t.close();
    }
  }
});
test("browser receipt binds actual executed client/test/contract bytes and cannot silently gain navigation claims", async () => {
  const receipt = await verifyBrowserReceipt(root);
  assert.equal(receipt.browserProcessRestarts, 1);
  assert.equal(receipt.actualDestinationOpened, false);
  for (const mutation of ["client", "claim"]) {
    const dir = await fs.mkdtemp(
      path.join(os.tmpdir(), "pump-privacy-browser-receipt-"),
    );
    try {
      for (const file of [
        outputPath,
        "reconstruction/privacy-external-links/client.mjs",
        "reconstruction/privacy-external-links/browser-verification.json",
        "tests/original_privacy_external_links.browser.mjs",
      ]) {
        await fs.mkdir(path.dirname(path.join(dir, file)), { recursive: true });
        await fs.copyFile(path.join(root, file), path.join(dir, file));
      }
      if (mutation === "client")
        await fs.appendFile(
          path.join(dir, "reconstruction/privacy-external-links/client.mjs"),
          "\n// changed after execution\n",
        );
      else {
        const p = path.join(
            dir,
            "reconstruction/privacy-external-links/browser-verification.json",
          ),
          value = JSON.parse(await fs.readFile(p));
        value.actualDestinationOpened = true;
        await fs.writeFile(p, JSON.stringify(value));
      }
      await assert.rejects(
        verifyBrowserReceipt(dir),
        /stale browser receipt|scope\/result/,
      );
    } finally {
      await fs.rm(dir, { recursive: true, force: true });
    }
  }
});
test("current footer/Settings receipt binds consumers/screenshots and rejects edits or upstream claims", async () => {
  const receipt = await verifyAppBrowserReceipt(root);
  assert.equal(receipt.outboundConsumersExercised, true);
  for (const mutation of [
    "renderer",
    "consumer",
    "screenshot",
    "claim",
    "unmounted",
  ]) {
    const dir = await fs.mkdtemp(
      path.join(os.tmpdir(), "pump-privacy-app-receipt-"),
    );
    try {
      const folder = appBrowserDirectory;
      for (const file of [
        ...Object.keys(receipt.sourceInputs),
        ...Object.keys(receipt.screenshots).map((name) => `${folder}/${name}`),
        `${folder}/verification.json`,
      ]) {
        await fs.mkdir(path.dirname(path.join(dir, file)), { recursive: true });
        await fs.copyFile(path.join(root, file), path.join(dir, file));
      }
      await verifyAppBrowserReceipt(dir);
      if (mutation === "consumer") {
        const file = path.join(
          dir,
          "packages/frontend/src/components/shell/SiteFooter.tsx",
        );
        const text = await fs.readFile(file, "utf8");
        const changed = text.replace(
          /<FooterOutboundLinks>([\s\S]*?)<\/FooterOutboundLinks>/,
          "$1",
        );
        assert.notEqual(changed, text, "actual footer mount was mutated");
        await fs.writeFile(file, changed);
      } else if (mutation === "renderer")
        await fs.appendFile(
          path.join(
            dir,
            "packages/frontend/src/components/settings/privacy-setting-control.tsx",
          ),
          "\n// changed after browser run\n",
        );
      else if (mutation === "screenshot")
        await fs.appendFile(
          path.join(dir, `${folder}/footer-desktop.png`),
          "changed",
        );
      else if (mutation === "unmounted") {
        const file = path.join(
          dir,
          "packages/frontend/src/components/settings/settings-control.tsx",
        );
        const text = await fs.readFile(file, "utf8");
        await fs.writeFile(
          file,
          text.replace(
            "<PrivacySettingControl label={setting.label} />",
            "<span className={styles.unavailable}>Unavailable</span>",
          ),
        );
      } else {
        const file = path.join(dir, `${folder}/verification.json`);
        const value = JSON.parse(await fs.readFile(file));
        value.serverCompatibilityClaimed = true;
        await fs.writeFile(file, JSON.stringify(value));
      }
      await assert.rejects(
        verifyAppBrowserReceipt(dir),
        /stale app|app receipt result\/scope/,
      );
    } finally {
      await fs.rm(dir, { recursive: true, force: true });
    }
  }
});
