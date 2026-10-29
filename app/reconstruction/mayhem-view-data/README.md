# Mayhem live-state and page-data boundary

This editable source reconstructs the pure data operations inside captured
`457065` (`MayhemScreener`): the complete live mode/state update callback, its
event callback, and the joins from served coins and provider snapshots to ordered
ten-row pages and row-display inputs. The maintained `mayhem-data.ts` handles a
different, synthetic DTO and sorter; it does not contain this state reducer or
these provider joins and page handoffs.

This unit adds no mounted component, endpoint, provider, socket, cache, retry
policy or native adapter. It does not consume the one-response research capture
from #1759. The earlier parent/request/SSR attribution is credited to that packet;
the new work is the state and complete pure view-data flow. No progress status,
count, denominator or compatibility claim changes.

## Use

```js
import { createMayhemUpdate, createMayhemEvent, deriveMayhemView }
  from './view.mjs';

// `set` is the owning store's set capability. The original update operation
// receives the current root and returns that same root or a { byMint } partial.
const update = createMayhemUpdate(set);
const onMayhemEvent = createMayhemEvent(update);

const view = deriveMayhemView({
  data: servedCoins,                 // actual query array, or null/undefined
  hydratedCoins: normalizedCoins,    // already delivered by 609252.f
  marketActivity: activityByMint,    // already delivered by 849812.b
  byMint: modeStateSnapshot.byMint,
  coinState: liveCoinSnapshot,       // 653805-style { coins: { [mint]: ... } }
  sort: 'lastTraded', pageIndex: 0,
  isLoading: false, isError: false, paused: false,
});
// Consumer-owned: apply view.pageIndexCorrection when it is defined; pass
// view.visibleMints and view.subscribeVisible to an actual subscription provider.
```

All names in this facade and its result objects are descriptive local names,
not recovered original TypeScript names. `body`, `marketCapPositive`,
`modeTranslationKey`, `volumePresent` and `pageIndexCorrection` expose source
decisions without implementing JSX, number formatting, translation or React
setters. An absent translation key corresponds to the captured em-dash branch.
The input boundary deliberately adds no schema parser or invented defaults for
missing provider snapshots. Malformed values can throw as the captured operations
do; the successful response DTO declaration is not a runtime validation oracle.

## Source behavior retained

- The live reducer starts from an empty `byMint` object. Partial updates merge
  both fields using `??`. An existing unchanged entry returns the exact old root;
  a new mint with both fields absent still gets an entry. Live state/mode values
  are not enum-validated. The event callback only requires a truthy `mint`.
- Changed entries copy other keys with `for...in`, reinsert the changed key and
  cap through `Object.keys(...).slice(...)`. This is JavaScript enumeration,
  including enumerable inherited keys and integer-like ordering. It is not a
  generic LRU: an integer-looking newly added key can be evicted immediately.
- Served query coins remain the base row objects. Their mints feed the activity
  provider and the hydration descriptor: limit `Math.max(1, mints.length)`,
  `includeNsfw: true`, and disabled for no mints. Hydrated coins only build a mode
  fallback map. Its admission gate is the actual `auto`/`manual` enum; later valid
  duplicates replace earlier values, and later invalid values do not clear them.
- `volume` sorts by the delivered `24h.volumeUSD ?? 0`; `mcap` and `newest` sort
  by base-response fields with the original nullish-zero fallback. Ties preserve
  served order. Default/`lastTraded` returns the served array itself, without a
  timestamp sort or mint tie-breaker. Live caps do not influence sorting.
- Page count is at least one; the current page is clamped only at the upper end.
  The captured control handlers produce nonnegative integer state. Ten-row
  slices determine absolute ranks and visible subscription inputs. Loading then
  error then empty take body precedence, while the visible-mint handoff is still
  computed. Pagination is hidden during loading/error or at ten rows or fewer.
