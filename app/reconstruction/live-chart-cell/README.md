# Complete main `/live` ChartCell owner

This editable unit closes the complete `763145.Card → 454430.ChartCell` display family left external by [1939](https://github.com/lalalune/pumpfun-source/pull/1939): three Cell variants, four35-slot query owners, four loading/empty/error/memo renderers, five one-way viewport hooks, the client-ready hook and two48-slot lazy chart-library bridges. Original factories are authenticated/parsed only; maintained adapted functions execute in proof, raw captures do not.

Observed `https://pump.fun/live` HTML/Flight includes the actual main Card chain and initial `bf1738` Cell/query/renderer/IO context,170450 and179843 loader. Its three retained lazy chunks bind708937 namespace forwarding→832914.LineChartCellChart. All alternative physical contexts and lazy arrays remain explicit. Initial-script presence is static context, not a global active registration winner or proof that every variant executes on the main page. No individual token-detail page is recovered.

## Construction and actual ports

`createLiveChartCell({contexts,React,jsx,compiler,classNames,useQuery,helpers,eligibility,readOHLC,queryKeys,dynamic,loadModule,chartModules,dom})` returns `ChartCell`, `useCandlesticks`, `Display`, `useViewport`, `useClientReady` and `LineChartCellChart`. `CHART_VARIANTS` lists captured context hashes; caller explicitly chooses each owner, for example `MAIN_CAPTURE_CHART_CONTEXT` (the static observed main/lazy context, not an inferred runtime winner). All other capabilities are required source-compatible interfaces:

- React352386 supplies named hooks and default memo/useId exports; JSX732486, compiler445242/532815 and class helper338319.c remain supplied.
- `useQuery(options)` is actual690877; original query/cache/scheduling/retry execution is external. `eligibility({coinAddress,coinCreatedTimestamp,chainId})` is actual636882.f, not an invented resolver.
- `helpers.isYoungCoin`, `youngCandleWindow`, `defaultLineWindow`, `CHART_DEFAULTS` reuse [1827](https://github.com/lalalune/pumpfun-source/pull/1827)'s exact public APIs. They map to693908.a/S/Y and captured line defaults. No helper body is copied. `queryKeys` provides exact38279.Q.COIN_CANDLES/COIN_LINE_CHART constructors, retaining source argument and marker behavior.
- **`readOHLC(options)` is actual997627.u**, with all five complete source-context witnesses. It returns OHLC candlesticks, not `{time,price}` points.1827's `createSparklineReader` implements997627.B and is **not interchangeable**; it is never substituted. [1860](https://github.com/lalalune/pumpfun-source/pull/1860)'s505835 normalized transport/decoder is separately credited; this unit does not implement u normalization, candle/line service acquisition or new exports for private helpers.
- `dynamic(loader,options)` is actual453706.default; `loadModule(id)` is the source runtime's namespace interface `A(179843)`. The captured three-chunk loader and708937 interop remain inert evidence. Original resource loading/Next scheduling/provider behavior is unqualified. Caller may return this unit's `LineChartCellChart` namespace from its compatible loader; no original chunks execute.
- `chartModules` supplies actual source interfaces116368.f (Area),612531.f (chart constructor),671603.f (XAxis),25264.f (YAxis),998188.t (axis map),45143.f (responsive container),216934.f (palette). Source constructor configuration and primitive props are preserved; the chart library, rendering geometry, theme acquisition and financial correctness remain external.
- `dom.IntersectionObserver` supplies native-compatible observation. Its explicit undefined value preserves the actual unavailable-observer fallback; no silent capability default is invented.

Prior1939/1897/1928 callers,1821/1914 data boundaries,1879 hero/player and1570/1617 archive work retain attribution. No open PR implementation is silently imported or retallied.

## Preserved operations

170450.f is **client-ready/hydration admission**, not a remote feature flag: no-op subscription, true client snapshot, false server snapshot. ChartCell's320px native one-way viewport gate remains separate. Pending markup, React memo, coin/rest argument handoff and last-spread renderer overrides stay intact. Once seen, admission is not revoked for leaving viewport or a new coin in the same instance.

The35-slot query owner retains cached young classification by timestamp, independent later helper calls, candle/line key selection plus `sparklineCandlesticks`/nullish-chain suffix, nullish timestamp0, width/timeframe/stale/refetch options, eligibility, gc600000/retry1/delay2000 and falsey-data fallback. Extra generic options are not an invented override spread. Query function delegates unchanged to u; its current data/time behavior is supplied separately from memoized key classification.

Renderer loading wins, then error/missing/length≤1 gives the source dash; valid arrays go to the dynamic chart. Its actual custom comparator compares loading/error/className plus data length and **last.close only**. Other field/first.open changes can be suppressed; no correction is invented.

The48-slot chart bridge maps the first row's open and later rows' close, uses `time || timestamp`, strips useId colons, computes min/max and padding `(max-min)*.05 || .01*max`, creates the positive-color gradient and forwards exact nonanimated library props. It adds no sorting, deduplication, finite-data filtering or financial policy. Zero/negative-flat domain quirks remain. Library rendering, data validity and universal equivalence are not established by observing those props.

## Replay

```sh
cd app
node reconstruction/live-chart-cell/recover.mjs --check
node --test tests/live_chart_cell.test.mjs
node reconstruction/live-chart-cell/browser.mjs --output /absolute/new/output-directory
```

`--write` regenerates module/provenance. `recover(appRoot)`/`verify(appRoot)` also replay from a minimal public-input export, with no formatted factory/private files or unmerged implementation. All raw lazy assets are already retained; no new acquisition is required.

The finite host uses real React/compiler/native IO, with authored query snapshots/age results/eligibility/OHLC/lazy namespace/library/palette and layout ports. The source's actual lazy callback, data/memo/render props and observer state execute; no original services, financial data, library or resource loader executes. Only own loopback HTML/bundle GETs are allowed. No original CSS, mounted app, native/API/visual/financial/security or feature-completion claim. Freeze source/method/bundle inputs before proof and preserve failures/cleanup; later receipts describe actual finite outcomes.

## Finite result and preserved attempts

At source/Node freeze `d45a3e6f136faadd7e25e7f4aab7a2c207d8817a`, source CLI and **11 focused Node/real-React SSR/portable cases PASS**. Its first browser attempt passed one observation then failed loading-child visibility, leaving later steps unrun. The corrected `542c25f198a94f24f3817b3162e43c31e0f6bd0e` host passed **one nine-observation real-React/compiler/nativeIO story**, with zero page errors/non-host requests and explicit cleanup. The first control is a repeat, not10unique successes. Earlier `b07a8fec` had no browser run.

Exactly one authored host CSS rule supplied24px/56px to the already-present empty loading child; source, fixture, assertion and deadline stayed unchanged. This is fixture geometry, not original CSS/pixel/service qualification. The [packet](qualification/README.md) retains all three methods, both raw attempts/fullbundles/traces, failed screenshot, two method diffs and all14bundle inputs. App698/npm/SDK,53Git/9captures/10tooling atD45 and progress check/nine tests passed; initial sparse-progress failure and exact542Git restoration are separate. No query/data/library/media/provider service executes beyond the labeled synthetic ports, and no old result is retargeted to a later receipt-only head.
