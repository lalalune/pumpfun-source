// Source-bound editable image owner; provider implementation and product mount are external.
export const CALLOUT_PREVIEW_CLASS =
  "overlay-glass rounded-xl border border-border-tertiary text-text-primary shadow-lg";
export function createCalloutImagePreview({
  jsx,
  jsxs,
  useMemoCache,
  React,
  HoverCard,
  Link,
  classNames,
  document,
  window,
  Node,
}) {
  for (const [name, value] of Object.entries({
    jsx,
    jsxs,
    useMemoCache,
    classNames,
    Node,
  }))
    if (typeof value !== "function")
      throw new TypeError(
        "Explicit image-preview capability required: " + name,
      );
  for (const name of ["useRef", "useState", "useEffect"])
    if (typeof React?.[name] !== "function")
      throw new TypeError(
        "Explicit React image-preview hook required: " + name,
      );
  for (const name of ["Root", "Trigger", "Portal", "Positioner", "Popup"])
    if (HoverCard?.[name] == null)
      throw new TypeError(
        "Explicit same-instance HoverCard component required: " + name,
      );
  if (
    Link == null ||
    !window ||
    typeof document?.addEventListener !== "function" ||
    typeof document?.removeEventListener !== "function"
  )
    throw new TypeError(
      "Explicit Link/viewport/document event capabilities required",
    );
  const i = { c: useMemoCache },
    a = {
      useRef: React.useRef,
      useState: React.useState,
      useEffect: React.useEffect,
    },
    er = { c: classNames },
    t = { jsx: jsx, jsxs: jsxs },
    Z = HoverCard,
    ei = { default: Link },
    ea = { V: CALLOUT_PREVIEW_CLASS },
    X = HoverCard,
    Y = HoverCard,
    ee = HoverCard,
    et = HoverCard;
  return (e) => {
    let r,
      n,
      l,
      s,
      o,
      d,
      c,
      u,
      m,
      p,
      h,
      f,
      g,
      x = (0, i.c)(35),
      {
        src: v,
        testId: y,
        className: w,
        dense: b,
        priority: j,
        hostHref: N,
        onHostClick: C,
      } = e,
      S = void 0 !== j && j,
      M = (0, a.useRef)(null),
      T = (0, a.useRef)(null),
      [k, R] = (0, a.useState)(!1),
      [_, E] = (0, a.useState)(null);
    (x[0] !== k
      ? ((r = () => {
          if (!k) return;
          let e = (e) => {
            let t = M.current;
            t && e.target instanceof Node && e.target.contains(t) && R(!1);
          };
          return (
            document.addEventListener("scroll", e, {
              capture: !0,
              passive: !0,
            }),
            () => document.removeEventListener("scroll", e, { capture: !0 })
          );
        }),
        (n = [k]),
        (x[0] = k),
        (x[1] = r),
        (x[2] = n))
      : ((r = x[1]), (n = x[2])),
      (0, a.useEffect)(r, n),
      x[3] === Symbol.for("react.memo_cache_sentinel")
        ? ((l = (e) => {
            let { movementX: t, movementY: i } = e.nativeEvent;
            (0 !== t || 0 !== i) &&
              (T.current = e.currentTarget.getBoundingClientRect().top);
          }),
          (x[3] = l))
        : (l = x[3]));
    let P = l;
    x[4] === Symbol.for("react.memo_cache_sentinel")
      ? ((s = (e, t) => {
          let i = M.current;
          e &&
          "trigger-hover" === t.reason &&
          T.current !== i?.getBoundingClientRect().top
            ? t.cancel()
            : (R(e),
              e &&
                E(
                  i
                    ? (({
                        naturalWidth: e,
                        naturalHeight: t,
                        viewportWidth: i,
                        viewportHeight: a,
                      }) => {
                        if (e <= 0 || t <= 0) return null;
                        let r = Math.min(0.9 * i, 960) - 8,
                          n = Math.min(0.85 * a, 960) - 8;
                        if (r <= 0 || n <= 0) return null;
                        let l = Math.min(r / e, n / t, 3);
                        return {
                          width: Math.round(e * l),
                          height: Math.round(t * l),
                        };
                      })({
                        naturalWidth: i.naturalWidth,
                        naturalHeight: i.naturalHeight,
                        viewportWidth: window.innerWidth,
                        viewportHeight: window.innerHeight,
                      })
                    : null,
                ));
        }),
        (x[4] = s))
      : (s = x[4]);
    let A = s;
    x[5] === Symbol.for("react.memo_cache_sentinel")
      ? ((o = () => {
          T.current = null;
        }),
        (x[5] = o))
      : (o = x[5]);
    let z = S ? "eager" : "lazy",
      U = S ? "high" : void 0,
      I = void 0 !== b && b ? "rounded-md" : "rounded-xl",
      F = !N && w;
    (x[6] !== I || x[7] !== F
      ? ((d = (0, er.c)(
          "max-h-80 w-auto max-w-full border border-border-secondary object-cover",
          I,
          F,
        )),
        (x[6] = I),
        (x[7] = F),
        (x[8] = d))
      : (d = x[8]),
      x[9] !== v || x[10] !== d || x[11] !== z || x[12] !== U || x[13] !== y
        ? ((c = (0, t.jsx)(Z.Trigger, {
            delay: 600,
            closeDelay: 100,
            onMouseEnter: o,
            onMouseMove: P,
            render: (0, t.jsx)("img", {
              ref: M,
              src: v,
              alt: "",
              loading: z,
              fetchPriority: U,
              "data-testid": y,
              className: d,
            }),
          })),
          (x[9] = v),
          (x[10] = d),
          (x[11] = z),
          (x[12] = U),
          (x[13] = y),
          (x[14] = c))
        : (c = x[14]));
    let O = c;
    x[15] !== w || x[16] !== N || x[17] !== C || x[18] !== y || x[19] !== O
      ? ((u = N
          ? (0, t.jsx)(ei.default, {
              href: N,
              prefetch: !1,
              onClick: C,
              tabIndex: -1,
              "aria-hidden": "true",
              "data-testid": `${y}-host-link`,
              className: (0, er.c)("relative z-[2] block w-fit max-w-full", w),
              children: O,
            })
          : O),
        (x[15] = w),
        (x[16] = N),
        (x[17] = C),
        (x[18] = y),
        (x[19] = O),
        (x[20] = u))
      : (u = x[20]);
    let B = `${y}-preview-popup`;
    x[21] === Symbol.for("react.memo_cache_sentinel")
      ? ((m = (0, er.c)(
          "origin-(--transform-origin) p-1 outline-none duration-150 data-[open]:animate-in data-[open]:fade-in-0 data-[open]:zoom-in-95",
          ea.V,
        )),
        (x[21] = m))
      : (m = x[21]);
    let D = `${y}-preview`;
    return (
      x[22] !== _
        ? ((p = _
            ? {
                "--zoom-w": `${_.width}px`,
                "--zoom-ratio": `${_.width} / ${_.height}`,
              }
            : void 0),
          (x[22] = _),
          (x[23] = p))
        : (p = x[23]),
      x[24] !== v || x[25] !== D || x[26] !== p
        ? ((h = (0, t.jsx)("img", {
            src: v,
            alt: "",
            decoding: "async",
            draggable: !1,
            "data-testid": D,
            className:
              "block h-auto w-auto max-w-[calc(var(--available-width)-8px)] max-h-[calc(var(--available-height)-8px)] aspect-[var(--zoom-ratio)] w-[min(var(--zoom-w),calc(var(--available-width)_-_8px),calc((var(--available-height)_-_8px)_*_var(--zoom-ratio)))] rounded-md object-contain",
            style: p,
          })),
          (x[24] = v),
          (x[25] = D),
          (x[26] = p),
          (x[27] = h))
        : (h = x[27]),
      x[28] !== B || x[29] !== h
        ? ((f = (0, t.jsx)(X.Portal, {
            children: (0, t.jsx)(Y.Positioner, {
              side: "right",
              align: "start",
              sideOffset: 12,
              collisionPadding: 16,
              className: "pointer-events-none z-[1000]",
              children: (0, t.jsx)(ee.Popup, {
                "data-testid": B,
                className: m,
                children: h,
              }),
            }),
          })),
          (x[28] = B),
          (x[29] = h),
          (x[30] = f))
        : (f = x[30]),
      x[31] !== k || x[32] !== u || x[33] !== f
        ? ((g = (0, t.jsxs)(et.Root, {
            open: k,
            onOpenChange: A,
            children: [u, f],
          })),
          (x[31] = k),
          (x[32] = u),
          (x[33] = f),
          (x[34] = g))
        : (g = x[34]),
      g
    );
  };
}
