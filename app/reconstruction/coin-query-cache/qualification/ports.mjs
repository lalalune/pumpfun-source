// Qualification-only capabilities. This is not TanStack Query or an original provider.
export function memoPort() {
  const slots = [];
  return (n) => {
    if (!slots.length)
      slots.push(...Array(n).fill(Symbol.for("react.memo_cache_sentinel")));
    if (slots.length !== n) throw Error("unexpected memo size");
    return slots;
  };
}
export function queryClientPort() {
  const entries = new Map(),
    writes = [],
    reads = [];
  return {
    entries,
    writes,
    reads,
    put(key, data, at = 0) {
      entries.set(JSON.stringify(key), {
        queryKey: key,
        state: { data, dataUpdatedAt: at },
      });
    },
    getQueryState(key) {
      reads.push(key);
      return entries.get(JSON.stringify(key))?.state;
    },
    getQueryCache() {
      return {
        findAll: ({ queryKey }) =>
          [...entries.values()].filter((e) =>
            queryKey.every((part, i) => part === e.queryKey[i]),
          ),
      };
    },
    setQueryData(key, data) {
      writes.push([key, data]);
      const old = entries.get(JSON.stringify(key));
      entries.set(JSON.stringify(key), {
        queryKey: key,
        state: { data, dataUpdatedAt: old?.state.dataUpdatedAt ?? 0 },
      });
    },
  };
}
