"use client";
import type { ComponentType, ReactNode } from "react";
import type { ViewerEntry } from "../viewer/original-viewer-card";
import type { Prize } from "../original-prizes";
export type Competition = {
  id: string;
  kind: "person" | "group";
  phase: string;
  title: string;
  startsAt: string | null;
  endsAt: string | null;
  prizes: Prize[];
  [key: string]: unknown;
};
export type Buckets = {
  live: Competition[];
  upcoming: Competition[];
  past: Competition[];
};
export type Detail = {
  competition: Competition;
  leaderboard: { entries: ViewerEntry[] };
  viewer?: { entry: ViewerEntry | null } | null;
};
export type Snapshot<T> = {
  data?: T;
  isError: boolean;
  isLoading: boolean;
  refetch: () => unknown;
};
export type ListSnapshot = Snapshot<Buckets>;
export type DetailSnapshot = Snapshot<Detail>;
export type BoardClient = {
  useList: (o: { isVisible: true }) => ListSnapshot;
  useDetail: (o: {
    idOrSlug: string | null;
    isVisible: true;
  }) => DetailSnapshot;
  selectCompetition: (
    data: Buckets | undefined,
    kind: "person" | "group",
  ) => Competition | null;
};
export type BoardProps = {
  kind: "person" | "group";
  periodControl?: ReactNode;
  periodControlTopPx?: number | null;
  periodControlLeadClassName?: string;
};
export type ControlProps = {
  periodControl?: ReactNode;
  periodControlTopPx?: number | null;
};
type BoardItem =
  | { type: "hero" }
  | { type: "highlights"; competitionId: string; entries: ViewerEntry[] }
  | { type: "pending" }
  | { type: "viewer"; entry: ViewerEntry }
  | {
      type: "section";
      section: "final" | "standings" | "prizes";
      isCardTop: boolean;
    }
  | { type: "row"; entry: ViewerEntry; prize: Prize | null; isLast: boolean }
  | { type: "prize_line"; paidRanks: number }
  | { type: "tier"; prize: Prize; isLast: boolean };
