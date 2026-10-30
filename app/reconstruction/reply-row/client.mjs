import { replyContextPreview } from "../user-replies/client.mjs";
const threadPath = (e) => {
  let { coinMint: t, calloutId: i, replyId: l } = e;
  return `/callouts/${t}/${i}/${l}`;
};
const ROW_INSET = { terminal: "px-3", comfortable: "px-5" };
// Complete source owner; existing render/leaf/provider APIs are explicit capabilities.
export function createOrdinaryReplyRow({
  jsx,
  jsxs,
  Fragment,
  useMemoCache,
  classNames,
  useTranslation,
  truncateAddress,
  normalizeAvatarInput,
  previewImage,
  Link,
  CoinPosition,
  RootCallout,
  QuotePreview,
  ReplyCell,
}) {
  for (const [name, cap] of Object.entries({
    jsx,
    jsxs,
    useMemoCache,
    classNames,
    useTranslation,
    truncateAddress,
    normalizeAvatarInput,
    previewImage,
  }))
    if (typeof cap !== "function")
      throw new TypeError("Explicit ordinary row capability required: " + name);
  for (const [name, cap] of Object.entries({
    Fragment,
    Link,
    CoinPosition,
    RootCallout,
    QuotePreview,
    ReplyCell,
  }))
    if (cap == null)
      throw new TypeError("Explicit ordinary row renderer required: " + name);
  const t = { jsx, jsxs, Fragment },
    r = { c: useMemoCache },
    l = { d: truncateAddress },
    a = { default: Link },
    i = { f: useTranslation },
    n = { f: CoinPosition },
    s = { f: RootCallout },
    o = { f: QuotePreview },
    d = { f: ReplyCell },
    c = { f: normalizeAvatarInput },
    u = { U: ROW_INSET },
    m = { Z: previewImage, z: { list: 40 } },
    f = { f: threadPath },
    p = { g: replyContextPreview },
    h = { c: classNames };
  return function (e) {
    let v,
      b,
      g,
      y,
      x,
      w,
      _,
      A,
      j,
      I,
      U,
      S,
      N,
      C,
      k,
      E,
      M,
      P = (0, r.c)(90),
      {
        row: F,
        variant: R,
        coinSymbol: T,
        coinName: z,
        coinImageUri: O,
        coinChainId: $,
        positionRead: K,
        xUsername: B,
        replierAvatarShape: L,
        replierHref: Z,
        density: q,
        inset: W,
        divider: H,
        testId: V,
      } = e,
      G = void 0 === R ? "reply" : R,
      D = void 0 === q ? "terminal" : q,
      X = void 0 === W ? "density" : W,
      Y = void 0 === H || H,
      Q = void 0 === V ? "callout-reply-row" : V,
      { t: J } = (0, i.f)();
    if (
      P[0] !== T ||
      P[1] !== D ||
      P[2] !== Y ||
      P[3] !== X ||
      P[4] !== L ||
      P[5] !== Z ||
      P[6] !== F ||
      P[7] !== J ||
      P[8] !== Q ||
      P[9] !== G ||
      P[10] !== B
    ) {
      I = Symbol.for("react.early_return_sentinel");
      e: {
        let e,
          r,
          a,
          i,
          n = (0, h.c)(
            "w-full py-3",
            Y && "border-b border-border-secondary",
            "density" === X && ("comfortable" === D ? u.U.comfortable : "px-4"),
          );
        if (
          (({ reply: w, parent: y, callout: v } = F),
          P[21] !== v || P[22] !== J
            ? ((e =
                v?.author.username?.trim() ||
                (v?.author.walletAddress
                  ? (0, l.d)(v.author.walletAddress, 4, 4)
                  : J("web.callouts.quoted_anonymous_author"))),
              (P[21] = v),
              (P[22] = J),
              (P[23] = e))
            : (e = P[23]),
          (b = e),
          P[24] !== T
            ? ((r = T?.replace(/^\$/, "")), (P[24] = T), (P[25] = r))
            : (r = P[25]),
          (_ = r),
          P[26] !== v || P[27] !== w
            ? ((a =
                v?.calloutId != null
                  ? (0, f.f)({
                      coinMint: v.coinMint,
                      calloutId: v.calloutId,
                      replyId: w.replyId,
                    })
                  : null),
              (P[26] = v),
              (P[27] = w),
              (P[28] = a))
            : (a = P[28]),
          (g = a),
          P[29] !== y
            ? ((i = y?.reply
                ? y.reply.caller?.username?.trim() ||
                  (y.reply.caller?.walletAddress
                    ? (0, l.d)(y.reply.caller.walletAddress, 4, 4)
                    : (0, l.d)(y.reply.userId, 4, 4))
                : null),
              (P[29] = y),
              (P[30] = i))
            : (i = P[30]),
          (x = i),
          !v)
        ) {
          let e, r, l;
          (P[31] !== J || P[32] !== G
            ? ((e = J(
                "quote" === G
                  ? "web.callouts.quoting_deleted_callout"
                  : "web.callouts.replying_on_deleted_callout",
              )),
              (P[31] = J),
              (P[32] = G),
              (P[33] = e))
            : (e = P[33]),
            P[34] !== e
              ? ((r = (0, t.jsx)("span", {
                  className: "text-xs text-text-tertiary",
                  children: e,
                })),
                (P[34] = e),
                (P[35] = r))
              : (r = P[35]),
            P[36] !== L || P[37] !== Z || P[38] !== w || P[39] !== B
              ? ((l = (0, t.jsx)(d.f, {
                  reply: w,
                  mint: "",
                  calloutId: "",
                  hideActions: !0,
                  fallbackXUsername: B,
                  replierAvatarShape: L,
                  replierHref: Z,
                  className: "border-b-0 pb-0",
                })),
                (P[36] = L),
                (P[37] = Z),
                (P[38] = w),
                (P[39] = B),
                (P[40] = l))
              : (l = P[40]),
            (I = (0, t.jsxs)("div", {
              "data-testid": Q,
              className: (0, h.c)(n, "flex flex-col"),
              children: [r, l],
            })));
          break e;
        }
        ((A = Q),
          (j = (0, h.c)(
            n,
            "transition-colors",
            "comfortable" === D
              ? "hover:bg-bg-tertiary"
              : "hover:bg-bg-secondary",
          )));
      }
      ((P[0] = T),
        (P[1] = D),
        (P[2] = Y),
        (P[3] = X),
        (P[4] = L),
        (P[5] = Z),
        (P[6] = F),
        (P[7] = J),
        (P[8] = Q),
        (P[9] = G),
        (P[10] = B),
        (P[11] = v),
        (P[12] = b),
        (P[13] = g),
        (P[14] = y),
        (P[15] = x),
        (P[16] = w),
        (P[17] = _),
        (P[18] = A),
        (P[19] = j),
        (P[20] = I));
    } else
      ((v = P[11]),
        (b = P[12]),
        (g = P[13]),
        (y = P[14]),
        (x = P[15]),
        (w = P[16]),
        (_ = P[17]),
        (A = P[18]),
        (j = P[19]),
        (I = P[20]));
    if (I !== Symbol.for("react.early_return_sentinel")) return I;
    let ee = v.author.walletAddress ?? "";
    (P[41] !== v.author.avatarUrl
      ? ((U = (0, m.Z)({
          sourceUrl: (0, c.f)(v.author.avatarUrl),
          width: m.z.list,
        })),
        (P[41] = v.author.avatarUrl),
        (P[42] = U))
      : (U = P[42]),
      P[43] !== _
        ? ((S = _
            ? (0, t.jsxs)("span", {
                className: "truncate text-xs text-text-tertiary",
                children: ["$", _],
              })
            : void 0),
          (P[43] = _),
          (P[44] = S))
        : (S = P[44]));
    let et = "comfortable" === D ? "comfortable" : "compact",
      er = "comfortable" === D ? "md" : "sm",
      el = g ?? void 0,
      ea = `${Q}-op`;
    if (
      P[45] !== y ||
      P[46] !== x ||
      P[47] !== F ||
      P[48] !== J ||
      P[49] !== Q ||
      P[50] !== G
    ) {
      let e;
      ((N =
        "quote" === G
          ? (0, t.jsx)(o.f, { quoted: (0, p.g)(F) })
          : y
            ? (0, t.jsx)("span", {
                "data-testid": `${Q}-parent`,
                className:
                  "truncate border-l-2 border-border-secondary pl-2 text-xs text-text-tertiary",
                children:
                  y.tombstone || !y.reply
                    ? J("web.callouts.replying_to_deleted")
                    : (0, t.jsxs)(t.Fragment, {
                        children: [
                          (0, t.jsx)("span", {
                            className: "font-medium text-text-secondary",
                            children: x,
                          }),
                          ": ",
                          (e = y.reply.content.replace(/\s+/g, " ").trim())
                            .length > 80
                            ? `${e.slice(0, 80)}…`
                            : e,
                        ],
                      }),
              })
            : null),
        (P[45] = y),
        (P[46] = x),
        (P[47] = F),
        (P[48] = J),
        (P[49] = Q),
        (P[50] = G),
        (P[51] = N));
    } else N = P[51];
    let ei = v.author.walletAddress ?? "",
      en = "comfortable" === D ? "w-full" : void 0;
    return (
      P[52] !== v.coinMint ||
      P[53] !== $ ||
      P[54] !== O ||
      P[55] !== z ||
      P[56] !== T ||
      P[57] !== D ||
      P[58] !== K ||
      P[59] !== ei ||
      P[60] !== en
        ? ((C = (0, t.jsx)(n.f, {
            mint: v.coinMint,
            authorAddress: ei,
            positionRead: K,
            symbol: T,
            name: z,
            imageUri: O,
            chainId: $,
            density: D,
            className: en,
          })),
          (P[52] = v.coinMint),
          (P[53] = $),
          (P[54] = O),
          (P[55] = z),
          (P[56] = T),
          (P[57] = D),
          (P[58] = K),
          (P[59] = ei),
          (P[60] = en),
          (P[61] = C))
        : (C = P[61]),
      P[62] !== v.createdAtMs ||
      P[63] !== v.mediaUrl ||
      P[64] !== v.note ||
      P[65] !== b ||
      P[66] !== S ||
      P[67] !== et ||
      P[68] !== er ||
      P[69] !== el ||
      P[70] !== ea ||
      P[71] !== N ||
      P[72] !== C ||
      P[73] !== ee ||
      P[74] !== U
        ? ((k = (0, t.jsxs)(s.f, {
            authorAddress: ee,
            authorName: b,
            authorAvatarUrl: U,
            createdAt: v.createdAtMs,
            note: v.note,
            mediaUrl: v.mediaUrl,
            nameAdornment: S,
            density: et,
            noteSize: er,
            forceThreadRail: !0,
            href: el,
            testId: ea,
            className: "border-b-0 pb-0",
            children: [N, C],
          })),
          (P[62] = v.createdAtMs),
          (P[63] = v.mediaUrl),
          (P[64] = v.note),
          (P[65] = b),
          (P[66] = S),
          (P[67] = et),
          (P[68] = er),
          (P[69] = el),
          (P[70] = ea),
          (P[71] = N),
          (P[72] = C),
          (P[73] = ee),
          (P[74] = U),
          (P[75] = k))
        : (k = P[75]),
      P[76] !== v.calloutId ||
      P[77] !== v.coinMint ||
      P[78] !== g ||
      P[79] !== L ||
      P[80] !== Z ||
      P[81] !== w ||
      P[82] !== J ||
      P[83] !== B
        ? ((E = g
            ? (0, t.jsxs)("div", {
                className: "relative",
                children: [
                  (0, t.jsx)(a.default, {
                    href: g,
                    "aria-label": J("web.callouts.open_thread_at_reply_a11y"),
                    className: "absolute inset-0 z-[1]",
                  }),
                  (0, t.jsx)(d.f, {
                    reply: w,
                    mint: v.coinMint,
                    calloutId: v.calloutId ?? "",
                    hideActions: !1,
                    fallbackXUsername: B,
                    replierAvatarShape: L,
                    replierHref: Z,
                    className:
                      "pointer-events-none relative z-[2] w-full border-b-0 pb-0 pt-1 [&_a]:pointer-events-auto [&_button]:pointer-events-auto",
                  }),
                ],
              })
            : (0, t.jsx)(d.f, {
                reply: w,
                mint: v.coinMint,
                calloutId: v.calloutId ?? "",
                hideActions: !0,
                fallbackXUsername: B,
                replierAvatarShape: L,
                replierHref: Z,
                className: "w-full border-b-0 pb-0 pt-1",
              })),
          (P[76] = v.calloutId),
          (P[77] = v.coinMint),
          (P[78] = g),
          (P[79] = L),
          (P[80] = Z),
          (P[81] = w),
          (P[82] = J),
          (P[83] = B),
          (P[84] = E))
        : (E = P[84]),
      P[85] !== k || P[86] !== E || P[87] !== A || P[88] !== j
        ? ((M = (0, t.jsxs)("div", {
            "data-testid": A,
            className: j,
            children: [k, E],
          })),
          (P[85] = k),
          (P[86] = E),
          (P[87] = A),
          (P[88] = j),
          (P[89] = M))
        : (M = P[89]),
      M
    );
  };
}
