export function createProfileHoverCard({
  environmentSnapshot,
  React,
  compiler,
  jsxRuntime,
  useApiClientsConfig,
  useVerifiedStatus,
  useProfileLookup,
  useQuery,
  readBalanceSummary,
  readWindowPnl,
  normalizeBalanceSummary,
  readXProfile,
  useFeatureFlag,
  groupRoute,
  shortenAddress,
  plural,
  formatMoney,
  formatCompact,
  formatSigned,
  formatPnlClass,
  formatCount,
  formatUpdated,
  classes,
  Avatar,
  VerifiedBadge,
  XTooltip,
  HoverRoot,
  HoverTrigger,
  HoverContent,
  XIcon,
  CheckIcon,
  CopyIcon,
  navigator,
  setInterval,
  clearInterval,
  setTimeout
}) {
  const t = environmentSnapshot,
    r = jsxRuntime,
    n = {
      c: compiler
    },
    a = {
      Tc: XIcon,
      sX: CheckIcon,
      xR: CopyIcon
    },
    i = {
      useApiClientsConfig
    },
    l = {
      D: {
        WEB_SQUADS: "webSquads"
      }
    },
    o = {
      k: useFeatureFlag
    },
    s = {
      c: classes,
      A: "https://pump.mypinata.cloud/ipfs/QmeSzchzEPqCU1jwTnsipwcBAeH7S4bmVvFGfF65iA1BY1"
    },
    u = {
      w: formatMoney
    },
    d = {
      C: formatUpdated
    },
    c = {
      d: shortenAddress,
      V: plural
    },
    f = {
      Z: groupRoute
    },
    m = {
      f: normalizeBalanceSummary
    },
    h = {
      l: formatCompact,
      u: formatSigned,
      k: formatPnlClass,
      O: formatCount
    },
    p = {
      f: Avatar
    },
    x = {
      f: VerifiedBadge
    },
    g = {
      s: useVerifiedStatus
    },
    y = {
      C: useProfileLookup
    },
    v = React,
    b = {
      c: HoverRoot,
      b: HoverTrigger,
      P: HoverContent
    },
    w = {
      V: "overlay-glass rounded-xl border border-border-tertiary text-text-primary shadow-lg"
    },
    j = {
      useQuery
    },
    A = {
      a: XTooltip
    },
    I = {
      k: readXProfile
    },
    $ = readBalanceSummary,
    R = readWindowPnl;
  let z = void 0 !== t.default && "https://pump.mypinata.cloud/ipfs/" || "https://pump.mypinata.cloud/ipfs/",
    O = `${w.V} w-[280px] p-3`,
    L = "text-[11px] font-normal leading-4 text-text-quaternary",
    q = "inline-block h-3 animate-pulse rounded-sm bg-bg-tertiary align-middle",
    V = "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-accent",
    X = e => e.stopPropagation(),
    B = `inline-flex h-7 min-w-0 flex-1 items-center justify-center rounded-md bg-bg-tertiary px-2.5 text-[12px] font-medium leading-none text-text-primary transition-colors hover:bg-bg-tertiary/75 ${V}`,
    H = `inline-flex size-7 shrink-0 items-center justify-center rounded-md text-text-secondary transition-colors hover:bg-bg-tertiary hover:text-text-primary ${V}`;
  let W = e => {
    let t,
      i,
      l,
      o,
      u,
      d,
      c = (0, n.c)(15),
      {
        className: f,
        xProfile: m
      } = e;
    c[0] !== m.x_username ? (t = m.x_username.trim(), c[0] = m.x_username, c[1] = t) : t = c[1];
    let h = t;
    c[2] !== m.x_profile_url ? (i = m.x_profile_url?.trim() || null, c[2] = m.x_profile_url, c[3] = i) : i = c[3];
    let p = i;
    if (!h || !p) return null;
    let x = `View @${h} on X`;
    c[4] !== f ? (l = (0, s.c)("inline-flex size-5 shrink-0 items-center justify-center rounded-sm text-text-quaternary transition-colors hover:bg-bg-tertiary hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-accent", f), c[4] = f, c[5] = l) : l = c[5];
    let g = `@${h}`;
    return c[6] === Symbol.for("react.memo_cache_sentinel") ? (o = (0, r.jsx)(a.Tc, {
      className: "size-3.5",
      "aria-hidden": !0
    }), c[6] = o) : o = c[6], c[7] !== x || c[8] !== p || c[9] !== l || c[10] !== g ? (u = (0, r.jsx)("a", {
      href: p,
      target: "_blank",
      rel: "noreferrer",
      onClick: E,
      className: l,
      "aria-label": x,
      title: g,
      children: o
    }), c[7] = x, c[8] = p, c[9] = l, c[10] = g, c[11] = u) : u = c[11], c[12] !== u || c[13] !== m ? (d = (0, r.jsx)(A.a, {
      xProfile: m,
      children: u
    }), c[12] = u, c[13] = m, c[14] = d) : d = c[14], d;
  };
  function E(e) {
    return e.stopPropagation();
  }
  function Y(e) {
    let t,
      a,
      i,
      l,
      o,
      u,
      d = (0, n.c)(14),
      {
        label: c,
        value: f,
        loading: m,
        title: h,
        valueClassName: p
      } = e;
    return d[0] === Symbol.for("react.memo_cache_sentinel") ? (t = (0, s.c)("flex h-6 items-center", L), d[0] = t) : t = d[0], d[1] !== c ? (a = (0, r.jsx)("dt", {
      className: t,
      children: c
    }), d[1] = c, d[2] = a) : a = d[2], d[3] === Symbol.for("react.memo_cache_sentinel") ? (i = (0, s.c)("flex h-6 items-center justify-end", "min-w-0 text-right text-[13px] font-medium leading-4 tabular-nums text-text-primary"), d[3] = i) : i = d[3], d[4] !== m || d[5] !== f || d[6] !== p ? (l = m ? (0, r.jsx)("span", {
      "aria-hidden": !0,
      className: (0, s.c)(q, "w-12")
    }) : (0, r.jsx)("span", {
      className: (0, s.c)("truncate", p),
      children: f
    }), d[4] = m, d[5] = f, d[6] = p, d[7] = l) : l = d[7], d[8] !== l || d[9] !== h ? (o = (0, r.jsx)("dd", {
      className: i,
      title: h,
      children: l
    }), d[8] = l, d[9] = h, d[10] = o) : o = d[10], d[11] !== a || d[12] !== o ? (u = (0, r.jsxs)(r.Fragment, {
      children: [a, o]
    }), d[11] = a, d[12] = o, d[13] = u) : u = d[13], u;
  }
  const ProfileHoverCard = e => {
    var t;
    let w,
      C,
      _,
      N,
      P,
      S,
      M,
      k,
      D,
      F,
      T,
      U,
      A,
      E,
      J,
      Q,
      K,
      Z,
      G,
      ee,
      et,
      er,
      en,
      ea,
      ei,
      el,
      eo,
      es,
      eu,
      ed,
      ec,
      ef,
      em,
      eh,
      ep,
      ex,
      eg,
      ey,
      ev,
      eb,
      ew,
      ej,
      eC = (0, n.c)(111),
      {
        children: e_,
        className: eN,
        closeDelay: eP,
        context: eS,
        disabled: eM,
        fallbackAvatarUrl: ek,
        fallbackUsername: eD,
        followSlot: eF,
        ipfsPrefix: eT,
        onOpenChange: e$,
        openDelay: eU,
        userAddress: eR,
        userId: eA,
        userProfileLink: eW,
        side: eE,
        align: eI
      } = e,
      {
        clientServerUrl: ez
      } = (0, i.useApiClientsConfig)(),
      [eO, eL] = (0, v.useState)(!1),
      [eq, eV] = (0, v.useState)(!1),
      eX = (0, g.s)(eA ?? eR);
    eC[0] === Symbol.for("react.memo_cache_sentinel") ? (w = {
      staleTime: 3e5
    }, eC[0] = w) : w = eC[0], eC[1] !== ez || eC[2] !== eO || eC[3] !== eR ? (C = {
      clientServerUrl: ez,
      enabled: eO,
      queryOptions: w,
      userIdentifier: eR
    }, eC[1] = ez, eC[2] = eO, eC[3] = eR, eC[4] = C) : C = eC[4];
    let eB = (0, y.C)(C);
    eC[5] !== eO || eC[6] !== eR ? (_ = {
      enabled: eO,
      userAddress: eR
    }, eC[5] = eO, eC[6] = eR, eC[7] = _) : _ = eC[7];
    let eH = (e => {
      let t,
        r,
        a,
        l = (0, n.c)(10),
        {
          enabled: o,
          queryOptions: s,
          userAddress: u
        } = e,
        {
          profileApiUrl: d
        } = (0, i.useApiClientsConfig)(),
        c = o && !!u;
      return (l[0] !== d || l[1] !== u ? (t = () => $({
        profileApiUrl: d,
        userAddress: u
      }), l[0] = d, l[1] = u, l[2] = t) : t = l[2], l[3] !== u) ? (r = ["balanceSummary", u], l[3] = u, l[4] = r) : r = l[4], l[5] !== s || l[6] !== c || l[7] !== t || l[8] !== r ? (a = {
        enabled: c,
        queryFn: t,
        queryKey: r,
        staleTime: 3e5,
        ...s
      }, l[5] = s, l[6] = c, l[7] = t, l[8] = r, l[9] = a) : a = l[9], (0, j.useQuery)(a);
    })(_);
    eC[8] !== eO || eC[9] !== eR ? (N = {
      enabled: eO,
      userAddress: eR
    }, eC[8] = eO, eC[9] = eR, eC[10] = N) : N = eC[10];
    let eY = (e => {
        let t,
          r,
          a,
          l = (0, n.c)(9),
          {
            enabled: o,
            userAddress: s
          } = e,
          {
            clientServerUrl: u
          } = (0, i.useApiClientsConfig)(),
          d = o && s.length > 0;
        return (l[0] !== u || l[1] !== s ? (t = () => R(u, s), l[0] = u, l[1] = s, l[2] = t) : t = l[2], l[3] !== s) ? (r = ["userProfileHoverWindowPnl", "1w", s], l[3] = s, l[4] = r) : r = l[4], l[5] !== d || l[6] !== t || l[7] !== r ? (a = {
          enabled: d,
          queryFn: t,
          queryKey: r,
          retry: 1,
          staleTime: 6e4
        }, l[5] = d, l[6] = t, l[7] = r, l[8] = a) : a = l[8], (0, j.useQuery)(a);
      })(N),
      eJ = eB.data,
      eQ = eT && eT.trim().length > 0 ? eT : z;
    eC[11] !== eD || eC[12] !== eJ?.username || eC[13] !== eR ? (P = eJ?.username?.trim() || eD?.trim() || (0, c.d)(eR), eC[11] = eD, eC[12] = eJ?.username, eC[13] = eR, eC[14] = P) : P = eC[14];
    let eK = P;
    eC[15] !== ek || eC[16] !== eJ?.profile_image ? (S = eJ?.profile_image?.trim() || ek?.trim() || null, eC[15] = ek, eC[16] = eJ?.profile_image, eC[17] = S) : S = eC[17];
    let eZ = S,
      eG = eZ === s.A ? null : eZ;
    eC[18] !== eD || eC[19] !== eJ?.username ? (M = eJ?.username?.trim() || eD?.trim(), eC[18] = eD, eC[19] = eJ?.username, eC[20] = M) : M = eC[20];
    let e0 = !!M;
    eC[21] !== eJ ? (D = (0, I.k)(eJ), k = D?.x_username?.trim() || null, eC[21] = eJ, eC[22] = k, eC[23] = D) : (k = eC[22], D = eC[23]);
    let e1 = k,
      e2 = null !== D && null !== e1,
      e3 = (ej = eJ?.group_badges?.find(e => e.group_id)) ? {
        groupId: ej.group_id,
        username: ej.username?.trim() || null,
        profileImageUrl: ej.profile_image_url?.trim() || null
      } : null,
      e5 = e3 ? `Squad: ${e3.username ?? "Squad"}` : null,
      e4 = (0, o.k)(l.D.WEB_SQUADS);
    if (eC[24] !== eJ) F = eJ?.bio?.trim() || null, eC[24] = eJ, eC[25] = F;else F = eC[25];
    let e8 = F,
      e6 = (e => {
        if (!e) return null;
        let {
          followers: t,
          following: r
        } = e;
        return Number.isFinite(t) && Number.isFinite(r) ? {
          followers: t,
          following: r
        } : null;
      })(eJ),
      e9 = eY.data ?? null,
      e7 = eH.data,
      te = e7?.success === !0 ? e7.data : null,
      tt = (0, m.f)(te),
      tr = void 0 !== e7 && !1 === e7.success,
      tn = eH.isPending,
      ta = eH.isError || tr,
      ti = eB.isPending,
      tl = !tn && !ta,
      to = tl ? Number.isFinite(t = tt.totalValue) ? Math.abs(t) >= 1e6 ? (0, h.l)(t) : (0, u.w)(t) : (0, u.w)(0) : null,
      ts = tl ? (0, u.w)(tt.totalValue) : void 0,
      tu = tl ? tt.nativeBalance.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 4
      }) : null,
      td = tt.portfolioPnL,
      tc = tl && td.totalCostBasisUsd > 0,
      tf = (0, h.u)(td.totalUnrealizedUsd),
      tm = eW || `/profile/${eR}`,
      [th, tp] = (0, v.useState)(null);
    (0, v.useEffect)(() => {
      if (!eO || tn || ta || null === tt.lastUpdatedTs) return void tp(null);
      let e = tt.lastUpdatedTs,
        t = () => tp((0, d.C)(e));
      t();
      let r = setInterval(t, 3e4);
      return () => clearInterval(r);
    }, [eO, tt.lastUpdatedTs, ta, tn]), eC[26] !== eR ? (T = async () => {
      await navigator.clipboard.writeText(eR), eV(!0), setTimeout(() => eV(!1), 2e3);
    }, eC[26] = eR, eC[27] = T) : T = eC[27];
    let tx = T;
    eC[28] !== eR ? (U = (0, c.d)(eR, 4, 4), eC[28] = eR, eC[29] = U) : U = eC[29];
    let tg = U,
      ty = "string" == typeof eS ? eS : void 0;
    if (void 0 !== eM && eM) {
      let e;
      return eC[30] !== e_ ? (e = (0, r.jsx)(r.Fragment, {
        children: e_
      }), eC[30] = e_, eC[31] = e) : e = eC[31], e;
    }
    eC[32] !== e$ ? (A = e => {
      eL(e), e$?.(e);
    }, eC[32] = e$, eC[33] = A) : A = eC[33], eC[34] !== e_ ? (E = (0, r.jsx)(b.b, {
      asChild: !0,
      children: e_
    }), eC[34] = e_, eC[35] = E) : E = eC[35], eC[36] !== eN ? (J = (0, s.c)(O, eN), eC[36] = eN, eC[37] = J) : J = eC[37], eC[38] === Symbol.for("react.memo_cache_sentinel") ? (Q = (0, s.c)("shrink-0 rounded-full", V), eC[38] = Q) : Q = eC[38], eC[39] !== eG || eC[40] !== eK || eC[41] !== eQ || eC[42] !== ti || eC[43] !== eR ? (K = ti && !eG ? (0, r.jsx)("span", {
      className: "block size-8 animate-pulse rounded-full bg-bg-tertiary"
    }) : (0, r.jsx)(p.f, {
      address: eR,
      alt: eK,
      className: "size-8 rounded-full",
      height: 32,
      ipfsPrefix: eQ,
      isAnonymous: !1,
      src: eG ?? void 0,
      width: 32
    }), eC[39] = eG, eC[40] = eK, eC[41] = eQ, eC[42] = ti, eC[43] = eR, eC[44] = K) : K = eC[44], eC[45] !== tm || eC[46] !== K ? (Z = (0, r.jsx)("a", {
      href: tm,
      className: Q,
      children: K
    }), eC[45] = tm, eC[46] = K, eC[47] = Z) : Z = eC[47], eC[48] === Symbol.for("react.memo_cache_sentinel") ? (G = (0, s.c)("min-w-0 rounded-sm", V), eC[48] = G) : G = eC[48], eC[49] !== eK ? (ee = (0, r.jsx)("h4", {
      className: "truncate text-[13px] font-medium leading-4 text-text-primary",
      children: eK
    }), eC[49] = eK, eC[50] = ee) : ee = eC[50], eC[51] !== tm || eC[52] !== ee ? (et = (0, r.jsx)("a", {
      href: tm,
      className: G,
      children: ee
    }), eC[51] = tm, eC[52] = ee, eC[53] = et) : et = eC[53], eC[54] !== eX ? (er = eX ? (0, r.jsx)(x.f, {
      size: 14
    }) : null, eC[54] = eX, eC[55] = er) : er = eC[55], eC[56] !== e2 || eC[57] !== D ? (en = e2 && D ? (0, r.jsx)(W, {
      xProfile: D
    }) : null, eC[56] = e2, eC[57] = D, eC[58] = en) : en = eC[58];
    let tv = e4 && e3 && e5 ? (0, r.jsx)("a", {
      href: (0, f.Z)({
        groupId: e3.groupId,
        username: e3.username
      }),
      "aria-label": e5,
      title: e5,
      "data-testid": "user-profile-hover-squad",
      className: (0, s.c)("inline-flex size-4 shrink-0 items-center justify-center overflow-hidden rounded-sm bg-bg-tertiary transition-opacity hover:opacity-80", V),
      children: (0, r.jsx)(p.f, {
        address: e3.groupId,
        alt: "",
        className: "size-3 rounded-sm object-cover",
        height: 12,
        ipfsPrefix: eQ,
        isAnonymous: !1,
        src: e3.profileImageUrl ?? void 0,
        width: 12
      })
    }) : null;
    eC[59] !== et || eC[60] !== er || eC[61] !== en || eC[62] !== tv ? (ea = (0, r.jsxs)("div", {
      className: "flex min-w-0 items-center gap-1",
      children: [et, er, en, tv]
    }), eC[59] = et, eC[60] = er, eC[61] = en, eC[62] = tv, eC[63] = ea) : ea = eC[63], eC[64] !== e0 || eC[65] !== tg ? (ei = e0 ? (0, r.jsx)("p", {
      className: "truncate font-mono text-[11px] font-normal leading-4 text-text-quaternary",
      children: tg
    }) : null, eC[64] = e0, eC[65] = tg, eC[66] = ei) : ei = eC[66], eC[67] !== ea || eC[68] !== ei ? (el = (0, r.jsxs)("div", {
      className: "min-w-0 flex-1",
      children: [ea, ei]
    }), eC[67] = ea, eC[68] = ei, eC[69] = el) : el = eC[69], eC[70] !== Z || eC[71] !== el ? (eo = (0, r.jsxs)("div", {
      className: "flex items-center gap-2.5",
      "data-testid": "user-profile-hover-identity",
      children: [Z, el]
    }), eC[70] = Z, eC[71] = el, eC[72] = eo) : eo = eC[72], eC[73] !== e8 ? (es = e8 ? (0, r.jsx)("p", {
      className: "mt-2 line-clamp-2 text-[11px] font-normal leading-4 text-text-secondary",
      "data-testid": "user-profile-hover-bio",
      children: e8
    }) : null, eC[73] = e8, eC[74] = es) : es = eC[74], eC[75] === Symbol.for("react.memo_cache_sentinel") ? (eu = (0, r.jsx)("div", {
      "aria-hidden": !0,
      className: "mt-2 border-t border-border-secondary"
    }), eC[75] = eu) : eu = eC[75], eC[76] !== eS || eC[77] !== ty ? (ed = eS ? (0, r.jsx)("p", {
      className: (0, s.c)("mt-2 truncate", L),
      "data-testid": "user-profile-hover-context",
      title: ty,
      children: eS
    }) : null, eC[76] = eS, eC[77] = ty, eC[78] = ed) : ed = eC[78], eC[79] !== e9 ? (ec = null === e9 ? void 0 : (0, u.w)(e9), eC[79] = e9, eC[80] = ec) : ec = eC[80], eC[81] !== e9 ? (ef = null === e9 ? "—" : (0, h.u)(e9), eC[81] = e9, eC[82] = ef) : ef = eC[82], eC[83] !== e9 ? (em = null === e9 ? void 0 : (0, h.k)(e9), eC[83] = e9, eC[84] = em) : em = eC[84], eC[85] !== ec || eC[86] !== ef || eC[87] !== em || eC[88] !== eY.isPending ? (eh = (0, r.jsx)(Y, {
      label: "7d PnL",
      loading: eY.isPending,
      title: ec,
      value: ef,
      valueClassName: em
    }), eC[85] = ec, eC[86] = ef, eC[87] = em, eC[88] = eY.isPending, eC[89] = eh) : eh = eC[89];
    let tb = ta ? "—" : `${tt.tokenCount} ${(0, c.V)("token", "tokens", tt.tokenCount)}`;
    eC[90] !== tn || eC[91] !== tb ? (ep = (0, r.jsx)(Y, {
      label: "Holding",
      loading: tn,
      value: tb
    }), eC[90] = tn, eC[91] = tb, eC[92] = ep) : ep = eC[92], eC[93] !== th || eC[94] !== ta || eC[95] !== tn ? (ex = ta ? (0, r.jsx)("p", {
      className: "mt-1 text-right text-[11px] font-normal leading-4 text-loss",
      "data-testid": "user-profile-hover-updated",
      children: "Balance unavailable"
    }) : tn ? (0, r.jsx)("p", {
      className: (0, s.c)("mt-1 text-right", L),
      "data-testid": "user-profile-hover-updated",
      children: (0, r.jsx)("span", {
        "aria-hidden": !0,
        className: (0, s.c)(q, "w-24")
      })
    }) : null === th ? null : (0, r.jsxs)("p", {
      className: (0, s.c)("mt-1 text-right", L),
      "data-testid": "user-profile-hover-updated",
      children: ["Updated ", th]
    }), eC[93] = th, eC[94] = ta, eC[95] = tn, eC[96] = ex) : ex = eC[96], eC[97] !== eF ? (eg = eF ? (0, r.jsx)("div", {
      className: "shrink-0",
      children: eF
    }) : null, eC[97] = eF, eC[98] = eg) : eg = eC[98], eC[99] !== tm ? (ey = (0, r.jsx)("a", {
      href: tm,
      className: B,
      children: "View profile"
    }), eC[99] = tm, eC[100] = ey) : ey = eC[100];
    let tw = eq ? "Address copied" : "Copy address";
    return eC[101] !== eq ? (ev = eq ? (0, r.jsx)(a.sX, {
      "aria-hidden": !0,
      className: "size-3.5 text-gain"
    }) : (0, r.jsx)(a.xR, {
      "aria-hidden": !0,
      className: "size-3.5"
    }), eC[101] = eq, eC[102] = ev) : ev = eC[102], eC[103] !== tx || eC[104] !== tw || eC[105] !== ev ? (eb = (0, r.jsx)("button", {
      type: "button",
      onClick: tx,
      "aria-label": tw,
      title: "Copy address",
      className: H,
      children: ev
    }), eC[103] = tx, eC[104] = tw, eC[105] = ev, eC[106] = eb) : eb = eC[106], eC[107] !== eg || eC[108] !== ey || eC[109] !== eb ? (ew = (0, r.jsxs)("div", {
      className: "mt-2 flex items-center gap-2",
      "data-testid": "user-profile-hover-actions",
      children: [eg, ey, eb]
    }), eC[107] = eg, eC[108] = ey, eC[109] = eb, eC[110] = ew) : ew = eC[110], (0, r.jsxs)(b.c, {
      closeDelay: void 0 === eP ? 100 : eP,
      onOpenChange: A,
      openDelay: void 0 === eU ? 500 : eU,
      children: [E, (0, r.jsxs)(b.P, {
        side: void 0 === eE ? "top" : eE,
        align: void 0 === eI ? "center" : eI,
        collisionPadding: 12,
        className: J,
        onClick: X,
        children: [eo, es, ti || e6 ? (0, r.jsx)("p", {
          className: (0, s.c)("mt-1.5 h-4 truncate", L),
          "data-testid": "user-profile-hover-follows",
          children: e6 ? (0, r.jsxs)(r.Fragment, {
            children: [(0, r.jsx)("span", {
              className: "font-medium text-text-primary",
              children: (0, h.O)(e6.following)
            }), " following · ", (0, r.jsx)("span", {
              className: "font-medium text-text-primary",
              children: (0, h.O)(e6.followers)
            }), " followers"]
          }) : (0, r.jsx)("span", {
            "aria-hidden": !0,
            className: (0, s.c)(q, "w-28")
          })
        }) : null, eu, ed, (0, r.jsxs)("dl", {
          className: "mt-1 grid grid-cols-[auto_1fr] items-center gap-x-3",
          "data-testid": "user-profile-hover-stats",
          children: [(0, r.jsx)(Y, {
            label: "SOL balance",
            loading: tn,
            title: tu ?? void 0,
            value: ta ? "—" : tu
          }), (0, r.jsx)(Y, {
            label: "Portfolio",
            loading: tn,
            title: ts,
            value: ta ? "—" : to
          }), eh, ep, tc ? (0, r.jsx)(Y, {
            label: "PnL",
            loading: !1,
            title: (0, u.w)(td.totalUnrealizedUsd),
            value: tf,
            valueClassName: (0, h.k)(td.totalUnrealizedUsd)
          }) : null]
        }), ex, ew]
      })]
    });
  };
  return {
    ProfileHoverCard
  };
}
