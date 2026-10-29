# Source-bound activity query, queued store and readback

The captured `201629` owning hook is a separate path from `849812.b`: it warms an eligible query from other cache entries, fetches missing batches, patches a queued activity store, seeds cached responses in a microtask, and returns a selected activity projection. This packet reconstructs that complete hook and the complete `372743` store, with actual Home/GO caller statements. It preserves all three query variants and five store variants through explicit selections.

This is not a mounted website feature or service implementation. There are no external requests, sockets, auth/session capabilities, original provider implementations, financial/oracle/accounting claims, native compatibility claims or feature/endpoint credits.

## Source and reused boundaries

`contract.json` binds 17 source entries and 131 AST/range witnesses through the unchanged authenticated source reader. Complete private declarations and exports are retained for all three `201629` variants and all five `372743` variants. Actual `228998` contains two selected calls and `20149` one; complete enclosing statements expose their context without copying their screens, filters or query providers. `998243.f` is the actual `queueMicrotask` forwarding wrapper; its native scheduler is an injected capability.

The client receives these existing boundaries explicitly:

- `849812.g` batch reader and the `680930` helper interface, credited to proposed [#1873](https://github.com/lalalune/pumpfun-source/pull/1873). No reader or other owning query frame is copied. The helper equality is specifically the captured `24h.volumeUSD`/`priceChangePercent` comparison, not generic deep equality. `qualification/helper-ports.mjs` reuses all six known helper contexts **only as source-bound qualification capabilities**, with their attribution and explicit variant selection. It is not a runtime client dependency or another helper recovery claim.
- The curried bound-store provider, subscription middleware and frame-batch API, credited to proposed [#1870](https://github.com/lalalune/pumpfun-source/pull/1870). No provider/frame scheduler implementation is copied; the qualification host supplies those ports.
- React hooks, query/client/cache/observer, `Date.now` and native microtask scheduling. The synthetic provider/query/frame host is clearly separated from the translated source.

There is no runtime import from an unmerged PR, no silent dependency on its files and no original active-loader winner claim. The authored variant dispatcher accepts only its own supported hash-string keys; inherited object keys are not variants. All captures, ledgers, counts and earlier packages remain unchanged.

## Preserved behavior

The query uses Set/filter/sort mint normalization and a joined key. Cross-query warming is permitted only when the current key's data is `undefined`; it requires a fresh, noninvalidated cache entry and a fresh global per-mint timestamp. The entry with the highest `dataUpdatedAt` wins, with first-entry retention on a tie. Missing batches receive the original interval/metric options and signal. Every nonempty request increments its hook's generation. Only the latest completion patches the store, while **all** completions still update fetched-mint timestamps and return their own merged response.

Truthy observed query data queues a seed microtask independently of fetch enablement. Patches and seeds enqueue until a frame flush. Within a window whose previous and next values are both truthy, patches skip nullish fields; otherwise the next window replaces the previous value, including null. For an existing address, seeding fills only missing fields within windows truthy in both current and seed data. A wholly absent window is skipped. A new address receives the whole seed. Clearing resets committed state and pending batch data, but does not invent cancellation for a previously queued seed microtask or global scheduler.

`readBack=false` selects a shared empty object. Selected-field equality can retain old unselected metrics. On change, the hook caches a shallow copy but initially returns the new projection; a later equal projection returns the cached copy, so those first two references can differ. Subsequent equal reads retain the cached reference. The missing-`24h` refetch guard consults committed state, then awaits invalidation before refetch. The hook introduces no new error result field or reader error policy.

## Reproduction

With the repository's documented pinned dependencies, from the repository root:

```sh
cd app
node scripts/original-market-activity-state.mjs --check
node --test tests/original_market_activity_state.test.mjs tests/original_source.test.mjs
node reconstruction/market-activity-state/qualification/browser.mjs --output "/tmp/activity read state fresh run"
```

Use a fresh output directory. The controller resolves its own app root, bundles locally, serves one GET-only ephemeral loopback fixture and closes browser/server in `finally`. No Next server, app backend or data-service request is used. Captured factories are parsed without execution; the new translation is executed against explicit capabilities. `--write` regenerates the client, semantic JSON contract and qualification helper file. The contract checker does not require canonical JSON formatting.

## Finite results and historical limits

- 33 direct/source checks pass: all five store variants, all three query variants, all six helper contexts, native microtask control, TTL/cache/generation distinctions, seed/readback/reference/refetch behavior, signal/rejection propagation and eight actual verifier mutations. The artificial frame/query/cache capabilities do not establish original provider or timing parity.
- All 11 unchanged authenticated source-reader checks pass.
- Six real React browser cases pass, two per query variant using the first explicit store/helper contexts. They exercise native microtask seeding and frame/readback handoff, reference behavior and refetch order, plus overlapping generations, stale-completion timestamp refresh and cache warming without an older store overwrite. All five store and six helper variants are covered directly, not claimed as a browser Cartesian product. Zero page errors; ordinary unmount leaves zero injected provider listeners/pending frame items, and browser/server close. The source has no added global cache disposal.
- Initial direct tests recorded 16 passes/eight oracle failures. The test incorrectly expected an absent seed window to be added and expected the first returned projection to be the cached copy. Both expectations were corrected to the actual source; exact original test bytes/log and hashes remain retained. An intermediate correction's log is preserved privately; the original missing-window input and explicit absence assertion are present in the final test.
- A separate pre-browser counterexample showed the **authored** variant dispatcher accepting inherited `toString`/`constructor` keys. Own string-key checks corrected this adapter boundary before the browser run. The original query/store/helper function bodies were unchanged. Exact pre-fix client/helper bytes and raw counterexample are retained as inert historical evidence, not an original-source defect or a security claim.

`qualification/VALIDATION.json`, runtime input readback and the sealed manifest bind the exact phase revisions, inputs, logs and limits. Local injected fetch callbacks and cache rows are not real service responses or original query-engine behavior. No feature milestone, original visual parity, accounting result or security acceptance follows from these finite checks.
