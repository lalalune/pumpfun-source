# Captured candle-history client and normalized deliveries

The Mayhem chart reader delegates normalized candle/line history to **505835.Z/x**.
Those operations were still external to the editable sparkline flow in #1827.
This unit reconstructs their complete request, retry/optional-relay, error and
normalization path, including the actually used **771073.Z** candle decoder and
**921152.h** UTC-week bucket. It adds no history service, route, proxy, dataset or
native adapter.

The original service origin is the already-attributed **503630.R** literal
`https://frontend-api-v3.pump.fun`; that is source attribution, not permission or
an automatic network destination. This module requires explicit host destination
and fetch capabilities. All executable HTTP proof uses ephemeral **127.0.0.1**
servers and synthetic values. There are no external history/relay/RPC reads,
credentials, transactions, captured-code execution or financial-data claims.

## Use and host boundary

```js
import { createCandleHistoryClient, readCandleHistory, CandleHistoryFetchError }
  from './client.mjs';

const client = createCandleHistoryClient({
  baseUrl: callerSelectedHistoryOrigin,
  fetchImpl: callerSelectedFetch,
  relayFetchImpl: callerSelectedRelayFetch,
});
const result = await client.candles({
  chainId, address, interval: '30m', count: 60, measure: 'price_usd',
  beforeTs, init,
  // Optional source flags: relay, retryDelaysMs, sleep, onRelayServed.
});
const line = await client.line({ chainId, address, res: '1m', count: 60,
  maxPoints: 72, measure: 'price_usd', init });
```

`client.candles`/`line` are a small **authored host facade**: construction requires
a string destination and both fetch functions. Calls copy their option fields
and use configured capabilities only where the per-call value is undefined.
They replace the source's ambient origin/global-fetch defaults, without creating
a relay implementation. The relay fetch port receives the actual **relative**
`/api/swap-api…` URL; its host must resolve it deliberately. The module does not
pretend that this route is implemented by the maintained backend.

`readCandleHistory(input)` and `readLineHistory(input)` are the recovered core
operations on an explicitly configured input object. The candle operation
deliberately rereads `input.interval` **after awaiting** delivery, as the captured
Z callback does. Mutating that object while a request is pending can therefore
produce an interval mismatch even when the request URL used its old interval.
The host facade's call snapshot is distinct from that source behavior; callers
needing reference behavior can use the core operation directly. The line
operation destructures its fields before delivery, matching x.

`requestHistory` exposes the complete retry operation with explicit fetch ports.
Direct callers must supply those ports. `buildCandleUrl`, `buildLineUrl`, envelope
predicates and pure normalizers are also usable independently. Descriptive
export/file names are local, not recovered original TypeScript names.

## Request and failure semantics

- Paths remove trailing base slashes and encode only the address. Query fields
  retain source order. Candle interval aliases determine upstream resolution
  and bar multiplier; multiplied counts round up and clamp to 1..300. The line
  builder clamps count to 1..300 and maximum points to 2..2000. It adds no input
  validator: omitted/nonfinite values can retain NaN text or throw as in source.
- Positive `beforeTs` becomes `Math.floor(beforeTs) - 1`; zero/negative/undefined
  omit it. The wrapper in #1827 owns its separate caller-side cursor adjustment.
  This unit does not duplicate that wrapper, mapper, query keys or age policy.
- `fetchImpl(url, init)` receives the original init reference. The client adds no
  method, headers, credentials, timeout or body. Ordinary undefined-init reads
  use the supplied fetch implementation's GET behavior. Caller-supplied init
  forwarding is not a new authorization or credential policy.
- Only an **exact false** `response.ok` takes the HTTP-failure branch. HTTP 429 or
  status at least 500 is retryable; other HTTP failures stop. Network failures,
  JSON failures and invalid envelopes are retryable. JSON is consumed from the
  original response. Envelopes require arrays/served resolution (and candle
  `hasOlder` boolean); this is not complete successful-DTO/schema validation.
- The retry default is **[]**, meaning one attempt. Exported `[300, 900]` is
  retained as a separate source value, never promoted to an implicit policy.
  Supplied delays are awaited before attempts after zero, and sleep errors
  propagate. Primary retryability controls the loop.
- Relay is opt-in, only after a primary **network** failure (`status === null`).
  It uses pathname/query from an absolute URL and drops its origin/hash. Invalid
  absolute URLs suppress relay selection. Successful relay invokes the supplied
  synchronous callback with `{attempt}` before returning; callback errors
  propagate. Relay HTTP failure does not independently choose loop continuation.
