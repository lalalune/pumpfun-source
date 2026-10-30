import React from "../../packages/frontend/node_modules/react/index.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import {
  jsx,
  jsxs,
} from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { c as useMemoCache } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import { createSettingsDecimalInput } from "../../reconstruction/settings-decimal-input/client.mjs";
const Input = createSettingsDecimalInput({
  jsx,
  jsxs,
  useMemoCache,
  useState: React.useState,
});
let update, root;
const commits = [],
  mounts = [],
  unmounts = [];
let state = {
    value: 5,
    min: 2.5,
    step: 0.25,
    unit: "units",
    isDisabled: false,
    present: true,
    reject: false,
  },
  latest;
function MountedInput(p) {
  const id = React.useId();
  React.useEffect(() => {
    mounts.push(id);
    return () => unmounts.push(id);
  }, []);
  return jsx("div", { "data-instance": id, children: jsx(Input, p) });
}
function App() {
  const [s, set] = React.useState(state);
  state = s;
  update = (patch) => set((old) => ({ ...old, ...patch }));
  latest = s;
  return jsxs("main", {
    children: [
      jsx("h1", { children: "Synthetic decimal draft input" }),
      jsx("p", {
        children:
          "Supplied numeric props/callback only; no real preferences or account data.",
      }),
      jsx("output", { "data-value": true, children: String(s.value) }),
      s.present
        ? jsx(MountedInput, {
            value: s.value,
            min: s.min,
            step: s.step,
            unit: s.unit,
            isDisabled: s.isDisabled,
            label: "Synthetic decimal value",
            onCommit(value) {
              commits.push({ value, accepted: !s.reject });
              if (s.reject) throw Error("SYNTHETIC numeric commit denial");
              set((old) => ({ ...old, value }));
            },
          })
        : null,
      jsx("button", {
        "data-action": "blur",
        children: "Outside focus target",
      }),
    ],
  });
}
root = createRoot(document.getElementById("root"));
root.render(jsx(App, {}));
window.settingsDecimalFixture = {
  patch(patch) {
    update(patch);
  },
  snapshot() {
    return { state: latest, commits, mounts, unmounts };
  },
  unmount() {
    root.unmount();
  },
};
