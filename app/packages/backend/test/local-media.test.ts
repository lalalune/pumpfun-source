import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import {
  mkdtemp,
  readFile,
  rm,
  writeFile,
  mkdir,
  symlink,
  readdir,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test, { type TestContext } from "node:test";
import Fastify from "fastify";
import { buildApp } from "../src/app.js";
import { registerLocalMediaRoutes } from "../src/local-media-routes.js";
import {
  LOCAL_MEDIA_PREFIX as P,
  LocalMediaStore,
  MAX_IMAGE_BYTES,
  type LocalMediaLimits,
} from "../src/local-media-store.js";

// Synthetic 1x1 PNG test image; no user upload or captured production media.
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aK1cAAAAASUVORK5CYII=",
  "base64",
);
const TOKEN = "synthetic-test-only-local-capability-123456789";
const AUTH = { authorization: `Bearer ${TOKEN}` };
const pngId = createHash("sha256").update(PNG).digest("hex");
const DRAFT = {
  imageId: pngId,
  name: "Synthetic example",
  symbol: "TEST",
  description: "Local test only.",
  showName: true,
};

async function setup(
  t: TestContext,
  limits: LocalMediaLimits = {},
) {
  const directory = await mkdtemp(join(tmpdir(), "local-media-test-"));
  const store = await LocalMediaStore.open(directory, limits);
  const app = Fastify();
  registerLocalMediaRoutes(app, { store, token: TOKEN });
  await app.ready();
  t.after(async () => {
    await app.close();
    await store.close();
    await rm(directory, { recursive: true, force: true });
  });
  return { directory, store, app };
}

test("local media is absent from the default application", async (t) => {
  const app = buildApp();
  t.after(() => app.close());
  const result = await app.inject({
    method: "POST",
    url: `${P}/metadata`,
    headers: AUTH,
    payload: DRAFT,
  });
  assert.equal(result.statusCode, 501);
  assert.equal(result.json().error, "COMPATIBILITY_NOT_IMPLEMENTED");
});

test("synthetic image -> metadata -> restart -> readback -> dependency-safe deletion", async (t) => {
  const { app, store, directory } = await setup(t);
  const uploaded = await app.inject({
    method: "POST",
    url: `${P}/images`,
    headers: { ...AUTH, "content-type": "image/png" },
    payload: PNG,
  });
  assert.equal(uploaded.statusCode, 201);
  assert.equal(uploaded.json().id, pngId);
  assert.equal(uploaded.json().mode, "local-only");
  assert.equal(uploaded.json().bytes, PNG.length);
  const media = await app.inject({
    url: uploaded.json().contentUri,
    headers: AUTH,
  });
  assert.equal(media.statusCode, 200);
  assert.deepEqual(media.rawPayload, PNG);
  assert.equal(media.headers["content-disposition"], "attachment");
  assert.equal(media.headers["x-content-type-options"], "nosniff");
  assert.equal(media.headers["cache-control"], "no-store");
  const saved = await app.inject({
    method: "POST",
    url: `${P}/metadata`,
    headers: AUTH,
    payload: {
      ...DRAFT,
      website: "https://example.com",
      twitter: "https://x.com/test",
    },
  });
  assert.equal(saved.statusCode, 201);
  const result = saved.json();
  assert.equal(
    result.metadata.createdOn,
    "urn:pump-reconstruction:local-media",
  );
  assert.equal(result.metadata.image, uploaded.json().contentUri);
  const document = await app.inject({ url: result.metadataUri, headers: AUTH });
  assert.deepEqual(document.json(), result.metadata);
  assert.equal(
    createHash("sha256").update(JSON.stringify(document.json())).digest("hex"),
    result.id,
  );
  const conflict = await app.inject({
    method: "DELETE",
    url: `${P}/images/${pngId}`,
    headers: AUTH,
  });
  assert.equal(conflict.statusCode, 409);
  assert.equal(conflict.json().code, "LOCAL_MEDIA_IN_USE");
  await app.close();
  await store.close();
  const restarted = await LocalMediaStore.open(directory);
  assert.deepEqual(restarted.getImage(pngId).content, PNG);
  assert.deepEqual(restarted.getMetadata(result.id).metadata, result.metadata);
  await restarted.deleteMetadata(result.id);
  await restarted.deleteImage(pngId);
  await restarted.close();
  const empty = await LocalMediaStore.open(directory);
  assert.throws(() => empty.getImage(pngId), { code: "LOCAL_MEDIA_NOT_FOUND" });
  assert.throws(() => empty.getMetadata(result.id), {
    code: "LOCAL_MEDIA_NOT_FOUND",
  });
  await empty.close();
  assert.throws(() => store.getImage(pngId), { code: "LOCAL_MEDIA_CLOSED" });
});

