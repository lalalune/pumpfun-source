// Complete432405.f guard; no navigation or side effect is supplied.
export const isOrdinaryClick = (e) =>
  !e.defaultPrevented &&
  0 === e.button &&
  !e.metaKey &&
  !e.ctrlKey &&
  !e.shiftKey &&
  !e.altKey;
