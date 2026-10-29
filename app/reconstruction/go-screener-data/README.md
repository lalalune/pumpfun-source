# Main-app bounty screener data boundary

This editable source reconstructs the actual `851373.ScreenerListingView` data
path: filter/sort parameters, its two infinite-list queries, parsed pages,
cursor handoff, local facet calculations, enrichment result selection and feed
inputs. It supplies callable maintained logic where the original operations
were previously confined to captured factories and source notes.

It does not replace the historical 25-bounty `/go` adapter from merged #648.
Open #1612/#1634 address that adapter's draft/date UI behavior and remain separate.
No page, route, endpoint, provider, dataset, ledger/status/count or native feature
is added. Separate GO/revenue microsites, account actions, submissions, funding,
claims, payouts and accounting remain outside this work.

## First-party context, with an explicit route limit

The authenticated `https://pump.fun/go` document is
`evidence/web/objects/e66810e11f481135`, 1,030,034 bytes, SHA-256
`8037ac8c628063897531326090f1a4d3cbf8ed0051f4f6e9f88c821f4fee9ece`.
Its original/final URL is the same first-party URL and status is 200.

Three literal Flight pushes are parsed as inert JSON. The accepted byte-aware
Flight parser resolves import `11a` to module `768385`, name record `119` to
`BountiesDiscoverRoutePage`, and actual element `82` to `$L11a`. The same retained
HTML contains a `/go/bounties` tab anchor and initially loads the first-party
parent/loader chunks. The used parent reads the pathname, maps the actual
`409355.b` `/go/bounties` route to its `bounties` branch, and passes filter,
near-me, facet callbacks, sort and view inputs to its lazy screener. The actual
`660787` loader names `3v64vaswz40vp.js` then imports `851373`; those child bytes
are also retained under `https://pump.fun/_next/…`.

This establishes **main-app conditional source context**, not a deferred separate
GO microsite. Only `/go` HTML was captured, and it displays the trending branch.
There is no `/go/bounties` HTTP capture, observed lazy screener execution, new
route qualification, global active-runtime winner or anonymous API admission.
`PROVENANCE.json` includes the capture/push/Flight/anchor and actual source edge
witnesses; no static numeric-ID mention is treated as a rendered element.

## Use and capabilities

```js
import { createGoScreener } from './screener.mjs';

const model = createGoScreener({
  client,          // actual 944410.useLivestreamApiClient-shaped delivery
  responseSchema,  // actual 711902.L parse capability
  xFeatures,      // supplied 314197.f feature result, not an auth principal
  enrichTasks,    // actual 260095.E result: {bounties, liveTokens}
  now,            // raw Date.now-shaped capability
});
const queries = model.plan({ filters, sortKey, nearMe });
// Host-owned query library schedules queries.listing / queries.phaseFacets.
// queryFn remains lazy. Constructing the model/plan performs no HTTP request.
const view = model.derive({
  filters, nearMe, viewMode,
  listingResult, facetsResult, sentinelRef,
});
// Host-owned effects/rendering consume view.facets/timeLeftCounts,
// visibleMints/subscribeVisible, sentinel, footerProps and feedProps.
```

`client.get('bounties/v2/tasks', { searchParams }).json()` is the exact captured
read shape. No default client, origin, fetch, token, cookie, session or credential
store exists here. Its effective configuration, authentication, HTTP errors,
retries, JSON decoding and cancellation remain external. No provider is queried
in the tests. The `PUBLIC` query-key name is not evidence of anonymous access.

`responseSchema.parse` is the real used boundary, invoked after JSON. All three
physical `711902` variants are retained as source contexts. Their schema includes
defaults and attachment transforms; this unit deliberately supplies no substitute
parser, hand-written DTO acceptance or default/stripping approximation. Tests
inject explicit parser results to prove call order and use of parsed values,
without claiming reconstructed Zod behavior or current response compatibility.

`enrichTasks(tasks)` is the used `260095.E` boundary and returns normalized
bounties plus the supplied live-token map. Its user/token providers, viewer
address and task adaptation are not instantiated or reconstructed. No account or
wallet state is read. This model preserves the caller's consumed arguments and
result-field use, including the existing complete `471106.N` feed projection.

`now` is explicit for reproducible local semantics. The original filter builder
samples once, local filtering samples its time-left instant separately, phase
classification samples only on its valid pending-expiry branch, and time counts
sample independently. These are not collapsed into a fake atomic clock snapshot.

## Preserved flow

- The full query arrow retains all captured text, creator/coin/reward, status,
  phase, expiry, numeric-threshold, sort/order, geo, limit, facets and cursor
  predicates. Limit defaults to 24 **only for undefined**. The complete query
  key preserves nullish fields, joined reward mints and strict-boolean flag keys.
  This is source behavior, not new validation or permission to use any field.
