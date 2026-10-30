// Source-bound reuse of already-recovered1846 helpers ONLY for qualification. Runtime client requires the original namespace capability.
export const helperVariants = [
  {
    source: "evidence/web/objects/2d59b7c63a95235e.js",
    sha256: "7fb1990b807291b37cfd559db80e1d428cea58bfa9007bd6e823f78785a43c7f",
  },
  {
    source: "evidence/web/objects/c3601a995a6b7f37.js",
    sha256: "960ab98a1f113c07b8a86ad009f505faaadc056a45f4a07d9ae86baf0aca0310",
  },
  {
    source: "evidence/web/objects/57624d7eddba52e1.js",
    sha256: "70a717bf9bc6bf6a0f33a8d910030e7eb13df2348e96b805af3d43b58dab86ec",
  },
  {
    source: "evidence/web/objects/0e0a55c249b456d7.js",
    sha256: "c40d7f92b3999c9387da21f01eca0802a91204b49bddbe6fa41088133d5425c8",
  },
  {
    source: "evidence/web/objects/082b15d8e8570a9a.js",
    sha256: "45e56c6c56b6ebc80d4b1979b3ef6bd3c83ecf5aed7b773183e164311ae892dd",
  },
  {
    source: "evidence/web/objects/1681353d046eeca6.js",
    sha256: "b7754f3a78d17d64d1df27ef1649d16e623c6e16fc3e0b2b4edbe3386550aad4",
  },
];
function helpers0() {
  let o = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
  };
  let s = (e) => {
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
  };
  let d = (e) => void 0 === e.parentMessageId || null === e.parentMessageId;
  let c = (e) => {
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
  };
  let u = (e) => {
    let { updates: t, updateCount: i } = e,
      a = t ?? [],
      l = a.filter(d).length,
      r = a.length - l;
    return Math.max((i ?? a.length) - r, l);
  };
  return {
    g: (e) => {
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
    v: (e) => {
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
    s: (e) => {
      let { updates: t, updateCount: i } = e,
        a = t ?? [],
        l = a.filter(d).length,
        r = a.length - l;
      return Math.max((i ?? a.length) - r, l);
    },
  };
}
function helpers1() {
  let s = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
  };
  let o = (e) => {
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
  };
  let d = (e) => void 0 === e.parentMessageId || null === e.parentMessageId;
  let u = (e) => {
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
  };
  let c = (e) => {
    let { updates: t, updateCount: r } = e,
      l = t ?? [],
      i = l.filter(d).length,
      a = l.length - i;
    return Math.max((r ?? l.length) - a, i);
  };
  return {
    g: (e) => {
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
    v: (e) => {
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
    s: (e) => {
      let { updates: t, updateCount: r } = e,
        l = t ?? [],
        i = l.filter(d).length,
        a = l.length - i;
      return Math.max((r ?? l.length) - a, i);
    },
  };
}
function helpers2() {
  let s = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
  };
  let o = (e) => {
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
  };
  let d = (e) => void 0 === e.parentMessageId || null === e.parentMessageId;
  let c = (e) => {
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
  };
  let u = (e) => {
    let { updates: t, updateCount: r } = e,
      i = t ?? [],
      l = i.filter(d).length,
      n = i.length - l;
    return Math.max((r ?? i.length) - n, l);
  };
  return {
    g: (e) => {
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
    v: (e) => {
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
    s: (e) => {
      let { updates: t, updateCount: r } = e,
        i = t ?? [],
        l = i.filter(d).length,
        n = i.length - l;
      return Math.max((r ?? i.length) - n, l);
    },
  };
}
function helpers3() {
  let o = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
  };
  let s = (e) => {
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
  };
  let c = (e) => void 0 === e.parentMessageId || null === e.parentMessageId;
  let d = (e) => {
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
  };
  let u = (e) => {
    let { updates: t, updateCount: r } = e,
      i = t ?? [],
      l = i.filter(c).length,
      a = i.length - l;
    return Math.max((r ?? i.length) - a, l);
  };
  return {
    g: (e) => {
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
    v: (e) => {
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
    s: (e) => {
      let { updates: t, updateCount: r } = e,
        i = t ?? [],
        l = i.filter(c).length,
        a = i.length - l;
      return Math.max((r ?? i.length) - a, l);
    },
  };
}
function helpers4() {
  let n = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
  };
  let s = (e) => {
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
  };
  let c = (e) => void 0 === e.parentMessageId || null === e.parentMessageId;
  let d = (e) => {
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
  };
  let u = (e) => {
    let { updates: t, updateCount: r } = e,
      l = t ?? [],
      o = l.filter(c).length,
      i = l.length - o;
    return Math.max((r ?? l.length) - i, o);
  };
  return {
    g: (e) => {
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
    v: (e) => {
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
    s: (e) => {
      let { updates: t, updateCount: r } = e,
        l = t ?? [],
        o = l.filter(c).length,
        i = l.length - o;
      return Math.max((r ?? l.length) - i, o);
    },
  };
}
function helpers5() {
  let o = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
  };
  let s = (e) => {
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
  };
  let d = (e) => void 0 === e.parentMessageId || null === e.parentMessageId;
  let c = (e) => {
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
  };
  let u = (e) => {
    let { updates: t, updateCount: i } = e,
      l = t ?? [],
      r = l.filter(d).length,
      a = l.length - r;
    return Math.max((i ?? l.length) - a, r);
  };
  return {
    g: (e) => {
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
    v: (e) => {
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
    s: (e) => {
      let { updates: t, updateCount: i } = e,
        l = t ?? [],
        r = l.filter(d).length,
        a = l.length - r;
      return Math.max((i ?? l.length) - a, r);
    },
  };
}
export function createNormalizerHelpers(variant) {
  const table = {
    "7fb1990b807291b37cfd559db80e1d428cea58bfa9007bd6e823f78785a43c7f":
      helpers0,
    "960ab98a1f113c07b8a86ad009f505faaadc056a45f4a07d9ae86baf0aca0310":
      helpers1,
    "70a717bf9bc6bf6a0f33a8d910030e7eb13df2348e96b805af3d43b58dab86ec":
      helpers2,
    c40d7f92b3999c9387da21f01eca0802a91204b49bddbe6fa41088133d5425c8: helpers3,
    "45e56c6c56b6ebc80d4b1979b3ef6bd3c83ecf5aed7b773183e164311ae892dd":
      helpers4,
    b7754f3a78d17d64d1df27ef1649d16e623c6e16fc3e0b2b4edbe3386550aad4: helpers5,
  };
  if (typeof variant !== "string" || !Object.hasOwn(table, variant))
    throw TypeError("explicit supported1846 helper hash required");
  return table[variant]();
}
