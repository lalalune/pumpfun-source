# Pump application reconstruction PRD

Date: 2026-10-28. Status: research and build foundation complete; frontend behavior and backend compatibility remain implementation work. Scope authority: the user request in this chat. This document covers the website, official JavaScript SDK and independent API-compatible backend, not the on-chain programs already being reconstructed elsewhere in this repository.

## 1. Outcome

Make a new agent productive without rediscovering the product surface, package layout, original public artifacts or compatibility boundaries. Reconstruct the frontend as closely as observable evidence permits. Preserve the official SDK source and public API. Replace the website backend with independently implemented behavior compatible with every agreed in-scope API operation and state.

“100% API compatibility” is the target, **not a result of this checkpoint**. It means an explicitly enumerated and reviewed API surface passes differential contract tests, including errors, auth, pagination, ordering and realtime behavior. It cannot mean knowledge of unobservable private internals. The developer API has 67 documented operations; that is not the full website API denominator.

### Delivered checkpoint

- Official SDK 4.3.1 archive, registry metadata, SHA-512 verification, unchanged `src/`, root and `/swap` builds in CommonJS/ESM with declarations.
- Public page and asset capture: 688 records, including 648 JS files; URL/hash/headers manifest and original bytes retained. All recorded requests in this crawl succeeded. The asset graph is exhausted within the configured scope. This does not cover authenticated states, unvisited routes, unlinked dynamic resources or future deployments.
- Babel-based recovery of 5,947 unique literal Turbopack factory variants across 7,337 captured occurrences, including the runtime's leading nested registration format, with original module IDs, hash variants and exact source ranges. Readable factories are research artifacts, not a reconstructed runnable original application.
- Next.js 16.4.1 / React 19.2.3 / Turbopack build; local navigation shell and placeholders for included routes, using captured design tokens and Geist fonts.
- Official developer OpenAPI snapshot and generated TypeScript declarations; 330 strict static operation candidates from website JS. Those include shared, excluded, privileged and possibly unreachable code.
- Backend fixture harness, service boundary convention and explicit 501 fallback. No live trading, authentication, persistence, indexer or realtime implementation.
- Reproducible install/build/test/typecheck/evidence verification commands and agent handoff.

## 2. Sources and confidence model

