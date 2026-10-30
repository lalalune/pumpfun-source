# Original shared SearchDialog owning controller

The earlier search units recover transport, request execution, query operations,
identifier submission and the mounted key matcher. They leave the owning dialog
frame, result composition and callback lifetime outside their scope. This unit
restores the **complete ordinary `238128.tg` owner and exported
`SearchDialogLazy` child**, with required source-signature capabilities at their
actual provider and rendering boundaries. It does not replace or mount the
maintained application's independent search UI.

`original-search-dialog-controller.mjs` authenticates the single physical
`238128` factory (`9e5affaf…`, raw `ccb10fa3de5597c4.js`), then emits editable
source. The complete owner compares as a strict AST after exactly three
credited body bridges: the Solana navigator and ordered submit from
`search-navigation`, and the key matcher from `search-shortcuts`. Their existing
source verifiers run unchanged. All other owner statements, including the three
other-chain handlers, inline hook frames, JSX handoff, dependencies and ordering,
are retained. Parser positions/comments/raw spelling metadata alone are ignored.
Seventeen used local helpers/constants and the complete four-slot lazy child
also compare strictly. The actual parent `onMounted` handoff is source-bound.
No captured module is imported/evaluated; the emitted module is the maintained
source under test.

The canonical JSON contract records the raw factory/citation SHA-256s and
UTF-16/UTF-8 ranges, import IDs, every inventoried variant at each referenced
provider boundary, free owner bindings, renderer/capability map, five physical
group-limit providers and credited dependency hashes. It does **not** choose an
active winner among the four `379705` coin hooks, three `600775` user hooks or
other ambiguous providers. The existing loader/session/cache/493025 attribution
stays credited and unchanged. The board-only owner in #1867 is distinct: this
caller supplies `isSearchMode:true` to its required coin-search hook port.

## Construction and complete boundary

```js
import { createSearchDialogController } from "./client.mjs";
const { SearchDialog, SearchDialogLazy } = createSearchDialogController(ports);
// A host supplies every listed capability; it renders one returned component.
// SearchDialogLazy({ onMounted }) retains the actual mount effect and child.
```

There are no data, storage, feature, router, service or renderer defaults. One
constructor instance represents one original module instance. The contract's
`requiredFunctions`, `namespaces`, `rendererNamespaces` and `renderers` fields
are the exact interface list, not an inferred SDK or full provider API.

| Capability family                                                                                                                                      | Actual source-shaped boundary                                                                                                                                                                                                                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `React`, `jsxRuntime`, `memoCache(size)`                                                                                                               | Real framework/compiler hooks. Retains every inline memo/state/ref/effect/callback frame.                                                                                                                                                                                                                                              |
| `useSearchOpen()`, `useSetSearchOpen()`                                                                                                                | Supplied snapshots of `617614.F/Z`; setter accepts the boolean used by the owner. The Zustand store/acquisition is not implemented.                                                                                                                                                                                                    |
| `useLocalTerms(key, initial)`, `useRecentCoins()`, `useRecentCards()`                                                                                  | Supplied local-recents hook results. Exact key, remembered-term deduplication/cap, clear callbacks, viewed times, hydration merge and ordering belong to this owner. No actual storage reads/writes.                                                                                                                                   |
| `useFlag(name[, default])`, `useNsfw()`, `useChainFlags()`, `nearEnabled(flags)`, `hexEnabled(flags)`                                                  | Required read-only feature/admission snapshots; three flag strings and two chain IDs are source-authenticated. No configuration, identity or feature-service acquisition.                                                                                                                                                              |
| `useCoinSearch(options)`, `useUserSearch({searchTerm})`, `useCoinHydration(options)`, `useCoinUpdates(rows, enabled)`                                  | The actual imported hook/result boundaries. Existing query/executor/hydration work is credited; no duplicate implementation or real request/subscription.                                                                                                                                                                              |
| `useQuery(options)`, `useInfiniteQuery(options)`, `useQueries(options)`, `useDebouncedValue(value, 500)`, `useQueryClient()`                           | Required query/debounce runtimes. This unit owns the retained inline trending, PnL, Near and group options/callbacks/memos, not TanStack scheduling, debounce timing, retries or provider lifecycle.                                                                                                                                   |
| `queryKeys`, `groupSearchKey(term, size)`, `groupProfileKey(id)`, `keepPreviousData`                                                                   | Required actual query-key/placeholder boundaries. They are cache machinery, not credentials. No invented original key/provider winner.                                                                                                                                                                                                 |
| `useGroupClient()`, `searchGroups({api, searchTerm, offset, limit, signal})`, `projectGroup(row)`                                                      | Source `944410`, `560328.B` and `760447.h` ports. The inline group callback forwards signal/client, hydrates each profile through `setQueryData`, selects flat pages and retains defaults/caps. The external reader/schema/service is not reconstructed. All five physical limit providers agree on page size20 and maximum offset500. |
| `readTrendingCoins()`, `readPnlLeaders({period, sort, limit})`                                                                                         | Existing raw local request helpers retained as cited external reader boundaries. Actual defaults are daily/combined/20 and five-minute stale/ten-minute GC, enabled only when open, no mount/focus refetch. No PnL accounting or backend ranking.                                                                                      |
| `resolveIdentifier(text, signal)`, `getContractClient()`, `readCoin(options)`, `probeKnownMint(text, signal)`, `probeSolanaMint(text, signal)`         | Required read-only resolver/request/probe capabilities. The existing resolver client/Solana core is credited. No service origin, RPC, authentication, session, authorization or response schema acquisition.                                                                                                                           |
| `validSolanaAddress`, `walletProfile`, `isEvmAddress`, `canonicalCoinAddress`, `normalizeHexIdentifier`, `isNearIdentifier`, `isNearCoin`, `isHexCoin` | Supplied admission/normalization/classification functions at the exact imported boundaries. They do not establish account ownership or access.                                                                                                                                                                                         |
| `useRouter()`, `useCoinClick()`, `useLastClick()`, `track*`                                                                                            | Supplied navigation/click/analytics callbacks. The owner retains their argument and call order. `/coin/...` is a navigation string only; excluded coin pages are not implemented.                                                                                                                                                      |
| `browserWindow`, `browserDocument`, `AbortController`                                                                                                  | Explicit DOM listener/focus and local cancellation capabilities. The ordinary JavaScript `DOMException` intrinsic is shared with the inherited navigator module. No clipboard/provider/storage API acquisition.                                                                                                                        |
| `useTranslation`, `classNames`, `styles`, `renderers`                                                                                                  | Exact rendering handoff, including Dialog open/change, Input/form/ref/paste, tabs, section/row/empty/loading/recents/recommendation callbacks. Individual components/providers and visual behavior remain external.                                                                                                                    |
| `isPerp`, `perpDisplay`                                                                                                                                | Deferred Perps classification/display ports. Branches remain in source; finite proof admits ordinary rows only and makes no Perps implementation claim.                                                                                                                                                                                |

