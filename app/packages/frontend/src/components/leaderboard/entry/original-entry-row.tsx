"use client";
import type { ComponentType, ReactNode, CSSProperties } from "react";
export type Entry = {
  entryId: string;
  participantId: string;
  kind: "group" | "person";
  rank: number;
  pnlUsd: number;
  memberCount: number;
  walletAddress: string | null;
  username: string | null;
  profileImageUrl: string | null;
  isVerified: boolean;
  verifiedBadgeVisible: boolean;
};
export type Prize = { rankFrom: number; rankTo: number; amount: string };
export type AvatarProps = {
  address: string;
  alt: string;
  className: string;
  height: number;
  ipfsPrefix: string;
  isAnonymous: false;
  src?: string;
  width: number;
};
export type LinkProps = {
  href: string | null;
  prefetch: false;
  className: string;
  children?: ReactNode;
};
export function createEntryRow({
  jsx,
  jsxs,
  React,
  useMemoCache,
  useTranslation,
  classNames,
  Avatar,
  Link,
  profileHref,
  shortWallet,
  isVerified,
  formatPnl,
  squadHref,
  normalizeImage,
  ipfsPrefix,
}: {
  jsx: typeof import("react/jsx-runtime").jsx;
  jsxs: typeof import("react/jsx-runtime").jsxs;
  React: Pick<typeof import("react"), "createElement">;
  useMemoCache: (size: number) => any[];
  useTranslation: () => {
    t: (key: string, values?: Record<string, string | number>) => string;
  };
  classNames: (...parts: Array<string | undefined | false>) => string;
  Avatar: ComponentType<AvatarProps>;
  Link: ComponentType<LinkProps>;
  profileHref: (value: string) => string | null;
  shortWallet: (value: string) => string;
  isVerified: (value: Entry) => boolean;
  formatPnl: (value: number) => string;
  squadHref: (value: { groupId: string; username: string | null }) => string;
  normalizeImage: (value: string | null) => string | undefined;
  ipfsPrefix: string;
}) {
  const VerifiedBadge: ComponentType<{ size: number; className?: string }> =
    (() => {
      const t = { jsx, jsxs },
        r = { c: useMemoCache },
        n = { c: classNames };
      let a =
        "M63.85 15.5C69.82 15.5 73.8 22.38 79.03 24.43C84.45 26.55 91.98 23.92 96.08 28.02C100.18 32.12 97.55 39.65 99.67 45.07C101.72 50.3 108.6 54.28 108.6 60.25C108.6 66.22 101.72 70.2 99.67 75.43C97.55 80.85 100.18 88.38 96.08 92.48C91.98 96.58 84.45 93.95 79.03 96.07C73.8 98.12 69.82 105 63.85 105C57.88 105 53.9 98.12 48.67 96.07C43.25 93.95 35.72 96.58 31.62 92.48C27.52 88.38 30.15 80.85 28.03 75.43C25.98 70.2 19.1 66.22 19.1 60.25C19.1 54.28 25.98 50.3 28.03 45.07C30.15 39.65 27.52 32.12 31.62 28.02C35.72 23.92 43.25 26.55 48.67 24.43C53.9 22.38 57.88 15.5 63.85 15.5Z";
      return function (e) {
        let i,
          l,
          o,
          s,
          u,
          d = (0, r.c)(11),
          { size: c, className: f } = e,
          m = 179 / (c - 4),
          h = `${19.1 - m} ${15.5 - m} ${89.5 + 2 * m} ${89.5 + 2 * m}`;
        d[0] !== f
          ? ((i = (0, n.c)("shrink-0", f)), (d[0] = f), (d[1] = i))
          : (i = d[1]);
        let p = 2 * m;
        return (
          d[2] !== p
            ? ((l = (0, t.jsx)("path", {
                d: a,
                fill: "none",
                stroke: "#0F0F12",
                strokeWidth: p,
                strokeLinejoin: "round",
              })),
              (d[2] = p),
              (d[3] = l))
            : (l = d[3]),
          d[4] === Symbol.for("react.memo_cache_sentinel")
            ? ((o = (0, t.jsx)("path", { d: a, fill: "#FBBF24" })),
              (s = (0, t.jsx)("path", {
                d: "M52.6 62.2L61.05 70.65L79.95 49.95",
                fill: "none",
                stroke: "#090B18",
                strokeWidth: 10,
                strokeLinecap: "round",
                strokeLinejoin: "round",
              })),
              (d[4] = o),
              (d[5] = s))
            : ((o = d[4]), (s = d[5])),
          d[6] !== c || d[7] !== i || d[8] !== l || d[9] !== h
            ? ((u = (0, t.jsxs)("svg", {
                width: c,
                height: c,
                viewBox: h,
                fill: "none",
                role: "img",
                "aria-label": "Verified account",
                className: i,
                children: [l, o, s],
              })),
              (d[6] = c),
              (d[7] = i),
              (d[8] = l),
              (d[9] = h),
              (d[10] = u))
            : (u = d[10]),
          u
        );
      };
    })();
  const Crown: ComponentType<{ className?: string; "aria-hidden"?: boolean }> =
    (() => {
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
      return (e) =>
        t.default.createElement(
          r,
          { ...e, ariaLabel: "crown, vip" },
          t.default.createElement("path", {
            d: "M4.33416 18.204L2 7L8 10L12 4L16 10L22 7L19.6658 18.204C19.5692 18.6677 19.1605 19 18.6869 19H5.31314C4.83946 19 4.43077 18.6677 4.33416 18.204Z",
            stroke: "currentColor",
            strokeWidth: "2",
            strokeLinecap: "square",
            strokeLinejoin: "round",
          }),
        );
    })();
  const a = { jsx, jsxs },
    s = { c: useMemoCache },
    l = { f: useTranslation },
    n: { S: Record<number, string | undefined> } = {
      S: { 1: "text-[#FFD700]", 2: "text-[#C0C0C0]", 3: "text-[#CD7F32]" },
    },
    A = { c: classNames },
    G = { Z: squadHref },
    C = { $: profileHref },
    P = { d: shortWallet },
    V = { f: normalizeImage },
    Z = { f: Avatar },
    W = { f: ipfsPrefix },
    J = { f: isVerified },
    B = { f: VerifiedBadge },
    q = { zN: Crown },
    Q = { default: Link },
    H = { w: formatPnl };
  const Row: ComponentType<{ entry: Entry; prize?: Prize | null }> = function X(
    e,
  ) {
    let t,
      r,
      i,
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
      I = (0, s.c)(63),
      { entry: U, prize: S } = e,
      { t: F } = (0, l.f)(),
      L = "group" === U.kind,
      M = n.S[U.rank];
    I[0] !== U.username || I[1] !== L || I[2] !== F
      ? ((t =
          U.username ??
          F(
            L
              ? "web.leaderboard.squads_unnamed_row"
              : "web.leaderboard.cup.anonymous",
          )),
        (I[0] = U.username),
        (I[1] = L),
        (I[2] = F),
        (I[3] = t))
      : (t = I[3]);
    let $ = t,
      E =
        0 === U.pnlUsd
          ? "text-text-primary"
          : U.pnlUsd > 0
            ? "text-gain"
            : "text-loss",
      R = U.entryId,
      T = M ?? "text-text-tertiary";
    I[4] !== T
      ? ((r = (0, A.c)("w-7 shrink-0 text-xs font-semibold tabular-nums", T)),
        (I[4] = T),
        (I[5] = r))
      : (r = I[5]);
    let O = U.rank > 0 ? U.rank : "–";
    if (
      (I[6] !== r || I[7] !== O
        ? ((i = (0, a.jsx)("span", { className: r, children: O })),
          (I[6] = r),
          (I[7] = O),
          (I[8] = i))
        : (i = I[8]),
      I[9] !== U)
    )
      ((d =
        "group" === U.kind
          ? (0, G.Z)({ groupId: U.participantId, username: U.username })
          : (0, C.$)(U.walletAddress ?? U.participantId)),
        (I[9] = U),
        (I[10] = d));
    else d = I[10];
    let D = U.walletAddress ?? U.participantId,
      K = L ? "rounded-xl" : "rounded-full";
    (I[11] !== K
      ? ((o = (0, A.c)("size-10 shrink-0 object-cover", K)),
        (I[11] = K),
        (I[12] = o))
      : (o = I[12]),
      I[13] !== U.profileImageUrl
        ? ((c = (0, V.f)(U.profileImageUrl)),
          (I[13] = U.profileImageUrl),
          (I[14] = c))
        : (c = I[14]),
      I[15] !== o || I[16] !== c || I[17] !== D
        ? ((u = (0, a.jsx)(Z.f, {
            address: D,
            alt: "",
            className: o,
            height: 40,
            ipfsPrefix: W.f,
            isAnonymous: !1,
            src: c,
            width: 40,
          })),
          (I[15] = o),
          (I[16] = c),
          (I[17] = D),
          (I[18] = u))
        : (u = I[18]));
    let X = M ?? "text-text-primary";
    if (
      (I[19] !== X
        ? ((m = (0, A.c)("truncate text-sm font-semibold hover:underline", X)),
          (I[19] = X),
          (I[20] = m))
        : (m = I[20]),
      I[21] !== $ || I[22] !== m
        ? ((p = (0, a.jsx)("span", { className: m, children: $ })),
          (I[21] = $),
          (I[22] = m),
          (I[23] = p))
        : (p = I[23]),
      I[24] !== U
        ? ((x = (0, J.f)(U) ? (0, a.jsx)(B.f, { size: 18 }) : null),
          (I[24] = U),
          (I[25] = x))
        : (x = I[25]),
      I[26] !== M
        ? ((b = M
            ? (0, a.jsx)(q.zN, {
                "aria-hidden": !0,
                className: (0, A.c)("size-3.5 shrink-0", M),
              })
            : null),
          (I[26] = M),
          (I[27] = b))
        : (b = I[27]),
      I[28] !== p || I[29] !== x || I[30] !== b
        ? ((h = (0, a.jsxs)("span", {
            className: "flex min-w-0 items-center gap-1.5",
            children: [p, x, b],
          })),
          (I[28] = p),
          (I[29] = x),
          (I[30] = b),
          (I[31] = h))
        : (h = I[31]),
      I[32] !== U.memberCount ||
      I[33] !== U.walletAddress ||
      I[34] !== L ||
      I[35] !== F
        ? ((f = L
            ? (0, a.jsx)("span", {
                className: "block truncate text-xs text-text-tertiary",
                children: F("profile.squads.info.member_count", {
                  count: U.memberCount,
                }),
              })
            : U.walletAddress
              ? (0, a.jsx)("span", {
                  className: "block truncate text-xs text-text-tertiary",
                  children: (0, P.d)(U.walletAddress),
                })
              : null),
          (I[32] = U.memberCount),
          (I[33] = U.walletAddress),
          (I[34] = L),
          (I[35] = F),
          (I[36] = f))
        : (f = I[36]),
      I[37] !== h || I[38] !== f
        ? ((g = (0, a.jsxs)("span", {
            className: "min-w-0",
            children: [h, f],
          })),
          (I[37] = h),
          (I[38] = f),
          (I[39] = g))
        : (g = I[39]),
      I[40] !== u || I[41] !== g || I[42] !== d
        ? ((y = (0, a.jsxs)(Q.default, {
            href: d,
            prefetch: !1,
            className: "flex min-w-0 flex-1 items-center gap-3",
            children: [u, g],
          })),
          (I[40] = u),
          (I[41] = g),
          (I[42] = d),
          (I[43] = y))
        : (y = I[43]),
      I[44] !== E
        ? ((w = (0, A.c)("text-sm font-bold tabular-nums", E)),
          (I[44] = E),
          (I[45] = w))
        : (w = I[45]),
      I[46] !== U.pnlUsd)
    ) {
      let e;
      ((e = U.pnlUsd),
        (j = `${e > 0 ? "+" : ""}${(0, H.w)(e)}`),
        (I[46] = U.pnlUsd),
        (I[47] = j));
    } else j = I[47];
    return (
      I[48] !== w || I[49] !== j
        ? ((v = (0, a.jsx)("span", { className: w, children: j })),
          (I[48] = w),
          (I[49] = j),
          (I[50] = v))
        : (v = I[50]),
      I[51] !== S
        ? ((N = S
            ? (0, a.jsx)("span", {
                className:
                  "rounded-full bg-bg-tertiary px-2 py-0.5 text-[10px] font-semibold text-text-primary",
                "data-testid": "cup-entry-prize",
                children: S.amount,
              })
            : null),
          (I[51] = S),
          (I[52] = N))
        : (N = I[52]),
      I[53] !== v || I[54] !== N
        ? ((_ = (0, a.jsxs)("span", {
            className: "ml-auto flex shrink-0 flex-col items-end gap-1",
            children: [v, N],
          })),
          (I[53] = v),
          (I[54] = N),
          (I[55] = _))
        : (_ = I[55]),
      I[56] !== y || I[57] !== _ || I[58] !== i
        ? ((k = (0, a.jsxs)("div", {
            className: "flex items-center gap-3",
            children: [i, y, _],
          })),
          (I[56] = y),
          (I[57] = _),
          (I[58] = i),
          (I[59] = k))
        : (k = I[59]),
      I[60] !== U.entryId || I[61] !== k
        ? ((z = (0, a.jsx)("div", {
            "data-testid": "cup-entry-row",
            "data-entry-id": R,
            className: "px-4 py-3 transition-colors hover:bg-bg-secondary",
            children: k,
          })),
          (I[60] = U.entryId),
          (I[61] = k),
          (I[62] = z))
        : (z = I[62]),
      z
    );
  };
  const X = Row;
  const EntryConsumer: ComponentType<{
    row: { entry: Entry; prize?: Prize | null };
  }> = ({ row: e }) => (0, a.jsx)(X, { entry: e.entry, prize: e.prize });
  return { Row, EntryConsumer };
}
