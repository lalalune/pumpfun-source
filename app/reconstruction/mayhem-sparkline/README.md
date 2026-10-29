# Mayhem chart query, point delivery and SVG boundary

The captured Mayhem row has a complete sparkline path that was still confined to
compiled factories: `457065.G → h → 375676.f → 997627.B`, then the returned price
points determine the line, fill, gradient and placeholder. This unit supplies an
editable, explicit recomputation of that path, with source-authenticated provider
ports. It is distinct from the wallet-summary chart reader `58159` and the
Mayhem state/page flow in #1812.

The public API names are authored descriptions. The unit adds no page, mounted
component, chart service, financial calculation, network default, dataset or
native adapter, and does not consume #1759's one-response research fixture.
Current feature statuses/counts remain unchanged.

## Composition

```js
import { createSparklineReader, createMayhemSparkline } from './sparkline.mjs';

const readSparkline = createSparklineReader({
  resolveChain,       // actual 505835.U interface: ({mint, chainId}) -> chain|null
  readCandleHistory,  // actual 505835.Z normalized delivery: args -> {candles}
  readLineHistory,    // actual 505835.x normalized delivery: args -> {points}
  now,               // raw clock corresponding to Date.now
});
const recompute = createMayhemSparkline({
  readSparkline, now, adjustedNow,  // adjustedNow corresponds to 668487.t
  getQueryResult, useId,           // owning query result and React ID capabilities
  jsx, jsxs, mergeClassNames,      // actual JSX/class operations are external
});
const element = recompute({ mint, createdTimestamp, chainId, colorClassName, className });
```

History ports return the **normalized provider objects**, not `Response` objects
or raw HTTP JSON. Their actual implementations, request origins, retries,
relay/interval aggregation and transport are external, not fabricated here.
`getQueryResult(options)` returns the owning query result whose `data` is consumed
by the row. The query function remains lazy and all I/O belongs to the supplied
capability. JSX ports may return real elements or inspection descriptors; tests
use inspection descriptors and do not establish mounted UI behavior.

`recompute` is an explicit local facade, **not the original React hook or memo
cache**. The captured parent caches its timeframe by creation timestamp; the
planner separately caches its young-coin classification by timestamp/source and
other query computations by their dependencies. This facade computes a supplied
snapshot when called. It does not claim automatic age-based key changes, React
scheduling, memo identity, query execution, refetch timers or subscription
lifecycle. A host must supply the actual recomputation/scheduling boundary.

## Preserved data behavior

- The parent selects `6h`, `24h` or `1w` using the **adjusted** `668487.t` clock,
  only for a finite positive creation timestamp. Its query options use the
  separate `createdTimestamp > 0` enabled guard, 300,000 ms stale time,
  600,000 ms GC time and a 10-second refetch callback only while delivered data
  has at most one point. This callback returns false after two points.
- The provider uses **raw** `Date.now` samples independently. Young means a
  finite positive creation timestamp no more than one hour old, including
  future timestamps after age clamps to zero. Young candle intervals change at
  five, fifteen and thirty minutes. Default line timeframe/width have their own
  captured age thresholds. The parent timeframe override and provider width
  default remain separate.
- The query plan chooses candle or line keys with the original field order,
  `sparklineLineChartPoints` suffix, and `chainId ?? null` partition. Query
  options spread **after** computed `queryFn`/`queryKey`, so they can override
  both. Final enabled is still eligibility `&& (enabled ?? true)`. The generic
  TON timestamp exception is retained; the actual Mayhem enabled guard can
  still disable such a request.
- The reader resamples raw age when its query function runs. A key planned just
  before one hour can still be a candles key while the later reader chooses
  line points. There is no invented synchronization between these clocks or
  snapshots. Tests explicitly retain this boundary.
- Young deliveries pass through the actual candle wrapper's `String` conversion
  of OHLCV before `Number(close)`. The point filter keeps only finite numeric
  timestamps and finite nonnegative closes, including zero. It does not coerce
  timestamp strings. Old/explicitly non-candle reads pass the normalized line
  provider's `points` array through unchanged.
