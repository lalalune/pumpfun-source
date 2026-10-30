import React from "../../packages/frontend/node_modules/react/index.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import {
  jsx,
  jsxs,
  Fragment,
} from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { c as useMemoCache } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import { createSharedSidebarNavigation } from "../../reconstruction/shared-sidebar-navigation/client.mjs";
import { diagnosticSidebarPorts } from "./shared-sidebar-diagnostic-ports.mjs";
const events = [],
  listeners = new Set(),
  routes = {
    home: "/",
    explore: "/explore",
    leaderboard: "/leaderboard",
    live: "/live",
  },
  Icon = (kind) => (p) =>
    jsx("svg", {
      "data-diagnostic-icon": kind,
      viewBox: "0 0 12 12",
      ...p,
      children: jsx("circle", { cx: 6, cy: 6, r: 4 }),
    }),
  icons = { fill: Icon("fill"), line: Icon("line") };
let current, update, context, root;
const browser = {
  matchMedia(query) {
    const match = window.matchMedia(query);
    events.push({ kind: "media", query, matches: match.matches });
    return match;
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
};
function Link(p) {
  return jsx("a", {
    ...p,
    onClick(event) {
      p.onClick?.(event);
      if (
        !event.defaultPrevented &&
        !event.metaKey &&
        !event.ctrlKey &&
        !event.altKey &&
        !event.shiftKey &&
        event.button === 0
      ) {
        event.preventDefault();
        history.pushState({ synthetic: true }, "", p.href);
        update({ href: location.href });
      }
    },
  });
}
const nav = createSharedSidebarNavigation({
  ...diagnosticSidebarPorts(React, { jsx, jsxs, Fragment }),
  useMemoCache,
  window: browser,
  Link,
  routes,
});
function Probe() {
  context = nav.useSidebar();
  return jsx("output", {
    "data-state-probe": true,
    children: JSON.stringify({
      open: context.open,
      openMobile: context.openMobile,
      state: context.state,
    }),
  });
}
function Content() {
  const items = ["home", "explore", "leaderboard", "live"].map((key) => ({
    key,
    label: "Synthetic " + key,
    href: routes[key],
    icon: icons,
    isActive: nav.isNavigationActive(
      key,
      new URL(current.href).pathname,
      new URL(current.href).searchParams.get("feed"),
    ),
    dataTestId: "nav-" + key,
    onClick() {
      events.push({ kind: "navigate-callback", key });
    },
    isNew: key === "live",
  }));
  return jsxs(Fragment, {
    children: [
      jsx(nav.SidebarTrigger, {
        "data-testid": "outside-trigger",
        onClick(event) {
          events.push({
            kind: "trigger-callback",
            prevent: current.preventTrigger,
            deny: current.denyTrigger,
          });
          if (current.preventTrigger) event.preventDefault();
          if (current.denyTrigger)
            throw Error("SYNTHETIC trigger callback denial");
        },
      }),
      jsx(Probe, {}),
      jsx(nav.Sidebar, {
        collapsible: "icon",
        children: jsxs(Fragment, {
          children: [
            jsx(nav.SidebarHeader, {
              children: jsx("strong", { children: "Nav" }),
            }),
            jsx(nav.SidebarContent, {
              children: jsx(nav.NavGroup, { title: "Synthetic group", items }),
            }),
            jsx(nav.SidebarFooter, {
              children: jsx(nav.ActionList, {
                items: [
                  {
                    key: "safe-action",
                    label: "Synthetic readonly action",
                    icon: icons.line,
                    isLoading: false,
                    unreadCount: 12,
                    dataTestId: "safe-action",
                    onClick() {
                      events.push({ kind: "safe-action" });
                    },
                  },
                ],
              }),
            }),
            jsx(nav.SidebarRail, { "data-testid": "rail" }),
          ],
        }),
      }),
      jsx(nav.SidebarInset, {
        children: jsx("p", {
          children:
            "Synthetic caller body. No auth/account/support/native app or provider acquisition.",
        }),
      }),
    ],
  });
}
function App() {
  const [s, set] = React.useState({
    present: true,
    href: location.href,
    preventTrigger: false,
    denyTrigger: false,
    controlled: false,
    controlledOpen: false,
    denyControlled: true,
  });
  current = s;
  update = (patch) => set((old) => ({ ...old, ...patch }));
  const Provider = s.controlled ? nav.SidebarProvider : nav.SidebarController;
  return jsxs("main", {
    children: [
      jsx("h1", {
        children: "Synthetic original Sidebar/controller/navigation",
      }),
      jsx("p", {
        children:
          "Source-backed family; diagnostic Drawer/Slot/Tooltip/Link/style ports only.",
      }),
      s.present
        ? jsx(Provider, {
            defaultOpen: false,
            ...(s.controlled
              ? {
                  open: s.controlledOpen,
                  onOpenChange(value) {
                    events.push({
                      kind: "controlled-callback",
                      value,
                      accepted: !s.denyControlled,
                    });
                    if (!s.denyControlled)
                      set((old) => ({ ...old, controlledOpen: value }));
                  },
                }
              : {}),
            children: jsx(Content, {}),
          })
        : null,
    ],
  });
}
root = createRoot(document.getElementById("root"));
root.render(jsx(App, {}));
window.sharedSidebarFixture = {
  snapshot() {
    return {
      state: current,
      context: context && {
        open: context.open,
        openMobile: context.openMobile,
        state: context.state,
      },
      events,
      listeners: listeners.size,
      href: location.href,
    };
  },
  patch(patch) {
    update(patch);
  },
  toggleTwice() {
    context.toggleSidebar();
    context.toggleSidebar();
  },
  setDesktop(value) {
    context.setOpen(value);
  },
  setMobile(value) {
    context.setOpenMobile(value);
  },
  unmount() {
    root.unmount();
  },
};
