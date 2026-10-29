# Source-bound lite-trade listener lifecycle

Captured module `915631` / shared registration `949629` supplies a complete keyed listener registry, React subscription lifecycle and event-to-local-update handoff. It is used by the captured Mayhem visible-page mint list and by the Home caller's explicit `mints/isEnabled/onLiteTrade` options. Existing source joins left this lifecycle external. This packet recovers that complete used factory as editable JavaScript and binds both protocol-namespace variants and the actual subject prefix.

It establishes no connection and implements no provider service. Connection operations, boot readiness, the live-coin store and React scheduling are explicit injected capabilities. No original website mount, auth, service availability, endpoint operation, native compatibility, price/oracle/accounting result or feature milestone is claimed.

## Source closure

`contract.json` binds eight source entries and 35 AST/range witnesses through the unchanged authenticated source reader:

- The only physical `915631/949629` factory, `32d1e326a183…`, including every private registry/helper declaration and both complete exported hooks.
- Both `985526` namespace variants, `d07a60b6380a…` and `d2419cfba786…`. Their full namespace declarations/getters are retained, including mutable objects. Both declare `Unified = "UNIFIED"`. Callers explicitly choose a variant hash; this does not identify an original active-loader winner.
- The actual `237237.V` subject prefix, `unifiedTradeEvent.lite`.
- Actual imports and selected complete enclosing caller statements from `457065` and `228998`. The former passes visible-page mints and a nonempty gate to `915631.f`; the latter calls `949629.f` with explicit callback/options. Their page/query/normalization/sorting logic is not copied.
- The source of external `390065.N` and `544514.f` is bound to clarify the capability boundary. `544514.f` is one-shot **boot/idle readiness**, not auth or session readiness. Neither provider implementation is reconstructed here.

The full store from proposed [#1870](https://github.com/lalalune/pumpfun-source/pull/1870) remains an injected `653805.x`-shaped capability: a selector hook with `getState().peekCoin` and `updateCoin`. There is no runtime import from that unmerged PR and no copied store or frame-batch implementation. The existing Mayhem joins in [#1812](https://github.com/lalalune/pumpfun-source/pull/1812) are separate. Original captures, source ledgers, previous packages and feature counts are unchanged.

## Behavior retained

A module instance shares a per-trimmed-mint registry across its hook users. Hooks retain their original per-hook mint keys. A `none` listener wins aggregate coalescing; otherwise the provider receives `latest`. A mode change unsubscribes then resubscribes. Removing the last listener deletes the registry entry. There is no invented provider refcount API, delayed release or server subscription acknowledgement.

The hook retains its sorted/joined mint dependency, stable forwarding callback, effect-updated callback ref, mint reconciliation and mode changes. Disabled, not-ready, empty and inactive states clear its current subscriptions. Unmount clears them too. Listener exceptions and unsubscribe exceptions follow the captured catches. A thrown provider unsubscribe is **not** evidence that transport resources were released; the finite failure check deliberately preserves that distinction.

The event adapter preserves the existing finite-positive `marketCap` guard, truthy price/timestamp branches, Date constructor/`now`, exact `type === "buy"`, and truthy previous pending ATH check. It passes an update to the injected local store and logs caught callback errors. It adds no field/freshness admission and makes no financial or oracle interpretation. The same provider is assumed across users of one module instance, as in the source; cross-provider arbitration is not supplied.

## Reproduction

Use the repository's documented pinned dependencies. From the repository root:

```sh
cd app
node scripts/original-lite-trade-listeners.mjs --check
node --test tests/original_lite_trade_listeners.test.mjs tests/original_source.test.mjs
node reconstruction/lite-trade-listeners/qualification/browser.mjs --output "/tmp/lite trade listeners fresh run"
```

The output directory must not exist. The browser controller finds its app root relative to itself, bundles locally, serves one ephemeral GET-only loopback fixture and closes browser/server in `finally`. It starts no Next server, app backend, socket, RPC or external data request. Captured factories are parsed without execution; only the generated translation runs. `--write` regenerates the client/contract. The contract gate compares parsed JSON semantics, not canonical JSON formatting.

`qualification/ports.mjs` is an authored local capability host. Its recorded `subscribe`, `unsubscribe` and event emissions are ordinary local calls, **not** original transport delivery or an emulated remote service. React browser/SSR checks test this finite composition only.

## Qualification and limits

- 21 direct/source checks pass across both namespace variants, including shared listeners, mode reconciliation, callbacks, mint/enable/readiness/connection gates, unmount, caught failures, event-to-local-update fields, eight actual verifier mutations, and a real React SSR control showing no effect subscription activation.
- All 11 unchanged source-reader checks pass.
- Six real React browser cases pass, three per namespace variant: shared callbacks/coalescing and cleanup, actual effect reconciliation, and event-to-local-store handoff. Zero page errors; all injected subscriptions are removed on ordinary unmount, browser closed and loopback server stopped.
- A pre-browser test-replay audit found a CWD-only SSR test setup failure: 20 checks passed and one failed from `app/`, because it resolved `app/app/packages`. The historical log and exact initial test bytes/blob/commit remain bound; the bytes are retained as an inert `.source.txt` file independently of public commit ancestry. The test now resolves dependencies relative to its module; the documented `app/` command passes all 21. Generated client, controller and fixture bytes were unchanged.

`qualification/VALIDATION.json`, runtime input readback and the sealed manifest preserve exact revisions, commands, outputs and cleanup. None of this proves original provider scheduling, service behavior, current live data, original UI parity or security acceptance.
