import React, {
  useState,
  useEffect,
  useSyncExternalStore,
} from "../../packages/frontend/node_modules/react/index.js";
import { c as useMemoCache } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import {
  jsx,
  jsxs,
  Fragment,
} from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import {
  createLocalKeyRuntime,
  createLegacyInitializer,
  createSettingsRuntime,
  createFeedAnimationsDefinition,
  createSettingsSwitch,
} from "../../reconstruction/local-settings-runtime/client.mjs";
import {
  syntheticSettingsWindow,
  SyntheticStorageEvent,
} from "./local-settings-ports.mjs";

const key = "home.show-animations";
const browser = syntheticSettingsWindow({ [key]: "false" });
const local = createLocalKeyRuntime({
  window: browser.window,
  StorageEvent: SyntheticStorageEvent,
});
const definition = createFeedAnimationsDefinition(local);
const settings = createSettingsRuntime({
  registry: { [definition.id]: definition },
  initializeLegacy: createLegacyInitializer({ window: browser.window }),
  useMemoCache,
  useSyncExternalStore,
});
const forbidden = () => {
  throw Error("Private confirmation/provider capability not supplied");
};
let pointerBubbles = 0,
  currentSetter,
  firstSetter,
  setterChanged = false;
const Switch = createSettingsSwitch({
  jsx,
  jsxs,
  Fragment,
  useMemoCache,
  useState,
  useTranslation: () => ({ t: (key) => key }),
  translateKey: (t, key) => t(key),
  useHydrated: () => {
    const [ready, setReady] = useState(false);
    useEffect(() => setReady(true), []);
    return ready;
  },
  settings,
  Button: forbidden,
  confirmation: {
    N: forbidden,
    K: forbidden,
    c: forbidden,
    $: "primary",
    Z: "secondary",
  },
  // Explicit captured-shaped host port, not a reconstruction of 439587.Z.
  Switch: ({ isChecked, isDisabled, onCheckedChange, ...props }) =>
    React.createElement(
      "button",
      {
        role: "switch",
        "aria-label": props["aria-label"],
        "aria-checked": isChecked,
        disabled: isDisabled,
        onClick: () => onCheckedChange(!isChecked),
      },
      isChecked ? "On" : "Off",
    ),
});
function App() {
  const [value, setter] = settings.useSettingPair(definition.id);
  currentSetter = setter;
  firstSetter ??= setter;
  if (firstSetter !== setter) setterChanged = true;
  return React.createElement(
    "main",
    { onPointerDown: () => pointerBubbles++ },
    React.createElement("h1", {}, "Original local-setting React fixture"),
    React.createElement(
      "p",
      {},
      "Synthetic storage and host controls; not the product Settings page.",
    ),
    React.createElement(Switch, {
      definition,
      label: "Synthetic animation preference",
    }),
    React.createElement("output", { id: "snapshot" }, String(value)),
    React.createElement(
      "button",
      {
        id: "twice",
        onClick: () => {
          setter((v) => !v);
          setter((v) => !v);
        },
      },
      "Two functional updates",
    ),
  );
}
const root = createRoot(document.getElementById("root"));
root.render(React.createElement(App));
window.localSettingsFixture = {
  summary: () => ({
    values: Object.fromEntries(browser.values),
    calls: [...browser.calls],
    pointerBubbles,
    setterChanged,
  }),
  failWrites: (value) => {
    browser.failures.write = value;
  },
  write: (value) => settings.writeSetting(definition.id, value),
  external: (value) => {
    browser.values.set(key, JSON.stringify(value));
    browser.window.dispatchEvent(new SyntheticStorageEvent("storage", { key }));
  },
  freshRead: () =>
    createLocalKeyRuntime({
      window: browser.window,
      StorageEvent: SyntheticStorageEvent,
    })
      .localKey({ key, codec: "json" })
      .read(),
  doubleUpdate: () => {
    currentSetter((v) => !v);
    currentSetter((v) => !v);
  },
  clearCalls: () => {
    browser.calls.length = 0;
  },
  unmount: () => root.unmount(),
};
