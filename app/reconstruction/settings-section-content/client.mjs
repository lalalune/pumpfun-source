// Complete source-adapted original Settings section-content grouping/display owner.
export function createSettingsSectionContent({
  jsx,
  jsxs,
  useMemoCache,
  useTranslation,
  translateKey,
  useHiddenSettingIds,
  definitionsForSection,
  Section,
  Field,
  AccountHeader,
  NotificationSettingsSections,
  PrivacyFooter,
}) {
  const t = { jsx, jsxs },
    i = { c: useMemoCache },
    l = { f: useTranslation },
    K = { f: translateKey },
    ep = { n: definitionsForSection },
    T = { X: Section },
    ed = Field,
    eT = AccountHeader,
    ej = { NotificationSettingsSections },
    eW = PrivacyFooter,
    eh = useHiddenSettingIds;
  let ez = new Set([
      "trading.presets",
      "trading.autoApprove",
      "trading.priorityLevel",
    ]),
    eD = {
      trading: [
        { labelKey: "web.trade.execution", match: (e) => ez.has(e) },
        {
          labelKey: "web.trade.quick_buy",
          match: (e) =>
            e.startsWith("trading.quickBuy.") ||
            e.startsWith("trading.quickSell.") ||
            "trading.profileQuickTradeButtons" === e,
        },
        {
          labelKey: "coin_details.chart.settings.denomination",
          match: (e) =>
            e.startsWith("trading.paymentAsset.") ||
            e.startsWith("trading.inputUnit."),
        },
      ],
      chart: [
        { match: (e) => !e.startsWith("chart.markers.") },
        {
          labelKey: "web.settings.chart.bubbles",
          descriptionKey: "web.settings.chart.bubbles_description",
          compact: !0,
          match: (e) => e.startsWith("chart.markers."),
        },
      ],
    };
  function eM() {
    return !0;
  }
  function eL(e) {
    return (0, t.jsx)(ed, { definition: e }, e.id);
  }
  function eF(e) {
    let r,
      s,
      n,
      a,
      o,
      c,
      d = (0, i.c)(19),
      { section: x, onRequestClose: u } = e,
      { t: m } = (0, l.f)(),
      h = eh();
    if (d[0] !== h || d[1] !== u || d[2] !== x || d[3] !== m) {
      o = Symbol.for("react.early_return_sentinel");
      e: {
        var p;
        let e, i, l, c;
        d[9] !== h
          ? ((e = (e) => "hidden" !== e.control.kind && !h.has(e.id)),
            (d[9] = h),
            (d[10] = e))
          : (e = d[10]);
        let f = (0, ep.n)(x).filter(e);
        if ("notifications" === x) {
          let e;
          (d[11] === Symbol.for("react.memo_cache_sentinel")
            ? ((e = (0, t.jsx)("div", {
                className: "pt-1",
                children: (0, t.jsx)(ej.NotificationSettingsSections, {}),
              })),
              (d[11] = e))
            : (e = d[11]),
            (o = e));
          break e;
        }
        let y =
            ((p = eD[x] ?? [{ match: eM }]),
            (i = new Set()),
            (l = p.map((e) => {
              let t = f.filter((t) => !i.has(t.id) && e.match(t.id));
              for (let e of t) i.add(e.id);
              return { group: e, rows: t };
            })),
            (c = f.filter((e) => !i.has(e.id))).length > 0 &&
              l.push({ group: { match: () => !0 }, rows: c }),
            l.filter((e) => e.rows.length > 0)),
          b = y.map((e, i) => {
            let { group: r, rows: s } = e;
            return (0, t.jsxs)(
              T.X,
              {
                label: r.labelKey ? (0, K.f)(m, r.labelKey) : void 0,
                description: r.descriptionKey
                  ? (0, K.f)(m, r.descriptionKey)
                  : void 0,
                children: [
                  s.map((e) =>
                    (0, t.jsx)(ed, { definition: e, compact: r.compact }, e.id),
                  ),
                  "privacy" === x && i === y.length - 1
                    ? (0, t.jsx)(eW, { onOpen: u })
                    : null,
                ],
              },
              r.labelKey ?? `run-${i}`,
            );
          });
        ((r = `settings-section-${x}`),
          (s = "flex flex-col gap-7 pt-1"),
          d[12] !== x
            ? ((n = "account" === x ? (0, t.jsx)(eT, {}) : null),
              (d[12] = x),
              (d[13] = n))
            : (n = d[13]),
          (a =
            "account" === x && b.length > 0
              ? (0, t.jsx)(T.X, {
                  label: m("web.settings.account.profile"),
                  children: f.map(eL),
                })
              : b));
      }
      ((d[0] = h),
        (d[1] = u),
        (d[2] = x),
        (d[3] = m),
        (d[4] = r),
        (d[5] = s),
        (d[6] = n),
        (d[7] = a),
        (d[8] = o));
    } else ((r = d[4]), (s = d[5]), (n = d[6]), (a = d[7]), (o = d[8]));
    return o !== Symbol.for("react.early_return_sentinel")
      ? o
      : (d[14] !== r || d[15] !== s || d[16] !== n || d[17] !== a
          ? ((c = (0, t.jsxs)("div", {
              "data-testid": r,
              className: s,
              children: [n, a],
            })),
            (d[14] = r),
            (d[15] = s),
            (d[16] = n),
            (d[17] = a),
            (d[18] = c))
          : (c = d[18]),
        c);
  }
  return eF;
}