test("retries deduplicate, concurrent writes do not lose metadata, returned objects cannot mutate storage", async (t) => {
  const { store, app } = await setup(t);
  const uploads = await Promise.all(
    Array.from({ length: 4 }, () => store.putImage(PNG, "image/png")),
  );
  assert.equal(uploads.filter((item) => item.created).length, 1);
  const result = await app.inject({
    method: "POST",
    url: `${P}/images`,
    headers: { ...AUTH, "content-type": "image/png" },
    payload: PNG,
  });
  assert.equal(result.statusCode, 200);
  assert.equal(result.json().created, false);
  const saved = await Promise.all(
    Array.from({ length: 5 }, (_, index) =>
      store.putMetadata({ ...DRAFT, name: `Example ${index}` }),
    ),
  );
  for (const item of saved)
    assert.equal(store.getMetadata(item.id).metadata.name, item.metadata.name);
  const repeated = await store.putMetadata({ ...DRAFT, name: "Example 0" });
  assert.equal(repeated.created, false);
  repeated.metadata.name = "mutated";
  assert.equal(store.getMetadata(repeated.id).metadata.name, "Example 0");
  const image = store.getImage(pngId);
  image.content.fill(0);
  assert.deepEqual(store.getImage(pngId).content, PNG);
});

test("capability auth is mandatory even for reads; wrong/malformed capability and browser origins fail closed", async (t) => {
  const { app, store } = await setup(t);
  await store.putImage(PNG, "image/png");
  for (const headers of [
    {},
    { authorization: "test-format-only-key" },
    { authorization: `Bearer ${"a".repeat(300)}` },
    { authorization: `Bearer ${TOKEN}x` },
  ]) {
    const response = await app.inject({ url: `${P}/images/${pngId}`, headers });
    assert.equal(response.statusCode, 401);
  }
  for (const headers of [
    { ...AUTH, origin: "https://evil.example" },
    { ...AUTH, origin: "null" },
    { ...AUTH, "sec-fetch-site": "cross-site" },
  ]) {
    assert.equal(
      (await app.inject({ url: `${P}/images/${pngId}`, headers })).statusCode,
      403,
    );
  }
  const foreign = await app.inject({
    url: `${P}/images/${pngId}`,
    headers: { ...AUTH, "x-forwarded-for": "127.0.0.1" },
    remoteAddress: "203.0.113.1",
  });
  assert.equal(foreign.statusCode, 403);
  assert.equal(foreign.json().code, "LOCAL_MEDIA_LOOPBACK_REQUIRED");
  assert.equal(
    (
      await app.inject({
        url: `${P}/images/${pngId}`,
        headers: AUTH,
        remoteAddress: "::1",
      })
    ).statusCode,
    200,
  );
});

test("explicit operator capability has no insecure default", async (t) => {
  const { store } = await setup(t);
  for (const token of [
    "",
    "short",
    "space is not allowed even when it is a long token",
  ]) {
    const app = Fastify();
    t.after(() => app.close());
    assert.throws(() => registerLocalMediaRoutes(app, { store, token }));
  }
});

test("image body limit, MIME/signature checks and media isolation reject unsafe requests", async (t) => {
  const { app, directory } = await setup(t);
  for (const [type, body, status] of [
    ["image/png", Buffer.alloc(0), 413],
    ["image/jpeg", PNG, 415],
    ["image/png", Buffer.from("<script>not an image</script>"), 415],
    ["image/svg+xml", Buffer.from("<svg/>"), 415],
    ["application/json", Buffer.from("{}"), 415],
    ["image/png", Buffer.alloc(MAX_IMAGE_BYTES + 1), 413],
  ] as const) {
    const response = await app.inject({
      method: "POST",
      url: `${P}/images`,
      headers: { ...AUTH, "content-type": type },
      payload: body,
    });
    assert.equal(
      response.statusCode,
      status,
      `${type} ${body.length}: ${response.body}`,
    );
  }
  assert.deepEqual(await readdir(directory), [".media-owner"]);
});

