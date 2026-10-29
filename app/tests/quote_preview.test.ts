import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { quotePreviewPlan } from "../reconstruction/quote-preview/model.mjs";
import { recoverQuotePreview } from "../scripts/original-quote-preview.mjs";
import { openCorpus, sha256 } from "../scripts/original-contracts/source.mjs";
import {
  validateLocalFeed,
  FeedDataError,
} from "../packages/frontend/src/components/feed/feed-data.ts";
const root = fileURLToPath(new URL("..", import.meta.url));
const artifact = await recoverQuotePreview(root);
const user = {
  address: "11111111111111111111111111111111",
  userId: "alice",
  username: "Alice",
};
const post = (overrides: Record<string, unknown> = {}) => ({
  postId: "root",
  authorId: "alice",
  kind: "root",
  content: "target",
  mediaUrl: null,
  createdAt: "2024-01-01T00:00:00Z",
  parentPostId: null,
  rootPostId: null,
  quotedPostId: null,
  repostedPostId: null,
  likeCount: 0,
  replyCount: 0,
  repostCount: 0,
  quoteCount: 0,
  deleted: false,
  hidden: false,
  ...overrides,
});
const quote = (overrides: Record<string, unknown> = {}) =>
  post({
    postId: "quote",
    kind: "quote",
    content: "comment",
    quotedPostId: "root",
    ...overrides,
  });

test("registered386028.f and all physical variants bind actual174251.f, notN or390767.f", () => {
  assert.equal(artifact.entry.export, "f");
  assert.equal(artifact.entry.variants.length, 3);
  assert.equal(
    new Set(artifact.entry.variants.map((x) => x.factory.sha256)).size,
    3,
  );
  assert.equal(artifact.dependencies.mentionText.entry.module, 174251);
  assert.equal(artifact.dependencies.mentionText.entry.export, "f");
  assert.deepEqual(
    artifact.consumers.map((x) => x.module),
    [349919, 910976, 910976, 910976],
  );
  assert.equal(artifact.implementedSurface.dense, false);
  assert.equal(
    artifact.translation.originalEnglishCopy,
    "unknown in retained inputs",
  );
});

test("artifact, every original range, and all mounted implementation hashes reproduce", async () => {
  assert.equal(
    await fs.readFile(
      path.join(root, "reconstruction/quote-preview/contract.json"),
      "utf8",
    ),
    JSON.stringify(artifact, null, 2) + "\n",
  );
  const corpus = await openCorpus(root);
  for (const fragment of artifact.fragments) {
    const capture = await corpus.capture(fragment.source);
    assert.equal(capture.text.slice(...fragment.utf16), fragment.text);
    assert.equal(
      sha256(capture.bytes.subarray(...fragment.utf8)),
      fragment.sha256,
    );
  }
  for (const file of artifact.implementation)
    assert.equal(
      sha256(await fs.readFile(path.join(root, file.path))),
      file.sha256,
    );
});

test("a tampered original source fails authentication before adapter reconstruction", async (t) => {
  const temporary = await fs.mkdtemp(path.join(os.tmpdir(), "quote-preview-"));
  t.after(() => fs.rm(temporary, { recursive: true, force: true }));
  const source = artifact.entry.variants[0].factory.source;
  for (const file of [
    "evidence/web/manifest.json",
    "recovered/modules.json",
    source,
  ]) {
    const destination = path.join(temporary, file);
    await fs.mkdir(path.dirname(destination), { recursive: true });
    await fs.copyFile(path.join(root, file), destination);
  }
  const bytes = await fs.readFile(path.join(temporary, source));
  bytes[100] ^= 1;
  await fs.writeFile(path.join(temporary, source), bytes);
  await assert.rejects(
    recoverQuotePreview(temporary),
    /capture authentication failed/,
  );
});

test("source nullish author fallback preserves empty-name suppression and whitespace", () => {
  assert.deepEqual(
    quotePreviewPlan({ authorName: "", authorAddress: "1234567890", text: "" }),
    { kind: "quote", author: null, text: null },
  );
  assert.deepEqual(
    quotePreviewPlan({
      authorName: "  ",
      authorAddress: "1234567890",
      text: " hi ",
    }),
    { kind: "quote", author: "  ", text: " hi " },
  );
  assert.equal(
    quotePreviewPlan({ authorName: null, authorAddress: "123456789" }).author,
    "123456789",
  );
  assert.equal(
    quotePreviewPlan({ authorAddress: "1234567890" }).author,
    "1234…7890",
  );
  assert.equal(
    quotePreviewPlan({ authorAddress: "0x1234567890" }).author,
    "0x12…7890",
  );
});

test("deleted plan hides author/text and exposes only the known key; local copy is not an original translation", () => {
  assert.deepEqual(
    quotePreviewPlan({ deleted: true, authorName: "secret", text: "secret" }),
    { kind: "unavailable", translationKey: "profile.reposts.deleted_post" },
  );
  assert.deepEqual(quotePreviewPlan({ deleted: false }), {
    kind: "quote",
    author: null,
    text: null,
  });
  assert.equal(
    quotePreviewPlan({
      text: "<img src=x>\n@[Alice](------------------------------------)",
    }).text,
    "<img src=x>\n@[Alice](------------------------------------)",
  );
});

