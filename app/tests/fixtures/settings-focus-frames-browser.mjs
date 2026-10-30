import React, {
  useState,
  useEffect,
  useRef,
  use,
  createContext,
} from "../../packages/frontend/node_modules/react/index.js";
import { c as useMemoCache } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import {
  jsx,
  jsxs,
} from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import { createSettingsFocusFrames } from "../../reconstruction/settings-focus-frames/client.mjs";
// Explicit synthetic input/readonly view and native timer ports, without global/property overrides.
const timers = [],
  events = [],
  active = new Set();
let target = "feed.beta",
  instance = 0,
  show = true,
  redraw;
const timerPort = {
  setTimeout(callback, delay) {
    const record = {
      id: null,
      delay,
      start: performance.now(),
      fired: null,
      cleared: [],
    };
    record.id = window.setTimeout(() => {
      record.fired = performance.now();
      active.delete(record.id);
      events.push(["timer-fired", record.id]);
      callback();
    }, delay);
    timers.push(record);
    active.add(record.id);
    events.push(["timer-set", record.id, delay]);
    return record.id;
  },
  clearTimeout(id) {
    timers.find((t) => t.id === id)?.cleared.push(performance.now());
    active.delete(id);
    events.push(["timer-clear", id]);
    window.clearTimeout(id);
  },
};
const { FocusProvider, Row, Section } = createSettingsFocusFrames({
  jsx,
  jsxs,
  useMemoCache,
  createContext,
  use,
  useState,
  useEffect,
  useRef,
  classNames: (...values) => values.filter(Boolean).join(" "),
  window: timerPort,
});
function Host() {
  const [, bump] = useState(0);
  redraw = () => bump((x) => x + 1);
  return jsxs("main", {
    children: [
      jsx("h1", { children: "Synthetic original Settings focus and frames" }),
      jsx("p", {
        children:
          "Read-only rows, native 2500ms timer and native scroll; no product Settings mount.",
      }),
      jsx("input", {
        "aria-label": "Synthetic host focus control",
        placeholder: "Diagnostic native focus control",
      }),
      show
        ? jsx(
            FocusProvider,
            {
              settingId: target,
              children: jsx("div", {
                "data-scroll-host": true,
                children: jsx(Section, {
                  label: "Read-only synthetic section",
                  description:
                    "Original complete frame components; supplied content only.",
                  "data-testid": "source-section",
                  children: [
                    jsx(
                      Row,
                      {
                        settingId: "feed.alpha",
                        title: "Alpha row",
                        description: "Safe readonly description",
                        note: "Synthetic note",
                        control: jsx("span", { children: "Readonly slot" }),
                        children: jsx("span", { children: "Readonly child" }),
                      },
                      "alpha",
                    ),
                    jsx(
                      "div",
                      { "aria-hidden": true, "data-host-spacer": true },
                      "spacer",
                    ),
                    jsx(
                      Row,
                      {
                        settingId: "feed.beta",
                        title: "Beta row",
                        description: "Second safe row",
                        dense: true,
                      },
                      "beta",
                    ),
                    jsx(
                      "div",
                      { "aria-hidden": true, "data-host-spacer": true },
                      "end",
                    ),
                  ],
                }),
              }),
            },
            instance,
          )
        : jsx("p", {
            "data-host-unmounted": true,
            children: "Synthetic source subtree unmounted",
          }),
    ],
  });
}
const root = createRoot(document.getElementById("root"));
root.render(jsx(Host, {}));
window.settingsFocusFixture = {
  snapshot: () => ({
    target,
    instance,
    show,
    active: [...active],
    timers: structuredClone(timers),
    events: structuredClone(events),
  }),
  target(value) {
    target = value;
    redraw();
  },
  rerender() {
    redraw();
  },
  remount(value) {
    target = value;
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