test("four supported signatures and the exact image-byte boundary are local validation rules", async (t) => {
  const { store } = await setup(t);
  // Synthetic headers deliberately demonstrate signature checks, not full decoding.
  const gif = Buffer.from("47494638396101000100", "hex");
  const jpeg = Buffer.from("ffd8ffe0", "hex");
  const webp = Buffer.from("52494646080000005745425056503820", "hex");
  for (const [mime, bytes] of [
    ["image/gif", gif],
    ["image/jpeg", jpeg],
    ["image/webp", webp],
  ] as const) {
    const image = await store.putImage(bytes, mime);
    assert.equal(image.mime, mime);
    assert.deepEqual(store.getImage(image.id).content, bytes);
  }
  const boundary = Buffer.alloc(MAX_IMAGE_BYTES);
  PNG.copy(boundary);
  const image = await store.putImage(boundary, "image/png");
  assert.equal(image.bytes, MAX_IMAGE_BYTES);
  const metadata = await store.putMetadata({
    ...DRAFT,
    imageId: image.id,
    name: "x".repeat(32),
    symbol: "y".repeat(10),
    description: "z".repeat(2000),
    showName: false,
  });
  assert.equal(metadata.metadata.showName, false);
});

for (const [label, mime, bytes, offset] of [
  ["PNG IHDR", "image/png", PNG, 12],
  ["GIF header", "image/gif", Buffer.from("47494638396101000100", "hex"), 0],
  ["WebP RIFF", "image/webp", Buffer.from("52494646080000005745425056503820", "hex"), 0],
  ["WebP WEBP", "image/webp", Buffer.from("52494646080000005745425056503820", "hex"), 8],
] as const) {
  test(`high-bit ${label} aliases are rejected without publishing an image`, async (t) => {
    const { app, store, directory } = await setup(t);
    const valid = await store.putImage(bytes, mime);
    const before = await readFile(join(directory, "media.json"));
    const altered = Buffer.from(bytes);
    altered[offset] |= 0x80;
    const response = await app.inject({
      method: "POST",
      url: `${P}/images`,
      headers: { ...AUTH, "content-type": mime },
      payload: altered,
    });
    assert.equal(response.statusCode, 415);
    assert.equal(response.json().code, "LOCAL_MEDIA_IMAGE_TYPE");
    assert.deepEqual(await readFile(join(directory, "media.json")), before);
    assert.deepEqual(store.getImage(valid.id).content, bytes);
  });
}

test("metadata validates references, fields, text bounds, links and JSON byte cap", async (t) => {
  const { app, store } = await setup(t);
  const missing = await app.inject({
    method: "POST",
    url: `${P}/metadata`,
    headers: AUTH,
    payload: DRAFT,
  });
  assert.equal(missing.statusCode, 404);
  await store.putImage(PNG, "image/png");
  for (const draft of [
    null,
    [],
    {},
    { ...DRAFT, name: " " },
    { ...DRAFT, name: "n".repeat(33) },
    { ...DRAFT, symbol: "s".repeat(11) },
    { ...DRAFT, description: "d".repeat(2001) },
    { ...DRAFT, showName: "true" },
    { ...DRAFT, name: "\ud800" },
    { ...DRAFT, imageId: "../outside" },
    { ...DRAFT, image: "https://evil.example/x" },
    { ...DRAFT, createdOn: "https://pump.fun" },
    { ...DRAFT, website: "http://example.com" },
    { ...DRAFT, website: "https://user:pass@example.com" },
    { ...DRAFT, twitter: "https://evil.example/x" },
    { ...DRAFT, telegram: "https://t.me/" },
    { ...DRAFT, website: "https://example.com/" + "a".repeat(2048) },
  ]) {
    const response = await app.inject({
      method: "POST",
      url: `${P}/metadata`,
      headers: { ...AUTH, "content-type": "application/json" },
      payload: JSON.stringify(draft),
    });
    assert.equal(response.statusCode, 400, response.body);
  }
  assert.equal(
    (
      await app.inject({
        method: "POST",
        url: `${P}/metadata`,
        headers: AUTH,
        payload: { ...DRAFT, description: "x".repeat(20000) },
      })
    ).statusCode,
    413,
  );
  assert.equal(
    (
      await app.inject({
        method: "POST",
        url: `${P}/metadata`,
        headers: { ...AUTH, "content-type": "application/json" },
        payload: "{",
      })
    ).statusCode,
    400,
  );
});

