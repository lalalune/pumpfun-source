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
import { createNotificationsController } from "../reconstruction/notifications-controller/client.mjs";
import {
  verify,
  APP_ROOT,
  DIRECTORY,
} from "../scripts/original-notifications-controller.mjs";
const require = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const React = require("react"),
  jsxRuntime = require("react/jsx-runtime"),
  { c: memoCache } = require("react/compiler-runtime"),
  { renderToString } = require("react-dom/server");
function setup({
  permission = "default",
  supported = true,
  available = true,
  configuration = true,
  requestResult = "granted",
  requestError,
} = {}) {
  const calls = {
    permissionReads: 0,
    permissionRequests: 0,
    requestReceiver: false,
    marker: [],
    put: [],
    device: 0,
    registration: 0,
    messaging: 0,
    remove: 0,
    config: 0,
    flags: [],
    viewerScopes: [],
    reports: [],
    refresh: 0,
  };
  let currentPermission = permission;
  const memory = new Map();
  const notification = {
    get permission() {
      calls.permissionReads++;
      return currentPermission;
    },
    requestPermission() {
      calls.permissionRequests++;
      calls.requestReceiver = this === notification;
      if (requestError) return Promise.reject(requestError);
      currentPermission = requestResult;
      return Promise.resolve(requestResult);
    },
  };
  const markerStorage = {
    getItem(key) {
      calls.marker.push(["get", key]);
      return memory.get(key) ?? null;
    },
    setItem(key, value) {
      calls.marker.push(["set", key, value]);
      memory.set(key, value);
    },
    removeItem(key) {
      calls.marker.push(["remove", key]);
      memory.delete(key);
    },
  };
  const api = {
    put: async (path, options) => {
      calls.put.push({ path, options });
    },
  };
  const ports = {
    React,
    jsxRuntime,
    memoCache,
    useAvailability: () => available,
    useFlag: (key) => {
      calls.flags.push(key);
      return true;
    },
    useAuthSnapshot: () => ({
      authReady: true,
      fetchUser: () => {
        calls.refresh++;
      },
    }),
    useViewerKey: (scope) => {
      calls.viewerScopes.push(scope);
      return "synthetic-viewer";
    },
    usePathname: () => "/synthetic",
    useApiClient: () => api,
    useQueryClient: () => ({}),
    useMutation: (options) => ({ mutateAsync: options.mutationFn }),
    getConfigurationIndicator: () => {
      calls.config++;
      return configuration ? {} : null;
    },
    getDeviceHandle: () => {
      calls.device++;
      return "synthetic-device-handle";
    },
    getMessagingHandle: async () => {
      calls.messaging++;
      return {};
    },
    getRegistrationHandle: async () => {
      calls.registration++;
      return "synthetic-registration-handle";
    },
    removeRegistration: async () => {
      calls.remove++;
    },
    onMessage: () => () => {},
    foregroundMessage: () => {},
    invalidateInbox: () => {},
    reportError: (args) => {
      calls.reports.push({ feature: args.feature, operation: args.operation });
    },
    useTranslation: () => ({ t: (key) => "SYNTHETIC:" + key }),
    browserFacade: supported ? { Notification: notification } : {},
    notificationFacade: supported ? notification : undefined,
    markerStorage,
    Button: ({ isDisabled, onClick, children }) =>
      React.createElement(
        "button",
        { disabled: isDisabled, onClick },
        children,
      ),
    Link: ({ href, children }) => React.createElement("a", { href }, children),
  };
  const adapter = createNotificationsController(ports);
  return {
    ports,
    adapter,
    calls,
    memory,
    render({ prompt = false } = {}) {
      let value;
      function Consumer() {
        value = adapter.useNotificationsContext();
        return prompt
          ? React.createElement(adapter.PermissionPrompt, {})
          : React.createElement("output", null, value.permission);
      }
      const html = renderToString(
        React.createElement(
          adapter.Provider,
          {},
          React.createElement(Consumer),
        ),
      );
      return { html, value };
    },
  };
}
test("strict whole-source provider/context/permission/prompt AST proof retains actual used consumers and acquisition limits", async () => {
  const p = await verify();
  assert.equal(p.factories.length, 7);
  assert.equal(p.strictAstProof.nodes.length, 7);
  assert.equal(p.acquisitionPorts.length, 5);
  assert.equal(
    p.caller.settings.source,
    "evidence/web/objects/c9d58b1f7b1c6f01.js",
  );
  assert.match(p.strictAstProof.normalization, /no alpha/);
  assert.equal(p.flag.witness.text.includes("webDirectMessages"), true);
  assert.equal(p.externalHooks.viewer.factory.id, 779106);
  assert.equal(p.externalHooks.mutation.factory.id, 132838);
});
test("no implicit browser/provider/query/config/identity/storage/rendering capability", () => {
  const h = setup();
  for (const name of [
    "memoCache",
    "useAvailability",
    "useFlag",
    "useAuthSnapshot",
    "useViewerKey",
    "usePathname",
    "useApiClient",
    "useQueryClient",
    "useMutation",
    "getConfigurationIndicator",
    "getDeviceHandle",
    "getMessagingHandle",
    "getRegistrationHandle",
    "removeRegistration",
    "onMessage",
    "foregroundMessage",
    "invalidateInbox",
    "reportError",
    "useTranslation",
  ])
    assert.throws(
      () => createNotificationsController({ ...h.ports, [name]: undefined }),
      /Explicit notification capability/,
    );
  assert.throws(
    () =>
      createNotificationsController({ ...h.ports, markerStorage: undefined }),
    /marker storage/,
  );
  assert.throws(
    () =>
      createNotificationsController({ ...h.ports, browserFacade: undefined }),
    /browser/,
  );
  assert.throws(
    () => createNotificationsController({ ...h.ports, React: {} }),
    /React/,
  );
  assert.throws(
    () => createNotificationsController({ ...h.ports, jsxRuntime: {} }),
    /JSX/,
  );
  assert.deepEqual(h.calls.put, []);
  assert.deepEqual(h.calls.marker, []);
  assert.equal(h.calls.device, 0);
  assert.equal(h.calls.registration, 0);
  assert.equal(h.calls.messaging, 0);
  assert.equal(h.calls.permissionReads, 0);
});
test("permission helper preserves native availability, repeated getter decisions and request receiver without touching native APIs", async () => {
  for (const [permission, expected, reads, requests] of [
    ["granted", "granted", 1, 0],
    ["denied", "denied", 2, 0],
    ["default", "granted", 2, 1],
  ]) {
    const h = setup({ permission });
    assert.equal(await h.adapter.requestPermission(), expected);
    assert.equal(h.calls.permissionReads, reads);
    assert.equal(h.calls.permissionRequests, requests);
    if (requests) assert.equal(h.calls.requestReceiver, true);
    assert.equal(h.calls.config, 0);
    assert.equal(h.calls.registration, 0);
    assert.deepEqual(h.calls.put, []);
  }
  const h = setup({ supported: false });
  assert.equal(await h.adapter.requestPermission(), "denied");
  assert.equal(h.calls.permissionReads, 0);
  assert.equal(h.calls.permissionRequests, 0);
});
test("permission Promise rejection is propagated unchanged rather than fabricated as denied or granted", async () => {
  const error = Error("synthetic permission failure"),
    h = setup({ requestError: error });
  await assert.rejects(h.adapter.requestPermission(), (e) => e === error);
  assert.equal(h.calls.permissionRequests, 1);
  assert.equal(h.calls.registration, 0);
});
test("actual React SSR initializes only supplied read-only snapshots and retains feature-disabled defaults with callbacks", () => {
  for (const available of [false, true]) {
    const h = setup({ available, permission: "granted" }),
      { value } = h.render();
    assert.equal(value.permission, available ? "granted" : "unsupported");
    assert.equal(value.isConfigured, available);
    assert.equal(value.token, null);
    assert.equal(value.isRegistering, false);
    assert.equal(typeof value.enablePushNotifications, "function");
    assert.equal(typeof value.registerCurrentToken, "function");
    assert.deepEqual(h.calls.viewerScopes, ["push-token"]);
    assert.deepEqual(h.calls.flags, ["webDirectMessages"]);
    assert.equal(h.calls.permissionReads, 1);
    assert.equal(h.calls.config, 1);
    assert.deepEqual(h.calls.marker, []);
    assert.deepEqual(h.calls.put, []);
    assert.equal(h.calls.registration, 0);
    assert.equal(h.calls.messaging, 0);
  }
});
test("actual source prompt default/denied/unsupported/granted and configuration/availability gates are retained", () => {
  const defaultPrompt = setup().render({ prompt: true }).html;
  assert.match(defaultPrompt, /enable_notifications/);
  assert.match(defaultPrompt, /<button/);
  assert.match(defaultPrompt, /href="\/settings\/notifications"/);
  const denied = setup({ permission: "denied" }).render({ prompt: true }).html;
  assert.match(denied, /blocked_in_browser/);
  assert.doesNotMatch(denied, /<button/);
  for (const options of [
    { supported: false },
    { permission: "granted" },
    { configuration: false },
    { available: false },
  ])
    assert.equal(setup(options).render({ prompt: true }).html, "");
});
test("context reader preserves the actual missing-provider error", () => {
  const h = setup();
  function Consumer() {
    h.adapter.useNotificationsContext();
    return null;
  }
  assert.throws(
    () => renderToString(React.createElement(Consumer)),
    /useNotificationsContext must be used within NotificationsProvider/,
  );
});

