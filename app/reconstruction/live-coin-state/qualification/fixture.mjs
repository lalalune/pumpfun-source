// Authored standalone React host. No app route, transport or original provider.
import * as React from "react";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import { c as compiler } from "react/compiler-runtime";
import {
  createFrameBatchRuntime,
  createLiveCoinState,
  batchVariantHashes,
} from "../client.mjs";
import { manualEnvironment, syntheticBoundStore } from "./ports.mjs";
let root,
  current,
  serial = 0;
const element = React.createElement;
function nativeEnvironment() {
  const handles = new Map(),
    errors = [];
  let rafCalls = 0;
  return {
    environment: {
      window: {
        requestAnimationFrame(fn) {
          const id = window.requestAnimationFrame((t) => {
            handles.delete(`r${id}`);
            fn(t);
          });
          handles.set(`r${id}`, "raf");
          rafCalls++;
          return id;
        },
        cancelAnimationFrame(id) {
          handles.delete(`r${id}`);
          window.cancelAnimationFrame(id);
        },
      },
      document,
      setTimeout(fn, ms) {
        const id = window.setTimeout(() => {
          handles.delete(`t${id}`);
          fn();
        }, ms);
        handles.set(`t${id}`, "timeout");
        return id;
      },
      clearTimeout(id) {
        handles.delete(`t${id}`);
        window.clearTimeout(id);
      },
    },
    clock: Date,
    logger: { error: (...args) => errors.push(args) },
    errors,
    handles: () => [...handles.values()],
    rafCalls: () => rafCalls,
  };
}
function Pause({ frame, id }) {
  frame.usePause(id);
  return null;
}
function Host({ state }) {
  const [pauses, setPauses] = React.useState(state.initialPauses);
  const cap = state.live.useMarketCap("a"),
    coin = state.live.useCoin("a"),
    many = state.live.useCoins(state.mints);
  const sameMany = state.lastMany === many;
  state.renders++;
  state.lastMany = many;
  React.useEffect(() => {
    state.committed = { cap, coin, many, sameMany, pauses };
    state.mounted = true;
  });
  React.useEffect(
    () => () => {
      state.mounted = false;
    },
    [],
  );
  return element(
    "main",
    null,
    element("h1", null, "Synthetic queued state host"),
    element(
      "p",
      null,
      "Injected provider and scheduler. No website/service compatibility.",
    ),
    element(
      "output",
      { "data-testid": "cap" },
      cap === undefined ? "undefined" : String(cap),
    ),
    element("output", { "data-testid": "pauses" }, String(pauses)),
    element(
      "button",
      {
        onClick: () => {
          state.api.setCoin({ mint: "a", usdMarketCap: 2 });
          state.api.updateCoin("a", { usdMarketCap: 9 });
        },
      },
      "Queue A",
    ),
    element(
      "button",
      { onClick: () => state.api.setCoin({ mint: "b", usdMarketCap: 4 }) },
      "Queue unrelated",
    ),
    element(
      "button",
      { onClick: () => state.host.advance(16) },
      "Advance artificial frame",
    ),
    element(
      "button",
      { onClick: () => setPauses((n) => Math.max(0, n - 1)) },
      "Release one pause",
    ),
    ...Array.from({ length: pauses }, (_, id) =>
      element(Pause, { key: id, id, frame: state.frame }),
    ),
  );
}
function observe() {
  const s = current;
  if (!s) return null;
  const a = s.committed;
  return {
    instance: s.id,
    mounted: s.mounted,
    renders: s.renders,
    cap: a?.cap ?? null,
    manyMints: a?.many.map((c) => c?.mint ?? null),
    sameMany: a?.sameMany,
    pauses: a?.pauses,
    committed: s.api.getCoin("a") ?? null,
    pending: s.api.peekCoin("a") ?? null,
    handles: s.host.handles(),
    rafCalls: s.host.rafCalls?.() ?? null,
    errors: s.host.errors.length,
  };
}
function reset({
  variant = batchVariantHashes[0],
  mode = "manual",
  pauses = 0,
} = {}) {
  if (root) {
    flushSync(() => root.unmount());
    root = null;
  }
  const host = mode === "native" ? nativeEnvironment() : manualEnvironment();
  const frame = createFrameBatchRuntime({ variant, React, compiler, ...host });
  const live = createLiveCoinState({
    React,
    compiler,
    createBoundStore: syntheticBoundStore(React),
    frameBatch: frame,
    clock: host.clock,
  });
  current = {
    id: ++serial,
    host,
    frame,
    live,
    api: live.store.getState(),
    initialPauses: pauses,
    mints: ["a", "absent", "a"],
    renders: 0,
    mounted: false,
  };
  root = createRoot(document.getElementById("root"));
  flushSync(() => root.render(element(Host, { state: current })));
  return observe();
}
window.harness = {
  reset,
  observe,
  unmount() {
    flushSync(() => root.unmount());
    root = null;
    return observe();
  },
};
