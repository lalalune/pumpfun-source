# Captured Explore board response boundary

This completes the editable **response normalization boundary** following merged
[#695](https://github.com/lalalune/pumpfun-source/pull/695)'s board request
attribution. It adds no mounted Explore behavior, backend, network destination,
dataset, ranking engine or feature-progress credit. The existing historical
one-coin Explore fixture remains unchanged.

## Actual request to response

The existing request verifier authenticates initial-script hook379705 and its
583448 request helper: featured selects movers, trending selects trending; the
caller supplies limit300 and the builder caps it at150. Its observed origin is
advanced-indexer, not the other website contract client's frontend-api-v3 host.
This is existing #695 attribution, not rediscovered work.

The captured hook fetches with `credentials: include`, rejects non-OK status,
reads JSON and calls `583448.$(json)` with **one argument**. That wrapper calls
`503774.q(json, offset)`, where offset is consequently undefined. The response
normalizer retains served order and does not add `rec_rank` in that actual path.
It uses the **response's** board and timestamp. The hook then calls493025.f,
which mutates image/metadata URI and alias fields, applies an optional filter,
and on the normal featured/trending path slices the displayed page locally.
Those later image/filter/state operations are bound as evidence, not implemented
by this adapter. The captured150-result cap therefore does not establish
server pagination, total catalog size or a complete native discovery service.

`contract.json` independently authenticates both retained503774 factories:

| Physical object | UTF-16 range | Factory SHA-256 |
| --- | --- | --- |
| `3740fc4e7a24596d.js` | `[64165,67638)` | `609398a036a8f03009d8e18f6218b0db40076b5a728a62b1014447cd99fcc326` |
| `cf2bb278631744da.js` | `[17427,20900)` | `dbed6512bf8d85a7a28e44bfd719c9b2b3370bd2ec239920c5a4c8c4f3e93acf` |

It retains raw UTF-16/UTF-8 expression witnesses for both complete coin mappers,
q and seed exports, cache/clock expressions, every projected field and optional
assignment, plus the actual hook handoffs. The reviewed common q/d/cache behavior
is source-adapted by hand; byte identities are not an automated proof of full
semantic equivalence. No global registration/cache winner is selected, no shared
graph resolver is changed and no captured JavaScript is executed.

## Maintained adapter and capabilities

`createBoardResponseAdapter({ nowMs, isEvmRecord, retainChainId })` returns
`mapCoins(response, optionalServedRankOffset)` and `seedTimestamps(initialCoins)`.
Keep one instance for one modeled module lifetime; separate instances have
independent caches. No hidden clock, chain registry, cookies, session, fetch or
provider is created. All three functions are required and their exceptions
propagate. The contract binds their actual source boundaries:

- `nowMs`:668487.t reads `Date.now() + offset`. Supply an epoch-millisecond
  clock matching that convention. Its offset-fetch/refresh service is outside
  this unit; a monotonic-duration clock is not a substitute for it.
- `isEvmRecord`:605587.N considers explicit chain context and mint prefix. Its
  registry-dependent chain helper remains supplied, not guessed from an address.
- `retainChainId`: the actual605587.g OR646908.L OR541710.T-nonnull expression.
  Its registry dependency likewise remains explicit.
  All three indexed541710 T variants are separately authenticated, including
  each503774 chunk's local provider. Their real646908 import aliases resolve to
  the same Near/Starknet predicate; this does not select an active provider.

The adapter preserves concrete normalization behavior:

- Missing/non-array `entries` yields[]; entries otherwise map in served order.
  It is **not a DTO validator**: malformed entries can throw. Source presentation
  defaults, including zero reserve/supply fields, are not verified chain facts.
- Only finite positive numeric `serverTs` bypasses the clock. Otherwise the
  clock is read once per visited entry, before EVM classification, even if age
  is invalid. A non-finite/non-numeric age yields null; arithmetic output is not
  additionally range-sanitized.
- Age is converted to milliseconds. A module-lifetime Map keyed only by the raw
  mint reuses an existing timestamp when absolute difference is **strictly
  below60,000ms**. A hit does not refresh insertion order. At4,000 entries the
  oldest inserted key is deleted **before** deletion/reinsertion of a replaced
  mint, including replacement at capacity. No chain qualifier or case folding is
  invented. Earlier successful entries can change the cache before a later row
  throws; there is no transactional rollback.
- Seeding accepts positive finite timestamps for truthy, previously unseen mints;
  it never overwrites a known mint. The same4,000-entry eviction rule applies.
  The captured initial consumer calls it only for `initialCoins && Q`, whereQ
  is the `social-terminal` mode predicate; no unconditional seeding behavior is
  attributed to Explore. The method itself does not create that mode provider.
- Program aliases/fallbacks, holder zero suppression for EVM, strict-true flags,
  truthy optional IDs and followed-holder nullish defaults are retained. The
  response board controls the unknown-program fallback. Rank coercion is not
  silently replaced by an integer-validation policy; the actual hook omits it.

Stats exportsJ/Z, metadataH and predicate t are not adapted here. Their omission
does not affect q/d/$ behavior. The upstream hook's result cache, authentication
readiness, retries, cancellation and refetch lifecycle remain separate.

## Reproduce and limits

From `app/` with documented pinned dependencies:

```sh
node scripts/verify-market-board-response.mjs --check
node --test tests/market_board_response.test.mjs tests/market_board_response_bindings.test.mjs
```

`--write` regenerates only this derived contract after source review. Direct
semantic checks cover defaults/served order, malformed entries, port order and
exceptions, server timestamps, the60s boundary, cache cap/eviction/seeding,
classification-dependent fields, followed holders and rank coercion. Source
checks authenticate both real variants and reject changed captured bytes or
maintained-adapter drift. These tests run maintained code with finite synthetic
values; they are not acquired board results or original runtime execution.

**No acquisition was attempted.** Credentials-including fetch and the hook's
authentication-readiness prerequisite do not establish anonymous/public access.
Server validation/ranking/filtering/auth/errors, current values, actual provider
clock/classification services, configured production requests, pixel parity,
native API compatibility and security equivalence remain unqualified.