- The feature result removes follower-count sorting/threshold when disabled.
  It is availability logic, not backend authorization. Geo fields are included
  only when all three are non-nullish finite values; no coordinate/radius range
  validation or geolocation read is invented. Zero values remain present.
- Query text retains the original 256-UTF-16-unit clamp, including a possible
  split surrogate. This is distinct from #1726's local archive query-recovery
  correction. No URL encoding or Unicode-repair behavior is asserted here.
- Sort/filter construction retains distance precedence, OPEN phase behavior,
  SOL-mint mapping, raw USD filter bounds and intersections of ISO expiry ranges.
  The main query uses limit 24. The phase proxy removes status filters and uses
  limit 1. Both request first-page facets only for a nullish page parameter.
- `nextCursor ?? undefined` retains an empty string. The request itself omits
  an empty-string cursor and omits facets on that non-nullish page parameter.
  No guessed cursor lifetime, termination repair or backend pagination is added.
- Parsed task pages flatten in server order without deduplication. **Local
  filtering calculates facets, not the displayed list.** Phase facets use the
  proxy's first page when present, including an empty array; otherwise they use
  locally filtered task phases. Reward facets remove reward-token filters; time
  counts remove time-left filtering. The status array remains the shared empty
  array from the source.
- Phase derivation and local text/token/USD/time predicates preserve their
  actual edge cases. Missing or invalid expiry passes local time buckets;
  missing USD does not fail numeric filtering. Reward-mint facet counts count
  occurrences, not distinct tasks. The local seven-day bucket is strictly `>`.
  No reward, eligibility, balance, payout or financial correctness is inferred.
- Enriched bounties map by `id`, with the last duplicate winning. Raw task order
  drives the feed mapper; repeated raw IDs repeat the resolved item, and missing
  enrichment skips that item. Footer count/body decisions still use the raw task
  count. A raw nonempty result remains a feed during loading/error flags.
- Subscription inputs preserve reward-leg mints before each task's coin mint,
  with Set insertion order. Sentinel inputs forward existing has-next, fetching
  and fetch-next capability values. Footer/feed inputs retain the captured
  visible count, view mode, feed kind and disabled-hover-card flag.

The public function/result names and `body` label are authored descriptions.
This is explicit recomputation, not the original hook, memo identity, URL state,
query cache, observer, live subscription, parent callback effect or JSX renderer.
The parent route's own proxy query/sync controls also remain outside this
child-unit boundary. No authenticated action, provider lifecycle or rendered
main-app success is implemented by this source reconstruction.

## Provenance and offline verification

The base is upstream `094a06f18df738d41e77070c1a009e135671ac1a`. The sole used
query is `170258/c2cc17f47ff2…`; the sole consumer is
`851373/bbcb560d600f…`. The producer retains all 27 physical contexts, including
two route/sort/query-clamp/mint/client contexts where applicable, three feature
and schema contexts, and the complete used caller, filter, enrichment and feed
boundaries. It selects no arbitrary global winner from those variants.

The verifier authenticates original manifest/index, raw object/factory hashes,
UTF-16/UTF-8 ranges, actual imports/exports and retained HTML/Flight context.
Complete callback bodies keep actual local names/syntax; only recorded free
bindings/import targets map to explicit capabilities/constants. Block, function
and loop shadowing is preserved, with boolean spelling normalization. Simple
parameter-only clamp/sort variants reuse the accepted lexical alpha comparator.
Function-declaration wrappers compare through their parameters/body as arrows.
There are 57 callback/expression comparisons, not a universal React/compiler or
whole-application equivalence proof. Shared source/Flight tools and their prior
recoveries remain dependencies, not new credit.

From `app/` using the repository's existing pinned dependencies:

```sh
node reconstruction/go-screener-data/verify.mjs --check
node --test tests/go_screener_data.test.mjs
```

Fourteen focused cases exercise the complete explicit plan → two parsed page
queries plus phase proxy → facet/enrichment/feed flow; predicates, ordering,
references, failures, independent clock rules and cursor quirks; a public input
export at a path with spaces; and adapter/variant/rehashed Flight-import tampering.
Only editable maintained code and explicit synthetic capabilities execute.
Captured JavaScript, the historical dataset, services, Next and browsers do not.
Original captures, prior packets, SDK, runtime pages and feature ledger stay
unchanged. No fixture replay, native feature/compatibility or security credit is
claimed. Original shipped JavaScript retains its authorship.

After deliberate source review only, use
`node reconstruction/go-screener-data/verify.mjs --write` to regenerate provenance.
The source comparisons and actual-origin checks still run before writing.
