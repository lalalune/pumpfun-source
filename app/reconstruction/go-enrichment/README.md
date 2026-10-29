# Original GO bounty-enrichment boundary

The main-app screener passes raw bounty pages to `260095.E`, then supplies its
`bounties` and `liveTokens` to the feed-model caller. The surrounding screener is
already attributed by [open #1854](https://github.com/lalalune/pumpfun-source/pull/1854);
its required enrichment port remained external. This unit restores that complete
selected operation and its used display-data closure. It does not mount a GO UI,
read a live provider or implement a backend reward/accounting service.

The generator authenticates these complete selected operations in all retained
physical contexts, preserving memo slots, identity comparisons, declarations,
operators, calls, defaults and ordering:

- `260095.E/o`: full enrichment and separate token hooks; one physical variant.
- `242663.f`: token-result projection, all two physical variants.
- `609252.f`: raw coin-query result/default/error wrapper, all nine variants.
- `456647.m`: complete bounty display mapper and all its used local helpers.
- `462024.i/u/Q`: used token descriptors and submission/mutation display guards,
  both physical variants. Other exports and their unrelated dependencies remain
  excluded; this path does not use `32850`.

The existing lexical comparator is reused with its real function/loop scopes.
For object-rest bindings only, a marked compatibility aid adds `.value` equal
to the original `.argument`; the original `RestElement` type and all fields are
retained. This lossless representation is never executed. Exact source hashes
and UTF-16/UTF-8 witnesses remain in [contract.json](contract.json). Generated
client and contract are checked as exact canonical bytes. Captures are parsed
and hashed, never executed. Shared source/graph/inventory code is unchanged.

## Required capabilities

`createBountyEnrichment(ports)` requires all six functions. There is no implicit
network destination, fetch, cookie, storage, identity or clock provider:

| Port                                  | Actual call/result boundary                                                                                                                                            |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `memoCache(size)`                     | React compiler memo cache; source `445242` delegates to `532815.c` and `useMemoCache(size)`. Supply the existing React compiler runtime capability.                    |
| `useViewerSnapshot()`                 | `{ address }` external read-only snapshot. No wallet/session/auth acquisition or authorization is inferred.                                                            |
| `useBatchProfiles({ userAddresses })` | Actual `576766.f` result with `data` and `isPending`. Its accepted query/strict reader/error behavior is credited and unchanged; host owns real hook/query scheduling. |
| `useCoinQuery(mints, options)`        | Actual `689943.V` result: `data`, `isLoading`, `error`, `refetch`, `isError`, `isLoadingError`. Query/cache/TanStack/transport/provider behavior remains external.     |
| `useIpfsPrefix()`                     | Explicit `{ ipfsPrefix }` provider result. No provider availability or acquisition claim.                                                                              |
| `nowMs()`                             | Epoch milliseconds for the actual expiry admission predicate. It does not create a timer or invalidate memoized results.                                               |

The returned hooks are `useEnrichedBounties(rows)` and `useBountyTokens(rows)`.
`mapBounty(row, { creatorUser, coinMeta, viewerAddress })` exposes the same pure
display mapper actually used by enrichment; it still uses the supplied clock.
Instantiate the adapter outside rendering; call its hooks under real React.
Changing hook kinds requires a separate component/mount, as with the originals.

## Data and lifecycle semantics

Token stubs retain first-seen order, skipping empty values and native SOL/USDC
mints. Coin address is considered before reward legs. Creator addresses are
unique in source order. The coin wrapper supplies captured defaults (limit50,
offset0, market-cap descending, safe/disabled booleans), spreads remaining input
options last and forwards the mint array to the external query hook. It retains
undefined-versus-null response behavior and error conversion. No request/key,
retry, polling or abort policy is invented for that external query.

The accepted `493025` normalization is imported unchanged from search-session.
It can mutate raw rows while filling aliases and URI fields. Token projection
uses `usd_market_cap || market_cap || 0`, native `Number` supply scaling and
source name/symbol/image fallbacks. It is display computation, not financial
precision or a token-price service. [#1812](https://github.com/lalalune/pumpfun-source/pull/1812)
previously witnessed/injected `609252` hydration; this unit credits that prior
boundary and does not reclaim its reader/transport work.

The bounty mapper preserves markdown summary truncation, a copied/sorted
criterion list, nullish timestamp precedence, seven-day expiry fallback,
digit-only atomic-string conversion and native `Number` rounding/finite guards.
Reward legs retain order and duplicates; first-leg display currency remains
separate from the positive-only breakdown. Winner counting deduplicates the
submission/mint pair, preserves the first duplicate's claimed truthiness and
honors an explicit zero winner count. Viewer/creator/refund comparisons retain
the source's case handling. These fields are display decisions, not proof of
eligibility, balances, refunds, authorized actions or payment/accounting truth.

All three compiler memo frames and their returned identities remain intact.
Data, input and viewer changes invalidate only their actual source dependencies.
A clock change alone does not recompute a cached bounty or schedule expiry.
Submission and mutation display guards remain distinct: expiry/moderation can
disable submission while the mutation guard still returns true. Enrichment
loading depends only on nonempty requested creator/token sets and the respective
pending/loading results; the source does not turn every query error into a new
enrichment error state. Empty inputs still call the external hooks with their
actual empty/disabled arguments. No cancellation/cleanup behavior is invented
for hooks which have no own effects.

## Repeatable checks

From `app/`, using the existing pinned dependencies and installed Chromium:

```sh
node scripts/original-go-enrichment.mjs --check
node --test tests/original_go_enrichment.test.mjs
node --test tests/original_go_enrichment.browser.mjs
```

The last command bundles only the new maintained adapter and a synthetic React
host, then serves the root/bundle through one ephemeral loopback GET host. All
data-query/viewer/IPFS values are explicit synthetic results; there is **no HTTP
data-provider request**, real service, credentials, cookie or storage read.
It uses the actual React/compiler runtime, not an emulated hook scheduler.
Optional `PUMP_GO_ENRICHMENT_OUTPUT` saves its observations/input hashes and
`PUMP_BROWSER_EXECUTABLE` selects an existing Chromium executable. Host/browser
are closed on completion. No installation, Next server or product fixture is
needed.

Original auth/provider/query-runtime availability, live discovery, backend/API
or native compatibility, complete GO/individual-detail/refund/payout workflows,
product rendering/visual parity, security equivalence and feature completion
remain unqualified. Original captured materials retain their authorship.
