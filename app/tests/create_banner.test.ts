import assert from "node:assert/strict";
import { test } from "node:test";
import {
  BANNER_TIMEOUT_MS,
  BANNER_BYTES,
  BANNER_MAX_PIXELS,
  BANNER_TYPES,
  BannerDraftSession,
  prepareBanner,
  validateBanner,
  type BannerPlatform,
  type BannerPreview,
  type BannerState,
} from "../packages/frontend/src/app/create-banner-preview.ts";

const file = (name = "banner.png", type = "image/png", size = 10) =>
  new File([new Uint8Array(size)], name, { type });
function preview(name: string) {
  let releases = 0;
  return {
    value: {
      file: file(name),
      url: `blob:${name}`,
      width: 2,
      height: 1,
      dispose() {
        releases++;
      },
    } satisfies BannerPreview,
    releases: () => releases,
  };
}
function deferred<T>() {
  let resolve!: (value: T) => void, reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
function platform(width = 1500, height = 500) {
  const urls: string[] = [],
    revoked: string[] = [];
  const image = {
    naturalWidth: width,
    naturalHeight: height,
    onload: null as (() => void) | null,
    onerror: null as (() => void) | null,
    removeAttribute() {},
    decoding: "",
    src: "",
  };
  const api: BannerPlatform = {
    image: () => image as unknown as HTMLImageElement,
    url: () => {
      const url = `blob:${urls.length}`;
      urls.push(url);
      return url;
    },
    revoke: (url) => revoked.push(url),
  };
  return { api, image, urls, revoked };
}

test("admission is exact four-type, nonempty and inclusive4.5MB; no filename bypass", () => {
  for (const type of BANNER_TYPES)
    assert.equal(
      validateBanner(file("any.extension", type, BANNER_BYTES)),
      undefined,
    );
  for (const type of [
    "",
    "image/svg+xml",
    "video/mp4",
    "text/html",
    "image/jpg",
  ])
    assert.match(validateBanner(file("banner.png", type))!, /Choose a JPEG/);
  for (const size of [0, BANNER_BYTES + 1])
    assert.match(validateBanner(file("x", "image/png", size))!, /non-empty/);
});
test("invalid file and already-aborted admission allocate no URL or decoder", async () => {
  const p = platform();
  const c = new AbortController();
  c.abort();
  await assert.rejects(prepareBanner(file(), c.signal, p.api), {
    name: "AbortError",
  });
  await assert.rejects(
    prepareBanner(
      file("x", "image/svg+xml"),
      new AbortController().signal,
      p.api,
    ),
    /Choose a JPEG/,
  );
  assert.deepEqual(p.urls, []);
});
test("decoded dimensions are descriptive;3:1 is not enforced; resource has one release", async () => {
  const p = platform(19, 7),
    c = new AbortController();
  const pending = prepareBanner(file(), c.signal, p.api);
  p.image.onload!();
  const result = await pending;
  assert.equal(result.width, 19);
  assert.equal(result.height, 7);
  assert.deepEqual(p.revoked, []);
  assert.equal(p.image.onload, null);
  assert.equal(p.image.onerror, null);
  result.dispose();
  result.dispose();
  assert.deepEqual(p.revoked, ["blob:0"]);
});
test("unreadable image and active cancellation release URLs and handlers", async () => {
  for (const abort of [false, true]) {
    const p = platform(),
      c = new AbortController();
    const pending = prepareBanner(file(), c.signal, p.api);
    if (abort) c.abort();
    else p.image.onerror!();
    await assert.rejects(
      pending,
      abort ? { name: "AbortError" } : /could not decode/,
    );
    assert.deepEqual(p.revoked, ["blob:0"]);
    assert.equal(p.image.onload, null);
    assert.equal(p.image.onerror, null);
  }
});
test("invalid or oversized decoded dimensions fail within local allocation policy", async () => {
  for (const [w, h] of [
    [0, 5],
    [5, 0],
    [NaN, 1],
    [BANNER_MAX_PIXELS, 2],
  ]) {
    const p = platform(w, h),
      pending = prepareBanner(file(), new AbortController().signal, p.api);
    p.image.onload!();
    await assert.rejects(pending, /16-megapixel/);
    assert.deepEqual(p.revoked, ["blob:0"]);
  }
});
test("accepted banner persists across invalid and failed replacements; successful replace releases old", async () => {
  const states: BannerState[] = [],
    a = preview("first"),
    b = preview("second");
  const s = new BannerDraftSession(
    (state) => states.push(state),
    async (f) => {
      if (f.name === "broken") throw new Error("unreadable");
      return f.name === "first" ? a.value : b.value;
    },
  );
  await s.choose(file("first"));
  await s.choose(file("bad", "video/mp4"));
  assert.equal(states.at(-1)?.preview, a.value);
  assert.match(states.at(-1)!.error, /JPEG/);
  await s.choose(file("broken"));
  assert.equal(states.at(-1)?.preview, a.value);
  assert.equal(a.releases(), 0);
  await s.choose(file("second"));
  assert.equal(states.at(-1)?.preview, b.value);
  assert.equal(a.releases(), 1);
  s.dispose();
  assert.equal(b.releases(), 1);
});
test("out-of-order decodes cannot replace a newer accepted banner and stale resources release", async () => {
  const old = deferred<BannerPreview>(),
    newer = preview("newer"),
    stale = preview("stale");
  let state: BannerState | undefined, firstSignal: AbortSignal | undefined;
  const s = new BannerDraftSession(
    (next) => {
      state = next;
    },
    async (f, signal) => {
      if (f.name === "old") {
        firstSignal = signal;
        return old.promise;
      }
      return newer.value;
    },
  );
  const pending = s.choose(file("old"));
  await s.choose(file("new"));
  assert.equal(firstSignal?.aborted, true);
  old.resolve(stale.value);
  await pending;
  assert.equal(state?.preview, newer.value);
  assert.equal(stale.releases(), 1);
  s.dispose();
});
test("clear and unmount cancel pending work, dispose late success, and publish no late state", async () => {
  for (const unmount of [false, true]) {
    const d = deferred<BannerPreview>(),
      late = preview("late");
    const states: BannerState[] = [];
    const s = new BannerDraftSession(
      (next) => states.push(next),
      () => d.promise,
    );
    const pending = s.choose(file());
    if (unmount) s.dispose();
    else s.clear();
    const length = states.length;
    d.resolve(late.value);
    await pending;
    assert.equal(states.length, length);
    assert.equal(late.releases(), 1);
    s.dispose();
    s.dispose();
  }
});
test("invalid replacement cancels old decode; a late rejection cannot replace its useful error", async () => {
  const d = deferred<BannerPreview>();
  const states: BannerState[] = [];
  const s = new BannerDraftSession(
    (next) => states.push(next),
    () => d.promise,
  );
  const pending = s.choose(file());
  await s.choose(file("bad", "text/plain"));
  d.reject(new Error("stale failure"));
  await pending;
  assert.match(states.at(-1)!.error, /JPEG/);
  assert.equal(states.at(-1)!.pending, false);
  s.dispose();
});

test("decoder timeout releases resources without waiting on a native codec", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const p = platform();
  const pending = prepareBanner(file(), new AbortController().signal, p.api);
  t.mock.timers.tick(BANNER_TIMEOUT_MS);
  await assert.rejects(pending, /timed out/);
  assert.deepEqual(p.revoked, ["blob:0"]);
  assert.equal(p.image.onload, null);
  t.mock.timers.reset();
});
