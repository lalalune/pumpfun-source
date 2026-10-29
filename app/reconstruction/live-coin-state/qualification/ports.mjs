// Authored synthetic ports for finite qualification, not recovered providers.
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

export function manualEnvironment({ raf = true, hidden = false } = {}) {
  let time = 0,
    nextId = 1;
  const handles = new Map(),
    events = new Map(),
    errors = [];
  const schedule = (fn, delay, kind) => {
    const id = nextId++;
    handles.set(id, { fn, at: time + delay, kind });
    return id;
  };
  const document = {
    visibilityState: hidden ? "hidden" : "visible",
    addEventListener(type, fn) {
      if (!events.has(type)) events.set(type, new Set());
      events.get(type).add(fn);
    },
  };
  const window = raf
    ? {
        requestAnimationFrame: (fn) => schedule(fn, 16, "raf"),
        cancelAnimationFrame: (id) => handles.delete(id),
      }
    : {};
  return {
    environment: {
      window,
      document,
      setTimeout: (fn, delay) => schedule(fn, delay, "timeout"),
      clearTimeout: (id) => handles.delete(id),
    },
    clock: { now: () => time },
    logger: { error: (...args) => errors.push(args) },
    errors,
    setTime(value) {
      time = value;
    },
    handles: () =>
      [...handles].map(([id, h]) => ({ id, at: h.at, kind: h.kind })),
    listeners: (type) => events.get(type)?.size ?? 0,
    visibility(value) {
      document.visibilityState = value;
      for (const fn of events.get("visibilitychange") ?? []) fn();
    },
    advance(ms) {
      const end = time + ms;
      for (let count = 0; count < 10000; count++) {
        const next = [...handles]
          .filter(([, h]) => h.at <= end)
          .sort((a, b) => a[1].at - b[1].at || a[0] - b[0])[0];
        if (!next) {
          time = end;
          return;
        }
        const [id, h] = next;
        handles.delete(id);
        time = h.at;
        h.fn(time);
      }
      throw Error("synthetic scheduler did not settle");
    },
    fireKind(kind) {
      const entry = [...handles].find(([, h]) => h.kind === kind);
      if (!entry) throw Error(`missing synthetic ${kind}`);
      handles.delete(entry[0]);
      entry[1].fn(time);
    },
  };
}

export function manualHooks() {
  const components = new Map();
  let active;
  function slot(create) {
    if (!active) throw Error("synthetic render required");
    const index = active.cursor++;
    return active.slots[index] ?? (active.slots[index] = create());
  }
  return {
    React: {
      useRef: (initial) => slot(() => ({ current: initial })),
      useEffect(fn, deps) {
        const s = slot(() => ({ deps: null, cleanup: null }));
        if (!s.deps || deps.some((v, i) => !Object.is(v, s.deps[i]))) {
          s.cleanup?.();
          s.deps = deps;
          s.cleanup = fn();
        }
      },
    },
    compiler: (size) =>
      slot(() => Array(size).fill(Symbol.for("react.memo_cache_sentinel"))),
    render(id, fn) {
      const component = components.get(id) ?? { slots: [], cursor: 0 };
      components.set(id, component);
      component.cursor = 0;
      active = component;
      try {
        return fn();
      } finally {
        active = undefined;
      }
    },
    unmount(id) {
      const c = components.get(id);
      for (const s of c?.slots ?? []) s.cleanup?.();
      components.delete(id);
    },
  };
}
