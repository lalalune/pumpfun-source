# Main `/live` row carousel and geometry

This editable source unit closes the full main-page `647145.X` → `1074.Carousel` row boundary, including `502540.f` responsive width formulas, one-way per-card viewport admission and all three used measurement/selection/snap hooks (`798394`/`70678`/`65769`). The original factories are authenticated and parsed only, never evaluated. The generator emits complete selected functions/locals/export expressions, preserving their effects, refs, callbacks and cleanup.

Observed `https://pump.fun/live` HTML/Flight binds `31113` → `944001`/`310766` → `647145.X` and its actual row props. All eight selected factory contexts have one indexed physical origin; the actual initial scripts are retained. This is a static contextual binding, not an active runtime winner or mounted application result. Main Rows leaves selectedIndex and onSnapIndexChange undefined; the generic Carousel supports those props, but a test supplying them is an **authored caller**, not an observed main-page interaction.

## API and boundaries

`createLiveRowCarousel({React,jsx,compiler,classNames,Card,cardCounts,dom})` returns `Rows`, `Carousel`, `cardWidths`, `useGeometry`, `useSelection` and `useSnap`. Required capabilities bind actual React352386, JSX732486, compiler445242/532815, classnames426091.c, complete763145.Card presentation/navigation and the three DOM observer constructors. `cardCounts` supplies the existing [1821](https://github.com/lalalune/pumpfun-source/pull/1821) API values (2/3/4), witnessed rather than copied or claimed again. `Rows` preserves full source Card props and overrides index with actual map order.

Card/provider/navigation/account/media/coin-page behavior remains an exact source-bound port. No original Card is rendered by this qualification, no links are navigated and no provider/media acquisition occurs. [1897](https://github.com/lalalune/pumpfun-source/pull/1897) owns the main/section query/unlock/near-end caller; [1879](https://github.com/lalalune/pumpfun-source/pull/1879) owns the separate hero carousel. Their operations and 1570/1617 archive work retain attribution.

## Preserved source behavior

- Widths use all three source card counts and gap formulas, with the original below-one rejection. The first child wrapper's offsetWidth plus gap is measured, not inferred from a guessed breakpoint.
- ResizeObserver snaps to the nearest current offset with `instant`; MutationObserver remeasures child-list changes. Both disconnect on cleanup/gap replacement.
- Selection skips undefined index/null width, tracks previous selection and preserves the source optional skip-policy behavior. Carousel itself supplies no skip policy. Snap uses natural scrollend, a latest callback ref, zero-width guard and exact listener removal. The source effect depends on scrollRef/width, not callback identity or presence; no scheduling/policy correction is invented.
- Non-eager cards start with empty wrappers. Native admission uses the scroll-root margin `0px 300px 0px 300px`; after first intersection, seen is one-way and the observer disconnects. Eager mode bypasses that component.
- Near-end uses the latest callback ref and source dependencies. Scroll-root mode uses `0px 200px 200px 0px`; viewport mode uses null root and `0px 0px 400px 0px`. Child-count, root-mode and wrapper-class changes can recreate it. No fetch/query/paging lifecycle is added.

## Replay and proof limits

From a checkout with pinned app dependencies:

```sh
cd app
node reconstruction/live-row-carousel/recover.mjs --check
node --test tests/live_row_carousel.test.mjs
node reconstruction/live-row-carousel/browser.mjs --output /absolute/new/output-directory
```

`--write` regenerates the adapter/provenance; `recover(appRoot)`/`verify(appRoot)` allow a minimal explicit public-input export. Tests copy only declared repository files and link available installed dependencies, without private workfiles or open-PR implementations.

The finite method runs real React/compiler/DOM with delegated native observer/scroll implementations, but **authored container/card CSS and a synthetic Card**. It first exercises the actual main Rows adapter, then an explicitly authored generic-Carousel selection/snap caller. Instrumentation forwards native calls unchanged. Only loopback HTML/bundle GETs are allowed. This is no original CSS/layout, visual/native/application or service compatibility claim. Source, fixture, method and bundle inputs are frozen before runtime; later qualification records must state actual outcomes and failures.

## Finite qualification

Source verification and **six focused Node/real-React SSR/portable cases PASS** at `5e127c26894307c310e148844f9dd47a9bf6c4a7`. Its first real-React/native-observer story recorded **six passing observations, then a resize assertion failure**. The unchanged product source was checked again at corrected method `f8a263c89d3b1749a5c7b1954ea5340fb98eaaf7`, whose full **eight-observation story PASS** repeats the first six controls; this is not14 unique successes. Both raw attempts, method snapshots/diffs, full bundles, traces and cleanup are retained in [qualification](qualification/README.md).

The corrected passive native callback sample was offset1632, first-child width392 and gap16, followed by the actual source's instant-scroll1632. The original failure's callback operands were not measured; exact native CSS causation remains unproven. No source, geometry input or timing was changed to force the expectation. App698/npm/SDK, progress/nine tests and exact corrected-head53Git/9captures/10tooling checks passed. The initial sparse-progress-input failure and exact Git restoration are preserved separately. Later README/packet additions do not relabel the two measured cohorts.
