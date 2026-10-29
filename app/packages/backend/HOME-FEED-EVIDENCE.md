# Native local Home Feed evidence and boundaries

This unit adds a deterministic, read-only local model for the three captured
website operations below. It does not claim to reconstruct Pump's production
ranking, storage, authentication, live updates, prices, or users. The local
routes are deliberately namespaced under `/services/frontend`; the separately
documented developer API stays under `/v1` and keeps its API-key gate and
unimplemented response.

| Captured website operation | Local reconstruction route |
| --- | --- |
| `GET /home-feed` | `GET /services/frontend/home-feed` |
| `GET /home-feed/new` | `GET /services/frontend/home-feed/new` |
| `GET /home-feed/new/count` | `GET /services/frontend/home-feed/new/count` |

Every successful local response carries
`X-Reconstruction-Data-Source: synthetic-home-feed-local-v1` and
`X-Reconstruction-Compatibility: local-unqualified`. No production request is
made.

## Immutable source evidence

The following captured objects were checked directly against
`evidence/web/manifest.json`:

| Object | Bytes | SHA-256 | Role |
| --- | ---: | --- | --- |
| `evidence/web/objects/2b47dd0b38a1608f.js` | 507,700 | `e78d2f38b06f971847c18dd05457c75afc85208135f50d6e4022a5f197e8839d` | Route declarations and DTO schemas |
| `evidence/web/objects/3740fc4e7a24596d.js` | 67,649 | `7400496d0194dea1be93f3640e73b3131f7e18d3e3d14fffb1ed117578795295` | Website client variant |
| `evidence/web/objects/cf2bb278631744da.js` | 20,907 | `ddddd084a6579d81c0a5675fdea7d0eabcd2515645f093bb3650baa4f8b558e3` | Website client variant |

The route declaration fragments use UTF-16 code-unit ranges
`238484:242300`, `242322:245402`, and `245430:246787`. Their route literals
begin at the investigation offsets 238467, 242301, and 245403 respectively.
Both client variants contain module 735821. The recovered variants and their
authenticated complete-factory hashes are:

- `recovered/modules/735821-bd59c4bee570.js`, factory SHA-256
  `bd59c4bee5702bebd7d5a2b91640d9ed9c3170493c0809861e33f4c926744f3d`,
  source range `3740fc4e7a24596d.js:1201:8886`.
- `recovered/modules/735821-3adabf21c26e.js`, factory SHA-256
  `3adabf21c26e22024c9c08c3e218b88d0c052d972cf3c25779c1c8efc3350ba2`,
  source range `cf2bb278631744da.js:1201:8886`.

Their individual function ranges are `7031:7631` for `/home-feed`,
`7631:7994` for `/home-feed/new`, and `7994:8325` for the count operation.
The same ranges occur in both variants.

Open PR #686 independently closes the original website request chain and is
credited for that transport attribution. At reviewed head
`0f7b1148a702442aa66214a277f8d18b8209657e`, it proves the chain
`735821 -> 759257.j -> 30181.K -> 402030.createContractClient -> 898661` and
the `503630.R` origin `https://frontend-api-v3.pump.fun`. It also establishes
`credentials: "include"`, JSON content type, abort-signal forwarding, and the
transport's `x-pump-source: WEB` and `x-pump-platform: web` headers. That PR
adds contract evidence only: it installs no backend route and provides no
captured response body. This implementation does not copy its files or claim
its evidence extraction as new work.

No retained response fixture for these operations appears in
`contracts/public-fixtures.json`, `evidence/api-probes.json`,
`evidence/source-map-probes.json`, or the capture manifest. Consequently this
unit uses no captured market record as if it were current or complete.

## Finding classification

### Observed

- The three methods and paths above are requested by the website client.
- `/home-feed` sends a page-size default of 150, a default `all` chain, WEB
  platform data, optional facepile/viewer data, and `credentials: "include"`.
- `/home-feed/new` is a separate chronological feed and forwards page size,
  chain/bounds, and an optional page token.
- `/home-feed/new/count` sends a pinned `since` token plus chain/bounds.
- The selected request origin is `https://frontend-api-v3.pump.fun`.
- The response declarations include `coins`/`nextPageToken`; New also has
  `headToken`, `liveSubject`, and optional `liveSubjects`; count has
  `newCount`, `capped`, and `headToken`.
- The contract description uses a creation-time/callout-id keyset concept and
  describes a 24-hour New-feed window and 25-row head memos.

### Declared, not behaviorally qualified

