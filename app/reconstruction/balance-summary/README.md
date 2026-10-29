# Original profile-service balance summary read workflow

This reconstructs the complete captured **349572/524711** HTTP reader and query
policy, bound to the actual **465363** account-UI caller and **38279** endpoint
and cache-key provider. The maintained original portfolio-summary reader520669
uses a different service/response path; it is unchanged. Public mainnet SOL/SPL
inventory reads, wallet sessions, positions, valuation and PnL remain separate.

## Physical source and caller

`contract.json` is generated from immutable captured bytes through the shared
`scripts/original-contracts/source.mjs` registration/authentication reader. It
records original URLs, capture/factory hashes and exact UTF16/UTF8 half-open
ranges. No captured JavaScript or original runtime is executed.

All six indexed physical reader variants are retained explicitly. Their local
binding names differ; the verifier checks their actual exported reader/query
functions, origin-provider import, complete errors/retry paths and query hooks.
It pins each full factory hash rather than choosing an arbitrary global ID
winner. A changed or resealed factory requires review. The actual UI and one
reader variant share `a8933cf5deeab5bd.js`:

- UI465363: UTF16[7374,29539), SHA256 `0457d6da501f92a1a4e47d297a28feb6fae5512889e4eff04a9087ef1d956556`.
- Reader524711/349572: [37496,39289), SHA256 `5bbfa5818419ab77ec3f23176573ccdbbc3b3effe7354231d2bc2712611aa86d`.
- Provider38279: `ad7136d0b3a7f323.js`, [260,12654), SHA256 `8d71db5a2d47da722166199f0a64e93e0295051da46086355f136b93a3f3b89a`.

The UI passes only `{userAddress: subject}` to524711.\_. It destructures that
query's data/loading/error/refetch state, then uses the **truthiness** of the raw
response's `success` property to select `response.data` or undefined. That
source witness binds the actual response handoff; this module does not rebuild
the larger UI, number animation, balance fallback/display, provider/session or
error-toast lifecycle. In contrast the polling callback tests `success===true`.

## Request, response and error behavior

Provider38279 supplies `https://profile-api.pump.fun/balance/summary` and
`['balanceSummary', subject]`. The latter is a **query/cache key, not a credential**.
The adapter requires an explicit destination and fetch implementation: import
performs no request and supplies no production transport by default.

`read({userAddress,multiChain,fetchOptions})` interpolates the subject into the
URL before parsing. It does **not** encode or validate a path segment. Truthy
multiChain adds `multi_chain=true`; the query builder always requests it.
`fetchOptions` is forwarded unchanged, so fetch defaults apply when absent.
The actual UI caller supplies none. No Authorization header, cookie, credentials
override, timeout or ownership policy is added. Explicit caller options can
override native fetch defaults; this is not a GET-only security wrapper.

On an ok response, `.json()` is returned raw without a schema, shape repair or
`success:true` requirement. Malformed/empty JSON and transport errors propagate.
The reader does not validate amounts, infer holdings/PnL or calculate account
balances. On401 it throws `BalanceSummaryHttpError('Unauthorized',401)` without
reading the response body or retry header. Other non-ok statuses throw the
source message/status; only429 reads `Retry-After` and the clock. Error bodies
are not decoded or consumed by the reader.

Retry-After accepts the source's signed integer-seconds spelling or native
`Date.parse` date path. Negative seconds are absent; negative zero survives.
Past dates clamp to zero. A huge digit string can yield infinity: the parser
does not repair it, while the later finite-property guard treats an infinite
error delay as unavailable. An explicit `nowMs` port makes date cases repeatable.
Native date parsing outside these fixed cases is not cross-engine qualified.

## Query and cache policy

`queryOptions` closes over the original subject/options and returns the key,
queryFn and exact retry policies. It does not run a scheduler or retry itself:

- Retry only while failureCount<2 and finite numeric status is not401.
- For non429, delay is `min(1000*2**count,30000)`.
- For429, a finite retryAfterMs is capped at60000; otherwise delay is
  `5000*(count+1)`. That fallback has no added cap.
- Poll60000ms only when query state is `success` and data.success is strictly
  true; all other states poll15000ms.

`useBalanceSummary` reconstructs the complete seven-slot compiler-memo policy
through explicit `memo` and `useQuery` ports. Default enabled is `!!subject`;
staleTime is infinity; mount/focus/reconnect refetch are true. User query options
spread **last**, including overrides of enabled, queryFn and polling. Memo ports
must provide a correctly initialized, separate cache for each hook instance.
No React/query library or scheduler is guessed or installed.

The queryFn takes no query-context argument and does not forward its AbortSignal.
A signal inside the explicit fetchOptions does propagate to fetch. Old callbacks
retain their original subject/options after later hook calls. Tests prove those
finite call/identity boundaries, not original React lifecycle, concurrent cache
ownership, retry scheduling or browser session behavior.

```js
import { createBalanceSummaryClient } from "../../packages/frontend/src/original-contracts/balance-summary/client.mjs";

const reader = createBalanceSummaryClient({
  baseUrl: explicitIsolatedBaseUrl, // e.g. the local synthetic test provider
  fetchImplementation: fetch,
});
const served = await reader
  .queryOptions({ userAddress: explicitSubject })
  .queryFn();
```

## Reproduce and limits

From the repository root, using existing pinned dependencies:

```sh
node app/scripts/original-balance-summary.mjs --check
node --test app/tests/original_source.test.mjs app/tests/original_balance_summary.test.mjs
# Explicit deterministic regeneration; --check rejects any byte difference:
node app/scripts/original-balance-summary.mjs --write
# Optional fresh local synthetic wire receipt (does not touch sealed receipts):
PUMP_BALANCE_SUMMARY_WIRE_OUTPUT=/tmp/balance-summary-wire.json \
  node --test app/tests/original_balance_summary.test.mjs
```

The new checks cover source/caller binding, explicit destination/options, raw
subject and JSON behavior, ignored query signal versus actual fetch cancellation,
all error/retry/polling branches, memo identity/captured callbacks/last-spread
overrides, raw corruption, resealed401-source mutation and noncanonical contract
bytes. Real loopback HTTP uses exclusively synthetic public subjects/payloads:
seven complete responses plus one aborted GET, without automatic retries.
Only the ephemeral loopback origin is omitted from its wire receipt.

Immutable main094a lacks these maintained module/verifier paths. This is new
source reconstruction; no original/live server or fabricated baseline HTTP
response is used as a before proof. Qualification records bind actual source and
commands under [`validation/`](validation/VALIDATION.json): 20 focused checks
(nine new and eleven shared), seven complete loopback responses plus one aborted
GET, source verification, 698-object/npm/SDK evidence checks, progress and its nine
tests, and the required nine root captures/ten tooling tests passed. The root
commands' 46 actual read inputs match the source revision's Git blobs; no
original program/source rebuild is claimed. No production traffic, original backend
accounting/schema, authenticated access, owner/session enforcement, provider
winner/current availability, RPC, transaction/signing, native compatibility,
React UI integration, visual parity or feature percentage is claimed. Existing
contracts, captures, SDK and product implementation remain unchanged.
