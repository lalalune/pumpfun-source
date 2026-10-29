import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { verify } from "../scripts/original-home-layout-choice.mjs";
import {
  createHomeLayoutCookie,
  createCookieAdapter,
  createHomeLayoutDefinition,
  createLayoutPreviews,
  createChoiceRenderer,
  createSettingsField,
} from "../reconstruction/home-layout-choice/client.mjs";
const frontend = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const React = frontend("react"),
  runtime = frontend("react/jsx-runtime"),
  { c: useMemoCache } = frontend("react/compiler-runtime"),
  { renderToString } = frontend("react-dom/server");
const labels = {
  "web.home.layout_grid": "Grid",
  "web.home.layout_table": "Table",
  "web.home.feed_layout_a11y": "Feed layout",
  "web.settings.feed.layout_description": "Synthetic translated description",
};
const translateKey = (_t, key) => labels[key] ?? key;
const caps = {
  ...runtime,
  useMemoCache,
  useTranslation: () => ({ t: (key) => key }),
  translateKey,
  markString: (value) => value,
  classNames: (...args) => args.filter(Boolean).join(" "),
};
function storage(
  initial = "",
  { protocol = "https:", fail = false, log = [] } = {},
) {
  let value = initial;
  const document = {};
  Object.defineProperty(document, "cookie", {
    get() {
      log.push(["read"]);
      return value;
    },
    set(next) {
      log.push(["write", next]);
      if (fail) throw Error("synthetic cookie denied");
      value = next;
    },
  });
  return {
    ...createHomeLayoutCookie({ document, location: { protocol } }),
    value: () => value,
  };
}
function components({ value = "table", mounted = true, calls = [] } = {}) {
  const previews = createLayoutPreviews(caps),
    choice = createChoiceRenderer({ ...caps, previews });
  const fields = createSettingsField({
    ...caps,
    previews,
    choice,
    useHydrated: () => mounted,
    settings: {
      useSetting: (id) => (calls.push(["get", id]), value),
      useSetter: (id) => (
        calls.push(["setter", id]),
        (next) => calls.push(["set", next])
      ),
    },
    Row: ({ settingId, title, description, control, children }) =>
      React.createElement(
        "section",
        { "data-setting-id": settingId },
        React.createElement("h2", null, title),
        description && React.createElement("p", null, description),
        control,
        children,
      ),
    Switch: () => React.createElement("output", { "data-port": "switch" }),
    NumberInput: (props) =>
      React.createElement("output", {
        "data-port": "number",
        "data-value": String(props.value),
        "data-disabled": String(props.isDisabled),
      }),
    customControls: {
      sample: () => React.createElement("output", { "data-port": "custom" }),
    },
  });
  return { previews, choice, fields };
}
function definition(layout = storage()) {
  return createHomeLayoutDefinition({
    layout,
    cookieAdapter: createCookieAdapter,
  });
}

