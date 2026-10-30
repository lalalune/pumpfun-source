// Complete source-adapted shared Sidebar controller/display and ordinary supplied navigation rendering. No acquisition/actions implemented.
export function createSharedSidebarNavigation({
  jsx,
  jsxs,
  Fragment,
  React,
  useMemoCache,
  classNames,
  classVariants,
  Slot,
  TooltipRoot,
  TooltipTrigger,
  TooltipContent,
  DrawerRoot,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  makeSvgIcon,
  useTranslation,
  window,
  Link,
  NewBadge,
  ExternalIcon,
  routes,
}) {
  const sidebar = (() => {
    const t = { jsx, jsxs, Fragment },
      r = { c: useMemoCache },
      l = React,
      y = { c: classNames },
      n = { f: classVariants },
      i = { M: Slot },
      a = { W: TooltipRoot, _: TooltipTrigger, Y: TooltipContent },
      x = {
        j: DrawerRoot,
        U: DrawerContent,
        D: DrawerHeader,
        L: DrawerTitle,
        c: DrawerDescription,
      },
      s = { f: useTranslation },
      o = { f: makeSvgIcon };
    function c(e) {
      return (0, o.f)({
        tag: "svg",
        attr: {
          viewBox: "0 0 20 20",
          fill: "currentColor",
          "aria-hidden": "true",
        },
        child: [
          {
            tag: "path",
            attr: {
              fillRule: "evenodd",
              d: "M15.707 15.707a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 010 1.414zm-6 0a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 011.414 1.414L5.414 10l4.293 4.293a1 1 0 010 1.414z",
              clipRule: "evenodd",
            },
          },
        ],
      })(e);
    }
    function _() {
      let e = l.useContext(w);
      if (!e) throw Error("useSidebar must be used within a SidebarProvider.");
      return e;
    }
    function M(e) {
      return !e;
    }
    function D(e) {
      return !e;
    }
    let v = { position: "fixed", top: 0, bottom: 0 },
      w = l.createContext(null),
      j = l.forwardRef((e, a) => {
        let i,
          n,
          s,
          o,
          c,
          d,
          u,
          m,
          f,
          p,
          h,
          b,
          x,
          g,
          v,
          _,
          j = (0, r.c)(35);
        j[0] !== e
          ? (({
              defaultOpen: u,
              open: s,
              onOpenChange: c,
              className: n,
              style: d,
              children: i,
              ...o
            } = e),
            (j[0] = e),
            (j[1] = i),
            (j[2] = n),
            (j[3] = s),
            (j[4] = o),
            (j[5] = c),
            (j[6] = d),
            (j[7] = u))
          : ((i = j[1]),
            (n = j[2]),
            (s = j[3]),
            (o = j[4]),
            (c = j[5]),
            (d = j[6]),
            (u = j[7]));
        let C = void 0 === u || u,
          [N, S] = l.useState(!1),
          [k, E] = l.useState(C),
          A = s ?? k;
        j[8] !== A || j[9] !== c
          ? ((m = (e) => {
              let t = "function" == typeof e ? e(A) : e;
              c ? c(t) : E(t);
            }),
            (j[8] = A),
            (j[9] = c),
            (j[10] = m))
          : (m = j[10]);
        let I = m;
        j[11] !== I
          ? ((f = () => {
              window.matchMedia("(max-width: 767px)").matches ? S(M) : I(D);
            }),
            (j[11] = I),
            (j[12] = f))
          : (f = j[12]);
        let T = f;
        (j[13] !== T
          ? ((p = () => {
              let e = (e) => {
                "b" === e.key &&
                  (e.metaKey || e.ctrlKey) &&
                  (e.preventDefault(), T());
              };
              return (
                window.addEventListener("keydown", e),
                () => window.removeEventListener("keydown", e)
              );
            }),
            (h = [T]),
            (j[13] = T),
            (j[14] = p),
            (j[15] = h))
          : ((p = j[14]), (h = j[15])),
          l.useEffect(p, h));
        let R = A ? "expanded" : "collapsed";
        j[16] !== A || j[17] !== N || j[18] !== I || j[19] !== R || j[20] !== T
          ? ((b = {
              state: R,
              open: A,
              setOpen: I,
              openMobile: N,
              setOpenMobile: S,
              toggleSidebar: T,
            }),
            (j[16] = A),
            (j[17] = N),
            (j[18] = I),
            (j[19] = R),
            (j[20] = T),
            (j[21] = b))
          : (b = j[21]);
        let L = b;
        j[22] !== d
          ? ((x = {
              "--sidebar-width": "13rem",
              "--sidebar-width-icon": "3.5rem",
              ...d,
            }),
            (j[22] = d),
            (j[23] = x))
          : (x = j[23]);
        let O = x;
        return (
          j[24] !== n
            ? ((g = (0, y.c)("group/sidebar-wrapper flex min-h-svh w-full", n)),
              (j[24] = n),
              (j[25] = g))
            : (g = j[25]),
          j[26] !== i ||
          j[27] !== o ||
          j[28] !== a ||
          j[29] !== O ||
          j[30] !== g
            ? ((v = (0, t.jsx)("div", {
                style: O,
                className: g,
                ref: a,
                ...o,
                children: i,
              })),
              (j[26] = i),
              (j[27] = o),
              (j[28] = a),
              (j[29] = O),
              (j[30] = g),
              (j[31] = v))
            : (v = j[31]),
          j[32] !== L || j[33] !== v
            ? ((_ = (0, t.jsx)(w.Provider, { value: L, children: v })),
              (j[32] = L),
              (j[33] = v),
              (j[34] = _))
            : (_ = j[34]),
          _
        );
      }),
      C = l.forwardRef((e, a) => {
        let i,
          n,
          l,
          o,
          c,
          d,
          u,
          m,
          f,
          p,
          h,
          b,
          g,
          w,
          j,
          C,
          N,
          S,
          k,
          E,
          A,
          I,
          T,
          R,
          L = (0, r.c)(65);
        L[0] !== e
          ? (({
              side: c,
              variant: d,
              collapsible: u,
              className: n,
              style: o,
              children: i,
              ...l
            } = e),
            (L[0] = e),
            (L[1] = i),
            (L[2] = n),
            (L[3] = l),
            (L[4] = o),
            (L[5] = c),
            (L[6] = d),
            (L[7] = u))
          : ((i = L[1]),
            (n = L[2]),
            (l = L[3]),
            (o = L[4]),
            (c = L[5]),
            (d = L[6]),
            (u = L[7]));
        let O = void 0 === c ? "left" : c,
          M = void 0 === d ? "sidebar" : d,
          D = void 0 === u ? "offcanvas" : u,
          { state: F, openMobile: P, setOpenMobile: z } = _(),
          { t: K } = (0, s.f)();
        if ("none" === D) {
          let e, r;
          return (
            L[8] !== n
              ? ((e = (0, y.c)("flex h-full w-[--sidebar-width] flex-col", n)),
                (L[8] = n),
                (L[9] = e))
              : (e = L[9]),
            L[10] !== i || L[11] !== l || L[12] !== a || L[13] !== e
              ? ((r = (0, t.jsx)("div", {
                  className: e,
                  ref: a,
                  ...l,
                  children: i,
                })),
                (L[10] = i),
                (L[11] = l),
                (L[12] = a),
                (L[13] = e),
                (L[14] = r))
              : (r = L[14]),
            r
          );
        }
        (L[15] === Symbol.for("react.memo_cache_sentinel")
          ? ((m = { "--sidebar-width": "18rem" }), (L[15] = m))
          : (m = L[15]),
          L[16] !== K
            ? ((f = K("web.sidebar.title")), (L[16] = K), (L[17] = f))
            : (f = L[17]),
          L[18] !== f
            ? ((p = (0, t.jsx)(x.L, { children: f })), (L[18] = f), (L[19] = p))
            : (p = L[19]),
          L[20] !== K
            ? ((h = K("web.sidebar.mobile_description")),
              (L[20] = K),
              (L[21] = h))
            : (h = L[21]),
          L[22] !== h
            ? ((b = (0, t.jsx)(x.c, { children: h })), (L[22] = h), (L[23] = b))
            : (b = L[23]),
          L[24] !== p || L[25] !== b
            ? ((g = (0, t.jsxs)(x.D, {
                className: "sr-only",
                children: [p, b],
              })),
              (L[24] = p),
              (L[25] = b),
              (L[26] = g))
            : (g = L[26]),
          L[27] !== i
            ? ((w = (0, t.jsx)("div", {
                className: "flex h-full w-full flex-col",
                children: i,
              })),
              (L[27] = i),
              (L[28] = w))
            : (w = L[28]),
          L[29] !== O || L[30] !== w || L[31] !== g
            ? ((j = (0, t.jsxs)(x.U, {
                "data-sidebar": "sidebar",
                "data-mobile": "true",
                className:
                  "w-[--sidebar-width] border-r border-border-secondary bg-bg-primary p-0 md:hidden [&>button]:hidden",
                overlayClassName: "md:hidden",
                style: m,
                side: O,
                children: [g, w],
              })),
              (L[29] = O),
              (L[30] = w),
              (L[31] = g),
              (L[32] = j))
            : (j = L[32]),
          L[33] !== P || L[34] !== z || L[35] !== j
            ? ((C = (0, t.jsx)(x.j, { open: P, onOpenChange: z, children: j })),
              (L[33] = P),
              (L[34] = z),
              (L[35] = j),
              (L[36] = C))
            : (C = L[36]));
        let B = "collapsed" === F ? D : "",
          H =
            "floating" === M || "inset" === M
              ? "group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)_+_theme(spacing.4))]"
              : "group-data-[collapsible=icon]:w-[--sidebar-width-icon]";
        (L[37] !== H
          ? ((N = (0, y.c)(
              "relative w-[--sidebar-width] bg-transparent transition-[width] duration-200 ease-linear",
              "group-data-[collapsible=offcanvas]:w-0",
              "group-data-[side=right]:rotate-180",
              H,
            )),
            (L[37] = H),
            (L[38] = N))
          : (N = L[38]),
          L[39] !== N
            ? ((S = (0, t.jsx)("div", { className: N })),
              (L[39] = N),
              (L[40] = S))
            : (S = L[40]));
        let q =
            "left" === O
              ? "left-0 group-data-[collapsible=offcanvas]:left-[calc(var(--sidebar-width)*-1)]"
              : "right-0 group-data-[collapsible=offcanvas]:right-[calc(var(--sidebar-width)*-1)]",
          W =
            "floating" === M || "inset" === M
              ? "p-2 group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)_+_theme(spacing.4)_+2px)]"
              : "group-data-[collapsible=icon]:w-[--sidebar-width-icon] group-data-[side=left]:border-r group-data-[side=right]:border-l";
        return (
          L[41] !== n || L[42] !== q || L[43] !== W
            ? ((k = (0, y.c)(
                "z-40 hidden w-[--sidebar-width] transform-gpu transition-[left,right,width] duration-200 ease-linear md:flex",
                q,
                W,
                n,
              )),
              (L[41] = n),
              (L[42] = q),
              (L[43] = W),
              (L[44] = k))
            : (k = L[44]),
          L[45] !== o
            ? ((E = { ...v, ...o }), (L[45] = o), (L[46] = E))
            : (E = L[46]),
          L[47] !== i
            ? ((A = (0, t.jsx)("div", {
                "data-sidebar": "sidebar",
                className:
                  "relative flex h-full w-full flex-col bg-bg-primary group-data-[variant=floating]:rounded-lg group-data-[variant=floating]:border group-data-[variant=floating]:border-border-secondary group-data-[variant=floating]:shadow",
                children: i,
              })),
              (L[47] = i),
              (L[48] = A))
            : (A = L[48]),
          L[49] !== l || L[50] !== k || L[51] !== E || L[52] !== A
            ? ((I = (0, t.jsx)("div", {
                className: k,
                style: E,
                ...l,
                children: A,
              })),
              (L[49] = l),
              (L[50] = k),
              (L[51] = E),
              (L[52] = A),
              (L[53] = I))
            : (I = L[53]),
          L[54] !== a ||
          L[55] !== O ||
          L[56] !== F ||
          L[57] !== B ||
          L[58] !== S ||
          L[59] !== I ||
          L[60] !== M
            ? ((T = (0, t.jsxs)("div", {
                ref: a,
                className: "group peer hidden text-text-primary md:block",
                "data-state": F,
                "data-collapsible": B,
                "data-variant": M,
                "data-side": O,
                children: [S, I],
              })),
              (L[54] = a),
              (L[55] = O),
              (L[56] = F),
              (L[57] = B),
              (L[58] = S),
              (L[59] = I),
              (L[60] = M),
              (L[61] = T))
            : (T = L[61]),
          L[62] !== C || L[63] !== T
            ? ((R = (0, t.jsxs)(t.Fragment, { children: [C, T] })),
              (L[62] = C),
              (L[63] = T),
              (L[64] = R))
            : (R = L[64]),
          R
        );
      }),
      N = l.forwardRef((e, a) => {
        let i,
          n,
          l,
          o,
          d,
          u,
          m,
          f,
          p,
          h = (0, r.c)(21);
        h[0] !== e
          ? (({ className: i, onClick: n, ...l } = e),
            (h[0] = e),
            (h[1] = i),
            (h[2] = n),
            (h[3] = l))
          : ((i = h[1]), (n = h[2]), (l = h[3]));
        let { toggleSidebar: b } = _(),
          { t: x } = (0, s.f)();
        return (
          h[4] !== x
            ? ((o = x("web.sidebar.toggle")), (h[4] = x), (h[5] = o))
            : (o = h[5]),
          h[6] !== x
            ? ((d = x("web.sidebar.toggle")), (h[6] = x), (h[7] = d))
            : (d = h[7]),
          h[8] !== n || h[9] !== b
            ? ((u = (e) => {
                (n?.(e), b());
              }),
              (h[8] = n),
              (h[9] = b),
              (h[10] = u))
            : (u = h[10]),
          h[11] !== i
            ? ((m = (0, y.c)(
                "flex size-6 shrink-0 items-center justify-center rounded-full border border-border-secondary bg-bg-primary text-text-quaternary transition-colors hover:border-border-tertiary hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-accent [&>svg]:size-3.5",
                i,
              )),
              (h[11] = i),
              (h[12] = m))
            : (m = h[12]),
          h[13] === Symbol.for("react.memo_cache_sentinel")
            ? ((f = (0, t.jsx)(c, {
                className:
                  "transition-transform duration-200 group-data-[state=collapsed]:rotate-180",
              })),
              (h[13] = f))
            : (f = h[13]),
          h[14] !== l ||
          h[15] !== a ||
          h[16] !== o ||
          h[17] !== d ||
          h[18] !== u ||
          h[19] !== m
            ? ((p = (0, t.jsx)("button", {
                ref: a,
                type: "button",
                "data-sidebar": "trigger",
                "aria-label": o,
                title: d,
                onClick: u,
                className: m,
                ...l,
                children: f,
              })),
              (h[14] = l),
              (h[15] = a),
              (h[16] = o),
              (h[17] = d),
              (h[18] = u),
              (h[19] = m),
              (h[20] = p))
            : (p = h[20]),
          p
        );
      }),
      S = l.forwardRef((e, a) => {
        let i,
          n,
          l,
          o,
          c,
          d,
          u = (0, r.c)(16);
        u[0] !== e
          ? (({ className: i, ...n } = e), (u[0] = e), (u[1] = i), (u[2] = n))
          : ((i = u[1]), (n = u[2]));
        let { toggleSidebar: m } = _(),
          { t: f } = (0, s.f)();
        return (
          u[3] !== f
            ? ((l = f("web.sidebar.toggle")), (u[3] = f), (u[4] = l))
            : (l = u[4]),
          u[5] !== f
            ? ((o = f("web.sidebar.toggle")), (u[5] = f), (u[6] = o))
            : (o = u[6]),
          u[7] !== i
            ? ((c = (0, y.c)(
                "hover:after:bg-border-tertiary absolute inset-y-0 z-20 hidden w-4 -translate-x-1/2 transition-all ease-linear after:absolute after:inset-y-0 after:left-1/2 after:w-[2px] group-data-[side=left]:-right-4 group-data-[side=right]:left-0 sm:flex",
                "[[data-side=left]_&]:cursor-w-resize [[data-side=right]_&]:cursor-e-resize",
                "[[data-side=left][data-state=collapsed]_&]:cursor-e-resize [[data-side=right][data-state=collapsed]_&]:cursor-w-resize",
                "group-data-[collapsible=offcanvas]:hover:bg-bg-primary group-data-[collapsible=offcanvas]:translate-x-0 group-data-[collapsible=offcanvas]:after:left-full",
                "[[data-side=left][data-collapsible=offcanvas]_&]:-right-2",
                "[[data-side=right][data-collapsible=offcanvas]_&]:-left-2",
                i,
              )),
              (u[7] = i),
              (u[8] = c))
            : (c = u[8]),
          u[9] !== n ||
          u[10] !== a ||
          u[11] !== l ||
          u[12] !== o ||
          u[13] !== c ||
          u[14] !== m
            ? ((d = (0, t.jsx)("button", {
                ref: a,
                "data-sidebar": "rail",
                "aria-label": l,
                tabIndex: -1,
                onClick: m,
                title: o,
                className: c,
                ...n,
              })),
              (u[9] = n),
              (u[10] = a),
              (u[11] = l),
              (u[12] = o),
              (u[13] = c),
              (u[14] = m),
              (u[15] = d))
            : (d = u[15]),
          d
        );
      }),
      k = l.forwardRef((e, a) => {
        let i,
          n,
          l,
          s,
          o = (0, r.c)(9);
        return (
          o[0] !== e
            ? (({ className: i, ...n } = e), (o[0] = e), (o[1] = i), (o[2] = n))
            : ((i = o[1]), (n = o[2])),
          o[3] !== i
            ? ((l = (0, y.c)(
                "relative flex w-full flex-1 flex-col bg-bg-primary",
                "w-px md:peer-data-[variant=inset]:m-2 md:peer-data-[state=collapsed]:peer-data-[variant=inset]:ml-2 md:peer-data-[variant=inset]:ml-0 md:peer-data-[variant=inset]:rounded-xl md:peer-data-[variant=inset]:shadow",
                i,
              )),
              (o[3] = i),
              (o[4] = l))
            : (l = o[4]),
          o[5] !== n || o[6] !== a || o[7] !== l
            ? ((s = (0, t.jsx)("main", { ref: a, className: l, ...n })),
              (o[5] = n),
              (o[6] = a),
              (o[7] = l),
              (o[8] = s))
            : (s = o[8]),
          s
        );
      }),
      E = l.forwardRef((e, a) => {
        let i,
          n,
          l,
          s,
          o = (0, r.c)(9);
        return (
          o[0] !== e
            ? (({ className: i, ...n } = e), (o[0] = e), (o[1] = i), (o[2] = n))
            : ((i = o[1]), (n = o[2])),
          o[3] !== i
            ? ((l = (0, y.c)("flex flex-col gap-2 p-2", i)),
              (o[3] = i),
              (o[4] = l))
            : (l = o[4]),
          o[5] !== n || o[6] !== a || o[7] !== l
            ? ((s = (0, t.jsx)("div", {
                ref: a,
                "data-sidebar": "header",
                className: l,
                ...n,
              })),
              (o[5] = n),
              (o[6] = a),
              (o[7] = l),
              (o[8] = s))
            : (s = o[8]),
          s
        );
      }),
      A = l.forwardRef((e, a) => {
        let i,
          n,
          l,
          s,
          o = (0, r.c)(9);
        return (
          o[0] !== e
            ? (({ className: i, ...n } = e), (o[0] = e), (o[1] = i), (o[2] = n))
            : ((i = o[1]), (n = o[2])),
          o[3] !== i
            ? ((l = (0, y.c)("flex flex-col gap-2 p-2", i)),
              (o[3] = i),
              (o[4] = l))
            : (l = o[4]),
          o[5] !== n || o[6] !== a || o[7] !== l
            ? ((s = (0, t.jsx)("div", {
                ref: a,
                "data-sidebar": "footer",
                className: l,
                ...n,
              })),
              (o[5] = n),
              (o[6] = a),
              (o[7] = l),
              (o[8] = s))
            : (s = o[8]),
          s
        );
      }),
      I = l.forwardRef((e, a) => {
        let i,
          n,
          l,
          s,
          o = (0, r.c)(9);
        return (
          o[0] !== e
            ? (({ className: i, ...n } = e), (o[0] = e), (o[1] = i), (o[2] = n))
            : ((i = o[1]), (n = o[2])),
          o[3] !== i
            ? ((l = (0, y.c)(
                "flex min-h-0 flex-1 flex-col gap-2 overflow-auto group-data-[collapsible=icon]:overflow-x-hidden group-data-[collapsible=icon]:overflow-y-auto group-data-[collapsible=icon]:[scrollbar-width:none] group-data-[collapsible=icon]:[&::-webkit-scrollbar]:hidden",
                i,
              )),
              (o[3] = i),
              (o[4] = l))
            : (l = o[4]),
          o[5] !== n || o[6] !== a || o[7] !== l
            ? ((s = (0, t.jsx)("div", {
                ref: a,
                "data-sidebar": "content",
                className: l,
                ...n,
              })),
              (o[5] = n),
              (o[6] = a),
              (o[7] = l),
              (o[8] = s))
            : (s = o[8]),
          s
        );
      }),
      T = l.forwardRef((e, a) => {
        let i,
          n,
          l,
          s,
          o = (0, r.c)(9);
        return (
          o[0] !== e
            ? (({ className: i, ...n } = e), (o[0] = e), (o[1] = i), (o[2] = n))
            : ((i = o[1]), (n = o[2])),
          o[3] !== i
            ? ((l = (0, y.c)("flex w-full min-w-0 flex-col gap-1", i)),
              (o[3] = i),
              (o[4] = l))
            : (l = o[4]),
          o[5] !== n || o[6] !== a || o[7] !== l
            ? ((s = (0, t.jsx)("ul", {
                ref: a,
                "data-sidebar": "menu",
                className: l,
                ...n,
              })),
              (o[5] = n),
              (o[6] = a),
              (o[7] = l),
              (o[8] = s))
            : (s = o[8]),
          s
        );
      }),
      R = l.forwardRef((e, a) => {
        let i,
          n,
          l,
          s,
          o = (0, r.c)(9);
        return (
          o[0] !== e
            ? (({ className: i, ...n } = e), (o[0] = e), (o[1] = i), (o[2] = n))
            : ((i = o[1]), (n = o[2])),
          o[3] !== i
            ? ((l = (0, y.c)("group/menu-item relative", i)),
              (o[3] = i),
              (o[4] = l))
            : (l = o[4]),
          o[5] !== n || o[6] !== a || o[7] !== l
            ? ((s = (0, t.jsx)("li", {
                ref: a,
                "data-sidebar": "menu-item",
                className: l,
                ...n,
              })),
              (o[5] = n),
              (o[6] = a),
              (o[7] = l),
              (o[8] = s))
            : (s = o[8]),
          s
        );
      }),
      L = (0, n.f)(
        "peer/menu-button flex w-full items-center gap-2 overflow-hidden rounded-md p-2 text-left text-sm outline-none transition-[width,height,padding] hover:bg-bg-secondary hover:text-text-primary focus-visible:ring-2 focus-visible:ring-text-accent active:bg-bg-tertiary active:text-text-primary disabled:pointer-events-none disabled:opacity-50 group-has-[[data-sidebar=menu-action]]/menu-item:pr-8 aria-disabled:pointer-events-none aria-disabled:opacity-50 data-[active=true]:bg-bg-tertiary data-[active=true]:font-medium data-[active=true]:text-text-primary data-[state=open]:hover:bg-bg-secondary data-[state=open]:hover:text-text-primary group-data-[collapsible=icon]:!size-8 group-data-[collapsible=icon]:!p-2 [&>span:last-child]:truncate group-data-[collapsible=icon]:[&>span:last-child]:hidden [&>svg]:size-4 [&>svg]:shrink-0",
        {
          variants: {
            variant: {
              default: "hover:bg-bg-secondary hover:text-text-primary",
              outline:
                "bg-bg-primary shadow-[0_0_0_1px_var(--color-border-secondary)] hover:bg-bg-secondary hover:text-text-primary hover:shadow-[0_0_0_1px_var(--color-border-tertiary)]",
            },
            size: {
              default: "h-8 text-sm",
              sm: "h-7 text-xs",
              lg: "h-12 text-sm group-data-[collapsible=icon]:!p-0",
            },
          },
          defaultVariants: { variant: "default", size: "default" },
        },
      ),
      O = l.forwardRef((e, n) => {
        let l,
          s,
          o,
          c,
          d,
          u,
          m,
          f,
          p,
          h,
          b,
          x,
          g = (0, r.c)(29);
        g[0] !== e
          ? (({
              asChild: o,
              isActive: c,
              variant: d,
              size: u,
              tooltip: m,
              className: l,
              ...s
            } = e),
            (g[0] = e),
            (g[1] = l),
            (g[2] = s),
            (g[3] = o),
            (g[4] = c),
            (g[5] = d),
            (g[6] = u),
            (g[7] = m))
          : ((l = g[1]),
            (s = g[2]),
            (o = g[3]),
            (c = g[4]),
            (d = g[5]),
            (u = g[6]),
            (m = g[7]));
        let v = void 0 !== c && c,
          w = void 0 === d ? "default" : d,
          j = void 0 === u ? "default" : u,
          C = void 0 !== o && o ? i.M : "button",
          { state: N } = _();
        (g[8] !== l || g[9] !== j || g[10] !== w
          ? ((f = (0, y.c)(L({ variant: w, size: j }), l)),
            (g[8] = l),
            (g[9] = j),
            (g[10] = w),
            (g[11] = f))
          : (f = g[11]),
          g[12] !== C ||
          g[13] !== v ||
          g[14] !== s ||
          g[15] !== n ||
          g[16] !== j ||
          g[17] !== f
            ? ((p = (0, t.jsx)(C, {
                ref: n,
                "data-sidebar": "menu-button",
                "data-size": j,
                "data-active": v,
                className: f,
                ...s,
              })),
              (g[12] = C),
              (g[13] = v),
              (g[14] = s),
              (g[15] = n),
              (g[16] = j),
              (g[17] = f),
              (g[18] = p))
            : (p = g[18]));
        let S = p;
        if (!m) return S;
        if ("string" == typeof m) {
          let e;
          (g[19] !== m
            ? ((e = { children: m }), (g[19] = m), (g[20] = e))
            : (e = g[20]),
            (m = e));
        }
        g[21] !== S
          ? ((h = (0, t.jsx)(a._, { render: S })), (g[21] = S), (g[22] = h))
          : (h = g[22]);
        let k = "collapsed" !== N;
        return (
          g[23] !== k || g[24] !== m
            ? ((b = (0, t.jsx)(a.Y, { hidden: k, side: "right", ...m })),
              (g[23] = k),
              (g[24] = m),
              (g[25] = b))
            : (b = g[25]),
          g[26] !== h || g[27] !== b
            ? ((x = (0, t.jsxs)(a.W, { children: [h, b] })),
              (g[26] = h),
              (g[27] = b),
              (g[28] = x))
            : (x = g[28]),
          x
        );
      });
    j.displayName = "SidebarProvider";
    C.displayName = "Sidebar";
    N.displayName = "SidebarTrigger";
    S.displayName = "SidebarRail";
    k.displayName = "SidebarInset";
    E.displayName = "SidebarHeader";
    A.displayName = "SidebarFooter";
    I.displayName = "SidebarContent";
    T.displayName = "SidebarMenu";
    R.displayName = "SidebarMenuItem";
    O.displayName = "SidebarMenuButton";
    return {
      Sidebar: C,
      SidebarContent: I,
      SidebarFooter: A,
      SidebarHeader: E,
      SidebarInset: k,
      SidebarMenu: T,
      SidebarMenuButton: O,
      SidebarMenuItem: R,
      SidebarProvider: j,
      SidebarRail: S,
      SidebarTrigger: N,
      useSidebar: _,
    };
  })();
  const t = { jsx, jsxs, Fragment },
    r = { c: useMemoCache },
    er = { c: classNames },
    et = sidebar,
    c = { default: Link },
    v = { f: NewBadge },
    i = { x8: ExternalIcon },
    u = { Fragment };
  let el =
    "relative h-8 gap-2.5 rounded-md px-2.5 text-[13px] font-medium text-text-tertiary hover:bg-bg-secondary hover:text-text-primary data-[active=true]:bg-bg-tertiary data-[active=true]:text-text-primary group-data-[collapsible=icon]:!size-8 group-data-[collapsible=icon]:!p-0 group-data-[collapsible=icon]:justify-center [&>svg]:size-[18px] [&>svg]:shrink-0";
  function ea(e) {
    let a,
      i,
      n,
      l,
      s,
      o = (0, r.c)(12),
      { items: c, title: d, className: u } = e;
    return 0 === c.length
      ? null
      : (o[0] !== u
          ? ((a = (0, er.c)("flex flex-col", u)), (o[0] = u), (o[1] = a))
          : (a = o[1]),
        o[2] !== d
          ? ((i = d
              ? (0, t.jsx)("div", {
                  className:
                    "px-2.5 pb-1 text-[11px] font-normal leading-none text-text-quaternary group-data-[collapsible=icon]:hidden",
                  children: d,
                })
              : null),
            (o[2] = d),
            (o[3] = i))
          : (i = o[3]),
        o[4] !== c ? ((n = c.map(ei)), (o[4] = c), (o[5] = n)) : (n = o[5]),
        o[6] !== n
          ? ((l = (0, t.jsx)(et.SidebarMenu, {
              className: "gap-0.5",
              children: n,
            })),
            (o[6] = n),
            (o[7] = l))
          : (l = o[7]),
        o[8] !== a || o[9] !== i || o[10] !== l
          ? ((s = (0, t.jsxs)("div", { className: a, children: [i, l] })),
            (o[8] = a),
            (o[9] = i),
            (o[10] = l),
            (o[11] = s))
          : (s = o[11]),
        s);
  }
  function ei(e) {
    return (0, t.jsx)(en, { item: e }, e.key);
  }
  function en(e) {
    let a,
      i,
      n,
      l,
      s,
      o,
      d,
      u,
      m,
      f,
      p,
      h = (0, r.c)(37),
      { item: b } = e,
      x = b.isActive ? b.icon.fill : b.icon.line,
      g = b.external ? "a" : c.default;
    h[0] !== b.external
      ? ((a = b.external
          ? { target: "_blank", rel: "noopener noreferrer" }
          : {}),
        (h[0] = b.external),
        (h[1] = a))
      : (a = h[1]);
    let y = a,
      w = b.action ? "pr-28" : void 0;
    h[2] !== w
      ? ((i = (0, er.c)(
          "relative h-8 gap-2.5 rounded-md px-2.5 text-[13px] font-medium text-text-secondary hover:bg-bg-secondary hover:text-text-primary data-[active=true]:bg-bg-tertiary data-[active=true]:font-medium data-[active=true]:text-text-primary group-data-[collapsible=icon]:!size-8 group-data-[collapsible=icon]:!p-0 group-data-[collapsible=icon]:justify-center [&>svg]:size-[18px] [&>svg]:shrink-0",
          w,
        )),
        (h[2] = w),
        (h[3] = i))
      : (i = h[3]);
    let _ = b.isActive ? "page" : void 0,
      j = b.isActive
        ? "text-text-primary"
        : "text-text-tertiary group-hover/menu-item:text-text-primary";
    return (
      h[4] !== x || h[5] !== j
        ? ((n = (0, t.jsx)(x, { className: j })),
          (h[4] = x),
          (h[5] = j),
          (h[6] = n))
        : (n = h[6]),
      h[7] !== b.isNew
        ? ((l = b.isNew
            ? (0, t.jsx)("span", {
                "aria-hidden": !0,
                className:
                  "absolute right-1 top-1 hidden size-1.5 rounded-full bg-bg-accent group-data-[collapsible=icon]:block",
              })
            : null),
          (h[7] = b.isNew),
          (h[8] = l))
        : (l = h[8]),
      h[9] !== b.label
        ? ((s = (0, t.jsx)("span", {
            className: "truncate",
            children: b.label,
          })),
          (h[9] = b.label),
          (h[10] = s))
        : (s = h[10]),
      h[11] !== b.badge || h[12] !== b.isNew
        ? ((o = b.badge ?? (b.isNew ? (0, t.jsx)(v.f, {}) : null)),
          (h[11] = b.badge),
          (h[12] = b.isNew),
          (h[13] = o))
        : (o = h[13]),
      h[14] !== s || h[15] !== o
        ? ((d = (0, t.jsxs)("span", {
            className:
              "flex min-w-0 flex-1 items-center gap-1.5 group-data-[collapsible=icon]:hidden",
            children: [s, o],
          })),
          (h[14] = s),
          (h[15] = o),
          (h[16] = d))
        : (d = h[16]),
      h[17] !== g ||
      h[18] !== y ||
      h[19] !== b.dataTestId ||
      h[20] !== b.href ||
      h[21] !== b.onClick ||
      h[22] !== d ||
      h[23] !== _ ||
      h[24] !== n ||
      h[25] !== l
        ? ((u = (0, t.jsxs)(g, {
            href: b.href,
            "aria-current": _,
            "data-testid": b.dataTestId,
            onClick: b.onClick,
            ...y,
            children: [n, l, d],
          })),
          (h[17] = g),
          (h[18] = y),
          (h[19] = b.dataTestId),
          (h[20] = b.href),
          (h[21] = b.onClick),
          (h[22] = d),
          (h[23] = _),
          (h[24] = n),
          (h[25] = l),
          (h[26] = u))
        : (u = h[26]),
      h[27] !== b.isActive || h[28] !== b.label || h[29] !== u || h[30] !== i
        ? ((m = (0, t.jsx)(et.SidebarMenuButton, {
            className: i,
            isActive: b.isActive,
            tooltip: b.label,
            asChild: !0,
            children: u,
          })),
          (h[27] = b.isActive),
          (h[28] = b.label),
          (h[29] = u),
          (h[30] = i),
          (h[31] = m))
        : (m = h[31]),
      h[32] !== b.action
        ? ((f = b.action
            ? (0, t.jsx)("span", {
                className:
                  "absolute inset-y-0 right-1.5 flex items-center group-data-[collapsible=icon]:hidden",
                children: b.action,
              })
            : null),
          (h[32] = b.action),
          (h[33] = f))
        : (f = h[33]),
      h[34] !== m || h[35] !== f
        ? ((p = (0, t.jsxs)(et.SidebarMenuItem, { children: [m, f] })),
          (h[34] = m),
          (h[35] = f),
          (h[36] = p))
        : (p = h[36]),
      p
    );
  }
  function es(e) {
    let a,
      i,
      n,
      l = (0, r.c)(7),
      { items: s, className: o } = e;
    return 0 === s.length
      ? null
      : (l[0] !== o
          ? ((a = (0, er.c)("gap-0.5", o)), (l[0] = o), (l[1] = a))
          : (a = l[1]),
        l[2] !== s ? ((i = s.map(eo)), (l[2] = s), (l[3] = i)) : (i = l[3]),
        l[4] !== a || l[5] !== i
          ? ((n = (0, t.jsx)(et.SidebarMenu, { className: a, children: i })),
            (l[4] = a),
            (l[5] = i),
            (l[6] = n))
          : (n = l[6]),
        n);
  }
  function eo(e) {
    return (0, t.jsx)(
      et.SidebarMenuItem,
      {
        children: e.href
          ? (0, t.jsx)(ec, { item: e, href: e.href })
          : (0, t.jsx)(ed, { item: e }),
      },
      e.key,
    );
  }
  function ec(e) {
    let a,
      i,
      n,
      l,
      s = (0, r.c)(17),
      { item: o, href: d } = e,
      u = o.external ? "a" : c.default;
    s[0] !== o.external
      ? ((a = o.external
          ? { target: "_blank", rel: "noopener noreferrer" }
          : {}),
        (s[0] = o.external),
        (s[1] = a))
      : (a = s[1]);
    let m = a,
      f = o.isActive ?? !1,
      p = o.isActive ? "page" : void 0;
    return (
      s[2] !== o
        ? ((i = (0, t.jsx)(eu, { item: o })), (s[2] = o), (s[3] = i))
        : (i = s[3]),
      s[4] !== u ||
      s[5] !== m ||
      s[6] !== d ||
      s[7] !== o.ariaLabel ||
      s[8] !== o.dataTestId ||
      s[9] !== o.onClick ||
      s[10] !== p ||
      s[11] !== i
        ? ((n = (0, t.jsx)(u, {
            href: d,
            "aria-current": p,
            "aria-label": o.ariaLabel,
            "data-testid": o.dataTestId,
            onClick: o.onClick,
            ...m,
            children: i,
          })),
          (s[4] = u),
          (s[5] = m),
          (s[6] = d),
          (s[7] = o.ariaLabel),
          (s[8] = o.dataTestId),
          (s[9] = o.onClick),
          (s[10] = p),
          (s[11] = i),
          (s[12] = n))
        : (n = s[12]),
      s[13] !== o.label || s[14] !== f || s[15] !== n
        ? ((l = (0, t.jsx)(et.SidebarMenuButton, {
            className: el,
            isActive: f,
            tooltip: o.label,
            asChild: !0,
            children: n,
          })),
          (s[13] = o.label),
          (s[14] = f),
          (s[15] = n),
          (s[16] = l))
        : (l = s[16]),
      l
    );
  }
  function ed(e) {
    let a,
      i,
      n = (0, r.c)(9),
      { item: l } = e,
      s = l.isLoading || void 0;
    return (
      n[0] !== l
        ? ((a = (0, t.jsx)(eu, { item: l })), (n[0] = l), (n[1] = a))
        : (a = n[1]),
      n[2] !== l.ariaLabel ||
      n[3] !== l.dataTestId ||
      n[4] !== l.label ||
      n[5] !== l.onClick ||
      n[6] !== s ||
      n[7] !== a
        ? ((i = (0, t.jsx)(et.SidebarMenuButton, {
            type: "button",
            className: el,
            isActive: !1,
            tooltip: l.label,
            onClick: l.onClick,
            "data-testid": l.dataTestId,
            "aria-busy": s,
            "aria-label": l.ariaLabel,
            children: a,
          })),
          (n[2] = l.ariaLabel),
          (n[3] = l.dataTestId),
          (n[4] = l.label),
          (n[5] = l.onClick),
          (n[6] = s),
          (n[7] = a),
          (n[8] = i))
        : (i = n[8]),
      i
    );
  }
  function eu(e) {
    let a,
      n,
      l,
      s,
      o,
      c = (0, r.c)(16),
      { item: d } = e,
      u = d.icon,
      m = Number(d.unreadCount);
    (c[0] !== u || c[1] !== d.dataTestId || c[2] !== d.isLoading
      ? ((a = d.isLoading
          ? (0, t.jsx)("span", {
              "aria-hidden": !0,
              "data-testid": d.dataTestId ? `${d.dataTestId}-spinner` : void 0,
              className:
                "size-[18px] animate-spin rounded-full border-2 border-current border-t-transparent",
            })
          : (0, t.jsx)(u, {})),
        (c[0] = u),
        (c[1] = d.dataTestId),
        (c[2] = d.isLoading),
        (c[3] = a))
      : (a = c[3]),
      c[4] !== m
        ? ((n =
            m > 0
              ? (0, t.jsx)("span", {
                  className:
                    "absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-bg-accent text-[11px] font-medium leading-none text-text-on-accent",
                  children: m > 9 ? "9+" : m,
                })
              : null),
          (c[4] = m),
          (c[5] = n))
        : (n = c[5]),
      c[6] !== d.label
        ? ((l = (0, t.jsx)("span", {
            className: "flex-1 truncate group-data-[collapsible=icon]:hidden",
            children: d.label,
          })),
          (c[6] = d.label),
          (c[7] = l))
        : (l = c[7]));
    let f = d.badge ?? null;
    return (
      c[8] !== d.external
        ? ((s = d.external
            ? (0, t.jsx)(i.x8, {
                "aria-hidden": !0,
                className:
                  "!size-3.5 text-text-quaternary group-data-[collapsible=icon]:hidden",
              })
            : null),
          (c[8] = d.external),
          (c[9] = s))
        : (s = c[9]),
      c[10] !== a || c[11] !== n || c[12] !== l || c[13] !== f || c[14] !== s
        ? ((o = (0, t.jsxs)(t.Fragment, { children: [a, n, l, f, s] })),
          (c[10] = a),
          (c[11] = n),
          (c[12] = l),
          (c[13] = f),
          (c[14] = s),
          (c[15] = o))
        : (o = c[15]),
      o
    );
  }
  function eB(e, r) {
    return (0, t.jsxs)(
      u.Fragment,
      {
        children: [
          r > 0
            ? (0, t.jsx)("div", {
                "aria-hidden": !0,
                className:
                  "mx-auto my-2 hidden h-px w-6 bg-border-secondary group-data-[collapsible=icon]:block",
              })
            : null,
          (0, t.jsx)(ea, {
            title: e.title,
            items: e.items,
            className:
              0 === r ? "mt-2" : "mt-4 group-data-[collapsible=icon]:mt-0",
          }),
        ],
      },
      e.group,
    );
  }
  const SidebarController = (() => {
    const t = { jsx },
      r = { c: useMemoCache },
      i = sidebar;
    let l = "data-app-shell";
    const a = { p: l };
    return function (e) {
      let n,
        l,
        s = (0, r.c)(4),
        { children: o, defaultOpen: c } = e;
      return (
        s[0] === Symbol.for("react.memo_cache_sentinel")
          ? ((n = { [a.p]: "" }), (s[0] = n))
          : (n = s[0]),
        s[1] !== o || s[2] !== c
          ? ((l = (0, t.jsx)(i.SidebarProvider, {
              defaultOpen: c,
              ...n,
              children: o,
            })),
            (s[1] = o),
            (s[2] = c),
            (s[3] = l))
          : (l = s[3]),
        l
      );
    };
  })();
  const pathMatches = (e, t) => {
    let r, a;
    return (
      !!t &&
      ("/" === e ? "/" === t : (r = t) === (a = e) || r.startsWith(`${a}/`))
    );
  };
  const isNavigationActive = (() => {
    const ex = { f: pathMatches },
      e_ = routes;
    let ew = "/explore",
      ev = "watchlist";
    return (e, t, r, { watchlistRowShown: a = !0 } = {}) => {
      if ("explore" === e || "watchlist" === e) {
        let i = (0, ex.f)(ew, t),
          n = r === ev && a;
        return "watchlist" === e ? i && n : i && !n;
      }
      return (0, ex.f)(e_[e], t);
    };
  })();
  return {
    ...sidebar,
    SidebarController,
    NavGroup: ea,
    ActionList: es,
    Group: eB,
    pathMatches,
    isNavigationActive,
  };
}
