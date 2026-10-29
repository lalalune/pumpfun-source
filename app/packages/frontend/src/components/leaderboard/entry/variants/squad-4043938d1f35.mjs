// Explicit original source context; never a guessed runtime winner.
export function createHelper({ emptyImage } = {}) {
  let r = /^[A-Za-z0-9_]{1,15}$/,
    s = new Set(["create", "invitations"]),
    a = ({ groupId: e, username: a }) =>
      a && r.test(a) && !s.has(a.toLowerCase()) ? a : e;
  return (e) => `/squads/${encodeURIComponent(a(e))}`;
}
