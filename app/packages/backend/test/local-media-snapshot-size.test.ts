import assert from "node:assert/strict";
import {
  mkdtemp,
  readFile,
  readdir,
  rm,
  stat,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test, { type TestContext } from "node:test";
import {
  LocalMediaStore,
  type LocalMediaLimits,
} from "../src/local-media-store.js";

const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aK1cAAAAASUVORK5CYII=",
  "base64",
);

async function setup(t: TestContext, limits: LocalMediaLimits) {
  const directory = await mkdtemp(join(tmpdir(), "local-media-snapshot-"));
  const opened: LocalMediaStore[] = [];
  t.after(async () => {
    for (const store of opened) await store.close();
    await rm(directory, { recursive: true, force: true });
  });
  async function reopen() {
    const store = await LocalMediaStore.open(directory, limits);
    opened.push(store);
    return store;
  }
  return { directory, reopen, store: await reopen() };
}

for (const [label, character, count] of [
  ["JSON-escaped", "\u0001", 4],
  ["multibyte Unicode", "界", 16],
] as const) {
  test(`accepted ${label} metadata survives restart under a small image-byte quota`, async (t) => {
    const limits = { maxBytes: 1024, maxImages: 1, maxMetadata: count };
    const { directory, store, reopen } = await setup(t, limits);
    const image = await store.putImage(PNG, "image/png");
    const expected = [];
    for (let n = 0; n < count; n++) {
      const uploaded = await store.putMetadata({
        imageId: image.id,
        name: `Synthetic ${n}`,
        symbol: "TEST",
        description: character.repeat(2000),
        showName: false,
        twitter: "https://x.com/p" + character.repeat(2000),
        telegram: "https://t.me/p" + character.repeat(2000),
        website: "https://example.test/" + character.repeat(2000),
      });
      expected.push(store.getMetadata(uploaded.id));
    }
    // Regression: all these records were admitted, but the previous independent
    // read heuristic rejected the file that the same store had just published.
    const priorReadBound = limits.maxBytes * 2 + count * 16_384 + 65_536;
    assert.ok(
      (await stat(join(directory, "media.json"))).size > priorReadBound,
    );
    const before = await readFile(join(directory, "media.json"));
    await assert.rejects(
      store.putMetadata({
        imageId: image.id,
        name: "Quota overflow",
        symbol: "OVER",
        description: "Synthetic",
        showName: true,
      }),
      { code: "LOCAL_MEDIA_QUOTA" },
    );
    assert.deepEqual(await readFile(join(directory, "media.json")), before);
    await store.close();
    const restored = await reopen();
    assert.deepEqual(restored.getImage(image.id).content, PNG);
    for (const value of expected)
      assert.deepEqual(restored.getMetadata(value.id), value);
    await assert.rejects(restored.deleteImage(image.id), {
      code: "LOCAL_MEDIA_IN_USE",
    });
    for (const value of expected) await restored.deleteMetadata(value.id);
    await restored.deleteImage(image.id);
    await restored.close();
    assert.throws(() => restored.getImage(image.id), {
      code: "LOCAL_MEDIA_CLOSED",
    });
    const empty = await reopen();
    assert.throws(() => empty.getImage(image.id), {
      code: "LOCAL_MEDIA_NOT_FOUND",
    });
  });
}

test("per-image JSON overhead and individual base64 padding survive restart", async (t) => {
  const count = 850;
  const limits = { maxBytes: count * 5, maxImages: count, maxMetadata: 1 };
  const { directory, store, reopen } = await setup(t, limits);
  const expected = [];
  for (let n = 0; n < count; n++) {
    // Synthetic signature-only JPEG, not a decoder-valid image. The existing
    // admission contract checks signatures, not decodability, and is unchanged.
    const bytes = Buffer.from([0xff, 0xd8, 0xff, n >> 8, n & 255]);
    expected.push({
      id: (await store.putImage(bytes, "image/jpeg")).id,
      bytes,
    });
  }
  assert.ok(
    (await stat(join(directory, "media.json"))).size >
      limits.maxBytes * 2 + limits.maxMetadata * 16_384 + 65_536,
  );
  await assert.rejects(store.putImage(PNG, "image/png"), {
    code: "LOCAL_MEDIA_QUOTA",
  });
  await store.close();
  const restored = await reopen();
  for (const value of expected)
    assert.deepEqual(restored.getImage(value.id).content, value.bytes);
});

test("serialized read admission stays bounded and releases ownership on rejection", async (t) => {
  const limits = { maxBytes: PNG.length, maxImages: 1, maxMetadata: 1 };
  const { directory, store, reopen } = await setup(t, limits);
  const image = await store.putImage(PNG, "image/png");
  await store.close();
  const original = await readFile(join(directory, "media.json"));
  // Even whitespace is bounded before JSON decoding; larger limits are not an
  // unbounded read fallback for the restart regression.
  await writeFile(join(directory, "media.json"), Buffer.alloc(100_000, 32));
  await assert.rejects(reopen(), /Invalid local media snapshot size\/type/);
  assert.equal((await readdir(directory)).includes(".media-owner"), false);
  await writeFile(join(directory, "media.json"), original);
  assert.deepEqual((await reopen()).getImage(image.id).content, PNG);
});

test("quota arithmetic rejects unrepresentable aggregate bounds and keeps accepted limits fixed", async (t) => {
  const directory = await mkdtemp(join(tmpdir(), "local-media-quota-bound-"));
  t.after(() => rm(directory, { recursive: true, force: true }));
  for (const limits of [
    { maxMetadata: Number.MAX_SAFE_INTEGER },
    { maxBytes: Number.MAX_SAFE_INTEGER, maxImages: Number.MAX_SAFE_INTEGER },
  ]) {
    await assert.rejects(
      LocalMediaStore.open(directory, limits).then((store) => store.close()),
      /serialized snapshot bound is not a safe integer/,
    );
    assert.equal((await readdir(directory)).includes(".media-owner"), false);
  }
  const input = { maxBytes: PNG.length, maxImages: 1, maxMetadata: 1 };
  const store = await LocalMediaStore.open(directory, input);
  try {
    input.maxMetadata = 200;
    assert.equal(store.limits.maxMetadata, 1);
    assert.equal(Object.isFrozen(store.limits), true);
    assert.throws(
      () => Object.assign(store.limits, { maxMetadata: 200 }),
      TypeError,
    );
    assert.equal(store.limits.maxMetadata, 1);
  } finally {
    await store.close();
  }
});
