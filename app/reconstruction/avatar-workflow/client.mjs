import {
  normalizeSearchUri,
  FALLBACK_IMAGE,
} from "../search-session/session.mjs";
// Complete used asset closure; URI construction is not remote asset acquisition.
const uri = (() => {
  let r = "https://images.pump.fun",
    s = (e) => {
      try {
        return new URL(e);
      } catch {
        return null;
      }
    },
    t = (e) => {
      let r = s(e);
      return (
        r?.origin === "https://imagedelivery.net" &&
        r.pathname.startsWith("/WL1JOIJiM_NAChp6rtB6Cw/")
      );
    },
    o = ({ url: e, variant: r }) => {
      let s = new URL(e);
      return (s.searchParams.set("variant", r), s.toString());
    };
  return {
    T: (e) => s(e)?.origin === r,
    N: (e) => {
      if (!t(e)) return e;
      let s = new URL(e),
        a = s.pathname.split("/").slice(2),
        n = a.pop();
      if (!n || 0 === a.length) return e;
      let i = new URL(`${r}/${a.join("/")}`);
      return (
        (i.search = s.search),
        o({ url: i.toString(), variant: decodeURIComponent(n) })
      );
    },
    F: o,
  };
})();
const generate = (() => {
  function r(e, r, s) {
    if (0 === r.length) return s;
    let t = Math.floor(e() * r.length);
    return r[t] ?? s;
  }
  function s(e) {
    return Object.keys(e).sort();
  }
  var t = (e, r) =>
      `https://imagedelivery.net/WL1JOIJiM_NAChp6rtB6Cw/pump-avatar/${e}/${encodeURIComponent(r)}/600x600`,
    o = {
      backgrounds: {
        Amber: t("Backgrounds", "Amber"),
        Blue: t("Backgrounds", "Blue"),
        Cyan: t("Backgrounds", "Cyan"),
        "Dark-blue": t("Backgrounds", "Dark-blue"),
        Emerald: t("Backgrounds", "Emerald"),
        Green: t("Backgrounds", "Green"),
        Indigo: t("Backgrounds", "Indigo"),
        Orange: t("Backgrounds", "Orange"),
        Pink: t("Backgrounds", "Pink"),
        Purple: t("Backgrounds", "Purple"),
        Red: t("Backgrounds", "Red"),
      },
      bodies: {
        "Body-2-Blue": t("Bodies", "Body-2-Blue"),
        "Body-2-Cyan": t("Bodies", "Body-2-Cyan"),
        "Body-2-Emerald": t("Bodies", "Body-2-Emerald"),
        "Body-2-Green": t("Bodies", "Body-2-Green"),
        "Body-2-Indigo": t("Bodies", "Body-2-Indigo"),
        "Body-2-Orange": t("Bodies", "Body-2-Orange"),
        "Body-2-Red": t("Bodies", "Body-2-Red"),
        "Body-2-Yellow": t("Bodies", "Body-2-Yellow"),
        "Body-3-Blue-glass": t("Bodies", "Body-3-Blue-glass"),
        "Body-3-Blue-wand": t("Bodies", "Body-3-Blue-wand"),
        "Body-3-Blue": t("Bodies", "Body-3-Blue"),
        "Body-3-Cyan-glass": t("Bodies", "Body-3-Cyan-glass"),
        "Body-3-Cyan-wand": t("Bodies", "Body-3-Cyan-wand"),
        "Body-3-Cyan": t("Bodies", "Body-3-Cyan"),
        "Body-3-Emerald-glass": t("Bodies", "Body-3-Emerald-glass"),
        "Body-3-Emerald-wand": t("Bodies", "Body-3-Emerald-wand"),
        "Body-3-Emerald": t("Bodies", "Body-3-Emerald"),
        "Body-3-Green-glass": t("Bodies", "Body-3-Green-glass"),
        "Body-3-Green-wand": t("Bodies", "Body-3-Green-wand"),
        "Body-3-Green": t("Bodies", "Body-3-Green"),
        "Body-3-Indigo-glass": t("Bodies", "Body-3-Indigo-glass"),
        "Body-3-Indigo-wand": t("Bodies", "Body-3-Indigo-wand"),
        "Body-3-Indigo": t("Bodies", "Body-3-Indigo"),
        "Body-3-Orange-glass": t("Bodies", "Body-3-Orange-glass"),
        "Body-3-Orange-wand": t("Bodies", "Body-3-Orange-wand"),
        "Body-3-Orange": t("Bodies", "Body-3-Orange"),
        "Body-3-Red-glass": t("Bodies", "Body-3-Red-glass"),
        "Body-3-Red-wand": t("Bodies", "Body-3-Red-wand"),
        "Body-3-Red": t("Bodies", "Body-3-Red"),
        "Body-3-Yellow-glass": t("Bodies", "Body-3-Yellow-glass"),
        "Body-3-Yellow-wand": t("Bodies", "Body-3-Yellow-wand"),
        "Body-3-Yellow": t("Bodies", "Body-3-Yellow"),
        "Body-Blue": t("Bodies", "Body-Blue"),
        "Body-Cyan": t("Bodies", "Body-Cyan"),
        "Body-Emerald": t("Bodies", "Body-Emerald"),
        "Body-Green": t("Bodies", "Body-Green"),
        "Body-Indigo": t("Bodies", "Body-Indigo"),
        "Body-Orange": t("Bodies", "Body-Orange"),
        "Body-Red": t("Bodies", "Body-Red"),
        "Body-Yellow": t("Bodies", "Body-Yellow"),
      },
      faceExpressions: {
        "Face-1": t("Face-expressions", "Face-1"),
        "Face-10": t("Face-expressions", "Face-10"),
        "Face-11": t("Face-expressions", "Face-11"),
        "Face-2": t("Face-expressions", "Face-2"),
        "Face-3": t("Face-expressions", "Face-3"),
        "Face-4": t("Face-expressions", "Face-4"),
        "Face-5": t("Face-expressions", "Face-5"),
        "Face-6": t("Face-expressions", "Face-6"),
        "Face-7": t("Face-expressions", "Face-7"),
        "Face-8": t("Face-expressions", "Face-8"),
        "Face-9": t("Face-expressions", "Face-9"),
      },
      faceAccessories: {
        Blush: t("Face-Accessories", "Blush"),
        "Empty 2": t("Face-Accessories", "Empty 2"),
        Empty: t("Face-Accessories", "Empty"),
        "Glasses-black": t("Face-Accessories", "Glasses-black"),
        "Glasses-brown": t("Face-Accessories", "Glasses-brown"),
        Glasses: t("Face-Accessories", "Glasses"),
        Sunglasses: t("Face-Accessories", "Sunglasses"),
      },
      headAccessories: {
        Beret: t("Head-accessories", "Beret"),
        "Cap-back-green": t("Head-accessories", "Cap-back-green"),
        "Cap-back-red": t("Head-accessories", "Cap-back-red"),
        "Cap-back-yellow": t("Head-accessories", "Cap-back-yellow"),
        "Cap-Green": t("Head-accessories", "Cap-Green"),
        "Cap-Orange": t("Head-accessories", "Cap-Orange"),
        "Cap-Red": t("Head-accessories", "Cap-Red"),
        "Chef_s-Hat": t("Head-accessories", "Chef_s-Hat"),
        Crown: t("Head-accessories", "Crown"),
        "Durag-Yellow": t("Head-accessories", "Durag-Yellow"),
        Durag: t("Head-accessories", "Durag"),
        "Empty 2": t("Head-accessories", "Empty 2"),
        Empty: t("Head-accessories", "Empty"),
        "Graduation-hat": t("Head-accessories", "Graduation-hat"),
        "Hairstyle-1---Black": t("Head-accessories", "Hairstyle-1---Black"),
        "Hairstyle-1---Green": t("Head-accessories", "Hairstyle-1---Green"),
        "Hairstyle-1---Red": t("Head-accessories", "Hairstyle-1---Red"),
        "Hairstyle-2---Brown": t("Head-accessories", "Hairstyle-2---Brown"),
        "Hairstyle-2---Orange": t("Head-accessories", "Hairstyle-2---Orange"),
        "Hairstyle-3-blue": t("Head-accessories", "Hairstyle-3-blue"),
        "Hairstyle-3-grey": t("Head-accessories", "Hairstyle-3-grey"),
        "Hairstyle-3": t("Head-accessories", "Hairstyle-3"),
        "Hairstyle-4---Green": t("Head-accessories", "Hairstyle-4---Green"),
        "Hairstyle-4---Red": t("Head-accessories", "Hairstyle-4---Red"),
        "Hairstyle-5": t("Head-accessories", "Hairstyle-5"),
        "Hat-Brown": t("Head-accessories", "Hat-Brown"),
        Hat: t("Head-accessories", "Hat"),
        "Headphones-Grey": t("Head-accessories", "Headphones-Grey"),
        "Headphones-Maroon": t("Head-accessories", "Headphones-Maroon"),
        "Leafs-Yellow": t("Head-accessories", "Leafs-Yellow"),
        Leafs: t("Head-accessories", "Leafs"),
        "Winter-Hat-Blue": t("Head-accessories", "Winter-Hat-Blue"),
        "Winter-Hat-Yellow": t("Head-accessories", "Winter-Hat-Yellow"),
        "Winter-Hat": t("Head-accessories", "Winter-Hat"),
      },
      armAccessories: {
        "Bracelet-green": t("Arm-Accessories", "Bracelet-green"),
        "Bracelet-orange": t("Arm-Accessories", "Bracelet-orange"),
        "Empty 2": t("Arm-Accessories", "Empty 2"),
        Empty: t("Arm-Accessories", "Empty"),
        Watch: t("Arm-Accessories", "Watch"),
      },
      accessories: {
        "Bowtie-Green": t("Accessories", "Bowtie-Green"),
        "Bowtie-Indigo": t("Accessories", "Bowtie-Indigo"),
        "Bowtie-Orange": t("Accessories", "Bowtie-Orange"),
        "Bowtie-Red": t("Accessories", "Bowtie-Red"),
        Buckle: t("Accessories", "Buckle"),
        "Empty 2": t("Accessories", "Empty 2"),
        Empty: t("Accessories", "Empty"),
        "Necklace-Red": t("Accessories", "Necklace-Red"),
        "Necklace-White": t("Accessories", "Necklace-White"),
        "Necklace-Yellow": t("Accessories", "Necklace-Yellow"),
        "Scarf-Green": t("Accessories", "Scarf-Green"),
        "Scarf-Red": t("Accessories", "Scarf-Red"),
        "Tie-Green": t("Accessories", "Tie-Green"),
        "Tie-Red": t("Accessories", "Tie-Red"),
        "Tie-Yellow": t("Accessories", "Tie-Yellow"),
        "Winter-Scarf-Blue": t("Accessories", "Winter-Scarf-Blue"),
        "Winter-Scarf-Green": t("Accessories", "Winter-Scarf-Green"),
        "Winter-Scarf": t("Accessories", "Winter-Scarf"),
      },
    };
  return function (e, t = {}) {
    let a = t.catalog ?? o,
      n = (function (e, t, o = {}) {
        return (function (e, t, o = {}) {
          let a,
            n =
              ((a =
                (function (e) {
                  let r = 0x6a09e667 ^ e.length;
                  for (let s = 0; s < e.length; s++)
                    r =
                      ((r = Math.imul(r ^ e.charCodeAt(s), 0xcc9e2d51)) << 13) |
                      (r >>> 19);
                  return () => (
                    (r = Math.imul(
                      (r = Math.imul(r ^ (r >>> 16), 0x85ebca6b)) ^ (r >>> 13),
                      0xc2b2ae35,
                    )),
                    (r ^= r >>> 16) >>> 0
                  );
                })(e)() >>> 0),
              () => {
                a |= 0;
                let e = Math.imul(
                  (a = (a + 0x6d2b79f5) | 0) ^ (a >>> 15),
                  1 | a,
                );
                return (
                  (((e = (e + Math.imul(e ^ (e >>> 7), 61 | e)) ^ e) ^
                    (e >>> 14)) >>>
                    0) /
                  0x100000000
                );
              }),
            i = s(t.backgrounds),
            c = s(t.bodies),
            d = s(t.faceExpressions),
            l = s(t.faceAccessories),
            u = s(t.headAccessories),
            y = s(t.armAccessories),
            f = s(t.accessories),
            B = o.background ?? r(n, i, i[0] ?? ""),
            g = o.body ?? r(n, c, c[0] ?? ""),
            p = o.faceExpression ?? r(n, d, d[0] ?? ""),
            m = o.faceAccessory ?? r(n, l, l[0] ?? ""),
            h = o.headAccessory ?? r(n, u, u[0] ?? "");
          return {
            background: B,
            body: g,
            faceExpression: p,
            faceAccessory: m,
            headAccessory: h,
            armAccessory: o.armAccessory ?? r(n, y, y[0] ?? ""),
            accessory: o.accessory ?? r(n, f, f[0] ?? ""),
          };
        })(e, t, o);
      })(e, a, t.overrides);
    return [
      n.background ? a.backgrounds[n.background] : void 0,
      n.body ? a.bodies[n.body] : void 0,
      n.faceExpression ? a.faceExpressions[n.faceExpression] : void 0,
      n.faceAccessory ? a.faceAccessories[n.faceAccessory] : void 0,
      n.headAccessory ? a.headAccessories[n.headAccessory] : void 0,
      n.armAccessory ? a.armAccessories[n.armAccessory] : void 0,
      n.accessory ? a.accessories[n.accessory] : void 0,
    ].filter((e) => "string" == typeof e);
  };
})();
const image = (() => {
  const a = { r: normalizeSearchUri, A: FALLBACK_IMAGE },
    n = uri;
  let i = (e) => {
      if ("number" == typeof e && Number.isFinite(e) && e > 0) return e;
      if ("string" == typeof e) {
        let r = Number.parseInt(e, 10);
        if (Number.isFinite(r) && r > 0) return r;
      }
    },
    c = [24, 32, 64, 128, 144, 600],
    d = [".mypinata.cloud"],
    l = ["gateway.pinata.cloud"],
    u = (e) => {
      try {
        let { hostname: r, pathname: s } = new URL(e);
        if (!s.includes("/ipfs/")) return !1;
        let t = r.toLowerCase();
        if (l.some((e) => t === e)) return !0;
        return d.some((e) => t.endsWith(e));
      } catch {
        return !1;
      }
    },
    y = (e) => (c.includes(e) ? e : (c.find((r) => r >= e) ?? c[c.length - 1])),
    f = /^(?:https?:\/\/|blob:|data:)/i;
  return {
    D: (e, r) => {
      let s = (0, a.r)(e ?? null, r);
      return e && e !== a.A && s === a.A && f.test(e) ? e : s;
    },
    p: (e, r, s) => {
      let t = i(r) ?? i(s);
      if (!t || e.startsWith("blob:") || !u(e) || e.includes("img-width="))
        return e;
      let o = e.includes("?") ? "&" : "?";
      return `${e}${o}img-width=${t}&img-dpr=2&img-onerror=redirect`;
    },
    k: (e, r, s) => {
      let t = ((e, r) => {
        let s = i(e) ?? i(r);
        if (s) return y(Math.ceil(1.6 * s));
      })(r, s);
      return e.map((e) =>
        ((e, r) => {
          let s = (0, n.N)(e);
          if (!r || !(0, n.T)(s)) return s;
          let t = y(r);
          return (0, n.F)({ url: s, variant: `${t}x${t}` });
        })(e, t),
      );
    },
  };
})();
export const avatarAssets = {
  generate,
  normalizeSource: image.D,
  sizeSource: image.p,
  sizeLayers: image.k,
};
export { FALLBACK_IMAGE };
// Construct once using the caller's actual JSX/compiler/React/class interfaces.
export function createAvatarWorkflow({ jsx, useMemoCache, React, classNames }) {
  for (const [name, value] of Object.entries({ jsx, useMemoCache, classNames }))
    if (typeof value !== "function")
      throw new TypeError("Explicit Avatar capability required: " + name);
  for (const name of ["useState", "useEffect"])
    if (typeof React?.[name] !== "function")
      throw new TypeError("Explicit Avatar React hook required: " + name);
  const r = { jsx },
    s = { c: useMemoCache },
    t = { A: FALLBACK_IMAGE, c: classNames },
    o = { useState: React.useState, useEffect: React.useEffect },
    a = { D: image.D, p: image.p, k: image.k },
    i = { f: generate };
  function n(e) {
    let n,
      i,
      c,
      d,
      l,
      u,
      y,
      f,
      B,
      g,
      p,
      m,
      h,
      w,
      v = (0, s.c)(30);
    v[0] !== e
      ? (({
          src: u,
          className: n,
          ipfsPrefix: c,
          onError: d,
          width: f,
          height: i,
          alt: y,
          ...l
        } = e),
        (v[0] = e),
        (v[1] = n),
        (v[2] = i),
        (v[3] = c),
        (v[4] = d),
        (v[5] = l),
        (v[6] = u),
        (v[7] = y),
        (v[8] = f))
      : ((n = v[1]),
        (i = v[2]),
        (c = v[3]),
        (d = v[4]),
        (l = v[5]),
        (u = v[6]),
        (y = v[7]),
        (f = v[8]));
    let b = void 0 === y ? "" : y;
    v[9] !== i || v[10] !== c || v[11] !== u || v[12] !== f
      ? ((B = (0, a.p)((0, a.D)(u, c), f, i)),
        (v[9] = i),
        (v[10] = c),
        (v[11] = u),
        (v[12] = f),
        (v[13] = B))
      : (B = v[13]);
    let H = B,
      [A, E] = (0, o.useState)(!1);
    (v[14] === Symbol.for("react.memo_cache_sentinel")
      ? ((g = () => {
          E(!1);
        }),
        (v[14] = g))
      : (g = v[14]),
      v[15] !== H ? ((p = [H]), (v[15] = H), (v[16] = p)) : (p = v[16]),
      (0, o.useEffect)(g, p));
    let C = A ? t.A : H;
    return (
      v[17] !== n
        ? ((m = (0, t.c)("object-cover rounded-full overflow-hidden", n)),
          (v[17] = n),
          (v[18] = m))
        : (m = v[18]),
      v[19] !== A || v[20] !== d
        ? ((h = (e) => {
            (A || e.currentTarget.src === t.A || E(!0), d?.(e));
          }),
          (v[19] = A),
          (v[20] = d),
          (v[21] = h))
        : (h = v[21]),
      v[22] !== b ||
      v[23] !== C ||
      v[24] !== i ||
      v[25] !== l ||
      v[26] !== m ||
      v[27] !== h ||
      v[28] !== f
        ? ((w = (0, r.jsx)("img", {
            ...l,
            alt: b,
            width: f,
            height: i,
            src: C,
            className: m,
            onError: h,
          })),
          (v[22] = b),
          (v[23] = C),
          (v[24] = i),
          (v[25] = l),
          (v[26] = m),
          (v[27] = h),
          (v[28] = f),
          (v[29] = w))
        : (w = v[29]),
      w
    );
  }
  function c(e) {
    let o,
      n,
      c,
      d,
      l,
      u,
      y,
      f,
      B,
      g,
      p,
      m,
      h,
      w,
      v = (0, s.c)(34);
    v[0] !== e
      ? (({
          address: o,
          className: n,
          style: u,
          forwardRef: c,
          width: f,
          height: d,
          alt: y,
          ...l
        } = e),
        (v[0] = e),
        (v[1] = o),
        (v[2] = n),
        (v[3] = c),
        (v[4] = d),
        (v[5] = l),
        (v[6] = u),
        (v[7] = y),
        (v[8] = f))
      : ((o = v[1]),
        (n = v[2]),
        (c = v[3]),
        (d = v[4]),
        (l = v[5]),
        (u = v[6]),
        (y = v[7]),
        (f = v[8]));
    let b = void 0 === y ? "" : y;
    v[9] !== o || v[10] !== d || v[11] !== f
      ? ((B = (0, a.k)((0, i.f)(o), f, d)),
        (v[9] = o),
        (v[10] = d),
        (v[11] = f),
        (v[12] = B))
      : (B = v[12]);
    let H = B;
    if (
      (v[13] !== n
        ? ((g = (0, t.c)("relative overflow-hidden rounded-full", n)),
          (v[13] = n),
          (v[14] = g))
        : (g = v[14]),
      v[15] === Symbol.for("react.memo_cache_sentinel")
        ? ((p = { transform: "scale(1.6) translate(1%, 18%)" }), (v[15] = p))
        : (p = v[15]),
      v[16] !== b || v[17] !== d || v[18] !== l || v[19] !== H || v[20] !== f)
    ) {
      let e;
      (v[22] !== b || v[23] !== d || v[24] !== l || v[25] !== f
        ? ((e = (e) =>
            (0, r.jsx)(
              "img",
              {
                src: e,
                width: f,
                height: d,
                className: "absolute inset-0 h-full w-full object-cover",
                ...l,
                alt: b,
              },
              e,
            )),
          (v[22] = b),
          (v[23] = d),
          (v[24] = l),
          (v[25] = f),
          (v[26] = e))
        : (e = v[26]),
        (m = H.map(e)),
        (v[16] = b),
        (v[17] = d),
        (v[18] = l),
        (v[19] = H),
        (v[20] = f),
        (v[21] = m));
    } else m = v[21];
    return (
      v[27] !== m
        ? ((h = (0, r.jsx)("div", {
            className: "absolute inset-0 origin-center",
            style: p,
            children: m,
          })),
          (v[27] = m),
          (v[28] = h))
        : (h = v[28]),
      v[29] !== c || v[30] !== u || v[31] !== g || v[32] !== h
        ? ((w = (0, r.jsx)("div", {
            className: g,
            style: u,
            ref: c,
            children: h,
          })),
          (v[29] = c),
          (v[30] = u),
          (v[31] = g),
          (v[32] = h),
          (v[33] = w))
        : (w = v[33]),
      w
    );
  }
  return function (e) {
    let o,
      a,
      i,
      d,
      l,
      u,
      y = (0, s.c)(13);
    if (
      (y[0] !== e
        ? (({ src: l, address: o, ipfsPrefix: a, isAnonymous: i, ...d } = e),
          (y[0] = e),
          (y[1] = o),
          (y[2] = a),
          (y[3] = i),
          (y[4] = d),
          (y[5] = l))
        : ((o = y[1]), (a = y[2]), (i = y[3]), (d = y[4]), (l = y[5])),
      !i && o && (!l || l === t.A))
    ) {
      let e;
      return (
        y[6] !== o || y[7] !== d
          ? ((e = (0, r.jsx)(c, { address: o, ...d })),
            (y[6] = o),
            (y[7] = d),
            (y[8] = e))
          : (e = y[8]),
        e
      );
    }
    return (
      y[9] !== a || y[10] !== d || y[11] !== l
        ? ((u = (0, r.jsx)(n, { src: l, ipfsPrefix: a, ...d })),
          (y[9] = a),
          (y[10] = d),
          (y[11] = l),
          (y[12] = u))
        : (u = y[12]),
      u
    );
  };
}
