import React, {
  useSyncExternalStore,
} from "../../packages/frontend/node_modules/react/index.js";
import { c as useMemoCache } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import {
  jsx,
  jsxs,
} from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import {
  createHomeLayoutCookie,
  createCookieAdapter,
  createHomeLayoutDefinition,
  createLayoutPreviews,
  createChoiceRenderer,
  createSettingsField,
} from "../../reconstruction/home-layout-choice/client.mjs";

// Authored host only. This is not the original547562/provider, product page or browser cookie.
let cookieText = "",
  denyNext = false,
  root,
  definition,
  Field;
const calls = [],
  listeners = new Set();
const documentPort = {};
Object.defineProperty(documentPort, "cookie", {
  get() {
    calls.push(["read", cookieText]);
    return cookieText;
  },
  set(value) {
    calls.push(["write:attempt", value]);
    if (denyNext) {
      denyNext = false;
      throw Error("synthetic layout cookie denied");
    }
    cookieText = value;
    calls.push(["write:done", value]);
  },
});
const labels = {
  "web.home.layout_grid": "Grid",
  "web.home.layout_table": "Table",
  "web.home.feed_layout_a11y": "Feed layout",
  "web.settings.feed.layout_description":
    "Synthetic layout-choice host; no Home effect.",
};
const shared = {
  jsx,
  jsxs,
  useMemoCache,
  useTranslation: () => ({ t: (key) => key }),
  translateKey: (_t, key) => labels[key] ?? key,
  markString: (value) => value,
  classNames: (...values) => values.filter(Boolean).join(" "),
};
const previews = createLayoutPreviews(shared),
  choice = createChoiceRenderer({ ...shared, previews });
function mount() {
  const layout = createHomeLayoutCookie({
    document: documentPort,
    location: { protocol: "http:" },
  });
  definition = createHomeLayoutDefinition({
    layout,
    cookieAdapter: createCookieAdapter,
  });
  // API-compatible synthetic host hooks; exact547562 state/cache/legacy behavior stays external.
  const settings = {
    useSetting(id) {
      if (id !== definition.id) throw Error("Unexpected fixture definition");
      return useSyncExternalStore(
        (callback) => {
          const notify = () => {
            calls.push(["notify"]);
            callback();
          };
          listeners.add(notify);
          const stop = definition.adapter.subscribe(notify);
          return () => {
            stop();
            listeners.delete(notify);
            calls.push(["unsubscribe"]);
          };
        },
        () =>
          definition.coerce(definition.adapter.read() ?? definition.default),
        () => definition.default,
      );
    },
    useSetter(id) {
      if (id !== definition.id) throw Error("Unexpected fixture setter");
      return (value) => {
        calls.push(["set", value]);
        definition.adapter.write(definition.coerce(value));
      };
    },
  };
  Field = createSettingsField({
    ...shared,
    previews,
    choice,
    settings,
    useHydrated: () => true,
    Row: ({ settingId, title, description, control, children }) =>
      jsx("section", {
        "data-setting-id": settingId,
        children: jsxs("div", {
          children: [
            jsx("h2", { children: title }),
            jsx("p", { children: description }),
            control,
            children,
          ],
        }),
      }),
    Switch: () => {
      throw Error("Unselected switch port reached");
    },
    NumberInput: () => {
      throw Error("Unselected number port reached");
    },
    customControls: {},
  });
  root = createRoot(document.getElementById("root"));
  root.render(
    jsxs("main", {
      children: [
        jsx("h1", { children: "Synthetic original layout-choice fixture" }),
        jsx(Field, { definition }),
      ],
    }),
  );
}
window.homeLayoutFixture = {
  snapshot() {
    return {
      cookieText,
      calls: structuredClone(calls),
      listeners: listeners.size,
    };
  },
  external(value) {
    definition.adapter.write(definition.coerce(value));
  },
  denyNext() {
    denyNext = true;
  },
  unmount() {
    root.unmount();
  },
  mount,
};
mount();
