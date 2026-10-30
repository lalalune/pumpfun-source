export function createMobileFeedList({
  React,
  compiler,
  jsxRuntime,
  window,
  useFeatureFlag,
  usePositionsRead,
  useCoins,
  usePackCards,
  useUsers,
  isCollectibleEntry,
  isBase58Pubkey,
  normalizeMintKey,
  isPerpRow,
  useOpenPositionGate,
  PendingBanner,
  LoadMore,
  CalloutEntry,
  MainFeedRow,
  PositionInsert,
  RootCallout,
  Link,
  profileRoute,
  shortenAddress,
  normalizeImage,
  buildImage,
  RepostIcon,
  EmptyIcon,
  labelText
}) {
  const t = jsxRuntime,
    l = {
      c: compiler
    },
    i = React,
    a = {
      I3: RepostIcon,
      EX: EmptyIcon
    },
    n = {
      D: {
        WEB_PERPS: "webPerps",
        WEB_PACKS: "webPacks"
      }
    },
    o = {
      k: useFeatureFlag
    },
    c = {
      f: MainFeedRow
    },
    u = {
      $: profileRoute
    },
    m = {
      d: shortenAddress
    },
    f = {
      default: Link
    },
    p = {
      f: PositionInsert
    },
    g = {
      f: RootCallout
    },
    b = {
      f: normalizeImage
    },
    x = {
      Z: buildImage,
      z: {
        list: 40
      }
    },
    w = {
      f: LoadMore
    },
    y = {
      f: PendingBanner
    },
    v = {
      f: CalloutEntry
    },
    J = {
      f: useOpenPositionGate
    },
    ef = {
      f: usePositionsRead
    },
    e_ = {
      f: useCoins
    },
    eg = {
      f: usePackCards
    },
    ev = {
      f: useUsers
    },
    eN = {
      Q: isCollectibleEntry
    },
    ek = {
      l: isPerpRow
    },
    eM = {
      T: labelText
    },
    eP = {
      c: normalizeMintKey
    },
    eT = {
      f: isBase58Pubkey
    };
  let eD = [];
  let eB = (0, i.memo)(e => {
    let r,
      i,
      a,
      n,
      o = (0, l.c)(9);
    o[0] !== e ? ({
      applyOpenPositionGate: r,
      ...i
    } = e, o[0] = e, o[1] = r, o[2] = i) : (r = o[1], i = o[2]);
    let {
      entry: s
    } = i;
    o[3] !== s.coinMint || o[4] !== s.positionPnl || o[5] !== s.userId ? (a = {
      mint: s.coinMint,
      authorAddress: s.userId,
      positionPnl: s.positionPnl
    }, o[3] = s.coinMint, o[4] = s.positionPnl, o[5] = s.userId, o[6] = a) : a = o[6];
    let {
      shouldHide: d
    } = (0, J.f)(a);
    return r && d ? null : (o[7] !== i ? (n = (0, t.jsx)(v.f, {
      ...i
    }), o[7] = i, o[8] = n) : n = o[8], n);
  });
  let eG = e => {
    let r,
      a,
      s,
      d,
      u,
      m,
      f,
      p,
      g,
      b,
      x,
      v,
      _,
      j,
      N,
      k,
      A,
      S,
      M,
      P,
      T = (0, l.c)(91),
      {
        feed: C,
        listAriaLabel: I,
        errorTitle: D,
        emptyTitle: E,
        emptyDescription: U,
        applyOpenPositionGate: L,
        surface: F,
        autoLoadMore: R,
        autoRevealAtTop: Q,
        viewerAddress: $,
        isLoggedIn: K,
        viewerFollowing: H
      } = e,
      z = void 0 !== R && R,
      G = void 0 !== Q && Q,
      {
        rows: B,
        isLoadingHistory: O,
        error: q,
        pendingNewCount: W,
        pendingPreview: V,
        showNewCallouts: Z,
        hasNextPage: J,
        hasUnseen: X,
        isFetchingNextPage: Y,
        fetchNextPage: ee
      } = C;
    T[0] !== Z ? (r = () => {
      Z({
        trigger: "tap"
      }), window.scrollTo({
        top: 0,
        behavior: "smooth"
      });
    }, T[0] = Z, T[1] = r) : r = T[1];
    let et = r;
    T[2] !== G || T[3] !== W || T[4] !== Z ? (a = () => {
      if (!G || 0 === W) return;
      let e = () => {
        window.scrollY > 8 || Z({
          trigger: "auto"
        });
      };
      return e(), window.addEventListener("scroll", e, {
        passive: !0
      }), () => window.removeEventListener("scroll", e);
    }, s = [G, W, Z], T[2] = G, T[3] = W, T[4] = Z, T[5] = a, T[6] = s) : (a = T[5], s = T[6]), (0, i.useEffect)(a, s), T[7] !== B ? (d = Array.from(new Set(B.flatMap(eW))), T[7] = B, T[8] = d) : d = T[8];
    let el = d;
    if (T[9] !== V || T[10] !== B) {
      let e,
        t = [...B.flatMap(eV), ...V.map(eZ)];
      T[12] !== t ? (e = new Set(t), T[12] = t, T[13] = e) : e = T[13], u = Array.from(e), T[9] = V, T[10] = B, T[11] = u;
    } else u = T[11];
    let er = u;
    T[14] !== B ? (m = B.flatMap(eJ), T[14] = B, T[15] = m) : m = T[15];
    let ei = m,
      {
        readFor: ea
      } = (0, ef.f)(ei),
      en = (0, o.k)(n.D.WEB_PERPS, !1);
    T[16] !== en || T[17] !== B ? (f = en ? B : B.filter(eX), T[16] = en, T[17] = B, T[18] = f) : f = T[18];
    let eo = f;
    if (T[19] !== eo) {
      for (let e of (p = new Set(), eo)) {
        if (p.size >= 2) break;
        "callout" === e.type && e.entry.mediaUrl && p.add(e.key);
      }
      T[19] = eo, T[20] = p;
    } else p = T[20];
    let es = p,
      ed = 0 === er.length;
    T[21] !== er || T[22] !== ed ? (g = {
      mints: er,
      disabled: ed
    }, T[21] = er, T[22] = ed, T[23] = g) : g = T[23];
    let {
      coins: ec,
      loading: eu
    } = (0, e_.f)(g);
    if (T[24] !== ec) {
      for (let e of (b = new Map(), ec)) e?.mint && b.set((0, eP.c)(e.mint), e);
      T[24] = ec, T[25] = b;
    } else b = T[25];
    let em = b,
      ep = (0, o.k)(n.D.WEB_PACKS, !1);
    e: {
      let e, t;
      if (!ep || eu) {
        x = eD;
        break e;
      }
      if (T[26] !== em || T[27] !== eo) {
        for (let t of (e = new Set(), eo)) {
          if ("callout" !== t.type || (0, eN.Q)(t.entry)) continue;
          let l = t.entry.coinMint;
          !(0, eT.f)(l) || em.has((0, eP.c)(l)) || e.add(l);
        }
        T[26] = em, T[27] = eo, T[28] = e;
      } else e = T[28];
      T[29] !== e ? (t = 0 === e.size ? eD : [...e], T[29] = e, T[30] = t) : t = T[30], x = t;
    }
    let eb = x,
      {
        cardByMint: ex
      } = (0, eg.f)(eb);
    if (T[31] !== em || T[32] !== V) {
      let e;
      T[34] !== em ? (e = e => ({
        key: e.key,
        mint: e.coinMint,
        imageUrl: em.get((0, eP.c)(e.coinMint))?.image_uri
      }), T[34] = em, T[35] = e) : e = T[35], v = V.map(e), T[31] = em, T[32] = V, T[33] = v;
    } else v = T[33];
    let eh = v;
    T[36] !== el ? (_ = {
      userAddresses: el
    }, T[36] = el, T[37] = _) : _ = T[37];
    let {
      data: ew
    } = (0, ev.f)(_);
    T[38] !== ew ? (j = void 0 === ew ? [] : ew, T[38] = ew, T[39] = j) : j = T[39];
    let ey = j;
    if (T[40] !== ey) {
      for (let e of (N = new Map(), ey)) e?.address && N.set(e.address, e);
      T[40] = ey, T[41] = N;
    } else N = T[41];
    let ej = N;
    if (O && 0 === B.length) {
      let e;
      return T[42] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsx)(eO, {}), T[42] = e) : e = T[42], e;
    }
    if (q && 0 === B.length) {
      let e, l;
      return T[43] !== q ? (e = (0, eM.T)(q, "error-message"), T[43] = q, T[44] = e) : e = T[44], T[45] !== D || T[46] !== e ? (l = (0, t.jsx)(eq, {
        title: D,
        description: e
      }), T[45] = D, T[46] = e, T[47] = l) : l = T[47], l;
    }
    if (0 === B.length) {
      let e;
      return T[48] !== U || T[49] !== E ? (e = (0, t.jsx)(eq, {
        title: E,
        description: U
      }), T[48] = U, T[49] = E, T[50] = e) : e = T[50], e;
    }
    if (T[51] !== et || T[52] !== eh || T[53] !== W ? (k = (0, t.jsx)(y.f, {
      count: W,
      avatars: eh,
      onClick: et
    }), T[51] = et, T[52] = eh, T[53] = W, T[54] = k) : k = T[54], T[55] !== L || T[56] !== ex || T[57] !== em || T[58] !== K || T[59] !== es || T[60] !== ea || T[61] !== F || T[62] !== ej || T[63] !== $ || T[64] !== H || T[65] !== eo) {
      let e;
      T[67] !== L || T[68] !== ex || T[69] !== em || T[70] !== K || T[71] !== es || T[72] !== ea || T[73] !== F || T[74] !== ej || T[75] !== $ || T[76] !== H ? (e = (e, l) => {
        if ("callout" === e.type) return (0, t.jsx)("li", {
          children: (0, t.jsx)(eB, {
            entry: e.entry,
            coin: em.get((0, eP.c)(e.entry.coinMint)),
            card: ex.get(e.entry.coinMint) ?? null,
            user: ej.get(e.entry.userId),
            position: l,
            mediaPriority: es.has(e.key),
            applyOpenPositionGate: L,
            surface: F,
            viewerAddress: $,
            isLoggedIn: K,
            viewerFollowing: H,
            className: "px-4"
          })
        }, e.key);
        if ("trade" === e.type) return null;
        let r = "repost" === e.type ? e.callout : e.row.callout,
          i = e.coin ? em.get((0, eP.c)(e.coin.mint)) : void 0,
          a = i?.symbol ?? e.coin?.symbol,
          n = i?.name ?? e.coin?.name,
          o = i?.image_uri ?? e.coin?.image,
          s = i?.chain_id ?? e.coin?.chainId?.toString(),
          d = r ? ea(r.author.walletAddress, r.coinMint) : void 0;
        return (0, t.jsx)("li", {
          children: "repost" === e.type ? (0, t.jsx)(h, {
            row: e,
            coinSymbol: a,
            coinName: n,
            coinImageUri: o,
            coinChainId: s,
            positionRead: d
          }) : (0, t.jsx)(c.f, {
            row: e.row,
            variant: e.type,
            coinSymbol: a,
            coinName: n,
            coinImageUri: o,
            coinChainId: s,
            positionRead: d,
            xUsername: e.xUsername
          })
        }, e.key);
      }, T[67] = L, T[68] = ex, T[69] = em, T[70] = K, T[71] = es, T[72] = ea, T[73] = F, T[74] = ej, T[75] = $, T[76] = H, T[77] = e) : e = T[77], A = eo.map(e), T[55] = L, T[56] = ex, T[57] = em, T[58] = K, T[59] = es, T[60] = ea, T[61] = F, T[62] = ej, T[63] = $, T[64] = H, T[65] = eo, T[66] = A;
    } else A = T[66];
    return T[78] !== I || T[79] !== A ? (S = (0, t.jsx)("ul", {
      className: "-mx-4 flex flex-col",
      "aria-label": I,
      children: A
    }), T[78] = I, T[79] = A, T[80] = S) : S = T[80], T[81] !== z || T[82] !== ee || T[83] !== J || T[84] !== X || T[85] !== Y ? (M = (0, t.jsx)(w.f, {
      hasNextPage: J,
      autoLoadHasMore: X,
      isFetchingNextPage: Y,
      onFetchNextPage: ee,
      autoLoad: z
    }), T[81] = z, T[82] = ee, T[83] = J, T[84] = X, T[85] = Y, T[86] = M) : M = T[86], T[87] !== k || T[88] !== S || T[89] !== M ? (P = (0, t.jsxs)(t.Fragment, {
      children: [k, S, M]
    }), T[87] = k, T[88] = S, T[89] = M, T[90] = P) : P = T[90], P;
  };
  let eO = () => {
    let e,
      r = (0, l.c)(1);
    return r[0] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsx)("div", {
      "aria-hidden": !0,
      "data-testid": "feed-skeleton",
      className: "-mx-4 flex flex-col",
      children: Array.from({
        length: 6
      }).map(eY)
    }), r[0] = e) : e = r[0], e;
  };
  let eq = e => {
    let r,
      i,
      n,
      o,
      s = (0, l.c)(8),
      {
        title: d,
        description: c
      } = e;
    return s[0] === Symbol.for("react.memo_cache_sentinel") ? (r = (0, t.jsx)("div", {
      className: "flex size-10 items-center justify-center rounded-full border border-primary-green/30 bg-primary-green/10 text-primary-green",
      children: (0, t.jsx)(a.EX, {
        className: "size-5"
      })
    }), s[0] = r) : r = s[0], s[1] !== d ? (i = (0, t.jsx)("h2", {
      className: "text-base font-semibold text-text-primary",
      children: d
    }), s[1] = d, s[2] = i) : i = s[2], s[3] !== c ? (n = c ? (0, t.jsx)("p", {
      className: "max-w-md text-sm text-text-tertiary",
      children: c
    }) : null, s[3] = c, s[4] = n) : n = s[4], s[5] !== i || s[6] !== n ? (o = (0, t.jsxs)("section", {
      className: "flex flex-col items-center gap-2 rounded-2xl border border-border-tertiary bg-bg-secondary p-8 text-center",
      children: [r, i, n]
    }), s[5] = i, s[6] = n, s[7] = o) : o = s[7], o;
  };
  let eK = {
    "for-you": {
      listAriaLabel: "web.feed.list_for_you",
      errorTitle: "web.feed.error_for_you",
      emptyTitle: "web.feed.empty_for_you_title",
      emptyDescription: "web.feed.empty_for_you_description"
    },
    top: {
      listAriaLabel: "web.feed.list_top",
      errorTitle: "web.feed.error_top",
      emptyTitle: "web.feed.empty_top_title",
      emptyDescription: "web.feed.empty_top_description"
    },
    following: {
      listAriaLabel: "web.feed.list_following",
      errorTitle: "web.feed.error_following",
      emptyTitle: "web.feed.empty_following_title",
      emptyDescription: "web.feed.empty_following_description"
    }
  };
  let ez = e => {
    let {
      t: l,
      tab: r,
      showFollowingSignedOut: i,
      feedByTab: a,
      address: n,
      isLoggedIn: o,
      viewerFollowing: s
    } = e;
    if (i) return (0, t.jsx)(eq, {
      title: l("web.feed.signed_out_following_title"),
      description: l("web.feed.signed_out_following_description")
    });
    let d = eK[r];
    return (0, t.jsx)(eG, {
      feed: a[r],
      surface: "for-you" === r ? "home_feed" : void 0,
      listAriaLabel: l(d.listAriaLabel),
      errorTitle: l(d.errorTitle),
      emptyTitle: l(d.emptyTitle),
      emptyDescription: l(d.emptyDescription),
      applyOpenPositionGate: "top" !== r,
      autoLoadMore: "for-you" === r,
      autoRevealAtTop: "following" === r,
      viewerAddress: n,
      isLoggedIn: o,
      viewerFollowing: s
    }, r);
  };
  function h(e) {
    let r,
      i,
      n,
      o,
      s,
      d,
      c,
      h,
      w,
      y,
      v,
      _ = (0, l.c)(42),
      {
        row: j,
        coinSymbol: N,
        coinName: k,
        coinImageUri: A,
        coinChainId: S,
        positionRead: M,
        testId: P
      } = e,
      T = void 0 === P ? "callout-repost-row" : P,
      {
        reposter: C,
        callout: I
      } = j;
    _[0] !== C.address || _[1] !== C.name ? (r = C.name?.trim() || (C.address ? (0, m.d)(C.address, 4, 4) : "Someone"), _[0] = C.address, _[1] = C.name, _[2] = r) : r = _[2];
    let D = r;
    _[3] !== I.author.username || _[4] !== I.author.walletAddress ? (i = I.author.username?.trim() || (I.author.walletAddress ? (0, m.d)(I.author.walletAddress, 4, 4) : "a caller"), _[3] = I.author.username, _[4] = I.author.walletAddress, _[5] = i) : i = _[5];
    let E = i;
    _[6] !== N ? (n = N?.replace(/^\$/, ""), _[6] = N, _[7] = n) : n = _[7];
    let U = n,
      L = null != I.calloutId ? `/callouts/${I.coinMint}/${I.calloutId}` : null,
      F = `${T}-attribution`;
    _[8] === Symbol.for("react.memo_cache_sentinel") ? (o = (0, t.jsx)(a.I3, {
      className: "size-3.5 shrink-0",
      "aria-hidden": !0
    }), _[8] = o) : o = _[8], _[9] !== C.address || _[10] !== D ? (s = C.address ? (0, t.jsx)(f.default, {
      href: (0, u.$)(C.address),
      className: "relative z-[2] truncate font-medium text-text-secondary hover:underline",
      children: D
    }) : (0, t.jsx)("span", {
      className: "truncate font-medium text-text-secondary",
      children: D
    }), _[9] = C.address, _[10] = D, _[11] = s) : s = _[11], _[12] !== F || _[13] !== s ? (d = (0, t.jsxs)("p", {
      "data-testid": F,
      className: "mb-1 flex items-center gap-1.5 pl-4 text-xs text-text-tertiary",
      children: [o, s, "reposted"]
    }), _[12] = F, _[13] = s, _[14] = d) : d = _[14];
    let R = I.author.walletAddress ?? "";
    _[15] !== I.author.avatarUrl ? (c = (0, x.Z)({
      sourceUrl: (0, b.f)(I.author.avatarUrl),
      width: x.z.list
    }), _[15] = I.author.avatarUrl, _[16] = c) : c = _[16], _[17] !== U ? (h = U ? (0, t.jsxs)("span", {
      className: "truncate text-xs text-text-tertiary",
      children: ["$", U]
    }) : void 0, _[17] = U, _[18] = h) : h = _[18];
    let Q = L ?? void 0,
      $ = `${T}-callout`,
      K = I.author.walletAddress ?? "";
    return _[19] !== I.coinMint || _[20] !== S || _[21] !== A || _[22] !== k || _[23] !== N || _[24] !== M || _[25] !== K ? (w = (0, t.jsx)(p.f, {
      mint: I.coinMint,
      authorAddress: K,
      positionRead: M,
      symbol: N,
      name: k,
      imageUri: A,
      chainId: S
    }), _[19] = I.coinMint, _[20] = S, _[21] = A, _[22] = k, _[23] = N, _[24] = M, _[25] = K, _[26] = w) : w = _[26], _[27] !== I.createdAtMs || _[28] !== I.mediaUrl || _[29] !== I.note || _[30] !== E || _[31] !== h || _[32] !== Q || _[33] !== $ || _[34] !== w || _[35] !== R || _[36] !== c ? (y = (0, t.jsx)(g.f, {
      authorAddress: R,
      authorName: E,
      authorAvatarUrl: c,
      createdAt: I.createdAtMs,
      note: I.note,
      mediaUrl: I.mediaUrl,
      nameAdornment: h,
      density: "compact",
      noteSize: "sm",
      href: Q,
      testId: $,
      className: "border-b-0 pb-0",
      children: w
    }), _[27] = I.createdAtMs, _[28] = I.mediaUrl, _[29] = I.note, _[30] = E, _[31] = h, _[32] = Q, _[33] = $, _[34] = w, _[35] = R, _[36] = c, _[37] = y) : y = _[37], _[38] !== y || _[39] !== d || _[40] !== T ? (v = (0, t.jsxs)("div", {
      "data-testid": T,
      className: "w-full border-b border-border-tertiary px-4 pb-3 pt-2 transition-colors hover:bg-bg-secondary",
      children: [d, y]
    }), _[38] = y, _[39] = d, _[40] = T, _[41] = v) : v = _[41], v;
  }
  function eW(e) {
    return "callout" === e.type ? [e.entry.userId] : [];
  }
  function eV(e) {
    return "callout" === e.type ? [e.entry.coinMint] : "trade" === e.type ? [] : e.coin?.mint ?? [];
  }
  function eZ(e) {
    return e.coinMint;
  }
  function eJ(e) {
    return "reply" === e.type || "quote" === e.type ? [{
      userId: e.row.callout?.author.walletAddress,
      mint: e.row.callout?.coinMint
    }] : "repost" === e.type ? [{
      userId: e.callout.author.walletAddress,
      mint: e.callout.coinMint
    }] : [];
  }
  function eX(e) {
    return !(0, ek.l)(e);
  }
  function eY(e, l) {
    return (0, t.jsxs)("div", {
      className: "flex flex-col gap-1.5 border-b border-border-tertiary px-4 py-2",
      children: [(0, t.jsxs)("div", {
        className: "flex items-center gap-3",
        children: [(0, t.jsx)("div", {
          className: "size-9 animate-pulse rounded-full bg-bg-quaternary"
        }), (0, t.jsxs)("div", {
          className: "flex flex-col gap-1.5",
          children: [(0, t.jsx)("div", {
            className: "h-3.5 w-28 animate-pulse rounded bg-bg-quaternary"
          }), (0, t.jsx)("div", {
            className: "h-3 w-48 animate-pulse rounded bg-bg-tertiary"
          })]
        })]
      }), (0, t.jsx)("div", {
        className: "ml-10 h-[60px] animate-pulse rounded-xl bg-bg-tertiary"
      })]
    }, l);
  }
  return {
    FeedList: eG,
    selectFeed: ez,
    RepostRow: h,
    EmptyState: eq,
    Skeleton: eO
  };
}