- Home page size is 1..200 and page is a non-negative safe integer.
- New page size is 1..50; `updatesLimit` is 1..10.
- Home `pageToken` has a 256-code-point declaration limit.
- Chain, asset-class, market-cap, callout-market-cap, and cost-basis fields are
  declared filters.
- The first two declarations are public `content.read` contracts; the count
  declaration is not wrapped by that same keyed-host declaration.
- Production descriptions discuss pre/post-ranking filtering, refill behavior,
  degraded fallbacks, live NATS subjects, and worker-written memos. Those
  descriptions are retained as evidence, not implemented services.

### Local design

- The only data is the checked-in `synthetic-home-feed-v1` seed. It is explicit
  example data, never historical Pump activity. Its canonical JSON SHA-256 is
  `3482fa9ed2f690d6002a4e9fe7932c6d7ce2d0258c9094cb9e438cfae0a5644e`.
- Startup rejects a changed default seed, malformed records, duplicate record
  or callout identities, unsupported chains/classes, invalid timestamps,
  unsafe strings, invalid numeric values, and future-dated rows.
- Required strings must contain a non-whitespace character, matching the
  maintained native-feed response consumer. Previously a supplied local store
  could admit blank coin/author labels, identifiers or thesis text and return
  HTTP 200, only for that consumer to reject the whole page. Admission now
  rejects those records before serving; valid strings retain their exact
  whitespace and Unicode rather than being trimmed or repaired. This is local
  constructor/consumer consistency, not an inferred production text rule. The
  unchanged hash-bound default seed already satisfies this requirement.
- Ranked order is the seed's explicit `localRank`, then creation time
  descending, then callout ID. It is deterministic and is not Pump ranking.
- New order is creation time descending, then callout ID. The 24-hour cutoff is
  anchored to the seed's fixed `observedAt`, not the process clock.
- Continuation and head tokens are versioned canonical-JSON base64url
  envelopes bound to operation, dataset, and normalized filter context, with a
  128-bit SHA-256-derived integrity checksum. This is a local opaque token
  format, not an asserted production cursor encoding.
- New-count counts eligible rows newer than the caller's pinned head. It never
  changes that `since` input. The explicit local memo depth is 25; a single/all
  chain caps globally, while a multi-chain query caps each selected chain and
  reports `capped` when any selected memo overflows.
- Errors use the existing local backend envelope. Unknown, repeated,
  malformed, contradictory, oversized, foreign, and tampered inputs fail
  closed. These status/error choices are local behavior where the captured
  server outcome is unknown.
- `liveSubject` is the literal
  `local.reconstruction.realtime-unavailable`; no subscription endpoint or
  realtime service exists.

### Unknown or unsupported

- Production ranking, candidate hydration, cache behavior, fallback behavior,
  databases, and response records.
- Server-side cookie authentication, viewer authorization, wallet ownership,
  personalization, followed-holder facepiles, private data, and regional or
  account error precedence.
- Production cursor bytes, missing/unrecognized-token restart behavior, and
  exact head-memo implementation.
- NATS subjects, live head delivery, recommendation IDs/scores, current
  markets/prices, media, and mutable actions.

Unsupported personalized parameters return a local 501 response rather than
pretending that `userId`, telemetry, `platform=APP`, or
`includeFollowedHolders=true` authenticates a viewer. Hidden and deleted local
records are never projected. Projected records contain no external media URL,
wallet address, cookie, credential, private profile field, or recommendation
claim.

## Verification

Focused tests exercise the real Fastify app with injection and loopback HTTP.
They cover all routes and automatic HEAD handling, schema projection,
deterministic ranking, keyset continuity, equal timestamps, 24-hour filtering,
pinned count behavior, memo caps, query boundaries, seed validation,
immutability, cursor tampering/context swaps, fixture-route shadowing, separate
`/v1` behavior, existing posts, and the generic 501 fallback. A network guard
also proves these local reads invoke no external fetch.

Run from `app/`:

```sh
corepack pnpm@10.24.0 --filter @pump-reconstruction/backend exec tsx --test test/home-feed.test.ts
corepack pnpm@10.24.0 --filter @pump-reconstruction/backend exec node --import tsx --test test/home-feed-string-admission.test.ts
corepack pnpm@10.24.0 --filter @pump-reconstruction/backend test
corepack pnpm@10.24.0 build
corepack pnpm@10.24.0 test
corepack pnpm@10.24.0 typecheck
corepack pnpm@10.24.0 verify:evidence
corepack pnpm@10.24.0 check:progress
node scripts/smoke.mjs
```

The developer operation denominator, native developer-operation count, route
qualification, and frontend progress scores remain unchanged. A local tested
read model is not original production compatibility.
