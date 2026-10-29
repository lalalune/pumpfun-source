import React, {
  useState,
  useEffect,
  useContext,
  useId,
  createContext,
  createRef,
} from "../../packages/frontend/node_modules/react/index.js";
import { c as useMemoCache } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import {
  jsx,
  jsxs,
} from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import { createSettingsResourceContent } from "../../reconstruction/settings-resource-gate/client.mjs";
// Explicit synthetic provider/prefetch and diagnostic view ports. No actual storage/cookies/tenant resources.
const events = [],
  requests = [],
  mounted = new Map();
const focusContext = createContext(null),
  focus = { id: "synthetic-focus" },
  visible = ["feed", "privacy"],
  scrollRef = createRef();
let providerSerial = 0,
  instance = 0,
  query = "",
  section = "feed",
  show = true,
  redraw,
  contentRenders = 0,
  closeCount = 0;
function provider(language, exists = false) {
  const id = ++providerSerial;
  return {
    id,
    language,
    available: exists,
    exists(key) {
      events.push(["exists", id, key]);
      return this.available;
    },
  };
}
let current = provider("fr-FR");
const normalizeLocale = (language) => {
  events.push(["normalize", language]);
  return { "fr-FR": "fr", "de-DE": "de" }[language] ?? null;
};
function prefetchCatalog(i18n, locale) {
  events.push(["prefetch", i18n.id, locale]);
  let resolve, reject;
  const promise = new Promise((a, b) => {
    resolve = a;
    reject = b;
  });
  requests.push({
    id: requests.length,
    provider: i18n.id,
    locale,
    pending: true,
    resolve: () => {
      events.push(["resolve", requests.find((r) => r.promise === promise).id]);
      resolve();
    },
    reject: () => {
      events.push(["reject", requests.find((r) => r.promise === promise).id]);
      reject(Error("SYNTHETIC prefetch capability rejection"));
    },
    promise,
  });
  return promise;
}
function Section({ section, onRequestClose }) {
  const id = useId(),
    value = useContext(focusContext);
  useEffect(() => {
    mounted.set(id, section);
    events.push(["section-mount", section, id]);
    return () => {
      mounted.delete(id);
      events.push(["section-unmount", section, id]);
    };
  }, [id, section]);
  return jsxs("article", {
    "data-host-section": section,
    "data-host-instance": id,
    "data-host-focus": value?.id,
    children: [
      jsx("h2", { children: "Synthetic section " + section }),
      jsx("button", {
        onClick: onRequestClose,
        children: "Synthetic close callback",
      }),
    ],
  });
}
function Results({ query, visibleSections }) {
  return jsx("output", {
    "data-host-results": true,
    "data-visible-identity": visibleSections === visible ? "same" : "different",
    children: query,
  });
}
const { SettingsResourceContent } = createSettingsResourceContent({
  jsx,
  jsxs,
  useMemoCache,
  useState,
  useEffect,
  useTranslation: () => ({ i18n: current }),
  normalizeLocale,
  defaultLocale: "en",
  prefetchCatalog,
  SearchResults: Results,
  Section,
  FocusProvider: focusContext.Provider,
});
const close = () => {
  closeCount++;
  events.push(["close"]);
};
function ObservedContent(props) {
  contentRenders++;
  events.push(["content-render", current.id, instance]);
  return jsx(SettingsResourceContent, props);
}
function Host() {
  const [, setVersion] = useState(0);
  redraw = () => setVersion((x) => x + 1);
  return jsxs("main", {
    children: [
      jsx("h1", {
        children: "Synthetic original Settings resource-attempt fixture",
      }),
      jsx("p", {
        children:
          "Read-only host views and controlled provider promises; not product Settings.",
      }),
      show
        ? jsx(
            ObservedContent,
            {
              query,
              visibleSections: visible,
              section,
              focusValue: focus,
              onRequestClose: close,
              scrollRef,
            },
            instance,
          )
        : jsx("p", {
            "data-host-unmounted": true,
            children: "Synthetic content unmounted",
          }),
    ],
  });
}
const root = createRoot(document.getElementById("root"));
root.render(jsx(Host, {}));
window.settingsResourceFixture = {
  snapshot: () => ({
    provider: current.id,
    language: current.language,
    sentinel: current.available,
    instance,
    contentRenders,
    closeCount,
    mounted: Object.fromEntries(mounted),
    requests: requests.map(({ id, provider, locale, pending }) => ({
      id,
      provider,
      locale,
      pending,
    })),
    events: structuredClone(events),
  }),
  query(value) {
    query = value;
    redraw();
  },
  section(value) {
    section = value;
    redraw();
  },
  resolve(id) {
    requests[id].pending = false;
    requests[id].resolve();
  },
  reject(id) {
    requests[id].pending = false;
    requests[id].reject();
  },
  provider(language, exists) {
    current = provider(language, exists);
    redraw();
  },
  language(value) {
    current.language = value;
    redraw();
  },
  remount(language, exists = false) {
    current = provider(language, exists);
    instance++;
    show = true;
    redraw();
  },
  hide() {
    show = false;
    redraw();
  },
  unmount() {
    root.unmount();
  },
};
