# Original SearchDialog idle Discover strip

The full SearchDialog owner in #1925 supplies idle `topTraders`,
`topTradersLoading`, `trendingCoins`, `trendingLoading` and `onNavigate` props but
leaves this renderer external. This reconstructs the complete `238128.tp`
50-slot owner and inline14-slot scroll store, full53-slot trader and49-slot coin
tiles, loading skeletons,19-slot arrows, selection initializer and used helpers.
Ordinary rows #1937 and recent terms #1962 remain separate credited boundaries.

The generator authenticates singleton238128 (`9e5affaf…`) in raw
`ccb10fa3de5597c4.js`. All19 selected declarations compare as complete strict
ASTs. Only parser positions/comments/raw spelling are ignored; no alpha/type/
branch/operation mask or captured-code execution. Client/contract bytes are
canonical. Actual MAIN/#1925 handoff, flag/event constants, imports and every
inventoried provider variant are bound. No active provider winner is selected.

```js
import { createSearchIdleStrip } from "./client.mjs";
const {
  DiscoverStrip,
  TraderTile,
  CoinTile,
  TraderSkeleton,
  CoinSkeleton,
  Arrows,
} = createSearchIdleStrip(ports);
// Render DiscoverStrip with supplied ordinary rows/loading flags/onNavigate.
```

One constructor is one original module instance. All16 functions,12 renderers
and framework/browser capabilities are required explicitly. No service, storage,
row, formatter or presentation defaults are provided.

| Required capability                                                                                                                          | Actual source interface and limit                                                                                                                                                                  |
| -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `React`, `jsxRuntime`, `memoCache(size)`                                                                                                     | Framework/compiler API; full memo/state and native `useSyncExternalStore` frames remain local.                                                                                                     |
| `browserWindow.sessionStorage.getItem/setItem`                                                                                               | Exact `search.idle-strip` calls through a supplied synthetic memory adapter. Invalid/read-failed values default to hot-coins. State updates before caught write failure. No actual storage access. |
| `browserWindow.matchMedia?`                                                                                                                  | Optional source reduced-motion query and `{matches}` result controls native `scrollBy` auto/smooth. No preference acquisition.                                                                     |
| `MutationObserver`, `ResizeObserver`                                                                                                         | Native-shaped constructors; ResizeObserver may explicitly be undefined. Passive scroll, child-list mutation and optional resize subscribe and clean up exactly as captured.                        |
| `useTranslation()`, `classNames(...)`, `avatarSize`                                                                                          | Existing translation/style/sizing ports; retained `$ = k.s.comfortable` uses the supplied comfortable size.                                                                                        |
| `useFlag(key)`, `useProfile({address,enabled})`                                                                                              | Exact webAvatarDecorations key and existing profile hook; supplied snapshots/results only, no config/account/auth acquisition.                                                                     |
| `pnlTone(value,0)`, `formatPnlUsd(value)`, `formatPnlPercent(value)`                                                                         | Exact display formatter ports for supplied fields, no financial/ranking/accounting computation.                                                                                                    |
| `useLiveMarketCap({mint,chainId,fallbackMarketCap,coin})`, `formatMarketCap(value)`                                                          | Existing cap result/formatter; local nullish fallback retains zero. No price read or inferred financial data.                                                                                      |
| `useCoinImpression(mint,props,undefined,sourceElement)`                                                                                      | Exact index/rounded cap/source descriptor and returned ref. Metrics remain supplied.                                                                                                               |
| `useCoinClickHandlers()`, `useImpressionContext()`                                                                                           | Returned `handleCoinClick` / `setLastClickImpression`; source order is last-impression, coin-click, incoming callback. Inert recorders only, no protected action/navigation implementation.        |
| `useCandlesticks(mint,created_timestamp ?? null,undefined,{chainId})`                                                                        | Supplied `{candlesticks,error,isLoading}` handed to external Sparkline; no chart reader/provider/data service.                                                                                     |
| `cleanSymbol(value)`, `usePrefetch(coin)`                                                                                                    | Actual formatter and `{prefetch,hoverProps}` ports; explicit source onClick overrides hover onClick. No prefetch service.                                                                          |
| `Heading`, `Empty`, `SkeletonPart`, `Link`, `ProfileDisplay`, `SegmentedControl`, `CoinAvatar`, `CoinName`, `Sparkline`, arrow icons/buttons | Twelve renderer APIs retain exact source props. Existing Avatar/decoration/chart/helper work is credited, not copied or combined-runtime qualified.                                                |

Availability includes loading or nonempty data. An unavailable picked list falls
back to the other available list without overwriting selection or supplied
storage; neither available displays the captured empty message and disables both
choices. Loading renders5 skeletons. Strip key changes with available selection.
Native extent checks retain the source1px tolerance and page by clientWidth.

Trader tiles preserve username/fallback, decoration, no-link/no-hover profile
props and formatter calls. Coin tiles retain chart/timestamp/cap/symbol and
instrumentation order. `/coin/{mint}` hrefs remain metadata only: excluded detail
pages and actual navigation are not implemented/exercised. Profile routing uses
the accepted unchanged helper. No parent state, history/query implementation,
service/config/account/cookie/credential acquisition or protected action is added.

From the repository root with existing pinned dependencies:

```sh
node app/scripts/original-search-idle-strip.mjs --check
node --test app/tests/original_search_idle_strip.test.mjs
node --test app/tests/original_search_idle_strip.browser.mjs
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
python3 app/scripts/verify-evidence.py
```

The finite proof supplies synthetic rows/provider results and memory storage/
motion ports, with real React/compiler/context, native geometry/scroll/observers
and trusted clicks. Only local root/bundle GETs are permitted; actual storage,
cookies and provider requests are blocked. This is bounded source/workflow proof,
not product/Next/full-app/visual/native/API/backend/security/accounting/feature
completion or combined #1925 qualification. Immutable captures/SDK/helpers and
feature progress are unchanged.
