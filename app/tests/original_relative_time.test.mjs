import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { recoverRelativeTime } from "../scripts/original-relative-time.mjs";
import { openCorpus, sha256 } from "../scripts/original-contracts/source.mjs";
import test from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import {
  createServerClock,
  createClockTicks,
  parseTimestamp,
  formatElapsed,
} from "../reconstruction/relative-time/model.mjs";
function deferred() {
  let resolve;
  const promise = new Promise((r) => {
    resolve = r;
  });
  return { promise, resolve };
}
function fixture() {
  let now = 1250,
    offset = 0,
    syncCount = 0,
    sequence = 0;
  const timers = new Map(),
    document = new EventTarget();
  document.hidden = false;
  const clock = {
    now: () => now + offset,
    offset: () => offset,
    synchronize: () => {
      syncCount++;
      return Promise.resolve();
    },
  };
  const ticks = createClockTicks({
    clock,
    document,
    setTimeout: (callback, delay) => {
      const id = ++sequence;
      timers.set(id, { callback, delay });
      return id;
    },
    clearTimeout: (id) => timers.delete(id),
  });
  return {
    ticks,
    timers,
    document,
    setNow: (n) => {
      now = n;
    },
    setOffset: (n) => {
      offset = n;
    },
    syncCount: () => syncCount,
    visibility(hidden) {
      document.hidden = hidden;
      document.dispatchEvent(new Event("visibilitychange"));
    },
    fire() {
      const [id, timer] = timers.entries().next().value;
      timers.delete(id);
      timer.callback();
    },
  };
}
test("timestamp parser preserves null/date/number/string rules and seconds threshold", () => {
  for (const x of [
    null,
    undefined,
    NaN,
    Infinity,
    -Infinity,
    "bad",
    new Date(NaN),
  ])
    assert.equal(parseTimestamp(x), null);
  for (const [x, y] of [
    [0, 0],
    [-2, -2000],
    [9999999999, 9999999999000],
    [10000000000, 10000000000],
    [1e100, 1e100],
  ])
    assert.equal(parseTimestamp(x), y);
  const d = new Date("2026-10-29T00:00:00.000Z");
  assert.equal(parseTimestamp(d), d.getTime());
  assert.equal(parseTimestamp(d.toISOString()), d.getTime());
  assert.throws(() => parseTimestamp(Symbol()), TypeError);
});
test("elapsed labels preserve one-second/future clamp, floor and30day/360day units", () => {
  for (const x of [NaN, Infinity, -Infinity])
    assert.equal(formatElapsed(x), "");
  for (const x of [-100000, 0, 1, 999, 1999])
    assert.equal(formatElapsed(x), "1s ago");
  for (const [x, y] of [
    [59999, "59s"],
    [60000, "1m"],
    [3599999, "59m"],
    [3600000, "1h"],
    [86399999, "23h"],
    [86400000, "1d"],
    [2591999999, "29d"],
    [2592000000, "1mo"],
    [31103999999, "11mo"],
    [31104000000, "1y"],
  ]) {
    assert.equal(formatElapsed(x), y + " ago");
    assert.equal(formatElapsed(x, false), y);
  }
});
test("sampler preserves exact path/cache/credentials/timeout and shared in-flight Promise", async () => {
  const p = deferred();
  let now = 1000,
    calls = 0;
  const signal = new AbortController().signal;
  const clock = createServerClock({
    now: () => now,
    timeoutSignal: (ms) => {
      assert.equal(ms, 5000);
      return signal;
    },
    fetch: (path, options) => {
      calls++;
      assert.equal(path, "/api/server-time");
      assert.deepEqual(options, {
        cache: "no-store",
        credentials: "omit",
        signal,
      });
      return p.promise;
    },
  });
  const a = clock.synchronize(),
    b = clock.synchronize();
  assert.equal(a, b);
  assert.equal(calls, 1);
  assert.equal(clock.hasSynchronized(), false);
  now = 1100;
  p.resolve(Response.json({ nowMs: 12000 }));
  await a;
  assert.equal(clock.offset(), 10950);
  assert.equal(clock.now(), 12050);
  assert.equal(clock.hasSynchronized(), true);
});
test("offset deadband is strictly less than5000 with rounded midpoint correction", async () => {
  for (const [x, y] of [
    [4999.9, 0],
    [-4999.9, 0],
    [5000, 5000],
    [-5000, -5000],
    [5000.6, 5001],
    [-5000.6, -5001],
  ]) {
    const c = createServerClock({
      now: () => 10000,
      fetch: async () => Response.json({ nowMs: 10000 + x }),
    });
    await c.synchronize();
    assert.equal(c.offset(), y);
  }
});
test("successful sample is eligible exactly15minutes after receipt", async () => {
  let now = 1000,
    calls = 0;
  const c = createServerClock({
    now: () => now,
    fetch: async () => {
      calls++;
      return Response.json({ nowMs: now });
    },
  });
  await c.synchronize();
  now = 900999;
  await c.synchronize();
  assert.equal(calls, 1);
  now = 901000;
  await c.synchronize();
  assert.equal(calls, 2);
});
test("HTTP/decode/body/abort failures retain60second backoff without fabricated sync", async () => {
  for (const fail of [
    async () => new Response("bad", { status: 503 }),
    async () => new Response("bad"),
    async () => Response.json(null),
    async () => Response.json({ nowMs: "1000" }),
    async () => Response.json({}),
    async () => Response.json({ nowMs: null }),
    async () => {
      throw new DOMException("Aborted", "AbortError");
    },
  ]) {
    let now = 1000,
      calls = 0;
    const c = createServerClock({
      now: () => now,
      fetch: async () => {
        calls++;
        return fail();
      },
    });
    await c.synchronize();
    assert.equal(c.offset(), 0);
    assert.equal(c.hasSynchronized(), false);
    now = 60999;
    await c.synchronize();
    assert.equal(calls, 1);
    now = 61000;
    await c.synchronize();
    assert.equal(calls, 2);
  }
});
test("later failure preserves previously synchronized offset/status", async () => {
  let now = 1000,
    fail = false;
  const c = createServerClock({
    now: () => now,
    fetch: async () => {
      if (fail) throw Error("offline");
      return Response.json({ nowMs: 9000 });
    },
  });
  await c.synchronize();
  assert.equal(c.offset(), 8000);
  fail = true;
  now = 901000;
  await c.synchronize();
  assert.equal(c.offset(), 8000);
  assert.equal(c.hasSynchronized(), true);
});
test("actual loopback GET/JSON response traverse the clock sampler", async (t) => {
  let now = 1000;
  const requests = [];
  const server = createServer((req, res) => {
    requests.push(`${req.method} ${req.url}`);
    now = 1100;
    res.writeHead(200, {
      "content-type": "application/json",
      "cache-control": "no-store",
    });
    res.end(JSON.stringify({ nowMs: 12000 }));
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  t.after(() => new Promise((r) => server.close(r)));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const c = createServerClock({
    now: () => now,
    fetch: (path, options) => fetch(new URL(path, origin), options),
  });
  await c.synchronize();
  assert.deepEqual(requests, ["GET /api/server-time"]);
  assert.equal(c.offset(), 10950);
  assert.equal(c.now(), 12050);
});
test("first/last subscriptions share one aligned timer and visibility listener", () => {
  const f = fixture();
  let calls = 0;
  const a = f.ticks.subscribe(() => calls++),
    b = f.ticks.subscribe(() => calls++);
  assert.equal(f.timers.size, 1);
  assert.equal([...f.timers.values()][0].delay, 750);
  assert.equal(f.syncCount(), 1);
  assert.equal(f.ticks.getServerSnapshot(), 0);
  f.setNow(2000);
  f.fire();
  assert.equal(calls, 2);
  assert.equal(f.ticks.getSnapshot(), 2000);
  assert.equal([...f.timers.values()][0].delay, 1000);
  a();
  assert.equal(f.timers.size, 1);
  b();
  assert.equal(f.timers.size, 0);
  f.visibility(false);
  assert.equal(f.syncCount(), 1);
});
test("visibility hide stops ticking and resume refreshes snapshot/sample eligibility", () => {
  const f = fixture();
  let calls = 0;
  const stop = f.ticks.subscribe(() => calls++);
  f.visibility(true);
  assert.equal(f.timers.size, 0);
  assert.equal(f.syncCount(), 1);
  f.setNow(6750);
  f.visibility(false);
  assert.equal(calls, 1);
  assert.equal(f.ticks.getSnapshot(), 6750);
  assert.equal([...f.timers.values()][0].delay, 250);
  assert.equal(f.syncCount(), 2);
  stop();
});
test("initial hidden subscriber still samples but starts no display timer", () => {
  const f = fixture();
  f.document.hidden = true;
  const stop = f.ticks.subscribe(() => {});
  assert.equal(f.timers.size, 0);
  assert.equal(f.syncCount(), 1);
  stop();
});
test("changed offset notifies active listeners after sync, but not unsubscribed listeners", async () => {
  const f = fixture();
  let calls = 0;
  const stop = f.ticks.subscribe(() => calls++);
  f.setOffset(9000);
  await Promise.resolve();
  assert.equal(calls, 1);
  assert.equal(f.ticks.getSnapshot(), 10250);
  stop();
  const g = fixture();
  let after = 0;
  const cancel = g.ticks.subscribe(() => after++);
  g.setOffset(9000);
  cancel();
  await Promise.resolve();
  assert.equal(after, 0);
});
test("ordinary display ticks never create periodic server samples", () => {
  const f = fixture(),
    stop = f.ticks.subscribe(() => {});
  f.setNow(99999999);
  f.fire();
  assert.equal(f.syncCount(), 1);
  stop();
});
test("source rearm-after-notification edge stays explicit", () => {
  const f = fixture(),
    calls = [];
  let stop;
  stop = f.ticks.subscribe(() => {
    calls.push("first");
    stop();
  });
  f.fire();
  assert.deepEqual(calls, ["first"]);
  // Original632817 rearms even when the last listener unsubscribes inside emit.
  assert.equal(f.timers.size, 1);
  stop();
  assert.equal(f.timers.size, 0);
});

const root = fileURLToPath(new URL("..", import.meta.url));
const artifact = await recoverRelativeTime(root);
test("actual529841.f and actual204478.f consumer plus both format variants and English Flight data are bound", () => {
  assert.equal(artifact.entry.id, 529841);
  assert.equal(artifact.entry.actualConsumer.id, 204478);
  assert.equal(artifact.entry.actualConsumer.export, "f");
  assert.equal(artifact.formats.length, 2);
  assert.equal(new Set(artifact.formats.map((x) => x.factory.sha256)).size, 2);
  assert.deepEqual(artifact.english.units, {
    year: "y",
    month: "mo",
    day: "d",
    hour: "h",
    minute: "m",
    second: "s",
  });
  assert.equal(artifact.english.suffix, "{{time}} ago");
});
test("artifact/current implementation and every raw UTF16/UTF8 factory/English-literal range reproduce", async () => {
  assert.equal(
    await fs.readFile(
      path.join(root, "reconstruction/relative-time/contract.json"),
      "utf8",
    ),
    JSON.stringify(artifact, null, 2) + "\n",
  );
  const corpus = await openCorpus(root);
  for (const w of [...artifact.fragments, artifact.english.originalLiteral]) {
    const source = await corpus.capture(w.source);
    assert.equal(sha256(source.bytes.subarray(...w.utf8)), w.sha256);
    if (w.text !== undefined)
      assert.equal(source.text.slice(...w.utf16), w.text);
  }
  for (const p of artifact.implementation)
    assert.equal(sha256(await fs.readFile(path.join(root, p.path))), p.sha256);
});
test("tampered clock factory and English Flight input each fail authentication before recovery", async (t) => {
  const temp = await fs.mkdtemp(
    path.join(os.tmpdir(), "relative-time-source-"),
  );
  t.after(() => fs.rm(temp, { recursive: true, force: true }));
  const files = new Set([
    "evidence/web/manifest.json",
    "recovered/modules.json",
    ...artifact.factories.map((f) => f.source),
    artifact.english.originalLiteral.source,
  ]);
  for (const name of files) {
    const target = path.join(temp, name);
    await fs.mkdir(path.dirname(target), { recursive: true });
    await fs.copyFile(path.join(root, name), target);
  }
  for (const name of [
    artifact.factories.find((f) => f.id === 668487).source,
    artifact.english.originalLiteral.source,
  ]) {
    const target = path.join(temp, name),
      bytes = await fs.readFile(target),
      original = Buffer.from(bytes);
    bytes[100] ^= 1;
    await fs.writeFile(target, bytes);
    await assert.rejects(
      recoverRelativeTime(temp),
      /capture authentication failed/,
    );
    await fs.writeFile(target, original);
  }
});
