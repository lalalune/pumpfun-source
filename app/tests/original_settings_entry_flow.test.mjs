import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { verify } from "../scripts/original-settings-entry-flow.mjs";
import { createSettingsEntryFlow } from "../reconstruction/settings-entry-flow/client.mjs";
const require = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  React = require("react"),
  { jsx } = require("react/jsx-runtime"),
  { c: useMemoCache } = require("react/compiler-runtime"),
  { renderToString } = require("react-dom/server");
function fixture({
  flag = true,
  section = "feed",
  setting = null,
  window: provided,
} = {}) {
  const calls = [],
    ids = ["feed", "privacy"],
    stringParser = {},
    enumParser = {},
    flagKey = {},
    patches = [],
    props = [];
  let href =
      "https://synthetic.invalid/?keep=one&keep=two&setting=old#fragment",
    state = { synthetic: true },
    loader;
  const window = provided ?? {
    location: {
      get href() {
        return href;
      },
    },
    history: {
      get state() {
        return state;
      },
      replaceState(s, title, url) {
        calls.push(["replace", s, title, String(url)]);
        state = s;
        href = String(url);
      },
    },
    dispatchEvent(event) {
      calls.push(["dispatch", event]);
      return true;
    },
    addEventListener() {
      throw Error("Effects must not run during SSR");
    },
  };
  const flow = createSettingsEntryFlow({
    window,
    URL,
    CustomEvent,
    jsx,
    useMemoCache,
    useEffect: React.useEffect,
    useFeatureFlag: (key) => {
      assert.equal(key, flagKey);
      return flag;
    },
    settingsFlag: flagKey,
    sectionIds: ids,
    parseAsStringEnum: (got) => {
      assert.equal(got, ids);
      calls.push(["enum", got]);
      return enumParser;
    },
    parseAsString: stringParser,
    useQueryStates: (schema, options) => {
      calls.push(["query", schema, options]);
      return [{ settings: section, setting }, (p) => patches.push(p)];
    },
    dynamic: (load, options) => {
      loader = load;
      calls.push(["dynamic", options]);
      return (p) => {
        props.push(p);
        return jsx("p", {
          children: p.section + ":" + String(p.focusSettingId),
        });
      };
    },
    loadModule: (id) => {
      calls.push(["load", id]);
      return Promise.resolve({ SettingsModal: () => null });
    },
  });
  return {
    flow,
    calls,
    patches,
    props,
    ids,
    stringParser,
    enumParser,
    loader,
    render: () => renderToString(jsx(flow.SettingsModalHost, {})),
    href: () => href,
    state: () => state,
  };
}
test("full original five retained regions, six physical factories and static namespace chain are authenticated", async () => {
  const c = await verify();
  assert.equal(c.retained.length, 5);
  assert.equal(c.factories.length, 6);
  assert.equal(c.witnesses.length, 11);
  assert.deepEqual(c.catalogIds, [
    "trading",
    "chart",
    "feed",
    "notifications",
    "account",
    "display",
    "privacy",
    "admin",
  ]);
  assert.match(c.capabilities.query, /atomic/);
});
test("single enum/string schema and exact dynamic SSR/module/load projection capabilities are used", async () => {
  const f = fixture();
  assert.equal(f.calls[0][0], "enum");
  assert.deepEqual(f.calls[1], [
    "dynamic",
    { loadableGenerated: { modules: [190147] }, ssr: false },
  ]);
  await f.loader();
  assert.deepEqual(f.calls.at(-1), ["load", 298590]);
  f.render();
  const q = f.calls.find((c) => c[0] === "query");
  assert.deepEqual(q[1], { settings: f.enumParser, setting: f.stringParser });
  assert.deepEqual(q[2], { history: "replace", clearOnDefault: true });
});
test("opener commits URL before dispatch and preserves native duplicate params/hash/history state/detail identity", () => {
  const f = fixture(),
    detail = { section: "feed", settingId: "feed.synthetic" };
  f.flow.openSettings(detail);
  const tail = f.calls.slice(-2);
  assert.equal(tail[0][0], "replace");
  assert.equal(tail[1][0], "dispatch");
  assert.equal(tail[1][1].type, "pump:open-settings");
  assert.equal(tail[1][1].detail, detail);
  const u = new URL(f.href());
  assert.deepEqual(u.searchParams.getAll("keep"), ["one", "two"]);
  assert.equal(u.hash, "#fragment");
  assert.equal(u.searchParams.get("setting"), "feed.synthetic");
  assert.equal(tail[0][1], f.state());
  assert.equal(tail[0][2], "");
});
test("opener truthy settingId deletes empty/undefined/null/zero while truthy strings set without new validation", () => {
  for (const value of ["", undefined, null, 0]) {
    const f = fixture();
    f.flow.openSettings({ section: "privacy", settingId: value });
    assert.equal(new URL(f.href()).searchParams.has("setting"), false);
  }
  const f = fixture();
  f.flow.openSettings({ section: "feed", settingId: "0" });
  assert.equal(new URL(f.href()).searchParams.get("setting"), "0");
});
test("history failure prevents dispatch, dispatch failure leaves preceding URL commit observable", () => {
  const failure = new Error("SYNTHETIC history denial"),
    events = [];
  const f = fixture({
    window: {
      location: { href: "https://synthetic.invalid/" },
      history: {
        state: null,
        replaceState() {
          throw failure;
        },
      },
      dispatchEvent: (e) => events.push(e),
    },
  });
  assert.throws(
    () => f.flow.openSettings({ section: "feed" }),
    (e) => e === failure,
  );
  assert.equal(events.length, 0);
  const w = {
      location: { href: "https://synthetic.invalid/" },
      history: {
        state: null,
        replaceState(s, t, url) {
          w.location.href = String(url);
        },
      },
      dispatchEvent() {
        throw failure;
      },
    },
    g = fixture({ window: w });
  assert.throws(
    () => g.flow.openSettings({ section: "privacy" }),
    (e) => e === failure,
  );
  assert.equal(
    new URL(w.location.href).searchParams.get("settings"),
    "privacy",
  );
});
test("SSR never accesses window effects and false flag or absent section returns null", () => {
  const forbidden = new Proxy(
    {},
    {
      get() {
        throw Error("SYNTHETIC forbidden browser read during SSR");
      },
    },
  );
  assert.equal(fixture({ flag: false, window: forbidden }).render(), "");
  assert.equal(fixture({ section: null, window: forbidden }).render(), "");
});
test("actual React SSR forwards source modal props; host nullish callbacks and close patch both keys atomically", () => {
  const f = fixture({ setting: "feed.synthetic" });
  assert.match(f.render(), /feed:feed.synthetic/);
  const p = f.props[0];
  assert.equal(p.section, "feed");
  assert.equal(p.focusSettingId, "feed.synthetic");
  p.onSectionChange("privacy", "");
  p.onSectionChange("feed", undefined);
  p.onClose();
  assert.deepEqual(f.patches, [
    { settings: "privacy", setting: "" },
    { settings: "feed", setting: null },
    { settings: null, setting: null },
  ]);
  assert.deepEqual(Object.keys(p).sort(), [
    "focusSettingId",
    "onClose",
    "onSectionChange",
    "section",
  ]);
});
