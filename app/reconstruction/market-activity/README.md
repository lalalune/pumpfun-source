# Captured Mayhem market-activity reader and owning query frame

The Mayhem parent **457065** calls **849812.b** with the mints projected from
its base query coins. The view-data reconstruction in #1812 receives the result
as an external activity input. This unit closes that distinct source boundary:
the complete batch reader, response normalization, batching, query descriptors,
combined state, manual batch refresh/cache write and invalidation callbacks.
It does not install a market service or mount a product feature.

All four physical 849812 factories and all six 680930 helper variants remain
explicit. The verifier authenticates their raw registration/range/hash bindings,
compares complete used operations and retains the full **31-slot compiler memo
frame**. Only used 680930 t/$/d exports, 26077.f's complete local dependency
closure and the actual 975982.k / 605587.h predicates are included. The existing
origin attribution and #1812 consumer receive no new recovery credit. No active
global provider winner is inferred.

## Explicit host capabilities

```js
import { createMarketActivityModule } from './client.mjs';

const activity = createMarketActivityModule({
  getBaseUrl: callerSelectedOrigin,
  fetchActivity: callerSelectedFetchCapability,
  logger: callerSelectedLogger,
  useMemoCache: callerSelectedCompilerMemoHook,
  useQueryClient: callerSelectedQueryClientHook,
  useQueries: callerSelectedQueriesHook,
  useMutation: callerSelectedMutationHook,
});
const state = activity.useMarketActivity(baseCoinMints);
// state.marketActivity / loading / error / refetchMints / invalidateCache
```

These capabilities correspond to actual imports, rather than invented services.
`getBaseUrl` replaces the ambient **503630.V** invocation; the captured selector
uses `new URL(version, 'https://swap-api.pump.fun')` with default version `v1`.
That literal is source attribution only, never an automatic destination here.
The reader appends `/coins/market-activity/batch` without normalizing the host
return. `fetchActivity` represents actual **796654.f**, whose underlying fetch
and success/network-failure telemetry are retained as a source witness but not
implemented. Logger **254667.y.warn** is also an external capability. No telemetry,
auth, cookie, storage, session or device provider is acquired.

The hook ports are the actual **445242.c(31)** compiler memo operation,
**606933.useQueryClient**, **935258.f** queries and **132838.f** mutation operation.
Their implementations, scheduling, cancellation and cache lifetimes are external.
Use one module instance in a stable host scope; per-render provider substitution
is not a recovered runtime guarantee. The module generates no requests on import
or construction. The retained factories are parsed as inert source; tests execute
the generated editable operations, never imported/evaluated capture bundles.

## Preserved request and data behavior

- Solana admission trims only for its 32..44-character base58 test. The original
  input string, including surrounding whitespace, remains in a request. EVM
  admission requires exact `0x` plus 40 hex digits. The combined predicate calls
  the Solana predicate first; a non-string can throw before the reader's catch.
- A direct reader preserves valid address order and duplicates. An empty/nullish
  address input returns `{}` before destination/fetch. Options use truthy
  `intervals`/`metrics` overrides, so an empty array is retained. Address filtering
  and option selection occur outside `try`; their exceptions are not swallowed.
- The complete request is `POST`, JSON Content-Type and ordered JSON fields
  `addresses`, `intervals`, `metrics`, plus the direct caller's optional signal.
  It adds no credentials, authorization, timeout or retry policy. This is a
  read-client POST, not permission to contact a real service.
- HTTP failure, fetch failure, abort, JSON failure and normalization exceptions
  inside the try block call `logger.warn(message,{error,mintCount})` and return
  `{}`. A throwing logger escapes. Failed reads can therefore become successful
  empty query deliveries; no stronger query-error or cancellation promise is
  invented.
- Normalization uses own record entries and exactly four windows: 5m/1h/6h/24h.
  A missing/non-object window becomes null. Object window fields are copied, then
  `volumeUSD`, `buyVolumeUSD` and `sellVolumeUSD` are replaced by finite numeric
  values in the inclusive range 0..1e12, or null. Nonblank numeric strings are
  converted. Other metrics are preserved without validation; this is not a full
  response schema or financial-data qualification. Inputs are not mutated.

## Complete query and callback behavior

The hook filters addresses, then deduplicates, removes falsy entries, sorts with
ordinary JavaScript ordering and splits into batches of 50. It preserves the
source's reference-based compiler cache: mutating the same input array does not
necessarily rebuild batches. The exported low-level splitter retains its
unvalidated size parameter; callers must not supply a nonpositive size that
would fail to advance the original loop.

Each query key is `['marketActivity', batch.join(',')]`. Defaults are enabled,
no polling, 300000-ms stale time and 600000-ms GC time. Refetch on mount, window
focus and reconnect and query retries are false. Explicit polling uses
`!!enablePolling && pollingInterval`, defaulting the interval only when undefined.
`shouldFetch` defaults only when undefined; source truthiness/null behavior is
retained. Query functions use fixed default intervals/metrics and do **not**
forward the query library's supplied abort signal.

Combined state retains all data slots, truthy pending aggregation and the first
truthy query error. Batches merge through ordinary `Object.assign` in delivered
order, with later records winning; no deduplication by recency or validation is
added. `refetchMints` deduplicates requested identifiers and invokes mutation for
each full current batch containing an exact matching value. It does not await
those mutations. The mutation callback awaits the reader, then writes and returns
that exact object under the original batch key. Cache write exceptions propagate.
`invalidateCache` invokes each current key without awaiting returned promises.
No implementation of the query library, socket/event source or persisted cache
is supplied.

The complete callback bodies, import/consumer witnesses and physical variants
are retained in `PROVENANCE.json`. Canonical module bytes are regenerated only
from those authenticated fragments and explicit host bindings. Structural alpha
comparison preserves statements/operators/values/order and maps qualified import
targets; it is not universal React, provider or runtime equivalence.

## Repeatable qualification

From `app/`, using the existing pinned dependencies:

```sh
node reconstruction/market-activity/verify.mjs --check
node --test tests/market_activity.test.mjs tests/original_source.test.mjs
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
```

From the repository root:

```sh
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

The finite tests use explicit query/cache ports, the installed React/compiler
runtime in a small SSR host and real ephemeral **127.0.0.1-only HTTP** with
synthetic payloads. They bind request-to-normalization and query/callback/cache
handoffs, failure boundaries, memo identity and source mutations. They do not
contact history, activity, relay, RPC or other real services. There is no Next
server, browser, credential, captured-code execution or dataset acquisition.

Original service availability, telemetry, provider internals, auth, ranking,
market/financial accuracy, mounted UI, native/API compatibility, full runtime
or security equivalence and feature completion remain unqualified. Captures,
SDK, dependencies, prior packets and all progress statuses/counts stay unchanged.
Descriptive exported names and host admission are local source-adaptation names,
not recovered original TypeScript paths. Original shipped code retains its
authorship. Regenerate only after source review with `verify.mjs --write`.
