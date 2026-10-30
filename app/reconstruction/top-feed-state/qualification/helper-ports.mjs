// Qualification-only source-bound reuse of prior1846 namespaces; no new helper credit.
export const helperVariants = [
  {
    source: "evidence/web/objects/2d59b7c63a95235e.js",
    normalizer:
      "7fb1990b807291b37cfd559db80e1d428cea58bfa9007bd6e823f78785a43c7f",
    engagement:
      "ed70f0477b2463c917640da04af8eb3a94830fa4da63e0f1caf9bcdfe0cb6581",
  },
  {
    source: "evidence/web/objects/c3601a995a6b7f37.js",
    normalizer:
      "960ab98a1f113c07b8a86ad009f505faaadc056a45f4a07d9ae86baf0aca0310",
    engagement:
      "d2e1e635c3aa80d582ec16b7d4ca1097022e69062ff4c02777ac71ae09f8ce96",
  },
  {
    source: "evidence/web/objects/57624d7eddba52e1.js",
    normalizer:
      "70a717bf9bc6bf6a0f33a8d910030e7eb13df2348e96b805af3d43b58dab86ec",
    engagement:
      "d2e1e635c3aa80d582ec16b7d4ca1097022e69062ff4c02777ac71ae09f8ce96",
  },
  {
    source: "evidence/web/objects/0e0a55c249b456d7.js",
    normalizer:
      "c40d7f92b3999c9387da21f01eca0802a91204b49bddbe6fa41088133d5425c8",
    engagement:
      "d2e1e635c3aa80d582ec16b7d4ca1097022e69062ff4c02777ac71ae09f8ce96",
  },
  {
    source: "evidence/web/objects/082b15d8e8570a9a.js",
    normalizer:
      "45e56c6c56b6ebc80d4b1979b3ef6bd3c83ecf5aed7b773183e164311ae892dd",
    engagement:
      "d2e1e635c3aa80d582ec16b7d4ca1097022e69062ff4c02777ac71ae09f8ce96",
  },
  {
    source: "evidence/web/objects/1681353d046eeca6.js",
    normalizer:
      "b7754f3a78d17d64d1df27ef1649d16e623c6e16fc3e0b2b4edbe3386550aad4",
    engagement:
      "ed70f0477b2463c917640da04af8eb3a94830fa4da63e0f1caf9bcdfe0cb6581",
  },
];
function helpers0() {
  let o = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
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
    normalizerHelpers: {
      l: (e) => {
        if (!e) return 0;
        let t = Date.parse(e);
        return Number.isFinite(t) ? t : 0;
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
    },
    engagementHelpers: {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...("boolean" == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...("boolean" == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
  };
}
function helpers1() {
  let s = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
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
    normalizerHelpers: {
      l: (e) => {
        if (!e) return 0;
        let t = Date.parse(e);
        return Number.isFinite(t) ? t : 0;
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
    },
    engagementHelpers: {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...("boolean" == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...("boolean" == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
  };
}
function helpers2() {
  let s = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
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
    normalizerHelpers: {
      l: (e) => {
        if (!e) return 0;
        let t = Date.parse(e);
        return Number.isFinite(t) ? t : 0;
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
    },
    engagementHelpers: {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...("boolean" == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...("boolean" == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
  };
}
function helpers3() {
  let o = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
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
    normalizerHelpers: {
      l: (e) => {
        if (!e) return 0;
        let t = Date.parse(e);
        return Number.isFinite(t) ? t : 0;
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
    },
    engagementHelpers: {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...("boolean" == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...("boolean" == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
  };
}
function helpers4() {
  let n = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
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
    normalizerHelpers: {
      l: (e) => {
        if (!e) return 0;
        let t = Date.parse(e);
        return Number.isFinite(t) ? t : 0;
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
    },
    engagementHelpers: {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...("boolean" == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...("boolean" == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
  };
}
function helpers5() {
  let o = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
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
    normalizerHelpers: {
      l: (e) => {
        if (!e) return 0;
        let t = Date.parse(e);
        return Number.isFinite(t) ? t : 0;
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
    },
    engagementHelpers: {
      P: (e) => ({
        ...(null != e.likes ? { likeCount: e.likes } : {}),
        ...(null != e.replyCount ? { replyCount: e.replyCount } : {}),
        ...(null != e.repostCount ? { repostCount: e.repostCount } : {}),
        ...(null != e.viewCount ? { viewCount: e.viewCount } : {}),
        ...("boolean" == typeof e.hasLiked
          ? { likedByViewer: e.hasLiked }
          : {}),
        ...("boolean" == typeof e.hasReposted
          ? { repostedByViewer: e.hasReposted }
          : {}),
      }),
    },
  };
}
export function createHelperPorts(variant) {
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
    throw TypeError("explicit supported1846 helper context required");
  return table[variant]();
}
