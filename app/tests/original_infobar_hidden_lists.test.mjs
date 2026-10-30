import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { verify } from "../scripts/original-infobar-hidden-lists.mjs";
import {
  createHiddenInfoBarValues,
  createHiddenInfoBarDefinitions,
  createHiddenInfoBarFields,
} from "../reconstruction/infobar-hidden-lists/client.mjs";
const require = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  React = require("react"),
  runtime = require("react/jsx-runtime"),
  { c: useMemoCache } = require("react/compiler-runtime"),
  { renderToString } = require("react-dom/server");
const values = createHiddenInfoBarValues();
function fixture({ tokens = {}, profiles = {}, throwWrite } = {}) {
  const writes = [],
    rows = [],
    buttons = [],
    formats = [];
  const translation = (key, options) =>
    ({
      "web.info_bar.hidden_tokens": "Hidden tokens",
      "web.info_bar.hidden_profiles": "Hidden profiles",
      "web.info_bar.no_hidden_tokens": "None hidden",
      "web.info_bar.hidden_positions_note": "Synthetic positions note",
      "web.info_bar.show_all_hidden": "Show all hidden",
    })[key] ??
    (options?.symbol
      ? "Unhide " + options.symbol
      : options?.name
        ? "Unhide " + options.name
        : key);
  const useSetting = (id) => [
    id.endsWith("hiddenTokens") ? tokens : profiles,
    (next) => {
      if (throwWrite) throw throwWrite;
      writes.push({ id, next });
    },
  ];
  const fields = createHiddenInfoBarFields({
    jsx: (type, props, key) => {
      if (type === "button") buttons.push(props);
      return runtime.jsx(type, props, key);
    },
    jsxs: (type, props, key) => {
      if (type === "button") buttons.push(props);
      return runtime.jsxs(type, props, key);
    },
    useMemoCache,
    useTranslation: () => ({ t: translation }),
    translateKey: (t, key) => t(key),
    useSetting,
    readSetting: (id) => {
      assert.equal(id, "feed.infoBar.hiddenProfiles");
      return profiles;
    },
    Row: (props) => {
      rows.push(props);
      return runtime.jsxs("section", {
        "data-setting-id": props.settingId,
        children: [
          runtime.jsx("h2", { children: props.title }),
          runtime.jsx("p", {
            "data-description": true,
            children: props.description,
          }),
          runtime.jsx("p", { "data-note": true, children: props.note }),
          props.control,
          props.children,
        ],
      });
    },
    Action: (props) => runtime.jsx("button", props),
    CloseIcon: (props) => runtime.jsx("span", props),
    formatProfileLabel: (props) => {
      formats.push(["profile", props]);
      return props.username ? "@" + props.username : "@synthetic-fallback";
    },
    truncateAddress: (address, left, right) => {
      formats.push(["truncate", address, left, right]);
      return "synthetic-abbreviation";
    },
    normalizeDisplayText: (label, kind) => {
      formats.push(["normalize", label, kind]);
      return label;
    },
    values,
  });
  return {
    writes,
    rows,
    buttons,
    formats,
    render(kind) {
      const id =
        "feed.infoBar.hidden" + (kind === "tokens" ? "Tokens" : "Profiles");
      return renderToString(
        runtime.jsx(
          kind === "tokens" ? fields.HiddenTokens : fields.HiddenProfiles,
          {
            definition: {
              id,
              labelKey:
                kind === "tokens"
                  ? "web.info_bar.hidden_tokens"
                  : "web.info_bar.hidden_profiles",
            },
          },
        ),
      );
    },
  };
}
test("source gate binds full fields/chips/sorts/coerce/actualdevice descriptors and caller boundaries", async () => {
  const c = await verify();
  assert.equal(c.retained.length, 14);
  assert.equal(c.factories.length, 4);
  assert.equal(c.witnesses.length, 10);
  assert.match(c.credit, /1839/);
  assert.match(c.credit, /1920/);
});
test("coerce preserves source validation/fallbacks and distinct token/profile canonical-key rules", () => {
  const tokens = values.coerceTokens({
    first: { mint: "0xAB", symbol: 7, hiddenAt: Infinity },
    last: { mint: "0xAb", symbol: "LAST", hiddenAt: 9 },
    spaces: { mint: "  0xAB  ", symbol: " ", hiddenAt: 2 },
    bad: { mint: "  " },
    missing: { address: "synthetic-profile" },
  });
  assert.deepEqual(Object.keys(tokens), ["0xab", "  0xAB  "]);
  assert.equal(tokens["0xab"].symbol, "LAST");
  assert.equal(tokens["  0xAB  "].mint, "  0xAB  ");
  assert.deepEqual(
    values.coerceProfiles({
      a: { address: " 0xAB ", username: 8, hiddenAt: NaN },
    }),
    { "0xab": { address: " 0xAB ", username: "", hiddenAt: 0 } },
  );
  assert.equal(values.tokenKey("0XAB"), "0XAB");
  assert.equal(values.profileKey(" 0xAB "), "0xab");
  assert.deepEqual(values.coerceTokens(null), {});
  assert.deepEqual(values.coerceProfiles("not-object"), {});
});
test("coerce retains newest200before canonical-key collapse and does not invent strictaccount validation", () => {
  const input = Object.fromEntries(
    Array.from({ length: 202 }, (_, i) => [
      i,
      { mint: "synthetic-" + i, symbol: "S" + i, hiddenAt: i },
    ]),
  );
  const result = values.coerceTokens(input);
  assert.equal(Object.keys(result).length, 200);
  assert.equal(result["synthetic-0"], undefined);
  assert.equal(result["synthetic-1"], undefined);
  assert.equal(result["synthetic-201"].hiddenAt, 201);
  assert.equal(
    values.coerceTokens({ x: { mint: "not-a-chain-address", hiddenAt: 0 } })[
      "not-a-chain-address"
    ].hiddenAt,
    0,
  );
});
test("complete descriptors bind coerce identities and suppliedbucket store/select/setField config", () => {
  const calls = [],
    state = {
      hiddenTokens: { seed: true },
      hiddenProfiles: { other: true },
      setField: (field, next) => calls.push([field, next]),
    };
  const ds = createHiddenInfoBarDefinitions({
    values,
    store: state,
    makeBucketAdapter: (config) => config,
  });
  assert.deepEqual(
    ds.map((d) => d.id),
    ["feed.infoBar.hiddenTokens", "feed.infoBar.hiddenProfiles"],
  );
  assert.equal(ds[0].coerce, values.coerceTokens);
  assert.equal(ds[1].coerce, values.coerceProfiles);
  for (const [index, key] of ["hiddenTokens", "hiddenProfiles"].entries()) {
    const d = ds[index];
    assert.equal(d.scope, "device");
    assert.equal(d.adapter.store(), state);
    assert.equal(d.adapter.select(state), state[key]);
    const next = { synthetic: true };
    d.adapter.write({ next, state });
    assert.equal(calls.at(-1)[0], key);
    assert.equal(calls.at(-1)[1], next);
  }
});
test("complete token field sortsnewestfirst, formats fallback, andkeeps empty-cross-list description quirk", () => {
  const f = fixture({
    tokens: values.coerceTokens({
      a: { mint: "0xAA", symbol: "A", hiddenAt: 1 },
      b: { mint: "synthetic-b", symbol: "", hiddenAt: 3 },
    }),
  });
  const h = f.render("tokens");
  assert.ok(h.indexOf("synthetic-abbreviation") < h.indexOf(">A</span>"));
  assert.match(h, /<ul aria-label="Hidden tokens"/);
  assert.ok(
    f.formats.some(
      (x) =>
        x[0] === "truncate" &&
        x[1] === "synthetic-b" &&
        x[2] === 4 &&
        x[3] === 4,
    ),
  );
  assert.ok(
    f.formats.some((x) => x[0] === "normalize" && x[2] === "coin-symbol"),
  );
  const empty = fixture();
  empty.render("tokens");
  assert.equal(empty.rows[0].description, "None hidden");
  const cross = fixture({
    profiles: {
      synthetic: { address: "synthetic-profile", username: "P", hiddenAt: 1 },
    },
  });
  cross.render("tokens");
  assert.equal(cross.rows[0].description, undefined);
  assert.equal(cross.rows[0].control, undefined);
  assert.equal(cross.rows[0].children, null);
});
test("complete profile field supplies username-or-null labelport, sourcecategory and row identity", () => {
  const f = fixture({
    profiles: {
      a: { address: "synthetic-one", username: "name", hiddenAt: 1 },
      b: { address: "synthetic-two", username: "", hiddenAt: 3 },
    },
  });
  const h = f.render("profiles");
  assert.ok(h.indexOf("@synthetic-fallback") < h.indexOf("@name"));
  assert.deepEqual(
    f.formats.filter((x) => x[0] === "profile").map((x) => x[1]),
    [
      { address: "synthetic-two", username: null },
      { address: "synthetic-one", username: "name" },
    ],
  );
  assert.ok(
    f.formats.some((x) => x[0] === "normalize" && x[2] === "user-name"),
  );
  assert.equal(f.rows[0].settingId, "feed.infoBar.hiddenProfiles");
});
test("unhide passes exactlatest-valuefunctional update and clear passesemptyobject; suppliedwrite errors stayobservable", () => {
  for (const kind of ["tokens", "profiles"]) {
    const data =
      kind === "tokens"
        ? { tokens: { "0xaa": { mint: "0xAA", symbol: "A", hiddenAt: 1 } } }
        : {
            profiles: {
              "0xaa": { address: " 0xAA ", username: "A", hiddenAt: 1 },
            },
          };
    const f = fixture(data);
    f.render(kind);
    const button = f.buttons.find((b) => b["aria-label"]);
    assert.ok(button);
    button.onClick();
    assert.equal(typeof f.writes[0].next, "function");
    const later = {
      ...(kind === "tokens" ? data.tokens : data.profiles),
      newSynthetic: { hiddenAt: 2 },
    };
    assert.deepEqual(f.writes[0].next(later), {
      newSynthetic: { hiddenAt: 2 },
    });
    f.rows[0].control.props.onClick();
    assert.deepEqual(f.writes[1].next, {});
    const failure = Error("SYNTHETIC localsetter failure"),
      broken = fixture({ ...data, throwWrite: failure });
    broken.render(kind);
    assert.throws(
      () => broken.buttons.find((b) => b["aria-label"]).onClick(),
      (e) => e === failure,
    );
  }
});
