import assert from "node:assert/strict";
import { test } from "node:test";
import {
  readFile,
  writeFile,
  mkdtemp,
  mkdir,
  link,
  rm,
} from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  competitionRefreshInterval,
  competitionIsForeground,
  startCompetitionReads,
} from "../packages/frontend/src/app/leaderboard/competition-refresh.ts";
import { verifyCompetitionRefresh } from "../scripts/verify-competition-refresh.mjs";
import { startCompetitionRefreshHttp } from "./fixtures/competition-refresh-http.mjs";
import { parseLeaderboardResponse } from "../packages/frontend/src/app/leaderboard/types.ts";

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const LOOP = "packages/frontend/src/app/leaderboard/competition-refresh.ts";
const PAGE = "packages/frontend/src/app/leaderboard/leaderboard-client.tsx";
const flush = () => new Promise((resolve) => setImmediate(resolve));
function deferred() {
  let resolve;
  const promise = new Promise((r) => {
    resolve = r;
  });
  return { promise, resolve };
}
function browser({ visible = true, focused = true } = {}) {
  class Target extends EventTarget {
    events = new Map();
    addEventListener(name, fn) {
      super.addEventListener(name, fn);
      if (!this.events.has(name)) this.events.set(name, new Set());
      this.events.get(name).add(fn);
    }
    removeEventListener(name, fn) {
      super.removeEventListener(name, fn);
      this.events.get(name)?.delete(fn);
    }
  }
  const document = new Target(),
    window = new Target();
  document.visibilityState = visible ? "visible" : "hidden";
  document.focused = focused;
  document.hasFocus = () => document.focused;
  let id = 0;
  const timers = new Map();
  return {
    document,
    window,
    timers,
    setTimeout(callback, delay) {
      const n = ++id;
      timers.set(n, { callback, delay });
      return n;
    },
    clearTimeout(id) {
      timers.delete(id);
    },
    fire() {
      assert.equal(timers.size, 1);
      const [id, item] = [...timers][0];
      timers.delete(id);
      item.callback();
    },
    focus(value) {
      document.focused = value;
      window.dispatchEvent(new Event(value ? "focus" : "blur"));
    },
    visible(value) {
      document.visibilityState = value ? "visible" : "hidden";
      document.dispatchEvent(new Event("visibilitychange"));
    },
    listeners() {
      return [...document.events.values(), ...window.events.values()].reduce(
        (n, set) => n + set.size,
        0,
      );
    },
  };
}

test("accepted complete caller, both source variants, cadence and used native fetch/cleanup are bound", async () => {
  const result = await verifyCompetitionRefresh();
  assert.deepEqual(result.originalDescriptors, {
    "useList.mjs": { intervalMs: 60000, staleTimeMs: 15000 },
    "useDetail.mjs": { intervalMs: 15000, staleTimeMs: 5000 },
  });
  assert.ok(
    result.actualConsumerCalls.some((row) => row.label.includes("961415.f")),
  );
  assert.equal(
    result.originalWitnesses.filter((row) =>
      row.label.includes("same complete snapshot"),
    ).length,
    2,
  );
});

