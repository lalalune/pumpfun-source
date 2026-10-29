// Source-adapted full original search/results component. Explicit module-lifetime ports only.
export function createSettingsSearchResults({
  jsx,
  jsxs,
  useMemoCache,
  useTranslation,
  translateKey,
  useHiddenSettingIds,
  registry,
  sections,
  Field,
  Section,
}) {
  const t = { jsx, jsxs },
    i = { c: useMemoCache },
    l = { f: useTranslation },
    K = { f: translateKey },
    T = { X: Section },
    ep = { g: registry },
    ey = { n: sections },
    ed = Field,
    eh = useHiddenSettingIds;
  let ef = (e) =>
    e.toLocaleLowerCase().normalize("NFKD").replace(/\p{M}/gu, "");
  function eb(e) {
    let r,
      s,
      n,
      a,
      o,
      c,
      d,
      x = (0, i.c)(31),
      { query: u, visibleSections: m } = e,
      { t: h } = (0, l.f)(),
      p = eh();
    x[0] !== h
      ? ((r = (e) => {
          let t = ey.n.find((t) => t.id === e);
          return t ? (0, K.f)(h, t.labelKey) : e;
        }),
        (x[0] = h),
        (x[1] = r))
      : (r = x[1]);
    let f = r;
    if (x[2] !== p || x[3] !== u || x[4] !== f || x[5] !== h || x[6] !== m) {
      c = Symbol.for("react.early_return_sentinel");
      e: {
        let e, i, r;
        (x[12] !== p || x[13] !== m
          ? ((e = (e) => m.includes(e.section) && !p.has(e.id)),
            (x[12] = p),
            (x[13] = m),
            (x[14] = e))
          : (e = x[14]),
          x[15] !== h
            ? ((i = (e) => (0, K.f)(h, e)), (x[15] = h), (x[16] = i))
            : (i = x[16]),
          x[17] !== f
            ? ((r = (e) => f(e.section)), (x[17] = f), (x[18] = r))
            : (r = x[18]));
        let l = (({
          query: e,
          definitions: t,
          translate: i,
          sectionLabelOf: r,
        }) => {
          let s = ef(e).split(/\s+/).filter(Boolean);
          return 0 === s.length
            ? []
            : t.filter((e) => {
                if ("hidden" === e.control.kind) return !1;
                let t = (({ definition: e, translate: t, sectionLabel: i }) =>
                  ef(
                    [
                      t(e.labelKey),
                      e.descriptionKey ? t(e.descriptionKey) : "",
                      ...(e.searchTerms ?? []),
                      i,
                      e.id.replace(/[.]/g, " "),
                    ].join(" "),
                  ))({ definition: e, translate: i, sectionLabel: r(e) });
                return s.every((e) => t.includes(e));
              });
        })({
          query: u,
          definitions: ep.g.filter(e),
          translate: i,
          sectionLabelOf: r,
        });
        if (0 === l.length) {
          let e, i;
          (x[19] !== u || x[20] !== h
            ? ((e = h("web.settings.search_empty", { query: u })),
              (x[19] = u),
              (x[20] = h),
              (x[21] = e))
            : (e = x[21]),
            x[22] !== e
              ? ((i = (0, t.jsx)("p", {
                  role: "status",
                  className:
                    "px-1 py-12 text-center text-sm text-text-tertiary",
                  children: e,
                })),
                (x[22] = e),
                (x[23] = i))
              : (i = x[23]),
            (c = i));
          break e;
        }
        let d = new Map();
        for (let e of l) {
          let t = d.get(e.section) ?? [];
          (t.push(e), d.set(e.section, t));
        }
        ((s = "region"),
          x[24] !== h
            ? ((n = h("web.settings.search_results")), (x[24] = h), (x[25] = n))
            : (n = x[25]),
          (a = "flex flex-col gap-7 pt-1"),
          (o = ey.n
            .filter((e) => d.has(e.id))
            .map((e) =>
              (0, t.jsx)(
                T.X,
                {
                  label: (0, K.f)(h, e.labelKey),
                  children: (d.get(e.id) ?? []).map(eg),
                },
                e.id,
              ),
            )));
      }
      ((x[2] = p),
        (x[3] = u),
        (x[4] = f),
        (x[5] = h),
        (x[6] = m),
        (x[7] = s),
        (x[8] = n),
        (x[9] = a),
        (x[10] = o),
        (x[11] = c));
    } else ((s = x[7]), (n = x[8]), (a = x[9]), (o = x[10]), (c = x[11]));
    return c !== Symbol.for("react.early_return_sentinel")
      ? c
      : (x[26] !== s || x[27] !== n || x[28] !== a || x[29] !== o
          ? ((d = (0, t.jsx)("div", {
              role: s,
              "aria-label": n,
              className: a,
              children: o,
            })),
            (x[26] = s),
            (x[27] = n),
            (x[28] = a),
            (x[29] = o),
            (x[30] = d))
          : (d = x[30]),
        d);
  }
  function eg(e) {
    return (0, t.jsx)(ed, { definition: e }, e.id);
  }
  return eb;
}
