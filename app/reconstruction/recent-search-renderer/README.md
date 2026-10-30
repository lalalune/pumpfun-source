# Original recent-search read state and address display

The full SearchDialog owner in #1925 leaves its recent-term renderer external.
This restores that **complete `tu` RecentTerms component**, its inline candidate/
hydration join and group-query frame, the complete `td` address-profile row and
six used selectors. The actual MAIN `terms/canExpand/onClear/onNavigate` handoff
is source-bound. History persistence (#1245/#1925), the ordinary result rows
(#1937) and existing providers/helpers remain separate credited boundaries.

The generator authenticates the physical singleton238128 factory (`9e5affaf…`)
in raw `ccb10fa3de5597c4.js`. All eleven selected component/selector/context
nodes compare as strict complete ASTs, including the 31/25/13-slot state/query/
join frames and26-slot address row. Only parser locations/comments/raw spelling
metadata are ignored. Declarations, values, fields, calls, branches, callback
order and JSX keys are preserved. No alpha/type/operation mask or captured
module execution. The emitted module and JSON contract compare as exact
canonical bytes.

## Complete boundary and required capabilities

```js
import { createRecentSearchRenderer } from "./client.mjs";
const { RecentTerms, AddressRow } = createRecentSearchRenderer(ports);
// Render RecentTerms({terms, canExpand, onClear, onNavigate}) with supplied terms.
```

One instance represents one original module instance. The constructor supplies
no data, service, history, navigation or renderer defaults. Its contract lists
all required functions/renderers, actual imports, inventoried physical variants,
raw UTF-16/UTF-8/SHA-256 citations, free bindings and selected helper hashes.
Listing provider variants does not choose an active runtime winner.

| Capability                                                                                                    | Actual source signature and limit                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `React`, `jsxRuntime`, `memoCache(size)`, `useTranslation()`                                                  | Real framework/compiler/translation capabilities. All selected local state and memo frames remain in the component.                                                                                                                                                                                                           |
| `useChainFlags()`, `nearEnabled(flags)`, `useGroupsEnabled()`                                                 | Required read-only feature snapshots. No flag/configuration/session acquisition or new auth/open/pause guard.                                                                                                                                                                                                                 |
| `validSolanaAddress`, `isEvmAddress`, `isGroupIdentifier`, `canonicalCoinAddress`, `walletProfile`            | Exact source admission/canonical/curve operations at required ports. They do not establish ownership or authorization. Accepted Solana text normalization is imported/verified unchanged.                                                                                                                                     |
| `normalizeNearInput(value)`                                                                                   | Actual trimming/admission helper `ti`, already recovered with #1925, remains required. No duplicate Near/parser/provider implementation.                                                                                                                                                                                      |
| `useGroupClient()`, `groupProfileKey(id)`, `readGroup({api,groupId,signal})`, `useQueries({queries,combine})` | Complete local query/options/combiner frame is retained; external client, key, reader and query lifecycle stay supplied. Keys are cache machinery, not credentials. The actual query forwards the provided native signal with the captured id/client and30-second stale time. No real account/group query or API/auth policy. |
| `useCoinHydration({mints,includeNsfw:true,disabled})`                                                         | Supplies `{coins,loading,isLoadingError,fallbackPending}`. The actual candidate join owns precedence and fallback. No batch reader/cache/service is implemented.                                                                                                                                                              |
| `useNearCoins(mints,enabled)`                                                                                 | Exact existing `to` helper boundary from #1925, yielding `{byAddress:Map,pending}`. Its full source/query/combiner/interface witnesses are retained as prior attribution; no hidden unmerged import or new Near/RPC provider.                                                                                                 |
| `useCoinUpdates(rows)`                                                                                        | Actual one-argument call for selected coin results. The provider's default activation/subscription remains external; no new open/pause/timer rule.                                                                                                                                                                            |
| `useProfile({address})`, `useVerifiedProfile(address)`, `formatFollowers(value)`                              | Actual782067 coalescer/profile and179736/#1841 verification/format ports. Only supplied profile data is consumed; no account lookup is sent.                                                                                                                                                                                  |
| `renderers`                                                                                                   | Required `Heading`, `Empty`, `SkeletonPart`, `Link`, `SearchIcon`, `ProfileDisplay`, `CoinRow` and `GroupRow`. `CoinRow/GroupRow` match #1937; no copying their source or hidden composition. `ProfileDisplay`/verification work remains credited.                                                                            |
| `styles.row/action`, explicit `avatarSize`                                                                    | Original-used presentation boundaries. No original CSS, primitive or visual compatibility claim.                                                                                                                                                                                                                              |

The accepted `profileRoute` helper is imported and verified unchanged. Existing
normalization/admission/query/read/helper work and the reused free-binding proof
infrastructure are credited dependencies, not new helper or feature credit.
Original shipped JavaScript retains its authorship; names/interfaces here are
maintained reconstruction choices, not recovered TypeScript filenames.

## Preserved read and interaction behavior

- Initially only the first three terms are classified and hydrated. Expansion
  uses the original functional state updater. `canExpand` gates the visible
  expansion without resetting local expanded state; replacing/clearing terms
  also adds no new reset. This is component state, not persistence.
- Classify shown terms as Solana/EVM/optional Near candidates and UUID groups,
  retaining raw text separately. Group selection has priority, then Near and
  canonical coin matches. The join preserves provided pending/error/fallback
  state and the source Solana-only curve-admitted user fallback.
- Group queries use captured ids/keys/client/signal, enabled flag and30-second
  stale time. Their combiner associates results by query position, stores defined
  data and otherwise marks pending ids only while the feature is enabled. It
  does not invent retry, error UI, authentication or authorization behavior.
  Calling a query function directly bypasses the supplied runtime's admission.
- Existing coin data wins before loading/fallback checks. Loading or fallback
  pending precedes text/user fallback; loading-error suppresses Solana user
  fallback. Unresolved EVM stays text. Near uses the supplied cohort Map/pending
  boundary, including cohort-wide pending for an unresolved Near candidate.
- Only selected coin results reach the one-argument update port. Source row
  handoffs retain the visible index, SEARCH/RECENT_LIST constants, raw term and
  current navigation callback identity. No actual navigation happens here.
- The address row requests its supplied profile hook with `{address}`, and its
  verification port with the same address. Missing data displays an address
  prefix; supplied data may provide username/follower/avatar/X fields. Description
  is absent until profile data exists. Link/ProfileDisplay remain rendering ports.
- Text fallback encodes the original term, preserving whitespace. Pending rows
  use the exact skeleton handoff. Clear calls the supplied parent callback and
  disables only when the provided terms array is empty; no storage is read.

## Repeat

From `app/`, with pinned dependencies and an existing Chromium:

```sh
node scripts/original-recent-search-renderer.mjs --check
node --test tests/original_recent_search_renderer.test.mjs
node --test tests/original_recent_search_renderer.browser.mjs
```

The browser producer bundles actual React/compiler/context with explicit
synthetic ordinary terms and provider/renderer results. One ephemeral loopback
GET host serves root and bundle only; external requests, cookie/storage and
Notification access are blocked. It records actual bundle/method input hashes,
closes browser/server in finally and uses no Next/install/product fixture.
`PUMP_RECENT_SEARCH_RENDERER_OUTPUT` saves finite observations/input hashes;
`PUMP_BROWSER_EXECUTABLE` selects an existing executable.

Supplied query/profile/curve/renderer results are not actual account queries or
original provider behavior. No storage/history persistence, service, session,
credential/cookie/clipboard acquisition, actual navigation, protected action or
Perps implementation/execution. No combined #1925/#1937 runtime, original
provider/visual/security/full-app/native/API/backend/feature-completion claim or
progress change. Prior packets, SDK, captures and shared helpers remain unchanged.