test("canonical source gate binds complete dispatcher/choice and selected layout-cookie contexts", async () => {
  const c = await verify();
  assert.equal(c.selectedIndexEntries.length, 6);
  assert.deepEqual(c.selectedPreviewKeys, ["layout-grid", "layout-table"]);
  assert.ok(c.retained.length >= 20);
  assert.match(c.credit, /1839/);
  assert.equal(c.callerWitnesses.length, 4);
});
test("layout enum/default and exact coercion preserve the table fallback", () => {
  const c = createHomeLayoutCookie({});
  assert.equal(c.key, "home_feed_layout");
  assert.deepEqual(c.layouts, { GRID: "grid", TABLE: "table" });
  for (const x of [null, undefined, "GRID", 1, {}, ""])
    assert.equal(c.coerce(x), "table");
  assert.equal(c.coerce("grid"), "grid");
  assert.equal(c.read(), null);
  assert.equal(c.readServer(""), "table");
  assert.doesNotThrow(() => c.write("grid"));
});
test("synthetic reader uses first matching cookie, preserves invalid-first and URI errors", () => {
  assert.equal(
    storage("other=x; home_feed_layout=grid; home_feed_layout=table").read(),
    "grid",
  );
  assert.equal(
    storage("home_feed_layout=invalid; home_feed_layout=grid").read(),
    null,
  );
  assert.equal(storage("home_feed_layout=gr%69d").read(), "grid");
  assert.equal(storage("home_feed_layout=grid=extra").read(), null);
  assert.throws(() => storage("home_feed_layout=%E0%A4").read(), URIError);
});
test("header parser normalizes first matching value independently of document", () => {
  const c = createHomeLayoutCookie({});
  assert.equal(c.readServer("other=x; home_feed_layout=grid"), "grid");
  assert.equal(
    c.readServer("home_feed_layout=invalid; home_feed_layout=grid"),
    "table",
  );
  assert.throws(() => c.readServer("home_feed_layout=%"), URIError);
});
test("cookie writer preserves one-year path/samesite and protocol-sensitive secure attributes", () => {
  for (const protocol of ["https:", "http:"]) {
    const c = storage("", { protocol });
    c.write("grid");
    assert.equal(
      c.value(),
      "home_feed_layout=grid; path=/; max-age=31536000; samesite=lax" +
        (protocol === "https:" ? "; secure" : ""),
    );
  }
  const c = storage();
  c.write("uncoerced");
  assert.match(c.value(), /^home_feed_layout=uncoerced;/);
});
test("actual cookie adapter nullish read and optional header context are preserved", () => {
  const c = createCookieAdapter({
    read: () => null,
    write: () => {},
    readServer: (x) => x,
  });
  assert.equal(c.read(), undefined);
  assert.equal(
    c.readServer({ cookieHeader: "synthetic header" }),
    "synthetic header",
  );
  assert.equal(
    createCookieAdapter({ read: () => false, write: () => {} }).read(),
    false,
  );
  assert.equal(
    createCookieAdapter({ read: () => 0, write: () => {} }).readServer,
    undefined,
  );
});
test("adapter writes before notifying, deduplicates Set listeners and unsubscribes by identity", () => {
  const log = [],
    c = createCookieAdapter({
      read: () => undefined,
      write: (value) => log.push(["write", value]),
    });
  const fn = () => log.push(["notify"]);
  const stop1 = c.subscribe(fn),
    stop2 = c.subscribe(fn);
  c.write("grid");
  assert.deepEqual(log, [["write", "grid"], ["notify"]]);
  stop1();
  c.write("table");
  stop2();
  assert.deepEqual(log, [["write", "grid"], ["notify"], ["write", "table"]]);
});
test("writer errors propagate before notification; callback errors preserve original Set iteration", () => {
  let notifications = 0;
  const denied = createCookieAdapter({
    read: () => undefined,
    write: () => {
      throw Error("synthetic denied");
    },
  });
  denied.subscribe(() => notifications++);
  assert.throws(() => denied.write("grid"), /synthetic denied/);
  assert.equal(notifications, 0);
  const c = createCookieAdapter({ read: () => undefined, write: () => {} });
  c.subscribe(() => {
    throw Error("synthetic listener");
  });
  c.subscribe(() => notifications++);
  assert.throws(() => c.write("grid"), /synthetic listener/);
  assert.equal(notifications, 0);
});
test("actual descriptor binds two preview choices and strict-string coercion to cookie adapter", () => {
  const log = [],
    d = definition(storage("", { log }));
  assert.equal(d.id, "feed.homeLayout");
  assert.equal(d.default, "table");
  assert.equal(d.control.kind, "pills");
  assert.deepEqual(
    d.control.options.map((x) => [x.value, x.preview]),
    [
      ["grid", "layout-grid"],
      ["table", "layout-table"],
    ],
  );
  assert.equal(d.coerce(1), "table");
  assert.equal(d.coerce("grid"), "grid");
  d.adapter.write(d.coerce("grid"));
  assert.match(log.at(-1)[1], /^home_feed_layout=grid;/);
});
test("actual React SSR field renders selected table and both complete pure SVG projections", () => {
  const d = definition(),
    { fields } = components();
  const text = renderToString(React.createElement(fields, { definition: d }));
  assert.match(text, /role="radiogroup" aria-label="Feed layout"/);
  assert.equal((text.match(/role="radio"/g) || []).length, 2);
  assert.equal((text.match(/aria-checked="true"/g) || []).length, 1);
  assert.equal((text.match(/viewBox="0 0 120 64"/g) || []).length, 2);
  assert.match(text, /Synthetic translated description/);
  assert.match(text, /data-setting-id="feed.homeLayout"/);
});
test("Object.is radio selection retains NaN and signed-zero semantics in plain branch", () => {
  const { choice } = components();
  const options = [
    { value: NaN, rawLabel: "NaN" },
    { value: 0, rawLabel: "zero" },
    { value: -0, rawLabel: "minus" },
  ];
  for (const value of [NaN, -0]) {
    const text = renderToString(
      React.createElement(choice.Choice, {
        options,
        value,
        onChange: () => {},
        label: "synthetic choices",
      }),
    );
    assert.equal((text.match(/aria-checked="true"/g) || []).length, 1);
  }
});
test("plain and preview layout/disabled branches retain source compact-label decisions", () => {
  const { choice } = components();
  assert.equal(choice.isCompact(["a", "b", "c", "d"]), true);
  assert.equal(choice.isCompact(["a".repeat(27)]), false);
  assert.equal(choice.isCompact(["a", "b", "c", "d", "e"]), false);
  const d = definition();
  let text = renderToString(
    React.createElement(choice.Choice, {
      options: d.control.options,
      value: "grid",
      label: "Layout",
      onChange: () => {},
      isDisabled: true,
    }),
  );
  assert.equal((text.match(/disabled=""/g) || []).length, 2);
  text = renderToString(
    React.createElement(choice.Choice, {
      options: [{ value: "x", rawLabel: "x".repeat(27) }],
      value: "x",
      label: "Long",
      onChange: () => {},
    }),
  );
  assert.match(text, /flex-wrap/);
});
test("complete generic dispatcher retains early hook order and external control boundaries", () => {
  const calls = [],
    { fields } = components({ calls, mounted: false });
  const d = definition();
  let text = renderToString(
    React.createElement(fields, {
      definition: { ...d, control: { kind: "hidden" } },
    }),
  );
  assert.equal(text, "");
  assert.deepEqual(calls.slice(0, 2), [
    ["get", "feed.homeLayout"],
    ["setter", "feed.homeLayout"],
  ]);
  for (const [kind, port] of [
    ["switch", "switch"],
    ["number", "number"],
  ]) {
    text = renderToString(
      React.createElement(fields, {
        definition: { ...d, firstPaintSensitive: true, control: { kind } },
      }),
    );
    assert.match(text, new RegExp('data-port="' + port + '"'));
    if (kind === "number") assert.match(text, /data-disabled="true"/);
  }
  text = renderToString(
    React.createElement(fields, {
      definition: { ...d, control: { kind: "custom", component: "sample" } },
    }),
  );
  assert.match(text, /data-port="custom"/);
  text = renderToString(
    React.createElement(fields, {
      definition: { ...d, control: { kind: "custom", component: "missing" } },
    }),
  );
  assert.equal(text, "");
});
