// Source-adapted original language workflow. All browser/provider capabilities are explicit.
export function createLocaleCatalog() {
  let t = {
      en: { label: "English", englishLabel: "English", flag: "🇺🇸" },
      zh: { label: "中文", englishLabel: "Chinese (simplified)", flag: "🇨🇳" },
      fr: { label: "Français", englishLabel: "French (Europe)", flag: "🇫🇷" },
      de: { label: "Deutsch", englishLabel: "German", flag: "🇩🇪" },
      ru: { label: "Русский", englishLabel: "Russian", flag: "🇷🇺" },
      es: {
        label: "Español",
        englishLabel: "Spanish (Latin America)",
        flag: "🇪🇸",
      },
      pt: {
        label: "Português",
        englishLabel: "Portuguese (Brazil)",
        flag: "🇧🇷",
      },
      tr: { label: "Türkçe", englishLabel: "Turkish", flag: "🇹🇷" },
      ar: { label: "العربية", englishLabel: "Arabic", flag: "🇸🇦" },
      it: { label: "Italiano", englishLabel: "Italian", flag: "🇮🇹" },
      vi: { label: "Tiếng Việt", englishLabel: "Vietnamese", flag: "🇻🇳" },
      ko: { label: "한국어", englishLabel: "Korean", flag: "🇰🇷" },
      uk: { label: "Українська", englishLabel: "Ukrainian", flag: "🇺🇦" },
      th: { label: "ไทย", englishLabel: "Thai", flag: "🇹🇭" },
      he: { label: "עברית", englishLabel: "Hebrew", flag: "🇮🇱" },
      pl: { label: "Polski", englishLabel: "Polish", flag: "🇵🇱" },
      nl: { label: "Nederlands", englishLabel: "Dutch", flag: "🇳🇱" },
      ro: { label: "Română", englishLabel: "Romanian", flag: "🇷🇴" },
      cs: { label: "Čeština", englishLabel: "Czech", flag: "🇨🇿" },
      fa: { label: "فارسی", englishLabel: "Persian", flag: "🇮🇷" },
      el: { label: "Ελληνικά", englishLabel: "Greek", flag: "🇬🇷" },
      ja: { label: "日本語", englishLabel: "Japanese", flag: "🇯🇵" },
      hu: { label: "Magyar", englishLabel: "Hungarian", flag: "🇭🇺" },
      bg: { label: "Български", englishLabel: "Bulgarian", flag: "🇧🇬" },
      sk: { label: "Slovenčina", englishLabel: "Slovak", flag: "🇸🇰" },
      sv: { label: "Svenska", englishLabel: "Swedish", flag: "🇸🇪" },
      hr: { label: "Hrvatski", englishLabel: "Croatian", flag: "🇭🇷" },
      fi: { label: "Suomi", englishLabel: "Finnish", flag: "🇫🇮" },
      nb: {
        label: "Norsk",
        englishLabel: "Norwegian (Bokmål)",
        flag: "🇳🇴",
        aliases: ["no"],
      },
      da: { label: "Dansk", englishLabel: "Danish", flag: "🇩🇰" },
      sl: { label: "Slovenščina", englishLabel: "Slovenian", flag: "🇸🇮" },
      sr: { label: "Српски", englishLabel: "Serbian", flag: "🇷🇸" },
      lt: { label: "Lietuvių", englishLabel: "Lithuanian", flag: "🇱🇹" },
      lv: { label: "Latviešu", englishLabel: "Latvian", flag: "🇱🇻" },
      et: { label: "Eesti", englishLabel: "Estonian", flag: "🇪🇪" },
    },
    n = Object.keys(t),
    r = new Map(
      Object.entries(t).flatMap(([e, { aliases: t }]) =>
        (t ?? []).map((t) => [t, e]),
      ),
    );
  return {
    metadata: t,
    locales: n,
    defaultLocale: "en",
    normalizeLocale: (e) => {
      if (!e) return null;
      let n = e.trim().toLowerCase();
      if (!n) return null;
      if (Object.hasOwn(t, n)) return n;
      let a = r.get(n);
      if (a) return a;
      let i = n.split("-", 1)[0];
      return i === n ? null : Object.hasOwn(t, i) ? i : (r.get(i) ?? null);
    },
  };
}
export function createLocaleCookie({ document, location, normalizeLocale }) {
  const t = { v: normalizeLocale };
  let n = "pump_locale",
    r = (e) => (0, t.v)(e),
    a = (e) => {
      if (!e) return null;
      for (let t of e.split(";")) {
        let [e, ...a] = t.trim().split("=");
        if (e === n && a.length > 0) return r(decodeURIComponent(a.join("=")));
      }
      return null;
    };
  return {
    parseHeader: a,
    readCookie: () => ("u" < typeof document ? null : a(document.cookie)),
    writeCookie: (e) => {
      if ("u" < typeof document) return;
      let t = "https:" === location.protocol ? "; secure" : "";
      document.cookie = `${n}=${e}; path=/; max-age=31536000; samesite=lax${t}`;
    },
  };
}
export function createLanguageClient({ fetch, logger, writeCookie }) {
  const t = { y: logger },
    n = { E: writeCookie };
  function r(e) {
    return e instanceof Error ? `${e.name}: ${e.message}` : String(e);
  }
  let a = "translation";
  async function i(e, t) {
    let r = new URLSearchParams({ ns: t.join(",") }),
      n = await fetch(`/api/i18n/${e}?${r}`);
    if (!n.ok) throw Error(`i18n namespace fetch failed: ${n.status}`);
    return await n.json();
  }
  async function o(e, t, r) {
    let n = r.filter((r) => !e.getResource(t, a, r));
    if (0 === n.length) return;
    let o = await i(t, n);
    e.addResourceBundle(t, a, o, !0, !0);
  }
  let s = new WeakMap();
  async function l(e, n) {
    let i = s.get(e);
    if ((i || ((i = new Set()), s.set(e, i)), !i.has(n))) {
      i.add(n);
      try {
        let t = await fetch(`/api/i18n/${n}?ns=__all__`);
        if (!t.ok) throw Error(`i18n catalog fetch: ${t.status}`);
        let r = await t.json();
        e.addResourceBundle(n, a, r, !0, !0);
      } catch (e) {
        (i.delete(n),
          t.y.warn("i18n: idle full-catalog prefetch failed", {
            locale: n,
            reason: r(e),
            error: e,
          }));
      }
    }
  }
  async function c({ instance: e, locale: a, namespaces: i, router: s }) {
    try {
      (await l(e, a), await o(e, a, i));
    } catch (e) {
      t.y.warn("i18n: namespace seed before language switch failed", {
        locale: a,
        reason: r(e),
        error: e,
      });
    }
    ((0, n.E)(a), await e.changeLanguage(a), s.refresh());
  }
  return {
    namespace: a,
    seedNamespaces: o,
    prefetchCatalog: l,
    changeLanguage: c,
  };
}
export function createLanguageSelector({
  jsx,
  jsxs,
  useMemoCache,
  useState,
  useTransition,
  useTranslation,
  useRouter,
  select,
  catalog,
  changeLanguage,
}) {
  const t = { jsx, jsxs },
    i = { c: useMemoCache },
    l = { useRouter },
    n = { useState, useTransition },
    a = { f: useTranslation },
    r = {
      d: select.Root,
      P: select.Trigger,
      U: select.Value,
      r: select.Content,
      T: select.Item,
    },
    s = { C: changeLanguage },
    c = {
      L: catalog.metadata,
      O: catalog.locales,
      T: catalog.defaultLocale,
      v: catalog.normalizeLocale,
    },
    d = { T: (e, t) => e };
  let o = [
    "account",
    "advanced_search.tabs",
    "common",
    "geo_block",
    "home.tabs",
    "home.movers",
    "numbers",
    "profile.recently_viewed",
    "search",
    "settings",
    "time",
    "web.account",
    "web.app_update",
    "web.auth",
    "web.common",
    "web.consent",
    "web.errors",
    "web.fees",
    "web.footer",
    "web.geo_block",
    "web.info_bar",
    "web.leave_site",
    "web.nav",
    "web.notifications",
    "web.achievements",
    "web.pagination",
    "web.search",
    "web.session",
    "web.settings",
    "web.sidebar",
    "web.wallets",
    "web.tos",
    "web.topbar",
    "web.ui",
    "web.upsell",
    "web.wallet",
    "web.wallet_deprecation",
  ];
  function u(e) {
    let i = c.L[e],
      l = i.englishLabel !== i.label;
    return (0, t.jsx)(
      r.T,
      {
        value: e,
        textValue: i.label,
        "data-testid": `language-option-${e}`,
        children: (0, t.jsxs)("span", {
          className: "flex items-baseline gap-2",
          children: [
            (0, t.jsx)("span", { "aria-hidden": !0, children: i.flag }),
            (0, t.jsx)("span", {
              className: "text-sm font-medium",
              children: (0, d.T)(i.label, "language-value"),
            }),
            l
              ? (0, t.jsx)("span", {
                  className: "text-xs text-text-tertiary",
                  children: (0, d.T)(i.englishLabel, "language-value"),
                })
              : null,
          ],
        }),
      },
      e,
    );
  }
  return function (e) {
    let x,
      m,
      f,
      b,
      p,
      _,
      g,
      h,
      y,
      w = (0, i.c)(27),
      { className: j } = e,
      { i18n: k } = (0, a.f)(),
      { refresh: v } = (0, l.useRouter)(),
      [N, C] = (0, n.useState)(null),
      [T, S] = (0, n.useTransition)(),
      O = null !== N || T;
    w[0] !== k.language
      ? ((x = (0, c.v)(k.language) ?? c.T), (w[0] = k.language), (w[1] = x))
      : (x = w[1]);
    let L = x,
      A = c.L[L];
    w[2] !== L || w[3] !== k || w[4] !== O || w[5] !== v
      ? ((m = (e) => {
          let t = (0, c.v)(e);
          t &&
            t !== L &&
            !O &&
            (C(t),
            (0, s.C)({
              instance: k,
              locale: t,
              namespaces: o,
              router: { refresh: () => S(() => v()) },
            }).finally(() => {
              C(null);
            }));
        }),
        (w[2] = L),
        (w[3] = k),
        (w[4] = O),
        (w[5] = v),
        (w[6] = m))
      : (m = w[6]);
    let E = m,
      D = O || void 0,
      I =
        j ??
        "h-11 w-full rounded-md border-border-tertiary bg-bg-tertiary px-3 text-sm text-text-primary shadow-none";
    return (
      w[7] !== A.flag || w[8] !== O
        ? ((f = O
            ? (0, t.jsx)("span", {
                "aria-hidden": !0,
                className:
                  "size-4 animate-spin rounded-full border-2 border-current border-t-transparent text-text-tertiary",
              })
            : (0, t.jsx)("span", { "aria-hidden": !0, children: A.flag })),
          (w[7] = A.flag),
          (w[8] = O),
          (w[9] = f))
        : (f = w[9]),
      w[10] !== A.label
        ? ((b = (0, d.T)(A.label, "language-value")),
          (w[10] = A.label),
          (w[11] = b))
        : (b = w[11]),
      w[12] !== b
        ? ((p = (0, t.jsx)("span", { className: "font-medium", children: b })),
          (w[12] = b),
          (w[13] = p))
        : (p = w[13]),
      w[14] !== f || w[15] !== p
        ? ((_ = (0, t.jsx)(r.U, {
            children: (0, t.jsxs)("span", {
              className: "flex items-center gap-2",
              children: [f, p],
            }),
          })),
          (w[14] = f),
          (w[15] = p),
          (w[16] = _))
        : (_ = w[16]),
      w[17] !== D || w[18] !== I || w[19] !== _
        ? ((g = (0, t.jsx)(r.P, {
            "aria-busy": D,
            "data-testid": "language-select-trigger",
            className: I,
            chevronClassName: "size-3 text-text-quaternary opacity-100",
            children: _,
          })),
          (w[17] = D),
          (w[18] = I),
          (w[19] = _),
          (w[20] = g))
        : (g = w[20]),
      w[21] === Symbol.for("react.memo_cache_sentinel")
        ? ((h = (0, t.jsx)(r.r, {
            className:
              "max-h-[min(var(--radix-select-content-available-height),480px)]",
            children: c.O.map(u),
          })),
          (w[21] = h))
        : (h = w[21]),
      w[22] !== L || w[23] !== E || w[24] !== O || w[25] !== g
        ? ((y = (0, t.jsxs)(r.d, {
            value: L,
            onValueChange: E,
            disabled: O,
            children: [g, h],
          })),
          (w[22] = L),
          (w[23] = E),
          (w[24] = O),
          (w[25] = g),
          (w[26] = y))
        : (y = w[26]),
      y
    );
  };
}
