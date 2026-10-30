import React from "../../packages/frontend/node_modules/react/index.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import {
  jsx,
  jsxs,
} from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { c as useMemoCache } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import { createSettingsEntryFlow } from "../../reconstruction/settings-entry-flow/client.mjs";
const events = [],
  changes = [],
  listeners = new Set(),
  querySubscribers = new Set(),
  flagSubscribers = new Set(),
  mounts = [],
  unmounts = [],
  ids = ["feed", "privacy"];
let enabled = false,
  currentProps,
  root,
  loadCount = 0,
  schema,
  options,
  queryRead = 0;
const notify = () => {
  for (const fn of querySubscribers) fn();
};
const browser = {
  location: window.location,
  history: {
    get state() {
      return window.history.state;
    },
    replaceState(state, title, url) {
      events.push({
        kind: "replace-before",
        href: window.location.href,
        next: String(url),
        state,
      });
      window.history.replaceState(state, title, url);
      notify();
      events.push({ kind: "replace-after", href: window.location.href });
    },
  },
  addEventListener(type, fn) {
    events.push({ kind: "listen", type });
    listeners.add(fn);
    window.addEventListener(type, fn);
  },
  removeEventListener(type, fn) {
    events.push({ kind: "unlisten", type });
    listeners.delete(fn);
    window.removeEventListener(type, fn);
  },
  dispatchEvent(event) {
    events.push({
      kind: "dispatch",
      type: event.type,
      href: window.location.href,
      detail: event.detail,
    });
    return window.dispatchEvent(event);
  },
};
function setQuery(patch) {
  changes.push(patch);
  const u = new URL(window.location.href);
  for (const [k, v] of Object.entries(patch))
    v === null ? u.searchParams.delete(k) : u.searchParams.set(k, v);
  browser.history.replaceState(window.history.state, "", u);
}
const stringParser = { kind: "synthetic-string-parser" },
  enumParser = { kind: "synthetic-enum-parser" },
  flagKey = Symbol("synthetic WEB_SETTINGS_HUB");
function useQueryStates(s, o) {
  schema = s;
  options = o;
  queryRead++;
  const href = React.useSyncExternalStore(
    (fn) => {
      querySubscribers.add(fn);
      return () => querySubscribers.delete(fn);
    },
    () => window.location.href,
    () => "",
  );
  const u = new URL(href);
  return [
    {
      settings: u.searchParams.get("settings"),
      setting: u.searchParams.get("setting"),
    },
    setQuery,
  ];
}
function ModalProbe(p) {
  currentProps = p;
  const id = React.useId();
  React.useEffect(() => {
    mounts.push(id);
    return () => {
      unmounts.push(id);
    };
  }, []);
  return jsxs("section", {
    "data-modal": id,
    children: [
      jsx("h2", { children: "Synthetic read-only modal probe" }),
      jsx("p", {
        "data-props": true,
        children: p.section + ":" + String(p.focusSettingId),
      }),
      jsx("button", {
        "data-action": "section",
        onClick: () => p.onSectionChange("privacy", "privacy.synthetic"),
        children: "Change section via original callback",
      }),
      jsx("button", {
        "data-action": "empty",
        onClick: () => p.onSectionChange("feed", ""),
        children: "Empty string via original callback",
      }),
      jsx("button", {
        "data-action": "close",
        onClick: p.onClose,
        children: "Close via original callback",
      }),
    ],
  });
}
const flow = createSettingsEntryFlow({
  window: browser,
  URL,
  CustomEvent,
  jsx,
  useMemoCache,
  useEffect: React.useEffect,
  settingsFlag: flagKey,
  useFeatureFlag(key) {
    if (key !== flagKey) throw Error("Unexpected synthetic flag key");
    return React.useSyncExternalStore(
      (fn) => {
        flagSubscribers.add(fn);
        return () => flagSubscribers.delete(fn);
      },
      () => enabled,
      () => false,
    );
  },
  sectionIds: ids,
  parseAsStringEnum(got) {
    if (got !== ids) throw Error("Unexpected section IDs");
    return enumParser;
  },
  parseAsString: stringParser,
  useQueryStates,
  dynamic(loader, o) {
    events.push({ kind: "dynamic-options", options: o });
    const Lazy = React.lazy(() =>
      loader().then((Component) => ({ default: Component })),
    );
    return (p) =>
      jsx(React.Suspense, {
        fallback: jsx("p", {
          "data-loading": true,
          children: "Synthetic lazy capability pending",
        }),
        children: jsx(Lazy, p),
      });
  },
  loadModule(id) {
    if (id !== 298590) throw Error("Unexpected loader ID");
    loadCount++;
    events.push({ kind: "load", id });
    return Promise.resolve({ SettingsModal: ModalProbe });
  },
});
function App() {
  return jsxs("main", {
    children: [
      jsx("h1", { children: "Synthetic Settings URL/event entry workflow" }),
      jsx("p", {
        children:
          "No cookie, storage, tenant, account or protected modal acquisition.",
      }),
      jsx(flow.SettingsModalHost, {}),
    ],
  });
}
root = createRoot(document.getElementById("root"));
root.render(jsx(App, {}));
window.settingsEntryFixture = {
  snapshot() {
    return {
      events,
      changes,
      listeners: listeners.size,
      subscribers: querySubscribers.size,
      flagSubscribers: flagSubscribers.size,
      mounts,
      unmounts,
      loadCount,
      queryRead,
      schema: {
        settings: schema?.settings === enumParser,
        setting: schema?.setting === stringParser,
      },
      options,
      href: window.location.href,
      state: window.history.state,
      props: currentProps && {
        section: currentProps.section,
        focusSettingId: currentProps.focusSettingId,
      },
    };
  },
  flag(value) {
    enabled = value;
    for (const fn of flagSubscribers) fn();
  },
  open: flow.openSettings,
  unmount() {
    root.unmount();
  },
  remount() {
    root = createRoot(document.getElementById("root"));
    root.render(jsx(App, {}));
  },
};
