# Captured livestream listing data boundary

This editable source reconstructs the complete credentialed listing arrows in
the physical `859960/606706/539335` factory, followed by its infinite-page
selection and the `310766` section's data handoff. It supplies an inspectable
query/response/page boundary that the maintained historical archive does not
implement. It adds no mounted component, endpoint, provider, dataset or cache.

The existing `/live` adapter authenticates 42 historical Most viewers records;
it does not run these queries. Open #1570 and #1617 separately reconstruct
Highest market cap archive navigation and six historical hero selections.
Their captures, source attribution and work remain prerequisites, with no new
fixture, unique-stream, native-feature or progress credit claimed here.

## Explicit capabilities

```js
import {
  createLiveListing, createPlaylistMapRead, mostViewedSectionArguments,
  liveSectionQuery, liveSectionResult, liveSectionView,
} from './listing.mjs';

// All capabilities come from a consumer. None has a global fetch/default URL.
const readPlaylistMap = createPlaylistMapRead({
  getServiceOrigin, fetchResponse, playlistSchema,
});
const { fetchSection } = createLiveListing({
  getContractClient, readPlaylistMap, logger, errorContext,
});
const query = liveSectionQuery(mostViewedSectionArguments({ limit: 24 }), {
  includeNsfw, ipfsPrefix, fetchSection,
});
// A query consumer owns execution, caching and delivery. This does not run one.
// query.queryFn({ pageParam: 0 }) is an explicit read if that consumer calls it.
const delivered = liveSectionResult(queryResultSnapshot);
const section = liveSectionView(delivered, { onShowAll, isExpanded, eager });
```

`getContractClient()` represents the actual `759257.j()` operation and returns
its route-call capability. Its service resolution, authentication, credentials,
query encoding, JSON decoding, Ky hooks/retries, cancellation and HTTP-error
wrapping are external. The retained query arrow supplies its exact options,
including `credentials: 'include'`, the error hook and `next.revalidate: 10`.
An injected implementation must honor those options to make an HTTP claim.
These source facts do **not** establish anonymous access or browser admission.

`getServiceOrigin`, `fetchResponse` and `playlistSchema` are the actual
`503630.c`, fetch and `558898.S` boundaries. The playlist arrow constructs the
original POST path/body/options, checks HTTP status, decodes JSON and invokes
`playlistSchema.parse(...).map`, in that order. There is no default parser or
approximation of Zod: the entire captured schema declaration is authenticated
as a source witness, while a compatible parse capability is supplied externally.
No playlist acquisition, playback/token authorization or provider orchestration
was performed. Playlist/media strings remain inert data in this module.

Coin-array identity and URI/coin normalization reuse the already-maintained
[search-session implementation](../search-session/session.mjs) of `997887.l`,
`493025.f` and `426091`; this unit does not copy or claim those recoveries. The
verifier invokes that accepted source verifier and binds its proof and source
hashes. In particular, the successful listing response is not validated by an
invented coin DTO parser. Normalization can mutate the supplied coin records,
as the captured operation does.

## Operations preserved

- Default listing limit is **24**, with undefined-only defaults. Most viewers
  forces **100** and warns for any requested limit other than 24, including 100.
  Sort names become `livestream_num_participants`, `market_cap` or `featured`.
  `order: 'desc'` and `currentlyLive: true` are request inputs; no local ranking,
  live-state filter, sanitization or extra schema is inferred.
- The two actual registry entries pass `{ livePageSort: ..., ...options }`.
  Caller options can override that leading sort. Card projection preserves served
  order and original coin identity, nullish title/time/image fallbacks, truthy
  low-playlist preference, raw metrics, creator values and media strings.
- Only cards without a truthy playlist contribute mints to the playlist-map read;
  duplicate mints stay duplicated. Failure is logged through the explicit
  formatter/logger capabilities and leaves the cards available. Map entries use
  low, standard, high, then VOD truthy precedence. Base-query and normalizer errors
  propagate; this unit adds no retry, cancellation, suppression or fallback data.
- Infinite-page keys include sort, NSFW input, resolved limit and IPFS prefix.
  Initial data is seeded by truthiness, so an empty array still seeds page zero.
  Stale time defaults to 10,000 only for undefined. The next offset adds the raw
  last-page length and stops on an absent/empty page; it does not advance by the
  requested limit or selected count.
- Selection deduplicates the first truthy `playlistUrl || thumbnail` key across
  all pages. It does not deduplicate by mint. Cards without either truthy key
  remain, and surviving card references/page parameters stay intact. Selected
  pages are flattened in order for the section consumer.
- The complete near-end callback fetches only with `hasNextPage` and without an
  in-progress next page. Completion fires when loading is false. Section data
  is loading, empty or delivered cards; there is no invented error state. Show
  all uses the captured four-card threshold or `hasNextPage`, gated by the
  caller's truthy Show-all capability. Expanded wrapping, eager and viewport
  observation inputs are returned as data; rendering and observation are external.

The facade/result names are local descriptions, not recovered TypeScript names.
React memo identities, scheduling, useInfiniteQuery, initial-section unlocking,
viewport/scroll effects, route navigation, hero/clip queries, provider lifecycle,
number/image rendering, current listings and configured production behavior are
outside this unit. No captured JavaScript is evaluated.

## Exact source and replay

The base is upstream `094a06f18df738d41e77070c1a009e135671ac1a`, not the fork's
older main. `PROVENANCE.json` authenticates manifest/index, complete physical
factories, imports/exports, raw object/factory SHA-256 and UTF-16/UTF-8 ranges.
The listing is the sole indexed `859960` variant, SHA-256
`d97c7c9447e248dcaeef4b872bb869c9056d2979cdf53731913116fb8544e429`,
in `evidence/web/objects/44a65b4313e51497.js` at UTF-16 `[25955,30183)`.
`539335.f` and `606706.O` are its actual co-registered constants; `944001.Z`
contains the two used registry entries and the same physical factory's
`310766.Z` consumes their result. The complete `31113` parent and external
playlist schema are retained as witnesses. No global active runtime winner is
inferred from numeric IDs, physical containment or this bounded selection.

The verifier reuses the accepted lexical alpha comparison. It retains complete
parameters, async flags, operations, branches and evaluation order, maps only
recorded free/import bindings to explicit capabilities, and normalizes `!0/!1`.
Function-declaration wrappers compare through their parameters/body as arrows;
no function identity/constructor/React equivalence is claimed. Consumer JSX
remains a source witness; only the listed conditional and forwarded data inputs
are reconstructed. The entire editable module is also hash-bound.

From `app/`, using the repository's pinned dependencies, with no network calls:

```sh
node reconstruction/live-listing-data/verify.mjs --check
node --test tests/live_listing_data.test.mjs
```

Tests execute only editable maintained code and explicit synthetic capabilities.
They cover the composed two-page flow, request policy, normalizer mutation,
playlist ordering/failure, abort/error propagation, media-key selection, raw
offsets, seed/default distinctions and consumer callbacks. Source checks also
reauthenticate a minimal public input export in a path with spaces and reject a
resealed semantic edit. These finite checks are not HTTP, browser, live provider,
playback, mounted UI, native compatibility, universal equivalence or security
qualification. Original captures and prior packages remain unchanged.

Only after deliberate source review, regenerate the checked-in proof with
`node reconstruction/live-listing-data/verify.mjs --write`. Source comparisons
still run before writing; editing its hash alone cannot bless a changed callback.
