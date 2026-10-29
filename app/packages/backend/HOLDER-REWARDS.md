# Opt-in local holder-rewards book (page mode)

`GET /services/frontend/fees/holder-rewards` serves page mode of the captured
website operation `GET /fees/holder-rewards` from one explicitly supplied local
book. Without `holderRewardsStore` / `HOLDER_REWARDS_FILE` the route is not
registered and the existing fixture replay or `501 COMPATIBILITY_NOT_IMPLEMENTED`
remains. There is no default dataset. This is not original backend source, an
indexer, a price service, claims, authentication or a qualified compatible service.

It is the first native route in the ledger's backend family "Rewards / fees /
referrals" (`/fees`), and the data the Holder rewards page's ledger note says it
cannot yet establish: accrued and paid holder rewards per coin.

## Evidence

- Declaration: `evidence/web/objects/2b47dd0b38a1608f.js`
  (`https://pump.fun/_next/static/immutable/chunks/2cr_aqnw2j4n5.js`, SHA-256
  `e78d2f38b06f971847c18dd05457c75afc85208135f50d6e4022a5f197e8839d`), factory
  **698550** `[163764,180401)` SHA-256 `f677a629…a787d` (the same factory
  `../frontend/HOLDER-REWARDS-EVIDENCE.md` cites). The route entry is UTF-16
  `[173422,178279)`, SHA-256
  `093e0f36314336df90f332586fa48d3f9c5f56ce5f99f94ae643b1604c53eb17`.
- [`../../contracts/original-holder-rewards.json`](../../contracts/original-holder-rewards.json)
  holds the query and response converted from that AST by
  `scripts/original-contracts/holder-rewards.mjs`, with every fragment's UTF-16
  and UTF-8 range and hash. No captured JavaScript is evaluated.
  `tests/original_holder_rewards.test.mjs` regenerates it from the frozen
  captures and compares byte-for-byte, as the other original-contract units do.
- Reachability: across every authenticated JS capture, only the declaration
  names this operation. No captured caller, service origin or authorization is
  observed, and none is claimed.
- Context, not binding: the sibling fee reads in factory **99415**
  (`994c0030bcc62017.js`) call `GET /fees/coin`, `/fees/creator` and
  `/fees/shareholder` through `759257.j`, whose origin is `503630.R`
  `https://frontend-api-v3.pump.fun`. The route therefore sits beside Home Feed
  under `/services/frontend`, the local website namespace, outside the
  developer API-key gate. The developer `/v1` surface is unchanged.

## Converter extension

The declaration uses two Zod forms the shared converter rejected until now:
`z.record(key, value)` (the `quotes` map) and a flagless `.regex(/…/)` (the
`quote` filter). `schema.mjs` now emits them as JSON Schema
`propertyNames`/`additionalProperties` and `pattern`, and `validate.mjs` checks
them. Record keys and values are all checked; named object shapes still accept
extra fields. Only an open `z.string()` record key is reproduced: Zod requires
every key of an enum-keyed record, so any other key schema still fails closed.
No existing contract used either form, and every existing original-contract
test still passes against its committed artifact.

## Supported request and explicit boundaries

- **Page mode** is any request carrying `sort`, `direction`, `quote`,
  `payingOnly`, `page` or `limit`, the six parameters the `cursor` description
  calls exclusive with it. The `next` description names only page/limit/sort,
  so treating `quote`, `payingOnly` or `direction` alone as page mode is a
  local reading. Defaults: `sort=accrued`, `direction=desc`, `page=1`,
  `limit=50`, limit 1–2000.
- **Cursor mode**, including a bare request (the declared default order is
  `accrued.usdAtTrade`, then `usdNow`), returns `501` with reason
  `CURSOR_MODE_UNAVAILABLE`. `sort=accruedNow` and `sort=distributed` order by the
  current quote mark and return `501` `CURRENT_MARK_SORT_UNAVAILABLE`. Neither
  falls back to a guessed page.
- `cursor` together with a page parameter, and unknown, duplicate or malformed
  keys, are local `400`s with a `field`. All parameters are validated before the
  current-mark `501`, so a malformed request is always a `400`. `page` and
  `limit` take canonical positive integers, `payingOnly` takes `true`/`false`,
  and `quote` uses the declared base58 regex. A page whose offset would exceed
  `MAX_SAFE_INTEGER` is a `400`.

## Local policies (not observed upstream)

- Sort keys: `accrued` = `accrued.usdAtTrade` (compared as an exact decimal),
  `lastPayout` = `payouts.lastPayoutAt`, `wallets` = `payouts.recipientCount`,
  `trades` = `accrued.numTrades`, `lastTrade` = the row's `lastTradeAt`.
  `direction` orders non-null keys; null keys always sort last; ties use exact
  code-unit `mint` order. Decimal keys are parsed once to integers at the book's
  widest scale, and each sort/direction order is built on first use and reused,
  so a request costs one filter and a slice, never a sort. The route needs no
  key, so this matters: sorting a 100,000-coin book per request blocked the
  event loop for seconds.
