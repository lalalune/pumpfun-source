import React, {
  useState,
  useRef,
  useEffect,
  useCallback,
  useContext,
} from "../../packages/frontend/node_modules/react/index.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import { createBoardCoinHook } from "../../reconstruction/board-read-state/client.mjs";
import { createSearchCache } from "../../reconstruction/search-session/session.mjs";

// Explicit synthetic capability outputs. This is NOT503774's implementation.
const outputs = new Map(
  Object.entries({
    "synthetic-A1": [
      { mint: "synthetic-A1", name: "A1" },
      { mint: "synthetic-A2", name: "A2" },
      { mint: "synthetic-A3", name: "A3" },
    ],
    "synthetic-T1": [
      { mint: "synthetic-T1", name: "T1" },
      { mint: "synthetic-T2", name: "T2" },
      { mint: "synthetic-T3", name: "T3" },
    ],
    "synthetic-B1": [{ mint: "synthetic-B1", name: "B1" }],
  }),
);
const context = React.createContext(null);
let clock = 1000,
  events = [],
  rendered = null,
  mountSerial = 0,
  root,
  updateInput,
  updateContext,
  latest,
  savedRefetch;
const cache = createSearchCache({ now: () => clock });
const useSnapshot = () => useContext(context);
const hook = createBoardCoinHook({
  React: { useState, useRef, useEffect, useCallback },
  cache,
  baseUrl: location.origin,
  fetchResponse: async (url, init) => {
    const id = events.filter((e) => e.type === "fetch-start").length + 1;
    events.push({
      type: "fetch-start",
      id,
      pathAndQuery: new URL(url).pathname + new URL(url).search,
      credentials: init.credentials,
      headers: init.headers,
    });
    init.signal.addEventListener(
      "abort",
      () => events.push({ type: "abort", id }),
      { once: true },
    );
    try {
      const response = await fetch(url, init);
      events.push({ type: "fetch-response", id, status: response.status });
      return response;
    } catch (error) {
      events.push({ type: "fetch-error", id, name: error.name });
      throw error;
    }
  },
  parseBoard: function (payload) {
    events.push({
      type: "parse-port",
      argumentCount: arguments.length,
      payload,
    });
    if (!Array.isArray(payload.entries))
      throw Error("Synthetic port expected an entries array");
    const expected = outputs.get(payload.entries[0]?.m);
    if (!expected) throw Error("Unconfigured synthetic response capability");
    // Fixed opaque outputs, configured separately from the network response.
    // No original response-normalizer algorithm is implemented or qualified.
    return structuredClone(expected);
  },
  seedBoardCoins: function (coins) {
    events.push({
      type: "seed-port",
      argumentCount: arguments.length,
      mints: coins.map((c) => c.mint),
    });
  },
  nowMs: () => clock,
  AbortController,
  useViewerSnapshot: () => useSnapshot().viewer,
  useSessionSnapshot: () => useSnapshot().session,
  usePrimarySessionIdSnapshot: () => useSnapshot().primaryId,
  useVariant: () => useSnapshot().variant,
  useExposure: () => useSnapshot().exposure,
  useIpfsPrefix: () => ({ ipfsPrefix: useSnapshot().prefix }),
  requestIdentity: function (value) {
    events.push({
      type: "identity-port",
      argumentCount: arguments.length,
      syntheticInput: value ?? null,
    });
    return {
      deviceId: "synthetic-device",
      sessionId: value,
      sessionStartTimestampMs:
        value === "pump_session_0_synthetic" ? 0 : undefined,
    };
  },
  debounce: (callback, delay) => {
    events.push({ type: "debounce-port", delay });
    const result = () => {
      throw Error("Excluded search debounce must not execute in board domain");
    };
    result.cancel = () => events.push({ type: "cancel-search-port" });
    return result;
  },
  useLivePollInterval: (interval, enabled) => {
    events.push({ type: "poll-port", interval, enabled });
    if (enabled !== false)
      throw Error("Board domain must disable the LIVE interval port");
    return false;
  },
  timers: {
    setInterval: () => {
      events.push({ type: "unexpected-interval" });
      throw Error("No board polling");
    },
    clearInterval: () => events.push({ type: "clear-interval" }),
  },
  logger: {
    error: (...args) =>
      events.push({ type: "excluded-error", args: args.map(String) }),
  },
});
const initialInput = {
  sort: "featured",
  offset: 0,
  limit: 2,
  includeNsfw: false,
  order: "DESC",
  chain: "solana",
};
const initialContext = {
  viewer: { address: undefined, userId: undefined, authReady: false },
  session: { sessionData: undefined },
  primaryId: "pump_session_0_synthetic",
  variant: "social-terminal",
  exposure: {},
  prefix: "https://synthetic.invalid/ipfs/",
};
function Observer({ input }) {
  const result = hook(input);
  latest = result;
  useEffect(() => {
    const state = {
      coins: result.coins.map((c) => c.mint),
      servedCoins: result.servedCoins.map((c) => c.mint),
      loading: result.loading,
      error: result.error,
      hasMorePages: result.hasMorePages,
      requestKey: result.requestKey,
      rowsRequestKey: result.rowsRequestKey,
    };
    rendered = state;
    events.push({ type: "render-commit", state });
  });
  return React.createElement(
    "output",
    { id: "state" },
    JSON.stringify({
      coins: latest.coins.map((c) => c.mint),
      loading: latest.loading,
      error: latest.error,
    }),
  );
}
function App({ input: givenInput, scope: givenScope }) {
  const [input, setInput] = useState(givenInput),
    [scope, setScope] = useState(givenScope);
  updateInput = (patch) => setInput((old) => ({ ...old, ...patch }));
  updateContext = (patch) => setScope((old) => ({ ...old, ...patch }));
  useEffect(() => {
    mountSerial += 1;
    events.push({ type: "host-commit", serial: mountSerial });
  });
  return React.createElement(
    context.Provider,
    { value: scope },
    React.createElement(Observer, { input }),
  );
}
function mount(input = {}, scope = {}) {
  rendered = null;
  latest = null;
  root = createRoot(document.getElementById("root"));
  root.render(
    React.createElement(App, {
      input: { ...initialInput, ...input },
      scope: { ...initialContext, ...scope },
    }),
  );
}
window.boardHarness = {
  mount,
  render: (patch) => updateInput(patch),
  scope: (patch) => updateContext(patch),
  state: () => rendered,
  serial: () => mountSerial,
  events: () => structuredClone(events),
  setClock: (value) => {
    clock = value;
  },
  refetch: (options) => latest.refetch(options),
  fetchCoins: (...args) => latest.fetchCoins(...args),
  saveRefetch: () => {
    savedRefetch = latest.refetch;
  },
  callSavedRefetch: (options) => savedRefetch(options),
  setCoins: (value) => latest.setCoins(value),
  unmount: () => {
    root.unmount();
    events.push({ type: "host-unmounted" });
  },
  cache: () =>
    [...cache.entries.entries()].map(([key, value]) => ({
      key,
      storedAt: value.storedAt,
    })),
};
mount();
