import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { verify } from "../scripts/original-settings-section-content.mjs";
import { createSettingsSectionContent } from "../reconstruction/settings-section-content/client.mjs";
const require = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  React = require("react"),
  jsx = require("react/jsx-runtime"),
  { c: useMemoCache } = require("react/compiler-runtime"),
  { renderToString } = require("react-dom/server");
const item = (id, kind = "custom") => ({
  id,
  control: { kind, component: "synthetic-readonly" },
});
function fixture({ definitions = [], hidden = new Set(), reader } = {}) {
  const calls = [],
    fields = [],
    frames = [],
    close = () => {};
  const Content = createSettingsSectionContent({
    ...jsx,
    useMemoCache,
    useTranslation: () => ({ t: (key) => "Synthetic:" + key }),
    translateKey: (t, key) => t(key),
    useHiddenSettingIds: () => hidden,
    definitionsForSection:
      reader ??
      ((section) => {
        calls.push(["read", section]);
        return definitions;
      }),
    Section: (props) => {
      frames.push(props);
      return jsx.jsxs("section", {
        "data-frame-label": props.label ?? "unlabelled",
        children: [
          props.label ? jsx.jsx("h2", { children: props.label }) : null,
          props.description
            ? jsx.jsx("p", { children: props.description })
            : null,
          props.children,
        ],
      });
    },
    Field: (props) => {
      fields.push(props);
      return jsx.jsx("p", {
        "data-field": props.definition.id,
        "data-compact": props.compact,
        children: props.definition.id,
      });
    },
    AccountHeader: () => {
      calls.push(["account"]);
      return jsx.jsx("p", {
        "data-port": "account",
        children: "External readonly account header",
      });
    },
    NotificationSettingsSections: () => {
      calls.push(["notifications"]);
      return jsx.jsx("p", {
        "data-port": "notifications",
        children: "External readonly notifications",
      });
    },
    PrivacyFooter: (props) => {
      calls.push(["privacy", props]);
      return jsx.jsx("p", {
        "data-port": "privacy",
        children: "External readonly privacy footer",
      });
    },
  });
  return {
    fields,
    frames,
    calls,
    close,
    html(section) {
      return renderToString(
        jsx.jsx(Content, { section, onRequestClose: close }),
      );
    },
  };
}
test("complete original grouping/forwarders/renderer and section-keyed actualcaller are bound", async () => {
  const c = await verify();
  assert.equal(c.retained.length, 5);
  assert.equal(c.witnesses.length, 10);
  assert.match(c.credit, /1911/);
  assert.match(c.credit, /1920/);
});
test("ordinary fallbackgroup preserves registryidentity/order, excludes hiddenkind and hiddenID before output", () => {
  const defs = [
      item("feed.second"),
      item("feed.hiddenKind", "hidden"),
      item("feed.hiddenID"),
      item("feed.first"),
    ],
    f = fixture({ definitions: defs, hidden: new Set(["feed.hiddenID"]) });
  const h = f.html("feed");
  assert.match(h, /data-testid="settings-section-feed"/);
  assert.deepEqual(
    f.fields.map((p) => p.definition.id),
    ["feed.second", "feed.first"],
  );
  assert.equal(f.fields[0].definition, defs[0]);
  assert.equal(f.frames.length, 1);
  assert.equal(f.frames[0].label, undefined);
  assert.equal(f.frames[0].description, undefined);
  assert.doesNotMatch(h, /hiddenKind|hiddenID/);
});
test("inerttrade groupingmetadata takes firstmatches thenleftovers, preserving registryorder within groups", () => {
  const ids = [
      "unmatched.synthetic",
      "trading.paymentAsset.synthetic",
      "trading.quickSell.synthetic",
      "trading.presets",
      "trading.quickBuy.synthetic",
    ],
    f = fixture({ definitions: ids.map((id) => item(id)) });
  f.html("trading");
  assert.deepEqual(
    f.fields.map((p) => p.definition.id),
    [
      "trading.presets",
      "trading.quickSell.synthetic",
      "trading.quickBuy.synthetic",
      "trading.paymentAsset.synthetic",
      "unmatched.synthetic",
    ],
  );
  assert.deepEqual(
    f.frames.map((p) => p.label),
    [
      "Synthetic:web.trade.execution",
      "Synthetic:web.trade.quick_buy",
      "Synthetic:coin_details.chart.settings.denomination",
      undefined,
    ],
  );
  assert.ok(f.fields.every((p) => !("value" in p) && !("onChange" in p)));
});
test("inertchart groupingmetadata placesnonmarkers first and passescompact only to markerbucket", () => {
  const f = fixture({
    definitions: [
      item("chart.markers.second"),
      item("chart.axis.synthetic"),
      item("chart.markers.first"),
    ],
  });
  f.html("chart");
  assert.deepEqual(
    f.fields.map((p) => p.definition.id),
    ["chart.axis.synthetic", "chart.markers.second", "chart.markers.first"],
  );
  assert.deepEqual(
    f.fields.map((p) => p.compact),
    [undefined, true, true],
  );
  assert.equal(
    f.frames[1].description,
    "Synthetic:web.settings.chart.bubbles_description",
  );
});
test("empty andunknownordinarysections keep originalemptycontainer without inventedstatus or footer", () => {
  for (const section of ["feed", "privacy", "unknown"]) {
    const f = fixture();
    const h = f.html(section);
    assert.match(
      h,
      new RegExp('data-testid="settings-section-' + section + '"'),
    );
    assert.doesNotMatch(h, /<section|role="status"|data-port/);
    assert.equal(f.frames.length, 0);
  }
});
test("privacyfooter isonlylastnonemptygroup and receives exact callerclosecallback", () => {
  const f = fixture({ definitions: [item("privacy.synthetic")] });
  f.html("privacy");
  assert.equal(f.frames.length, 1);
  assert.equal(f.calls.filter((x) => x[0] === "privacy").length, 1);
  assert.equal(f.calls.find((x) => x[0] === "privacy")[1].onOpen, f.close);
});
test("accountandnotification specialbranches delegateonlyreadonlyports and retain originalempty/earlyreturn shape", () => {
  const a = fixture({ definitions: [item("account.synthetic")] });
  const html = a.html("account");
  assert.match(html, /data-port="account"/);
  assert.equal(a.frames.length, 1);
  assert.equal(a.frames[0].label, "Synthetic:web.settings.account.profile");
  assert.deepEqual(
    a.fields.map((p) => p.definition.id),
    ["account.synthetic"],
  );
  const empty = fixture();
  empty.html("account");
  assert.deepEqual(empty.calls, [["read", "account"], ["account"]]);
  const n = fixture({ definitions: [item("notifications.synthetic")] });
  const out = n.html("notifications");
  assert.match(out, /data-port="notifications"/);
  assert.doesNotMatch(
    out,
    /settings-section-notifications|data-field|<section/,
  );
  assert.equal(n.fields.length, 0);
  assert.equal(n.frames.length, 0);
  assert.deepEqual(n.calls, [["read", "notifications"], ["notifications"]]);
});
test("supplieddefinitionreader errorsremainobservable without inventing a fallback/errorboundary", () => {
  const failure = Error("SYNTHETIC metadata reader failed");
  const f = fixture({
    reader() {
      throw failure;
    },
  });
  assert.throws(
    () => f.html("feed"),
    (error) => error === failure,
  );
});
