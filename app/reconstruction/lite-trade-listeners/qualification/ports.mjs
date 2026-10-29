// Authored local qualification capabilities, not recovered React/provider implementations.
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
export function localCapabilities() {
  let serial = 0,
    active = true,
    ready = true,
    connection;
  const subscriptions = new Map(),
    history = [],
    errors = [],
    updates = [],
    coins = new Map();
  const storeState = {
    updateCoin: (mint, patch) => {
      updates.push({ mint, patch });
    },
    peekCoin: (mint) => coins.get(mint),
  };
  const boundStore = (selector) => selector(storeState);
  boundStore.getState = () => storeState;
  const subscribe = (instance, subject, callback, extra, options) => {
    const id = ++serial;
    const entry = { id, instance, subject, callback, extra, options };
    subscriptions.set(id, entry);
    history.push({ kind: "subscribe", id, instance, subject, extra, options });
    return id;
  };
  const unsubscribe = (instance, id) => {
    history.push({ kind: "unsubscribe", instance, id });
    subscriptions.delete(id);
  };
  const setActive = (value) => {
    active = value;
    connection = {
      subscribe,
      unsubscribe,
      isInstanceActive: (instance) => instance === "UNIFIED" && value,
    };
  };
  setActive(true);
  return {
    useConnection: () => connection,
    useReady: () => ready,
    liveCoinStore: boundStore,
    logger: { error: (...args) => errors.push(args) },
    DatePort: Date,
    subscriptions,
    history,
    errors,
    updates,
    coins,
    storeState,
    setActive,
    setReady(value) {
      ready = value;
    },
    emit(mint, event) {
      for (const entry of [...subscriptions.values()])
        if (entry.subject === `unifiedTradeEvent.lite.${mint}`)
          entry.callback(event);
    },
    observe() {
      return {
        active,
        ready,
        subscriptions: [...subscriptions.values()].map(
          ({ callback, ...rest }) => rest,
        ),
        history: [...history],
        updates: updates.map(({ mint, patch }) => ({
          mint,
          patch: { ...patch },
        })),
        errors: errors.map((args) => ({
          message: args[0],
          error: String(args[1]?.error),
        })),
      };
    },
  };
}