- Rows join `24h` activity, live state/mode, and a separate live-cap selector.
  State/mode use nullish fallbacks; live cap falls back only for **undefined**,
  so null and zero override a positive base cap. Zero volume is present. Unknown
  truthy live modes use the captured auto translation key. Trend defaults to
  gain for missing change, and telemetry retains the base cap rather than the
  live display cap.

`pageIndex` is the supplied current-render state. The captured filter/sort
callbacks separately reset it to zero. The facade does not reconstruct those
controls, hover/refetch effects, store scheduling, memo-cache identities,
subscription lifecycle, navigation, telemetry delivery, charts or rendering.
It returns `!paused && 10000` as data, without starting a timer or issuing a read.

## Attribution and provider closure

`PROVENANCE.json` authenticates the existing manifest/index and raw registration
ranges, with URL, object/factory SHA-256, UTF-16 and UTF-8 half-open ranges. The
verifier parses inert syntax and never imports/evaluates a captured factory.

| Boundary | Exact captured provenance and limit |
| --- | --- |
| Owning parent | The sole `457065/fdc0ca7368bc…` variant, raw `b5dd8c92e81b5961.js`; complete parent, row helpers, updater and event callback retained as range witnesses. |
| Hydration mode enum | Actual `457065 → 402030.MAYHEM_MODES` getter → `540480`, then `['auto', 'manual']`; no assumed numeric-ID alias. |
| Hydrated coins | All nine physical `609252` variants and their actual `493025.f` imports/calls retained. The accepted [search-session normalizer](../search-session/session.mjs) already reconstructs `493025`/`426091`; it is an upstream dependency, not new recovery here. The Mayhem-page chunk's candidate is `609252/c331cdee0726…`. No global runtime winner is inferred. |
| Activity | All four `849812` variants are retained (`8e943b08`, `3b8b0b59`, `49ebaebc`, `e3bb5a03`), with actual `26077` response-normalizer and `680930` merge imports. All six physical merge variants and the normalizer factory bind the delivered record contract. The page-chunk candidate is `e3bb5a03`. Fetching, query/cache orchestration and the activity POST service are outside this unit. |
| Live cap | Complete `653805.J` selector boundary binds `coins[mint]?.usdMarketCap`; store queues, clocks and updates are external. |
| Visible mints | The actual grouped export `915631.f`, distinct from its factory's `949629.f`, and the parent's actual call/arguments are bound. Subscription transport/lifecycle remains external. |

The verifier structurally compares complete update/event callbacks, comparator
and mint-reader bodies, the hydrated mode-map loop, and the listed join/page/
display expressions. Only recorded identifier substitutions and boolean spelling
normalization are used. Other complete callbacks remain immutable range witnesses;
the entire descriptive facade is hash-bound and exercised below. These are
bounded expression/callback checks, not a universal equivalence proof of the
compiled React component or its dependency graph.

## Reproduce offline

From `app/` with the repository's existing pinned dependencies:

```sh
node reconstruction/mayhem-view-data/verify.mjs --check
node --test tests/mayhem_view_data.test.mjs tests/original_source.test.mjs
node --experimental-strip-types --test tests/mayhem_screener.test.ts tests/mayhem-missing-sort.test.mjs
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
```

From the repository root:

```sh
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

The twelve new tests execute only this editable source: complete state/event and
snapshot-to-page/row flows, ordering/reference behavior, shrinking-result pages,
and raw-input/variant/adapter corruption. An independent temporary path with
spaces contains only the required public manifest, index, raw objects, model and
proof; verification does not need formatted modules, private work files or the
#1759 live response. Original captures and earlier packets remain unchanged.

Run `node reconstruction/mayhem-view-data/verify.mjs --write` only after deliberate
source review to regenerate provenance. It still enforces the original callback
and expression comparisons before writing. See `VALIDATION.json` and compressed
logs for exact tested inputs and the distinction between source tests and
unclaimed UI/network behavior. Original shipped JavaScript retains its authorship.
