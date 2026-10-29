import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { once } from "node:events";
import { mkdtemp, readFile, mkdir, writeFile, rm } from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
const app = fileURLToPath(new URL("..", import.meta.url)),
  frontend = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  backend = createRequire(
    new URL("../packages/backend/package.json", import.meta.url),
  );
const { chromium } = frontend("@playwright/test"),
  { build, version: esbuildVersion } = createRequire(backend.resolve("tsx"))(
    "esbuild",
  ),
  hash = (b) => createHash("sha256").update(b).digest("hex");
test(
  "actual React permission/controller with inert facades: gates, overlap/ref commits, callbacks, late cleanup and failures",
  { timeout: 45000 },
  async () => {
    const temp = await mkdtemp(
        path.join(os.tmpdir(), "inert-notification-controller-"),
      ),
      output = process.env.PUMP_NOTIFICATION_CONTROLLER_OUTPUT;
    const packet = {
      scope:
        "Synthetic source-controller proof only. All permission/config/device/registration/viewer/messaging/storage/client/query/foreground values are inert supplied ports; NO real API, credentials, tokens, sessions, storage, notifications, subscription or provider HTTP request",
      observations: [],
      pageErrors: [],
      unexpected: [],
      hostRequests: [],
    };
    let server, browser, page;
    const state = () => page.evaluate(() => window.notificationHarness.state()),
      counts = () => page.evaluate(() => window.notificationHarness.counts()),
      events = () => page.evaluate(() => window.notificationHarness.events());
    const waitState = async (expected) => {
      await page.waitForFunction((e) => {
        const s = window.notificationHarness.state();
        return s && Object.entries(e).every(([k, v]) => s[k] === v);
      }, expected);
      return state();
    };
    const waitCounts = async (expected) => {
      await page.waitForFunction((e) => {
        const c = window.notificationHarness.counts();
        return Object.entries(e).every(([k, v]) => c[k] === v);
      }, expected);
      return counts();
    };
    const observe = async (name) => {
      packet.observations.push({
        name,
        state: await state(),
        counts: await counts(),
      });
    };
    const scope = async (patch) => {
      const n = await page.evaluate(() =>
        window.notificationHarness.hostSerial(),
      );
      await page.evaluate((p) => window.notificationHarness.scope(p), patch);
      await page.waitForFunction(
        (n) => window.notificationHarness.hostSerial() > n,
        n,
      );
    };
    const plan = async (kind, plans) =>
      page.evaluate(
        ({ kind, plans }) => window.notificationHarness.plan(kind, plans),
        { kind, plans },
      );
    const release = async (method, id, value) =>
      page.evaluate(
        ({ method, id, value }) =>
          window.notificationHarness[method](id, value),
        { method, id, value },
      );
    const waitReport = async (operation) =>
      page.waitForFunction(
        (op) =>
          window.notificationHarness
            .events()
            .some((e) => e.type === "report-error" && e.operation === op),
        operation,
      );
    try {
      const result = await build({
          absWorkingDir: app,
          entryPoints: ["tests/fixtures/notifications-controller-browser.mjs"],
          bundle: true,
          platform: "browser",
          format: "esm",
          outfile: path.join(temp, "fixture.js"),
          define: { "process.env.NODE_ENV": '"development"' },
          metafile: true,
          logLevel: "silent",
        }),
        bundle = await readFile(path.join(temp, "fixture.js"));
      packet.bundleSha256 = hash(bundle);
      packet.nodeVersion = process.version;
      packet.reactVersion = frontend("react/package.json").version;
      packet.reactDomVersion = frontend("react-dom/package.json").version;
      packet.esbuildVersion = esbuildVersion;
      packet.bundledInputs = [];
      for (const name of Object.keys(result.metafile.inputs).sort()) {
        const b = await readFile(path.resolve(app, name));
        packet.bundledInputs.push({
          path: name,
          bytes: b.length,
          sha256: hash(b),
        });
      }
      packet.inputs = [];
      for (const name of [
        "reconstruction/notifications-controller/client.mjs",
        "reconstruction/notifications-controller/contract.json",
        "scripts/original-notifications-controller.mjs",
        "tests/fixtures/notifications-controller-browser.mjs",
        "tests/original_notifications_controller.browser.mjs",
        "pnpm-lock.yaml",
      ]) {
        const b = await readFile(path.join(app, name));
        packet.inputs.push({ path: name, bytes: b.length, sha256: hash(b) });
      }
      server = createServer((req, res) => {
        packet.hostRequests.push({ method: req.method, path: req.url });
        if (req.method !== "GET") {
          packet.unexpected.push("nonGET host request");
          res.writeHead(405).end();
        } else if (req.url === "/") {
          res.setHeader("content-type", "text/html");
          res.end(
            '<!doctype html><html><title>Inert notification controller</title><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
          );
        } else if (req.url === "/fixture.js") {
          res.setHeader("content-type", "text/javascript");
          res.end(bundle);
        } else {
          if (req.url !== "/favicon.ico")
            packet.unexpected.push("unknown host path");
          res.writeHead(404).end();
        }
      });
      server.listen(0, "127.0.0.1");
      await once(server, "listening");
      const base = "http://127.0.0.1:" + server.address().port;
      browser = await chromium.launch({
        headless: true,
        executablePath:
          process.env.PUMP_BROWSER_EXECUTABLE ?? chromium.executablePath(),
      });
      packet.chromiumVersion = browser.version();
      const context = await browser.newContext();
      page = await context.newPage();
      page.on("pageerror", (e) => packet.pageErrors.push(e.message));
      await page.addInitScript(() => {
        for (const name of [
          "Notification",
          "localStorage",
          "sessionStorage",
          "PushManager",
        ])
          Object.defineProperty(window, name, {
            get() {
              throw Error("Real " + name + " acquisition excluded");
            },
            configurable: true,
          });
        Object.defineProperty(document, "cookie", {
          get() {
            throw Error("Cookie read excluded");
          },
          set() {
            throw Error("Cookie write excluded");
          },
          configurable: true,
        });
        Object.defineProperty(navigator, "serviceWorker", {
          get() {
            throw Error("Real service worker acquisition excluded");
          },
          configurable: true,
        });
      });
      await page.route("**/*", (route) => {
        const r = route.request();
        if (new URL(r.url()).origin !== base || r.method() !== "GET") {
          packet.unexpected.push("unexpected browser request");
          return route.abort();
        }
        return route.continue();
      });
      await page.goto(base);
      await page.waitForFunction(
        () => window.notificationHarness?.hostSerial() > 0,
      );
      await waitState({
        permission: "default",
        isRegistering: false,
        hasRegistration: false,
        isConfigured: true,
      });
      assert.deepEqual(await counts(), {
        registration: 0,
        api: 0,
        messaging: 0,
        installed: 0,
        active: 0,
        markerOwned: false,
      });
      await observe(
        "initial offered source prompt with no registration/provider activity",
      );
      await plan("registration", [{}, {}]);
      await plan("api", [{}, {}]);
      await plan("messaging", [{}]);
      await page
        .getByRole("button", { name: "Enable synthetic notifications" })
        .click();
      await waitState({ isRegistering: true, permission: "default" });
      assert.equal(
        (await events()).filter((e) => e.type === "permission-request").length,
        1,
      );
      assert.equal(
        await page.getByRole("button", { name: /enabling/ }).isDisabled(),
        true,
      );
      await observe(
        "trusted source prompt click invokes only inert permission capability and busy state",
      );
      await page.evaluate(() => window.notificationHarness.grant("granted"));
      await waitCounts({ registration: 2 });
      await waitState({ permission: "granted", isRegistering: true });
      assert.equal((await counts()).api, 0);
      await observe(
        "held permission transition exposes original overlapping manual/automatic registration calls",
      );
      await release("releaseRegistration", 1, "synthetic-registration-a");
      await waitCounts({ api: 1, messaging: 1 });
      await waitState({ hasRegistration: true, isRegistering: true });
      await release("releaseRegistration", 2, "synthetic-registration-a");
      await waitCounts({ api: 2 });
      assert.equal((await counts()).markerOwned, false);
      await observe(
        "source publishes handle before client success; refs have not committed and overlapping client calls remain",
      );
      await release("releaseApi", 1);
      await waitState({ isRegistering: false });
      await waitCounts({ markerOwned: true });
      assert.equal(
        (await events()).filter((e) => e.type === "api-fulfilled").length,
        1,
      );
      await observe(
        "first finally clears boolean busy even while second call remains held",
      );
      await release("releaseApi", 2);
      await release("releaseMessaging", 1);
      await waitCounts({ installed: 1, active: 1 });
      await observe(
        "successful calls commit source refs/marker and one inert listener",
      );
      await plan("registration", [{ value: "synthetic-registration-a" }]);
      const dedup = await page.evaluate(() =>
        window.notificationHarness.register(),
      );
      assert.deepEqual(dedup, { hasResult: true, resultIsSynthetic: true });
      await waitState({ isRegistering: false });
      assert.equal((await counts()).api, 2);
      await observe(
        "same handle/viewer ref equality skips repeated client mutation",
      );
      await scope({ pathname: "/after", dm: false });
      const before = (await events()).length;
      await page.evaluate(() => window.notificationHarness.emit());
      let tail = (await events()).slice(before);
      assert.deepEqual(
        tail.map((e) => e.type),
        ["foreground", "invalidate-inbox", "refresh-user"],
      );
      assert.equal(tail[0].pathname, "/after");
      assert.equal(tail[0].dm, false);
      assert.equal(tail[0].clientMatches, true);
      assert.equal(tail[0].queryClientMatches, true);
      assert.equal((await counts()).installed, 1);
      await observe(
        "latest path/flag refs and unawaited foreground→inbox→refresh callback order",
      );
      await plan("registration", [{}]);
      await plan("api", [{}]);
      await plan("messaging", [{}, {}]);
      await scope({ viewer: "synthetic-viewer-b" });
      await waitCounts({ registration: 4, messaging: 2, active: 0 });
      assert.equal(
        (await events()).filter((e) => e.type === "remove-registration").length,
        1,
      );
      await release("releaseRegistration", 4, "synthetic-registration-b");
      await waitCounts({ api: 3, messaging: 3 });
      await release("releaseMessaging", 2);
      assert.equal((await counts()).installed, 1);
      await release("releaseMessaging", 3);
      await waitCounts({ installed: 2, active: 1 });
      await release("releaseApi", 3);
      await waitState({ isRegistering: false });
      await observe(
        "viewer change removes old registration and cancels late messaging installation before current listener",
      );
      await scope({ viewer: null });
      await waitState({ hasRegistration: false, isRegistering: false });
      await waitCounts({ active: 0, markerOwned: false });
      assert.equal(
        (await events()).filter((e) => e.type === "remove-registration").length,
        2,
      );
      assert.equal(
        (await events()).filter((e) => e.type === "marker-remove").length,
        1,
      );
      await observe(
        "actual logout branch clears owned marker/state and unregisters listener",
      );
      await scope({ available: false });
      await waitState({
        permission: "unsupported",
        isConfigured: false,
        hasRegistration: false,
      });
      const previous = await counts();
      assert.deepEqual(
        await page.evaluate(() => window.notificationHarness.enable()),
        { hasResult: false },
      );
      assert.deepEqual(await counts(), previous);
      await observe(
        "feature-disabled result uses source defaults and manual enable does no work",
      );
      await page.evaluate(() =>
        window.notificationHarness.reset({
          permission: "granted",
          registration: [{ value: "synthetic-registration-failed" }],
          api: [{ reject: "synthetic API failure" }],
          messaging: [{ value: { syntheticMessaging: true } }],
        }),
      );
      await waitReport("register-token");
      await waitState({
        permission: "granted",
        hasRegistration: true,
        isRegistering: false,
      });
      await waitCounts({ installed: 3, active: 1, markerOwned: false });
      await observe(
        "client rejection propagates to source reporter/finally; handle state remains and no ownership marker commits",
      );
      await page.evaluate(() =>
        window.notificationHarness.reset({
          permission: "granted",
          registration: [{ value: "synthetic-registration-messaging-error" }],
          api: [{ value: null }],
          messaging: [{ reject: "synthetic messaging failure" }],
        }),
      );
      await waitReport("init-messaging");
      await waitState({ hasRegistration: true, isRegistering: false });
      await waitCounts({ active: 0, markerOwned: true });
      await observe(
        "messaging rejection reports its own source operation and installs no listener",
      );
      await page.evaluate(() =>
        window.notificationHarness.reset({
          permission: "default",
          configuration: false,
        }),
      );
      await waitState({
        permission: "default",
        isConfigured: false,
        hasRegistration: false,
      });
      const blocked = await counts();
      assert.deepEqual(
        await page.evaluate(() => window.notificationHarness.register()),
        { hasResult: false, resultIsSynthetic: true },
      );
      assert.deepEqual(await counts(), blocked);
      await observe(
        "configuration-null guard prevents permission and registration work",
      );
      packet.events = await events();
      assert.equal(
        packet.events.filter((e) => e.type === "report-error").length,
        2,
      );
      assert.ok(
        packet.events
          .filter((e) => e.type === "permission-request")
          .every((e) => e.receiver),
      );
      assert.ok(
        packet.events
          .filter((e) => e.type === "api-put")
          .every(
            (e) =>
              e.path === "v1/device-tokens" &&
              JSON.stringify(e.keys) ===
                JSON.stringify(["token", "platform", "deviceId"]) &&
              e.platform === "web" &&
              e.deviceIsSynthetic &&
              e.registrationIsSynthetic,
          ),
      );
      assert.ok(
        packet.events
          .filter((e) => e.type.startsWith("marker-"))
          .every((e) => e.key === "pump-push-token-owned"),
      );
      assert.deepEqual(packet.pageErrors, []);
      assert.deepEqual(packet.unexpected, []);
      assert.ok(
        packet.hostRequests.every((e) =>
          ["/", "/fixture.js", "/favicon.ico"].includes(e.path),
        ),
      );
      await page.evaluate(() => window.notificationHarness.unmount());
      packet.result = "PASS";
    } catch (error) {
      packet.result = "FAIL";
      packet.failure = { name: error.name, message: error.message };
      if (page)
        try {
          packet.events = await events();
          packet.lastState = await state();
          packet.lastCounts = await counts();
        } catch {}
      throw error;
    } finally {
      if (output) {
        await mkdir(output, { recursive: true });
        await writeFile(
          path.join(output, "react-verification.json"),
          JSON.stringify(packet, null, 2) + "\n",
        );
      }
      if (browser) await browser.close();
      if (server) {
        server.closeAllConnections();
        server.close();
      }
      await rm(temp, { recursive: true, force: true });
    }
  },
);
