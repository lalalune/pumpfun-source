# Source-bound live-coin state and frame batching

The captured Mayhem mint/cap join and other readers use shared module `653805`, while the lite-trade caller selects its `updateCoin` operation and consults `peekCoin`. Those call sites previously led to an external state boundary. This packet recovers the **complete captured queued store, shallow selector cache, used subscription middleware, and both physical frame-batch variants**, as editable JavaScript with explicit runtime ports.

This is source reconstruction, not a mounted feature. There are no service requests, socket subscriptions, original provider implementation, financial interpretation, native API qualification or feature-ledger changes.

## Retained source and boundaries

`contract.json` binds nine source entries and 66 AST/range witnesses through the unchanged authenticated source reader. It retains the complete private declarations and selected export bodies from:

- `653805` / shared `362324`, factory `f2496f3277c7…`: queued operations, committed and pending reads, ATH-field merge, all three selectors, shallow equality and reference retention.
- Both `811005` variants, `eaadb129bb56…` and `c232e5e54526…`: full scheduler state, callback queue, batch constructor, global enqueue, pause hook and effect cleanup. Callers must explicitly select a hash. No original active-variant winner is inferred.
- Used `634103.u` (`subscribeWithSelector`), including immediate notification, equality function and unsubscribe forwarding. The persistence/storage exports in that factory are excluded; the existing settings-framework recovery in [#1839](https://github.com/lalalune/pumpfun-source/pull/1839) remains separate.

The curried `78436` bound-store API and React subscription scheduling remain an injected provider port. React/compiler hooks, clock, browser scheduler and logger are also injected. `qualification/ports.mjs` is an authored synthetic host, not the original Zustand/provider implementation.

Four complete selected enclosing consumer statements and their import/receiver ranges are bound separately: `457065.J`, `401134.F`, `493870.k`, and `915631.x`. They establish actual read/update uses without implementing those screens or their transports. The existing Mayhem join in [#1812](https://github.com/lalalune/pumpfun-source/pull/1812) remains external; its `undefined`-only fallback is not replaced. These witnesses are not an exhaustive consumer graph or a minified-name/global-loader resolution claim.

## Behavior retained

`updateCoin`, `setCoin` and `removeCoin` are local queued state operations. Ordinary getters see committed values. `peekCoin` applies a pending operation without committing it. A later `committed` operation retains the prior queued base; a later explicit set/remove replaces the base while prior queued patches can survive. The latest enqueue timestamp is retained even if the injected clock moves backwards. Defined ATH fields use the captured `Math.max` operation; there is no added number, field, freshness or price admission.

A visible queue schedules RAF and a 100 ms fallback. Hidden/no-RAF queues use 250 ms. Visibility change can flush pending work. Nested pause effects cancel global handles; the final completion releases and flushes, while unmount cleanup releases/reschedules without directly flushing. Direct `batch.flush()` bypasses the global pause. The batch clears a snapshot before callbacks, preserves reentrant enqueues, and isolates callback errors through the logger.

The captured retained batch registry and visibility listener have no unregister/dispose operation. This packet does not invent one. Closing the qualification page releases its environment; that is distinct from source-level disposal. Set/Map-like shallow comparison uses size and `get`, including its existing behavior for different keys whose values are both `undefined`. No generic equality replacement is substituted.

## Reproduction

Use the repository's documented pinned dependency setup. From the repository root:

```sh
cd app
node scripts/original-live-coin-state.mjs --check
node --test tests/original_live_coin_state.test.mjs tests/original_source.test.mjs
node reconstruction/live-coin-state/qualification/browser.mjs --output "/tmp/live coin state fresh run"
```

Choose a **new** output directory; the browser controller refuses to overwrite one. It derives its app root from its own location, bundles locally from existing dependencies, starts one ephemeral GET-only loopback server, and closes Chromium/server in `finally`. It uses no Next route, app backend or external service. Captured factories are parsed without execution; only the new generated translation is run. `--write` regenerates the editable client and contract. The contract checker compares parsed JSON semantics; it does not require canonical JSON formatting.

## Finite qualification

- 25 direct/source checks passed across both variants: interleavings, pending/committed reads, ATH/clock behavior, all selectors, shallow reference rules, listeners/equality/unsubscribe, reentrancy, callback errors, RAF/fallback/visibility, nested pause completion/cleanup and eight actual verifier mutations. One real Node timer control exercised the 250 ms no-RAF path; the other scheduler cases use explicitly artificial time.
- The unchanged shared source-reader suite passed all 11 checks.
- Six real React/compiler browser cases passed: three per variant, covering committed/pending rendering and selector stability, actual nested pause effects/cleanup, and native RAF delivery with fallback cancellation. The provider and manual scheduler remain synthetic ports. Zero page errors were recorded, and browser/server cleanup was observed.
- The first direct-test attempt is preserved separately: 21 passed and four failed. Two repeated oracle mistakes caused those failures: a backwards artificial clock step did not reach its scheduled frame, and Set insertion order was incorrectly expected to change the captured entries-based comparison. Only those expectations/stepping were corrected; the translated client bytes were unchanged. The raw first log is historical and is not relabeled as the final test source.

`qualification/VALIDATION.json` and `qualification/MANIFEST.json` bind the exact records, frozen source head, commands and limits. No mounted website behavior, production delivery, original-provider timing parity, oracle/accounting correctness, security clearance or native compatibility follows from these finite results.
