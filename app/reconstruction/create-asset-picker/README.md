# Captured Create quote-asset picker

This reconstructs the complete **used picker boundary** in archived factory
734638: `em` category controls, `eM` picker and its actually invoked inline query
hook, `eD` result row and `eF/eB` loading rows. Their compiler frames contain
25/54/34/31/1 slots. The actual open-only `eL → eM` caller and coordinator
handoff are statically bound. This supplies the missing external picker-body
boundary left explicit by #1906; it does not count that coordinator again or
import its unmerged runtime module.

The producer authenticates **38 physical roles / 26 selected numeric IDs** and
**132 source witnesses**. It pins every current indexed variant of those IDs.
The six row-style contexts agree only on the seven used literal exports; both
category-selector contexts and both IPFS-context variants are recorded without
choosing an active-loader winner. React, query/debounce/provider and shared
renderer implementations are explicit ports, not claims of a complete loader
or original runtime.

## Complete selected workflow

The five input fields are exactly `isLoading`, `stocks`, `onSelect`,
`onSelectPumpCoin`, `onClose`. Search input stores raw text; local filtering and
the query trim it at their original sites. Stock matches use lowercase symbol
or ticker. The category map is the original plain object (`rwa → stocks`,
`crypto → crypto`, `meme → memes`), including inherited lookup behavior; no own
property guard or new asset-type admission is added. Category controls appear
only if at least one supplied stock has a non-undefined classification.

The embedded query hook always runs. It calls the supplied unfiltered
`47938.u` supported-mints reader, which is distinct from #1906's filtered
`47938.s` stock list. Its set is memoized by the supplied data-array identity.
The complete query key is
`['create','pump-quote-coin-search',debouncedTerm,1,includeNsfw,ipfsPrefix]`.
Enabled means only that the debounced term is nonempty; changing to a category
that hides Pump results does **not** disable this query. The supplied debounce
hook receives exactly 250ms. Query stale time is 30,000ms and placeholder data
is the original identity function.

The actual query function calls the supplied contract-client factory with no
arguments, then calls `GET /coins/search-unrestricted` with searchTerm,
limit20/offset0, includeNsfw, market_cap/DESC, program pump, maxDepth1,
`credentials:'include'`, the query context's AbortSignal and the original
`afterResponse` hook. That hook throws `Pump coin search failed: STATUS` when
`ok` is false. The response passes through the observed `997887.l` identity
and `493025.f` normalizer. **Identity is not schema validation.** No shape gate,
query cancellation policy or protected-service eligibility is invented.

Those identity/normalization/URI helpers are already maintained and source
verified in `reconstruction/search-session`; they are credited and supplied
through exact required signatures. The proof uses the maintained helpers,
including original in-place field/URI mutation. The source module implements
neither the contract client, its origin/configuration/response transport, the
supported-mint reader nor the query cache/scheduler. Their captured imports and
capability contexts remain inert witnesses. No actual origin, cookie, token,
user preference or provider data is acquired.

The complete original select predicate preserves truthy name/symbol, pump
program, absent truthy pool, depth≤1 with nullish-zero default, Mayhem-state
presence exclusion, strict-true ban, non-undefined decimals, supported-mint
exclusion and depth/quote classification. Dedup checks the **first raw input
occurrence** of a mint, so an earlier ineligible duplicate can suppress a later
eligible record. Source quirks such as null decimals surviving the undefined
check remain. This is source reconstruction, not financial or launch admission.
No current assets, prices, rank or authenticity is established.

Pump rows are shown only for a nonempty trimmed term in all/memes categories.
Errors mask query data even during refetch; the exposed error is non-null only
when isError and not isFetching. The complete original effect sends the
supplied error reporter a mint-shaped term only when the original regex
matches. Retry invokes the supplied query object's refetch and discards its
return value. Loading, no-results, mint-not-eligible, error/retry and rows follow
original precedence. No telemetry or retry scheduler is implemented.

Rows keep the source projection, exact selected-record callbacks and display
hand-offs. Stock zero monetary values reach the supplied formatter; Pump falsy
values become undefined at the row call. Formatting is an external display
port, not a pricing calculation. The original mouse-only pointerdown
stopPropagation guard remains; touch/pen and parent dismissal policy are not
silently normalized. Selection itself calls the parent and does not invent
local closure; #1906 owns its separate parent close behavior.

## Exact required ports and qualification

`client.d.mts` records local structural signatures of observed JavaScript,
**not recovered original TypeScript or runtime validators**. All capabilities
are required: React/compiler/JSX; translator; debounce tuple hook; IPFS-prefix,
NSFW and unfiltered supported-mint snapshots; complete query options/result;
contract client factory/call; existing identity/normalizer; error reporter;
formatter/class merger; category/art/avatar/name/error/skeleton/icon renderers.
The source-derived default module has no service fallback or implicit provider.

With existing pinned dependencies, from the repository root:

```sh
node app/scripts/original-create-asset-picker.mjs --check
node --test app/tests/original_create_asset_picker.test.mjs
```

The producer parses captured bytes without executing factories. Canonical UTF-8
client and contract bytes are regenerated from the selected operations. Direct
checks exercise the full local field/category→query options and callback→
normalization/select→row/error/retry boundaries, including seven actual
maintained-verifier mutation rejections. Their virtual child memo frames are
artificial and do not qualify React scheduling.

The separately frozen real React/compiler method uses authored query/debounce,
provider/transport and renderer ports:

```sh
node app/reconstruction/create-asset-picker/qualification/browser.mjs \
  --source FULL_FETCHABLE_SOURCE_COMMIT \
  --output "/tmp/create picker fresh qualification"
```

It uses native browser input/buttons/mouse/touch, real React/compiler, a supplied
250ms timer hook, the already-maintained normalizer and an in-memory contract
call port. It never makes the captured GET. The authored query port applies
select to supplied records; it does not implement TanStack caching or original
request/debounce scheduling. The host blocks external requests, serves only
its own bundle/HTML, records hashes/results/trace and closes in finally. No
pass is claimed until explicit qualification receipts are added.

## Prior work and limits

#1906 owns the coordinator/store/gateway; #1869 validation and #1884 fee controls
remain separate. Existing search-session identity/normalizers and SDK quote
classification are credited, with no first-recovery/copy retally. Avatar/art and
media #681/#885/#1817 are opaque shared ports or untouched boundaries; no image,
video, metadata, upload or avatar implementation is added.

No full default Create, private H, fee projection, reservation/Keypair, wallet,
auth/session, credential/cookie, funding, service/provider acquisition,
upload, instruction, signing, transaction or submit runs. Original captures,
SDK, maintained product/UI, dependencies, lockfile and feature ledger remain
unchanged. No mounted website, full-app/Next build, original DOM/visual/runtime
parity, current market/asset validity, service/native compatibility, security
clearance or milestone claim is made.
