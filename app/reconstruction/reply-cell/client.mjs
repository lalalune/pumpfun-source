import { FALLBACK_IMAGE } from "../search-session/session.mjs";
import {
  profileRoute,
  createSolanaGuards,
} from "../search-navigation/navigation.mjs";
const truncateAddress = (() => {
  function t(e, t, n) {
    if (!e) return "";
    let r = 4,
      i = 4;
    return ("number" == typeof t && "number" == typeof n
      ? ((r = t), (i = n))
      : t &&
        "object" == typeof t &&
        ((r = t.startLength ?? 4), (i = t.endLength ?? 4)),
    e.length <= r + i + 1)
      ? e
      : `${e.slice(0, r)}…${e.slice(-i)}`;
  }
  return t;
})();
const formatCount = (() => {
  let n = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }),
    r = new Intl.NumberFormat("en-US", {
      notation: "compact",
      compactDisplay: "short",
      maximumSignificantDigits: 3,
    }),
    i = (e) => "number" == typeof e && Number.isFinite(e);
  return function (e) {
    if (!i(e)) return "—";
    let t = Math.abs(e);
    return t >= 1e4 ? r.format(t).toUpperCase() : n.format(t);
  };
})();
const normalizeAvatarInput = (() => {
  const t = { A: FALLBACK_IMAGE };
  return (e) => {
    let i = e?.trim() ?? "";
    if (i && i !== t.A) return i;
  };
})();
export function createReplyCell({
  jsx,
  jsxs,
  useMemoCache,
  classNames,
  base58,
  sourceUri,
  Avatar,
  VerifiedBadge,
  ProfileHover,
  ProfileLink,
  SocialLink,
  RelativeTime,
  RichText,
  ImagePreview,
  MuteMenu,
  ShareMenu,
  useTranslation,
  useIpfsPrefix,
  useVerified,
  useOwnId,
  useReplyLike,
  HeartFilled,
  HeartOutline,
  ShareIcon,
  CommentIcon,
}) {
  for (const [name, value] of Object.entries({
    jsx,
    jsxs,
    useMemoCache,
    classNames,
    useTranslation,
    useIpfsPrefix,
    useVerified,
    useOwnId,
    useReplyLike,
  }))
    if (typeof value !== "function")
      throw new TypeError("Explicit reply-cell capability required: " + name);
  for (const [name, value] of Object.entries({
    Avatar,
    VerifiedBadge,
    ProfileHover,
    ProfileLink,
    SocialLink,
    RelativeTime,
    RichText,
    ImagePreview,
    MuteMenu,
    ShareMenu,
    HeartFilled,
    HeartOutline,
    ShareIcon,
    CommentIcon,
  }))
    if (value == null)
      throw new TypeError("Explicit reply renderer required: " + name);
  if (
    typeof base58?.decode !== "function" ||
    typeof sourceUri?.D !== "function" ||
    typeof sourceUri?.d !== "function"
  )
    throw new TypeError(
      "Explicit base58.decode and existing URI D/d capabilities required",
    );
  const previewImage = (() => {
    const t = sourceUri;
    let r = "https://pump.mypinata.cloud/ipfs/";
    return ({ sourceUrl: e, width: n, ipfsPrefix: i = r }) => {
      let a = e?.trim();
      if (!a) return null;
      let l = (0, t.D)(a, i);
      if (!(0, t.d)(l)) return l;
      let o = new URL(l);
      return (
        o.searchParams.set("img-width", String(n)),
        o.searchParams.set("img-dpr", String(2)),
        o.searchParams.set("img-onerror", "redirect"),
        o.toString()
      );
    };
  })();
  const t = { jsx, jsxs },
    l = { c: useMemoCache },
    z = { c: classNames },
    C = { d: truncateAddress },
    S = { f: createSolanaGuards({ base58 }).validAddress },
    a = { $: profileRoute },
    I = { z: { list: 40 }, Z: previewImage },
    _ = { f: normalizeAvatarInput },
    L = { O: formatCount },
    h = { k: "text-hot", $: "hover:bg-hot/10 hover:text-hot" },
    m = { cJ: HeartFilled },
    p = { cJ: HeartOutline, q4: ShareIcon, Z2: CommentIcon },
    r = { f: Avatar },
    i = { f: VerifiedBadge },
    s = { f: ProfileHover },
    k = { o: ProfileLink },
    j = { f: SocialLink },
    N = { f: RelativeTime },
    y = { f: RichText },
    d = { f: ImagePreview },
    w = { f: MuteMenu },
    x = { f: ShareMenu },
    c = { f: useTranslation },
    P = { useIpfsPrefix: useIpfsPrefix },
    v = { s: useVerified },
    b = { $: useOwnId },
    g = { f: useReplyLike };
  let A = (e) =>
      e.caller?.walletAddress ?? ((0, S.f)(e.userId) ? e.userId : null),
    U = (e) => {
      let t = A(e);
      return (
        e.caller?.username?.trim() ||
        e.caller?.displayName?.trim() ||
        (0, C.d)(t ?? e.userId, 4, 4)
      );
    },
    q =
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bg-accent";
  function T(e) {
    return e.stopPropagation();
  }
  function O(e) {
    let n,
      o,
      u,
      f,
      C,
      S,
      O,
      E,
      R,
      $,
      D,
      F,
      M,
      Q,
      V,
      K,
      H,
      B,
      W,
      X,
      Z,
      J,
      Y,
      G = (0, l.c)(96),
      { t: ee } = (0, c.f)(),
      {
        reply: et,
        mint: el,
        calloutId: ea,
        focused: es,
        hideActions: er,
        fallbackXUsername: ei,
        commentCount: en,
        commentsExpanded: eo,
        onToggleComments: ec,
        commentsSlot: ed,
        replierAvatarShape: eu,
        replierHref: em,
        className: ep,
      } = e,
      ex = void 0 !== eo && eo,
      ef = void 0 === eu ? "circle" : eu,
      { ipfsPrefix: eh } = (0, P.useIpfsPrefix)();
    G[0] !== et ? ((n = A(et)), (G[0] = et), (G[1] = n)) : (n = G[1]);
    let eg = n,
      ey = (0, v.s)(eg ?? et.userId),
      eb = (0, b.$)();
    G[2] !== eb || G[3] !== et.authorCcUserId || G[4] !== et.userId
      ? ((o = !eb(et.userId) && !eb(et.authorCcUserId)),
        (G[2] = eb),
        (G[3] = et.authorCcUserId),
        (G[4] = et.userId),
        (G[5] = o))
      : (o = G[5]);
    let ev = o,
      ew = et.likeCount ?? 0,
      ej = et.likedByViewer ?? !1;
    G[6] !== ea ||
    G[7] !== el ||
    G[8] !== et.replyId ||
    G[9] !== ew ||
    G[10] !== ej
      ? ((u = {
          mint: el,
          calloutId: ea,
          replyId: et.replyId,
          likeCount: ew,
          likedByViewer: ej,
          surface: "callout_detail",
        }),
        (G[6] = ea),
        (G[7] = el),
        (G[8] = et.replyId),
        (G[9] = ew),
        (G[10] = ej),
        (G[11] = u))
      : (u = G[11]);
    let e_ = (0, g.f)(u);
    G[12] !== et ? ((f = U(et)), (G[12] = et), (G[13] = f)) : (f = G[13]);
    let ek = f;
    G[14] !== et.caller?.avatarUrl
      ? ((C = (0, I.Z)({
          sourceUrl: (0, _.f)(et.caller?.avatarUrl),
          width: I.z.list,
        })),
        (G[14] = et.caller?.avatarUrl),
        (G[15] = C))
      : (C = G[15]);
    let eN = C,
      eI = "squircle" === ef ? "rounded-xl" : "rounded-full",
      eC = eg ?? et.userId,
      eS = "squircle" === ef && "rounded-xl";
    G[16] !== eS
      ? ((S = (0, z.c)("h-9 w-9", eS)), (G[16] = eS), (G[17] = S))
      : (S = G[17]);
    let eA = eN ?? void 0;
    G[18] !== ek || G[19] !== eh || G[20] !== S || G[21] !== eA || G[22] !== eC
      ? ((O = (0, t.jsx)(r.f, {
          address: eC,
          alt: ek,
          className: S,
          height: 36,
          ipfsPrefix: eh,
          isAnonymous: !1,
          src: eA,
          width: 36,
        })),
        (G[18] = ek),
        (G[19] = eh),
        (G[20] = S),
        (G[21] = eA),
        (G[22] = eC),
        (G[23] = O))
      : (O = G[23]);
    let eU = O;
    G[24] !== em || G[25] !== et.userId || G[26] !== eg
      ? ((E =
          void 0 === em ? (0, a.$)({ address: eg, userId: et.userId }) : em),
        (G[24] = em),
        (G[25] = et.userId),
        (G[26] = eg),
        (G[27] = E))
      : (E = G[27]);
    let eL = E,
      ez = void 0 === em ? eg : null,
      eP = (void 0 === em && (eg || et.userId)) || "",
      eq = void 0 !== em;
    G[28] !== eN || G[29] !== ek || G[30] !== ez
      ? ((R = (e) =>
          ez
            ? (0, t.jsx)(s.f, {
                fallbackAvatarUrl: eN ?? null,
                fallbackUsername: ek,
                userAddress: ez,
                children: e,
              })
            : e),
        (G[28] = eN),
        (G[29] = ek),
        (G[30] = ez),
        (G[31] = R))
      : (R = G[31]);
    let eO = R,
      eT = et.replyId,
      eE = es && "bg-white/[0.04]";
    return (
      G[32] !== ep || G[33] !== eE
        ? (($ = (0, z.c)(
            "flex w-full items-start gap-3 border-b border-border-tertiary py-3",
            eE,
            ep,
          )),
          (G[32] = ep),
          (G[33] = eE),
          (G[34] = $))
        : ($ = G[34]),
      G[35] !== eU ||
      G[36] !== eI ||
      G[37] !== ek ||
      G[38] !== eL ||
      G[39] !== eq ||
      G[40] !== eP ||
      G[41] !== ee ||
      G[42] !== eO
        ? ((D = eL
            ? eO(
                (0, t.jsx)(k.o, {
                  profileId: eP,
                  href: eL,
                  "aria-label": ee("web.callouts.open_profile_a11y", {
                    username: ek,
                  }),
                  className: (0, z.c)(
                    "shrink-0 transition-opacity hover:opacity-80",
                    eq && q,
                    eq && `block ${eI}`,
                  ),
                  children: eU,
                }),
              )
            : eU),
          (G[35] = eU),
          (G[36] = eI),
          (G[37] = ek),
          (G[38] = eL),
          (G[39] = eq),
          (G[40] = eP),
          (G[41] = ee),
          (G[42] = eO),
          (G[43] = D))
        : (D = G[43]),
      G[44] !== ek ||
      G[45] !== eL ||
      G[46] !== eq ||
      G[47] !== eP ||
      G[48] !== eO
        ? ((F = eL
            ? eO(
                (0, t.jsx)(k.o, {
                  profileId: eP,
                  href: eL,
                  className: (0, z.c)(
                    "truncate text-sm font-semibold text-text-primary hover:underline",
                    eq && q,
                  ),
                  children: ek,
                }),
              )
            : (0, t.jsx)("span", {
                className: "truncate text-sm font-semibold text-text-primary",
                children: ek,
              })),
          (G[44] = ek),
          (G[45] = eL),
          (G[46] = eq),
          (G[47] = eP),
          (G[48] = eO),
          (G[49] = F))
        : (F = G[49]),
      G[50] !== ey
        ? ((M = ey ? (0, t.jsx)(i.f, { size: 18 }) : null),
          (G[50] = ey),
          (G[51] = M))
        : (M = G[51]),
      G[52] !== F || G[53] !== M
        ? ((Q = (0, t.jsxs)("span", {
            className: "flex min-w-0 items-center gap-1",
            children: [F, M],
          })),
          (G[52] = F),
          (G[53] = M),
          (G[54] = Q))
        : (Q = G[54]),
      G[55] !== ei || G[56] !== et.caller?.twitterUrl
        ? ((V =
            et.caller?.twitterUrl || ei
              ? (0, t.jsx)(j.f, {
                  twitterUrl: et.caller?.twitterUrl,
                  xUsername: et.caller?.twitterUrl ? void 0 : ei,
                })
              : null),
          (G[55] = ei),
          (G[56] = et.caller?.twitterUrl),
          (G[57] = V))
        : (V = G[57]),
      G[58] !== et.createdAt
        ? ((K = (0, t.jsx)("span", {
            className: "min-w-0 shrink-0 truncate text-xs text-text-tertiary",
            children: (0, t.jsx)(N.f, { timestamp: et.createdAt }),
          })),
          (G[58] = et.createdAt),
          (G[59] = K))
        : (K = G[59]),
      G[60] !== ek ||
      G[61] !== et.authorCcUserId ||
      G[62] !== et.replyId ||
      G[63] !== ev
        ? ((H = ev
            ? (0, t.jsx)(w.f, {
                target: { kind: "reply", id: et.replyId },
                author: { userId: et.authorCcUserId, name: ek },
                density: "comfortable",
                className: "relative z-[2] -my-1 ml-auto",
              })
            : null),
          (G[60] = ek),
          (G[61] = et.authorCcUserId),
          (G[62] = et.replyId),
          (G[63] = ev),
          (G[64] = H))
        : (H = G[64]),
      G[65] !== Q || G[66] !== V || G[67] !== K || G[68] !== H
        ? ((B = (0, t.jsxs)("div", {
            className: "flex w-full items-center gap-1.5",
            children: [Q, V, K, H],
          })),
          (G[65] = Q),
          (G[66] = V),
          (G[67] = K),
          (G[68] = H),
          (G[69] = B))
        : (B = G[69]),
      G[70] !== et.content
        ? ((W = (0, t.jsx)("p", {
            className:
              "w-full whitespace-pre-wrap break-words text-sm leading-5 text-text-primary",
            children: (0, t.jsx)(y.f, { content: et.content }),
          })),
          (G[70] = et.content),
          (G[71] = W))
        : (W = G[71]),
      G[72] !== et.mediaUrl
        ? ((X = et.mediaUrl
            ? (0, t.jsx)(d.f, {
                src: et.mediaUrl,
                testId: "callout-reply-media",
                className: "mt-1",
              })
            : null),
          (G[72] = et.mediaUrl),
          (G[73] = X))
        : (X = G[73]),
      G[74] !== ea ||
      G[75] !== en ||
      G[76] !== ex ||
      G[77] !== ek ||
      G[78] !== er ||
      G[79] !== e_ ||
      G[80] !== el ||
      G[81] !== ec ||
      G[82] !== et.replyId ||
      G[83] !== ee
        ? ((Z = er
            ? null
            : (0, t.jsxs)("div", {
                className: "flex items-center gap-1",
                children: [
                  (0, t.jsxs)("button", {
                    type: "button",
                    onClick: (e) => {
                      (e.stopPropagation(), e_.toggle());
                    },
                    "aria-label": ee(
                      e_.isLiked
                        ? "web.callouts.unlike_reply_a11y"
                        : "web.callouts.like_reply_a11y",
                    ),
                    "aria-pressed": e_.isLiked,
                    "data-testid": "callout-reply-like",
                    className: (0, z.c)(
                      "relative z-[2] -ml-1.5 inline-flex w-fit items-center gap-1 rounded-full px-1.5 py-0.5 text-xs font-semibold tabular-nums transition-colors",
                      e_.isLiked
                        ? "text-text-primary"
                        : (0, z.c)("text-text-tertiary", h.$),
                    ),
                    children: [
                      e_.isLiked
                        ? (0, t.jsx)(m.cJ, {
                            className: (0, z.c)("size-3", h.k),
                          })
                        : (0, t.jsx)(p.cJ, { className: "size-3" }),
                      e_.likeCount > 0 ? (0, L.O)(e_.likeCount) : null,
                    ],
                  }),
                  (0, t.jsx)(x.f, {
                    sharePath: `/callouts/${el}/${ea}/${et.replyId}`,
                    shareTitle: ee("web.callouts.reply_share_title", {
                      name: ek,
                    }),
                    children: (0, t.jsx)("button", {
                      type: "button",
                      "aria-label": ee("web.callouts.share_reply_a11y"),
                      "data-testid": "callout-reply-share",
                      onClick: T,
                      className:
                        "relative z-[2] inline-flex w-fit items-center rounded-full px-1.5 py-0.5 text-text-tertiary transition-colors hover:bg-white/5 hover:text-text-secondary",
                      children: (0, t.jsx)(p.q4, { className: "size-3" }),
                    }),
                  }),
                  ec
                    ? (0, t.jsxs)("button", {
                        type: "button",
                        onClick: (e) => {
                          (e.stopPropagation(), ec());
                        },
                        "aria-label": ex
                          ? ee("web.callouts.hide_comments_a11y")
                          : en
                            ? ee("web.callouts.view_comments_a11y", {
                                count: en,
                              })
                            : ee("callouts.reply.title", { username: ek }),
                        "aria-expanded": ex,
                        "data-testid": "callout-reply-comments-toggle",
                        className: (0, z.c)(
                          "relative z-[2] inline-flex w-fit items-center gap-1 rounded-full px-1.5 py-0.5 text-xs font-semibold tabular-nums transition-colors",
                          ex
                            ? "text-text-secondary"
                            : "text-text-tertiary hover:bg-white/5 hover:text-text-secondary",
                        ),
                        children: [
                          (0, t.jsx)(p.Z2, { className: "size-3" }),
                          null != en ? (0, L.O)(en) : null,
                        ],
                      })
                    : null != en
                      ? (0, t.jsxs)("span", {
                          "data-testid": "callout-reply-comments-count",
                          "aria-label": ee("web.callouts.comments_count", {
                            count: en,
                          }),
                          className:
                            "inline-flex w-fit items-center gap-1 rounded-full px-1.5 py-0.5 text-xs font-semibold tabular-nums text-text-tertiary",
                          children: [
                            (0, t.jsx)(p.Z2, { className: "size-3" }),
                            (0, L.O)(en),
                          ],
                        })
                      : null,
                ],
              })),
          (G[74] = ea),
          (G[75] = en),
          (G[76] = ex),
          (G[77] = ek),
          (G[78] = er),
          (G[79] = e_),
          (G[80] = el),
          (G[81] = ec),
          (G[82] = et.replyId),
          (G[83] = ee),
          (G[84] = Z))
        : (Z = G[84]),
      G[85] !== ed || G[86] !== B || G[87] !== W || G[88] !== X || G[89] !== Z
        ? ((J = (0, t.jsxs)("div", {
            className: "flex min-w-0 flex-1 flex-col items-start gap-0.5",
            children: [B, W, X, Z, ed],
          })),
          (G[85] = ed),
          (G[86] = B),
          (G[87] = W),
          (G[88] = X),
          (G[89] = Z),
          (G[90] = J))
        : (J = G[90]),
      G[91] !== et.replyId || G[92] !== $ || G[93] !== D || G[94] !== J
        ? ((Y = (0, t.jsxs)("div", {
            "data-testid": "callout-reply-cell",
            "data-reply-id": eT,
            className: $,
            children: [D, J],
          })),
          (G[91] = et.replyId),
          (G[92] = $),
          (G[93] = D),
          (G[94] = J),
          (G[95] = Y))
        : (Y = G[95]),
      Y
    );
  }
  return O;
}
// Actual descriptors; parent selection/data/query/navigation are not reconstructed here.
export function createMainReplyRenderers({ jsx, ReplyCell }) {
  if (typeof jsx !== "function" || ReplyCell == null)
    throw new TypeError("Explicit JSX and stable ReplyCell required");
  const t = { jsx },
    d = { f: ReplyCell };
  return {
    missingCallout: ({
      reply,
      callout,
      replierAvatarShape,
      replierHref,
      fallbackXUsername,
    }) => {
      const w = reply,
        v = callout,
        L = replierAvatarShape,
        Z = replierHref,
        B = fallbackXUsername;
      return (0, t.jsx)(d.f, {
        reply: w,
        mint: "",
        calloutId: "",
        hideActions: !0,
        fallbackXUsername: B,
        replierAvatarShape: L,
        replierHref: Z,
        className: "border-b-0 pb-0",
      });
    },
    linkedCallout: ({
      reply,
      callout,
      replierAvatarShape,
      replierHref,
      fallbackXUsername,
    }) => {
      const w = reply,
        v = callout,
        L = replierAvatarShape,
        Z = replierHref,
        B = fallbackXUsername;
      return (0, t.jsx)(d.f, {
        reply: w,
        mint: v.coinMint,
        calloutId: v.calloutId ?? "",
        hideActions: !1,
        fallbackXUsername: B,
        replierAvatarShape: L,
        replierHref: Z,
        className:
          "pointer-events-none relative z-[2] w-full border-b-0 pb-0 pt-1 [&_a]:pointer-events-auto [&_button]:pointer-events-auto",
      });
    },
    unlinkedCallout: ({
      reply,
      callout,
      replierAvatarShape,
      replierHref,
      fallbackXUsername,
    }) => {
      const w = reply,
        v = callout,
        L = replierAvatarShape,
        Z = replierHref,
        B = fallbackXUsername;
      return (0, t.jsx)(d.f, {
        reply: w,
        mint: v.coinMint,
        calloutId: v.calloutId ?? "",
        hideActions: !0,
        fallbackXUsername: B,
        replierAvatarShape: L,
        replierHref: Z,
        className: "w-full border-b-0 pb-0 pt-1",
      });
    },
  };
}
