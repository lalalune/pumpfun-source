// Authored qualification capabilities; React/provider portions reused from proposed1870/1881.
// These are not recovered providers, query engines or frame schedulers.
export function manualReact() {
  const instances = new Map();
  let current;
  function memo(create, deps) {
    const index = current.cursor++,
      old = current.slots[index];
    if (
      !old ||
      old.deps.length !== deps.length ||
      deps.some((v, i) => !Object.is(v, old.deps[i]))
    ) {
      current.slots[index] = { value: create(), deps };
    }
    return current.slots[index].value;
  }
  function commit(instance) {
    const tasks = instance.pending;
    instance.pending = [];
    for (const fn of tasks) fn();
  }
  return {
    React: {
      useRef(value) {
        const index = current.cursor++;
        return (
          current.slots[index] ?? (current.slots[index] = { current: value })
        );
      },
      useMemo: memo,
      useCallback: (value, deps) => memo(() => value, deps),
      useEffect(fn, deps) {
        const owner = current,
          index = owner.cursor++,
          old = owner.slots[index];
        if (
          !old ||
          old.deps.length !== deps.length ||
          deps.some((v, i) => !Object.is(v, old.deps[i]))
        ) {
          owner.pending.push(() => {
            old?.cleanup?.();
            owner.slots[index] = { deps, cleanup: fn() };
          });
        }
      },
    },
    render(id, fn, { effects = true } = {}) {
      const instance = instances.get(id) ?? {
        slots: [],
        cursor: 0,
        pending: [],
      };
      instances.set(id, instance);
      instance.cursor = 0;
      current = instance;
      try {
        const result = fn();
        current = undefined;
        if (effects) commit(instance);
        return result;
      } finally {
        current = undefined;
      }
    },
    commit(id) {
      commit(instances.get(id));
    },
    unmount(id) {
      const instance = instances.get(id);
      for (const slot of instance?.slots ?? []) slot.cleanup?.();
      instances.delete(id);
    },
  };
}

export function syntheticBoundStore(React) {
  return () => (initialize) => {
    let state, initial;
    const listeners = new Set();
    const api = {
      getState: () => state,
      getInitialState: () => initial,
      setState(update, replace) {
        const next = typeof update === "function" ? update(state) : update;
        if (Object.is(next, state)) return;
        const old = state;
        state =
          (replace ?? (typeof next !== "object" || next === null))
            ? next
            : Object.assign({}, state, next);
        listeners.forEach((listener) => listener(state, old));
      },
      subscribe(listener) {
        listeners.add(listener);
        return () => listeners.delete(listener);
      },
    };
    initial = state = initialize(api.setState, api.getState, api);
    const bound = (selector) =>
      React?.useSyncExternalStore
        ? React.useSyncExternalStore(
            api.subscribe,
            () => selector(state),
            () => selector(initial),
          )
        : selector(state);
    Object.assign(bound, api);
    return bound;
  };
}

export function localStatePorts({ React, nativeMicrotasks = false } = {}) {
  let time = 1_000_000;
  const batches = [],
    microtasks = [],
    requests = [],
    invalidations = [],
    queryOptions = [],
    cacheEntries = [],
    queryStates = new Map(),
    sequence = [];
  let result = {
    data: undefined,
    isLoading: false,
    refetch: async () => {
      sequence.push("refetch");
      return "refetched";
    },
  };
  const client = {
    getQueryState: (key) => queryStates.get(JSON.stringify(key)),
    getQueryCache: () => ({
      findAll: ({ queryKey }) =>
        cacheEntries.filter((e) =>
          queryKey.every((k, i) => Object.is(e.queryKey[i], k)),
        ),
    }),
    invalidateQueries: async (options) => {
      invalidations.push(options);
      sequence.push("invalidate");
    },
  };
  const ports = {
    React,
    createBoundStore: syntheticBoundStore(React),
    subscribeWithSelector: (creator) => creator, // single-callback subscription behavior only; selector middleware is an external port
    createBatch({ merge, onFlush }) {
      const values = new Map();
      const batch = {
        set(key, value) {
          values.set(
            key,
            values.has(key) && merge ? merge(values.get(key), value) : value,
          );
        },
        peek: (key) => values.get(key),
        clear: () => values.clear(),
        get size() {
          return values.size;
        },
        flush() {
          if (!values.size) return;
          const snapshot = new Map(values);
          values.clear();
          onFlush(snapshot);
        },
      };
      batches.push(batch);
      return batch;
    },
    clock: { now: () => time },
    queueMicrotask: nativeMicrotasks
      ? globalThis.queueMicrotask
      : (fn) => microtasks.push(fn),
    useQuery: (options) => {
      queryOptions.push(options);
      return result;
    },
    useQueryClient: () => client,
    fetchBatch: async (mints, options) => {
      requests.push({ mints, options });
      return {};
    },
  };
  return {
    ports,
    batches,
    microtasks,
    requests,
    invalidations,
    queryOptions,
    cacheEntries,
    queryStates,
    sequence,
    client,
    setTime: (n) => {
      time = n;
    },
    time: () => time,
    setResult: (value) => {
      result = { ...result, ...value };
    },
    options: () => queryOptions.at(-1),
    drainMicrotasks() {
      for (let n = 0; microtasks.length; n++) {
        if (n > 1000) throw Error("synthetic microtasks did not settle");
        microtasks.shift()();
      }
    },
    flushFrames() {
      for (const batch of batches) batch.flush();
    },
  };
}