- The line mapper retains its timeframe regex, ordered first-fit resolutions,
  creation-bounded span, 1..300 count and 2..2000 maximum-point bounds. Unsupported
  timeframe text returns null; malformed non-string input can throw. Dependency
  errors propagate rather than creating points or a fallback transport.
- SVG x coordinates are **index-spaced**, not time-spaced. Prices map into the
  captured 80-percent vertical range with the original constant-price fallback.
  Line/fill strings, child order, gradient stops, URL reference, view box,
  `preserveAspectRatio`, stroke/vector attributes and hidden placeholder are
  retained. The supplied React ID is requested even for the placeholder.
- There is no extra point validator in the renderer. Nullish/short data yields
  the placeholder; an object lacking a usable `.map` can throw, and NaN prices
  can produce NaN coordinates. The actual normalized provider contract is the
  upstream boundary. This unit does not silently strengthen it or qualify an
  arbitrary financial response.

## Source and variant closure

`PROVENANCE.json` binds manifest/index hashes, full raw capture/factory hashes,
URLs and byte/UTF-16 ranges. Verification parses inert registrations; it never
executes original factories. The complete raw callbacks remain available through
their range witnesses.

| Actual boundary | Retained contexts |
| --- | --- |
| Row → chart | Sole `457065/fdc0ca7368bc…`, including actual `G → h` props and complete `h` callback. |
| Query planner | All three `375676` variants: `a12988ba`, `87ebb7ab`, `e52a57ef`. Complete query callback/key field substitution and option precedence are checked in every variant. |
| Age helpers/reader | All five physical grouped factories registering **636882**, **693908** and **997627**, with each qualified export distinguished. The shared page chunk's candidate is `67fd293f`. |
| Candle wrapper | All nine `349942` variants, including its actual import/call to `505835.Z`; page-chunk candidate `18f71154`. |
| Provider/mapper | One grouped factory registering **505835**, **442951**, **628731**. Actual `U/Z/x` delivery contracts and the complete parameter mapper are bound. No service/relay implementation is added. |
| Keys/eligibility/clock | Sole `38279` default/key constructors, `646908` TON predicate and `668487` adjusted-clock exports. The existing clock reconstruction in related **open** #1472 remains external; it is not copied or claimed as accepted main source. |

There are 22 unique physical factory contexts. No global active runtime winner is
selected merely because an ID occurs in a page chunk. The verifier performs 63
exact callback/expression/attribute comparisons, using recorded identifier/port
substitutions, explicit pure key-array constructor field substitution and boolean
spelling normalization. Other complete callbacks are retained as source witnesses
and checked through direct semantics; this is not whole-React or universal
structural equivalence.

## Offline checks

From `app/`, using the existing pinned dependencies:

```sh
node reconstruction/mayhem-sparkline/verify.mjs --check
node --test tests/mayhem_sparkline.test.mjs tests/original_source.test.mjs
node --experimental-strip-types --test tests/mayhem_screener.test.ts tests/mayhem-missing-sort.test.mjs
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
```

From the repository root:

```sh
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

The twelve new tests cover complete explicit caller → query → normalized
delivery → SVG flows, threshold and invalid-data branches, independent clock
samples, option overrides, exact error identity and source/adapter mutations.
All service values and inspection-renderer operations are explicit synthetic
test inputs; this is no API, browser, rendered-page or visual parity proof.
Verification also replays from public raw inputs in a temporary path with spaces,
without formatted factories or private work files. See `VALIDATION.json` for the
exact tested revision and retained logs. Regenerate provenance only after source
review with `node reconstruction/mayhem-sparkline/verify.mjs --write`.

Original shipped JavaScript retains its authorship. Original captures, SDK,
earlier source packets, runtime pages, ledgers and dependency files are preserved.
