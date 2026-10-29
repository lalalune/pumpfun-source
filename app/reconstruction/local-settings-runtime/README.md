# Original local-settings hook and switch workflow

This supplies the missing complete `547562` hook framework, `671027` initializer
and actual `416380` switch renderer for one safe original descriptor:
`807786`'s `feed.showAnimations`. Its path is actual Settings switch dispatch
`124884` → `416380` → `547562` → descriptor coercion → local JSON adapter →
notification → `useSyncExternalStore` snapshot → React render. The descriptor is
included by the actual `272700` registry spread. Exact complete retained ASTs,
explicit physical capture contexts and call witnesses are in `contract.json`.
Captured factories are parsed as data, never executed or imported.

The existing privacy-external-links unit already recovers selected `654506`
key/cache/fallback behavior. This unit credits that work and retains the full
used local-key declarations to close the new framework/UI path. It does not
claim first helper recovery, a whole registry, an active deployment winner or
feature completion. Upstream material retains its authorship; the factory
names and capability API are analyst integration names.

## Preserved semantics

- Definition objects own WeakMap-cached views. `Object.is` compares raw adapter
  values before coercion, preserving the same coerced object on repeated reads.
  The raw cache updates before coercion; a thrown coercer can leave the prior
  coerced result cached for that same raw value. This source quirk is preserved.
- Direct `writeSetting` coerces and writes. The React setter first reads the
  current snapshot even for a literal update; functional updates therefore read
  the latest adapter value, rather than a prior render's captured value.
- SSR returns the uncoerced definition default or an explicit `serverValue`
  override, including `false`, without reading browser storage. The original
  React memo-cache and `useSyncExternalStore` calls remain intact.
- Initialization marks a definition in its WeakSet before checking storage or
  adopting legacy values. Adoption merges plain objects/arrays in order, writes
  the coerced result before cleanup, and preserves legacy keys only for strict
  `removeAfterAdopt:false`. A failed throwing write is not silently retried for
  that same definition. Tests use synthetic legacy keys, never trading data.
- Local JSON storage retains parsed-object caches and write-failure fallback.
  A successful write clears fallback; a storage event does not. A new module
  lifetime reads the supplied durable port again. Failed removal cannot invent
  deletion. Module-lifetime event listeners remain installed; subscriber
  cleanup removes the callback, with the original Set deduplication behavior.
- The actual switch checks only strict `true`; its first-paint disabling and
  confirmation state logic remain in the complete source component. Private
  Switch/confirmation/provider implementations are explicit ports, not supplied
  original behavior. This unit constructs only the safe nonconfirming descriptor.

## Integration boundary

Importing `client.mjs` has no side effects and reads no global browser data.
Construct each runtime once per intended original module lifetime, then supply
its explicit ports to actual React components. The relevant returned interfaces
are:

```js
const local = createLocalKeyRuntime({ window: syntheticWindow, StorageEvent });
const definition = createFeedAnimationsDefinition(local);
const settings = createSettingsRuntime({
  registry: { [definition.id]: definition },
  initializeLegacy: createLegacyInitializer({ window: syntheticWindow }),
  useMemoCache, // Actual React/compiler runtime capability.
  useSyncExternalStore,
});
const SettingSwitch = createSettingsSwitch({
  ...explicitReactTranslationControlPorts,
  settings,
});
// Render <SettingSwitch definition={definition} label={suppliedLabel} />.
```

The source-derived descriptor uses JSON key `home.show-animations`, default
`true`, and only strict `false` disables it. It is device-local metadata, not
account ownership or server authorization. There is no implicit registry,
window, storage, cookie, flag service, API destination or control implementation.
This adds no generic preferences page and does not fabricate a Home animation
effect. Existing app Settings, Home, privacy, notifications, captures, SDK,
dependencies and lockfiles remain unchanged. LocalBucket and locale-cookie
adapters remain outside this unit; no current cookie or credential is read.

## Repeatable qualification

Run from `app/` with the existing pinned dependencies:

```sh
node scripts/original-local-settings-runtime.mjs
node --test tests/original_local_settings_runtime.test.mjs
PUMP_LOCAL_SETTINGS_OUTPUT=/your/isolated/output node --test tests/original_local_settings_runtime_browser.test.mjs
```

The source gate compares exact generated client and contract UTF-8 bytes and
checks complete retained ASTs against authenticated originals. Negative tests
reject changed client logic and even semantically equivalent noncanonical
contract text. The initial negative fixture could not hardlink between the
workspace and temporary filesystem (`EXDEV`); its narrowly scoped fallback copies
immutable test inputs when that specific error occurs. Source evidence is never
modified. That initial log is retained separately from final frozen-head results.

Tests cover source identity, caching, fresh functional updates, actual React SSR,
legacy/error ordering and fallback quirks. The standalone browser uses real
React/compiler hooks and the complete original renderer at 390px and 1280px.
Its storage/events and host controls are explicitly synthetic ports. It exercises
mouse/keyboard updates, latest-value functional updates, failed-write fallback,
external notifications and unmount subscription cleanup without accessing real
browser storage or cookies. Its controlled fixture is not the product Settings
page or an original screenshot. No Next process or backend is involved.

The frozen source/method revision is
`3e6abe66aed513eac9db5d396d242e06c0348790`: **19 domain + 11 shared-source
tests pass**, and **one actual React browser workflow passes at both widths**.
Recursive typecheck, 698 capture/npm/unchanged-SDK checks and nine progress tests
also pass. See `validation/RECORD.json` for exact input/output hashes and setup
failure limits. The later documentation/receipt commit preserves every executed
runtime, generator, method and original-source input; no Next build or full-app
browser result is claimed for this unmounted module.

No server persistence, auth/session, support/Firebase, admin/trading/claim flow,
signing, live request, network mutation, original private provider, production
API, pixel parity, security clearance or milestone completion is qualified.
