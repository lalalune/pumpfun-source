// Reconstructed source boundary. Captured factories are never imported or evaluated.
// Callers must select reviewed physical variants and supply the external runtimes.
function helpers0(decodeBase58) {
  const assets = (e) => ({
    ...(null != e.assetClass ? { assetClass: e.assetClass } : {}),
    ...(null != e.collectible ? { collectible: e.collectible } : {}),
  });
  const excludeAuthor = (() => {
    const l = (e, t) => {
      let a = e.holders.filter((e) => !t(e));
      if (a.length === e.holders.length) return e;
      if (0 === a.length) return null;
      let i = e.holders.length - a.length;
      return { holders: a, totalCount: Math.max(e.totalCount - i, a.length) };
    };
    return (e, t) => (e && t ? l(e, (e) => e.userId === t) : e);
  })();
  const chainFromId = (() => {
    const i = { d: 'near:mainnet', W: 'starknet:SN_MAIN' };
    return (e) => (e === i.d || e === i.W ? e : void 0);
  })();
  const isSolanaMint = (() => {
    const t = { f: { decode: decodeBase58 } };
    return function (e) {
      try {
        return 32 === t.f.decode(e).length;
      } catch {
        return !1;
      }
    };
  })();
  return { assets, excludeAuthor, chainFromId, isSolanaMint };
}
function helpers1(decodeBase58) {
  const assets = (e) => ({
    ...(null != e.assetClass ? { assetClass: e.assetClass } : {}),
    ...(null != e.collectible ? { collectible: e.collectible } : {}),
  });
  const excludeAuthor = (() => {
    const l = (e, t) => {
      let r = e.holders.filter((e) => !t(e));
      if (r.length === e.holders.length) return e;
      if (0 === r.length) return null;
      let n = e.holders.length - r.length;
      return { holders: r, totalCount: Math.max(e.totalCount - n, r.length) };
    };
    return (e, t) => (e && t ? l(e, (e) => e.userId === t) : e);
  })();
  const chainFromId = (() => {
    const n = { d: 'near:mainnet', W: 'starknet:SN_MAIN' };
    return (e) => (e === n.d || e === n.W ? e : void 0);
  })();
  const isSolanaMint = (() => {
    const t = { f: { decode: decodeBase58 } };
    return function (e) {
      try {
        return 32 === t.f.decode(e).length;
      } catch {
        return !1;
      }
    };
  })();
  return { assets, excludeAuthor, chainFromId, isSolanaMint };
}
function normalizer0(helpers) {
  const t = {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...('boolean' == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...('boolean' == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
    i = { E: helpers.assets },
    a = { i: helpers.excludeAuthor },
    l = { f: helpers.isSolanaMint },
    n = { T: helpers.chainFromId };
  let r = (e) =>
    e.startsWith('0x') || e.startsWith('0X') ? e.toLowerCase() : e;
  let o = (e) => {
      if (!e) return 0;
      let t = Date.parse(e);
      return Number.isFinite(t) ? t : 0;
    },
    s = (e) => {
      let {
        amountHeld: t,
        valueUsd: i,
        pnlUsd: a,
        pnlPercentage: l,
        costBasisUsd: r,
        amountBoughtUsd: n,
        receiptBasisUsd: o,
        realizedPnlUsd: s,
        isExited: d,
      } = e;
      if (null != t || null != a || null != i)
        return {
          amountHeld: t,
          valueUsd: i,
          pnlUsd: a,
          pnlPercentage: l,
          costBasisUsd: r,
          amountBoughtUsd: n,
          receiptBasisUsd: o,
          realizedPnlUsd: s,
          isExited: d,
        };
    },
    d = (e) => void 0 === e.parentMessageId || null === e.parentMessageId,
    c = (e) => {
      let { updates: t, mint: i, calloutId: a } = e;
      return t?.length
        ? t
            .filter(d)
            .map((e) => ({
              id: e.id,
              content: e.content,
              createdAt: o(e.createdAt),
              mint: i,
              calloutId: a,
              likeCount: e.likeCount ?? 0,
              likedByViewer: !1,
              mediaUrl: e.mediaUrl ?? null,
            }))
            .sort(
              (e, t) =>
                (e.createdAt || Number.MAX_SAFE_INTEGER) -
                (t.createdAt || Number.MAX_SAFE_INTEGER),
            )
        : [];
    },
    u = (e) => {
      let { updates: t, updateCount: i } = e,
        a = t ?? [],
        l = a.filter(d).length,
        r = a.length - l;
      return Math.max((i ?? a.length) - r, l);
    };
  return (e) => {
    let d = e.position,
      m = d?.callout;
    if (!d || !m || null === m.calloutId) return null;
    let f = m.thesis?.trim() || void 0,
      p = ((e) => {
        let t;
        if ('quote' !== e.contentKind) return;
        let i = e.quote;
        if (!i || i.reply.tombstone) return;
        let { parent: a, callout: l } = i;
        return (
          (t = a
            ? a.tombstone
              ? { deleted: !0 }
              : {
                  authorName: a.userName?.trim() || void 0,
                  authorAddress: a.walletAddress ?? void 0,
                  text: a.content.trim() || void 0,
                  deleted: !1,
                }
            : l
              ? {
                  authorName: l.userName?.trim() || void 0,
                  authorAddress: l.walletAddress ?? void 0,
                  text: l.callout.thesis?.trim() || void 0,
                  deleted: !1,
                }
              : { deleted: !0 }),
          {
            replyId: i.reply.id,
            content: i.reply.content,
            createdAt: o(i.reply.createdAt),
            quotedContentId: a?.id ?? l?.callout.calloutId ?? null,
            calloutId: l?.callout.calloutId ?? null,
            quoted: t,
          }
        );
      })(d),
      h = s(d),
      b = (0, a.i)(e.followedHolders, d.userId),
      y = (0, n.T)(e.chain_id);
    return {
      key: `cid:${m.calloutId}`,
      calloutId: m.calloutId,
      coinMint: e.coinMint,
      userId: d.walletAddress ?? d.userId,
      authorCcUserId: d.userId,
      multiple: m.multiple ?? 0,
      marketCapUsd: null != m.calledOutAtMcap ? m.calledOutAtMcap : void 0,
      createdAt: o(m.calloutTimestamp),
      coinName: e.coinName ?? void 0,
      coinSymbol: e.symbol ?? void 0,
      coinImage: e.coinImage ?? void 0,
      ...(y ? { coinChain: y } : e.chain ? { coinChain: e.chain } : {}),
      ...(m.chain ? { chain: m.chain } : {}),
      ...(m.perp ? { perp: m.perp } : {}),
      ...(0, i.E)(m),
      ...(null != e.marketCap ? { coinMarketCapUsd: e.marketCap } : {}),
      username: d.userName || void 0,
      xUsername: d.xUsername ?? void 0,
      profileImage: d.profileImage ?? void 0,
      resolvedAvatarDecoration: d.resolvedAvatarDecoration ?? void 0,
      note: f,
      ...(m.mediaUrl ? { mediaUrl: m.mediaUrl } : {}),
      ...(0, t.P)(m),
      updates: c({
        updates: m.updates,
        mint: e.coinMint,
        calloutId: m.calloutId,
      }),
      updateCount: u({ updates: m.updates, updateCount: m.updateCount }),
      ...(h ? { positionPnl: h } : {}),
      ...(b?.holders.length ? { followedHolders: b } : {}),
      ...(p ? { quote: p } : {}),
      ...(e.recommendationId ? { recommendationId: e.recommendationId } : {}),
      ...(null != e.recommendationRank
        ? { recommendationRank: e.recommendationRank }
        : {}),
      positionId: (({ chainSlug: e, holderWallet: t, mint: i }) => {
        let a;
        if (t && i)
          return (
            (a = e ? e.toLowerCase() : (0, l.f)(i) ? 'solana' : 'unknown'),
            `${a}:${r(t)}:${r(i)}`
          );
      })({
        chainSlug: e.chain,
        holderWallet: d.walletAddress ?? d.userId,
        mint: e.coinMint,
      }),
    };
  };
}
function normalizer1(helpers) {
  const t = {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...('boolean' == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...('boolean' == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
    r = { E: helpers.assets },
    l = { i: helpers.excludeAuthor },
    i = { f: helpers.isSolanaMint },
    n = { T: helpers.chainFromId };
  let a = (e) =>
    e.startsWith('0x') || e.startsWith('0X') ? e.toLowerCase() : e;
  let s = (e) => {
      if (!e) return 0;
      let t = Date.parse(e);
      return Number.isFinite(t) ? t : 0;
    },
    o = (e) => {
      let {
        amountHeld: t,
        valueUsd: r,
        pnlUsd: l,
        pnlPercentage: i,
        costBasisUsd: a,
        amountBoughtUsd: n,
        receiptBasisUsd: s,
        realizedPnlUsd: o,
        isExited: d,
      } = e;
      if (null != t || null != l || null != r)
        return {
          amountHeld: t,
          valueUsd: r,
          pnlUsd: l,
          pnlPercentage: i,
          costBasisUsd: a,
          amountBoughtUsd: n,
          receiptBasisUsd: s,
          realizedPnlUsd: o,
          isExited: d,
        };
    },
    d = (e) => void 0 === e.parentMessageId || null === e.parentMessageId,
    u = (e) => {
      let { updates: t, mint: r, calloutId: l } = e;
      return t?.length
        ? t
            .filter(d)
            .map((e) => ({
              id: e.id,
              content: e.content,
              createdAt: s(e.createdAt),
              mint: r,
              calloutId: l,
              likeCount: e.likeCount ?? 0,
              likedByViewer: !1,
              mediaUrl: e.mediaUrl ?? null,
            }))
            .sort(
              (e, t) =>
                (e.createdAt || Number.MAX_SAFE_INTEGER) -
                (t.createdAt || Number.MAX_SAFE_INTEGER),
            )
        : [];
    },
    c = (e) => {
      let { updates: t, updateCount: r } = e,
        l = t ?? [],
        i = l.filter(d).length,
        a = l.length - i;
      return Math.max((r ?? l.length) - a, i);
    };
  return (e) => {
    let d = e.position,
      m = d?.callout;
    if (!d || !m || null === m.calloutId) return null;
    let p = m.thesis?.trim() || void 0,
      h = ((e) => {
        let t;
        if ('quote' !== e.contentKind) return;
        let r = e.quote;
        if (!r || r.reply.tombstone) return;
        let { parent: l, callout: i } = r;
        return (
          (t = l
            ? l.tombstone
              ? { deleted: !0 }
              : {
                  authorName: l.userName?.trim() || void 0,
                  authorAddress: l.walletAddress ?? void 0,
                  text: l.content.trim() || void 0,
                  deleted: !1,
                }
            : i
              ? {
                  authorName: i.userName?.trim() || void 0,
                  authorAddress: i.walletAddress ?? void 0,
                  text: i.callout.thesis?.trim() || void 0,
                  deleted: !1,
                }
              : { deleted: !0 }),
          {
            replyId: r.reply.id,
            content: r.reply.content,
            createdAt: s(r.reply.createdAt),
            quotedContentId: l?.id ?? i?.callout.calloutId ?? null,
            calloutId: i?.callout.calloutId ?? null,
            quoted: t,
          }
        );
      })(d),
      f = o(d),
      g = (0, l.i)(e.followedHolders, d.userId),
      y = (0, n.T)(e.chain_id);
    return {
      key: `cid:${m.calloutId}`,
      calloutId: m.calloutId,
      coinMint: e.coinMint,
      userId: d.walletAddress ?? d.userId,
      authorCcUserId: d.userId,
      multiple: m.multiple ?? 0,
      marketCapUsd: null != m.calledOutAtMcap ? m.calledOutAtMcap : void 0,
      createdAt: s(m.calloutTimestamp),
      coinName: e.coinName ?? void 0,
      coinSymbol: e.symbol ?? void 0,
      coinImage: e.coinImage ?? void 0,
      ...(y ? { coinChain: y } : e.chain ? { coinChain: e.chain } : {}),
      ...(m.chain ? { chain: m.chain } : {}),
      ...(m.perp ? { perp: m.perp } : {}),
      ...(0, r.E)(m),
      ...(null != e.marketCap ? { coinMarketCapUsd: e.marketCap } : {}),
      username: d.userName || void 0,
      xUsername: d.xUsername ?? void 0,
      profileImage: d.profileImage ?? void 0,
      resolvedAvatarDecoration: d.resolvedAvatarDecoration ?? void 0,
      note: p,
      ...(m.mediaUrl ? { mediaUrl: m.mediaUrl } : {}),
      ...(0, t.P)(m),
      updates: u({
        updates: m.updates,
        mint: e.coinMint,
        calloutId: m.calloutId,
      }),
      updateCount: c({ updates: m.updates, updateCount: m.updateCount }),
      ...(f ? { positionPnl: f } : {}),
      ...(g?.holders.length ? { followedHolders: g } : {}),
      ...(h ? { quote: h } : {}),
      ...(e.recommendationId ? { recommendationId: e.recommendationId } : {}),
      ...(null != e.recommendationRank
        ? { recommendationRank: e.recommendationRank }
        : {}),
      positionId: (({ chainSlug: e, holderWallet: t, mint: r }) => {
        let l;
        if (t && r)
          return (
            (l = e ? e.toLowerCase() : (0, i.f)(r) ? 'solana' : 'unknown'),
            `${l}:${a(t)}:${a(r)}`
          );
      })({
        chainSlug: e.chain,
        holderWallet: d.walletAddress ?? d.userId,
        mint: e.coinMint,
      }),
    };
  };
}
function normalizer2(helpers) {
  const t = {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...('boolean' == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...('boolean' == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
    r = { E: helpers.assets },
    i = { i: helpers.excludeAuthor },
    l = { f: helpers.isSolanaMint },
    a = { T: helpers.chainFromId };
  let n = (e) =>
    e.startsWith('0x') || e.startsWith('0X') ? e.toLowerCase() : e;
  let s = (e) => {
      if (!e) return 0;
      let t = Date.parse(e);
      return Number.isFinite(t) ? t : 0;
    },
    o = (e) => {
      let {
        amountHeld: t,
        valueUsd: r,
        pnlUsd: i,
        pnlPercentage: l,
        costBasisUsd: n,
        amountBoughtUsd: a,
        receiptBasisUsd: s,
        realizedPnlUsd: o,
        isExited: d,
      } = e;
      if (null != t || null != i || null != r)
        return {
          amountHeld: t,
          valueUsd: r,
          pnlUsd: i,
          pnlPercentage: l,
          costBasisUsd: n,
          amountBoughtUsd: a,
          receiptBasisUsd: s,
          realizedPnlUsd: o,
          isExited: d,
        };
    },
    d = (e) => void 0 === e.parentMessageId || null === e.parentMessageId,
    c = (e) => {
      let { updates: t, mint: r, calloutId: i } = e;
      return t?.length
        ? t
            .filter(d)
            .map((e) => ({
              id: e.id,
              content: e.content,
              createdAt: s(e.createdAt),
              mint: r,
              calloutId: i,
              likeCount: e.likeCount ?? 0,
              likedByViewer: !1,
              mediaUrl: e.mediaUrl ?? null,
            }))
            .sort(
              (e, t) =>
                (e.createdAt || Number.MAX_SAFE_INTEGER) -
                (t.createdAt || Number.MAX_SAFE_INTEGER),
            )
        : [];
    },
    u = (e) => {
      let { updates: t, updateCount: r } = e,
        i = t ?? [],
        l = i.filter(d).length,
        n = i.length - l;
      return Math.max((r ?? i.length) - n, l);
    };
  return (e) => {
    let d = e.position,
      m = d?.callout;
    if (!d || !m || null === m.calloutId) return null;
    let h = m.thesis?.trim() || void 0,
      f = ((e) => {
        let t;
        if ('quote' !== e.contentKind) return;
        let r = e.quote;
        if (!r || r.reply.tombstone) return;
        let { parent: i, callout: l } = r;
        return (
          (t = i
            ? i.tombstone
              ? { deleted: !0 }
              : {
                  authorName: i.userName?.trim() || void 0,
                  authorAddress: i.walletAddress ?? void 0,
                  text: i.content.trim() || void 0,
                  deleted: !1,
                }
            : l
              ? {
                  authorName: l.userName?.trim() || void 0,
                  authorAddress: l.walletAddress ?? void 0,
                  text: l.callout.thesis?.trim() || void 0,
                  deleted: !1,
                }
              : { deleted: !0 }),
          {
            replyId: r.reply.id,
            content: r.reply.content,
            createdAt: s(r.reply.createdAt),
            quotedContentId: i?.id ?? l?.callout.calloutId ?? null,
            calloutId: l?.callout.calloutId ?? null,
            quoted: t,
          }
        );
      })(d),
      x = o(d),
      p = (0, i.i)(e.followedHolders, d.userId),
      y = (0, a.T)(e.chain_id);
    return {
      key: `cid:${m.calloutId}`,
      calloutId: m.calloutId,
      coinMint: e.coinMint,
      userId: d.walletAddress ?? d.userId,
      authorCcUserId: d.userId,
      multiple: m.multiple ?? 0,
      marketCapUsd: null != m.calledOutAtMcap ? m.calledOutAtMcap : void 0,
      createdAt: s(m.calloutTimestamp),
      coinName: e.coinName ?? void 0,
      coinSymbol: e.symbol ?? void 0,
      coinImage: e.coinImage ?? void 0,
      ...(y ? { coinChain: y } : e.chain ? { coinChain: e.chain } : {}),
      ...(m.chain ? { chain: m.chain } : {}),
      ...(m.perp ? { perp: m.perp } : {}),
      ...(0, r.E)(m),
      ...(null != e.marketCap ? { coinMarketCapUsd: e.marketCap } : {}),
      username: d.userName || void 0,
      xUsername: d.xUsername ?? void 0,
      profileImage: d.profileImage ?? void 0,
      resolvedAvatarDecoration: d.resolvedAvatarDecoration ?? void 0,
      note: h,
      ...(m.mediaUrl ? { mediaUrl: m.mediaUrl } : {}),
      ...(0, t.P)(m),
      updates: c({
        updates: m.updates,
        mint: e.coinMint,
        calloutId: m.calloutId,
      }),
      updateCount: u({ updates: m.updates, updateCount: m.updateCount }),
      ...(x ? { positionPnl: x } : {}),
      ...(p?.holders.length ? { followedHolders: p } : {}),
      ...(f ? { quote: f } : {}),
      ...(e.recommendationId ? { recommendationId: e.recommendationId } : {}),
      ...(null != e.recommendationRank
        ? { recommendationRank: e.recommendationRank }
        : {}),
      positionId: (({ chainSlug: e, holderWallet: t, mint: r }) => {
        let i;
        if (t && r)
          return (
            (i = e ? e.toLowerCase() : (0, l.f)(r) ? 'solana' : 'unknown'),
            `${i}:${n(t)}:${n(r)}`
          );
      })({
        chainSlug: e.chain,
        holderWallet: d.walletAddress ?? d.userId,
        mint: e.coinMint,
      }),
    };
  };
}
function normalizer3(helpers) {
  const t = {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...('boolean' == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...('boolean' == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
    r = { E: helpers.assets },
    i = { i: helpers.excludeAuthor },
    l = { f: helpers.isSolanaMint },
    n = { T: helpers.chainFromId };
  let a = (e) =>
    e.startsWith('0x') || e.startsWith('0X') ? e.toLowerCase() : e;
  let o = (e) => {
      if (!e) return 0;
      let t = Date.parse(e);
      return Number.isFinite(t) ? t : 0;
    },
    s = (e) => {
      let {
        amountHeld: t,
        valueUsd: r,
        pnlUsd: i,
        pnlPercentage: l,
        costBasisUsd: a,
        amountBoughtUsd: n,
        receiptBasisUsd: o,
        realizedPnlUsd: s,
        isExited: c,
      } = e;
      if (null != t || null != i || null != r)
        return {
          amountHeld: t,
          valueUsd: r,
          pnlUsd: i,
          pnlPercentage: l,
          costBasisUsd: a,
          amountBoughtUsd: n,
          receiptBasisUsd: o,
          realizedPnlUsd: s,
          isExited: c,
        };
    },
    c = (e) => void 0 === e.parentMessageId || null === e.parentMessageId,
    d = (e) => {
      let { updates: t, mint: r, calloutId: i } = e;
      return t?.length
        ? t
            .filter(c)
            .map((e) => ({
              id: e.id,
              content: e.content,
              createdAt: o(e.createdAt),
              mint: r,
              calloutId: i,
              likeCount: e.likeCount ?? 0,
              likedByViewer: !1,
              mediaUrl: e.mediaUrl ?? null,
            }))
            .sort(
              (e, t) =>
                (e.createdAt || Number.MAX_SAFE_INTEGER) -
                (t.createdAt || Number.MAX_SAFE_INTEGER),
            )
        : [];
    },
    u = (e) => {
      let { updates: t, updateCount: r } = e,
        i = t ?? [],
        l = i.filter(c).length,
        a = i.length - l;
      return Math.max((r ?? i.length) - a, l);
    };
  return (e) => {
    let c = e.position,
      m = c?.callout;
    if (!c || !m || null === m.calloutId) return null;
    let p = m.thesis?.trim() || void 0,
      h = ((e) => {
        let t;
        if ('quote' !== e.contentKind) return;
        let r = e.quote;
        if (!r || r.reply.tombstone) return;
        let { parent: i, callout: l } = r;
        return (
          (t = i
            ? i.tombstone
              ? { deleted: !0 }
              : {
                  authorName: i.userName?.trim() || void 0,
                  authorAddress: i.walletAddress ?? void 0,
                  text: i.content.trim() || void 0,
                  deleted: !1,
                }
            : l
              ? {
                  authorName: l.userName?.trim() || void 0,
                  authorAddress: l.walletAddress ?? void 0,
                  text: l.callout.thesis?.trim() || void 0,
                  deleted: !1,
                }
              : { deleted: !0 }),
          {
            replyId: r.reply.id,
            content: r.reply.content,
            createdAt: o(r.reply.createdAt),
            quotedContentId: i?.id ?? l?.callout.calloutId ?? null,
            calloutId: l?.callout.calloutId ?? null,
            quoted: t,
          }
        );
      })(c),
      f = s(c),
      y = (0, i.i)(e.followedHolders, c.userId),
      b = (0, n.T)(e.chain_id);
    return {
      key: `cid:${m.calloutId}`,
      calloutId: m.calloutId,
      coinMint: e.coinMint,
      userId: c.walletAddress ?? c.userId,
      authorCcUserId: c.userId,
      multiple: m.multiple ?? 0,
      marketCapUsd: null != m.calledOutAtMcap ? m.calledOutAtMcap : void 0,
      createdAt: o(m.calloutTimestamp),
      coinName: e.coinName ?? void 0,
      coinSymbol: e.symbol ?? void 0,
      coinImage: e.coinImage ?? void 0,
      ...(b ? { coinChain: b } : e.chain ? { coinChain: e.chain } : {}),
      ...(m.chain ? { chain: m.chain } : {}),
      ...(m.perp ? { perp: m.perp } : {}),
      ...(0, r.E)(m),
      ...(null != e.marketCap ? { coinMarketCapUsd: e.marketCap } : {}),
      username: c.userName || void 0,
      xUsername: c.xUsername ?? void 0,
      profileImage: c.profileImage ?? void 0,
      resolvedAvatarDecoration: c.resolvedAvatarDecoration ?? void 0,
      note: p,
      ...(m.mediaUrl ? { mediaUrl: m.mediaUrl } : {}),
      ...(0, t.P)(m),
      updates: d({
        updates: m.updates,
        mint: e.coinMint,
        calloutId: m.calloutId,
      }),
      updateCount: u({ updates: m.updates, updateCount: m.updateCount }),
      ...(f ? { positionPnl: f } : {}),
      ...(y?.holders.length ? { followedHolders: y } : {}),
      ...(h ? { quote: h } : {}),
      ...(e.recommendationId ? { recommendationId: e.recommendationId } : {}),
      ...(null != e.recommendationRank
        ? { recommendationRank: e.recommendationRank }
        : {}),
      positionId: (({ chainSlug: e, holderWallet: t, mint: r }) => {
        let i;
        if (t && r)
          return (
            (i = e ? e.toLowerCase() : (0, l.f)(r) ? 'solana' : 'unknown'),
            `${i}:${a(t)}:${a(r)}`
          );
      })({
        chainSlug: e.chain,
        holderWallet: c.walletAddress ?? c.userId,
        mint: e.coinMint,
      }),
    };
  };
}
function normalizer4(helpers) {
  const t = {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...('boolean' == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...('boolean' == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
    r = { E: helpers.assets },
    l = { i: helpers.excludeAuthor },
    o = { f: helpers.isSolanaMint },
    a = { T: helpers.chainFromId };
  let i = (e) =>
    e.startsWith('0x') || e.startsWith('0X') ? e.toLowerCase() : e;
  let n = (e) => {
      if (!e) return 0;
      let t = Date.parse(e);
      return Number.isFinite(t) ? t : 0;
    },
    s = (e) => {
      let {
        amountHeld: t,
        valueUsd: r,
        pnlUsd: l,
        pnlPercentage: o,
        costBasisUsd: i,
        amountBoughtUsd: a,
        receiptBasisUsd: n,
        realizedPnlUsd: s,
        isExited: c,
      } = e;
      if (null != t || null != l || null != r)
        return {
          amountHeld: t,
          valueUsd: r,
          pnlUsd: l,
          pnlPercentage: o,
          costBasisUsd: i,
          amountBoughtUsd: a,
          receiptBasisUsd: n,
          realizedPnlUsd: s,
          isExited: c,
        };
    },
    c = (e) => void 0 === e.parentMessageId || null === e.parentMessageId,
    d = (e) => {
      let { updates: t, mint: r, calloutId: l } = e;
      return t?.length
        ? t
            .filter(c)
            .map((e) => ({
              id: e.id,
              content: e.content,
              createdAt: n(e.createdAt),
              mint: r,
              calloutId: l,
              likeCount: e.likeCount ?? 0,
              likedByViewer: !1,
              mediaUrl: e.mediaUrl ?? null,
            }))
            .sort(
              (e, t) =>
                (e.createdAt || Number.MAX_SAFE_INTEGER) -
                (t.createdAt || Number.MAX_SAFE_INTEGER),
            )
        : [];
    },
    u = (e) => {
      let { updates: t, updateCount: r } = e,
        l = t ?? [],
        o = l.filter(c).length,
        i = l.length - o;
      return Math.max((r ?? l.length) - i, o);
    };
  return (e) => {
    let c = e.position,
      m = c?.callout;
    if (!c || !m || null === m.calloutId) return null;
    let p = m.thesis?.trim() || void 0,
      b = ((e) => {
        let t;
        if ('quote' !== e.contentKind) return;
        let r = e.quote;
        if (!r || r.reply.tombstone) return;
        let { parent: l, callout: o } = r;
        return (
          (t = l
            ? l.tombstone
              ? { deleted: !0 }
              : {
                  authorName: l.userName?.trim() || void 0,
                  authorAddress: l.walletAddress ?? void 0,
                  text: l.content.trim() || void 0,
                  deleted: !1,
                }
            : o
              ? {
                  authorName: o.userName?.trim() || void 0,
                  authorAddress: o.walletAddress ?? void 0,
                  text: o.callout.thesis?.trim() || void 0,
                  deleted: !1,
                }
              : { deleted: !0 }),
          {
            replyId: r.reply.id,
            content: r.reply.content,
            createdAt: n(r.reply.createdAt),
            quotedContentId: l?.id ?? o?.callout.calloutId ?? null,
            calloutId: o?.callout.calloutId ?? null,
            quoted: t,
          }
        );
      })(c),
      h = s(c),
      y = (0, l.i)(e.followedHolders, c.userId),
      f = (0, a.T)(e.chain_id);
    return {
      key: `cid:${m.calloutId}`,
      calloutId: m.calloutId,
      coinMint: e.coinMint,
      userId: c.walletAddress ?? c.userId,
      authorCcUserId: c.userId,
      multiple: m.multiple ?? 0,
      marketCapUsd: null != m.calledOutAtMcap ? m.calledOutAtMcap : void 0,
      createdAt: n(m.calloutTimestamp),
      coinName: e.coinName ?? void 0,
      coinSymbol: e.symbol ?? void 0,
      coinImage: e.coinImage ?? void 0,
      ...(f ? { coinChain: f } : e.chain ? { coinChain: e.chain } : {}),
      ...(m.chain ? { chain: m.chain } : {}),
      ...(m.perp ? { perp: m.perp } : {}),
      ...(0, r.E)(m),
      ...(null != e.marketCap ? { coinMarketCapUsd: e.marketCap } : {}),
      username: c.userName || void 0,
      xUsername: c.xUsername ?? void 0,
      profileImage: c.profileImage ?? void 0,
      resolvedAvatarDecoration: c.resolvedAvatarDecoration ?? void 0,
      note: p,
      ...(m.mediaUrl ? { mediaUrl: m.mediaUrl } : {}),
      ...(0, t.P)(m),
      updates: d({
        updates: m.updates,
        mint: e.coinMint,
        calloutId: m.calloutId,
      }),
      updateCount: u({ updates: m.updates, updateCount: m.updateCount }),
      ...(h ? { positionPnl: h } : {}),
      ...(y?.holders.length ? { followedHolders: y } : {}),
      ...(b ? { quote: b } : {}),
      ...(e.recommendationId ? { recommendationId: e.recommendationId } : {}),
      ...(null != e.recommendationRank
        ? { recommendationRank: e.recommendationRank }
        : {}),
      positionId: (({ chainSlug: e, holderWallet: t, mint: r }) => {
        let l;
        if (t && r)
          return (
            (l = e ? e.toLowerCase() : (0, o.f)(r) ? 'solana' : 'unknown'),
            `${l}:${i(t)}:${i(r)}`
          );
      })({
        chainSlug: e.chain,
        holderWallet: c.walletAddress ?? c.userId,
        mint: e.coinMint,
      }),
    };
  };
}
function normalizer5(helpers) {
  const t = {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...('boolean' == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...('boolean' == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
    i = { E: helpers.assets },
    l = { i: helpers.excludeAuthor },
    r = { f: helpers.isSolanaMint },
    n = { T: helpers.chainFromId };
  let a = (e) =>
    e.startsWith('0x') || e.startsWith('0X') ? e.toLowerCase() : e;
  let o = (e) => {
      if (!e) return 0;
      let t = Date.parse(e);
      return Number.isFinite(t) ? t : 0;
    },
    s = (e) => {
      let {
        amountHeld: t,
        valueUsd: i,
        pnlUsd: l,
        pnlPercentage: r,
        costBasisUsd: a,
        amountBoughtUsd: n,
        receiptBasisUsd: o,
        realizedPnlUsd: s,
        isExited: d,
      } = e;
      if (null != t || null != l || null != i)
        return {
          amountHeld: t,
          valueUsd: i,
          pnlUsd: l,
          pnlPercentage: r,
          costBasisUsd: a,
          amountBoughtUsd: n,
          receiptBasisUsd: o,
          realizedPnlUsd: s,
          isExited: d,
        };
    },
    d = (e) => void 0 === e.parentMessageId || null === e.parentMessageId,
    c = (e) => {
      let { updates: t, mint: i, calloutId: l } = e;
      return t?.length
        ? t
            .filter(d)
            .map((e) => ({
              id: e.id,
              content: e.content,
              createdAt: o(e.createdAt),
              mint: i,
              calloutId: l,
              likeCount: e.likeCount ?? 0,
              likedByViewer: !1,
              mediaUrl: e.mediaUrl ?? null,
            }))
            .sort(
              (e, t) =>
                (e.createdAt || Number.MAX_SAFE_INTEGER) -
                (t.createdAt || Number.MAX_SAFE_INTEGER),
            )
        : [];
    },
    u = (e) => {
      let { updates: t, updateCount: i } = e,
        l = t ?? [],
        r = l.filter(d).length,
        a = l.length - r;
      return Math.max((i ?? l.length) - a, r);
    };
  return (e) => {
    let d = e.position,
      m = d?.callout;
    if (!d || !m || null === m.calloutId) return null;
    let f = m.thesis?.trim() || void 0,
      y = ((e) => {
        let t;
        if ('quote' !== e.contentKind) return;
        let i = e.quote;
        if (!i || i.reply.tombstone) return;
        let { parent: l, callout: r } = i;
        return (
          (t = l
            ? l.tombstone
              ? { deleted: !0 }
              : {
                  authorName: l.userName?.trim() || void 0,
                  authorAddress: l.walletAddress ?? void 0,
                  text: l.content.trim() || void 0,
                  deleted: !1,
                }
            : r
              ? {
                  authorName: r.userName?.trim() || void 0,
                  authorAddress: r.walletAddress ?? void 0,
                  text: r.callout.thesis?.trim() || void 0,
                  deleted: !1,
                }
              : { deleted: !0 }),
          {
            replyId: i.reply.id,
            content: i.reply.content,
            createdAt: o(i.reply.createdAt),
            quotedContentId: l?.id ?? r?.callout.calloutId ?? null,
            calloutId: r?.callout.calloutId ?? null,
            quoted: t,
          }
        );
      })(d),
      h = s(d),
      p = (0, l.i)(e.followedHolders, d.userId),
      x = (0, n.T)(e.chain_id);
    return {
      key: `cid:${m.calloutId}`,
      calloutId: m.calloutId,
      coinMint: e.coinMint,
      userId: d.walletAddress ?? d.userId,
      authorCcUserId: d.userId,
      multiple: m.multiple ?? 0,
      marketCapUsd: null != m.calledOutAtMcap ? m.calledOutAtMcap : void 0,
      createdAt: o(m.calloutTimestamp),
      coinName: e.coinName ?? void 0,
      coinSymbol: e.symbol ?? void 0,
      coinImage: e.coinImage ?? void 0,
      ...(x ? { coinChain: x } : e.chain ? { coinChain: e.chain } : {}),
      ...(m.chain ? { chain: m.chain } : {}),
      ...(m.perp ? { perp: m.perp } : {}),
      ...(0, i.E)(m),
      ...(null != e.marketCap ? { coinMarketCapUsd: e.marketCap } : {}),
      username: d.userName || void 0,
      xUsername: d.xUsername ?? void 0,
      profileImage: d.profileImage ?? void 0,
      resolvedAvatarDecoration: d.resolvedAvatarDecoration ?? void 0,
      note: f,
      ...(m.mediaUrl ? { mediaUrl: m.mediaUrl } : {}),
      ...(0, t.P)(m),
      updates: c({
        updates: m.updates,
        mint: e.coinMint,
        calloutId: m.calloutId,
      }),
      updateCount: u({ updates: m.updates, updateCount: m.updateCount }),
      ...(h ? { positionPnl: h } : {}),
      ...(p?.holders.length ? { followedHolders: p } : {}),
      ...(y ? { quote: y } : {}),
      ...(e.recommendationId ? { recommendationId: e.recommendationId } : {}),
      ...(null != e.recommendationRank
        ? { recommendationRank: e.recommendationRank }
        : {}),
      positionId: (({ chainSlug: e, holderWallet: t, mint: i }) => {
        let l;
        if (t && i)
          return (
            (l = e ? e.toLowerCase() : (0, r.f)(i) ? 'solana' : 'unknown'),
            `${l}:${a(t)}:${a(i)}`
          );
      })({
        chainSlug: e.chain,
        holderWallet: d.walletAddress ?? d.userId,
        mint: e.coinMint,
      }),
    };
  };
}
const helpersByContext = new Map([
  ['evidence/web/objects/3740fc4e7a24596d.js', helpers0],
  ['evidence/web/objects/cf2bb278631744da.js', helpers1],
]);
const normalizers = new Map([
  [
    '7fb1990b807291b37cfd559db80e1d428cea58bfa9007bd6e823f78785a43c7f',
    normalizer0,
  ],
  [
    '960ab98a1f113c07b8a86ad009f505faaadc056a45f4a07d9ae86baf0aca0310',
    normalizer1,
  ],
  [
    '70a717bf9bc6bf6a0f33a8d910030e7eb13df2348e96b805af3d43b58dab86ec',
    normalizer2,
  ],
  [
    'c40d7f92b3999c9387da21f01eca0802a91204b49bddbe6fa41088133d5425c8',
    normalizer3,
  ],
  [
    '45e56c6c56b6ebc80d4b1979b3ef6bd3c83ecf5aed7b773183e164311ae892dd',
    normalizer4,
  ],
  [
    'b7754f3a78d17d64d1df27ef1649d16e623c6e16fc3e0b2b4edbe3386550aad4',
    normalizer5,
  ],
]);
export const normalizerVariants = Object.freeze([
  {
    sha256: '7fb1990b807291b37cfd559db80e1d428cea58bfa9007bd6e823f78785a43c7f',
    source: 'evidence/web/objects/2d59b7c63a95235e.js',
    metrics: 'ed70f0477b2463c917640da04af8eb3a94830fa4da63e0f1caf9bcdfe0cb6581',
  },
  {
    sha256: '960ab98a1f113c07b8a86ad009f505faaadc056a45f4a07d9ae86baf0aca0310',
    source: 'evidence/web/objects/c3601a995a6b7f37.js',
    metrics: 'd2e1e635c3aa80d582ec16b7d4ca1097022e69062ff4c02777ac71ae09f8ce96',
  },
  {
    sha256: '70a717bf9bc6bf6a0f33a8d910030e7eb13df2348e96b805af3d43b58dab86ec',
    source: 'evidence/web/objects/57624d7eddba52e1.js',
    metrics: 'd2e1e635c3aa80d582ec16b7d4ca1097022e69062ff4c02777ac71ae09f8ce96',
  },
  {
    sha256: 'c40d7f92b3999c9387da21f01eca0802a91204b49bddbe6fa41088133d5425c8',
    source: 'evidence/web/objects/0e0a55c249b456d7.js',
    metrics: 'd2e1e635c3aa80d582ec16b7d4ca1097022e69062ff4c02777ac71ae09f8ce96',
  },
  {
    sha256: '45e56c6c56b6ebc80d4b1979b3ef6bd3c83ecf5aed7b773183e164311ae892dd',
    source: 'evidence/web/objects/082b15d8e8570a9a.js',
    metrics: 'd2e1e635c3aa80d582ec16b7d4ca1097022e69062ff4c02777ac71ae09f8ce96',
  },
  {
    sha256: 'b7754f3a78d17d64d1df27ef1649d16e623c6e16fc3e0b2b4edbe3386550aad4',
    source: 'evidence/web/objects/1681353d046eeca6.js',
    metrics: 'ed70f0477b2463c917640da04af8eb3a94830fa4da63e0f1caf9bcdfe0cb6581',
  },
]);
export const helperContexts = Object.freeze([
  'evidence/web/objects/3740fc4e7a24596d.js',
  'evidence/web/objects/cf2bb278631744da.js',
]);
export function createHomeFeedRead({
  normalizerVariant,
  helperContext,
  React,
  useMemoCache,
  useQuery,
  useHomeFeedSeed,
  fetchHomeFeed,
  decodeBase58,
  timers = globalThis,
}) {
  const createHelpers = helpersByContext.get(helperContext),
    createNormalizer = normalizers.get(normalizerVariant);
  if (!createHelpers || !createNormalizer)
    throw new TypeError(
      'Explicit reviewed helper context and normalizer variant required',
    );
  for (const capability of [
    useMemoCache,
    useQuery,
    useHomeFeedSeed,
    fetchHomeFeed,
    decodeBase58,
    timers.setInterval,
    timers.clearInterval,
  ])
    if (typeof capability !== 'function')
      throw new TypeError('Missing explicit Home-feed runtime capability');
  const normalizeRow = createNormalizer(createHelpers(decodeBase58));
  const setInterval = timers.setInterval.bind(timers),
    clearInterval = timers.clearInterval.bind(timers);
  const t = { c: useMemoCache },
    n = { useQuery },
    r = React,
    i = { t: 15000, I: 3 },
    l = { c: 150, Z: fetchHomeFeed },
    a = { y: normalizeRow },
    o = { useHomeFeedSeed };
  let s = i.t,
    u = new Set(),
    c = (e) => {
      let {
        pageSize: t,
        chain: n,
        includeFollowedHolders: r,
        viewerAddress: i,
      } = e;
      return {
        queryKey: ['callouts', 'home-feed', n, t, r, i],
        queryFn: ({ signal: e }) =>
          (0, l.Z)({
            pageSize: t,
            chain: n,
            includeFollowedHolders: r,
            viewerAddress: i,
            signal: e,
          }),
        staleTime: s,
        retry: 3,
      };
    };
  function d() {
    return new WeakMap();
  }
  function m(e) {
    return e.key;
  }
  function f(e) {
    return e.key;
  }
  function p(e) {
    return [e.key, e];
  }
  function h(e) {
    return e.key;
  }
  function g(e) {
    return { key: e.key, coinMint: e.coinMint, coinSymbol: e.coinSymbol };
  }
  function y(e) {
    return e.key;
  }
  function v(e) {
    return e.key;
  }
  function b(e) {
    return e.key;
  }
  function w(e) {
    return e.key;
  }
  return {
    normalizeRow,
    prefetchHomeFeed: (e, t = {}) => {
      let {
        pageSize: n = l.c,
        chain: r = 'all',
        includeFollowedHolders: i = !1,
        viewerAddress: a = null,
      } = t;
      return e.prefetchQuery(
        c({
          pageSize: n,
          chain: r,
          includeFollowedHolders: i,
          viewerAddress: a,
        }),
      );
    },
    useHomeFeed: (e) => {
      let s,
        x,
        k,
        M,
        C,
        I,
        S,
        N,
        A,
        j,
        _,
        U,
        E,
        T,
        $,
        R = (0, t.c)(51),
        {
          enabled: D,
          pageSize: F,
          chain: P,
          includeFollowedHolders: B,
          viewerAddress: q,
        } = void 0 === e ? {} : e,
        O = void 0 === D || D,
        z = void 0 === F ? l.c : F,
        W = void 0 === P ? 'all' : P,
        L = void 0 === q ? null : q,
        V = (0, o.useHomeFeedSeed)(),
        [Q] = (0, r.useState)(L),
        G = V?.chain === W && L === Q ? V.response : void 0,
        H = c({
          pageSize: z,
          chain: W,
          includeFollowedHolders: void 0 !== B && B,
          viewerAddress: L,
        });
      R[0] !== O || R[1] !== G || R[2] !== H
        ? ((s = {
            ...H,
            enabled: O,
            placeholderData: G,
            refetchOnWindowFocus: !0,
            refetchInterval: 15e3,
            refetchIntervalInBackground: !1,
          }),
          (R[0] = O),
          (R[1] = G),
          (R[2] = H),
          (R[3] = s))
        : (s = R[3]);
      let K = (0, n.useQuery)(s),
        Z = K.data ?? G,
        [X] = (0, r.useState)(d);
      if (R[4] !== X || R[5] !== Z?.coins) {
        let e = new Set();
        for (let t of ((x = []), Z?.coins ?? [])) {
          let n = X.get(t);
          (void 0 === n && ((n = (0, a.y)(t)), X.set(t, n)),
            !n || e.has(n.key) || (e.add(n.key), x.push(n)));
        }
        ((R[4] = X), (R[5] = Z?.coins), (R[6] = x));
      } else x = R[6];
      let J = x,
        [Y, ee] = (0, r.useState)(null),
        [et, en] = (0, r.useState)(u),
        [er, ei] = (0, r.useState)(0);
      R[7] !== J
        ? ((k = new Set(J.map(m))), (R[7] = J), (R[8] = k))
        : (k = R[8]);
      let el = k,
        [ea, eo] = (0, r.useState)(L);
      (ea !== L && (eo(L), ee(null), ei(0), en(u)),
        J.length > 0 &&
          (null === Y || !Y.some((e) => el.has(e))) &&
          (ee(J.slice(0, 12).map(f)), ei(0)),
        R[9] !== J
          ? ((M = new Map(J.map(p))), (R[9] = J), (R[10] = M))
          : (M = R[10]));
      let es = M;
      if (R[11] !== es || R[12] !== J || R[13] !== Y) {
        let e = Y ?? J.slice(0, 12).map(h);
        for (let t of ((I = new Set()), (C = []), e)) {
          let e = es.get(t);
          !e || I.has(t) || (I.add(t), C.push(e));
        }
        ((R[11] = es), (R[12] = J), (R[13] = Y), (R[14] = C), (R[15] = I));
      } else ((C = R[14]), (I = R[15]));
      if (R[16] !== C || R[17] !== I || R[18] !== J || R[19] !== et) {
        let e = J.filter((e) => !I.has(e.key));
        ((S = {
          callouts: C,
          unseen: e.filter((e) => !et.has(e.key)),
          retiredRows: e.filter((e) => et.has(e.key)),
        }),
          (R[16] = C),
          (R[17] = I),
          (R[18] = J),
          (R[19] = et),
          (R[20] = S));
      } else S = R[20];
      let { callouts: eu, unseen: ec, retiredRows: ed } = S,
        em = (0, r.useRef)(0);
      (R[21] !== ec.length
        ? ((N = () => {
            em.current = ec.length;
          }),
          (A = [ec.length]),
          (R[21] = ec.length),
          (R[22] = N),
          (R[23] = A))
        : ((N = R[22]), (A = R[23])),
        (0, r.useEffect)(N, A));
      let ef = ec.length > 0;
      (R[24] !== O || R[25] !== ef
        ? ((j = () => {
            if (!O || !ef) return;
            let e = setInterval(() => {
              let e = Math.min(em.current, 25);
              ei((t) => (t >= e ? t : t + 1));
            }, 2500);
            return () => clearInterval(e);
          }),
          (_ = [O, ef]),
          (R[24] = O),
          (R[25] = ef),
          (R[26] = j),
          (R[27] = _))
        : ((j = R[26]), (_ = R[27])),
        (0, r.useEffect)(j, _));
      let ep = Math.min(er, ec.length, 25),
        eh = Math.min(ep, i.I);
      R[28] !== eh || R[29] !== ec
        ? ((U = ec.slice(0, eh).map(g)),
          (R[28] = eh),
          (R[29] = ec),
          (R[30] = U))
        : (U = R[30]);
      let eg = U;
      R[31] !== eu ||
      R[32] !== el ||
      R[33] !== er ||
      R[34] !== et ||
      R[35] !== ec
        ? ((E = () => {
            if (0 === ec.length) return;
            let e = Math.max(Math.min(er, ec.length), 1),
              t = ec.slice(0, e).map(y),
              n = eu.map(v),
              r = new Set(t),
              i = [...t, ...n.filter((e) => !r.has(e))];
            (ee(i.slice(0, 40)),
              en(
                new Set([
                  ...Array.from(et).filter((e) => el.has(e)),
                  ...i.slice(40),
                ]),
              ),
              ei(0));
          }),
          (R[31] = eu),
          (R[32] = el),
          (R[33] = er),
          (R[34] = et),
          (R[35] = ec),
          (R[36] = E))
        : (E = R[36]);
      let ey = E;
      R[37] !== eu || R[38] !== ed || R[39] !== ec
        ? ((T = () => {
            let e = (ec.length > 0 ? ec : ed).slice(0, 12);
            if (0 === e.length) return;
            ee([...eu.map(b), ...e.map(w)]);
            let t = Math.max(ec.length - 12, 0);
            ei((e) => Math.min(e, t));
          }),
          (R[37] = eu),
          (R[38] = ed),
          (R[39] = ec),
          (R[40] = T))
        : (T = R[40]);
      let ev = T,
        eb = O && K.isPending && !Z,
        ew =
          K.isError && !Z && 0 === eu.length
            ? 'Could not load the callouts feed'
            : null,
        ex = ec.length > 0 || ed.length > 0,
        ek = ec.length > 0;
      return (
        R[41] !== eu ||
        R[42] !== ev ||
        R[43] !== ep ||
        R[44] !== eg ||
        R[45] !== ey ||
        R[46] !== eb ||
        R[47] !== ew ||
        R[48] !== ex ||
        R[49] !== ek
          ? (($ = {
              callouts: eu,
              isLoadingHistory: eb,
              error: ew,
              pendingNewCount: ep,
              pendingPreview: eg,
              showNewCallouts: ey,
              hasNextPage: ex,
              hasUnseen: ek,
              isFetchingNextPage: !1,
              fetchNextPage: ev,
            }),
            (R[41] = eu),
            (R[42] = ev),
            (R[43] = ep),
            (R[44] = eg),
            (R[45] = ey),
            (R[46] = eb),
            (R[47] = ew),
            (R[48] = ex),
            (R[49] = ek),
            (R[50] = $))
          : ($ = R[50]),
        $
      );
    },
  };
}
