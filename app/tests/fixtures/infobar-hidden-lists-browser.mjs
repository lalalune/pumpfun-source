import React, {
  useState,
  useContext,
  createContext,
} from "../../packages/frontend/node_modules/react/index.js";
import { c as useMemoCache } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import {
  jsx,
  jsxs,
} from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import {
  createHiddenInfoBarValues,
  createHiddenInfoBarDefinitions,
  createHiddenInfoBarFields,
} from "../../reconstruction/infobar-hidden-lists/client.mjs";
// Safe synthetic in-memory data and local-setting/bucket ports only; no original private store or actual browser storage.
const values = createHiddenInfoBarValues(),
  events = [],
  formats = [],
  StoreContext = createContext(null);
let fail = false,
  notify;
const state = {
  hiddenTokens: values.coerceTokens({
    a: { mint: "0xAB", symbol: "ALPHA", hiddenAt: 1 },
    b: { mint: "synthetic-beta", symbol: "BETA", hiddenAt: 4 },
    c: { mint: "synthetic-fallback", symbol: "", hiddenAt: 2 },
  }),
  hiddenProfiles: values.coerceProfiles({
    a: { address: "synthetic-alice", username: "alice", hiddenAt: 1 },
    b: { address: " 0xBB ", username: "bob", hiddenAt: 5 },
  }),
  setField(key, next) {
    if (fail) throw Error("SYNTHETIC local setter denied");
    events.push(["setField", key, Object.keys(next)]);
    this[key] = next;
    notify();
  },
};
const definitions = createHiddenInfoBarDefinitions({
    values,
    store: state,
    makeBucketAdapter: (config) => ({
      write(next) {
        return config.write({ next, state: config.store() });
      },
      read() {
        return config.select(config.store());
      },
    }),
  }),
  byId = new Map(definitions.map((d) => [d.id, d]));
const writers = Object.fromEntries(
  definitions.map((d) => [
    d.id,
    (next) => {
      events.push(["write-request", d.id, typeof next]);
      const latest = d.adapter.read();
      events.push(["latest-read", d.id, Object.keys(latest)]);
      const result = typeof next === "function" ? next(latest) : next;
      d.adapter.write(d.coerce(result));
    },
  ]),
);
const translation = (key, options) =>
  ({
    "web.info_bar.hidden_tokens": "Hidden tokens",
    "web.info_bar.hidden_profiles": "Hidden profiles",
    "web.info_bar.no_hidden_tokens": "None hidden",
    "web.info_bar.hidden_positions_note":
      "Synthetic note: positions are separate",
    "web.info_bar.show_all_hidden": "Show all hidden",
  })[key] ??
  (options?.symbol
    ? "Unhide " + options.symbol
    : options?.name
      ? "Unhide " + options.name
      : key);
const useSetting = (id) => {
  const snapshot = useContext(StoreContext);
  return [
    snapshot[id.endsWith("hiddenTokens") ? "hiddenTokens" : "hiddenProfiles"],
    writers[id],
  ];
};
const readSetting = (id) => {
  const snapshot = useContext(StoreContext);
  if (id !== "feed.infoBar.hiddenProfiles")
    throw Error("Unexpected synthetic setting read");
  return snapshot.hiddenProfiles;
};
function Row({ settingId, title, description, note, control, children }) {
  return jsxs("section", {
    "data-setting-id": settingId,
    children: [
      jsx("h2", { children: title }),
      description
        ? jsx("p", { "data-description": true, children: description })
        : null,
      note ? jsx("p", { "data-note": true, children: note }) : null,
      control,
      children,
    ],
  });
}
const { HiddenTokens, HiddenProfiles } = createHiddenInfoBarFields({
  jsx,
  jsxs,
  useMemoCache,
  useTranslation: () => ({ t: translation }),
  translateKey: (t, key) => t(key),
  useSetting,
  readSetting,
  Row,
  Action: (props) => jsx("button", props),
  CloseIcon: (props) => jsx("span", { ...props, children: "×" }),
  formatProfileLabel: (props) => {
    formats.push(["profile", props]);
    return "@" + (props.username ?? "synthetic-fallback");
  },
  truncateAddress: (address, left, right) => {
    formats.push(["truncate", address, left, right]);
    return "synthetic-abbreviation";
  },
  normalizeDisplayText: (label, category) => {
    formats.push(["normalize", label, category]);
    return label;
  },
  values,
});
function Host() {
  const [, setVersion] = useState(0);
  notify = () => setVersion((n) => n + 1);
  return jsxs("main", {
    children: [
      jsx("h1", { children: "Synthetic original InfoBar hidden-list fields" }),
      jsx("p", {
        children:
          "In-memory synthetic local-setting ports and readonly metadata; not product preferences.",
      }),
      jsx(StoreContext.Provider, {
        value: {
          hiddenTokens: state.hiddenTokens,
          hiddenProfiles: state.hiddenProfiles,
        },
        children: jsxs("div", {
          children: [
            jsx(HiddenTokens, {
              definition: byId.get("feed.infoBar.hiddenTokens"),
            }),
            jsx(HiddenProfiles, {
              definition: byId.get("feed.infoBar.hiddenProfiles"),
            }),
          ],
        }),
      }),
    ],
  });
}
const root = createRoot(document.getElementById("root"));
root.render(jsx(Host, {}));
window.hiddenInfoBarFixture = {
  snapshot: () => ({
    tokens: structuredClone(state.hiddenTokens),
    profiles: structuredClone(state.hiddenProfiles),
    events: structuredClone(events),
    formats: structuredClone(formats),
    fail,
  }),
  fail(value) {
    fail = value;
  },
  addToken() {
    state.hiddenTokens = values.coerceTokens({
      ...state.hiddenTokens,
      "synthetic-latest": {
        mint: "synthetic-latest",
        symbol: "LATEST",
        hiddenAt: 9,
      },
    });
    events.push(["synthetic-add"]);
    notify();
  },
  unmount() {
    root.unmount();
  },
};
