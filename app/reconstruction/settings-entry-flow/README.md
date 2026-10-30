# Original Settings entry workflow

This recovers the complete `443032.SettingsModalHost` and `487832.v` URL/event opener as editable React logic. Five complete original AST regions occur exactly once in the used `createSettingsEntryFlow` constructor. Eleven raw witnesses and six authenticated physical factories bind the schema, feature flag, metadata, event import, dynamic callback and static `298590 → 190147 → 124884.SettingsModal` chain. Captures and chunk loaders are parsed as data, never evaluated or requested.

Supply React JSX/compiler/effect capabilities, explicit `window/URL/CustomEvent`, `useFeatureFlag(settingsFlag)` for the original `WEB_SETTINGS_HUB` key, the actual metadata's `sectionIds`, and **one atomic** `useQueryStates` capability with `parseAsStringEnum` and `parseAsString`. The retained host constructs the original `{settings,setting}` schema and `{history:"replace",clearOnDefault:true}` options. Two single-key hooks are not a substitute. The accepted #868 single-query subset does not supply this API; vendor parser, scheduling, history queue, cache and SSR behavior remain external.

The constructor returns `{eventName,openSettings,SettingsModalHost}`. `openSettings({section,settingId})` updates the existing URL with `replaceState` before dispatching `pump:open-settings` using the original detail object. Other parameters, duplicates, hash and history state survive. Its setting ID test is **truthy**; the host listener forwards into an atomic callback with **nullish** conversion. An empty string can therefore be deleted by the helper then re-added by the listening host. Close clears both keys. Errors propagate in original order: a history failure prevents dispatch; a dispatch failure does not undo the committed URL.

The feature flag controls event-listener installation and modal rendering. Effect dependency cleanup removes the old listener. No section or a false flag returns null and unmounts the child; reopen mounts a new child. Section changes while open retain its identity. `dynamic(loader,{loadableGenerated:{modules:[190147]},ssr:false})` and `loadModule(298590) → Promise<{SettingsModal}>` are required capabilities. The actual static bridge is witnessed without running original bundles. Dynamic loading/cache/error/SSR/provider behavior belongs to the supplied implementation; it is not reconstructed Next dynamic or the protected child modal.

Attribution: existing #675/#683 metadata, #868 query subset, #1911 resource, #1920 focus, #1898 results, #1952 content, #1872 dispatcher and #1839 state are credited external boundaries. None are copied or imported from unmerged work. No native page, global Settings mount, focus/highlight feature, protected control or provider is changed.

From `app/` with existing pinned dependencies:

```sh
node scripts/original-settings-entry-flow.mjs
node --test tests/original_settings_entry_flow.test.mjs tests/original_source.test.mjs
PUMP_SETTINGS_ENTRY_OUTPUT=/your/isolated/output node --test tests/original_settings_entry_flow_browser.test.mjs
```

Tests use only synthetic fresh URL/history/event/query/feature state and a read-only modal probe. The finite browser uses native URL, history, events and actual React lifetimes through explicit recording ports, a synthetic atomic query capability and a React.lazy/Suspense-compatible dynamic port. These choices demonstrate recovered source behavior under stated capabilities, not original Nuqs/Next/provider parity. No actual cookies, storage, sessions, credentials, user/account/preferences, tenant, permission or protected acquisition; no trading/admin controls, native/API/pixel/full-app compatibility, security clearance or completion score is claimed. Original materials retain their authorship.

Frozen qualification at `63d720af1c2141276e96efffa1950556c5efccf0` passes seven domain/SSR plus eleven shared-source tests, one actual React/Chromium two-width workflow, three workspace typechecks, 698 capture/npm/SDK checks and nine progress tests. Both widths have zero unexpected errors/overflow. [Sealed receipts](validation/README.md) bind 19 selected inputs and preserve the initial synthetic SSR harness failure separately. Packet verification passes normally and under Python `-O`; none of these results establishes original provider/vendor or full-app parity.
