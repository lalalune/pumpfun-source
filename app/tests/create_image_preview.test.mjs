import test from "node:test";
import assert from "node:assert/strict";
import {
  prepareImagePreview,
  IMAGE_PREVIEW_TIMEOUT_MS,
} from "../packages/frontend/src/app/create-image-preview.ts";

// Explicit decoder events qualify ownership/cancellation, not native image codecs.
function fixture(t) {
  const active = new Set(),
    revoked = [],
    images = [];
  let sequence = 0;
  t.mock.method(URL, "createObjectURL", () => {
    const url = `blob:synthetic-image-${++sequence}`;
    active.add(url);
    return url;
  });
  t.mock.method(URL, "revokeObjectURL", (url) => {
    assert.ok(active.delete(url), "release owned URL exactly once");
    revoked.push(url);
  });
  const previous = Object.getOwnPropertyDescriptor(globalThis, "Image");
  globalThis.Image = class {
    naturalWidth = 1;
    naturalHeight = 1;
    constructor() {
      images.push(this);
    }
    removeAttribute(name) {
      assert.equal(name, "src");
      this.src = "";
    }
  };
  t.after(() => {
    if (previous) Object.defineProperty(globalThis, "Image", previous);
    else delete globalThis.Image;
    assert.equal(active.size, 0);
  });
  return { active, revoked, images };
}
const file = (type = "image/png", content = "synthetic") =>
  new File([content], "local.png", { type });

test("successful load transfers URL ownership and clears listeners", async (t) => {
  const f = fixture(t),
    controller = new AbortController();
  const pending = prepareImagePreview(file(), controller.signal);
  f.images[0].onload();
  const url = await pending;
  controller.abort();
  assert.equal(f.active.has(url), true);
  assert.equal(f.images[0].onload, null);
  assert.equal(f.images[0].onerror, null);
  assert.equal(f.images[0].src, "");
  URL.revokeObjectURL(url);
});

test("decode rejection and zero dimensions revoke candidate URLs", async (t) => {
  const f = fixture(t);
  for (const mode of ["error", "zero"]) {
    const pending = prepareImagePreview(file(), new AbortController().signal);
    const assertion = assert.rejects(pending, /could not decode/);
    const image = f.images.at(-1);
    if (mode === "zero") {
      image.naturalWidth = 0;
      image.onload();
    } else image.onerror();
    await assertion;
  }
  assert.equal(f.revoked.length, 2);
});

test("abort before or during decode ignores late callbacks and releases ownership", async (t) => {
  const f = fixture(t),
    controller = new AbortController();
  const pending = prepareImagePreview(file(), controller.signal);
  const assertion = assert.rejects(pending, { name: "AbortError" });
  const late = f.images[0].onload;
  controller.abort();
  late();
  await assertion;
  await assert.rejects(prepareImagePreview(file(), controller.signal), {
    name: "AbortError",
  });
  assert.equal(f.images.length, 1);
  assert.equal(f.revoked.length, 1);
});

test("timeout is bounded and late decode cannot transfer released URL", async (t) => {
  const f = fixture(t);
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const pending = prepareImagePreview(file(), new AbortController().signal);
  const assertion = assert.rejects(pending, /timed out/);
  const late = f.images[0].onload;
  t.mock.timers.tick(IMAGE_PREVIEW_TIMEOUT_MS);
  late();
  await assertion;
  assert.equal(f.revoked.length, 1);
});

test("allocation failure rejects cleanly without a retained URL", async (t) => {
  fixture(t);
  t.mock.method(URL, "createObjectURL", () => {
    throw new Error("allocation failed");
  });
  await assert.rejects(
    prepareImagePreview(file(), new AbortController().signal),
    /allocation failed/,
  );
});
