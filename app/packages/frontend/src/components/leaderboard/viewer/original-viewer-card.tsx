"use client";
import type { ComponentType, ReactNode, CSSProperties } from "react";
import type { Entry, AvatarProps } from "../entry/original-entry-row";
export type ViewerEntry = Entry & {
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  buySpendSol: number;
};
export type ViewerLinkProps = {
  href: string | null;
  prefetch: false;
  className: string;
  children?: ReactNode;
  "aria-label": string;
};
export type Stat = {
  label: string;
  value: string;
  tone: "gain" | "loss" | "neutral";
};
export function createViewerCard({
  jsx,
  jsxs,
  React,
  useMemoCache,
  useTranslation,
  useSolPrice,
  classNames,
  Avatar,
  Link,
  profileHref,
  shortWallet,
  formatPnl,
  formatVolume,
  squadHref,
  normalizeImage,
  ipfsPrefix,
}: {
  jsx: typeof import("react/jsx-runtime").jsx;
  jsxs: typeof import("react/jsx-runtime").jsxs;
  React: Pick<typeof import("react"), "createElement" | "useState">;
  useMemoCache: (size: number) => any[];
  useTranslation: () => {
    t: (key: string, values?: Record<string, string | number>) => string;
  };
  useSolPrice: (options: Record<string, never>) => { data?: number | null };
  classNames: (...parts: Array<string | undefined | false>) => string;
  Avatar: ComponentType<AvatarProps>;
  Link: ComponentType<ViewerLinkProps>;
  profileHref: (value: string) => string | null;
  shortWallet: (value: string) => string;
  formatPnl: (value: number) => string;
  formatVolume: (value: number) => string;
  squadHref: (value: { groupId: string; username: string | null }) => string;
  normalizeImage: (value: string | null) => string | undefined;
  ipfsPrefix: string;
}) {
  const a = { jsx, jsxs },
    s = { c: useMemoCache },
    i = { useState: React.useState },
    l = { f: useTranslation },
    A = { c: classNames },
    G = { Z: squadHref },
    C = { $: profileHref },
    P = { d: shortWallet },
    V = { f: normalizeImage },
    Z = { f: Avatar },
    W = { f: ipfsPrefix },
    Q = { default: Link },
    H = { w: formatPnl, v: formatVolume },
    e4 = { f: useSolPrice };
  const q = (() => {
    const t = { default: React };
    const r: ComponentType<{
      children?: ReactNode;
      size?: number | string;
      ariaLabel?: string;
      color?: string;
      ariaHidden?: boolean;
      style?: CSSProperties;
      [key: string]: unknown;
    }> = ({
      children: e,
      size: r = 24,
      ariaLabel: o,
      color: a,
      ariaHidden: n = !0,
      style: C,
      ...l
    }) =>
      t.default.createElement(
        "svg",
        {
          ...l,
          "aria-hidden": n,
          role: n ? void 0 : "img",
          width: "number" == typeof r ? `${r}px` : r,
          height: "number" == typeof r ? `${r}px` : r,
          viewBox: "0 0 24 24",
          fill: "none",
          xmlns: "http://www.w3.org/2000/svg",
          style: { color: a, ...C },
        },
        o && !n && t.default.createElement("title", null, o),
        e,
      );
    return {
      cg: (e: { className?: string }) =>
        t.default.createElement(
          r,
          { ...e, ariaLabel: "chevron-top" },
          t.default.createElement("path", {
            d: "M4 15.0001L11.2929 7.7072C11.6834 7.31668 12.3166 7.31667 12.7071 7.7072L20 15.0001",
            stroke: "currentColor",
            strokeWidth: "2",
            strokeLinecap: "round",
            strokeLinejoin: "round",
          }),
        ),
      J0: (e: { className?: string }) =>
        t.default.createElement(
          r,
          { ...e, ariaLabel: "chevron-bottom" },
          t.default.createElement("path", {
            d: "M20 9L12.7071 16.2929C12.3166 16.6834 11.6834 16.6834 11.2929 16.2929L4 9",
            stroke: "currentColor",
            strokeWidth: "2",
            strokeLinecap: "round",
            strokeLinejoin: "round",
          }),
        ),
    };
  })();
  const e6: Record<Stat["tone"], string> = {
    gain: "text-gain",
    loss: "text-loss",
    neutral: "text-text-primary",
  };
  let e5 = (e: string, t?: number | null): Stat => {
    if (null == t) return { label: e, value: "—", tone: "neutral" };
    let r = 0.005 > Math.abs(t) ? 0 : t;
    return {
      label: e,
      value: (0, H.w)(r),
      tone: 0 === r ? "neutral" : r > 0 ? "gain" : "loss",
    };
  };
  function e8(e: Stat) {
    return (0, a.jsxs)(
      "div",
      {
        className:
          "flex min-w-0 flex-col gap-0.5 rounded-xl bg-bg-tertiary px-3 py-2",
        children: [
          (0, a.jsx)("span", {
            className:
              "truncate text-[10px] font-medium uppercase tracking-wider text-text-tertiary",
            children: e.label,
          }),
          (0, a.jsx)("span", {
            className: (0, A.c)(
              "truncate text-sm font-semibold tabular-nums",
              e6[e.tone],
            ),
            children: e.value,
          }),
        ],
      },
      e.label,
    );
  }
  function e7(e: { entry?: ViewerEntry | null; className?: string }) {
    let t,
      r,
      l,
      n,
      i = (0, s.c)(9),
      { entry: d, className: o } = e;
    i[0] === Symbol.for("react.memo_cache_sentinel")
      ? ((t = {}), (i[0] = t))
      : (t = i[0]);
    let { data: c } = (0, e4.f)(t);
    return (
      i[1] !== o
        ? ((r = (0, A.c)("grid grid-cols-3 gap-2", o)), (i[1] = o), (i[2] = r))
        : (r = i[2]),
      i[3] !== d || i[4] !== c
        ? ((l = (({ entry: e, solPriceUsd: t }): Stat[] => [
            e5("Realized", e?.realizedPnlUsd),
            e5("Unrealized", e?.unrealizedPnlUsd),
            {
              label: "Volume",
              value:
                e?.buySpendSol != null && t ? (0, H.v)(e.buySpendSol * t) : "—",
              tone: "neutral",
            },
          ])({ entry: d, solPriceUsd: c }).map(e8)),
          (i[3] = d),
          (i[4] = c),
          (i[5] = l))
        : (l = i[5]),
      i[6] !== r || i[7] !== l
        ? ((n = (0, a.jsx)("div", { className: r, children: l })),
          (i[6] = r),
          (i[7] = l),
          (i[8] = n))
        : (n = i[8]),
      n
    );
  }
  function te(e: boolean) {
    return !e;
  }
  function e9(e: { entry: ViewerEntry }) {
    let t,
      r,
      n,
      d,
      o,
      c,
      u,
      m,
      p,
      x,
      b,
      h,
      f,
      g,
      y,
      w,
      j,
      v,
      N,
      _,
      k,
      z,
      I,
      U,
      S,
      F,
      L = (0, s.c)(76),
      { entry: M } = e,
      { t: $ } = (0, l.f)(),
      [E, R] = (0, i.useState)(!1),
      T = "group" === M.kind;
    L[0] !== M.username || L[1] !== M.walletAddress || L[2] !== T || L[3] !== $
      ? ((t =
          M.username ??
          (T
            ? $("web.leaderboard.squads_unnamed_row")
            : M.walletAddress
              ? (0, P.d)(M.walletAddress)
              : $("web.leaderboard.cup.anonymous"))),
        (L[0] = M.username),
        (L[1] = M.walletAddress),
        (L[2] = T),
        (L[3] = $),
        (L[4] = t))
      : (t = L[4]);
    let O = t,
      D =
        0 === M.pnlUsd
          ? "text-text-primary"
          : M.pnlUsd > 0
            ? "text-gain"
            : "text-loss";
    L[5] !== M.participantId ||
    L[6] !== M.username ||
    L[7] !== M.walletAddress ||
    L[8] !== T
      ? ((r = T
          ? (0, G.Z)({ groupId: M.participantId, username: M.username })
          : (0, C.$)(M.walletAddress ?? M.participantId)),
        (L[5] = M.participantId),
        (L[6] = M.username),
        (L[7] = M.walletAddress),
        (L[8] = T),
        (L[9] = r))
      : (r = L[9]);
    let K = r,
      B = M.walletAddress ?? M.participantId,
      J = T ? "rounded-xl" : "rounded-full";
    (L[10] !== J
      ? ((n = (0, A.c)("size-10 object-cover", J)), (L[10] = J), (L[11] = n))
      : (n = L[11]),
      L[12] !== M.profileImageUrl
        ? ((d = (0, V.f)(M.profileImageUrl)),
          (L[12] = M.profileImageUrl),
          (L[13] = d))
        : (d = L[13]),
      L[14] !== B || L[15] !== n || L[16] !== d
        ? ((o = (0, a.jsx)(Z.f, {
            address: B,
            alt: "",
            className: n,
            height: 40,
            ipfsPrefix: W.f,
            isAnonymous: !1,
            src: d,
            width: 40,
          })),
          (L[14] = B),
          (L[15] = n),
          (L[16] = d),
          (L[17] = o))
        : (o = L[17]),
      L[18] !== T || L[19] !== $
        ? ((c = T
            ? null
            : (0, a.jsx)("span", {
                className:
                  "absolute -bottom-1 left-1/2 -translate-x-1/2 rounded-full bg-white px-1.5 text-[9px] font-bold uppercase leading-[14px] text-black",
                children: $("web.leaderboard.you_badge"),
              })),
          (L[18] = T),
          (L[19] = $),
          (L[20] = c))
        : (c = L[20]),
      L[21] !== O || L[22] !== K || L[23] !== o || L[24] !== c
        ? ((u = (0, a.jsxs)(Q.default, {
            href: K,
            prefetch: !1,
            className: "relative shrink-0",
            "aria-label": O,
            children: [o, c],
          })),
          (L[21] = O),
          (L[22] = K),
          (L[23] = o),
          (L[24] = c),
          (L[25] = u))
        : (u = L[25]),
      L[26] !== O
        ? ((m = (0, a.jsx)("span", {
            className: "truncate text-sm font-semibold text-text-primary",
            children: O,
          })),
          (L[26] = O),
          (L[27] = m))
        : (m = L[27]),
      L[28] !== $
        ? ((p = $("kolscan.top_charts.profit_usd_header")),
          (L[28] = $),
          (L[29] = p))
        : (p = L[29]),
      L[30] !== p
        ? ((x = (0, a.jsx)("span", {
            className:
              "shrink-0 text-[10px] font-medium uppercase tracking-wider text-text-tertiary",
            children: p,
          })),
          (L[30] = p),
          (L[31] = x))
        : (x = L[31]),
      L[32] !== m || L[33] !== x
        ? ((b = (0, a.jsxs)("div", {
            className: "flex items-baseline justify-between gap-2",
            children: [m, x],
          })),
          (L[32] = m),
          (L[33] = x),
          (L[34] = b))
        : (b = L[34]),
      L[35] !== T || L[36] !== $
        ? ((h = $(
            T
              ? "web.leaderboard.cup.your_squad"
              : "kolscan.top_charts.your_rank",
          )),
          (L[35] = T),
          (L[36] = $),
          (L[37] = h))
        : (h = L[37]));
    let X = M.rank > 0 ? `#${M.rank}` : "#—";
    return (
      L[38] !== X
        ? ((f = (0, a.jsx)("span", {
            className: "font-semibold text-gain",
            children: X,
          })),
          (L[38] = X),
          (L[39] = f))
        : (f = L[39]),
      L[40] !== h || L[41] !== f
        ? ((g = (0, a.jsxs)("span", {
            className: "flex items-baseline gap-1 text-xs text-text-tertiary",
            children: [h, f],
          })),
          (L[40] = h),
          (L[41] = f),
          (L[42] = g))
        : (g = L[42]),
      L[43] !== D
        ? ((y = (0, A.c)("shrink-0 text-sm font-bold tabular-nums", D)),
          (L[43] = D),
          (L[44] = y))
        : (y = L[44]),
      L[45] !== M.pnlUsd
        ? ((w = (0, H.w)(M.pnlUsd)), (L[45] = M.pnlUsd), (L[46] = w))
        : (w = L[46]),
      L[47] !== y || L[48] !== w
        ? ((j = (0, a.jsx)("span", {
            className: y,
            "data-testid": "cup-rank-card-pnl",
            children: w,
          })),
          (L[47] = y),
          (L[48] = w),
          (L[49] = j))
        : (j = L[49]),
      L[50] !== g || L[51] !== j
        ? ((v = (0, a.jsxs)("div", {
            className: "flex items-baseline justify-between gap-2",
            children: [g, j],
          })),
          (L[50] = g),
          (L[51] = j),
          (L[52] = v))
        : (v = L[52]),
      L[53] !== b || L[54] !== v
        ? ((N = (0, a.jsxs)("div", {
            className: "min-w-0 flex-1",
            children: [b, v],
          })),
          (L[53] = b),
          (L[54] = v),
          (L[55] = N))
        : (N = L[55]),
      L[56] !== E || L[57] !== $
        ? ((_ = $(
            E
              ? "kolscan.top_charts.hide_stats"
              : "kolscan.top_charts.show_stats",
          )),
          (L[56] = E),
          (L[57] = $),
          (L[58] = _))
        : (_ = L[58]),
      L[59] === Symbol.for("react.memo_cache_sentinel")
        ? ((k = () => R(te)), (L[59] = k))
        : (k = L[59]),
      L[60] !== E
        ? ((z = E
            ? (0, a.jsx)(q.cg, { className: "size-4" })
            : (0, a.jsx)(q.J0, { className: "size-4" })),
          (L[60] = E),
          (L[61] = z))
        : (z = L[61]),
      L[62] !== E || L[63] !== _ || L[64] !== z
        ? ((I = (0, a.jsx)("button", {
            type: "button",
            "aria-expanded": E,
            "aria-label": _,
            onClick: k,
            className:
              "shrink-0 rounded-full p-1.5 text-text-tertiary transition-colors hover:bg-bg-tertiary hover:text-text-primary",
            children: z,
          })),
          (L[62] = E),
          (L[63] = _),
          (L[64] = z),
          (L[65] = I))
        : (I = L[65]),
      L[66] !== N || L[67] !== I || L[68] !== u
        ? ((U = (0, a.jsxs)("div", {
            className: "flex items-center gap-3",
            children: [u, N, I],
          })),
          (L[66] = N),
          (L[67] = I),
          (L[68] = u),
          (L[69] = U))
        : (U = L[69]),
      L[70] !== M || L[71] !== E
        ? ((S = E
            ? (0, a.jsx)(e7, {
                entry: M,
                className: "mt-3 border-t border-border-tertiary pt-3",
              })
            : null),
          (L[70] = M),
          (L[71] = E),
          (L[72] = S))
        : (S = L[72]),
      L[73] !== U || L[74] !== S
        ? ((F = (0, a.jsxs)("div", {
            "data-testid": "cup-rank-card",
            className: "rounded-2xl bg-bg-secondary px-4 py-3",
            children: [U, S],
          })),
          (L[73] = U),
          (L[74] = S),
          (L[75] = F))
        : (F = L[75]),
      F
    );
  }
  const Card: ComponentType<{ entry: ViewerEntry }> = e9;
  const ViewerConsumer: ComponentType<{ row: { entry: ViewerEntry } }> = ({
    row: e,
  }) => (0, a.jsx)(e9, { entry: e.entry });
  return { Card, Stats: e7, ViewerConsumer };
}
