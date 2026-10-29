// Authored standalone host: real React with injected local query/state/frame capabilities.
import * as React from "react";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import {
  createMarketActivityState,
  queryVariants,
  storeVariants,
} from "../client.mjs";
import { createHelperPort, helperVariants } from "./helper-ports.mjs";
import { localStatePorts } from "./ports.mjs";
const element = React.createElement;
let root,
  current,
  serial = 0;
function Host({ state }) {
  const [revision, setRevision] = React.useState(0);
  state.bump = () => setRevision((n) => n + 1);
  const read = state.boundary.useMarketActivity(state.mints, state.params);
  React.useEffect(() => {
    state.latest = read;
    state.mounted = true;
    state.revision = revision;
  });
  React.useEffect(
    () => () => {
      state.mounted = false;
    },
    [],
  );
  async function run(kind) {
    const options = state.host.options();
    if (kind === "defer") {
      state.defer = true;
      const promise = options.queryFn({
        queryKey: options.queryKey,
        signal: state.signal,
      });
      promise.then((value) => {
        state.responses.push(value);
        state.bump();
      });
      state.bump();
      return;
    }
    const value = await options.queryFn({
      queryKey: options.queryKey,
      signal: state.signal,
    });
    state.responses.push(value);
    if (kind === "normal") state.host.setResult({ data: value });
    state.bump();
  }
  return element(
    "main",
    null,
    element("h1", null, "Synthetic activity query and queued-store host"),
    element(
      "p",
      null,
      "Injected capabilities; no service, mounted website or financial qualification.",
    ),
    element(
      "button",
      { onClick: () => run("normal") },
      "Run request capability",
    ),
    element(
      "button",
      { onClick: () => state.host.flushFrames() },
      "Flush artificial frame",
    ),
    element(
      "button",
      {
        onClick: () =>
          state.boundary.setMarketActivity({ a: { "24h": { numTxs: 2 } } }),
      },
      "Patch unselected metric",
    ),
    element("button", { onClick: () => state.bump() }, "Render again"),
    element(
      "button",
      {
        onClick: () =>
          state.boundary.setMarketActivity({ a: { "24h": { volumeUSD: 3 } } }),
      },
      "Patch selected metric",
    ),
    element(
      "button",
      {
        onClick: () => {
          state.params = { readBack: false };
          state.bump();
        },
      },
      "Readback off",
    ),
    element(
      "button",
      {
        onClick: async () => {
          await read.refetchMints(["b"]);
          state.bump();
        },
      },
      "Refetch missing mint",
    ),
    element(
      "button",
      { onClick: () => run("defer") },
      "Start deferred request",
    ),
    element(
      "button",
      {
        onClick: () => {
          state.deferred[1].resolve({ a: { "24h": { volumeUSD: 2 } } });
        },
      },
      "Resolve second",
    ),
    element(
      "button",
      {
        onClick: () => {
          state.host.setTime(2_000_000);
          state.deferred[0].resolve({ a: { "24h": { volumeUSD: 1 } } });
        },
      },
      "Resolve first",
    ),
    element(
      "button",
      {
        onClick: () => {
          state.host.cacheEntries.push({
            queryKey: ["marketActivity", "warm"],
            state: {
              data: { a: { "24h": { volumeUSD: 7 } } },
              dataUpdatedAt: 2_000_000,
              isInvalidated: false,
            },
          });
          state.defer = false;
          run("warm");
        },
      },
      "Warm cache",
    ),
    element(
      "output",
      { "data-testid": "volume" },
      String(read.marketActivity.a?.["24h"]?.volumeUSD ?? "missing"),
    ),
  );
}
function reset({
  queryVariant = queryVariants[0].sha256,
  storeVariant = storeVariants[0].sha256,
  helperVariant = helperVariants[0].sha256,
} = {}) {
  if (root) {
    flushSync(() => root.unmount());
    root = null;
  }
  const state = {
    id: ++serial,
    selected: { queryVariant, storeVariant, helperVariant },
    mints: ["a"],
    params: {},
    mounted: false,
    responses: [],
    deferred: [],
    defer: false,
    microtasksQueued: 0,
    microtasksExecuted: 0,
    listeners: 0,
    refs: new WeakMap(),
    refSerial: 0,
    signal: new AbortController().signal,
  };
  const host = localStatePorts({ React, nativeMicrotasks: true });
  state.host = host;
  const createBoundStore = host.ports.createBoundStore;
  host.ports.createBoundStore = () => (initialize) =>
    createBoundStore()((set, get, api) => {
      const subscribe = api.subscribe;
      api.subscribe = (listener) => {
        state.listeners++;
        const off = subscribe(listener);
        return () => {
          state.listeners--;
          off();
        };
      };
      return initialize(set, get, api);
    });
  host.ports.queueMicrotask = (fn) => {
    state.microtasksQueued++;
    queueMicrotask(() => {
      fn();
      state.microtasksExecuted++;
    });
  };
  host.ports.fetchBatch = (mints, options) => {
    host.requests.push({ mints, options });
    if (state.defer)
      return new Promise((resolve) => state.deferred.push({ resolve }));
    return Promise.resolve({
      a: { "24h": { volumeUSD: 10, priceChangePercent: 2, numTxs: 1 } },
    });
  };
  state.boundary = createMarketActivityState({
    ...state.selected,
    ...host.ports,
    helpers: createHelperPort(helperVariant),
  });
  current = state;
  root = createRoot(document.getElementById("root"));
  flushSync(() => root.render(element(Host, { state })));
  return observe();
}
function observe() {
  const s = current;
  if (!s) return null;
  const projection = s.latest?.marketActivity;
  let reference = null;
  if (projection) {
    if (!s.refs.has(projection)) s.refs.set(projection, ++s.refSerial);
    reference = s.refs.get(projection);
  }
  return {
    instance: s.id,
    selected: s.selected,
    mounted: s.mounted,
    reference,
    read: projection ?? null,
    committed: s.boundary.store.getState().marketActivity,
    responses: [...s.responses],
    requests: s.host.requests.map((r) => ({
      mints: r.mints,
      intervals: r.options.intervals,
      metrics: r.options.metrics,
      hasSignal: r.options.signal === s.signal,
    })),
    sequence: [...s.host.sequence],
    pending: s.host.batches[0].size,
    microtasksQueued: s.microtasksQueued,
    microtasksExecuted: s.microtasksExecuted,
    listeners: s.listeners,
    revision: s.revision,
  };
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
