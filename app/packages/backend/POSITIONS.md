# Opt-in spot positions read model

This independently implemented backend reads an explicitly supplied local
materialization. It is **not** the original backend source, a chain indexer,
production Pump data, fixture replay, or qualified API compatibility. No default
position seed is shipped or enabled. The existing `/portfolio` Solana RPC UI is
unchanged.

## Implemented slice

- `GET /v1/user-positions/:userId`: exact identity/alias lookup, CSV mint selection
  (at most 200 entries), one row per requested mint, deduplication, optional author
  update enrichment (`updatesLimit` 0–20, default 5), null/absent preservation.
- `GET /v1/user-portfolio/:userId`: `OPEN`/`CLOSED`/`ALL`, `PNL`/`POSITION_SIZE`/
  `RECENCY`, chain and public spam filtering **before** count and pagination,
  `totalsOnly`, chain-matched coin joins, and truthful `updatesApplied`.

These handlers are registered only when `buildApp` receives a `positionsStore`.
Without one, the existing explicit fixture/501 harness remains unchanged. With
one, these handlers take priority over matching fixtures. Both remain inside the
existing developer API-key gate. No website-origin aliases, session ownership,
production proxy, external requests or mutation endpoint are added.

Successful replies carry `X-Reconstruction-Data-Source` (`synthetic` or
`local-materialized`), `X-Reconstruction-Observed-At`, and
`X-Reconstruction-Compatibility: unqualified`. Classification is an operator
assertion, not an authenticity proof. The observed timestamp is the imported
snapshot's stamp, never relabeled as a live observation.

## Evidence and confidence

The public developer OpenAPI snapshot is version **0.294.0**. The two paths are
in `contracts/developer-bindings.json` under `positions.read`, with declared
origin `https://api.pump.fun/v1`; website call origin remains unresolved.
The source checkpoint used here is `2fc654a20e9c7be2b9529f585942bb82c4c83ab2`.

| Captured factory | Exact UTF-16 half-open range | What it establishes |
| --- | --- | --- |
| `967229`, `fb9c61590f587e16e63242c58f343055cdcb029d2a2c6931df051f78f41b6876` | `2b47dd0b38a1608f.js` `[391539,392690)` | `publicRead("positions.read")`, mint max 200, update max 20/default 5, response DTO reference |
| `829258`, `e3a474234fdd438c6c6d64c063aabb960c880fb0f5562d29e8af92e4f6550a16` | Same object `[384184,391531)` | Portfolio enum normalization, pre-page spam filtering, public-only ownership rules, update-join marker |
| `984870`, `81460139322676a0f9685f4807f169ef30b84aded29a0f148b9f1bca4f6f1dda` | Same object `[470885,484647)` | Shared position DTO, precision/knowledge distinctions, portfolio-only enrichment |
| `384886` / `528766`, `9c9f618b76fb17141d8f9e484d08c037906da8c060c223efcd32bfee111f54cb` | `a73dd4b5aeff6202.js` `[5470,6802)` | Client batches/deduplicates mints, requests updatesLimit 0, treats 404 as empty |

Both object paths are under `evidence/web/objects/`. Their manifest-bound bytes
are 507,700 / SHA-256 `e78d2f38b06f971847c18dd05457c75afc85208135f50d6e4022a5f197e8839d`
and 23,591 / SHA-256 `811da914c6edb027447bdeec30e6c5d789c65a7267c97e8924799dec820aad6f`,
respectively. `positions-evidence.test.ts` independently checks lengths, complete
object hashes and the exact factory ranges without evaluating captured code.
The captured client calls factory `759257` (`e1c207697339004b48f6baa9f81f34e7644686ee424616b553e55b23c659b855`),
which constructs a contract client via `30181` and a URL provider `503630`; this
change does not guess that URL provider's runtime selection.

The portfolio factory also contains a `query` search parameter absent from the
pinned developer OpenAPI. It is not silently added to this developer endpoint.
Perps, owner dust/spam mutations and group aggregation appearing in the same
factory remain unimplemented; string presence is not scope or compatibility.

## Materialization contract (local design)

`PositionsDataset` in `src/positions-store.ts` defines the input:

- `schemaVersion: 1`, explicit data classification and UTC `observedAt`.
- Person subjects with exact `id`, explicit aliases and position fact records.
  Duplicate/ambiguous aliases and duplicate `(mint, chain, chainId)` rows fail.
  Known-empty subjects differ from unknown subjects. No usernames, linked wallet
  mappings or group membership are guessed.
- Position facts use the checked-in OpenAPI row type **without** embedded
  callout/coin/public-owner flags. Required quantities, basis, PnL and prices must
  be supplied; nullable values remain null. No financial value is calculated.
- Separate chain-keyed coin metadata, separate callouts, and a separate update
  relation. A position can reference only its subject's callout. Live author
  replies are joined, while deleted/hidden/non-author/non-parent rows are not.
