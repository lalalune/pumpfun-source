export function createVolumeFormatter(Intl) {
  let t = new Intl.NumberFormat("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }),
    n = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }),
    r = new Intl.NumberFormat("en-US", {
      notation: "compact",
      compactDisplay: "short",
      maximumSignificantDigits: 3,
    }),
    i = (e) => "number" == typeof e && Number.isFinite(e),
    o = (e, t, n) =>
      /[1-9]/.test(t) ? (e < 0 ? `−${t}` : n && e > 0 ? `+${t}` : t) : t;
  return function (e) {
    if (!i(e)) return "—";
    let s = Math.abs(e),
      l =
        s >= 999.5
          ? r.format(s).toUpperCase()
          : s >= 1
            ? n.format(s)
            : t.format(s);
    return o(e, `$${l}`, !1);
  };
}
