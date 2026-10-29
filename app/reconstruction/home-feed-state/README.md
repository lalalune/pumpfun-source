# Original Home ranked-feed read state

The retained website has a complete read-state coordinator in `99859.r`, but
the maintained Home feed uses an independent synthetic store. This unit makes
the captured coordinator and its response normalizers editable and callable.
It does **not** connect them to the maintained app or supply the original
service, React provider, query cache, session or telemetry environment.

The accepted [Home request/declaration packet](../../contracts/original-home-feed.json)
(#686) already binds `735821.Z` and its website transport. That reader remains
the explicit `fetchHomeFeed(options)` capability here. No request implementation
or operation-coverage credit is duplicated. Accepted #891 already reconstructs
the different user-replies flow. Mentions, relative time and quote-display
work in #1374/#1472/#1523 are separate and are not copied.

## Complete selected boundary

- The matching prefetch and hook use the same chain/page-size/followed-holders/
  viewer key and request arguments. Defaults remain 150 / `all` / false / null;
  stale time is 15 seconds, retry count 3, focus refetch enabled, periodic
  refetch 15 seconds and background interval refetch disabled.
- `154703.y` projects the full row: author identities, optional values, quote
  parent/callout precedence, tombstones, metrics, asset fields, root updates,
  position data, followed-holder exclusion and position identity. All six
  physical variants are retained. The helper contexts are explicit selections;
  this does not choose the original browser's active registration.
- The hook keeps its original compiler memo-cache structure, a per-hook
  `WeakMap` keyed by raw objects, raw-array identity memoization and first-key
  deduplication. Null normalization results remain cached. No sorting or
  response-admission policy is added.
- The seed requires a matching chain and equality to the hook's initial
  viewer. A changed viewer resets visible keys, retired keys and the pending
  counter. Non-overlapping snapshots also refresh the initial visible set.
- The initial visible set has 12 keys. The 2.5-second pending-reveal effect
  caps the count at 25 and its preview at 3. This effect itself has no document
  visibility check; query background polling is a separate option.
- Show-new prepends at least one unseen row and caps that operation's visible
  set at 40, retaining retired keys. Fetch-next appends 12 unseen rows, or 12
  retired rows when none are unseen. **This is local ranked-snapshot expansion,
  not an HTTP continuation request.** Fetch-next does not impose the 40-row cap.
- Loading/error output, timer cleanup, both actual parent hook consumers,
  Home's `callouts`→`rows` handoff and the screener feed-state prop are bound.
  The parent renderers, following/top feeds and their actions are excluded.

The [contract](contract.json) records exact capture hashes, factory registrations,
UTF-16/UTF-8 ranges and 61 witnesses. The producer authenticates all six
normalizers, both helper contexts, their metrics/asset/holder/chain helpers,
base58 dependency and actual compiler bridge. Complete selected functions and
private declarations are translated, rather than extracting a reduced state
kernel. Captured factories remain inert and are never imported or evaluated.

## Host capabilities

`createHomeFeedRead` requires an explicit normalizer hash and helper context
from the exported lists, plus these capabilities:

```js
const feed = createHomeFeedRead({
  normalizerVariant, // one listed physical 154703 variant
  helperContext, // one listed captured helper context
  React, // useState, useRef, useEffect
  useMemoCache, // the React compiler runtime's c(size)
  useQuery,
  useHomeFeedSeed,
  fetchHomeFeed, // accepted 735821.Z request boundary; not provided here
  decodeBase58, // returns decoded bytes; codec errors remain caught by 639374.f
  timers: globalThis,
});
// Call feed.useHomeFeed(options) from an actual React host.
// feed.prefetchHomeFeed(queryClient, options) uses the matching query callback.
// feed.normalizeRow(raw) exposes the same selected normalizer for direct reads.
```

The capability objects, explicit selection and constructor checks are authored
host adaptations. React, compiler scheduling, query retries/cache/observers,
seed/provider availability, interval scheduling and codec implementation remain
external. `Date.parse` retains host behavior. The source's CAIP literals and
address-case rules are preserved; no wallet, key, signing or chain operation is
performed. The declared DTO is not promoted into new runtime validation.

## Reproduction and finite qualification

From the repository root with the existing pinned app dependencies:

```sh
node app/scripts/original-home-feed-state.mjs --check
node --test app/tests/original_home_feed_state.test.mjs
node app/reconstruction/home-feed-state/qualification/browser.mjs \
  --output "/tmp/Home feed proof fresh" > "/tmp/Home feed proof fresh.log" 2>&1
```

The output directory must not exist; use a new path for each attempt. The
browser command derives its app root from its own file location, bundles only
maintained code and pinned local React dependencies using the existing `tsx`
dependency's esbuild, and starts one ephemeral loopback HTML server plus one
headless Chromium. It needs the already provisioned Playwright browser; it
does not install or download one. No Next, app route or backend is started.
Source verification also accepts `--app-root "/path with spaces/repository/app"`.

The direct tests exercise every normalizer/helper pairing, author/update/count
and quote/tombstone behavior, identity fallback, actual verifier rejection and
one real loopback HTTP callback→normalizer composition. That HTTP port is an
authored synthetic test input, not the website transport or service.

The [qualification](qualification/README.md) retains six actual React/compiler
host cases. Query/seed/codec inputs are explicitly synthetic; five scenarios
use a manual timer port. A separate case observes one actual 2500 ms interval
and real React unmount cleanup. These prove the finite translated-hook
composition, not the original query provider, polling reliability or timing
parity. No original code was executed, service response acquired or browser
session/credential read.

`mounted: false` and zero production operations in the contract describe the
maintained app and original service. The isolated synthetic qualification host
does mount the new translation. No original/maintained UI parity, native API,
backend, auth, feature milestone, new inventory count or security approval is
claimed. Earlier packets, captures, SDK and ledgers remain unchanged.
