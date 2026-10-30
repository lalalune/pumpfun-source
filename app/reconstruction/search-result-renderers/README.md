# Ordinary shared-search result rendering family

The owning SearchDialog in #1925 intentionally leaves result renderers external.
This unit restores that **complete ordinary result display family** from the
same singleton raw factory238128/`9e5affaf…`, including its actual MAIN
single-row and mixed-result call sites. It does not copy the owning state/query
frame or import unmerged code silently.

The source generator checks strict complete ASTs for `Z` (dispatcher), `Y`
(ordinary coin row), `ee` (user row), `en` (group row), `et` (skeleton), `ed`
(preview section), `eu` (mixed results), the used SVG icon and five shared local
constants. It preserves the complete memo frames, declarations, operations,
fields, arguments, JSX keys, callbacks and ordering. Only parser location,
comment and raw-spelling metadata are ignored. There are no alpha/type/branch/
operation masks and no captured-module evaluation.

The contract authenticates physical source ranges/UTF-8 bytes/SHA-256s, the
actual imported bindings, every inventoried provider variant, source enum
values, free-binding closure and exact canonical module/JSON bytes. It also
binds the owning `tg` call sites and row-selection callbacks credited to #1925.
A provider list is not an active-runtime winner or a recovered provider.

## Explicit API and dependencies

```js
import { createSearchResultRenderers } from "./client.mjs";
const results = createSearchResultRenderers(ports);
// results: CoinRow, OrdinaryCoinRow, UserRow, GroupRow, Skeleton, MixedResults.
// A host supplies all capabilities and renders the returned components.
```

These component names/signatures match the corresponding renderer boundaries
of #1925; composing those units requires an explicit dependency selection and
the remaining parent renderers. This packet qualifies its own source family
and finite host, not a combined full-dialog/product runtime.

| Required capability                                                                | Exact boundary retained                                                                                                                                                                                                                                                  |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `jsxRuntime`, `memoCache(size)`                                                    | Real JSX/compiler runtime, retaining all component memo frames.                                                                                                                                                                                                          |
| `useTranslation()`, `classNames(...values)`                                        | Required translation/style operations. `theme` supplies original-used `x/n/B/Y/e/C[comfortable]` and `N` token fields; `styles.row/seeAll`, explicit `avatarSize` and `imagePrefix` supply the other presentation boundaries. No visual/theme compatibility is inferred. |
| `useCoinMarketCap({mint, chainId, fallbackMarketCap, coin})`                       | Supplied current-market-cap snapshot. Nullish snapshot falls back to raw coin market cap; zero remains a selected snapshot. No market service/query/cache acquisition.                                                                                                   |
| `useCoinImpression(mint, metadata, searchTerm, sourceElement)`                     | Supplied ref/analytics boundary; the owner retains the original row ref and metadata object.                                                                                                                                                                             |
| `useCoinClick()`, `useLastClick()`                                                 | Return `handleCoinClick` and `setLastClickImpression`. Row click calls last-click, coin-click and its parent callback in that order, sharing metadata and term.                                                                                                          |
| `useCoinPrefetch(coin)`                                                            | Supplies `{prefetch, hoverProps}`. The original spread precedes its owned click handler; provided hover click does not replace that handler. No actual prefetch runs in proof.                                                                                           |
| `formatSymbol`, `shortenAddress`, `formatMarketCap`, `formatFollowers`             | Existing source-shaped formatting ports. This unit owns their real caller inputs, not their internals or financial precision/accounting.                                                                                                                                 |
| `useVerifiedProfile(subject)`                                                      | Actual `179736` lookup hook port, credited to OPEN #1841. It receives the source `userId ?? address` before display. No identity/provider/authentication acquisition or badge trust.                                                                                     |
| `groupRoute({groupId, username})`, `normalizeImage(value)`, `projectGroup(rawRow)` | Required group route/image/projection ports. Mixed results display the projected descriptor but its selection callback retains the original raw row. No group reader/service/schema or image fetch is implemented.                                                       |
| `trackBookmark(options)`                                                           | Source analytics sink used only by the supplied menu descriptor callback for an add action. No menu action is executed in proof.                                                                                                                                         |
| `isPerp`, `perpDisplay`, `renderers.PerpRow`                                       | Required deferred Perps boundaries of the retained dispatcher. This packet admits ordinary rows only and does not implement or qualify Perps.                                                                                                                            |
| `renderers`                                                                        | Required `BookmarkMenu`, `CoinAvatar`, `CoinName`, `RelativeTime`, `Link`, `ProfileDisplay`, `SkeletonPart`, `Avatar`, `GroupIcon`, `Badge`, `Heading` and deferred `PerpRow`. No defaults, acquisition or placeholder implementations.                                  |