## Preserved behavior and limits

- Closing aborts the selected controller, clears controller/paste refs, resets
  query/category and then sets open false. Editing aborts/clears refs before
  changing text. Open/toggle uses the current captured open snapshot.
- Recent terms remove exact duplicates, prepend the term and retain at most19
  previous entries. Recent coin hydration branches by Near feature and chain,
  falls back to original rows, merges cards only under `webPacks` and sorts by
  descending viewed time. These are supplied local records, not acquired data.
- Search invokes coin/user/group ports independently. Mixed sections limit to4,
  skip short user/group terms and expose their exact loading/hasMore state.
  Priority ordinary coins, optional Perps position and selected-tab fallback
  retain the captured operations. No new ranking, filter or error presentation.
- The group hook trims and supplies the debounce boundary, then builds its actual
  callback/key/options. A short final page stops. Full pages continue at total
  raw length unless that total is **greater than**500: exactly500 is allowed.
  Errors remain query results/propagation; the owner does not render a new error
  UI or add retry behavior. Directly invoking a query callback bypasses the
  supplied query runtime's enabled/pause semantics.
- Form submission uses the existing ordered Solana→EVM→long-hex→Near chain and
  exact true/`"cancelled"` stopping tokens, otherwise close/remember/encoded
  Explore navigation. Retained non-Solana handlers preserve their different
  guards, definitive/fallback classification, cancellation checks and catches.
  No broad unified success/error rule is invented.
- Paste consumes **event-supplied text**, normalizes/admit-checks it, preserves
  the input selection and invokes the matching handler without awaiting it.
  It does not acquire the clipboard or implement the excluded QuickPaste action
  workflow. Analytics and click/navigation order remain observable callbacks.
- The input ref preserves focus already inside the supplied dialog; otherwise it
  focuses the attached input. The inherited exact key matcher is installed and
  removed by the retained owner effect. Original parent loader/fallback behavior
  and Dialog/Input focus/dismissal internals remain outside the constructor.
- There is no new resolver-unmount cancellation effect. The key listener cleans
  up on unmount, but a pending operation is not automatically aborted there.
  No stronger cancellation, security or provider-availability guarantee is made.

## Repeat and evidence

From `app/`, using the existing pinned dependencies and Chromium:

```sh
node scripts/original-search-dialog-controller.mjs --check
node --test tests/original_search_dialog_controller.test.mjs
node --test tests/original_search_dialog_controller.browser.mjs
```

The last producer bundles the maintained module and real React/compiler with a
synthetic host. One ephemeral loopback GET server serves only root and bundle.
All data/query/recents/readers/probes/analytics/navigation/rendering capabilities
are explicit synthetic ports. It blocks external requests and real
cookie/storage/Notification acquisition, retains every actual bundled/method
input hash, and closes Chromium/server in `finally`.
`PUMP_SEARCH_DIALOG_CONTROLLER_OUTPUT` saves its finite observations/bindings;
`PUMP_BROWSER_EXECUTABLE` selects an existing executable. It uses no Next,
installation, product fixture or provider HTTP operation.

The standalone renderers provide only the documented port contract. They do
not prove original Dialog/Input/row behavior, a real service, whole search
runtime, lazy loading, auth/provider availability, frontend byte/visual parity,
backend/API/native compatibility or feature completion. SDK, captures, shared
source/graph tools, earlier packages and all progress counts remain unchanged.