export type HeroProps = {
  kind: "person" | "group";
  topControl?: ReactNode;
  topControlTopPx: number | null;
  className?: string;
  competition: Competition | null | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  onOpenRules: () => void;
};
export type HighlightProps = {
  competitionId: string;
  entries: ViewerEntry[];
  window: { fromMs: number; toMs: number } | null;
};
export type RulesProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  competition: Competition;
};
export type CardProps = {
  ariaLabel: string;
  testId?: string;
  children?: ReactNode;
};
export function createCompetitionBoard({
  jsx,
  jsxs,
  React,
  useMemoCache,
  useTranslation,
  useReducedMotion,
  classNames,
  client,
  Hero,
  Highlights,
  Rules,
  Card,
  EntryRow,
  ViewerCard,
  PrizeTier,
  findPrize,
}: {
  jsx: typeof import("react/jsx-runtime").jsx;
  jsxs: typeof import("react/jsx-runtime").jsxs;
  React: Pick<typeof import("react"), "useState">;
  useMemoCache: (size: number) => any[];
  useTranslation: () => {
    t: (key: string, values?: Record<string, string | number>) => string;
  };
  useReducedMotion: () => boolean | null | undefined;
  classNames: (...parts: Array<string | undefined | false>) => string;
  client: BoardClient;
  Hero: ComponentType<HeroProps>;
  Highlights: ComponentType<HighlightProps>;
  Rules: ComponentType<RulesProps>;
  Card: ComponentType<CardProps>;
  EntryRow: ComponentType<{ entry: ViewerEntry; prize?: Prize | null }>;
  ViewerCard: ComponentType<{ entry: ViewerEntry }>;
  PrizeTier: ComponentType<{ prize: Prize }>;
  findPrize: (prizes: Prize[], rank: number) => Prize | null;
}) {
  const a = { jsx, jsxs },
    s = { c: useMemoCache },
    i = { useState: React.useState },
    l = { f: useTranslation },
    U = { f: useReducedMotion },
    A = { c: classNames },
    n = { B: Card },
    td = { f: client.useList },
    ti = { f: client.useDetail },
    $ = {
      y: client.selectCompetition,
      V: (e: Prize[]) => e.reduce((e, t) => Math.max(e, t.rankTo), 0),
      J: findPrize,
    };
  const e$ = Hero,
    e3 = Highlights,
    tn = Rules,
    e9 = ViewerCard,
    X = EntryRow,
    D = PrizeTier;
  const T: ComponentType<{ title: string; isCardTop: boolean }> = (e) => {
    let t,
      r,
      l = (0, s.c)(5),
      { title: n, isCardTop: i } = e,
      d = i ? "pt-4" : "pt-2";
    return (
      l[0] !== d
        ? ((t = (0, A.c)(
            "px-4 pb-1 text-xs font-medium uppercase tracking-wider text-text-tertiary",
            d,
          )),
          (l[0] = d),
          (l[1] = t))
        : (t = l[1]),
      l[2] !== t || l[3] !== n
        ? ((r = (0, a.jsx)("h2", { className: t, children: n })),
          (l[2] = t),
          (l[3] = n),
          (l[4] = r))
        : (r = l[4]),
      r
    );
  };
  const O: ComponentType<{ paidRanks: number }> = (e) => {
    let t,
      r,
      n,
      i,
      d,
      o = (0, s.c)(9),
      { paidRanks: c } = e,
      { t: u } = (0, l.f)();
    return (
      o[0] === Symbol.for("react.memo_cache_sentinel")
        ? ((t = (0, a.jsx)("span", {
            "aria-hidden": !0,
            className: "h-px flex-1 bg-text-primary",
          })),
          (o[0] = t))
        : (t = o[0]),
      o[1] !== c || o[2] !== u
        ? ((r = u("web.leaderboard.cup.paid_ranks", { count: c })),
          (o[1] = c),
          (o[2] = u),
          (o[3] = r))
        : (r = o[3]),
      o[4] !== r
        ? ((n = (0, a.jsx)("span", {
            className:
              "text-[10px] font-semibold uppercase tracking-wider text-text-primary",
            children: r,
          })),
          (o[4] = r),
          (o[5] = n))
        : (n = o[5]),
      o[6] === Symbol.for("react.memo_cache_sentinel")
        ? ((i = (0, a.jsx)("span", {
            "aria-hidden": !0,
            className: "h-px flex-1 bg-text-primary",
          })),
          (o[6] = i))
        : (i = o[6]),
      o[7] !== n
        ? ((d = (0, a.jsxs)("div", {
            className: "flex items-center gap-3 px-4 py-2",
            "data-testid": "cup-payline",
            children: [t, n, i],
          })),
          (o[7] = n),
          (o[8] = d))
        : (d = o[8]),
      d
    );
  };
  const K: ComponentType<{ title: string; body: string; testId: string }> = (
    e,
  ) => {
    let t,
      r,
      l,
      n = (0, s.c)(8),
      { title: i, body: d, testId: o } = e;
    return (
      n[0] !== i
        ? ((t = (0, a.jsx)("p", {
            className: "text-base font-semibold text-text-primary",
            children: i,
          })),
          (n[0] = i),
          (n[1] = t))
        : (t = n[1]),
      n[2] !== d
        ? ((r = (0, a.jsx)("p", {
            className: "text-sm text-text-secondary",
            children: d,
          })),
          (n[2] = d),
          (n[3] = r))
        : (r = n[3]),
      n[4] !== t || n[5] !== r || n[6] !== o
        ? ((l = (0, a.jsxs)("div", {
            className:
              "flex flex-col items-center gap-2 rounded-3xl border border-border-tertiary px-6 py-8 text-center",
            "data-testid": o,
            children: [t, r],
          })),
          (n[4] = t),
          (n[5] = r),
          (n[6] = o),
          (n[7] = l))
        : (l = n[7]),
      l
    );
  };
  function tc(e: BoardItem) {
    return "highlights" === e.type;
  }
  function tu(e: BoardItem) {
    return "pending" === e.type;
  }
  function tm(e: BoardItem) {
    return (
      "viewer" === e.type ||
      "section" === e.type ||
      "row" === e.type ||
      "prize_line" === e.type ||
      "tier" === e.type
    );
  }
  function to(e: BoardProps) {
    let t,
      r,
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
      N = (0, s.c)(37),
      {
        kind: _,
        periodControl: k,
        periodControlTopPx: z,
        periodControlLeadClassName: I,
      } = e,
      S = void 0 === z ? null : z,
      { t: C } = (0, l.f)(),
      P = (() => {
        let e,
          t = (0, s.c)(2),
          { t: r } = (0, l.f)();
        return (
          t[0] !== r
            ? ((e = (e: string) =>
                "final" === e
                  ? r("web.leaderboard.cup.final_results")
                  : "prizes" === e
                    ? r("web.leaderboard.cup.prize_breakdown")
                    : r("web.leaderboard.cup.standings")),
              (t[0] = r),
              (t[1] = e))
            : (e = t[1]),
          e
        );
      })(),
      q = (0, U.f)() ?? !1,
      [F, L] = (0, i.useState)(!1),
      {
        list: M,
        detail: E,
        competition: R,
      }: {
        list: ListSnapshot;
        detail: DetailSnapshot;
        competition: Competition | null | undefined;
      } = ((f = (0, s.c)(10))[0] === Symbol.for("react.memo_cache_sentinel")
        ? ((p = { isVisible: !0 }), (f[0] = p))
        : (p = f[0]),
      (g = (0, td.f)(p)),
      f[1] !== _ || f[2] !== g.data
        ? ((x = (0, $.y)(g.data, _)), (f[1] = _), (f[2] = g.data), (f[3] = x))
        : (x = f[3]),
      (y = x),
      (w = y?.id ?? null),
      f[4] !== w
        ? ((b = { idOrSlug: w, isVisible: !0 }), (f[4] = w), (f[5] = b))
        : (b = f[5]),
      (j = (0, ti.f)(b)),
      (v = j.data?.competition ?? y),
      f[6] !== j || f[7] !== g || f[8] !== v
        ? ((h = { list: g, detail: j, competition: v }),
          (f[6] = j),
          (f[7] = g),
          (f[8] = v),
          (f[9] = h))
        : (h = f[9]),
      h);
    if (
      N[0] !== R ||
      N[1] !== E.data ||
      N[2] !== _ ||
      N[3] !== M ||
      N[4] !== k ||
      N[5] !== I ||
      N[6] !== S ||
      N[7] !== q ||
      N[8] !== P ||
      N[9] !== C
    ) {
      let e,
        s,
        l,
        i,
        u = (({
          competition: e,
          detail: t,
        }: {
          competition: Competition | null | undefined;
          detail: Detail | null | undefined;
        }): BoardItem[] => {
          let r: BoardItem[] = [{ type: "hero" }];
          if (!e) return r;
          let a = t?.leaderboard.entries ?? [],
            s = a.length > 0;
          (s && r.push({ type: "highlights", competitionId: e.id, entries: a }),
            !s && t && "live" === e.phase && r.push({ type: "pending" }));
          let l = s || e.prizes.length > 0,
            n = t?.viewer?.entry ?? null;
          l && n && r.push({ type: "viewer", entry: n });
          let i = !(l && n);
          if (s) {
            let t = (0, $.V)(e.prizes);
            (r.push({
              type: "section",
              section: "ended" === e.phase ? "final" : "standings",
              isCardTop: i,
            }),
              a.forEach((s, l) => {
                let n = l === a.length - 1;
                (r.push({
                  type: "row",
                  entry: s,
                  prize: (0, $.J)(e.prizes, s.rank),
                  isLast: n,
                }),
                  t > 0 &&
                    s.rank === t &&
                    !n &&
                    r.push({ type: "prize_line", paidRanks: t }));
              }));
          } else
            e.prizes.length > 0 &&
              (r.push({ type: "section", section: "prizes", isCardTop: i }),
              e.prizes.forEach((t, a) => {
                r.push({
                  type: "tier",
                  prize: t,
                  isLast: a === e.prizes.length - 1,
                });
              }));
          return r;
        })({ competition: R, detail: E.data }),
        m = u.filter(tm),
        p = u.some(tu),
        x = u.find(tc),
        b = m.length > 0 || p || void 0 !== x;
      ((t = "flex flex-col gap-4"),
        (r = "cup-leaderboard-board"),
        (d = _),
        N[15] !== M
          ? ((e = () => void M.refetch()), (N[15] = M), (N[16] = e))
          : (e = N[16]),
        N[17] === Symbol.for("react.memo_cache_sentinel")
          ? ((s = () => L(!0)), (N[17] = s))
          : (s = N[17]),
        N[18] !== R ||
        N[19] !== _ ||
        N[20] !== M.isError ||
        N[21] !== M.isLoading ||
        N[22] !== k ||
        N[23] !== I ||
        N[24] !== S ||
        N[25] !== e
          ? ((o = (0, a.jsx)(e$, {
              kind: _,
              topControl: k,
              topControlTopPx: S,
              className: I,
              competition: R,
              isLoading: M.isLoading,
              isError: M.isError,
              onRetry: e,
              onOpenRules: s,
            })),
            (N[18] = R),
            (N[19] = _),
            (N[20] = M.isError),
            (N[21] = M.isLoading),
            (N[22] = k),
            (N[23] = I),
            (N[24] = S),
            (N[25] = e),
            (N[26] = o))
          : (o = N[26]),
        (c = b
          ? (0, a.jsxs)("div", {
              className: (0, A.c)("flex flex-col gap-4", !q && "cup-board-in"),
              "data-testid": "cup-board-below-hero",
              children: [
                x && R
                  ? (0, a.jsx)(e3, {
                      competitionId: x.competitionId,
                      entries: x.entries,
                      window:
                        ((l = R.startsAt ? Date.parse(R.startsAt) : 0 / 0),
                        (i = R.endsAt ? Date.parse(R.endsAt) : 0 / 0),
                        Number.isFinite(l) && Number.isFinite(i) && !(i <= l)
                          ? { fromMs: l, toMs: i }
                          : null),
                    })
                  : null,
                p
                  ? (0, a.jsx)(K, {
                      title: C("web.leaderboard.cup.pending_title"),
                      body: C("web.leaderboard.cup.pending_body"),
                      testId: "cup-pending",
                    })
                  : null,
                m.length > 0
                  ? (0, a.jsx)(n.B, {
                      ariaLabel: C("web.leaderboard.rankings_aria"),
                      testId: "cup-board-card",
                      children: m.map((e, t) =>
                        (0, a.jsxs)(
                          "div",
                          {
                            className: (0, A.c)(
                              t > 0 &&
                                ("row" === e.type || "tier" === e.type) &&
                                "border-t border-border-primary",
                            ),
                            children: [
                              "viewer" === e.type
                                ? (0, a.jsx)("div", {
                                    className: "p-2",
                                    children: (0, a.jsx)(e9, {
                                      entry: e.entry,
                                    }),
                                  })
                                : null,
                              "section" === e.type
                                ? (0, a.jsx)(T, {
                                    title: P(e.section),
                                    isCardTop: e.isCardTop,
                                  })
                                : null,
                              "row" === e.type
                                ? (0, a.jsx)(X, {
                                    entry: e.entry,
                                    prize: e.prize,
                                  })
                                : null,
                              "prize_line" === e.type
                                ? (0, a.jsx)(O, { paidRanks: e.paidRanks })
                                : null,
                              "tier" === e.type
                                ? (0, a.jsx)(D, { prize: e.prize })
                                : null,
                            ],
                          },
                          ((e: BoardItem) => {
                            switch (e.type) {
                              case "row":
                                return `row:${e.entry.entryId}`;
                              case "tier":
                                return `tier:${e.prize.rankFrom}`;
                              case "section":
                                return `section:${e.section}`;
                              default:
                                return e.type;
                            }
                          })(e),
                        ),
                      ),
                    })
                  : null,
              ],
            })
          : null),
        (N[0] = R),
        (N[1] = E.data),
        (N[2] = _),
        (N[3] = M),
        (N[4] = k),
        (N[5] = I),
        (N[6] = S),
        (N[7] = q),
        (N[8] = P),
        (N[9] = C),
        (N[10] = t),
        (N[11] = r),
        (N[12] = d),
        (N[13] = o),
        (N[14] = c));
    } else ((t = N[10]), (r = N[11]), (d = N[12]), (o = N[13]), (c = N[14]));
    return (
      N[27] !== R || N[28] !== F
        ? ((u = R
            ? (0, a.jsx)(tn, { open: F, onOpenChange: L, competition: R })
            : null),
          (N[27] = R),
          (N[28] = F),
          (N[29] = u))
        : (u = N[29]),
      N[30] !== t ||
      N[31] !== r ||
      N[32] !== d ||
      N[33] !== o ||
      N[34] !== c ||
      N[35] !== u
        ? ((m = (0, a.jsxs)("div", {
            className: t,
            "data-testid": r,
            "data-cup-kind": d,
            children: [o, c, u],
          })),
          (N[30] = t),
          (N[31] = r),
          (N[32] = d),
          (N[33] = o),
          (N[34] = c),
          (N[35] = u),
          (N[36] = m))
        : (m = N[36]),
      m
    );
  }
  const PersonConsumer: ComponentType<ControlProps> = ({
    periodControl: ef,
    periodControlTopPx: eh,
  }) =>
    (0, a.jsx)(to, {
      kind: "person",
      periodControl: ef,
      periodControlTopPx: eh,
      periodControlLeadClassName:
        "[--cup-lead:79px] sm:[--cup-lead:61px] lg:[--cup-lead:43px]",
    });
  const GroupConsumer: ComponentType<ControlProps> = ({
    periodControl: en,
    periodControlTopPx: el,
  }) =>
    (0, a.jsx)(to, {
      kind: "group",
      periodControl: en,
      periodControlTopPx: el,
      periodControlLeadClassName: "[--cup-lead:8px]",
    });
  return { Board: to, PersonConsumer, GroupConsumer };
}