| Input | Authority / location | What it establishes | What it cannot establish |
|---|---|---|---|
| Official npm package | [npm](https://www.npmjs.com/package/@pump-fun/pump-sdk); `evidence/sdk/registry.json`, tar archive | Published TS, IDLs, package dependencies, exports, license declaration, gitHead | Matching private repo checkout, original lockfile/build config, runtime deployment |
| Public website | [pump.fun](https://pump.fun/); `evidence/web/manifest.json` | Exact response bytes, deployment markers, client runtime, CSS and HTML for visited routes | Full original TS/JS source tree, authenticated UI, all server actions |
| Official API docs | [docs.pump.fun](https://docs.pump.fun/), [OpenAPI](https://docs.pump.fun/openapi.public.json); `contracts/developer.openapi.json` | 67 documented operations, schemas, security and error contracts | Website-internal API completeness, implementation correctness |
| Public API samples | `evidence/api-probes.json` plus referenced objects | Observed HTTP status/body/selected headers for named requests | Exhaustive contracts, internals or stable service behavior |
| DNS and HTTP/CSP | `evidence/dns.json`, response headers in manifests | Exposed edge/CDN records and declared policies | Origin compute, private networking, every active third-party integration |
| AST extraction | `recovered/modules.json`, `contracts/internal-operations.json` | Literal factory boundaries and API-operation strings | Execution, reachability, service binding, type correctness or behavior equivalence |
| REA analysis | `evidence/rea/frontend-analysis.json` | Selected-source static semantic analysis and explicit gaps | Whole-app analysis; REA did not recover Turbopack modules here |

Use four labels: **observed** (bytes/traffic), **declared** (first-party documentation or package metadata), **inferred** (supported but not directly demonstrated), **unknown**. Implementation choices have a fifth label: **local design**, never upstream fact.

Initial ordinary HTTP and isolated browser access met a Cloudflare challenge. Subsequent public acquisition using the recorded `Googlebot` user agent returned the application. The captured output may differ from an ordinary authenticated browser response. No login, CAPTCHA bypass, production mutation or credential acquisition was performed. Preserve this limitation when using the snapshots.

No captured JS declared `sourceMappingURL`. Three explicit source map probes returned 404 (`evidence/source-map-probes.json`); this is not a proof that every map is absent. REA's source recovery provider requires a separate Linux Wakaru binary unavailable on this Mac; local Babel extraction instead recovers inert factory functions. Original frontend file paths and TypeScript types remain unknown.

## 3. Scope

### Included

- Shared responsive layout, navigation, search, onboarding/sign-in states, wallet integration boundaries and settings.
- Home/feed: for-you/following, posts/callouts, discovery, pagination, media and reactions where observable.
- Explore: search, filters, sorting, rankings and result navigation up to the excluded detail boundary.
- Leaderboard: trader PnL, groups, competitions and creator payouts.
- Live: discovery, playback, presence and stream metadata; define creator/broadcast scope after observing authorized flows.
- GO, Mayhem, holder rewards, profile/social graph and relevant portfolio surfaces.
- Create-coin flow, SDK integration and metadata/upload contracts. Offline/localnet signing tests first.
- First-party legal/fee reference pages and shared error/loading/empty states as required by included flows.
- Backend contracts needed for all included surfaces, SDK capabilities, fixture capture, offline compatibility testing and implementation plans.

### Excluded from implementation, retained in inventories

| Surface | Boundary and retained work |
|---|---|
| Support / Intercom | No support product rebuild. Keep provider contract and navigation boundary. |
| Terminal / Padre | No `trade.padre.gg` application rebuild. Preserve external URL and integration evidence. |
| App / mobile | No native app, app store flow, mobile-specific codebase or `app.pump.fun` rebuild. Responsive website is included. Retain promotion/provider evidence. |
| Token pages | No `/coin/[mint]`, token-detail/trading screen or `$PUMP` `/pump-token` rebuild. Their shared API/SDK contracts may still support discovery or rewards. |

Perps/Hyperliquid and separate PumpSwap/revenue/GO microsites are **deferred integration boundaries**, not implicitly added standalone applications. A local `/perps` placeholder records the boundary. Do not spend implementation effort on deferred surfaces without reviewing scope.

## 4. Workspace and build architecture

```text
app/
  packages/sdk/        official published source; reconstructed tsup build
  packages/frontend/   Next App Router + Turbopack
  packages/backend/    independent API compatibility service
  contracts/           OpenAPI, static API leads, routes, fixtures, coverage
  evidence/            raw immutable observations + provenance
  recovered/           inert readable factory variants and extraction manifest
  scripts/             public capture, AST extraction, formatting, integrity checks
  tests/               published SDK differential checks and recovery provenance
  infra/               optional local containers; not upstream infrastructure
```

Package manager: local pin pnpm 10.24.0. SDK publication metadata says pnpm 11.5.0; its historical lockfile was not available. Node >=22 for this workspace; the SDK publisher reports Node 24.22.1, while the verified local host uses 24.15.0. `pnpm-lock.yaml` pins our actual dependency resolution, not upstream transitive resolutions. `patches/@pump-fun__agent-payments-sdk@1.0.7.patch` changes one statement of that dependency's ESM entry, the named `BN` import from `@coral-xyz/anchor`, to a namespace import with a CommonJS-default fallback. Node releases before 24.14.0 (including 22.x) cannot detect that named CommonJS export, while Anchor's browser ESM has named exports but no default. The fallback preserves both resolution paths without editing SDK source.

SDK: tsup 8.5.0 and TypeScript 5.9.3 are local build choices within published major ranges. Original tsup/tsconfig files are not in the tarball. The declared repository/commit returned 404 during this research. Do not substitute a similarly named third-party SDK. Root and `/swap` stay separate because their exported names overlap. Local ESM output uses `.mjs`; the official package's original exports metadata is preserved in `evidence/sdk/registry.json`. Source fidelity is verified independently from build-output identity.

Frontend: Next 16.4.1 is directly embedded in compiled paths/runtime strings. React 19.2.3 and `@types/react` 19.2.7 appear in a captured pnpm path. Next's bundled React runtime also reports a canary version; this is distinct from the application dependency. The local build pins observed app versions and runs `next build --turbopack` and `next dev --turbopack`. React DOM 19.2.3 is a compatibility-aligned local choice, not independently version-proven in the bundle. Recovered colors and font assets are used locally; layout and interactions remain placeholders.

Backend: Fastify 5.6.2, TS and tsx are **local implementation choices**. Nothing here proves that upstream uses Fastify. The initial harness reads the OpenAPI document, recognizes developer routes under `/v1`, and serves only explicitly loaded read-only fixtures. Unknown routes return 501. Native mode, persistence and auth remain future work. Never use the fallback as the expected upstream response in parity tests.

## 5. Dependency inventory

### SDK: declared upstream runtime dependencies

| Package | Published range/version | Role |
|---|---|---|
| `@coral-xyz/anchor` | `^0.31.1` | IDL/program clients and serialization |
| `@solana/web3.js` | `^1.98.2` | Solana keys, RPC and transactions |
| `@solana/spl-token` | `^0.4.13` | SPL/Token-2022 operations |
| `@pump-fun/agent-payments-sdk` | `1.0.7` | Agent-payment integration |
| `bn.js` | `^5.2.2` | Integer arithmetic |
| `undici-types` | `^6.20.0` | Fetch/network declarations |

Original dev dependencies and scripts are preserved in the registry snapshot. Install resolves compatible versions in our lockfile; it does not recreate the publisher's entire environment. Native `bigint-buffer`, `bufferutil` and `utf-8-validate` build scripts were not enabled; tests exercised the JS fallback. One optional ws native peer mismatch is recorded in validation. This is not a performance qualification.

### Frontend: evidence-backed findings

| Library / system | Confidence | Evidence / version |
|---|---|---|
| Next / Turbopack | Observed | 16.4.1 embedded pnpm paths, runtime, `turbopack-*` assets |
| React / compiler-generated memoization | Observed | React 19.2.3 in pnpm path; compiler memo-cache patterns. Compiler plugin version unknown. |
| Geist | Observed | Captured `@font-face`, five WOFF2 files |
| Tailwind-style utility CSS | Inferred | Captured `--tw-*` utilities; exact package and version not established |
| Zod | Observed code fingerprint | `ZodError`, validators and issue structures; version unknown |
| Zustand | Observed code fingerprint | Persist-middleware diagnostic; version unknown |
| Valtio | Observed path | 1.13.2 in pnpm path |
| Privy React auth | Observed | `@privy-io/react-auth/tempo`, `PrivyProvider`, auth flows; version unknown |
| Socket.IO client | Observed code fingerprint | Protocol handlers, upgrade warning; exact version unknown |
| LiveKit | Observed/configured | LiveKit log bridge and production `wss://…livekit.cloud`; version unknown |
| Firebase | Observed | SDK registration string **11.10.0**; app/messaging code. Service use requires runtime confirmation. |
| Datadog RUM | Observed | `datadogRum` error instrumentation; version unknown |
| LaunchDarkly | Observed | Lazy-loaded runtime/context provider; version unknown |
| Mux player/data | Observed/configured | Mux player loader, data environment setting; version unknown |
| MapLibre GL | Observed | Map code and CSS; version unknown |
| Viem | Observed | Viem error/version formatter; exact version unresolved |
| WalletConnect / wallet adapters | Observed/configured | Connection, verification and provider code; exact versions unresolved |
| Radix / Base UI / TanStack / other packages | Leads only | Some related domains/patterns occur, but exact attribution needs tracing. Do not automatically add a guessed package. |

`evidence/web/dependency-paths.json` and `library-fingerprints.json` link findings to offsets. SDK dependencies are not evidence that the website imports this exact published SDK version. Generic third-party bundles include unused chain/RPC defaults; the host list is **not** a list of active providers.

### Backend dependency knowledge

Observed JSON and health responses show independent named services. A livestream health check reports a connected database without naming the engine. Frontend API health exposes event-loop metrics, consistent with a JS runtime but not definitive evidence of Node/Nest/Express. Nest-style `statusCode`/`message` responses are insufficient to identify a framework. PostgreSQL, Redis, queues, Kubernetes, ECS, Lambda, database schema, service language and deployment topology are **unknown**.

## 6. Infrastructure and third-party boundaries

| System | Evidence and finding | Classification / limit |
|---|---|---|
| Cloudflare | DNS edge addresses; `server: cloudflare`, `cf-ray`, challenge response and cache headers | Observed public edge/protection. Origin remains hidden. |
| Vercel | Main-page `x-vercel-id` / cache headers and `data-dpl-id`; API docs `server: Vercel` | Observed frontend/docs delivery. Does not prove every API runs on Vercel. |
| AWS CloudFront | `images.pump.fun` and `socialimages.pump.fun` CNAMEs resolve to CloudFront distributions | Observed image CDN. No inference of backend EC2/ECS/RDS from this. |
| Amazon S3 | First-party CSP names media/bounty S3 URLs | Declared allowed storage endpoints; bucket existence/region is not full storage architecture. |
| AWS WAF | Captcha SDK hostname in JS and CSP | Client integration evidence; not proof of all origin hosting on AWS. |
| `frontend-api-v3.pump.fun` | Static base URL; live public health, coin-list and price responses | First-party API surface. Backend source unknown. |
| `profile-api.pump.fun` | Static base URL and live `ProfileService` health | First-party service, persistence technology unknown. |
| `livestream-api.pump.fun` | Static base URL and public health | First-party orchestration API; separate LiveKit streaming dependency. |
| `advanced-api-v2`, `advanced-indexer`, `blockchain-swap`, `fun-block`, `swap-api`, `intents` | Literal client configuration/URL references | First-party hostnames; endpoint roles are partly inferred from names/call sites. `/v1/health` on swap returned `OK`. |
| LiveKit, Mux, Cloudflare Stream | Production config strings, player code and CSP | Third-party media/voice/playback. Trace each feature before choosing a replacement. |
| Privy | Client imports and [first-party privacy notice](https://pump.fun/docs/privacy-policy) | Third-party wallet/auth; do not copy app identifiers or assume access to upstream tenant. |
| LaunchDarkly | Runtime/provider factory and CSP | Third-party feature flags; flags and targeting affect reproducible behavior. |
| Datadog, Mixpanel, Google Analytics, AppsFlyer | RUM code, first-party privacy notice and/or CSP | Third-party monitoring/analytics/attribution. CSP permission alone is not proof of an active event stream. |
| Intercom | HMAC API candidate, CSP and client code | Third-party support, excluded product surface. |
| IPFS / Pinata / Filebase | Media URLs, upload API candidates, client imports | Third-party content storage/gateways; uploaded content lifecycle still needs contracts. |
| Helius / Jito / Nozomi / QuickNode | RPC/bundle host configuration or CSP | Blockchain-provider leads; actual default/region/failover not fully observed. |
| Relay / Hyperliquid / MoonPay / Helio | Client references/CSP and first-party privacy notice | Third-party bridge, perps and payment/onramp boundaries. Disabled locally. |

The privacy notice explicitly describes Privy, AppsFlyer, Relay and Hyperliquid roles. Its general language does not name the database, queue, server framework or full provider inventory. Shared first-party hostnames do not imply shared implementation. No DNS origin enumeration or privileged endpoint probing was performed.

## 7. API compatibility plan

### Separate surfaces

1. Website APIs: multiple origins, cookies/Privy/wallet auth, HTTP and realtime. Source-string candidates are leads; bind each to an origin and feature.
2. Developer API: `https://api.pump.fun/v1`, OpenAPI version 0.294.0, 67 operations across six scopes. Server-only key policy, documented rate limits and CORS behavior must be modeled. No key was requested or reused. An unauthenticated sample returned 401 `API_KEY_REQUIRED`.
3. Chain/RPC: SDK instructions and data reads. Do not conflate Solana JSON-RPC with Pump's application API.
4. Third-party service APIs: adapters/contracts; do not claim to reproduce a vendor's entire platform.

Local convention reserves `/services/frontend/*`, `/services/profile/*`, `/services/livestream/*`, `/services/swap/*` etc. to avoid collisions between upstream origins. `/v1/*` models the public developer API. Production-shaped origins can be added through a local gateway later. The initial harness has no automatic upstream proxy.

### Capture matrix per operation

Record method, origin, path template, query order/duplicates/defaults, headers, body encoding, auth state, feature flags, status, content type, response schema, pagination, cursor behavior, sort/tie-breaking, precision, timestamps, cache/rate-limit headers and failures. For mutations also record idempotency, conflicts, ownership and persistence. For Socket.IO/WebSockets record namespace/path, handshake, protocol version, auth, event name/payload, subscribe/unsubscribe, replay/reconnect, heartbeats, errors and delivery ordering.

Schemas are generated from the public specification. Internal Zod schemas and factory call sites must be traced and converted without claiming the regex inventory is a schema. The first replay fixture is a dated public SOL-price response; it has **zero live-price guarantees**. Backend native domain behavior has **zero qualified operations** at this checkpoint.

### Test oracle

- Use sanitized, provenance-linked golden requests/responses for deterministic fixture regression.
- Differential checks compare native local behavior with authorized upstream observations or official contract expectations. Normalize only named volatile fields, never discard precision, errors, ordering or identity differences to force a pass.
- Cover anonymous, authenticated, expired/revoked/wrong-scope auth, empty/full data, bad params, limits, missing/deleted IDs, partial failures, timeouts and retries.
- Exercise writes on owned test accounts or localnet/fixtures; production mutation is not a discovery technique.
- Keep unauthenticated and privileged routes separate. `/internal/*`, admin/moderation and developer-key management strings remain inventory-only until explicitly authorized and in scope.
- Require explicit scope denominator and zero unexplained differences before using “100% compatible.” Stub/proxy/fixture coverage must be reported separately.

## 8. Frontend reconstruction plan

Use the captured HTML to map route segments, loading boundaries and RSC references. Use `recovered/modules.json` to trace module imports and reconstruct components, hooks, schemas, styles and service clients. A numeric module ID may have multiple hash variants; choose the variant referenced by the page's actual chunk set. Missing source names become descriptive analyst names with provenance, not invented original filenames.

Rebuild the responsive shell, feed/explore/leaderboard and shared cards first. Then auth/profile/social graph, realtime/live, create/rewards and remaining included flows. Preserve query string/deep link/history semantics, pagination, input validation, flags, keyboard navigation, focus management and loading/error/empty states. Token-detail navigation ends at an explicit excluded boundary.

Visual acceptance requires matched viewport/state screenshots of desktop and mobile reference and local app. Record fonts, colors, spacing, dimensions, breakpoints, modal positions, scroll behavior and dynamic data. A successful Next build or similar dark theme is not visual equivalence. Current placeholders deliberately display their implementation status.

## 9. Backend implementation architecture (local design)

Keep transport contracts separate from domain behavior. Proposed units: identity/auth adapter, profile/social graph, feed/callouts, market/discovery read model, leaderboards/competitions, livestream orchestration, media/upload, rewards, and Solana indexer/RPC adapters. Use ports for third-party providers and clock/randomness. Choose database/queue/cache only after deriving access patterns and consistency requirements; do not assume upstream PostgreSQL or Redis.

Indexing will need slot ordering, commitment/reorg handling, replay/idempotency, historical backfill, lag reporting, precision and schema migration. Offline captured data plus localnet is the initial environment. User keys stay client-side or inside an explicitly designed custody boundary. Client API keys from upstream deployments are not configuration for this clone.

The SDK covers bonding curves, fee schedules, quote mints, Token-2022, AMM, rewards and PDAs. Reusing its unchanged source avoids inventing these routines. Validation against published JavaScript does not prove reconstructed on-chain byte identity or chain acceptance.

## 10. Sequenced implementation backlog

| Priority | Workstream | Concrete output / acceptance |
|---|---|---|
| P0 | Evidence discipline | Immutable snapshots, deployment identities, all hashes verified, authenticated capture procedure |
| P0 | Scope/API denominator | Review 330 candidates and 67 documented ops; origin/feature/auth/scope binding; remove prose/unreachable duplicates from denominator |
| P0 | SDK | Already builds; expand differential cases to instructions, PDA derivation, errors and boundary values; preserve source bytes |
| P1 | Frontend core | Reconstruct shell/feed/explore/leaderboard components and routes from factories; screenshot parity |
| P1 | Public reads | Native service handlers for captured discovery/profile/feed contracts, pagination and errors |
| P1 | Identity | Own Privy/dev-auth adapter, session semantics, wallet sign-in, account linking and permissions |
| P2 | Social writes | Posts/callouts/replies/reactions/follow/blocks/bookmarks, upload lifecycle, idempotency and consistency |
| P2 | Realtime/live | Socket.IO and LiveKit contracts, presence/reconnect/replay, player state/errors |
| P2 | Create/rewards | Localnet transaction composition and confirmation, metadata storage, claim/fee state |
| P2 | Indexer/read models | Backfill, reorgs, precision, cache consistency, failure/restart behavior |
| P3 | Operational parity | Rate limits, CORS, cache, tracing, abuse controls, staged deployment and rollback |
| Deferred | Excluded/unclear surfaces | Support, terminal, native app, token detail/$PUMP; perps and external microsites require scope decision |

Every workstream updates `contracts/coverage.json` with captured / fixture / implemented / qualified status and evidence. An agent should start with one route family, not a generic rewrite of all 330 candidates.

## 11. Checkpoint acceptance and remaining gates

Foundation acceptance: frozen install, SDK/frontend/backend build, typecheck, published-export comparison, sampled fee-math differential checks, read-only fixture routing tests, recovered-factory provenance and artifact hashes. Actual commands/results are in `evidence/validation.json`.

Not yet accepted: original frontend source identity, pixel/interaction parity, full internal API schemas, authenticated flows, native backend domain behavior, persistent storage, websocket behavior, chain execution or any production deployment. Docker files are untested local templates unless validation says otherwise.

Open questions: which authenticated roles and browser states define final scope; origin binding of every operation; actual backend framework/storage/queues; original frontend dependency versions beyond direct evidence; original source maps and build config; active provider tenant configuration; feature-flag targeting; acceptable deterministic normalization; ownership of test accounts/data; production SLOs and release criteria.
