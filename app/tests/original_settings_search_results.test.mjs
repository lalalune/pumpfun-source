import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { verify } from "../scripts/original-settings-search-results.mjs";
import { createSettingsSearchResults } from "../reconstruction/settings-search-results/client.mjs";
const require = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const React = require("react"),
  jsx = require("react/jsx-runtime"),
  { c: useMemoCache } = require("react/compiler-runtime"),
  { renderToString } = require("react-dom/server");
const dictionary = {
  "section.feed": "Feed",
  "section.privacy": "Privacy",
  blue: "Blue Café",
  "blue.description": "Compact cards",
  warning: "Warnings",
  "warning.description": "Read links",
  other: "Other shared result",
  "web.settings.search_results": "Settings search results",
};
const translation = (key, options) =>
  key === "web.settings.search_empty"
    ? "No matches for " + options.query
    : (dictionary[key] ?? key);
const catalog = [
  { id: "feed", labelKey: "section.feed" },
  { id: "privacy", labelKey: "section.privacy" },
];
function fixtures() {
  return [
    {
      id: "privacy.warning",
      section: "privacy",
      labelKey: "warning",
      descriptionKey: "warning.description",
      searchTerms: ["shared"],
      control: { kind: "switch" },
    },
    {
      id: "feed.blueCard",
      section: "feed",
      labelKey: "blue",
      descriptionKey: "blue.description",
      searchTerms: ["shared", "motion"],
      control: { kind: "pills" },
    },
    {
      id: "feed.other",
      section: "feed",
      labelKey: "other",
      searchTerms: ["shared"],
      control: { kind: "switch" },
    },
  ];
}
function component({
  registry = fixtures(),
  sections = catalog,
  hidden = new Set(),
  translate = translation,
  seen = [],
} = {}) {
  return createSettingsSearchResults({
    ...jsx,
    useMemoCache,
    useTranslation: () => ({ t: translate }),
    translateKey: (t, key) => t(key),
    useHiddenSettingIds: () => hidden,
    registry,
    sections,
    Field: ({ definition }) => {
      seen.push(definition);
      return React.createElement(
        "article",
        { "data-setting-id": definition.id },
        translate(definition.labelKey),
      );
    },
    Section: ({ label, children }) =>
      React.createElement(
        "section",
        { "data-group": label },
        React.createElement("h2", null, label),
        children,
      ),
  });
}
function render(query, options = {}, visibleSections = ["feed", "privacy"]) {
  return renderToString(
    React.createElement(component(options), { query, visibleSections }),
  );
}
const ids = (text) =>
  [...text.matchAll(/data-setting-id="([^"]+)"/g)].map((x) => x[1]);

test("source gate binds complete results component, normalizer and keyed actual field bridge", async () => {
  const c = await verify();
  assert.equal(c.retained.length, 3);
  assert.equal(c.callerWitnesses.length, 8);
  assert.equal(
    c.factory.sha256,
    "dfcb487f79e63fa817cef92fd322e172c6d44fb2270bad175820a463b2e382ea",
  );
  assert.match(c.credit, /1885/);
  assert.match(c.credit, /1872/);
  assert.match(c.credit, /1839/);
});
test("actual token-AND search spans label, description, searchTerms, section label and identifier words", () => {
  for (const q of [
    "CAFÉ motion",
    "feed blueCard",
    "Blue compact",
    "  café\tCARDS  ",
  ])
    assert.deepEqual(ids(render(q)), ["feed.blueCard"]);
  assert.deepEqual(ids(render("privacy warning links")), ["privacy.warning"]);
  assert.deepEqual(ids(render("motion nonexistent")), []);
});
test("matching groups follow catalog order and each group preserves original registry order", () => {
  const html = render("shared");
  assert.deepEqual(ids(html), [
    "feed.blueCard",
    "feed.other",
    "privacy.warning",
  ]);
  assert.ok(
    html.indexOf('data-group="Feed"') < html.indexOf('data-group="Privacy"'),
  );
  assert.match(html, /role="region" aria-label="Settings search results"/);
});
test("visible sections and hidden-ID Set exclude definitions before metadata is inspected", () => {
  const bad = (id, section, control = { kind: "switch" }) => ({
    id,
    section,
    control,
    get labelKey() {
      throw Error("excluded metadata must not be read");
    },
  });
  const registry = [
    ...fixtures(),
    bad("feed.hidden", "feed"),
    bad("outside", "outside"),
    bad("feed.hiddenKind", "feed", { kind: "hidden" }),
  ];
  assert.deepEqual(
    ids(render("shared", { registry, hidden: new Set(["feed.hidden"]) })),
    ["feed.blueCard", "feed.other", "privacy.warning"],
  );
  assert.deepEqual(
    ids(
      render("shared", { registry, hidden: new Set(["feed.hidden"]) }, [
        "privacy",
      ]),
    ),
    ["privacy.warning"],
  );
});
test("empty and unmatched results use original status path with query interpolation", () => {
  for (const query of ["", "zz unmatched"]) {
    const html = render(query);
    assert.match(html, /role="status"/);
    assert.match(html, /No matches for /);
    assert.deepEqual(ids(html), []);
  }
  assert.match(render("<not&found>"), /&lt;not&amp;found&gt;/);
});
test("normalizer retains original case-before-NFKD quirk and literal-dotted behavior", () => {
  assert.deepEqual(ids(render("MOTION")), ["feed.blueCard"]);
  assert.deepEqual(ids(render("𝐌𝐎𝐓𝐈𝐎𝐍")), []);
  assert.deepEqual(ids(render("feed.blueCard")), []);
});
test("missing section catalog metadata does not invent a group or replace source region with empty status", () => {
  const registry = [
    {
      id: "unknown.item",
      section: "unknown",
      labelKey: "blue",
      control: { kind: "switch" },
    },
  ];
  const html = render("Blue", { registry }, ["unknown"]);
  assert.match(html, /role="region"/);
  assert.doesNotMatch(html, /role="status"/);
  assert.deepEqual(ids(html), []);
});
test("field bridge passes original descriptor identity without preference construction or mutation", () => {
  const registry = fixtures(),
    seen = [],
    before = JSON.stringify(registry);
  render("shared", { registry, seen });
  assert.equal(seen[0], registry[1]);
  assert.equal(seen[1], registry[2]);
  assert.equal(seen[2], registry[0]);
  assert.equal(JSON.stringify(registry), before);
  assert.ok(seen.every((item) => !("value" in item) && !("checked" in item)));
});
test("section-label fallback participates in filtering while supplied translation errors remain explicit", () => {
  const registry = [
    {
      id: "unlisted.item",
      section: "unlisted",
      labelKey: "blue",
      control: { kind: "switch" },
    },
  ];
  assert.match(render("unlisted", { registry }, ["unlisted"]), /role="region"/);
  assert.throws(
    () =>
      render("shared", {
        translate: () => {
          throw Error("synthetic translation failure");
        },
      }),
    /synthetic translation failure/,
  );
});