test("identifiers cannot traverse paths and missing objects/deletes are explicit", async (t) => {
  const { app } = await setup(t);
  for (const path of [
    `${P}/images/nope`,
    `${P}/images/%2e%2e%2fsecret/content`,
    `${P}/metadata/${"a".repeat(64)}`,
  ]) {
    const response = await app.inject({ url: path, headers: AUTH });
    assert.ok([400, 404].includes(response.statusCode));
  }
  for (const kind of ["images", "metadata"]) {
    assert.equal(
      (
        await app.inject({
          method: "DELETE",
          url: `${P}/${kind}/${"a".repeat(64)}`,
          headers: AUTH,
        })
      ).statusCode,
      404,
    );
  }
});

test("byte/object quotas reject atomically and dedup does not consume quota", async (t) => {
  const { store, directory } = await setup(t, {
    maxBytes: PNG.length,
    maxImages: 1,
    maxMetadata: 1,
  });
  await store.putImage(PNG, "image/png");
  await store.putImage(PNG, "image/png");
  const before = await readFile(join(directory, "media.json"));
  const altered = Buffer.from(PNG);
  altered[altered.length - 1] ^= 1;
  await assert.rejects(store.putImage(altered, "image/png"), {
    code: "LOCAL_MEDIA_QUOTA",
  });
  assert.deepEqual(await readFile(join(directory, "media.json")), before);
  const first = await store.putMetadata(DRAFT);
  await store.putMetadata(DRAFT);
  await assert.rejects(store.putMetadata({ ...DRAFT, name: "Second" }), {
    code: "LOCAL_MEDIA_QUOTA",
  });
  await store.deleteMetadata(first.id);
  assert.equal(
    (await store.putMetadata({ ...DRAFT, name: "Second" })).created,
    true,
  );
});

test("failed snapshot publication leaves prior in-memory state and cleans the temporary file", async (t) => {
  const { store, directory } = await setup(t);
  await mkdir(join(directory, "media.json"));
  await assert.rejects(store.putImage(PNG, "image/png"));
  assert.throws(() => store.getImage(pngId), { code: "LOCAL_MEDIA_NOT_FOUND" });
  assert.deepEqual((await readdir(directory)).sort(), [
    ".media-owner",
    "media.json",
  ]);
  await rm(join(directory, "media.json"), { recursive: true });
  assert.equal((await store.putImage(PNG, "image/png")).created, true);
});

test("exclusive single-owner persistence releases on close and waits for queued writes", async (t) => {
  const { store, directory } = await setup(t);
  await assert.rejects(LocalMediaStore.open(directory), { code: "EEXIST" });
  const pending = store.putImage(PNG, "image/png");
  await store.close();
  await pending;
  await store.close(); // idempotent close must not delete a new owner's lock.
  const second = await LocalMediaStore.open(directory);
  assert.deepEqual(second.getImage(pngId).content, PNG);
  await store.close();
  await assert.rejects(LocalMediaStore.open(directory), { code: "EEXIST" });
  await second.close();
  await assert.rejects(store.putMetadata(DRAFT), {
    code: "LOCAL_MEDIA_CLOSED",
  });
});

test("a preexisting/stale owner file is never automatically removed or stolen", async (t) => {
  const { directory, store } = await setup(t);
  await store.close();
  const stale = "pid=synthetic-stale-owner\n";
  await writeFile(join(directory, ".media-owner"), stale);
  await assert.rejects(LocalMediaStore.open(directory), { code: "EEXIST" });
  assert.equal(await readFile(join(directory, ".media-owner"), "utf8"), stale);
});

