# Original Home read-ahead and inactive FOLLOWING badge

The captured MAIN Home component has two complete read-coordination owners beyond its individual feed readers: a **15-slot inactive FOLLOWING badge** and an **8-slot three-feed read-ahead effect**. This packet reconstructs both, their shared first-page cache updater and the actual tab consumers. It does not duplicate the standalone feed read/query cores or mount a page.

`original-home-feed-coordination.mjs` authenticates **24 raw AST witnesses in one physical 163807 factory** against the retained capture manifest and complete factory inventory. Witnesses bind both whole IIFEs, actual calls/input objects, the tab's `newCount`/`reset` consumers, all used import roles and the complete cache updater. The checker also attributes the existing private key/query signatures as required ports. Captured bundles/factories are parsed, never evaluated.

## Complete behavior

The inactive badge preserves:

- the source's literal `viewer !== null && !isActive` event-hook gate, not an authentication check;
- raw event-ID deduplication, while **every** event—including a duplicate—still runs the prefix cache updater and invalidation;
- first-page trimming across every matching viewer/page-size/kinds prefix, followed by `invalidateQueries({queryKey:prefix,refetchType:'none'})`;
- the updater's `undefined` return for zero/one page, preserved first-page references, and deliberate dropping of other cache fields when trimming;
- active-tab and viewer reset behavior, a stable explicit reset callback and compiler memoization. A chain change changes the subscription key **without clearing pending IDs**.

Read-ahead invokes the original Home, Top and FOLLOWING prefetch capabilities in that synchronous order, without awaiting their promises. It skips only FOLLOWING when `viewer === null`, defaults only an undefined `followingChain` to `all`, supplies page size 20 and passes the returned query descriptor unchanged. It preserves the complete dependency list and adds no catch, cleanup, cancellation or retry behavior.

## Required credited boundaries

`createHomeFeedCoordination` requires exact original-signature capabilities for:

- `445242.c` and React `useState`/`useEffect`;
- `606933.useQueryClient`, with the used `setQueriesData`, `invalidateQueries` and `prefetchInfiniteQuery` APIs;
- `106009.f`'s event-hook object API (`enabled`, `viewer`, `queryKey`, `kinds`, `surface`, `onNewContent`), whose presence/service acquisition is unimplemented here;
- [#1966](https://github.com/lalalune/pumpfun-source/pull/1966)'s original private `ec/et/el` query/key signatures, original `637172.m/R` chain namespace and `735821.G` kinds value;
- [#1846](https://github.com/lalalune/pumpfun-source/pull/1846)'s `99859.Z` Home prefetch and [#1973](https://github.com/lalalune/pumpfun-source/pull/1973)'s `364468.H` Top prefetch.

These are credited required capabilities, not silent imports from open PRs. The private key and chain roles are original lexical/namespace APIs, not a claim that #1966 exports each as a public module member. No earlier read/query core is copied, executed or awarded new source credit. Qualification-only `key-ports.mjs` reuses the two small exact source key signatures; chain normalization and the following query descriptor remain explicit synthetic ports in the finite tests.

## Replay

From the repository root with the documented pinned dependencies already present:

```sh
node app/scripts/original-home-feed-coordination.mjs --check
node --test app/tests/original_home_feed_coordination.test.mjs app/tests/original_source.test.mjs
node app/reconstruction/home-feed-coordination/qualification/browser.mjs --output /absolute/path/to/NEW-output-directory
```

The deterministic source gate reproduces the client, qualification keys and semantic JSON contract; it does not claim canonical JSON formatting. Negative tests actually alter emitted behavior/contract and invoke the verifier.

The browser controller resolves its inputs relative to its own file, refuses an existing output directory and preserves before/after hashes, result, trace and any failure. It uses pinned React 19.2.3 and its real compiler-cache API, esbuild 0.25.12 and Playwright 1.64.1. Only an ephemeral loopback HTML/bundle host runs. No Next, app backend, data-provider call, WS, RPC, wallet, cookie/session or telemetry request occurs.

Six real-React workflows cover prefix trimming and dedup, viewer/active/chain transitions, prefetch ordering/descriptor identity, effect dependencies and query-client replacement, null-versus-undefined gates, and a rendered local reset callback. The cache is a primed real Map with the used prefix/update semantics; the event source and prefetch/chain/query-descriptor ports are explicit synthetic capabilities. The reset case uses a local `HTMLElement.click()` callback, not a trusted original-tab interaction. Original event subscriptions, query scheduling, TTL/focus behavior and actual reader/provider implementations remain unqualified.

This is source and finite adapter-composition recovery, not original mounted UI, current personalized data, authentication, mutation, financial, native API, feature milestone or security qualification. No capture, prior packet, feature ledger, milestone or source count is changed.

## Retained result

At local source/method freeze `ea73078afb50fd8f76c98660111f79c5e895f3b9`, **12 focused + 11 shared source-reader tests** and the first frozen **six-case React/compiler-cache run** pass. The browser receipt records zero errors, all 15 input bindings unchanged, zero remaining event listeners, an empty root and closed browser/host. Its only requests were the local HTML and bundle GETs. Direct tests ran before the local commit with identical committed bytes.

`qualification/BINDINGS.json` records prior API attribution with immutable public source hashes and explicit private-role/export limits. No prior read core is imported or executed. In particular, #1973's later public query-builder export correction leaves its H-prefetch function unchanged; this unit uses that required original signature. The SHA256 manifest covers current packet files plus generator and tests, excluding itself. Local producer commit labels are historical checkout identifiers; public metadata can differ while the qualified tree/bytes remain equal.
