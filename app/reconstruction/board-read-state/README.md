# Explore board owning-hook frame

This source adaptation restores the complete used `379705.f` React hook frame
for non-search `FEATURED` and `TRENDING` inputs. Main `094a06f1` already contains
the request builder and shared search executor, but no executable board owning
frame joining their refs, effects, initialization, callbacks and state keys.
The actual `228998` Explore consumer and its initial-coin/local-filter handoffs
are retained as source witnesses. This module is not mounted in the product.

The generator authenticates all four physical hook variants, their module
imports, raw UTF-16/UTF-8 ranges and complete alpha-equivalent function ASTs.
It retains the full 577-line owning function. Only its query-builder and shared
executor callback bodies bridge to the existing accepted implementations; the
verifier restores those original bodies and compares the complete frame again.
Array binding positions and arity are preserved in a marked tuple representation
for the existing alpha comparator. No capture is executed. The contract and
editable module are verified as exact canonical bytes.

Reused work, without new recovery credit:

- [Request transport #695](https://github.com/lalalune/pumpfun-source/pull/695):
  `market-boards/request.mjs`, including the request cap of 150.
- Existing `search-session/session.mjs` shared executor/cache and `493025`
  postprocessor, plus `search-planner/planner.mjs` query construction.
- [Open response unit #1761](https://github.com/lalalune/pumpfun-source/pull/1761),
  public `07d93a198ff472ff11f278337d5481a3b4e21d51`, is **not imported or copied**.
  Supply one instance's `mapCoins` and `seedTimestamps` as `parseBoard` and
  `seedBoardCoins`. The actual hook calls each with one argument; it supplies no
  served-rank offset. Normalization, classification and timestamp-cache behavior
  are capabilities, not new implementations in this unit.

`createBoardCoinHook` requires explicit React hooks, shared cache, epoch clock,
AbortController, destination, fetch, response/seed operations, read-only
viewer/session/variant/exposure/IPFS snapshots, identity result, debounce,
LIVE-interval and timer/logger ports. Identity's `deviceId`, `sessionId` and
`sessionStartTimestampMs` are source-bound result fields, not acquired values.
No auth, cookie, storage, device, provider or session acquisition is implemented.
Authentication readiness is a source control-flow input, not proof of access.

The local adapter admits only the two board sorts outside search mode and exposes
their used return view. Other branches are retained in the source frame for
attribution but not exposed or qualified. Preserve one shared cache and the same
clock for the hook and cache. The LIVE interval port must return strict `false`
when its second argument is `false`: the original effect distinguishes that
value from a number. Both board branches pass `false`; there is no board timer
or newly invented foreground/pause subscription.

Observed boundaries include:

- Truthy initial rows initialize the loaded key; only social-terminal mode
  seeds timestamps. Trending also retains the initial served array.
- Movers passes the selected chain; trending omits it and uses the request
  builder's all-chain default. The hook requests 300, capped by the credited
  builder, without a wire offset. Default slicing is local. A true
  `forceLocalFiltering` hands the full normalized array to the outer filter
  owner, whose downstream rendering/filter policy is outside this unit.
- The eleven-field render key excludes viewer identifiers. Address changes can
  cause a background refresh; changing only user ID does not add an automatic
  effect read. Retained callbacks keep their original closure values.
- Shared executor cache age exactly 120,000 ms remains valid, and a cache hit
  still refreshes. Foreground/background errors, keyed state, sequence checks,
  native abort and cleanup retain the existing executor's semantics, including
  its unconditional final abort-ref clear. No stronger cancellation guarantee
  or per-viewer cache ownership is inferred.

From `app/`, using the pinned dependencies already installed:

```sh
node scripts/original-board-read-state.mjs --check
node --test tests/original_board_read_state.test.mjs
node --test tests/original_board_read_state.browser.mjs
```

The last command starts one ephemeral loopback GET-only proof host and Chromium,
then closes both. It bundles only the maintained module and a synthetic real
React host, not captured JavaScript. Response and identity capabilities return
fixed synthetic outputs and do not implement the original providers. It checks
real request/response/state/abort behavior without live discovery, credentials,
browser storage or cookies. Set `PUMP_BOARD_STATE_OUTPUT` to retain its JSON
observations; optional `PUMP_BROWSER_EXECUTABLE` selects an already installed
Chromium executable. There is no installation, Next server or product fixture.

This is bounded source reconstruction and finite synthetic lifecycle proof.
Original provider availability, auth/authorization, response implementation,
full React/runtime equivalence, downstream page filters/rendering, live market
data, ranking, backend/API/native compatibility, visual parity and feature
completion remain unqualified. No source inventory or completion counts change.
