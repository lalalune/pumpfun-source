import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import {
  parseMentions,
  mentionProfileHref,
  planMentionText,
} from "../reconstruction/mention-text/model.mjs";
import { recoverMentionText } from "../scripts/original-mention-text.mjs";
import { openCorpus, sha256 } from "../scripts/original-contracts/source.mjs";
const root = fileURLToPath(new URL("..", import.meta.url));
const id = "12345678-1234-1234-1234-123456789abc";
const token = (username, userId = id) => `@[${username}](${userId})`;
const segments = (content) =>
  planMentionText(content).lines.flatMap((line) => line.segments);
const artifact = await recoverMentionText(root);

test("source binds actual174251.f→314012.m/profile formatter and all three default-mode consumer variants", () => {
  assert.equal(artifact.entry.module, 174251);
  assert.equal(artifact.entry.export, "f");
  assert.equal(artifact.entry.displayName, "MentionText");
  assert.equal(artifact.implementedSurface.withinLink, false);
  assert.equal(artifact.implementedSurface.density, "comfortable");
  assert.equal(artifact.consumers.length, 3);
  assert.ok(artifact.consumers.every((x) => x.module === 386028));
  assert.equal(
    new Set(artifact.consumers.map((x) => x.factory.sha256)).size,
    3,
  );
});

test("contract and every original UTF16/UTF8 fragment and maintained-file hash reproduce", async () => {
  assert.equal(
    await fs.readFile(
      path.join(root, "reconstruction/mention-text/contract.json"),
      "utf8",
    ),
    JSON.stringify(artifact, null, 2) + "\n",
  );
  const corpus = await openCorpus(root);
  for (const fragment of artifact.fragments) {
    const source = await corpus.capture(fragment.source);
    assert.equal(source.text.slice(...fragment.utf16), fragment.text);
    assert.equal(
      sha256(source.bytes.subarray(...fragment.utf8)),
      fragment.sha256,
    );
  }
  for (const file of artifact.implementation)
    assert.equal(
      sha256(await fs.readFile(path.join(root, file.path))),
      file.sha256,
    );
});

test("tampered original mention source fails before reconstruction", async (t) => {
  const temporary = await fs.mkdtemp(
    path.join(os.tmpdir(), "mention-text-source-"),
  );
  t.after(() => fs.rm(temporary, { recursive: true, force: true }));
  for (const name of [
    "evidence/web/manifest.json",
    "recovered/modules.json",
    artifact.entry.factory.source,
  ]) {
    const destination = path.join(temporary, name);
    await fs.mkdir(path.dirname(destination), { recursive: true });
    await fs.copyFile(path.join(root, name), destination);
  }
  const source = path.join(temporary, artifact.entry.factory.source);
  const bytes = await fs.readFile(source);
  bytes[100] ^= 1;
  await fs.writeFile(source, bytes);
  await assert.rejects(
    recoverMentionText(temporary),
    /capture authentication failed/,
  );
});

test("plain fast path and empty input preserve exact strings without turning ordinary URLs or@names into links", () => {
  for (const text of [
    "",
    "plain\nline",
    "@alice https://example.org/status/9",
    "https://x.com/alice",
    "<b>not HTML</b>",
  ]) {
    const plan = planMentionText(text);
    if (text.includes("/status/"))
      assert.deepEqual(plan.lines[0].segments, [{ kind: "text", text }]);
    else assert.deepEqual(plan, { plain: text, lines: [] });
  }
});

test("mention parser preserves text/order/duplicates and ASCII case without resolving profiles", () => {
  const content = `Hi ${token("Alice")}!${token("Alice")} tail`;
  assert.deepEqual(parseMentions(content), [
    { kind: "text", text: "Hi " },
    { kind: "mention", username: "Alice", userId: id },
    { kind: "text", text: "!" },
    { kind: "mention", username: "Alice", userId: id },
    { kind: "text", text: " tail" },
  ]);
  assert.equal(
    mentionProfileHref(id.toUpperCase()),
    `/profile/${id.toUpperCase()}`,
  );
  assert.equal(mentionProfileHref(""), null);
});

