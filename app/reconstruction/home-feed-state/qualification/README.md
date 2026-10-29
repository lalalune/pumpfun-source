# Finite reconstructed-hook qualification

The browser controller and fixture are authored test hosts. They mount the
complete new translation in pinned React 19.2.3 and its real compiler memo
runtime, with synthetic query/seed/codec capabilities. They do not mount the
maintained Home page or the original website.

Frozen runtime source: `ea81b770d889f0696a1edb430092a4b5260bcf10`.
The first run passed **6/6**, with zero page errors:

1. First-key deduplication, first 12 rows, local append 12 and matching options.
2. Raw-array and WeakMap object identity preserve cached normalized rows.
3. Pending count/preview caps, show-new cap, retired fallback and local expansion.
4. Seed chain/initial-viewer gating and viewer reset.
5. Loading/error/disabled output under the supplied query states.
6. One actual 2500 ms interval, then real React unmount cleanup.

Five scenarios use a manual timer capability. Only the sixth observes the
native clock; its first tick was observed after 2519 ms. Neither that one
measurement nor manual callback stepping establishes production timing.
Query observers/cache/retry scheduling and seed/provider operation are not
implemented by this fixture. No query function or original service was invoked
in the browser run; its two HTTP reads fetch only the authored HTML and bundle.
The separate Node test uses one genuine local HTTP synthetic snapshot.

`browser/INPUTS.json` binds the pre-launch source head, twelve actual bundle
inputs (including maintained code, React, ReactDOM, compiler runtime and
scheduler) and bundle SHA-256. `browser/RESULT.json` keeps every case and its
observations. The trace and stdout are retained. Browser and server closed
normally; the server was not listening on exit. No Next or on-disk bundle cache
was created. There were no failed browser attempts to discard.

Later source-binding additions authenticate the base58/compiler dependency
edges and add verifier-negative cases. The browser-tested client, controller
and fixture bytes remain identical; their binding is retained separately.
No additional browser result is inferred for changed code.

Run the command in the parent README into a fresh output path. It records the
actual new checkout head and new observations without requiring this historical
private commit or overwriting these receipts. Setup failures remain setup
failures; stdout redirection preserves them even before browser launch.