test("strict canonical module/contract binding rejects an altered permission branch and reformatted metadata", async (t) => {
  const root = await mkdtemp(
    path.join(os.tmpdir(), "notifications-controller-source-"),
  );
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
    "reconstruction/notifications-foreground/client.mjs",
    "reconstruction/notifications-foreground/contract.json",
    "reconstruction/notifications-inbox/client.mjs",
    "reconstruction/notifications-inbox/contract.json",
    "contracts/settings-client-recovery.json",
    DIRECTORY + "/client.mjs",
    DIRECTORY + "/contract.json",
  ])
    await copy(name);
  const manifest = JSON.parse(
    await readFile(path.join(APP_ROOT, "evidence/web/manifest.json"), "utf8"),
  );
  for (const r of manifest.records)
    if (r.status === 200) await copy(r.path, true);
  const filename = path.join(root, DIRECTORY, "client.mjs"),
    client = await readFile(filename, "utf8");
  assert.ok(client.includes('"granted" === Notification.permission'));
  await writeFile(
    filename,
    client.replace(
      '"granted" === Notification.permission',
      '"denied" === Notification.permission',
    ),
  );
  await assert.rejects(verify(root), /module differs/);
  await writeFile(filename, client);
  const contract = path.join(root, DIRECTORY, "contract.json");
  await writeFile(
    contract,
    JSON.stringify(JSON.parse(await readFile(contract, "utf8"))),
  );
  await assert.rejects(verify(root), /contract bytes differ/);
});
