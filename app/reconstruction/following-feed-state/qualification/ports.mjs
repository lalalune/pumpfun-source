// Qualification-only React-like hook storage for direct tests. Real React is qualified separately.
export function manualHooks() {
  const slots = [];
  let at = 0,
    changed = false;
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
    get changed() {
      return changed;
    },
  };
}
export function queryCachePort() {
  const data = new Map(),
    calls = [];
  let invalidate = () => Promise.resolve();
  return {
    data,
    calls,
    setInvalidation(fn) {
      invalidate = fn;
    },
    getQueryData(key) {
      calls.push(["get", key]);
      return data.get(JSON.stringify(key));
    },
    setQueryData(key, value) {
      calls.push(["set", key, value]);
      data.set(JSON.stringify(key), value);
    },
    invalidateQueries(input) {
      calls.push(["invalidate", input]);
      return invalidate(input);
    },
  };
}