test("source gate rejects wrong detail cadence, OR foreground, ignored cleanup and detached request signal", async (t) => {
  const dir = await mkdtemp(path.join(APP, ".competition-refresh-mutant-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  for (const name of [
    "evidence/web/manifest.json",
    "recovered/modules.json",
    "scripts/original-contracts/source.mjs",
  ]) {
    await mkdir(path.dirname(path.join(dir, name)), { recursive: true });
    await link(path.join(APP, name), path.join(dir, name));
  }
  for (const relative of [
    "packages/frontend/src/app/api/leaderboard/route.ts",
    "packages/frontend/src/app/api/leaderboard/upstream.ts",
    "packages/frontend/src/app/leaderboard/types.ts",
    LOOP,
    PAGE,
  ]) {
    await mkdir(path.dirname(path.join(dir, relative)), { recursive: true });
    await writeFile(
      path.join(dir, relative),
      await readFile(path.join(APP, relative)),
    );
  }
  const contract = await verifyCompetitionRefresh();
  const sources = new Set();
  const visit = (value) => {
    if (!value || typeof value !== "object") return;
    for (const [key, child] of Object.entries(value)) {
      if (
        key === "source" &&
        typeof child === "string" &&
        child.startsWith("evidence/web/objects/")
      )
        sources.add(child);
      visit(child);
    }
  };
  // The accepted producer validates its complete prerequisite closure as well.
  const { buildCompetitionClient } = await import(
    "../scripts/original-competition-client.mjs"
  );
  visit((await buildCompetitionClient()).contract);
  visit(contract);
  for (const relative of sources) {
    await mkdir(path.dirname(path.join(dir, relative)), { recursive: true });
    await link(path.join(APP, relative), path.join(dir, relative));
  }
  await verifyCompetitionRefresh(dir);
  for (const [file, from, to, expected] of [
    [LOOP, "? 15_000", "? 5_000", /used list\/detail cadence/],
    [
      LOOP,
      '"visible" === document.visibilityState && document.hasFocus()',
      '"visible" === document.visibilityState || document.hasFocus()',
      /visible AND focused/,
    ],
    [
      PAGE,
      "return startCompetitionReads(",
      "startCompetitionReads(",
      /effect returns loop cleanup/,
    ],
    [
      PAGE,
      "          signal,",
      "          signal: undefined,",
      /actual request abort signal/,
    ],
  ]) {
    for (const item of [LOOP, PAGE])
      await writeFile(
        path.join(dir, item),
        await readFile(path.join(APP, item)),
      );
    const original = await readFile(path.join(APP, file), "utf8");
    assert.ok(
      original.includes(from),
      file + ": expected actual mutation site",
    );
    await writeFile(path.join(dir, file), original.replace(from, to));
    await assert.rejects(verifyCompetitionRefresh(dir), expected);
  }
});

test("native policy limits recurrence to competition list/detail and requires visible AND focused", () => {
  assert.equal(competitionRefreshInterval("competitions", null), 60000);
  assert.equal(competitionRefreshInterval("competitions", ""), 60000); // Existing native request treats empty as list.
  assert.equal(competitionRefreshInterval("competitions", "cup"), 15000);
  for (const category of ["traders", "creators"])
    assert.equal(competitionRefreshInterval(category, "cup"), false);
  for (const visible of [true, false])
    for (const focused of [true, false]) {
      const env = browser({ visible, focused });
      assert.equal(competitionIsForeground(env.document), visible && focused);
    }
});

test("first read runs even without foreground, recurrence waits exact policy, all subscriptions clean up", async () => {
  for (const interval of [15000, 60000]) {
    const env = browser({ focused: false });
    let reads = 0;
    const stop = startCompetitionReads(
      async () => {
        reads++;
      },
      interval,
      env,
    );
    assert.equal(reads, 1);
    await flush();
    assert.equal(env.timers.size, 0);
    assert.equal(env.listeners(), 3);
    env.focus(true);
    assert.equal([...env.timers.values()][0].delay, interval);
    env.fire();
    await flush();
    assert.equal(reads, 2);
    assert.equal([...env.timers.values()][0].delay, interval);
    stop();
    assert.equal(env.listeners(), 0);
    assert.equal(env.timers.size, 0);
  }
});

test("blur and hidden cancel only future polls; equivalent snapshots do not reset a pending interval", async () => {
  const env = browser();
  let reads = 0;
  const stop = startCompetitionReads(
    async () => {
      reads++;
    },
    15000,
    env,
  );
  await flush();
  const first = [...env.timers.keys()][0];
  env.focus(true);
  env.visible(true);
  assert.equal([...env.timers.keys()][0], first);
  env.focus(false);
  assert.equal(env.timers.size, 0);
  env.visible(false);
  env.focus(true);
  assert.equal(env.timers.size, 0);
  env.visible(true);
  assert.equal(env.timers.size, 1);
  assert.equal(reads, 1);
  stop();
});

