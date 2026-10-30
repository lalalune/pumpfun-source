import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { verify } from "../scripts/original-shared-sidebar-navigation.mjs";
import { createSharedSidebarNavigation } from "../reconstruction/shared-sidebar-navigation/client.mjs";
import { diagnosticSidebarPorts } from "./fixtures/shared-sidebar-diagnostic-ports.mjs";
const require = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  React = require("react"),
  runtime = require("react/jsx-runtime"),
  { c: useMemoCache } = require("react/compiler-runtime"),
  { renderToString } = require("react-dom/server");
const routes = {
    home: "/",
    explore: "/explore",
    leaderboard: "/leaderboard",
    live: "/live",
  },
  Icon = (kind) => (props) =>
    runtime.jsx("svg", { "data-diagnostic-icon": kind, ...props }),
  pair = { fill: Icon("fill"), line: Icon("line") };
function fixture({ onOpenChange } = {}) {
  let context;
  const props = [];
  const caps = {
    ...diagnosticSidebarPorts(React, runtime),
    useMemoCache,
    routes,
    window: new Proxy(
      {},
      {
        get() {
          throw Error("SYNTHETIC browser read during SSR");
        },
      },
    ),
    Link: (p) => {
      props.push(p);
      return runtime.jsx("a", p);
    },
  };
  const nav = createSharedSidebarNavigation(caps);
  function Probe() {
    context = nav.useSidebar();
    return null;
  }
  return {
    nav,
    props,
    get context() {
      return context;
    },
    render(child, options = {}) {
      return renderToString(
        runtime.jsxs(nav.SidebarProvider, {
          onOpenChange,
          ...options,
          children: [runtime.jsx(Probe, {}), child],
        }),
      );
    },
    controller(child, defaultOpen) {
      return renderToString(
        runtime.jsx(nav.SidebarController, {
          defaultOpen,
          children: runtime.jsxs(React.Fragment, {
            children: [runtime.jsx(Probe, {}), child],
          }),
        }),
      );
    },
  };
}
test("45fullregions/all12publicexports/rootRSCadmission andactualController/ordinaryconsumer are authenticated", async () => {
  const c = await verify();
  assert.equal(c.retained.length, 45);
  assert.equal(Object.keys(c.publicSidebarExports).length, 12);
  assert.equal(c.witnesses.length, 8);
  assert.deepEqual(
    c.capturedRoot.layout.map((x) => x.defaultOpen),
    [false, false],
  );
  assert.equal(c.capturedRoot.controllerExportString, "SidebarController");
});
test("actualSSRcontroller forwards capturedfalse/defaulttrue without browser/storage reads; complete frame and both CSSresponsive structures preserved", () => {
  const f = fixture(),
    N = f.nav;
  const h = f.controller(
    runtime.jsx(N.Sidebar, {
      collapsible: "icon",
      children: runtime.jsxs(React.Fragment, {
        children: [
          runtime.jsx(N.SidebarHeader, { children: "header" }),
          runtime.jsx(N.SidebarContent, { children: "body" }),
          runtime.jsx(N.SidebarFooter, { children: "footer" }),
          runtime.jsx(N.SidebarRail, {}),
        ],
      }),
    }),
    false,
  );
  assert.equal(f.context.open, false);
  assert.equal(f.context.openMobile, false);
  assert.equal(f.context.state, "collapsed");
  assert.match(h, /data-app-shell=""/);
  assert.match(h, /--sidebar-width:13rem/);
  assert.match(h, /--sidebar-width-icon:3.5rem/);
  assert.match(h, /--sidebar-width:18rem/);
  assert.match(h, /data-mobile="true"/);
  assert.match(h, /data-collapsible="icon"/);
  assert.equal(
    fixture().controller(null, undefined).includes("data-app-shell"),
    true,
  );
  const g = fixture();
  g.render(null);
  assert.equal(g.context.open, true);
});
test("controlled functional setter uses capturedopen and calls supplied callback, not a new freshvalue/store policy", () => {
  const calls = [],
    f = fixture({ onOpenChange: (value) => calls.push(value) });
  f.render(null, { open: false });
  f.context.setOpen((x) => !x);
  f.context.setOpen((x) => !x);
  assert.deepEqual(calls, [true, true]);
  assert.equal(f.context.open, false);
});
test("useSidebar outside actualProvider fails with originalerror; noncollapsible frame retains explicit none branch", () => {
  const f = fixture();
  function Outside() {
    f.nav.useSidebar();
    return null;
  }
  assert.throws(
    () => renderToString(runtime.jsx(Outside, {})),
    /useSidebar must be used within a SidebarProvider/,
  );
  const h = f.render(
    runtime.jsx(f.nav.Sidebar, { collapsible: "none", children: "plain" }),
  );
  assert.doesNotMatch(h, /data-mobile/);
  assert.match(h, /plain/);
});
test("ordinarygroup activeicons/aria-current/badge/action/empty andinternalLink props are forwarded unchanged", () => {
  const f = fixture(),
    click = () => {},
    items = [
      {
        key: "home",
        label: "Synthetic home",
        href: "/",
        icon: pair,
        isActive: true,
        isNew: true,
        onClick: click,
        action: runtime.jsx("span", { children: "Synthetic action" }),
      },
      {
        key: "live",
        label: "Synthetic live",
        href: "/live",
        icon: pair,
        isActive: false,
        badge: 0,
      },
    ];
  const h = f.render(
    runtime.jsx(f.nav.NavGroup, { title: "Synthetic group", items }),
  );
  assert.match(h, /data-diagnostic-icon="fill"/);
  assert.match(h, /data-diagnostic-icon="line"/);
  assert.match(h, /aria-current="page"/);
  assert.equal(f.props[0].onClick, click);
  assert.equal(f.props[0].href, "/");
  assert.match(h, /Synthetic action/);
  assert.equal(
    fixture()
      .render(runtime.jsx(f.nav.NavGroup, { items: [] }))
      .includes('data-sidebar="menu"'),
    false,
  );
});
test("actionlist fullhref/button/loading/unread coercion/external guards andtooltip override retain sourceconditions", () => {
  const f = fixture(),
    N = f.nav,
    icon = Icon("action");
  const h = f.render(
    runtime.jsxs(React.Fragment, {
      children: [
        runtime.jsx(N.ActionList, {
          items: [
            {
              key: "a",
              label: "Synthetic action",
              icon,
              onClick() {},
              isLoading: true,
              unreadCount: "12",
              dataTestId: "safe-action",
            },
            {
              key: "b",
              label: "Synthetic external",
              icon,
              href: "https://synthetic.invalid/",
              external: true,
              isActive: true,
            },
          ],
        }),
        runtime.jsx(N.SidebarMenuButton, {
          tooltip: { children: "override", hidden: false },
          children: "button",
        }),
      ],
    }),
  );
  assert.match(h, /aria-busy="true"/);
  assert.match(h, /safe-action-spinner/);
  assert.match(h, /9\+/);
  assert.match(h, /target="_blank"/);
  assert.match(h, /rel="noopener noreferrer"/);
  assert.match(h, /data-diagnostic-tooltip="true" data-side="right">override/);
});
test("actual primaryactive-policy uses exactpathboundary/homeexact/watchlistrowvisibility semantics", () => {
  const { nav } = fixture();
  assert.equal(nav.pathMatches("/", "/leaderboard"), false);
  assert.equal(nav.pathMatches("/live", "/livechat"), false);
  assert.equal(nav.pathMatches("/live", "/live/channel"), true);
  assert.equal(nav.pathMatches("/live", ""), false);
  assert.equal(nav.isNavigationActive("home", "/", null), true);
  assert.equal(
    nav.isNavigationActive("leaderboard", "/leaderboard/round", null),
    true,
  );
  assert.equal(
    nav.isNavigationActive("watchlist", "/explore", "watchlist"),
    true,
  );
  assert.equal(
    nav.isNavigationActive("explore", "/explore", "watchlist"),
    false,
  );
  assert.equal(
    nav.isNavigationActive("explore", "/explore", "watchlist", {
      watchlistRowShown: false,
    }),
    true,
  );
  assert.equal(
    nav.isNavigationActive("watchlist", "/explore", "watchlist", {
      watchlistRowShown: false,
    }),
    false,
  );
});
