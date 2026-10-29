# Captured coin query/cache and batch reader

The retained609252 coin-result wrappers call689943.V, but the existing GO display recovery (#1882) intentionally leaves that complete owning query/cache implementation external. This packet reconstructs **all52 memo slots of V**, its actual privateD reader, the two usedM cache keys, TTL constants,605587.c canonicalization and646908.L/B/_ literal closures. It source-binds **all nine physical609252 import/call contexts** as witnesses; it does not duplicate their wrapper implementation. The single689943 physical factory also registers783111. Other exports, history/F and unrelatedM keys are excluded.

The editable client is generated from selected captured AST nodes. Captures are parsed and hashed, never executed. Fifteen full factory entries and50 selected witnesses retain source URLs, strict UTF-8/UTF-16 ranges and hashes. The unchanged accepted997887.l identity is reused as `readSearchCoins` from search-session, with its maintained AST identity and three accepted dependency hashes checked. Existing search-session/positions namespace attribution is credited; no new identity/chain API or operation-ledger credit is claimed. POST /coins-v2/mints already exists in the static ledger.

## Runtime boundary

`createCoinQuery({useMemoCache,useQuery,useQueryClient,getContractClient,clock})` returns the complete `useCoins(mints, options)` hook and `readCoins(mints, options)` reader. These are translations, not an original runtime/provider acquisition. Supply compiler memo cache, query observer/client, clock and the exact759257.j factory capability. There is **no default request destination**. The source invokes `getContractClient()('POST /coins-v2/mints', options)`; no website transport, URL builder, cookies or authentication are acquired by this packet.

The reader sends `{body:{mints},credentials:'include',hooks:{afterResponse:[...]}}`. `includeNsfw` is read but omitted from the body; safe/nsfw query keys remain distinct. Its third-argument response hook throws on `!response.ok`; successful payloads pass unchanged through the accepted identity. No response schema admission, AbortSignal, headers, retry or pagination is invented. Runtime transport behavior beyond that named-operation capability remains external.

Cache inspection preserves the captured identity memo: changing the clock/cache alone does not rescan when the mints array and query-client identities remain stable. Exact coin keys preserve spelling; lowercase`0x` requests alone get canonical fallback scanning, choosing the highest timestamp and first equal tie. Freshness uses the strict60000ms boundary and exact TON/NEAR/Starknet exceptions. Query keys sort a copy and preserve duplicates; requests preserve input order. Merge precedence is stale→fresh→fetched, canonical last-wins, followed by original requested order/duplicates and omitted missing rows.

The source destructures limit/offset/sort/order without using them. Remaining options spread **last**, including caller overrides of key, function, enabled and timings. Raw query error/refetch/flags propagate. Loading depends on missing state, result count and query loading; success is `!loading && !error`, independently of the observer's isSuccess flag.

## Repeatable checks

From the repository root, with the documented pinned dependencies already installed:

```sh
node app/scripts/original-coin-query-cache.mjs --check
node --test app/tests/original_coin_query_cache.test.mjs app/tests/original_source.test.mjs
```

The source script also accepts `--app-root '/absolute/path with spaces/app'`. `--write` regenerates only this packet's client/contract. Contract verification compares parsed JSON semantics, not canonical JSON formatting. The direct suite exercises the full frame with explicit synthetic query/cache/memo ports, source/contract tampering and an actual ephemeral loopbackPOST. That local reader host asserts body/order/options, HTTP-error propagation and absence of Cookie/Authorization; it is not an upstream compatibility oracle.

For a standalone realReact/compiler workflow, use a **new, nonexistent output directory**, from any CWD:

```sh
node '/absolute/path/to/repository/app/reconstruction/coin-query-cache/qualification/browser.mjs' \
  --output '/absolute/path/to/new coin query output'
```

The controller uses installed React19.2.3, compiler runtime, esbuild and Playwright/Chromium; it installs nothing and starts no Next/backend/service. It hashes the whole bundle/runtime inputs before and after six finite cases. The local HTTP host serves only HTML/bundle; data and query observer/cache/scheduling are explicitly synthetic capabilities. Source promises and real React/compiler rerenders exercise cache identity/freshness, deferred missing-list completion/ordered merge/cache writes, NSFW body/key distinction, final option/refetch overrides, raw error/recovery and case fallback/disabled state. It checks observer cleanup, closes browser/host and preserves first failures in fresh outputs.

Qualification receipts and historical limits will be sealed under `qualification/`; these prove only the recorded finite composition. No mounted app, original loader winner/provider, current authenticated state, service availability, finance/oracle/price accuracy, original timing, feature milestones or native API qualification is claimed. Original captures, ledgers and earlier packages are unchanged.

## Sealed finite result

Runtime/client/controller freeze `c90c50e1607bd0e95d276a95e8dcc343f74dff2e` passed the source gate (50 witnesses/15 source entries/nine caller contexts), **26 direct/loopback +11 shared source-reader tests**, and **six realReact/compiler cases** with zero page errors. All17 pre/post input bindings agree; the host received only the two HTML/bundleGETs. Cleanup records zero observer subscriptions/DOM children and a closed browser/host. These local producer commit labels are not asserted to be public ancestors; public replay relies on retained file hashes/bytes.

The first direct attempt was25PASS/1FAIL: an authored tamper test searched decimal60000 while the source generator retains6e4, so that negative mutation did not alter the code. `INITIAL-TEST.source.txt` and `initial-direct.log` preserve the exact failing test bytes/output. The corrected test both changes the actual6e4 declaration and asserts every negative-code mutation changed bytes before calling the real verifier. The generated client is byte-identical to that initial attempt; no captured/runtime correction or original-source defect is claimed. All raw phase outputs remain preserved, and the browser method ran once after its freeze.