test("pending reads never overlap; foreground return during a read cannot start another; dispose aborts", async () => {
  const env = browser(),
    first = deferred(),
    second = deferred(),
    signals = [];
  const stop = startCompetitionReads(
    ({ signal }) => {
      signals.push(signal);
      return signals.length === 1 ? first.promise : second.promise;
    },
    15000,
    env,
  );
  assert.equal(signals.length, 1);
  assert.equal(env.timers.size, 0);
  env.focus(false);
  env.focus(true);
  assert.equal(env.timers.size, 0);
  first.resolve();
  await flush();
  env.fire();
  assert.equal(signals.length, 2);
  assert.equal(env.timers.size, 0);
  env.visible(false);
  env.visible(true);
  assert.equal(env.timers.size, 0);
  stop();
  assert.equal(signals[1].aborted, true);
  second.resolve();
  await flush();
  assert.equal(env.timers.size, 0);
  assert.equal(env.listeners(), 0);
});

test("backgrounding an in-flight read preserves that read, then remains stopped until foreground", async () => {
  const env = browser(),
    held = deferred();
  let signal;
  const stop = startCompetitionReads(
    (options) => {
      signal = options.signal;
      return held.promise;
    },
    60000,
    env,
  );
  env.visible(false);
  assert.equal(signal.aborted, false);
  held.resolve();
  await flush();
  assert.equal(env.timers.size, 0);
  env.visible(true);
  assert.equal([...env.timers.values()][0].delay, 60000);
  stop();
});

test("non-competition read stays single-attempt without subscriptions or browser snapshot access", async () => {
  const env = browser();
  env.document.hasFocus = () => {
    throw new Error("unexpected foreground read");
  };
  let reads = 0;
  const stop = startCompetitionReads(
    async () => {
      reads++;
    },
    false,
    env,
  );
  await flush();
  assert.equal(reads, 1);
  assert.equal(env.listeners(), 0);
  assert.equal(env.timers.size, 0);
  stop();
});

test("actual native handler and exported adapter observe changed supplied facts with the key gate retained", async (t) => {
  const fixture = await startCompetitionRefreshHttp();
  t.after(() => fixture.close());
  assert.equal(
    (await fetch(fixture.backendUrl + "/v1/competitions")).status,
    401,
  );
  const read = async (detail) => {
    const response = await fetch(
      fixture.adapterUrl +
        "/api/leaderboard?category=competitions" +
        (detail ? "&id=" + fixture.slug : ""),
    );
    assert.equal(response.status, 200);
    const body = parseLeaderboardResponse(await response.json());
    assert.equal(body.ok, true);
    return body.data;
  };
  assert.equal((await read(false)).live[0].title, "Synthetic read snapshot 1");
  assert.equal((await read(true)).entries[0].pnlUsd, 100);
  await fixture.command("advance");
  assert.equal((await read(false)).live[0].title, "Synthetic read snapshot 2");
  assert.equal((await read(true)).entries[0].pnlUsd, 200);
  await fixture.command("stop-backend");
  const failed = await fetch(
    fixture.adapterUrl +
      "/api/leaderboard?category=competitions&id=" +
      fixture.slug,
  );
  assert.equal(failed.status, 502);
  assert.equal((await failed.json()).ok, false);
  await fixture.command("start-backend");
  assert.equal((await read(true)).entries[0].pnlUsd, 200);
  const { ledger } = await fixture.command("snapshot");
  assert.ok(ledger.every((row) => row.method === "GET"));
  assert.ok(ledger.some((row) => !row.keyMatched && row.status === 401));
  assert.ok(
    ledger.filter((row) => row.keyMatched).every((row) => row.status === 200),
  );
});
