import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { verify } from "../scripts/original-settings-modal-owner.mjs";
import { createSettingsModalOwner } from "../reconstruction/settings-modal-owner/client.mjs";
const require = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  React = require("react"),
  runtime = require("react/jsx-runtime"),
  { c: useMemoCache } = require("react/compiler-runtime"),
  { renderToString } = require("react-dom/server");
const visible = [
  { id: "feed", labelKey: "synthetic.feed", tabLabelKey: "synthetic.feed.tab" },
  {
    id: "privacy",
    labelKey: "synthetic.privacy",
    tabLabelKey: "synthetic.privacy.tab",
  },
];
function fixture({
  sections = visible,
  ready = true,
  definitions = [{ id: "synthetic.feed", resettable: true }],
} = {}) {
  const calls = [],
    props = {},
    focus = [];
  const plain = (tag, record) => (p) => {
    if (record) props[record] = p;
    return runtime.jsx(tag, { children: p.children });
  };
  const Owner = createSettingsModalOwner({
    ...runtime,
    useMemoCache,
    useState: React.useState,
    useEffect: React.useEffect,
    useId: React.useId,
    useRef: React.useRef,
    useTranslation: () => {
      calls.push("translation");
      return { t: (key) => key };
    },
    translateKey: (t, k) => t(k),
    useVisibleSections: () => {
      calls.push("availability");
      return sections;
    },
    useSettingsResourceAttempt: () => {
      calls.push("resource");
      return ready;
    },
    useTransientSettingId: (id) => {
      calls.push("focus");
      focus.push(id);
      return id;
    },
    FocusContextProvider: (p) => {
      props.focus = p;
      return p.children;
    },
    definitionsForSection: (id) => {
      calls.push(["definitions", id]);
      return definitions;
    },
    SearchResults: (p) => {
      props.results = p;
      return runtime.jsx("p", { children: p.query });
    },
    SectionContent: (p) => {
      props.section = p;
      return runtime.jsx("p", { children: p.section });
    },
    Loading: () =>
      runtime.jsx("p", { "data-loading": true, children: "Synthetic loading" }),
    resetSection: (id) => calls.push(["reset", id]),
    DialogRoot: plain("div", "dialog"),
    DialogContent: plain("section", "content"),
    TabsRoot: plain("nav", "tabs"),
    TabsList: plain("div", "list"),
    TabsTrigger: (p) => runtime.jsx("button", { children: p.children }),
    Button: (p) =>
      runtime.jsx("button", { onClick: p.onClick, children: p.children }),
    CloseIcon: () => null,
    SearchIcon: () => null,
    ResetIcon: () => null,
    DeviceIcon: () => null,
  });
  return {
    calls,
    props,
    focus,
    render(p = {}) {
      return renderToString(
        runtime.jsx(Owner, {
          section: "feed",
          focusSettingId: "feed.synthetic",
          onSectionChange: (id) => calls.push(["select", id]),
          onClose: () => calls.push("close"),
          ...p,
        }),
      );
    },
  };
}
test("full owner exactly2AST substitutions and raw1920/context/child/reset call closure are authenticated", async () => {
  const c = await verify();
  assert.equal(c.retained.length, 2);
  assert.equal(c.owner.memoSlots, 100);
  assert.deepEqual(
    c.owner.transformations.map((x) => [x.binding, x.replacement]),
    [
      ["Y", "useVisibleSections()"],
      ["J", "useSettingsResourceAttempt()"],
    ],
  );
  assert.equal(c.witnesses.length, 10);
  assert.notEqual(c.owner.originalAstSha256, c.owner.adaptedAstSha256);
});
test("actual React SSR preserves unconditional hook boundary order and exact resource/focus/context/section signatures", () => {
  const f = fixture(),
    h = f.render();
  assert.deepEqual(f.calls.slice(0, 4), [
    "translation",
    "availability",
    "resource",
    "focus",
  ]);
  assert.deepEqual(f.focus, ["feed.synthetic"]);
  assert.equal(f.props.focus.value, "feed.synthetic");
  assert.deepEqual(Object.keys(f.props.focus).sort(), ["children", "value"]);
  assert.equal(f.props.section.section, "feed");
  assert.equal(typeof f.props.section.onRequestClose, "function");
  assert.equal(f.props.dialog.isOpen, true);
  assert.equal(f.props.tabs.value, "feed");
  assert.match(h, /web.settings.title/);
  assert.match(h, /data-testid="settings-search"/);
});
test("unavailable/denied requested section falls back without acquiring a permission/address or changing parent selection", () => {
  const f = fixture();
  f.render({ section: "account" });
  assert.equal(f.props.tabs.value, "feed");
  assert.equal(f.props.section.section, "feed");
  assert.equal(
    f.calls.some((x) => Array.isArray(x) && x[0] === "select"),
    false,
  );
});
test("empty metadata preserves original inert fallbackliteral without implementing its protected content", () => {
  const f = fixture({ sections: [], definitions: [] });
  f.render({ section: "unknown" });
  assert.equal(f.props.tabs.value, "trading");
  assert.equal(f.props.section.section, "trading");
  assert.equal(f.props.focus.value, "feed.synthetic");
});
test("resource false renders loading/busy while preserving original reset metadata policy; ready renders section", () => {
  const f = fixture({ ready: false });
  const h = f.render();
  assert.match(h, /aria-busy="true"/);
  assert.match(h, /data-loading="true"/);
  assert.equal(f.props.section, undefined);
  assert.match(h, /web.settings.reset_section/);
  const g = fixture();
  assert.doesNotMatch(g.render(), /aria-busy="true"/);
});
test("resettable strictfalse is preserved; notifications suppresses device note while explicit plain metadata remains readonly", () => {
  const f = fixture({ definitions: [{ id: "x", resettable: false }] });
  assert.doesNotMatch(f.render(), /web.settings.reset_section/);
  const g = fixture({
    sections: [
      {
        id: "notifications",
        labelKey: "synthetic.notifications",
        tabLabelKey: "synthetic.notifications.tab",
      },
    ],
    definitions: [],
  });
  const h = g.render({ section: "notifications" });
  assert.doesNotMatch(h, /web.settings.device_note/);
  assert.equal(g.props.section.section, "notifications");
});
test("dialog open-change callback only closes onfalsy; tab callback retains exact selection argument", () => {
  const f = fixture();
  f.render();
  f.props.dialog.onIsOpenChange(true);
  assert.equal(f.calls.includes("close"), false);
  f.props.dialog.onIsOpenChange(false);
  assert.equal(f.calls.at(-1), "close");
  f.props.tabs.onValueChange("privacy");
  assert.deepEqual(f.calls.at(-1), ["select", "privacy"]);
});
