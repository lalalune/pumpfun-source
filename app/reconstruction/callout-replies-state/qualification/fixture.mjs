import React from "react";
import { c as useMemoCache } from "react/compiler-runtime";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import { createCalloutRepliesReadState } from "../client.mjs";
import { createOverlayContext } from "./ports.mjs";
const el = React.createElement,
  check = (p, label) => {
    if (!p) throw Error(label);
  },
  same = (a, b, label) =>
    check(
      JSON.stringify(a) === JSON.stringify(b),
      label + ":" + JSON.stringify(a),
    );
const row = (replyId, extra = {}) => ({
  replyId,
  calloutId: "call",
  userId: "Alice",
  content: " text ",
  createdAt: 1,
  likeCount: 0,
  likedByViewer: false,
  ...extra,
});
const raw = (id, extra = {}) => ({
  id,
  userId: "Alice",
  content: "text",
  createdAt: "2026-01-01",
  likeCount: 2,
  ...extra,
});
const rec = (reply, extra = {}) => ({
  reply,
  isAuthorReply: true,
  parentReplyId: null,
  registeredAtMs: 1000000,
  ...extra,
});
let active, root;
async function until(fn) {
  const start = performance.now();
  while (!fn()) {
    if (performance.now() - start > 3000)
      throw Error("finite React condition timeout");
    await new Promise((r) => setTimeout(r, 5));
  }
}
function deferred() {
  let resolve;
  const promise = new Promise((r) => (resolve = r));
  return { promise, resolve };
}
function close() {
  if (root) {
    flushSync(() => root.unmount());
    root = null;
  }
  if (!active)
    return { overlayListeners: 0, queryListeners: 0, rootChildren: 0 };
  return {
    overlayListeners: active.overlay.listeners.size,
    queryListeners: [...active.cells.values()].reduce(
      (n, c) => n + c.listeners.size,
      0,
    ),
    rootChildren: document.getElementById("root").childElementCount,
  };
}
function mount({
  input = { mint: "m", calloutId: "call" },
  overlay = createOverlayContext(),
  data,
  reader = async () => ({ replies: [] }),
} = {}) {
  if (root) {
    const cleaned = close();
    same(
      cleaned,
      { overlayListeners: 0, queryListeners: 0, rootChildren: 0 },
      "prior context cleanup",
    );
  }
  const s = {
    input,
    overlay,
    data,
    reader,
    cells: new Map(),
    calls: [],
    out: null,
    now: 1000000,
    renders: 0,
    snapshots: [],
  };
  active = s;
  function useQuery(options) {
    const key = JSON.stringify(options.queryKey);
    let cell = s.cells.get(key);
    if (!cell) {
      cell = {
        listeners: new Set(),
        started: false,
        options,
        snapshot: {
          data: s.data,
          isLoading: false,
          error: null,
          isError: false,
        },
      };
      const publish = (patch) => {
        cell.snapshot = { ...cell.snapshot, ...patch };
        for (const fn of cell.listeners) fn();
      };
      cell.setData = (data) => publish({ data });
      cell.refetch = async () => {
        cell.started = true;
        publish({ isLoading: true, error: null, isError: false });
        try {
          const data = await cell.options.queryFn({
            signal: new AbortController().signal,
          });
          publish({ data, isLoading: false });
          return data;
        } catch (error) {
          publish({ error, isLoading: false, isError: true });
          throw error;
        }
      };
      s.cells.set(key, cell);
    }
    cell.options = options;
    s.lastOptions = options;
    s.cell = cell;
    const subscribe = React.useCallback(
      (fn) => {
        cell.listeners.add(fn);
        return () => cell.listeners.delete(fn);
      },
      [cell],
    );
    const get = React.useCallback(() => cell.snapshot, [cell]);
    const snapshot = React.useSyncExternalStore(subscribe, get, get);
    React.useEffect(() => {
      if (options.enabled && !cell.started) void cell.refetch().catch(() => {});
    }, [cell, options.enabled]);
    return { ...snapshot, refetch: cell.refetch };
  }
  s.api = createCalloutRepliesReadState({
    React,
    useMemoCache,
    useQuery,
    getContractClient: () => async (operation, options) => {
      s.calls.push({
        operation,
        params: options.params,
        query: options.query,
        credentials: options.credentials,
        headers: options.headers,
        hasSignal: options.signal instanceof AbortSignal,
      });
      let result = await s.reader(operation, options);
      if (result instanceof Response) {
        for (const hook of options.hooks.afterResponse) {
          const replacement = await hook({ synthetic: true }, options, result);
          if (replacement) result = replacement;
        }
        return result.json();
      }
      return result;
    },
    clock: { now: () => s.now, parse: Date.parse },
    Response,
    overlay,
  });
  function App() {
    const [, bump] = React.useReducer((n) => n + 1, 0);
    s.bump = bump;
    s.renders++;
    s.out = s.api.useReplies(s.input);
    const view = {
      rows: s.out.replies.map((r) => ({
        id: r.replyId,
        liked: r.likedByViewer,
        content: r.content,
      })),
      loading: s.out.isLoading,
      error: s.out.error?.message ?? s.out.error ?? null,
      version: s.api.getOverlayVersion(),
    };
    s.snapshots.push(view);
    return el(
      "main",
      null,
      el("h1", null, "Injected replies read context"),
      el("output", { "data-testid": "view" }, JSON.stringify(view)),
      el(
        "button",
        { onClick: () => void s.out.refetch().catch(() => {}) },
        "Refetch",
      ),
    );
  }
  root = createRoot(document.getElementById("root"));
  flushSync(() => root.render(el(App)));
  return s;
}
const observation = (s) => ({
  view: JSON.parse(document.querySelector("[data-testid=view]").textContent),
  calls: s.calls,
  queryKey: s.lastOptions.queryKey,
  renders: s.renders,
  snapshots: s.snapshots,
  pendingContext: [...s.overlay.pendingReplies],
  likedContext: [...s.overlay.likedByViewer],
  listeners: {
    overlay: s.overlay.listeners.size,
    query: [...s.cells.values()].reduce((n, c) => n + c.listeners.size, 0),
  },
});
window.repliesFixture = {
  names: [
    "deferred-list-and-overlay",
    "pending-ttl-scope-parent",
    "version-notification-memo",
    "response-error-404-refetch",
    "disabled-guard-and-defaults",
    "module-context-isolation",
  ],
  async run(name) {
    if (name === "deferred-list-and-overlay") {
      const gate = deferred(),
        context = createOverlayContext();
      context.pendingReplies.set("m|call", [
        rec(row("pending-local")),
        rec(row("real-local")),
      ]);
      context.likedByViewer.set("server", true);
      const s = mount({ overlay: context, reader: () => gate.promise });
      await until(() => s.calls.length === 1 && s.out.isLoading);
      same(
        s.out.replies.map((r) => r.replyId),
        ["pending-local", "real-local"],
        "pending visible while loading",
      );
      gate.resolve({ replies: [raw("server"), raw("server")] });
      await until(
        () => !s.out.isLoading && s.out.replies[0]?.replyId === "server",
      );
      same(
        s.out.replies.map((r) => r.replyId),
        ["server", "server", "real-local"],
        "wire duplicates and pending text dedup",
      );
      check(
        s.out.replies[0].likedByViewer === true,
        "read-only like projection",
      );
      check(
        s.calls[0].hasSignal && s.calls[0].credentials === "include",
        "actual source signal/options forwarded",
      );
      return observation(s);
    }
    if (name === "pending-ttl-scope-parent") {
      const context = createOverlayContext();
      context.pendingReplies.set("m|call", [
        rec(row("boundary"), { registeredAtMs: 700000 }),
        rec(row("expired"), { registeredAtMs: 699999 }),
        rec(row("other"), { isAuthorReply: false }),
        rec(row("child"), { parentReplyId: "parent" }),
      ]);
      const s = mount({
        input: { mint: "m", calloutId: "call", enabled: false },
        overlay: context,
        data: [],
      });
      same(
        s.out.replies.map((r) => r.replyId),
        ["boundary"],
        "inclusive TTL/root author filter",
      );
      check(
        context.pendingReplies.get("m|call").length === 3,
        "prune exact supplied context",
      );
      flushSync(() => {
        s.input = { ...s.input, scope: "all" };
        s.bump();
      });
      same(
        s.out.replies.map((r) => r.replyId),
        ["boundary", "other"],
        "all includes nonauthor but excludes child",
      );
      check(s.calls.length === 0, "disabled does not acquire reader");
      return observation(s);
    }
    if (name === "version-notification-memo") {
      const context = createOverlayContext(),
        data = [row("a")],
        s = mount({
          input: { mint: "m", calloutId: "call", enabled: false },
          overlay: context,
          data,
        });
      const first = s.out,
        renders = s.renders;
      context.likedByViewer.set("a", true);
      flushSync(() => s.api.notifyOverlayChange());
      check(s.renders > renders, "real subscription caused React render");
      check(
        s.out === first && s.out.replies === data,
        "source ignored-version memo preserves prior result",
      );
      check(s.api.getOverlayVersion() === 1, "actual notifier counter");
      flushSync(() => s.cell.setData([...data]));
      check(
        s.out.replies[0].likedByViewer === true && s.out.replies !== data,
        "new data identity recomputes projection",
      );
      return observation(s);
    }
    if (name === "response-error-404-refetch") {
      let mode = "503";
      const s = mount({
        reader: async () =>
          new Response(
            mode === "404"
              ? "malformed-body"
              : JSON.stringify(
                  mode === "ok"
                    ? { replies: [raw("a")] }
                    : { message: "synthetic" },
                ),
            {
              status: mode === "503" ? 503 : mode === "404" ? 404 : 200,
              headers: { "Content-Type": "application/json" },
            },
          ),
      });
      await until(() => s.out.isError);
      check(
        s.out.error instanceof Error &&
          s.out.error.message === "Failed to fetch callout replies: 503",
        "plain source error propagated",
      );
      mode = "404";
      await s.out.refetch();
      await until(() => !s.out.isError && !s.out.isLoading);
      same(
        s.out.replies,
        [],
        "actual native Response404 replacement before parsing malformed body",
      );
      mode = "ok";
      await s.out.refetch();
      await until(() => s.out.replies.length === 1);
      check(!s.out.error, "success recovery");
      return observation(s);
    }
    if (name === "disabled-guard-and-defaults") {
      const s = mount({
        input: { mint: "", calloutId: "", refetchIntervalMs: 0 },
        data: [],
      });
      check(
        s.lastOptions.enabled === false && s.lastOptions.refetchInterval === 0,
        "source enabled/zero interval",
      );
      same(
        s.lastOptions.queryKey,
        ["callouts", "replies", "", "", "author"],
        "keys preserve empty IDs",
      );
      let error;
      try {
        s.lastOptions.queryFn({ signal: new AbortController().signal });
      } catch (e) {
        error = e;
      }
      check(
        error?.message === "mint and calloutId required",
        "source callback rejects synchronously",
      );
      check(s.calls.length === 0, "guard skipped client");
      check(
        s.lastOptions.staleTime === 15000 &&
          s.lastOptions.gcTime === 300000 &&
          !s.lastOptions.refetchOnWindowFocus &&
          !s.lastOptions.refetchIntervalInBackground,
        "exact query policy",
      );
      return observation(s);
    }
    if (name === "module-context-isolation") {
      const a = createOverlayContext();
      a.pendingReplies.set("m|call", [rec(row("a"))]);
      a.likedByViewer.set("a", true);
      const s = mount({
        input: { mint: "m", calloutId: "call", enabled: false },
        overlay: a,
        data: [],
      });
      check(
        s.out.replies[0].likedByViewer === true,
        "first context primed values",
      );
      const first = observation(s),
        cleaned = close();
      same(
        cleaned,
        { overlayListeners: 0, queryListeners: 0, rootChildren: 0 },
        "first context cleanup",
      );
      const b = createOverlayContext(),
        t = mount({
          input: { mint: "m", calloutId: "call", enabled: false },
          overlay: b,
          data: [],
        });
      same(
        t.out.replies,
        [],
        "separate constructor context has no first context values",
      );
      check(
        t.api.getOverlayVersion() === 0,
        "local source version fresh per explicit constructor",
      );
      return { first, second: observation(t), firstCleaned: cleaned };
    }
    throw Error("unknown finite case");
  },
  cleanup: close,
};
