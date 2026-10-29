import { createHelper as v0 } from "./variants/squad-35ee9b42b219.mjs";
import { createHelper as v1 } from "./variants/squad-4043938d1f35.mjs";
import { createHelper as v2 } from "./variants/image-1877fed09a63.mjs";
import { createHelper as v3 } from "./variants/image-64085dc31cc9.mjs";
import { createHelper as v4 } from "./variants/image-9fa49ca7090d.mjs";
export const squadVariants = Object.freeze([
  {
    sha256: "35ee9b42b2197b69c4f65475eaafa8097929e9e2e1f0657cce4fc2d79565d075",
    path: "packages/frontend/src/components/leaderboard/entry/variants/squad-35ee9b42b219.mjs",
    source: "evidence/web/objects/da58569257a3fbc5.js",
  },
  {
    sha256: "4043938d1f3547190132378541afc93d48c24d0dc55898853f2b2b987071eeb1",
    path: "packages/frontend/src/components/leaderboard/entry/variants/squad-4043938d1f35.mjs",
    source: "evidence/web/objects/ea5d7a76f15713d7.js",
  },
]);
export const imageVariants = Object.freeze([
  {
    sha256: "1877fed09a6363588057a816a53c9d14fa46d3a3cb285321349a29a6ce48812a",
    path: "packages/frontend/src/components/leaderboard/entry/variants/image-1877fed09a63.mjs",
    source: "evidence/web/objects/257d1f445453cc81.js",
  },
  {
    sha256: "64085dc31cc9ebbcde019719b8096cfd198d84216b08826b70461fdfa689dc55",
    path: "packages/frontend/src/components/leaderboard/entry/variants/image-64085dc31cc9.mjs",
    source: "evidence/web/objects/ea5d7a76f15713d7.js",
  },
  {
    sha256: "9fa49ca7090d955ed1650833d4a5adb620e11fd63ee88437701c50bd419832a2",
    path: "packages/frontend/src/components/leaderboard/entry/variants/image-9fa49ca7090d.mjs",
    source: "evidence/web/objects/0746572aecdcf595.js",
  },
]);
const squads = new Map([
    ["35ee9b42b2197b69c4f65475eaafa8097929e9e2e1f0657cce4fc2d79565d075", v0],
    ["4043938d1f3547190132378541afc93d48c24d0dc55898853f2b2b987071eeb1", v1],
  ]),
  images = new Map([
    ["1877fed09a6363588057a816a53c9d14fa46d3a3cb285321349a29a6ce48812a", v2],
    ["64085dc31cc9ebbcde019719b8096cfd198d84216b08826b70461fdfa689dc55", v3],
    ["9fa49ca7090d955ed1650833d4a5adb620e11fd63ee88437701c50bd419832a2", v4],
  ]);
export function createEntryHelpers({ squadVariant, imageVariant, Intl }) {
  const squad = squads.get(squadVariant),
    image = images.get(imageVariant);
  if (!squad || !image)
    throw new TypeError(
      "Explicit reviewed squad and image source hashes required",
    );
  function r(e) {
    if (null == e) return null;
    let t =
      "string" == typeof e ? e : e.address?.trim() || e.userId?.trim() || "";
    return t ? `/profile/${encodeURIComponent(t)}` : null;
  }
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
  return {
    profileHref: r,
    shortWallet: t,
    isVerified: (e) => e?.isVerified === !0 && !1 !== e.verifiedBadgeVisible,
    formatPnl: function (e) {
      return isNaN(e) || !isFinite(e)
        ? "$0.00"
        : new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }).format(e);
    },
    squadHref: squad(),
    normalizeImage: image({
      emptyImage:
        "https://pump.mypinata.cloud/ipfs/QmeSzchzEPqCU1jwTnsipwcBAeH7S4bmVvFGfF65iA1BY1",
    }),
    ipfsPrefix: "https://pump.mypinata.cloud/ipfs/",
  };
}
