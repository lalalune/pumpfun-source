import React from "../../packages/frontend/node_modules/react/index.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import {
  jsx,
  jsxs,
} from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { c as useMemoCache } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import { createSettingsModalOwner } from "../../reconstruction/settings-modal-owner/client.mjs";
const sections = [
    {
      id: "feed",
      labelKey: "synthetic.feed",
      tabLabelKey: "synthetic.feed.tab",
    },
    {
      id: "privacy",
      labelKey: "synthetic.privacy",
      tabLabelKey: "synthetic.privacy.tab",
    },
  ],
  events = [],
  mounts = [],
  unmounts = [],
  queries = [],
  focusCalls = [];
const TabsContext = React.createContext(null),
  FocusContext = React.createContext(null);
let current, update, root, dialogCallback;
const translate = (key) => key;
function DialogRoot(p) {
  dialogCallback = p.onIsOpenChange;
  return jsx("div", { "data-dialog-root": true, children: p.children });
}
function TabsRoot(p) {
  return jsx(TabsContext.Provider, { value: p, children: p.children });
}
function TabsTrigger(p) {
  const v = React.useContext(TabsContext);
  return jsx("button", {
    role: "tab",
    "aria-selected": v.value === p.value,
    onClick: () => v.onValueChange(p.value),
    children: p.children,
  });
}
function SectionContent(p) {
  const id = React.useId(),
    focus = React.useContext(FocusContext);
  React.useEffect(() => {
    mounts.push({ id, section: p.section });
    return () => unmounts.push({ id, section: p.section });
  }, []);
  return jsxs("section", {
    "data-section": p.section,
    "data-instance": id,
    children: [
      jsx("p", { "data-focus-value": true, children: String(focus) }),
      ...Array.from({ length: 30 }, (_, n) =>
        jsx(
          "p",
          { children: "Synthetic readonly " + p.section + " row " + n },
          n,
        ),
      ),
    ],
  });
}
function SearchResults(p) {
  queries.push(p);
  return jsxs("section", {
    "data-results-query": p.query,
    children: Array.from({ length: 30 }, (_, n) =>
      jsx("p", { children: "Synthetic result " + p.query + " " + n }, n),
    ),
  });
}
const Owner = createSettingsModalOwner({
  jsx,
  jsxs,
  useMemoCache,
  useState: React.useState,
  useEffect: React.useEffect,
  useId: React.useId,
  useRef: React.useRef,
  useTranslation: () => ({ t: translate }),
  translateKey: (t, key) => t(key),
  useVisibleSections: () => current.sections,
  useSettingsResourceAttempt: () => current.ready,
  useTransientSettingId: (id) => {
    focusCalls.push(id);
    return id;
  },
  FocusContextProvider: FocusContext.Provider,
  definitionsForSection: () =>
    current.resettable
      ? [{ id: "synthetic.safe.display", resettable: true }]
      : [{ id: "synthetic.safe.display", resettable: false }],
  SearchResults,
  SectionContent,
  Loading: () =>
    jsx("div", {
      "data-loading": true,
      "aria-hidden": true,
      children: "Synthetic external loading renderer",
    }),
  resetSection: (section) => {
    events.push({ kind: "reset", section, accepted: !current.denyReset });
    if (current.denyReset) throw Error("SYNTHETIC reset callback denial");
  },
  DialogRoot,
  DialogContent: (p) =>
    jsx("section", { "data-testid": p["data-testid"], children: p.children }),
  TabsRoot,
  TabsList: (p) =>
    jsx("nav", { "aria-label": p["aria-label"], children: p.children }),
  TabsTrigger,
  Button: (p) =>
    jsx("button", { type: "button", onClick: p.onClick, children: p.children }),
  CloseIcon: () => jsx("span", { "aria-hidden": true, children: "×" }),
  SearchIcon: () => jsx("span", { "aria-hidden": true, children: "⌕" }),
  ResetIcon: () => jsx("span", { "aria-hidden": true, children: "↻" }),
  DeviceIcon: () => jsx("span", { "aria-hidden": true, children: "◎" }),
});
function App() {
  const [state, set] = React.useState({
    section: "feed",
    focusSettingId: "feed.synthetic",
    sections,
    ready: false,
    resettable: true,
    denyReset: false,
    present: true,
  });
  current = state;
  update = (p) => set((old) => ({ ...old, ...p }));
  return jsxs("main", {
    children: [
      jsx("h1", { children: "Synthetic complete Settings display owner" }),
      jsx("p", {
        children:
          "External availability/resource/readonly renderer/reset callback ports only; no providers or preferences acquired.",
      }),
      state.present
        ? jsx(Owner, {
            section: state.section,
            focusSettingId: state.focusSettingId,
            onSectionChange: (section) => {
              events.push({ kind: "select", section });
              set((old) => ({ ...old, section }));
            },
            onClose: () => {
              events.push({ kind: "close" });
              set((old) => ({ ...old, present: false }));
            },
          })
        : null,
    ],
  });
}
root = createRoot(document.getElementById("root"));
root.render(jsx(App, {}));
window.settingsModalFixture = {
  patch: (p) => update(p),
  dialog: (open) => dialogCallback(open),
  snapshot() {
    return {
      state: current,
      events,
      mounts,
      unmounts,
      queries: queries.map((q) => ({
        query: q.query,
        visibleSections: q.visibleSections,
      })),
      focusCalls,
    };
  },
  unmount() {
    root.unmount();
  },
};
