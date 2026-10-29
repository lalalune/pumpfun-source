import React, {
  useState,
  useTransition,
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
  createLocaleCatalog,
  createLocaleCookie,
  createLanguageClient,
  createLanguageSelector,
} from "../../reconstruction/language-switch/client.mjs";

// This is a controlled integration fixture, not the original Select/i18n provider.
const catalog = createLocaleCatalog(),
  steps = [],
  bundles = new Map();
let cookieText = "",
  holdChanges = true,
  releaseProvider,
  rejectNext = false;
const documentPort = {};
Object.defineProperty(documentPort, "cookie", {
  get: () => cookieText,
  set: (value) => {
    cookieText = value;
    steps.push(["cookie", value]);
  },
});
const cookie = createLocaleCookie({
  document: documentPort,
  location: { protocol: "http:" },
  normalizeLocale: catalog.normalizeLocale,
});
const instance = {
  language: "en",
  getResource(locale, namespace, key) {
    steps.push(["resource", locale, namespace, key]);
    return bundles.get(locale)?.[key];
  },
  addResourceBundle(locale, namespace, data, deep, overwrite) {
    steps.push(["bundle", locale, namespace, deep, overwrite]);
    bundles.set(locale, { ...bundles.get(locale), ...data });
  },
  async changeLanguage(locale) {
    steps.push(["change:start", locale]);
    if (holdChanges)
      await new Promise((resolve) => {
        releaseProvider = resolve;
      });
    if (rejectNext) {
      rejectNext = false;
      throw Error("synthetic provider rejection");
    }
    instance.language = locale;
    steps.push(["change:end", locale]);
  },
};
const service = createLanguageClient({
  fetch: (url) => fetch(url),
  logger: { warn: (...args) => steps.push(["warn", ...args]) },
  writeCookie: cookie.writeCookie,
});
const Context = createContext(null);
const select = {
  Root({ value, onValueChange, disabled, children }) {
    const [open, setOpen] = useState(false);
    return React.createElement(
      Context.Provider,
      { value: { value, onValueChange, disabled, open, setOpen } },
      React.createElement("div", { className: "select-port" }, children),
    );
  },
  Trigger({ children, chevronClassName, ...props }) {
    const context = useContext(Context);
    return React.createElement(
      "button",
      {
        ...props,
        type: "button",
        disabled: context.disabled,
        "aria-haspopup": "listbox",
        "aria-expanded": context.open,
        onClick: () => context.setOpen(!context.open),
      },
      children,
    );
  },
  Value: ({ children }) => React.createElement("span", null, children),
  Content({ children }) {
    const context = useContext(Context);
    return context.open
      ? React.createElement(
          "div",
          { role: "listbox", className: "options-port" },
          children,
        )
      : null;
  },
  Item({ value, textValue, children, ...props }) {
    const context = useContext(Context);
    return React.createElement(
      "button",
      {
        ...props,
        type: "button",
        role: "option",
        disabled: context.disabled,
        "aria-selected": context.value === value,
        onClick: () => {
          context.onValueChange(value);
          context.setOpen(false);
        },
      },
      children,
    );
  },
};
const Selector = createLanguageSelector({
  jsx,
  jsxs,
  useMemoCache,
  useState,
  useTransition,
  useTranslation: () => ({ i18n: instance }),
  useRouter: () => ({ refresh: () => steps.push(["refresh"]) }),
  select,
  catalog,
  changeLanguage: service.changeLanguage,
});
const root = createRoot(document.getElementById("root"));
root.render(
  React.createElement(
    "main",
    null,
    React.createElement("h1", null, "Original language-switch React fixture"),
    React.createElement(
      "p",
      null,
      "Synthetic document/location/i18n/Select/router ports. No real cookie or global app translation.",
    ),
    React.createElement(Selector),
  ),
);
window.languageFixture = {
  snapshot: () => ({
    cookieText,
    language: instance.language,
    steps: [...steps],
  }),
  finishProvider() {
    holdChanges = false;
    releaseProvider?.();
    releaseProvider = undefined;
  },
  rejectNext() {
    rejectNext = true;
  },
  holdProvider() {
    holdChanges = true;
  },
  unmount() {
    root.unmount();
  },
};