test("restart rejects corrupt images, metadata hashes, broken references, duplicate IDs and unversioned data", async (t) => {
  const { store, directory } = await setup(t);
  await store.putImage(PNG, "image/png");
  await store.putMetadata(DRAFT);
  const valid = JSON.parse(
    await readFile(join(directory, "media.json"), "utf8"),
  );
  await store.close();
  const variants = [
    (x: any) => {
      x.images[0].data = Buffer.from("altered").toString("base64");
    },
    (x: any) => {
      x.images[0].id = "a".repeat(64);
    },
    (x: any) => {
      x.images[0].data += "\n";
    },
    (x: any) => {
      x.metadata[0].value.name = "tampered";
    },
    (x: any) => {
      x.metadata[0].value.image = "https://example.com/x";
    },
    (x: any) => {
      x.metadata[0].value.createdOn = "https://pump.fun";
    },
    (x: any) => {
      x.images = [];
    },
    (x: any) => {
      x.images.push(x.images[0]);
    },
    (x: any) => {
      x.metadata.push(x.metadata[0]);
    },
    (x: any) => {
      x.version = 2;
    },
    (x: any) => {
      x.unexpected = true;
    },
  ];
  for (const mutate of variants) {
    const altered = structuredClone(valid);
    mutate(altered);
    await writeFile(join(directory, "media.json"), JSON.stringify(altered));
    await assert.rejects(LocalMediaStore.open(directory));
  }
  await writeFile(join(directory, "media.json"), JSON.stringify(valid));
  const reopened = await LocalMediaStore.open(directory);
  assert.deepEqual(reopened.getImage(pngId).content, PNG);
  await reopened.close();
});

test("startup rejects symlinked storage/snapshots and does not read their contents", async (t) => {
  const { directory, store } = await setup(t);
  await store.close();
  const outside = await mkdtemp(join(tmpdir(), "local-media-target-"));
  t.after(() => rm(outside, { recursive: true, force: true }));
  await writeFile(join(outside, "target"), "{}");
  try {
    await symlink(join(outside, "target"), join(directory, "media.json"));
  } catch (error) {
    if (process.platform === "win32" && (error as NodeJS.ErrnoException).code === "EPERM") {
      t.skip("Windows account cannot create file symlinks; requires Developer Mode or symlink privilege");
      return;
    }
    throw error;
  }
  await assert.rejects(LocalMediaStore.open(directory));
  const linked = join(directory, "linked");
  await symlink(outside, linked);
  await assert.rejects(LocalMediaStore.open(linked));
});

test("startup rejects a symlink to a valid snapshot, not only to invalid content", async (t) => {
  const { directory, store } = await setup(t);
  await store.close();
  const outside = await mkdtemp(join(tmpdir(), "local-media-valid-target-"));
  t.after(() => rm(outside, { recursive: true, force: true }));
  const source = await LocalMediaStore.open(outside);
  await source.putImage(PNG, "image/png");
  await source.close();
  try {
    await symlink(join(outside, "media.json"), join(directory, "media.json"));
  } catch (error) {
    if (process.platform === "win32" && (error as NodeJS.ErrnoException).code === "EPERM") {
      t.skip("Windows account cannot create file symlinks; requires Developer Mode or symlink privilege");
      return;
    }
    throw error;
  }
  await assert.rejects(LocalMediaStore.open(directory), /snapshot size\/type/);
  // The failed open releases ownership so a corrected directory can be reopened.
  await rm(join(directory, "media.json"));
  const reopened = await LocalMediaStore.open(directory);
  assert.throws(() => reopened.getImage(pngId), { code: "LOCAL_MEDIA_NOT_FOUND" });
  await reopened.close();
});

test("local routes leave unrelated parsers/routes alone and never call fetch", async (t) => {
  const { store } = await setup(t);
  const app = Fastify();
  t.after(() => app.close());
  registerLocalMediaRoutes(app, { store, token: TOKEN });
  app.post("/independent", async (request) => request.body);
  const original = globalThis.fetch;
  globalThis.fetch = async () => {
    throw new Error("Outbound fetch is forbidden.");
  };
  t.after(() => {
    globalThis.fetch = original;
  });
  assert.equal(
    (
      await app.inject({
        method: "POST",
        url: "/independent",
        payload: { ok: true },
      })
    ).statusCode,
    200,
  );
  assert.equal(
    (
      await app.inject({
        method: "POST",
        url: "/independent",
        headers: { "content-type": "image/png" },
        payload: PNG,
      })
    ).statusCode,
    415,
  );
  assert.equal(
    (
      await app.inject({
        method: "POST",
        url: `${P}/images`,
        headers: { ...AUTH, "content-type": "image/png" },
        payload: PNG,
      })
    ).statusCode,
    201,
  );
  assert.equal(
    (
      await app.inject({
        method: "POST",
        url: `${P}/metadata`,
        headers: AUTH,
        payload: DRAFT,
      })
    ).statusCode,
    201,
  );
});