- Every callout explicitly declares `updatesComplete`. Incomplete joins produce
  empty updates with `updatesApplied: false` on portfolio pages. A mint request
  requiring such a join fails explicitly; `updatesLimit=0` still works. An empty
  page/totals-only result has nothing to enrich and reports true.
- Callout, quoted-callout and separate-update timestamps must be no later than
  `observedAt`. Equality and explicitly unknown nullable timestamps remain valid.
- Public spam uses the supplied public verdict and callout exemption. Owner
  rescue/dust/liked/reposted flags are rejected, never copied into public reads.
  No verdict remains absent; it is not fabricated as a known false verdict.
- Native gas rows must use `coinMint: "native"` and `isNative: true`; they are
  portfolio-only and receive no token metadata.

Input must be finite plain JSON. Explicit local admission rejects unsupported
fields, invalid position/observation/callout/update calendar dates, unsafe or
negative social/trade counters, malformed ledger cursors, unsupported asset
classes/chains, private viewer state and dangling joins before a server starts.
Enrichment checks recurse through quoted callouts; only one quote level may be
expanded. Non-null perp/collectible payloads are rejected even when the caller
omits or mislabels assetClass. Nullable known-none fields remain null. These
social-counter/date restrictions are local input policy beyond the OpenAPI
number/string types, not a claim that upstream applies identical validation. Data is
cloned on input and output. The imported store is read-only until restart.

Run from `app`, after the normal backend build:

```sh
POSITIONS_FILE=/absolute/operator-owned/positions.json \
  node packages/backend/dist/server.js
```

The startup loader accepts a local regular UTF-8 JSON file up to 16 MiB, validates
it, and fails closed before listening. A request cannot select that path or
submit materializations. For programmatic integration, construct `PositionsStore`
with the validated dataset and pass `{ positionsStore }` to `buildApp`.

On POSIX, the read-open is nonblocking before the descriptor's file-type check,
so a named pipe with no writer is rejected rather than hanging startup. The
descriptor closes on both success and validation failure. This is local file
admission, not a general I/O deadline or production API behavior. Bounded child
tests cover readerless FIFOs; they skip Windows, whose named-pipe semantics are
not claimed. Ordinary-file validation and descriptor-cleanup controls still run.

The tests contain a clearly synthetic dataset builder, not a production default
or captured Pump activity. An actual data-producing adapter is still required.

## Explicit local policies and unknowns

- Materialization date input uses valid UTC `Z` timestamps (up to millisecond
  precision); this accepted format is a local policy, not every upstream ISO form.
- Default page 0/page size **50**; page size 1–200. The default size is a local
  choice, not established upstream behavior.
- PNL sorts supplied `pnlUsd` descending; POSITION_SIZE sorts supplied `valueUsd`
  descending; RECENCY sorts supplied `updatedAt` descending. Unknowns sort last;
  ties use a code-unit ordering of the serialized `(mint, chain, chainId)` key.
  Exact upstream tie/null policies and spot size-order implementation are unknown.
- Mint responses follow first occurrence order of exact requested strings.
  Case is preserved. A mint matching multiple chains fails explicitly rather
  than arbitrarily choosing one. Upstream ambiguity/ordering rules are unknown.
- Updates sort `createdAt` descending, null last, then exact id. Counts remain
  supplied source facts, never inferred from a truncated update page.
- Unknown identity is 404; malformed/duplicate/unknown query fields are 400
  `INVALID_QUERY`; unsupported joins/mints are 501 with an explicit local reason.
  These local error envelopes and query-coercion rules are not captured upstream
  error compatibility. The original fixture mode remains separate.
- Trust flags are retained for consumers to mask; no basis, PnL, quote, lifetime
  total, entry timestamp or exact trade count is invented. Monetary fields use
  the contract's JSON-number representation; this is not an exact-integer ledger.
- Group folds, cross-wallet financial aggregation, reorgs, backfill,
  realtime updates, prices, cache TTLs, canonical identity discovery, live marks,
  NEAR/Starknet/TON/perps/collectibles and provider availability are not implemented.
- A separate opt-in [spot trade-history read model](USER-TRADES.md) now computes
  canonical-wallet selection, trade/transfer filters and keyset pages from
  explicitly supplied facts. It does not derive this store's positions or PnL.
- Partial materialized spot-token support is not two qualified operations. The
  global native/qualified ledgers are unchanged. Other five positions.read
  operations remain untouched.

## Verification

From `app/packages/backend`:

```sh
node --import tsx --test test/positions*.test.ts
node --import tsx --test test/regular-file-admission.test.ts
node --import tsx --test test/*.test.ts
node node_modules/typescript/bin/tsc -p tsconfig.json
```

Tests cover joins and update completeness, exact unknown-value preservation,
selection/pagination/counts, public-only projections, malformed input/query
boundaries, source/input/output isolation, fixture separation, inherited API-key
gating and official response-schema conformance. They establish local behavior
and evidence integrity, **not production differential compatibility**.
