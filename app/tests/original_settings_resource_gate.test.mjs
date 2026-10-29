import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { verify } from "../scripts/original-settings-resource-gate.mjs";
import { createSettingsResourceContent } from "../reconstruction/settings-resource-gate/client.mjs";
const require = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const React = require("react"),
  jsx = require("react/jsx-runtime"),
  { c: useMemoCache } = require("react/compiler-runtime"),
  { renderToString } = require("react-dom/server");
function fixture({
  exists = false,
  query = "",
  section = "feed",
  i18n,
  seen = [],
} = {}) {
  const provider = i18n ?? {
    language: "synthetic-unsupported",
    exists(key) {
      seen.push(["exists", key]);
      return exists;
    },
  };
  const close = () => {},
    focus = { id: "synthetic-focus" },
    visible = ["feed", "privacy"],
    ref = React.createRef();
  const content = createSettingsResourceContent({
    ...jsx,
    useMemoCache,
    useState: React.useState,
    useEffect: React.useEffect,
    useTranslation: () => ({ i18n: provider }),
    normalizeLocale() {
      throw Error("SSR must not normalize or acquire resources");
    },
    defaultLocale: "en",
    prefetchCatalog() {
      throw Error("SSR must not prefetch");
    },
    FocusProvider: ({ value, children }) => {
      seen.push(["focus", value]);
      return children;
    },
    SearchResults: (props) => {
      seen.push(["results", props]);
      return jsx.jsx("output", {
        "data-host-result": true,
        children: props.query,
      });
    },
    Section: (props) => {
      seen.push(["section", props]);
      return jsx.jsx("p", {
        "data-host-section": props.section,
        children: props.section,
      });
    },
  });
  return {
    content,
    seen,
    close,
    focus,
    visible,
    ref,
    html: () =>
      renderToString(
        jsx.jsx(content.SettingsResourceContent, {
          query,
          section,
          visibleSections: visible,
          focusValue: focus,
          onRequestClose: close,
          scrollRef: ref,
        }),
      ),
  };
}
test("source gate binds entire actual attempt hook, loading and content/scroll memo regions", async () => {
  const c = await verify();
  assert.equal(c.retained.length, 8);
  assert.equal(c.witnesses.length, 12);
  assert.match(c.credit, /1864/);
  assert.match(c.credit, /1898/);
  assert.equal(
    c.factory.sha256,
    "dfcb487f79e63fa817cef92fd322e172c6d44fb2270bad175820a463b2e382ea",
  );
});
test("missing sentinel renders original aria-hidden five rows and busy wrapper on SSR; no resource acquisition", () => {
  const f = fixture();
  const h = f.html();
  assert.match(h, /aria-busy="true"/);
  assert.match(h, /aria-hidden="true"/);
  assert.equal((h.match(/justify-between gap-6 py-4/g) ?? []).length, 5);
  assert.equal((h.match(/animate-pulse/g) ?? []).length, 15);
  assert.doesNotMatch(h, /role="(?:status|progressbar)"/);
  assert.deepEqual(f.seen, [["exists", "web.trade.max_slippage"]]);
});
test("complete Loading component is consumable separately without inventing a progress announcement", () => {
  const f = fixture();
  const h = renderToString(jsx.jsx(f.content.Loading, {}));
  assert.match(h, /aria-hidden="true"/);
  assert.doesNotMatch(h, /aria-busy|role=/);
  assert.equal((h.match(/rounded-full/g) ?? []).length, 5);
  assert.deepEqual(f.seen, []);
});
test("existing sentinel renders the exact trimmed-query results branch and keeps supplied section-list identity", () => {
  const f = fixture({ exists: true, query: "  Café motion  " });
  const h = f.html();
  assert.match(h, /data-host-result="true"/);
  assert.doesNotMatch(h, /aria-busy|aria-hidden/);
  const [_, props] = f.seen.find((x) => x[0] === "results");
  assert.equal(props.query, "Café motion");
  assert.equal(props.visibleSections, f.visible);
  assert.equal(
    f.seen.some((x) => x[0] === "section" || x[0] === "focus"),
    false,
  );
});
test("whitespace query uses actual focus-provider/section branch with unchanged callback and focus identity", () => {
  const f = fixture({ exists: true, query: " \t ", section: "privacy" });
  const h = f.html();
  assert.match(h, /data-host-section="privacy"/);
  assert.equal(f.seen.find((x) => x[0] === "focus")[1], f.focus);
  const props = f.seen.find((x) => x[0] === "section")[1];
  assert.equal(props.section, "privacy");
  assert.equal(props.onRequestClose, f.close);
  assert.equal(
    f.seen.some((x) => x[0] === "results"),
    false,
  );
});
test("SSR initializes only from the sentinel and surfaces supplied exists errors unchanged", () => {
  const failure = Error("SYNTHETIC exists failure");
  const f = fixture({
    i18n: {
      language: "en",
      exists() {
        throw failure;
      },
    },
  });
  assert.throws(
    () => f.html(),
    (error) => error === failure,
  );
});