Avatar705313/fallback/decorations (#1916/#1927), verified-profile/693124 (#1841),
existing RelativeTime, formatting, prefetch, impression, query/cache and render
work remain credited external APIs. The accepted `search-navigation` profile
route helper is imported and verified unchanged. The source-scope audit is
reused proof infrastructure credited to #1925, not a separate recovery claim.
No shared source/graph helper, product component, SDK or capture is modified.

## Preserved ordinary data and interaction behavior

- Coin analytics metadata rounds a truthy raw market cap through its actual
  `Number(value.toFixed(2))`; zero uses0. Its displayed value instead uses the
  supplied nullish snapshot fallback. These distinct original UI computations
  are not a new market price, accounting or ranking model.
- Source-screen/element defaults apply only to undefined; explicit null stays
  null. Index metadata is zero-based while the supplied menu position is
  index+1. `rec_id` and search term retain their original positions/identity.
- The row passes the coin, position and analytics descriptor to its supplied
  menu renderer. It implements no bookmark/trade/protected action and executes
  no such action during qualification. Coin links remain navigation strings;
  excluded detail pages are not implemented or visited.
- Age rendering is selected by the original timestamp truthiness check. A
  truthy value reaches the supplied age renderer with suffix false; a falsy
  value uses the unknown-date translation. No clock/timer/provider is acquired.
- User display name chooses truthy wallet label, username, address prefix then
  anonymous translation. Description instead distinguishes undefined wallet
  label from a defined empty label, and handles strict-false Pump-user status.
  Raw display address remains unchanged while the inherited route helper trims
  and encodes its selected address/userId. Missing identity adds no invented link.
- Group username fallback, member-count translation, badge/avatar props and
  route/projection inputs retain their source definitions. Mixed group selection
  returns the original row, not its projected display descriptor.
- Section visibility gates mapping/rendering. A loading visible section renders
  its exact two-row skeleton; its SeeAll follows hasMore even while loading.
  Mixed sections retain source order, keys and callback row identity. No extra
  empty/error/retry/provider behavior is added.

## Repeat

From `app/`, with pinned dependencies and an existing Chromium:

```sh
node scripts/original-search-result-renderers.mjs --check
node --test tests/original_search_result_renderers.test.mjs
node --test tests/original_search_result_renderers.browser.mjs
```

The finite browser producer uses actual React/compiler/context rerenders with
explicit synthetic provider and renderer values. An ephemeral loopback host
serves root and bundle only, blocks external/cookie/storage/Notification access,
records actual bundled/method input hashes and closes browser/server in finally.
`PUMP_SEARCH_RESULT_RENDERERS_OUTPUT` saves its observations/bindings;
`PUMP_BROWSER_EXECUTABLE` selects an existing executable. It does not start Next,
install dependencies, mount a product fixture or send provider requests.

The host's link/display/avatar/query/formatting values are supplied ports,
not original provider implementations. Perps and menu action callbacks are not
executed. No auth/session/credential/cookie/storage/clipboard/service acquisition,
protected write, live price/discovery/image request or captured-code execution.
No full original runtime/visual/security/native/API/backend/feature-completion
qualification or progress milestone is claimed. Earlier packets remain unchanged.
