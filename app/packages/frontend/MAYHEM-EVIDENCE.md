# Mayhem screener reconstruction evidence

This document separates captured facts from local implementation choices. The
reconstruction never imports or executes recovered factories.

## Observed

The capture manifest was recorded at `2026-10-28T10:48:45.546100+00:00`.

| Factory  | Factory SHA-256                                                    | Captured object / SHA-256                                                                  |  UTF-16 range | Finding                                                                                                |
| -------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ | ------------: | ------------------------------------------------------------------------------------------------------ |
| `457065` | `fdc0ca7368bc30aecfa5cddc5930467b1ad51eb7c605cb109ba29e8551b13206` | `b5dd8c92e81b5961.js` / `5c37df61d37f2fe137803f151669385df362c5bca3cf4da12e2753bb07c90869` |   14752–32119 | Screener layout, four filters, four sort keys, row fields, loading/error/empty states, ten-row paging. |
| `985722` | `db8a6d669d7c3a8dedf92a8c926999dd0f530ff88ba2ba6926b7b41b0967d635` | `2b47dd0b38a1608f.js` / `e78d2f38b06f971847c18dd05457c75afc85208135f50d6e4022a5f197e8839d` | 100948–124759 | `GET /coins/mayhem-mode`, query bounds and response declaration.                                       |
| `38279`  | `8d71db5a2d47da722166199f0a64e93e0295051da46086355f136b93a3f3b89a` | `ad7136d0b3a7f323.js` / `ee1eb91e3cbfb10fa33462a1a2f500fed9902a88454dc715f059d56f405475b3` |     260–12654 | First-party client origin and request construction.                                                    |

The formatted recovered files have SHA-256 values
`6e54cd1402eda8c6b77fba8f9c79c6034669aa7d1d7cc6d39a0adcdea70335ed`,
`38393f04559b7a8683036daa46409256994618aa88d1699f9772992c2e51bc1d`,
and `0467a285c03eb766ffd00f7260777cc04d8df7a8f91d401733d35788f5f33ab0`
respectively.

The captured `/mayhem` HTML is
`evidence/web/objects/0c1c38e553b5ee46` (SHA-256
`13c794c2602f465fd458974dbfc093dc28c2273a0574a485171e9c08010417f5`).
It establishes the “Mayhem screener” heading and the shared dark Pump shell.

The observed filter mapping is:

- `all` → omit `mayhemState`;
- `active` → `active`;
- `paused` → `paused`;
- `ended` → `completed`.

The request defaults are `limit=60`, `offset=0`, and `includeNsfw=false`.
The captured limit maximum is 60 and offset maximum is 1000. The observed sort
keys are `lastTraded`, `volume`, `mcap`, and `newest`. `lastTraded` preserves
the service order; the other modes sort descending by 24-hour USD volume, USD
market cap, and creation timestamp. Missing numeric values compare as zero and
ties retain input order.

## Declared

The captured client declares `https://frontend-api-v3.pump.fun` and
`GET /coins/mayhem-mode`. `internal-operations.json` inventories that read but
does not qualify a native implementation. The website endpoint is not treated
as the separately documented developer API.

## Inferred

The table hierarchy and fields support coin identity, state, mode, creation
time, market cap, and market activity display. A string found in a recovered
factory is not proof that every field was present at runtime.

## Local design

- State and sort are URL-backed so refresh and browser history are deterministic.
- Production calls only a same-origin read-only adapter. Because no archived
  Mayhem response is checked in, that adapter returns an explicit unavailable
  response and never proxies the captured origin.
- Strict validation accepts successful data only from the visibly labelled
  synthetic browser-test source. Test data is not compiled into a production
  fallback.
- Invalid values normalize to `all` and `lastTraded`; request bounds fail closed.
- Abort controllers and sequence identities prevent stale responses replacing
  newer filter results.
- The original coin-detail action is omitted because `/coin/:mint` is excluded.

## Unknown

Current live coin contents, service ranking, current market values, production
availability, exact live retry policy, and a matching original data-state
screenshot are unknown. No wallet, trading, token creation, or mutation behavior
is implemented.

## Qualification

`tests/mayhem_screener.test.ts` checks the contract, bounds, validation, and all
sort modes. `packages/frontend/tests/mayhem.spec.ts` exercises the running app,
URL history, loading/empty/error states, stale-request rejection, four target
viewports, excluded routes, and the no-external/no-mutation boundary.

Screenshots in `packages/frontend/visual/mayhem-20261028/` are local acceptance
evidence. They are not claims of original pixel parity.


## Local pending-selection repair

State and sort navigation must preserve both requested choices while a React
Server Component (RSC) navigation is pending. On the previous implementation,
selecting Active and then 24h volume before the first request completed dropped
Active. Reversing those actions dropped the sort. Both cases are reproduced by
holding the real local RSC requests; no Mayhem data response is substituted.

The component now composes changes against its latest requested selection.
Committed route props restore the history state. Next Link's `onNavigate` keeps
ordinary link destinations and modified/new-tab clicks intact. The two added
cases in `tests/mayhem.spec.ts` verify both orders and Back/Forward, alongside
the seven existing cases. Desktop/mobile recordings show the same interaction
before and after. The unavailable-data boundary and source/qualification claims
above remain unchanged; this does not qualify the upstream service or market data.
