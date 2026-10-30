// Complete original decimal draft input; supplied numeric props/callback only.
export function createSettingsDecimalInput({
  jsx,
  jsxs,
  useMemoCache,
  useState,
}) {
  const t = { jsx, jsxs },
    i = { c: useMemoCache },
    n = { useState };
  let C =
    "flex h-8 items-center gap-1.5 rounded-md bg-bg-tertiary px-2.5 ring-1 ring-inset ring-border-tertiary transition-colors focus-within:ring-text-accent";
  let ea = /^\d*\.?\d*$/;
  function eo(e) {
    let r,
      s,
      l,
      a,
      o,
      c,
      d,
      x = (0, i.c)(20),
      {
        value: u,
        onCommit: m,
        min: h,
        step: p,
        unit: f,
        label: y,
        isDisabled: b,
      } = e,
      [g, j] = (0, n.useState)(null),
      v = g ?? String(u);
    x[0] !== h || x[1] !== m
      ? ((r = (e) => {
          let t = Number(e);
          "" !== e &&
            Number.isFinite(t) &&
            t > 0 &&
            m(void 0 !== h ? Math.max(t, h) : t);
        }),
        (x[0] = h),
        (x[1] = m),
        (x[2] = r))
      : (r = x[2]);
    let w = r;
    return (
      x[3] !== u
        ? ((s = () => j(String(u))), (x[3] = u), (x[4] = s))
        : (s = x[4]),
      x[5] !== w
        ? ((l = (e) => {
            let t = e.currentTarget.value.replace(/,/g, ".");
            ea.test(t) && !(t.length > 12) && (j(t), w(t));
          }),
          (x[5] = w),
          (x[6] = l))
        : (l = x[6]),
      x[7] === Symbol.for("react.memo_cache_sentinel")
        ? ((a = () => j(null)), (x[7] = a))
        : (a = x[7]),
      x[8] !== b ||
      x[9] !== y ||
      x[10] !== v ||
      x[11] !== p ||
      x[12] !== s ||
      x[13] !== l
        ? ((o = (0, t.jsx)("input", {
            type: "text",
            inputMode: "decimal",
            autoComplete: "off",
            spellCheck: !1,
            "aria-label": y,
            disabled: b,
            step: p,
            className:
              "w-full min-w-0 bg-transparent text-right text-[13px] tabular-nums text-text-primary outline-none disabled:opacity-50",
            value: v,
            onFocus: s,
            onChange: l,
            onBlur: a,
          })),
          (x[8] = b),
          (x[9] = y),
          (x[10] = v),
          (x[11] = p),
          (x[12] = s),
          (x[13] = l),
          (x[14] = o))
        : (o = x[14]),
      x[15] !== f
        ? ((c = f
            ? (0, t.jsx)("span", {
                className:
                  "pointer-events-none shrink-0 text-[11px] font-medium uppercase tracking-wide text-text-tertiary",
                children: f,
              })
            : null),
          (x[15] = f),
          (x[16] = c))
        : (c = x[16]),
      x[17] !== o || x[18] !== c
        ? ((d = (0, t.jsxs)("div", {
            className: `${C} w-28`,
            children: [o, c],
          })),
          (x[17] = o),
          (x[18] = c),
          (x[19] = d))
        : (d = x[19]),
      d
    );
  }
  return eo;
}
