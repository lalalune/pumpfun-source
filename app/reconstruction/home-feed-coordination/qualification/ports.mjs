// Qualification-only React-like hook storage for direct tests. Real React is qualified separately.
export function manualHooks() {
  const slots = [];
  let at = 0,
    changed = false;
  const effects = [];
  const same = (a, b) =>
    a?.length === b?.length && a.every((x, i) => Object.is(x, b[i]));
  const React = {
    useState(initial) {
      const i = at++;
      if (!(i in slots))
        slots[i] = typeof initial === "function" ? initial() : initial;
      return [
        slots[i],
        (next) => {
          const value = typeof next === "function" ? next(slots[i]) : next;
          if (!Object.is(value, slots[i])) {
            slots[i] = value;
            changed = true;
          }
        },
      ];
    },
    useEffect(fn, deps) {
      const i = at++;
      if (!(i in slots) || !same(slots[i].deps, deps)) {
        slots[i] = { deps: [...deps] };
        effects.push(fn);
      }
    },
    useRef(value) {
      const i = at++;
      if (!(i in slots)) slots[i] = { current: value };
      return slots[i];
    },
    useMemo(fn, deps) {
      const i = at++;
      if (!(i in slots) || !same(slots[i].deps, deps))
        slots[i] = { deps: [...deps], value: fn() };
      return slots[i].value;
    },
    useCallback(fn, deps) {
      return React.useMemo(() => fn, deps);
    },
  };
  return {
    React,
    begin() {
      at = 0;
      changed = false;
    },
    flushEffects() {
      const pending = effects.splice(0);
      return pending.map((fn) => fn());
    },
    get changed() {
      return changed;
    },
  };
}

export function cachePort() {
  const entries = new Map(),
    calls = [];
  return {
    entries,
    calls,
    setQueriesData(options, updater) {
      calls.push(["setQueriesData", options]);
      for (const [key, record] of entries)
        if (options.queryKey.every((v, i) => Object.is(v, record.key[i]))) {
          const next = updater(record.data);
          if (next !== undefined)
            entries.set(key, { key: record.key, data: next });
        }
    },
    invalidateQueries(options) {
      calls.push(["invalidateQueries", options]);
      return Promise.resolve();
    },
    prefetchInfiniteQuery(options) {
      calls.push(["prefetchInfiniteQuery", options]);
      return Promise.resolve(options);
    },
    put(key, data) {
      entries.set(JSON.stringify(key), { key, data });
    },
    get(key) {
      return entries.get(JSON.stringify(key))?.data;
    },
  };
}
