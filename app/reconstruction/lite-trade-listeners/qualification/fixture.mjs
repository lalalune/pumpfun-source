// Authored standalone host: real React, injected local provider/events, no connection.
import * as React from "react";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import { createLiteTradeHooks, protocolVariantHashes } from "../client.mjs";
import { localCapabilities } from "./ports.mjs";
let root,
  current,
  serial = 0;
const element = React.createElement;
class Clock extends Date {
  static now() {
    return 12345;
  }
}
function Subscriber({ state, label, mints, enabled, coalesce }) {
  const callback = React.useCallback(
    (event) => {
      state.events.push(`${label}:${event.seq}`);
      state.bump();
    },
    [state, label],
  );
  state.client.useSubscriptions({
    mints,
    isEnabled: enabled,
    coalesce,
    onLiteTrade: callback,
  });
  return null;
}
function Live({ state, mints, enabled }) {
  state.client.useLiteTrades(mints, enabled);
  return null;
}
function Host({ state }) {
  const [revision, setRevision] = React.useState(0),
    [second, setSecond] = React.useState(false),
    [label, setLabel] = React.useState("one"),
    [enabled, setEnabled] = React.useState(true),
    [mint, setMint] = React.useState("a");
  state.bump = () => setRevision((n) => n + 1);
  const mints = React.useMemo(() => (mint ? [mint] : []), [mint]);
  React.useEffect(() => {
    state.mounted = true;
    state.renderedRevision = revision;
    state.controls = { second, label, enabled, mint };
  });
  React.useEffect(
    () => () => {
      state.mounted = false;
    },
    [],
  );
  function readiness(value) {
    state.ports.setReady(value);
    state.bump();
  }
  function active(value) {
    state.ports.setActive(value);
    state.bump();
  }
  return element(
    "main",
    null,
    element("h1", null, "Synthetic lite-trade listener host"),
    element(
      "p",
      null,
      "Injected local capabilities only; no connection, auth or service.",
    ),
    element("button", { onClick: () => setSecond(true) }, "Mount second"),
    element("button", { onClick: () => setSecond(false) }, "Unmount second"),
    element(
      "button",
      { onClick: () => setLabel("updated") },
      "Change callback",
    ),
    element(
      "button",
      { onClick: () => state.ports.emit("a", { seq: 1 }) },
      "Emit one",
    ),
    element(
      "button",
      { onClick: () => state.ports.emit("a", { seq: 2 }) },
      "Emit two",
    ),
    element("button", { onClick: () => readiness(true) }, "Ready"),
    element("button", { onClick: () => active(false) }, "Inactive"),
    element("button", { onClick: () => active(true) }, "Active"),
    element("button", { onClick: () => setEnabled(false) }, "Disable"),
    element("button", { onClick: () => setEnabled(true) }, "Enable"),
    element("button", { onClick: () => setMint("b") }, "Mint B"),
    element("button", { onClick: () => setMint("") }, "Empty mints"),
    element(
      "button",
      {
        onClick: () =>
          state.ports.emit("a", {
            mint: "a",
            marketCap: "9",
            priceUsd: "2.5",
            timestamp: "2024-01-01T00:00:00Z",
            type: "buy",
          }),
      },
      "Emit valid trade",
    ),
    element(
      "button",
      { onClick: () => state.ports.emit("a", { mint: "a", marketCap: 0 }) },
      "Emit ignored trade",
    ),
    element(
      "button",
      {
        onClick: () =>
          state.ports.emit("a", {
            mint: "a",
            marketCap: 7,
            priceUsd: 0,
            timestamp: 0,
            type: "BUY",
          }),
      },
      "Emit lower trade",
    ),
    element("output", { "data-testid": "events" }, state.events.join(",")),
    element("output", { "data-testid": "second" }, String(second)),
    state.kind === "live"
      ? element(Live, { state, mints, enabled })
      : element(
          React.Fragment,
          null,
          element(Subscriber, {
            state,
            label,
            mints,
            enabled,
            coalesce: "latest",
          }),
          second
            ? element(Subscriber, {
                state,
                label: "two",
                mints,
                enabled,
                coalesce: "none",
              })
            : null,
        ),
  );
}
function observe() {
  if (!current) return null;
  return {
    instance: current.id,
    mounted: current.mounted,
    controls: current.controls,
    events: [...current.events],
    ...current.ports.observe(),
  };
}
window.harness = {
  reset({
    protocolVariant = protocolVariantHashes[0],
    kind = "subscriptions",
    ready = true,
  } = {}) {
    if (root) {
      flushSync(() => root.unmount());
      root = null;
    }
    const ports = localCapabilities();
    ports.DatePort = Clock;
    ports.setReady(ready);
    ports.coins.set("a", { usdAthMarketCap: 8 });
    const state = { id: ++serial, ports, kind, events: [], mounted: false };
    const update = ports.storeState.updateCoin;
    ports.storeState.updateCoin = (...args) => {
      update(...args);
      state.bump();
    };
    state.client = createLiteTradeHooks({ protocolVariant, React, ...ports });
    current = state;
    root = createRoot(document.getElementById("root"));
    flushSync(() => root.render(element(Host, { state })));
    return observe();
  },
  observe,
  unmount() {
    flushSync(() => root.unmount());
    root = null;
    return observe();
  },
};
