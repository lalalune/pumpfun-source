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
import { createSettingsSectionContent } from "../../reconstruction/settings-section-content/client.mjs";
// Readonly synthetic registry/visibility/renderer ports only. No private account/Hermes/cookie provider.
const item = (id) => ({
    id,
    control: { kind: "custom", component: "synthetic-readonly" },
  }),
  catalog = {
    chart: [
      item("chart.markers.b"),
      item("chart.axis.synthetic"),
      item("chart.markers.a"),
    ],
    feed: [item("feed.second"), item("feed.first")],
    privacy: [item("privacy.synthetic")],
    account: [],
    notifications: [item("notifications.synthetic")],
  };
const events = [],
  mounted = new Map(),
  frames = new Map();
let hidden = new Set(),
  section = "chart",
  redraw;
const close = () => events.push(["external-close"]);
function Field({ definition, compact }) {
  const id = useId();
  useEffect(() => {
    mounted.set(definition.id, id);
    events.push(["field-mount", definition.id, id]);
    return () => {
      mounted.delete(definition.id);
      events.push(["field-unmount", definition.id, id]);
    };
  }, [definition, id]);
  return jsx("article", {
    "data-field-id": definition.id,
    "data-host-instance": id,
    "data-compact": compact,
    children: definition.id,
  });
}
function Section(props) {
  const id = useId();
  useEffect(() => {
    frames.set(id, props.label ?? "unlabelled");
    return () => frames.delete(id);
  }, [id, props.label]);
  return jsxs("section", {
    "data-host-frame": id,
    "data-label": props.label ?? "unlabelled",
    children: [
      props.label ? jsx("h2", { children: props.label }) : null,
      props.description
        ? jsx("p", { "data-description": true, children: props.description })
        : null,
      props.children,
    ],
  });
}
const Content = createSettingsSectionContent({
  jsx,
  jsxs,
  useMemoCache,
  useTranslation: () => ({ t: translate }),
  translateKey: (t, key) => t(key),
  useHiddenSettingIds: () => hidden,
  definitionsForSection: (id) => catalog[id] ?? [],
  Section,
  Field,
  AccountHeader: () =>
    jsx("p", {
      "data-external-port": "account",
      children: "External readonly account header; no acquired data.",
    }),
  NotificationSettingsSections: () =>
    jsx("p", {
      "data-external-port": "notifications",
      children: "External readonly notification renderer; no provider request.",
    }),
  PrivacyFooter: (props) =>
    jsx("aside", {
      "data-external-port": "privacy",
      "data-close-identity": props.onOpen === close ? "same" : "different",
      children: "External readonly privacy footer; no cookie action.",
    }),
});
function translate(key) {
  return "Synthetic:" + key;
}
function Host() {
  const [, force] = useState(0);
  redraw = () => force((n) => n + 1);
  return jsxs("main", {
    children: [
      jsx("h1", { children: "Synthetic original Settings section content" }),
      jsx("p", {
        children:
          "Readonly metadata and external renderer ports; no preferences or private providers.",
      }),
      jsx(
        "div",
        { children: jsx(Content, { section, onRequestClose: close }) },
        section,
      ),
    ],
  });
}
const root = createRoot(document.getElementById("root"));
root.render(jsx(Host, {}));
window.settingsSectionFixture = {
  snapshot: () => ({
    section,
    hidden: [...hidden],
    mounted: Object.fromEntries(mounted),
    frames: Object.fromEntries(frames),
    events: structuredClone(events),
  }),
  hidden(ids) {
    hidden = new Set(ids);
    redraw();
  },
  section(value) {
    section = value;
    redraw();
  },
  unmount() {
    root.unmount();
  },
};