- `quote` filters on the row's `quoteMintAddress`. A coin is *paying* when
  `payouts.paidToHolders` is non-null (declared: null when the index has no
  holder payout), for both `payingOnly` and `totals.payingCount`.
- `matchingCount` and `offset` follow the request filter. `quotes`, `totals`
  and `byQuote` describe the whole book and never change with the page
  (declared). `next` is always `null` in page mode (declared).
- The route sets no `Cache-Control` of its own, as declared. Responses carry
  `X-Reconstruction-Data-Source`, `X-Reconstruction-Observed-At` and
  `X-Reconstruction-Compatibility: local-unqualified`.

## Supplied book and checks

`HolderRewardsDataset` in `src/holder-rewards-store.ts` is a **local schema**:
`schemaVersion`, `dataSource` (`synthetic` | `local-materialized`),
`observedAt`, `generatedAt`, and `coins`, `quotes`, `totals` and `byQuote`
shaped exactly like the declared response. Each object must have exactly the
declared keys. Construction rejects the book when:

- a value breaks the declared type or the local input domain: canonical
  millisecond UTC timestamps no later than `observedAt`; non-negative decimal
  strings; integer atomic strings; non-negative safe-integer counts and
  `decimals`; non-empty mints, PDAs and keys. Display strings (names, symbols,
  image URIs, socials) may be empty, as `z.string()` allows. `opsCharge` has no
  declared unit and stays opaque text;
- a mint repeats, or `firstTradeAt` is after `lastTradeAt`;
- `quotes` is not exactly the set of mints the coins accrued or paid in plus the
  `byQuote` mints (declared), or a key differs from its `mint`;
- `paidToHoldersUsd` is set while the quote amount or USD price is unknown
  (declared);
- a declared total disagrees with the rows: `coinCount`, `payingCount`,
  `payoutCount` (the sum of `payouts.payoutCount`) and `walletsRewarded` (the
  per-coin sum) must match exactly, and `walletsRewardedDistinct` must lie
  between the widest single coin and `walletsRewarded`.

The USD totals, `unpricedCoinCount` (bounded by `coinCount`) and the `byQuote`
facets (counts bounded by the book) are **producer-asserted**. Their per-coin
attribution and decimal formatting are not established by the declaration, so
they are served as supplied rather than recomputed.

Set server-only `HOLDER_REWARDS_FILE` to a local UTF-8 JSON file, or inject
`new HolderRewardsStore(book)` into `buildApp([], { holderRewardsStore })`. The
loader refuses symlinks on every platform, including Windows where `O_NOFOLLOW`
is undefined (the open PR #1298 approach), binds the opened handle to the
checked path, reads at most 64 MiB, decodes UTF-8 fatally and closes its
descriptor in `finally`. Limits: 100,000 coins and 1,000 `byQuote` facets. The
store deep-freezes its own copy, so neither the input nor a response can change it.

## Verification

Based on main `665499915f9caedcd38921d415a90f0606686398`, Windows 11, Node
24.12.0, pnpm 10.24.0 (`--frozen-lockfile`). Before the change the route had no
handler and returned `501` (the first test keeps that as the no-book result),
and main's converter stopped on this declaration with
`unsupported schema method regex on string`.

From `app/packages/backend`:

```sh
node --import tsx --test test/holder-rewards.test.ts   # 11/11
node --import tsx --test test/*.test.ts                # 969 pass, 5 skipped, 1 fail (below)
./node_modules/.bin/tsc --noEmit
./node_modules/.bin/tsc --noEmit --strict --target ES2022 --module NodeNext \
  --moduleResolution NodeNext --esModuleInterop --resolveJsonModule \
  --skipLibCheck --types node test/holder-rewards.test.ts
```

From `app/`:

```sh
node scripts/original-contracts/holder-rewards.mjs --check
node --test tests/original_holder_rewards.test.mjs     # 4/4
node --test tests/original_*.test.mjs                  # 525/528 (below)
python3 scripts/progress.py --check
```

From the repository root: `python3 scripts/verify_evidence.py` (9 captures)
and `python3 scripts/test_tooling.py` (10 tests) pass.

Failures, unrelated to this unit and reproduced on unmodified main: the payouts
`startup loader rejects symlink files when creation is permitted` test fails on
Windows with Developer Mode on (fixed by open PR #1298), and three
`original_*_browser` tests cannot launch Playwright Chromium, which is not
installed on this host. All requests use in-process `Fastify.inject` with
synthetic identifiers. No feature milestone, compatibility count, upstream
parity, origin binding or security property is claimed.
