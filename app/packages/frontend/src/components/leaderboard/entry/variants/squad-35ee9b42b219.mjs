// Explicit original source context; never a guessed runtime winner.
export function createHelper({ emptyImage } = {}) {
  let t = /^[A-Za-z0-9_]{1,15}$/,
    r = new Set(["create", "invitations"]),
    n = ({ groupId: e, username: n }) =>
      n && t.test(n) && !r.has(n.toLowerCase()) ? n : e;
  return (e) => `/squads/${encodeURIComponent(n(e))}`;
}
