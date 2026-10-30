import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { verify } from "../scripts/original-settings-focus-frames.mjs";
import { createSettingsFocusFrames } from "../reconstruction/settings-focus-frames/client.mjs";
const require = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  React = require("react"),
  jsx = require("react/jsx-runtime"),
  { c: useMemoCache } = require("react/compiler-runtime"),
  { renderToString } = require("react-dom/server");
function fixture() {
  return createSettingsFocusFrames({
    ...jsx,
    useMemoCache,
    createContext: React.createContext,
    use: React.use,
    useState: React.useState,
    useEffect: React.useEffect,
    useRef: React.useRef,
    classNames: (...args) => args.filter(Boolean).join(" "),
    window: {
      setTimeout() {
        throw Error("SSR must not start timers");
      },
      clearTimeout() {
        throw Error("SSR must not clear timers");
      },
    },
  });
}
test("complete grouped exports and actual Settings hook/provider/row/section consumers are source-bound", async () => {
  const c = await verify();
  assert.equal(c.retained.length, 7);
  assert.equal(c.witnesses.length, 9);
  assert.deepEqual(c.factory.ids, [379288, 165228]);
  assert.equal(
    c.factory.sha256,
    "ab377b76367b582ab93f114fe047043fdf3289275a00fc3e878ed31da36aad2c",
  );
  assert.match(c.credit, /1911/);
});
test("full row keeps title, description, note, control and children, escaping text without preference acquisition", () => {
  const { Row } = fixture();
  const h = renderToString(
    jsx.jsx(Row, {
      settingId: "feed.synthetic",
      title: "<unsafe&title>",
      description: "Description",
      note: "Readonly note",
      control: jsx.jsx("span", { children: "Readonly control slot" }),
      children: jsx.jsx("strong", { children: "Readonly child" }),
      dense: true,
      className: "host-marker",
    }),
  );
  assert.match(h, /data-setting-id="feed.synthetic"/);
  assert.doesNotMatch(h, /data-focused/);
  assert.match(h, /&lt;unsafe&amp;title&gt;/);
  for (const text of [
    "Description",
    "Readonly note",
    "Readonly control slot",
    "Readonly child",
    "py-2.5",
    "host-marker",
  ])
    assert.ok(h.includes(text));
});
test("complete focus provider highlights matching row during SSR without timer/scroll effects", () => {
  const { FocusProvider, Row } = fixture();
  const h = renderToString(
    jsx.jsx(FocusProvider, {
      settingId: "feed.target",
      children: [
        jsx.jsx(Row, { settingId: "feed.other", title: "Other" }, "other"),
        jsx.jsx(Row, { settingId: "feed.target", title: "Target" }, "target"),
      ],
    }),
  );
  assert.equal((h.match(/data-focused="true"/g) ?? []).length, 1);
  assert.match(h, /data-setting-id="feed.target" data-focused="true"/);
  assert.match(h, /py-3.5/);
});
test("falsey provider target and missing row ID do not invent focus; optional slots remain absent", () => {
  const { FocusProvider, Row } = fixture();
  for (const settingId of [undefined, null, ""]) {
    const h = renderToString(
      jsx.jsx(FocusProvider, {
        settingId,
        children: jsx.jsx(Row, { title: "Plain" }),
      }),
    );
    assert.doesNotMatch(h, /data-focused|data-setting-id|<p|mt-3|shrink-0/);
  }
});
test("full section renders header, description and row children using original optional branches", () => {
  const { Section, Row } = fixture();
  const h = renderToString(
    jsx.jsx(Section, {
      label: "Safe section",
      description: "Safe description",
      className: "host-section",
      "data-testid": "synthetic-section",
      children: jsx.jsx(Row, { settingId: "feed.one", title: "One" }),
    }),
  );
  assert.match(h, /<section data-testid="synthetic-section"/);
  assert.match(h, /<h3 class="pb-1[^\"]*pb-0/);
  assert.match(h, />Safe section<\/h3>/);
  assert.match(h, />Safe description<\/p>/);
  assert.match(h, /data-setting-id="feed.one"/);
  const blank = renderToString(jsx.jsx(Section, { children: "Read-only" }));
  assert.doesNotMatch(blank, /<h3|<p/);
  assert.match(blank, /divide-y divide-border-secondary/);
});
