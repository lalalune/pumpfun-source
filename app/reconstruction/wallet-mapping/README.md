# Complete captured wallet-mapping read owner

This restores the complete functional read/cache/query boundary of factory
**795663**: single SOL-address→canonical-EVM-wallet lookup, deduplicated parallel
batch mapping, positive/negative cache reuse and its query hook. The existing
`user-batch` README explicitly excluded this actual caller's mapping behavior.
This package adds that missing owner, with no new product UI, identity inference,
server implementation or feature-milestone credit.

`contract.json` authenticates original factory
`11dbd34fa7c445a0bad7970b695619d27c2c16a9242ad1e6c37d2e1269e912cc`,
its four exports and actual imports, full original syntax, all known origins,
UTF-16/UTF-8 ranges, the actual 689943 caller import, maintained source bytes and
credited dependency bindings. The original capture is the complete object
`evidence/web/objects/020facfab961bf67.js`, not copied snippets. No captured code
is executed and no active global runtime provider is inferred.

The strict batch reader (544930) and profile reader/error classes (528600) are
reused from existing packages unchanged; their recovery gets no new credit.
Their UTF-8 text hashes and the JSON inventory's source binding normalize
checkout CRLF to LF. Original capture hashes remain exact raw-byte hashes.
The new maintained adapter and generated receipt are checked out as LF.

## Explicit integration

```js
import {walletMappingClient} from './client.mjs';
const mapping = walletMappingClient({
  request: hostWebsiteContractClient,
  createClient: hostProfileHttpConstructor,
  getOrigin: hostExplicitOrigin,
  now: Date.now,
});
await mapping.cached({solAddresses: suppliedAddresses, queryClient: hostQueryClient, signal});
const result = mapping.useWalletMapping(hostUseQuery, {solAddress, enabled, fresh});
```

No host destination is supplied by default. The original declared website origin
is not permission to make a production request. Import and construction initiate
no I/O; only an explicit invocation reaches the supplied capability.

## Preserved owner behavior

- Single lookup delegates to the credited typed reader. Missing/undefined
  canonical wallet is null; only its typed `not_found` result becomes null.
  Other HTTP, parse and cancellation failures propagate without replacement.
- Batch input is deduplicated before splitting into concurrent 100-key reads.
  Empty input sends zero requests (unlike the raw batch dependency). Every
  requested address starts as null. Returned matching rows replace it, later
  duplicates win, and omitted rows remain null. Source response assumptions are
  preserved rather than strengthened into an invented DTO parser.
- Cache sampling uses one clock read. Any string, including the empty string,
  is reused regardless of age; null is reused only when its age is strictly less
  than 300000ms. Other/missing/stale states are batched. No cache writes occur
  until all batches resolve. Queried missing rows are cached as null. This is
  the captured policy, not a new freshness recommendation.
- Query key is `['walletMapping','solToEvm',address??null]`. It is enabled only
  for a truthy address and non-disabled host option. Normal stale time is five
  minutes; `fresh` changes it to zero and adds `refetchOnWindowFocus:false`.
  The query-runtime signal reaches the single lookup. The injected `useQuery`
  result is returned unchanged; this package invents no extra loading/error
  state or observer scheduler.

## Repeatable checks

```sh
node app/scripts/original-wallet-mapping.mjs --check
node --test app/tests/original_wallet_mapping.test.mjs app/tests/original_user_batch.test.mjs app/tests/original_profile_lookup.test.mjs
python app/scripts/verify-evidence.py
python scripts/verify_evidence.py
python -X utf8 scripts/test_tooling.py
```

Seven new tests plus 30 credited-dependency checks pass. A real loopback HTTP
server supplies clearly authored synthetic rows for single reads, 205 unique
addresses/three batch requests, missing rows, typed 404/503, cache expiration and
abort. These are interaction checks of the maintained adapter, not an original
server oracle. Independent controls reject changed source/maintained bytes and
accept semantically unchanged LF/CRLF inventory/prerequisite text.

The old dependency gates require their exact tracked Git LF bytes for inventory,
clients and generated receipts; this private Windows checkout was restored to
those unchanged tracked bytes before running their suites. No global Git
configuration or dependency logic was changed. New source gates qualify both
inventory/prerequisite newline forms themselves.

Limits: no wallet discovery, production data, actual identity relation, chain/RPC,
credentials, real sessions, native server compatibility or full original runtime
equivalence is established. Actual query-framework scheduling, compiler memo
identity and arbitrary React interleavings remain outside these finite port
tests. Captures, existing adapters, dependency locks and the feature ledger are
unchanged. Descriptive names are authored; upstream code/artifacts retain their
original attribution and ownership.