test("exact username and ID boundaries retain the source's loose36-character hex/hyphen rule", () => {
  for (const name of ["a", "123456789012345", "Name_123"])
    assert.equal(parseMentions(token(name))[0].kind, "mention");
  for (const name of ["", "1234567890123456", "café", "a-b", "a b"])
    assert.deepEqual(parseMentions(token(name)), [
      { kind: "text", text: token(name) },
    ]);
  assert.equal(parseMentions(token("a", "-".repeat(36)))[0].kind, "mention");
  for (const userId of [id.slice(1), id + "0", "g".repeat(36), "wallet-user"])
    assert.deepEqual(parseMentions(token("a", userId)), [
      { kind: "text", text: token("a", userId) },
    ]);
});

test("malformed serialized text remains literal and mention-looking prefixes/suffixes are preserved", () => {
  for (const text of ["@[a]", `@[a](${id}`, `@[a](${id} )`, `@[a]( ${id})`])
    assert.deepEqual(parseMentions(text), [{ kind: "text", text }]);
  assert.deepEqual(parseMentions(`x${token("a")}y`), [
    { kind: "text", text: "x" },
    { kind: "mention", username: "a", userId: id },
    { kind: "text", text: "y" },
  ]);
});

test("tweet candidates preserve exact URL, digit-prefix ID, username and trailing punctuation as separate text", () => {
  const url = "https://x.com/Alice/status/12345?ref=local";
  assert.deepEqual(segments(`${url}?!`), [
    { kind: "tweet", url, id: "12345", username: "Alice" },
    { kind: "text", text: "?!" },
  ]);
  const prefix = "http://mobile.twitter.com:8080/alice/status/12suffix";
  assert.deepEqual(segments(prefix), [
    { kind: "tweet", url: prefix, id: "12", username: "alice" },
  ]);
});

test("hostname/path qualification rejects lookalikes/multilevel subdomains/uppercaseSTATUS and never recognizes nonHTTP candidates", () => {
  for (const url of [
    "https://evilx.com/a/status/1",
    "https://x.com.evil.test/a/status/1",
    "https://a.b.x.com/a/status/1",
    "https://x.com/a/STATUS/1",
    "https://x.com/a/status/no",
    "ftp://x.com/a/status/1",
    "javascript://x.com/a/status/1",
  ])
    assert.equal(
      segments(url).some((s) => s.kind === "tweet"),
      false,
      url,
    );
});

test("multiple valid and invalid URLs keep intervening raw text and regex state cannot leak between renders", () => {
  const text =
    "https://else.test/a/status/1 then https://x.com/a/status/2, after https://twitter.com/b/status/3.";
  const expected = [
    { kind: "text", text: "https://else.test/a/status/1 then " },
    { kind: "tweet", url: "https://x.com/a/status/2", id: "2", username: "a" },
    { kind: "text", text: ", after " },
    {
      kind: "tweet",
      url: "https://twitter.com/b/status/3",
      id: "3",
      username: "b",
    },
    { kind: "text", text: "." },
  ];
  for (let i = 0; i < 4; i++) assert.deepEqual(segments(text), expected);
});

test("URL parentheses and encoded usernames retain the source candidate/path behavior", () => {
  const url = "https://x.com/alice%20bob/status/123(suffix)";
  assert.deepEqual(segments(url), [
    { kind: "tweet", url, id: "123", username: "alice%20bob" },
  ]);
});

test("mention parsing happens before tweet splitting and does not reinterpret mention contents as another token", () => {
  const content = `${token("a")} https://x.com/b/status/2`;
  assert.deepEqual(segments(content), [
    { kind: "mention", username: "a", userId: id },
    { kind: "text", text: " " },
    { kind: "tweet", username: "b", id: "2", url: "https://x.com/b/status/2" },
  ]);
});

test("greentext wraps onlyASCIIspace/tab-prefixed > lines and preserves all LF/empty/CR boundaries", () => {
  const plan = planMentionText(
    `normal\n\t> ${token("a")}\r\n\n\u00a0> plain\n`,
  );
  assert.equal(plan.plain, null);
  assert.deepEqual(
    plan.lines.map((l) => l.greentext),
    [false, true, false, false, false],
  );
  assert.deepEqual(
    plan.lines.map((l) => l.lineBreakAfter),
    [true, true, true, true, false],
  );
  assert.equal(plan.lines[1].segments.at(-1).text, "\r");
  assert.deepEqual(plan.lines[2].segments, []);
  assert.deepEqual(plan.lines[4].segments, []);
});

test("invalid input is not silently coerced and literal markup remains ordinary text forReact escaping", () => {
  assert.throws(() => planMentionText(null), TypeError);
  const text =
    '<script>window.bad=true</script><img src="https://evil.test/pixel">';
  assert.equal(planMentionText(text).plain, text);
});
