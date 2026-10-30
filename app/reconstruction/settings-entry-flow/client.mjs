// Source-adapted original Settings URL/event/controller/mount owner. Capabilities are explicit.
export function createSettingsEntryFlow({
  window,
  URL,
  CustomEvent,
  jsx,
  useMemoCache,
  useEffect,
  useFeatureFlag,
  settingsFlag,
  parseAsStringEnum,
  parseAsString,
  useQueryStates,
  sectionIds,
  dynamic,
  loadModule,
}) {
  const event = (() => {
    let t = "pump:open-settings";
    return {
      eventName: t,
      openSettings: (e) => {
        let r = new URL(window.location.href);
        (r.searchParams.set("settings", e.section),
          e.settingId
            ? r.searchParams.set("setting", e.settingId)
            : r.searchParams.delete("setting"),
          window.history.replaceState(window.history.state, "", r),
          window.dispatchEvent(new CustomEvent(t, { detail: e })));
      },
    };
  })();
  const t = { jsx },
    r = { c: useMemoCache },
    a = { D: { WEB_SETTINGS_HUB: settingsFlag } },
    i = { k: useFeatureFlag },
    n = { default: dynamic },
    l = { useEffect },
    s = { b: parseAsStringEnum, d: parseAsString, i: useQueryStates },
    o = { m: sectionIds },
    d = { O: event.eventName },
    e = { A: loadModule };
  let c = { settings: (0, s.b)(o.m), setting: s.d };
  let u = (0, n.default)(() => e.A(298590).then((e) => e.SettingsModal), {
    loadableGenerated: { modules: [190147] },
    ssr: !1,
  });
  const SettingsModalHost = function () {
    let e,
      n,
      o,
      m = (0, r.c)(9),
      f = (0, i.k)(a.D.WEB_SETTINGS_HUB),
      {
        section: p,
        settingId: h,
        open: b,
        close: x,
      } = (() => {
        let e,
          t,
          a,
          i,
          n = (0, r.c)(10);
        n[0] === Symbol.for("react.memo_cache_sentinel")
          ? ((e = { history: "replace", clearOnDefault: !0 }), (n[0] = e))
          : (e = n[0]);
        let [l, o] = (0, s.i)(c, e),
          { settings: d, setting: u } = l;
        n[1] !== o
          ? ((t = (e, t) => {
              o({ settings: e, setting: t ?? null });
            }),
            (n[1] = o),
            (n[2] = t))
          : (t = n[2]);
        let m = t;
        n[3] !== o
          ? ((a = () => {
              o({ settings: null, setting: null });
            }),
            (n[3] = o),
            (n[4] = a))
          : (a = n[4]);
        let f = a;
        return (
          n[5] !== f || n[6] !== m || n[7] !== d || n[8] !== u
            ? ((i = { section: d, settingId: u, open: m, close: f }),
              (n[5] = f),
              (n[6] = m),
              (n[7] = d),
              (n[8] = u),
              (n[9] = i))
            : (i = n[9]),
          i
        );
      })();
    return (m[0] !== f || m[1] !== b
      ? ((e = () => {
          if (!f) return;
          let e = (e) => {
            let { detail: t } = e;
            b(t.section, t.settingId);
          };
          return (
            window.addEventListener(d.O, e),
            () => window.removeEventListener(d.O, e)
          );
        }),
        (n = [f, b]),
        (m[0] = f),
        (m[1] = b),
        (m[2] = e),
        (m[3] = n))
      : ((e = m[2]), (n = m[3])),
    (0, l.useEffect)(e, n),
    f && p)
      ? (m[4] !== x || m[5] !== b || m[6] !== p || m[7] !== h
          ? ((o = (0, t.jsx)(u, {
              section: p,
              focusSettingId: h,
              onSectionChange: b,
              onClose: x,
            })),
            (m[4] = x),
            (m[5] = b),
            (m[6] = p),
            (m[7] = h),
            (m[8] = o))
          : (o = m[8]),
        o)
      : null;
  };
  return { ...event, SettingsModalHost };
}
