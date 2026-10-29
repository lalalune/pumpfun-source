import React, {
  useState,
  useEffect,
  useId,
} from "../../packages/frontend/node_modules/react/index.js";
import { c as useMemoCache } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import {
  jsx,
  jsxs,
} from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import { createSettingsSearchResults } from "../../reconstruction/settings-search-results/client.mjs";

// Read-only synthetic metadata and host capabilities. No preference/provider implementation.
const dictionary = {
  "section.feed": "Feed",
  "section.privacy": "Privacy",
  blue: "Blue Café",
  "blue.description": "Compact cards",
  warning: "Warnings",
  "warning.description": "Read links",
  other: "Other shared result",
  hidden: "Hidden shared",
  outside: "Outside shared",
  "web.settings.search_results": "Settings search results",
};
const translate = (key, options) =>
  key === "web.settings.search_empty"
    ? "No matches for " + options.query
    : (dictionary[key] ?? key);
const registry = [
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
  {
    id: "feed.hidden",
    section: "feed",
    labelKey: "hidden",
    searchTerms: ["shared"],
    control: { kind: "switch" },
  },
  {
    id: "feed.hiddenKind",
    section: "feed",
    labelKey: "hidden",
    searchTerms: ["shared"],
    control: { kind: "hidden" },
  },
  {
    id: "outside.item",
    section: "outside",
    labelKey: "outside",
    searchTerms: ["shared"],
    control: { kind: "switch" },
  },
];
const sections = [
  { id: "feed", labelKey: "section.feed" },
  { id: "privacy", labelKey: "section.privacy" },
];
let hidden = new Set(["feed.hidden"]),
  visible = ["feed", "privacy"],
  force;
const mounted = new Map(),
  events = [];
function Field({ definition }) {
  const instance = useId();
  useEffect(() => {
    mounted.set(definition.id, instance);
    events.push(["mount", definition.id, instance]);
    return () => {
      mounted.delete(definition.id);
      events.push(["unmount", definition.id, instance]);
    };
  }, [definition.id, instance]);
  return jsx("article", {
    "data-setting-id": definition.id,
    "data-host-instance": instance,
    children: translate(definition.labelKey),
  });
}
const Results = createSettingsSearchResults({
  jsx,
  jsxs,
  useMemoCache,
  useTranslation: () => ({ t: translate }),
  translateKey: (t, key) => t(key),
  useHiddenSettingIds: () => hidden,
  registry,
  sections,
  Field,
  Section: ({ label, children }) =>
    jsxs("section", {
      "data-group": label,
      children: [jsx("h2", { children: label }), children],
    }),
});
function Host() {
  const [query, setQuery] = useState("shared"),
    [, setVersion] = useState(0);
  force = () => setVersion((value) => value + 1);
  const trimmed = query.trim();
  return jsxs("main", {
    children: [
      jsx("h1", { children: "Synthetic original Settings results fixture" }),
      jsx("label", {
        children: jsxs("span", {
          children: [
            "Synthetic query ",
            jsx("input", {
              "aria-label": "Synthetic settings query",
              value: query,
              onChange: (event) => setQuery(event.currentTarget.value),
            }),
          ],
        }),
      }),
      trimmed
        ? jsx(Results, { query: trimmed, visibleSections: visible })
        : jsx("p", {
            "data-host-state": "blank-query",
            children:
              "Synthetic host: original caller selects an external section view for blank query.",
          }),
    ],
  });
}
const root = createRoot(document.getElementById("root"));
root.render(jsx(Host, {}));
window.settingsResultsFixture = {
  snapshot: () => ({
    mounted: Object.fromEntries(mounted),
    events: structuredClone(events),
  }),
  setHidden(ids) {
    hidden = new Set(ids);
    force();
  },
  setVisible(ids) {
    visible = [...ids];
    force();
  },
  unmount() {
    root.unmount();
  },
};
