// Explicit synthetic module context; no action, service or provider acquisition.
export function createOverlayContext() {
  return {
    pendingReplies: new Map(),
    likedByViewer: new Map(),
    listeners: new Set(),
  };
}
export function memoPort() {
  const slots = [];
  return (n) => {
    if (!slots.length)
      slots.push(...Array(n).fill(Symbol.for("react.memo_cache_sentinel")));
    if (slots.length !== n) throw Error("unexpected memo size");
    return slots;
  };
}
