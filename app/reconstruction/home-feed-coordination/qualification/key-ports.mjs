// Qualification-only reuse of1966 private key signatures; no read/query core copied.
const et = (e, t, l) => ["callouts", "following-alerts", e, t, l];
const el = (e, t, l, r) => [...et(e, t, l), r];
export const followingPrefixKey = et,
  followingChainKey = el;
