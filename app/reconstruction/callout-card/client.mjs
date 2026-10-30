// Complete original display owners. Required existing APIs stay explicit; captured factories never execute.
export function createCalloutCard(capabilities) {
  const {
    jsx,
    jsxs,
    Fragment,
    useMemoCache,
    useState,
    useRef,
    useEffect,
    useTranslation,
    classNames,
    profileRoute,
    Avatar,
    ProfileHover,
    ProfileLink,
    Link,
    AvatarDecoration,
    useDecorationKey,
    VerifiedBadge,
    RelativeTime,
    RichText,
    ImagePreview,
    Video,
    ShareMenu,
    useReplyLike,
    Comments,
    useIpfsPrefix,
    formatCount,
    ShareIcon,
    OutlineHeart,
    FilledHeart,
    CommentIcon,
    ResizeObserver,
  } = capabilities;
  for (const [name, value] of Object.entries({
    jsx,
    jsxs,
    useMemoCache,
    useState,
    useRef,
    useEffect,
    useTranslation,
    classNames,
    profileRoute,
    useDecorationKey,
    useReplyLike,
    useIpfsPrefix,
    formatCount,
  }))
    if (typeof value !== "function")
      throw new TypeError("Explicit callout capability required: " + name);
  for (const [name, value] of Object.entries({
    Fragment,
    Avatar,
    ProfileHover,
    ProfileLink,
    Link,
    AvatarDecoration,
    VerifiedBadge,
    RelativeTime,
    RichText,
    ImagePreview,
    Video,
    ShareMenu,
    Comments,
    ShareIcon,
    OutlineHeart,
    FilledHeart,
    CommentIcon,
  }))
    if (value == null)
      throw new TypeError("Explicit callout renderer required: " + name);
  if (!Object.hasOwn(capabilities, "ResizeObserver"))
    throw new TypeError("Explicit ResizeObserver presence/absence required");
  const t = { jsx, jsxs, Fragment },
    l = { c: useMemoCache },
    o = { useState, useRef, useEffect },
    c = { f: useTranslation },
    z = { c: classNames },
    a = { $: profileRoute },
    r = { f: Avatar },
    s = { f: ProfileHover },
    k = { o: ProfileLink },
    n = { default: Link },
    R = { f: AvatarDecoration },
    W = { f: useDecorationKey },
    i = { f: VerifiedBadge },
    N = { f: RelativeTime },
    y = { f: RichText },
    d = { f: ImagePreview },
    u = { f: Video },
    x = { f: ShareMenu },
    g = { f: useReplyLike },
    ed = Comments,
    P = { useIpfsPrefix },
    L = { O: formatCount },
    p = { q4: ShareIcon, cJ: OutlineHeart, Z2: CommentIcon },
    m = { cJ: FilledHeart };
  const f = {
      I: {
        terminal:
          "inline-flex h-6 items-center gap-1 rounded-md px-[5px] text-[11px] leading-4 font-medium tabular-nums",
        comfortable:
          "inline-flex h-6 items-center gap-1 rounded-md px-[5px] text-xs leading-4 font-medium tabular-nums",
      },
      L: "transition-colors outline-none hover:bg-bg-quaternary focus-visible:ring-2 focus-visible:ring-text-accent",
      d: "size-3.5 shrink-0",
    },
    h = { $: "hover:bg-hot/10 hover:text-hot", k: "text-hot" },
    ev = {
      y: (e) => {
        let t = e.split(/[?#]/, 1)[0] ?? e;
        return /\.(mp4|mov)$/i.test(t);
      },
    };
  const ew = { 2: "line-clamp-2", 3: "line-clamp-3", 4: "line-clamp-4" };
  function em(e) {
    let a,
      s,
      r,
      i,
      n,
      c = (0, l.c)(48),
      {
        updates: d,
        size: u,
        collapsible: m,
        expandableComments: p,
        authorName: x,
        authorAddress: f,
        authorUserId: h,
        authorAvatarUrl: g,
        authorAvatarDecoration: y,
        authorVerified: b,
        authorProfileId: v,
        timeAlign: w,
        timeDensity: j,
        hostHref: _,
        onHostClick: k,
        className: N,
        dense: I,
      } = e,
      C = void 0 === u ? "sm" : u,
      S = void 0 !== p && p,
      A = void 0 !== b && b,
      U = void 0 === v ? "" : v,
      L = void 0 === w ? "start" : w,
      P = void 0 === j ? "comfortable" : j,
      q = void 0 !== I && I,
      [O, T] = (0, o.useState)(!1);
    if (!d?.length) return null;
    let E = d.length - 1,
      R = void 0 !== m && m && !O && E > 0;
    c[0] !== R || c[1] !== d
      ? ((a = R ? d.slice(-1) : d), (c[0] = R), (c[1] = d), (c[2] = a))
      : (a = c[2]);
    let $ = a,
      D = !!(x && f),
      F = D ? void 0 : "gap-0.5 pt-1.5";
    if (
      (c[3] !== F
        ? ((s = (0, z.c)("flex w-full flex-col", F)), (c[3] = F), (c[4] = s))
        : (s = c[4]),
      c[5] !== q || c[6] !== D || c[7] !== R || c[8] !== C
        ? ((r = R
            ? (0, t.jsx)(ep, {
                size: C,
                dense: q,
                hasIdentity: D,
                onExpand: () => T(!0),
              })
            : null),
          (c[5] = q),
          (c[6] = D),
          (c[7] = R),
          (c[8] = C),
          (c[9] = r))
        : (r = c[9]),
      c[10] !== f ||
        c[11] !== y ||
        c[12] !== g ||
        c[13] !== x ||
        c[14] !== U ||
        c[15] !== h ||
        c[16] !== A ||
        c[17] !== N ||
        c[18] !== q ||
        c[19] !== S ||
        c[20] !== _ ||
        c[21] !== k ||
        c[22] !== C ||
        c[23] !== L ||
        c[24] !== P ||
        c[25] !== $)
    ) {
      let e;
      (c[27] !== f ||
      c[28] !== y ||
      c[29] !== g ||
      c[30] !== x ||
      c[31] !== U ||
      c[32] !== h ||
      c[33] !== A ||
      c[34] !== N ||
      c[35] !== q ||
      c[36] !== S ||
      c[37] !== _ ||
      c[38] !== k ||
      c[39] !== C ||
      c[40] !== L ||
      c[41] !== P ||
      c[42] !== $.length
        ? ((e = (e, l) =>
            (0, t.jsx)(
              ef,
              {
                update: e,
                size: C,
                expandableComments: S,
                authorName: x,
                authorAddress: f,
                authorUserId: h,
                authorAvatarUrl: g,
                authorAvatarDecoration: y,
                authorVerified: A,
                authorProfileId: U,
                timeAlign: L,
                timeDensity: P,
                hostHref: _,
                onHostClick: k,
                connectsToNext: l < $.length - 1,
                className: N,
                dense: q,
              },
              e.id,
            )),
          (c[27] = f),
          (c[28] = y),
          (c[29] = g),
          (c[30] = x),
          (c[31] = U),
          (c[32] = h),
          (c[33] = A),
          (c[34] = N),
          (c[35] = q),
          (c[36] = S),
          (c[37] = _),
          (c[38] = k),
          (c[39] = C),
          (c[40] = L),
          (c[41] = P),
          (c[42] = $.length),
          (c[43] = e))
        : (e = c[43]),
        (i = $.map(e)),
        (c[10] = f),
        (c[11] = y),
        (c[12] = g),
        (c[13] = x),
        (c[14] = U),
        (c[15] = h),
        (c[16] = A),
        (c[17] = N),
        (c[18] = q),
        (c[19] = S),
        (c[20] = _),
        (c[21] = k),
        (c[22] = C),
        (c[23] = L),
        (c[24] = P),
        (c[25] = $),
        (c[26] = i));
    } else i = c[26];
    return (
      c[44] !== s || c[45] !== r || c[46] !== i
        ? ((n = (0, t.jsxs)("div", {
            "data-testid": "callout-thread-updates",
            className: s,
            children: [r, i],
          })),
          (c[44] = s),
          (c[45] = r),
          (c[46] = i),
          (c[47] = n))
        : (n = c[47]),
      n
    );
  }
  function ep(e) {
    let a,
      s,
      r,
      i,
      n,
      o,
      d,
      u = (0, l.c)(21),
      { size: m, dense: p, hasIdentity: x, onExpand: f } = e,
      { t: h } = (0, c.f)(),
      g = p ? "gap-2" : "gap-3",
      y = x ? void 0 : "pl-3";
    return (
      u[0] !== g || u[1] !== y
        ? ((a = (0, z.c)("flex w-full items-center pb-1.5", g, y)),
          (u[0] = g),
          (u[1] = y),
          (u[2] = a))
        : (a = u[2]),
      u[3] !== p || u[4] !== x
        ? ((s = x
            ? (0, t.jsxs)("span", {
                "aria-hidden": !0,
                "data-testid": "callout-thread-spine-dotted",
                className: (0, z.c)(
                  "flex shrink-0 flex-col items-center justify-center gap-[3px] self-stretch py-0.5",
                  p ? "w-8" : "w-9",
                ),
                children: [
                  (0, t.jsx)(ex, {}),
                  (0, t.jsx)(ex, {}),
                  (0, t.jsx)(ex, {}),
                ],
              })
            : null),
          (u[3] = p),
          (u[4] = x),
          (u[5] = s))
        : (s = u[5]),
      u[6] !== f
        ? ((r = (e) => {
            (e.stopPropagation(), f());
          }),
          (u[6] = f),
          (u[7] = r))
        : (r = u[7]),
      u[8] !== p || u[9] !== m
        ? ((i = (0, z.c)(
            "relative z-[2] -my-1 h-6 rounded-md font-medium outline-none transition-colors focus-visible:ring-2 focus-visible:ring-text-accent",
            p
              ? "text-[12px] text-text-tertiary hover:text-text-primary"
              : (0, z.c)(
                  "text-text-accent hover:underline",
                  "md" === m ? "text-[13px]" : "text-xs",
                ),
            "leading-4",
          )),
          (u[8] = p),
          (u[9] = m),
          (u[10] = i))
        : (i = u[10]),
      u[11] !== h
        ? ((n = h("callouts.thread.show_more_updates")),
          (u[11] = h),
          (u[12] = n))
        : (n = u[12]),
      u[13] !== r || u[14] !== i || u[15] !== n
        ? ((o = (0, t.jsx)("button", {
            type: "button",
            onClick: r,
            "data-testid": "callout-updates-show-more",
            className: i,
            children: n,
          })),
          (u[13] = r),
          (u[14] = i),
          (u[15] = n),
          (u[16] = o))
        : (o = u[16]),
      u[17] !== a || u[18] !== s || u[19] !== o
        ? ((d = (0, t.jsxs)("div", {
            "data-testid": "callout-updates-show-more-row",
            className: a,
            children: [s, o],
          })),
          (u[17] = a),
          (u[18] = s),
          (u[19] = o),
          (u[20] = d))
        : (d = u[20]),
      d
    );
  }
  function ex() {
    let e,
      a = (0, l.c)(1);
    return (
      a[0] === Symbol.for("react.memo_cache_sentinel")
        ? ((e = (0, t.jsx)("span", {
            className: "block h-1 w-0.5 rounded-full bg-border-tertiary",
          })),
          (a[0] = e))
        : (e = a[0]),
      e
    );
  }
  function ef(e) {
    let n,
      u,
      b,
      v,
      w,
      j,
      _,
      I,
      C,
      S,
      A,
      U,
      q,
      O,
      T,
      E,
      $,
      D,
      F,
      M,
      Q,
      V,
      K,
      H = (0, l.c)(117),
      {
        update: B,
        size: X,
        expandableComments: Z,
        authorName: J,
        authorAddress: Y,
        authorUserId: G,
        authorAvatarUrl: ee,
        authorAvatarDecoration: et,
        authorVerified: el,
        authorProfileId: ea,
        timeAlign: es,
        timeDensity: er,
        hostHref: ei,
        onHostClick: en,
        connectsToNext: eo,
        className: ec,
        dense: eu,
      } = e,
      em = void 0 !== Z && Z,
      ep = void 0 !== el && el,
      ex = void 0 === ea ? "" : ea,
      ef = void 0 === es ? "start" : es,
      ev = void 0 === er ? "comfortable" : er,
      ew = void 0 !== eo && eo,
      ej = void 0 !== eu && eu,
      { t: e_ } = (0, c.f)(),
      ek = ej ? 32 : 36,
      eN = f.I[ej ? "terminal" : "comfortable"],
      [eI, eC] = (0, o.useState)(!1),
      { ipfsPrefix: eS } = (0, P.useIpfsPrefix)(),
      eA = (0, W.f)(et);
    H[0] !== B.calloutId ||
    H[1] !== B.id ||
    H[2] !== B.likeCount ||
    H[3] !== B.likedByViewer ||
    H[4] !== B.mint
      ? ((n = {
          mint: B.mint,
          calloutId: B.calloutId,
          replyId: B.id,
          likeCount: B.likeCount,
          likedByViewer: B.likedByViewer,
        }),
        (H[0] = B.calloutId),
        (H[1] = B.id),
        (H[2] = B.likeCount),
        (H[3] = B.likedByViewer),
        (H[4] = B.mint),
        (H[5] = n))
      : (n = H[5]);
    let eU = (0, g.f)(n),
      eL = !!(J && Y),
      ez = ej ? "gap-2" : "gap-3",
      eP = eL ? void 0 : "pl-3";
    (H[6] !== ez || H[7] !== eP
      ? ((u = (0, z.c)("flex w-full", ez, eP)),
        (H[6] = ez),
        (H[7] = eP),
        (H[8] = u))
      : (u = H[8]),
      H[9] !== Y ||
      H[10] !== ee ||
      H[11] !== eA ||
      H[12] !== J ||
      H[13] !== ex ||
      H[14] !== G ||
      H[15] !== ek ||
      H[16] !== ew ||
      H[17] !== ej ||
      H[18] !== eL ||
      H[19] !== eS
        ? ((b =
            eL && Y
              ? (0, t.jsxs)("div", {
                  className: (0, z.c)(
                    "flex shrink-0 flex-col items-center self-stretch",
                    ej ? "w-8" : "w-9",
                  ),
                  children: [
                    (0, t.jsx)(s.f, {
                      fallbackAvatarUrl: ee ?? null,
                      fallbackUsername: J ?? null,
                      userAddress: Y,
                      userId: G,
                      children: (0, t.jsx)(R.f, {
                        decoration: eA,
                        variant: "list",
                        className: "relative z-[2]",
                        children: (0, t.jsx)(k.o, {
                          profileId: ex,
                          href: (0, a.$)(Y),
                          prefetch: !1,
                          onClick: eb,
                          "aria-label": `Open ${J}'s profile`,
                          className: (0, z.c)(
                            "relative z-[2] block shrink-0 overflow-hidden rounded-full bg-bg-tertiary",
                            ej ? "size-8" : "size-9",
                          ),
                          children: (0, t.jsx)(r.f, {
                            address: Y,
                            alt: J ?? Y,
                            src: ee ?? void 0,
                            width: ek,
                            height: ek,
                            ipfsPrefix: eS,
                            isAnonymous: !1,
                            className: (0, z.c)(
                              "rounded-full object-cover",
                              ej ? "size-8" : "size-9",
                            ),
                          }),
                        }),
                      }),
                    }),
                    ew
                      ? (0, t.jsx)("span", {
                          "aria-hidden": !0,
                          "data-testid": "callout-thread-spine",
                          className:
                            "mt-1 w-0.5 flex-1 rounded-full bg-border-tertiary",
                        })
                      : null,
                  ],
                })
              : null),
          (H[9] = Y),
          (H[10] = ee),
          (H[11] = eA),
          (H[12] = J),
          (H[13] = ex),
          (H[14] = G),
          (H[15] = ek),
          (H[16] = ew),
          (H[17] = ej),
          (H[18] = eL),
          (H[19] = eS),
          (H[20] = b))
        : (b = H[20]));
    let eq = eL && ew ? "pb-4" : void 0;
    (H[21] !== eq
      ? ((v = (0, z.c)("flex min-w-0 flex-1 flex-col items-start gap-1", eq)),
        (H[21] = eq),
        (H[22] = v))
      : (v = H[22]),
      H[23] !== Y ||
      H[24] !== ee ||
      H[25] !== J ||
      H[26] !== ex ||
      H[27] !== G ||
      H[28] !== ep ||
      H[29] !== ej ||
      H[30] !== eL ||
      H[31] !== X ||
      H[32] !== ef ||
      H[33] !== ev ||
      H[34] !== B.createdAt
        ? ((w =
            eL && Y
              ? (0, t.jsxs)("div", {
                  className: "flex w-full items-center gap-1.5",
                  children: [
                    (0, t.jsxs)("span", {
                      className: "flex min-w-0 items-center gap-1",
                      children: [
                        (0, t.jsx)(s.f, {
                          fallbackAvatarUrl: ee ?? null,
                          fallbackUsername: J ?? null,
                          userAddress: Y,
                          userId: G,
                          children: (0, t.jsx)(k.o, {
                            profileId: ex,
                            href: (0, a.$)(Y),
                            prefetch: !1,
                            onClick: ey,
                            className: (0, z.c)(
                              "relative z-[2] max-w-full truncate whitespace-nowrap text-text-primary hover:underline",
                              ej
                                ? "text-[13px] font-medium leading-4"
                                : "text-sm font-medium leading-[18px]",
                            ),
                            children: J,
                          }),
                        }),
                        ep ? (0, t.jsx)(i.f, { size: ej ? 14 : 18 }) : null,
                      ],
                    }),
                    (0, t.jsx)(N.f, {
                      timestamp: B.createdAt,
                      density: ev,
                      className: (0, z.c)(
                        "min-w-0 truncate leading-4",
                        ej
                          ? "text-[11px] text-text-quaternary"
                          : (0, z.c)(
                              "text-text-tertiary",
                              "md" === X ? "text-[13px]" : "text-xs",
                            ),
                        "end" === ef ? "flex-1 text-right" : "shrink-0",
                      ),
                    }),
                  ],
                })
              : null),
          (H[23] = Y),
          (H[24] = ee),
          (H[25] = J),
          (H[26] = ex),
          (H[27] = G),
          (H[28] = ep),
          (H[29] = ej),
          (H[30] = eL),
          (H[31] = X),
          (H[32] = ef),
          (H[33] = ev),
          (H[34] = B.createdAt),
          (H[35] = w))
        : (w = H[35]));
    let eO = eL ? "text-text-secondary" : "text-text-tertiary",
      eT = "md" === X ? "text-[13px]" : "text-xs";
    (H[36] !== ec || H[37] !== eO || H[38] !== eT
      ? ((j = (0, z.c)(
          "w-full whitespace-pre-wrap break-words leading-4",
          eO,
          eT,
          ec,
        )),
        (H[36] = ec),
        (H[37] = eO),
        (H[38] = eT),
        (H[39] = j))
      : (j = H[39]),
      H[40] !== eL || H[41] !== e_ || H[42] !== ev || H[43] !== B.createdAt
        ? ((_ = eL
            ? null
            : (0, t.jsxs)(t.Fragment, {
                children: [
                  (0, t.jsx)("span", {
                    className: "font-medium text-text-accent",
                    children: e_("web.callouts.update_label"),
                  }),
                  (0, t.jsx)("span", { "aria-hidden": !0, children: " · " }),
                  (0, t.jsx)(N.f, { timestamp: B.createdAt, density: ev }),
                  (0, t.jsx)("span", { "aria-hidden": !0, children: " — " }),
                ],
              })),
          (H[40] = eL),
          (H[41] = e_),
          (H[42] = ev),
          (H[43] = B.createdAt),
          (H[44] = _))
        : (_ = H[44]));
    let eE = eL ? void 0 : "text-text-secondary";
    (H[45] !== ev || H[46] !== B.content
      ? ((I = (0, t.jsx)(y.f, { content: B.content, density: ev })),
        (H[45] = ev),
        (H[46] = B.content),
        (H[47] = I))
      : (I = H[47]),
      H[48] !== eE || H[49] !== I
        ? ((C = (0, t.jsx)("span", { className: eE, children: I })),
          (H[48] = eE),
          (H[49] = I),
          (H[50] = C))
        : (C = H[50]),
      H[51] !== j || H[52] !== _ || H[53] !== C
        ? ((S = (0, t.jsxs)("p", {
            "data-testid": "callout-update",
            className: j,
            children: [_, C],
          })),
          (H[51] = j),
          (H[52] = _),
          (H[53] = C),
          (H[54] = S))
        : (S = H[54]),
      H[55] !== ej || H[56] !== ei || H[57] !== en || H[58] !== B.mediaUrl
        ? ((A = B.mediaUrl
            ? (0, t.jsx)(d.f, {
                src: B.mediaUrl,
                testId: "callout-update-media",
                hostHref: ei,
                onHostClick: en,
                dense: ej,
              })
            : null),
          (H[55] = ej),
          (H[56] = ei),
          (H[57] = en),
          (H[58] = B.mediaUrl),
          (H[59] = A))
        : (A = H[59]),
      H[60] !== J ||
      H[61] !== eN ||
      H[62] !== eL ||
      H[63] !== e_ ||
      H[64] !== B.calloutId ||
      H[65] !== B.id ||
      H[66] !== B.mint
        ? ((U = eL
            ? (0, t.jsx)(x.f, {
                sharePath: `/callouts/${B.mint}/${B.calloutId}/${B.id}`,
                shareTitle: J
                  ? e_("web.callouts.update_share_title", { name: J })
                  : e_("web.callouts.update_share_title_anonymous"),
                children: (0, t.jsx)("button", {
                  type: "button",
                  "aria-label": e_("web.callouts.share_update_a11y"),
                  "data-testid": "callout-update-shares",
                  onClick: eg,
                  className: (0, z.c)(
                    "relative z-[2]",
                    eN,
                    f.L,
                    "text-text-quaternary hover:text-text-primary",
                  ),
                  children: (0, t.jsx)(p.q4, { className: f.d }),
                }),
              })
            : null),
          (H[60] = J),
          (H[61] = eN),
          (H[62] = eL),
          (H[63] = e_),
          (H[64] = B.calloutId),
          (H[65] = B.id),
          (H[66] = B.mint),
          (H[67] = U))
        : (U = H[67]),
      H[68] !== eU
        ? ((q = (e) => {
            (e.stopPropagation(), eU.toggle());
          }),
          (H[68] = eU),
          (H[69] = q))
        : (q = H[69]),
      H[70] !== eU.isLiked || H[71] !== e_
        ? ((O = e_(
            eU.isLiked
              ? "web.callouts.unlike_update_a11y"
              : "web.callouts.like_update_a11y",
          )),
          (H[70] = eU.isLiked),
          (H[71] = e_),
          (H[72] = O))
        : (O = H[72]));
    let eR = eU.isLiked;
    return (
      H[73] !== eN || H[74] !== eU.isLiked
        ? ((T = (0, z.c)(
            "relative z-[2] w-fit",
            eN,
            eU.isLiked
              ? "text-text-primary"
              : (0, z.c)("text-text-quaternary", h.$),
            f.L,
          )),
          (H[73] = eN),
          (H[74] = eU.isLiked),
          (H[75] = T))
        : (T = H[75]),
      H[76] !== eU.isLiked
        ? ((E = eU.isLiked
            ? (0, t.jsx)(m.cJ, { className: (0, z.c)(f.d, h.k) })
            : (0, t.jsx)(p.cJ, { className: f.d })),
          (H[76] = eU.isLiked),
          (H[77] = E))
        : (E = H[77]),
      H[78] !== eU.likeCount
        ? (($ = eU.likeCount > 0 ? (0, L.O)(eU.likeCount) : null),
          (H[78] = eU.likeCount),
          (H[79] = $))
        : ($ = H[79]),
      H[80] !== eU.isLiked ||
      H[81] !== q ||
      H[82] !== O ||
      H[83] !== T ||
      H[84] !== E ||
      H[85] !== $
        ? ((D = (0, t.jsxs)("button", {
            type: "button",
            onClick: q,
            "aria-label": O,
            "aria-pressed": eR,
            "data-testid": "callout-update-like",
            className: T,
            children: [E, $],
          })),
          (H[80] = eU.isLiked),
          (H[81] = q),
          (H[82] = O),
          (H[83] = T),
          (H[84] = E),
          (H[85] = $),
          (H[86] = D))
        : (D = H[86]),
      H[87] !== J ||
      H[88] !== eN ||
      H[89] !== eI ||
      H[90] !== em ||
      H[91] !== eL ||
      H[92] !== e_ ||
      H[93] !== B.replyCount
        ? ((F =
            eL && em
              ? (0, t.jsxs)("button", {
                  type: "button",
                  onClick: (e) => {
                    (e.stopPropagation(), eC(eh));
                  },
                  "aria-label": eI
                    ? e_("web.callouts.hide_comments_a11y")
                    : B.replyCount
                      ? e_("web.callouts.view_comments_a11y", {
                          count: B.replyCount,
                        })
                      : e_("callouts.reply.title", { username: J }),
                  "aria-expanded": eI,
                  "data-testid": "callout-update-comments-toggle",
                  className: (0, z.c)(
                    "relative z-[2] w-fit",
                    eN,
                    f.L,
                    eI
                      ? "text-text-secondary"
                      : "text-text-quaternary hover:text-text-primary",
                  ),
                  children: [
                    (0, t.jsx)(p.Z2, { className: f.d }),
                    null != B.replyCount ? (0, L.O)(B.replyCount) : null,
                  ],
                })
              : eL && null != B.replyCount
                ? (0, t.jsxs)("span", {
                    "data-testid": "callout-update-comments-count",
                    "aria-label": e_("web.callouts.comments_count", {
                      count: B.replyCount,
                    }),
                    className: (0, z.c)("w-fit text-text-quaternary", eN),
                    children: [
                      (0, t.jsx)(p.Z2, { className: f.d }),
                      (0, L.O)(B.replyCount),
                    ],
                  })
                : null),
          (H[87] = J),
          (H[88] = eN),
          (H[89] = eI),
          (H[90] = em),
          (H[91] = eL),
          (H[92] = e_),
          (H[93] = B.replyCount),
          (H[94] = F))
        : (F = H[94]),
      H[95] !== U || H[96] !== D || H[97] !== F
        ? ((M = (0, t.jsxs)("div", {
            "data-testid": "callout-update-metrics",
            className: "-ml-[5px] flex w-fit items-center",
            children: [U, D, F],
          })),
          (H[95] = U),
          (H[96] = D),
          (H[97] = F),
          (H[98] = M))
        : (M = H[98]),
      H[99] !== J ||
      H[100] !== eI ||
      H[101] !== B.calloutId ||
      H[102] !== B.id ||
      H[103] !== B.mint ||
      H[104] !== B.replyCount
        ? ((Q = eI
            ? (0, t.jsx)(ed, {
                mint: B.mint,
                calloutId: B.calloutId,
                parentReplyId: B.id,
                commentCount: B.replyCount,
                parentAuthorName: J,
                className: "pt-1",
              })
            : null),
          (H[99] = J),
          (H[100] = eI),
          (H[101] = B.calloutId),
          (H[102] = B.id),
          (H[103] = B.mint),
          (H[104] = B.replyCount),
          (H[105] = Q))
        : (Q = H[105]),
      H[106] !== v ||
      H[107] !== w ||
      H[108] !== S ||
      H[109] !== A ||
      H[110] !== M ||
      H[111] !== Q
        ? ((V = (0, t.jsxs)("div", {
            className: v,
            children: [w, S, A, M, Q],
          })),
          (H[106] = v),
          (H[107] = w),
          (H[108] = S),
          (H[109] = A),
          (H[110] = M),
          (H[111] = Q),
          (H[112] = V))
        : (V = H[112]),
      H[113] !== u || H[114] !== b || H[115] !== V
        ? ((K = (0, t.jsxs)("div", {
            "data-testid": "callout-update-row",
            className: u,
            children: [b, V],
          })),
          (H[113] = u),
          (H[114] = b),
          (H[115] = V),
          (H[116] = K))
        : (K = H[116]),
      K
    );
  }
  function eh(e) {
    return !e;
  }
  function eg(e) {
    return e.stopPropagation();
  }
  function ey(e) {
    return e.stopPropagation();
  }
  function eb(e) {
    return e.stopPropagation();
  }
  return function (e) {
    let m,
      p,
      x,
      f,
      h,
      g,
      b,
      v,
      w,
      j,
      _,
      I,
      C,
      S,
      A,
      U,
      L,
      q,
      O,
      T,
      E,
      $,
      D,
      F,
      M,
      Q,
      V,
      K,
      H,
      B,
      X,
      Z,
      J,
      Y,
      G,
      ee,
      et = (0, l.c)(208),
      {
        authorAddress: el,
        authorUserId: ea,
        authorName: es,
        authorAvatarUrl: er,
        authorAvatarDecoration: ei,
        authorAvatarShape: en,
        authorHref: eo,
        onAuthorClick: ec,
        authorVerified: ed,
        createdAt: eu,
        note: ep,
        mediaUrl: ex,
        mediaPriority: ef,
        updates: eh,
        noteSize: eg,
        updatesCollapsible: ey,
        updatesExpandableComments: eb,
        timeAlign: ej,
        topRight: e_,
        topRightAlign: ek,
        nameAdornment: eN,
        children: eI,
        contentGap: eC,
        aside: eS,
        below: eA,
        href: eU,
        prefetch: eL,
        linkProps: ez,
        id: eP,
        rootRef: eq,
        density: eO,
        divider: eT,
        onClick: eE,
        className: eR,
        testId: e$,
        noteTestId: eD,
        forceThreadRail: eF,
        noteClassName: eM,
        noteClampLines: eQ,
      } = e,
      eV = void 0 === en ? "circle" : en,
      eK = void 0 !== ed && ed,
      eH = void 0 !== ef && ef,
      eB = void 0 === eg ? "sm" : eg,
      eW = void 0 === ey || ey,
      eX = void 0 !== eb && eb,
      eZ = void 0 === ej ? "start" : ej,
      eJ = void 0 === ek ? "end" : ek,
      eY = void 0 === eC ? "sm" : eC,
      eG = void 0 !== eL && eL,
      e1 = void 0 === eO ? "comfortable" : eO,
      e0 = void 0 === eT ? "hairline" : eT,
      e2 = void 0 === eD ? "callout-note" : eD,
      e3 = void 0 !== eF && eF,
      { t: e4 } = (0, c.f)(),
      e5 = "dense" === e1,
      e6 = "comfortable" === e1,
      e8 = e5 ? 32 : 36,
      { ipfsPrefix: e7 } = (0, P.useIpfsPrefix)(),
      e9 = (0, W.f)(ei),
      te = eU ? "relative z-[2]" : void 0,
      tt = eU
        ? "relative z-[2] pointer-events-none [&_a]:pointer-events-auto [&_button]:pointer-events-auto [&_input]:pointer-events-auto [&_label]:pointer-events-auto [&_textarea]:pointer-events-auto [&_[data-compose-box]]:pointer-events-auto"
        : void 0;
    et[0] !== eE
      ? ((m = (e) => {
          !eE ||
            e.target.closest(
              "button, a, textarea, input, label, [data-compose-box]",
            ) ||
            eE(e);
        }),
        (et[0] = eE),
        (et[1] = m))
      : (m = et[1]);
    let tl = m;
    et[2] !== ep ? ((p = ep?.trim()), (et[2] = ep), (et[3] = p)) : (p = et[3]);
    let ta = p,
      [ts, tr] = (0, o.useState)(!1),
      [ti, tn] = (0, o.useState)(!1),
      to = (0, o.useRef)(null),
      tc = !!(eQ && ta);
    (et[4] !== tc
      ? ((x = () => {
          if (!tc) return;
          let e = to.current;
          if (!e) return;
          let t = () => tn(e.scrollHeight > e.clientHeight + 1);
          if ((t(), "u" < typeof ResizeObserver)) return;
          let l = new ResizeObserver(t);
          return (l.observe(e), () => l.disconnect());
        }),
        (f = [tc]),
        (et[4] = tc),
        (et[5] = x),
        (et[6] = f))
      : ((x = et[5]), (f = et[6])),
      (0, o.useEffect)(x, f));
    let td = e5
        ? "text-[13px] leading-[18px]"
        : "lg" === eB
          ? "text-[15px] leading-5"
          : "md" === eB
            ? "text-sm leading-[18px]"
            : "text-xs leading-4",
      tu = eQ && !ts && ew[eQ];
    et[7] !== eM || et[8] !== td || et[9] !== tu
      ? ((h = (0, z.c)(
          "w-full whitespace-pre-wrap break-words text-text-primary",
          td,
          eM,
          tu,
        )),
        (et[7] = eM),
        (et[8] = td),
        (et[9] = tu),
        (et[10] = h))
      : (h = et[10]);
    let tm = h,
      tp = !!eh?.length;
    et[11] !== el || et[12] !== eo
      ? ((g = void 0 === eo ? (0, a.$)(el) : eo),
        (et[11] = el),
        (et[12] = eo),
        (et[13] = g))
      : (g = et[13]);
    let tx = g;
    et[14] !== tx
      ? ((b = tx?.startsWith("/profile/") ?? !1), (et[14] = tx), (et[15] = b))
      : (b = et[15]);
    let tf = b,
      th = void 0 === eo ? el : "";
    if (
      et[16] !== eS ||
      et[17] !== el ||
      et[18] !== eV ||
      et[19] !== er ||
      et[20] !== e9 ||
      et[21] !== es ||
      et[22] !== ea ||
      et[23] !== e8 ||
      et[24] !== eA ||
      et[25] !== eR ||
      et[26] !== e6 ||
      et[27] !== e5 ||
      et[28] !== e0 ||
      et[29] !== e3 ||
      et[30] !== tl ||
      et[31] !== tf ||
      et[32] !== tp ||
      et[33] !== eU ||
      et[34] !== eP ||
      et[35] !== tx ||
      et[36] !== e7 ||
      et[37] !== ez ||
      et[38] !== ec ||
      et[39] !== eE ||
      et[40] !== eG ||
      et[41] !== te ||
      et[42] !== eq ||
      et[43] !== th ||
      et[44] !== e$
    ) {
      let e,
        l,
        a,
        i,
        o,
        c,
        d,
        u = (0, z.c)(
          "block shrink-0 overflow-hidden bg-bg-tertiary",
          e5 ? "size-8" : "size-9",
          "squircle" === eV ? "rounded-xl" : "rounded-full",
        ),
        m = er ?? void 0,
        p = e5 ? "size-8" : "size-9",
        x = "squircle" === eV ? "rounded-xl" : "rounded-full";
      (et[57] !== p || et[58] !== x
        ? ((e = (0, z.c)("object-cover", p, x)),
          (et[57] = p),
          (et[58] = x),
          (et[59] = e))
        : (e = et[59]),
        et[60] !== el ||
        et[61] !== es ||
        et[62] !== e8 ||
        et[63] !== e7 ||
        et[64] !== m ||
        et[65] !== e
          ? ((l = (0, t.jsx)(r.f, {
              address: el,
              alt: es,
              src: m,
              width: e8,
              height: e8,
              ipfsPrefix: e7,
              isAnonymous: !1,
              className: e,
            })),
            (et[60] = el),
            (et[61] = es),
            (et[62] = e8),
            (et[63] = e7),
            (et[64] = m),
            (et[65] = e),
            (et[66] = l))
          : (l = et[66]));
      let f = l;
      et[67] !== el ||
      et[68] !== er ||
      et[69] !== es ||
      et[70] !== ea ||
      et[71] !== tf
        ? ((a = (e) =>
            tf
              ? (0, t.jsx)(s.f, {
                  fallbackAvatarUrl: er ?? null,
                  fallbackUsername: es,
                  userAddress: el,
                  userId: ea,
                  children: e,
                })
              : e),
          (et[67] = el),
          (et[68] = er),
          (et[69] = es),
          (et[70] = ea),
          (et[71] = tf),
          (et[72] = a))
        : (a = et[72]);
      let h = a,
        g = (0, z.c)(
          "max-w-full truncate whitespace-nowrap font-medium text-text-primary",
          e5
            ? "text-[13px] leading-4"
            : e6
              ? "text-sm leading-5"
              : "text-sm leading-[18px]",
        );
      ((C = eP),
        (S = eq),
        (A = e$ ?? "callout-feed-card"),
        (U = !eU && eE ? tl : void 0));
      let y = "none" !== e0 && "border-b border-border-secondary",
        b = e6 ? "py-4" : "py-2",
        N = eU && "relative",
        P =
          (eU || eE) && "cursor-pointer transition-colors hover:bg-bg-tertiary";
      (et[73] !== eR ||
      et[74] !== y ||
      et[75] !== b ||
      et[76] !== N ||
      et[77] !== P
        ? ((L = (0, z.c)("flex w-full flex-col", y, b, N, P, eR)),
          (et[73] = eR),
          (et[74] = y),
          (et[75] = b),
          (et[76] = N),
          (et[77] = P),
          (et[78] = L))
        : (L = et[78]),
        et[79] !== es ||
        et[80] !== eU ||
        et[81] !== ez ||
        et[82] !== eE ||
        et[83] !== eG
          ? ((q = eU
              ? (0, t.jsx)(n.default, {
                  href: eU,
                  prefetch: eG,
                  ...ez,
                  onClick: eE,
                  "aria-label": `Open ${es}'s callout`,
                  className: "absolute inset-0 z-[1] focus-inset",
                })
              : null),
            (et[79] = es),
            (et[80] = eU),
            (et[81] = ez),
            (et[82] = eE),
            (et[83] = eG),
            (et[84] = q))
          : (q = et[84]),
        et[85] !== eS || et[86] !== eA || et[87] !== e5
          ? ((_ = (0, z.c)(
              "w-full items-start",
              eS || eA
                ? (0, z.c)(
                    "grid",
                    e5 ? "gap-x-2" : "gap-x-3",
                    eS
                      ? "grid-cols-[auto_minmax(0,1fr)_auto]"
                      : "grid-cols-[auto_minmax(0,1fr)]",
                  )
                : (0, z.c)("flex", e5 ? "gap-2" : "gap-3"),
            )),
            (et[85] = eS),
            (et[86] = eA),
            (et[87] = e5),
            (et[88] = _))
          : (_ = et[88]));
      let T = eA && "row-span-2";
      et[89] !== T
        ? ((i = (0, z.c)(
            "flex shrink-0 flex-col items-center self-stretch",
            T,
          )),
          (et[89] = T),
          (et[90] = i))
        : (i = et[90]);
      let E = tx
        ? (0, t.jsx)(k.o, {
            profileId: th,
            href: tx,
            prefetch: !1,
            onClick: (e) => {
              (e.stopPropagation(), ec?.());
            },
            "aria-label": `Open ${es}'s profile`,
            className: (0, z.c)(u, te),
            children: f,
          })
        : (0, t.jsx)("span", {
            "data-testid": "callout-author-avatar",
            className: u,
            children: f,
          });
      (et[91] !== e9 || et[92] !== E
        ? ((o = (0, t.jsx)(R.f, {
            decoration: e9,
            variant: "list",
            children: E,
          })),
          (et[91] = e9),
          (et[92] = E),
          (et[93] = o))
        : (o = et[93]),
        et[94] !== o || et[95] !== h
          ? ((c = h(o)), (et[94] = o), (et[95] = h), (et[96] = c))
          : (c = et[96]),
        et[97] !== e3 || et[98] !== tp
          ? ((d =
              tp || e3
                ? (0, t.jsx)("span", {
                    "aria-hidden": !0,
                    "data-testid": "callout-thread-spine",
                    className:
                      "my-1 w-0.5 flex-1 rounded-full bg-border-tertiary",
                  })
                : null),
            (et[97] = e3),
            (et[98] = tp),
            (et[99] = d))
          : (d = et[99]),
        et[100] !== i || et[101] !== c || et[102] !== d
          ? ((I = (0, t.jsxs)("div", { className: i, children: [c, d] })),
            (et[100] = i),
            (et[101] = c),
            (et[102] = d),
            (et[103] = I))
          : (I = et[103]));
      let $ = e5 ? "gap-1" : "gap-1.5";
      (et[104] !== $
        ? ((j = (0, z.c)("flex min-w-0 flex-1 flex-col", $)),
          (et[104] = $),
          (et[105] = j))
        : (j = et[105]),
        (w = "flex w-full items-center gap-1.5"),
        (v = "flex min-w-0 items-center gap-1"),
        (O = h(
          tx
            ? (0, t.jsx)(k.o, {
                profileId: th,
                href: tx,
                prefetch: !1,
                onClick: (e) => {
                  (e.stopPropagation(), ec?.());
                },
                className: (0, z.c)(g, "hover:underline", te),
                children: es,
              })
            : (0, t.jsx)("span", {
                "data-testid": "callout-author-name",
                className: g,
                children: es,
              }),
        )),
        (et[16] = eS),
        (et[17] = el),
        (et[18] = eV),
        (et[19] = er),
        (et[20] = e9),
        (et[21] = es),
        (et[22] = ea),
        (et[23] = e8),
        (et[24] = eA),
        (et[25] = eR),
        (et[26] = e6),
        (et[27] = e5),
        (et[28] = e0),
        (et[29] = e3),
        (et[30] = tl),
        (et[31] = tf),
        (et[32] = tp),
        (et[33] = eU),
        (et[34] = eP),
        (et[35] = tx),
        (et[36] = e7),
        (et[37] = ez),
        (et[38] = ec),
        (et[39] = eE),
        (et[40] = eG),
        (et[41] = te),
        (et[42] = eq),
        (et[43] = th),
        (et[44] = e$),
        (et[45] = v),
        (et[46] = w),
        (et[47] = j),
        (et[48] = _),
        (et[49] = I),
        (et[50] = C),
        (et[51] = S),
        (et[52] = A),
        (et[53] = U),
        (et[54] = L),
        (et[55] = q),
        (et[56] = O));
    } else
      ((v = et[45]),
        (w = et[46]),
        (j = et[47]),
        (_ = et[48]),
        (I = et[49]),
        (C = et[50]),
        (S = et[51]),
        (A = et[52]),
        (U = et[53]),
        (L = et[54]),
        (q = et[55]),
        (O = et[56]));
    (et[106] !== eK || et[107] !== e5
      ? ((T = eK ? (0, t.jsx)(i.f, { size: e5 ? 14 : 18 }) : null),
        (et[106] = eK),
        (et[107] = e5),
        (et[108] = T))
      : (T = et[108]),
      et[109] !== v || et[110] !== O || et[111] !== T
        ? ((E = (0, t.jsxs)("span", { className: v, children: [O, T] })),
          (et[109] = v),
          (et[110] = O),
          (et[111] = T),
          (et[112] = E))
        : (E = et[112]),
      et[113] !== eN || et[114] !== te
        ? (($ = eN
            ? (0, t.jsx)("div", {
                "data-testid": "callout-name-adornment",
                className: (0, z.c)("shrink-0", te),
                children: eN,
              })
            : null),
          (et[113] = eN),
          (et[114] = te),
          (et[115] = $))
        : ($ = et[115]),
      et[116] !== te || et[117] !== eZ || et[118] !== e_
        ? ((D =
            e_ && "end" === eZ
              ? (0, t.jsx)("div", {
                  className: (0, z.c)("ml-auto shrink-0", te),
                  children: e_,
                })
              : null),
          (et[116] = te),
          (et[117] = eZ),
          (et[118] = e_),
          (et[119] = D))
        : (D = et[119]),
      et[120] !== e6 ||
      et[121] !== eu ||
      et[122] !== e5 ||
      et[123] !== eZ ||
      et[124] !== e_
        ? ((F =
            null != eu
              ? (0, t.jsx)(N.f, {
                  timestamp: eu,
                  density: e6 ? "comfortable" : "terminal",
                  className: (0, z.c)(
                    "min-w-0 truncate",
                    e5
                      ? "text-[11px] leading-4 text-text-quaternary"
                      : e6
                        ? "text-[13px] leading-[18px] text-text-tertiary"
                        : "text-xs leading-4 text-text-tertiary",
                    "end" === eZ
                      ? e_
                        ? "shrink-0"
                        : "flex-1 text-right"
                      : "shrink-0",
                  ),
                })
              : null),
          (et[120] = e6),
          (et[121] = eu),
          (et[122] = e5),
          (et[123] = eZ),
          (et[124] = e_),
          (et[125] = F))
        : (F = et[125]),
      et[126] !== te || et[127] !== eZ || et[128] !== e_ || et[129] !== eJ
        ? ((M =
            e_ && "end" !== eZ
              ? (0, t.jsx)("div", {
                  "data-testid": "callout-top-right",
                  className: (0, z.c)(
                    "shrink-0",
                    "end" === eJ && "ml-auto",
                    te,
                  ),
                  children: e_,
                })
              : null),
          (et[126] = te),
          (et[127] = eZ),
          (et[128] = e_),
          (et[129] = eJ),
          (et[130] = M))
        : (M = et[130]),
      et[131] !== w ||
      et[132] !== E ||
      et[133] !== $ ||
      et[134] !== D ||
      et[135] !== F ||
      et[136] !== M
        ? ((Q = (0, t.jsxs)("div", {
            className: w,
            children: [E, $, D, F, M],
          })),
          (et[131] = w),
          (et[132] = E),
          (et[133] = $),
          (et[134] = D),
          (et[135] = F),
          (et[136] = M),
          (et[137] = Q))
        : (Q = et[137]),
      et[138] !== e6 || et[139] !== tm || et[140] !== e2 || et[141] !== ta
        ? ((V = ta
            ? (0, t.jsx)("p", {
                ref: to,
                "data-testid": e2,
                className: tm,
                children: (0, t.jsx)(y.f, {
                  content: ta,
                  density: e6 ? "comfortable" : "terminal",
                }),
              })
            : null),
          (et[138] = e6),
          (et[139] = tm),
          (et[140] = e2),
          (et[141] = ta),
          (et[142] = V))
        : (V = et[142]),
      et[143] !== e5 ||
      et[144] !== ti ||
      et[145] !== ts ||
      et[146] !== te ||
      et[147] !== e4
        ? ((K =
            ti && !ts
              ? (0, t.jsx)("button", {
                  type: "button",
                  "data-testid": "callout-note-show-more",
                  onClick: (e) => {
                    (e.stopPropagation(), tr(!0));
                  },
                  className: (0, z.c)(
                    "-my-1 h-6 self-start rounded-md text-xs font-medium leading-4 outline-none transition-colors hover:text-text-primary focus-visible:ring-2 focus-visible:ring-text-accent",
                    e5 ? "text-text-tertiary" : "text-text-accent",
                    te,
                  ),
                  children: e4("common.show_more"),
                })
              : null),
          (et[143] = e5),
          (et[144] = ti),
          (et[145] = ts),
          (et[146] = te),
          (et[147] = e4),
          (et[148] = K))
        : (K = et[148]),
      et[149] !== e5 ||
      et[150] !== eU ||
      et[151] !== eH ||
      et[152] !== ex ||
      et[153] !== eE
        ? ((H = ex
            ? (0, ev.y)(ex)
              ? (0, t.jsx)(u.f, { src: ex, testId: "callout-media", dense: e5 })
              : (0, t.jsx)(d.f, {
                  src: ex,
                  testId: "callout-media",
                  hostHref: eU,
                  onHostClick: eE,
                  dense: e5,
                  priority: eH,
                })
            : null),
          (et[149] = e5),
          (et[150] = eU),
          (et[151] = eH),
          (et[152] = ex),
          (et[153] = eE),
          (et[154] = H))
        : (H = et[154]),
      et[155] !== eA ||
      et[156] !== eI ||
      et[157] !== eY ||
      et[158] !== e5 ||
      et[159] !== tp ||
      et[160] !== tt
        ? ((B = eI
            ? (0, t.jsx)("div", {
                className: (0, z.c)(
                  "flex w-full flex-col items-start pt-1",
                  e5 ? "gap-1.5" : "md" === eY ? "gap-3" : "gap-2",
                  tp && !eA && "pb-3",
                  tt,
                ),
                children: eI,
              })
            : null),
          (et[155] = eA),
          (et[156] = eI),
          (et[157] = eY),
          (et[158] = e5),
          (et[159] = tp),
          (et[160] = tt),
          (et[161] = B))
        : (B = et[161]),
      et[162] !== j ||
      et[163] !== Q ||
      et[164] !== V ||
      et[165] !== K ||
      et[166] !== H ||
      et[167] !== B
        ? ((X = (0, t.jsxs)("div", {
            className: j,
            children: [Q, V, K, H, B],
          })),
          (et[162] = j),
          (et[163] = Q),
          (et[164] = V),
          (et[165] = K),
          (et[166] = H),
          (et[167] = B),
          (et[168] = X))
        : (X = et[168]),
      et[169] !== eS || et[170] !== tt
        ? ((Z = eS
            ? (0, t.jsx)("div", {
                "data-testid": "callout-aside",
                className: (0, z.c)("shrink-0 self-start", tt),
                children: eS,
              })
            : null),
          (et[169] = eS),
          (et[170] = tt),
          (et[171] = Z))
        : (Z = et[171]),
      et[172] !== eA || et[173] !== tp || et[174] !== tt
        ? ((J = eA
            ? (0, t.jsx)("div", {
                "data-testid": "callout-below",
                className: (0, z.c)(
                  "col-start-2 -col-end-1 min-w-0",
                  tp && "pb-3",
                  tt,
                ),
                children: eA,
              })
            : null),
          (et[172] = eA),
          (et[173] = tp),
          (et[174] = tt),
          (et[175] = J))
        : (J = et[175]),
      et[176] !== _ ||
      et[177] !== I ||
      et[178] !== X ||
      et[179] !== Z ||
      et[180] !== J
        ? ((Y = (0, t.jsxs)("div", { className: _, children: [I, X, Z, J] })),
          (et[176] = _),
          (et[177] = I),
          (et[178] = X),
          (et[179] = Z),
          (et[180] = J),
          (et[181] = Y))
        : (Y = et[181]));
    let tg = "sm" === eB ? "sm" : "md",
      ty = e6 ? "comfortable" : "terminal";
    return (
      et[182] !== el ||
      et[183] !== ei ||
      et[184] !== er ||
      et[185] !== es ||
      et[186] !== ea ||
      et[187] !== eK ||
      et[188] !== e5 ||
      et[189] !== eU ||
      et[190] !== eE ||
      et[191] !== th ||
      et[192] !== tg ||
      et[193] !== ty ||
      et[194] !== eZ ||
      et[195] !== eh ||
      et[196] !== eW ||
      et[197] !== eX
        ? ((G = (0, t.jsx)(em, {
            updates: eh,
            collapsible: eW,
            expandableComments: eX,
            size: tg,
            dense: e5,
            authorName: es,
            authorAddress: el,
            authorUserId: ea,
            authorAvatarUrl: er,
            authorAvatarDecoration: ei,
            authorVerified: eK,
            authorProfileId: th,
            timeAlign: eZ,
            timeDensity: ty,
            hostHref: eU,
            onHostClick: eE,
          })),
          (et[182] = el),
          (et[183] = ei),
          (et[184] = er),
          (et[185] = es),
          (et[186] = ea),
          (et[187] = eK),
          (et[188] = e5),
          (et[189] = eU),
          (et[190] = eE),
          (et[191] = th),
          (et[192] = tg),
          (et[193] = ty),
          (et[194] = eZ),
          (et[195] = eh),
          (et[196] = eW),
          (et[197] = eX),
          (et[198] = G))
        : (G = et[198]),
      et[199] !== C ||
      et[200] !== S ||
      et[201] !== A ||
      et[202] !== U ||
      et[203] !== L ||
      et[204] !== q ||
      et[205] !== Y ||
      et[206] !== G
        ? ((ee = (0, t.jsxs)("article", {
            id: C,
            ref: S,
            "data-testid": A,
            onClick: U,
            className: L,
            children: [q, Y, G],
          })),
          (et[199] = C),
          (et[200] = S),
          (et[201] = A),
          (et[202] = U),
          (et[203] = L),
          (et[204] = q),
          (et[205] = Y),
          (et[206] = G),
          (et[207] = ee))
        : (ee = et[207]),
      ee
    );
  };
}