test("opt-in join resolves forward references without changing default root projection or inputs", () => {
  const input = [quote(), post()],
    before = structuredClone(input);
  const defaults = validateLocalFeed(input, [user]);
  const expanded = validateLocalFeed(input, [user], { includeQuotes: true });
  assert.deepEqual(
    expanded.posts.filter((p) => !p.quotePreview),
    defaults.posts,
  );
  assert.deepEqual(expanded.posts.find((p) => p.id === "quote")?.quotePreview, {
    deleted: false,
    authorName: "Alice",
    authorAddress: user.address,
    text: "target",
  });
  assert.deepEqual(input, before);
  assert.equal(defaults.excluded.nonRoot, 1);
  assert.equal(expanded.excluded.nonRoot, 0);
});

test("hidden, deleted, missing and null local targets withhold all target data", () => {
  for (const target of [
    post({ hidden: true }),
    post({ deleted: true }),
    null,
  ]) {
    const data = validateLocalFeed(
      [quote(), ...(target ? [target] : [])],
      [user],
      { includeQuotes: true },
    );
    assert.deepEqual(data.posts[0]?.quotePreview, { deleted: true });
  }
  assert.deepEqual(
    validateLocalFeed([quote({ quotedPostId: null })], [user], {
      includeQuotes: true,
    }).posts[0].quotePreview,
    { deleted: true },
  );
});

test("unresolved target authors never become fabricated preview names or wallet addresses", () => {
  const data = validateLocalFeed(
    [quote(), post({ authorId: "not-a-wallet" })],
    [user],
    { includeQuotes: true },
  );
  assert.deepEqual(data.posts.find((p) => p.id === "quote")?.quotePreview, {
    deleted: false,
    text: "target",
  });
  const walletless = validateLocalFeed(
    [quote(), post()],
    [{ ...user, address: "", username: null }],
    { includeQuotes: true },
  );
  assert.deepEqual(
    walletless.posts.find((p) => p.id === "quote")?.quotePreview,
    { deleted: false, text: "target" },
  );
});

test("flat target projection does not recursively hydrate cycles or introduce media/network URLs", () => {
  const data = validateLocalFeed(
    [
      quote({
        quotedPostId: "quote",
        mediaUrl: "https://example.invalid/no-fetch.png",
      }),
    ],
    [user],
    { includeQuotes: true },
  );
  assert.deepEqual(data.posts[0].quotePreview, {
    deleted: false,
    authorName: "Alice",
    authorAddress: user.address,
    text: "comment",
  });
  assert.doesNotMatch(
    JSON.stringify(data),
    /https:|quotedPostId|quoteTargetId/,
  );
});

test("reposts and reply-shaped quote rows remain excluded; malformed admitted quote references fail closed", () => {
  const data = validateLocalFeed(
    [
      post({ postId: "repost", kind: "repost", repostedPostId: "root" }),
      quote({ postId: "reply-shaped", parentPostId: "root" }),
      post(),
    ],
    [user],
    { includeQuotes: true },
  );
  assert.deepEqual(
    data.posts.map((p) => p.id),
    ["root"],
  );
  assert.equal(data.excluded.nonRoot, 1);
  assert.equal(data.excluded.replies, 1);
  assert.deepEqual(
    validateLocalFeed([quote({ quotedPostId: 4 })], [user]).posts,
    [],
  );
  assert.throws(
    () =>
      validateLocalFeed([], [], { includeQuotes: "yes" as unknown as boolean }),
    FeedDataError,
  );
  for (const quotedPostId of [false, 4, {}, "", "bad\u0001"])
    assert.throws(
      () =>
        validateLocalFeed([quote({ quotedPostId })], [user], {
          includeQuotes: true,
        }),
      FeedDataError,
    );
  assert.throws(
    () => validateLocalFeed([post(), post()], [user], { includeQuotes: true }),
    /repeats a post identity/,
  );
});

test("checked-in immutable dataset gains only its three quotes, with unchanged root records and recorded counts", async () => {
  const posts = JSON.parse(
    await fs.readFile(
      path.join(root, "packages/backend/src/posts-seed.json"),
      "utf8",
    ),
  );
  const users = JSON.parse(
    await fs.readFile(
      path.join(root, "packages/backend/src/users-seed.json"),
      "utf8",
    ),
  );
  const defaults = validateLocalFeed(posts, users),
    expanded = validateLocalFeed(posts, users, { includeQuotes: true });
  assert.equal(defaults.posts.length, 3);
  assert.equal(expanded.posts.length, 6);
  assert.deepEqual(
    expanded.posts.filter((p) => !p.quotePreview),
    defaults.posts,
  );
  assert.equal(expanded.posts.filter((p) => p.quotePreview).length, 3);
  assert.deepEqual(expanded.excluded, {
    replies: 5,
    deleted: 2,
    hidden: 1,
    nonRoot: 1,
  });
  assert.ok(
    expanded.posts
      .filter((p) => p.quotePreview)
      .every((p) => p.quotePreview?.text === "First post on synthetic pump!"),
  );
});