- Final `CandleHistoryFetchError` retains primary message/status and the most
  recent failed relay details, even if a later primary HTTP error stops without
  another relay. The actual name, status/fallback own fields, null defaults and
  constructor operation order are retained. This is separate from the generic
  ContractError reconstruction.
- Fetch-phase `AbortError` propagates immediately and unchanged, including relay
  aborts. An abort while consuming JSON follows the source's JSON-failure catch.
  It can consume a retry delay; a later fetch with the already-aborted signal
  then propagates its abort. No stronger cancellation guarantee is invented.
- Post-delivery normalization happens outside the transport retry loop. A valid
  envelope containing a malformed row can therefore throw without another
  request or error-class wrapping.

## Normalized deliveries

Candles use the complete 771073.Z decoder: Number-converted OHLC must be finite
and strictly positive, while `openTimeMs` must already be finite. Volume is the
distinct `Number(volumeUsd) || 0` operation; it is not clamped to positive/finite
values. There is no additional OHLC consistency rule. Last **valid** duplicate
timestamp wins, then rows sort ascending. Original input objects stay unchanged.

Interval/resolution mismatch returns empty candles with `hasOlder: false` and
the mismatch flag. Supply is retained only from a nonempty string converting to
a positive finite number. Ordinary direct intervals keep normalized rows;
30-minute and 12-hour intervals aggregate into fixed buckets, and one-week
intervals use the actual UTC-Monday bucket. The six-hour alias is a direct four-
hour resolution, not an invented six-hour aggregate. Bucket open comes from the
first row, close from the last, high/low from extrema and volume from numeric
addition. With `hasOlder`, the first aggregate bucket is dropped only when there
is more than one aggregate bucket; a single bucket remains.

Line deliveries retain raw `barCount`, including rejected rows. On resolution
mismatch they return empty points before touching rows. Otherwise Number(price)
must be finite and positive, time must already be finite, and points sort by
time. Null malformed rows can throw, matching the source rather than silently
becoming an empty financial series. No response here is qualified as original,
current, accurate, CORS-readable or compatible with a deployed service.

## Source closure and prior credit

`PROVENANCE.json` authenticates raw capture URLs/hashes, exact registration IDs,
factory hashes and UTF-16/UTF-8 ranges through the existing safe source helper.
It retains the complete provider callbacks, not only selected string fragments.
All parsing is inert; the captured factories are never evaluated/imported.

- The sole physical **505835/d6df4a639b71…** factory also registers 442951 and 628731.
  Qualified exports distinguish Z/x, the error class and the line normalizer.
  The complete actual transport/retry/relay and post-delivery callbacks are bound.
- The sole **771073/743bed63aa8d…** decoder depends on its local positive-number
  helper. Its unrelated formatting/request exports are excluded.
- The sole **921152/8c0b21b64410…** used h export resolves the actual local UTC
  bucket; unrelated chart, storage, template and wallet exports stay excluded.
- Existing **503630** origin attribution and #1827's mapper/key/caller recovery
  receive no new recovery credit. The nine 349942 candle callers and five grouped
  636882/693908/997627 contexts reauthenticate their actual Z/x calls only to
  close the delivered interface. No active global runtime winner is inferred.

The verifier checks the recorded constructor/data/URL/retry/relay expressions
and ordered operations structurally, using explicit identifier/port substitution
and boolean spelling normalization. Splitting a constructor's unconditional
comma expression into ordered operations preserves that recorded order. The
complete remaining callback bodies are source witnesses and directly exercised
through finite HTTP/semantic tests. This is not universal whole-runtime, backend,
browser, financial or security equivalence.

## Reproduce offline and on loopback

From `app/` using the existing pinned dependencies:

```sh
node reconstruction/candle-history/verify.mjs --check
node --test tests/candle_history.test.mjs tests/original_source.test.mjs
python3 scripts/verify-evidence.py
python3 scripts/progress.py --check
```

From the repository root:

```sh
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

The tests create and close ephemeral loopback servers. They bind real GET URLs,
init forwarding, response normalization, retry and socket-close→relay sequences,
abort phases, error identities, caller mutation after await and the data
operations above. They also reject resealed retry/price-rule changes and missing
source variants/corrupt captures, and replay source verification from public raw
inputs in a path with spaces. Synthetic replies are test inputs, not archived
history fixtures or feature/compatibility credit. See `VALIDATION.json` for exact
tested input hashes and retained logs.

Regenerate source provenance only after review using
`node reconstruction/candle-history/verify.mjs --write`. Original captures, SDK,
dependency files, prior packets, pages and progress ledgers remain unchanged.
Original shipped JavaScript retains its authorship.
