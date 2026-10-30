# Original complete Settings display/controller owner

This recovers the complete outer `124884.SettingsModal` display/controller boundary: header/close, controlled tabs, search input/clear, scroll reset, resource/section/results branches, reset confirmation, device note, Done and dialog-open callbacks. No native/global page is mounted. Original captures are authenticated and parsed as data, never evaluated.

Exactly two AST substitutions are permitted and verified inside the original exported function:

| Binding | Original boundary | Required replacement |
| --- | --- | --- |
| `Y` | Whole availability IIFE, immediately after translation and before resource attempt | `useVisibleSections()` returning the complete visible-section metadata array |
| `J` | Whole resource-attempt IIFE, immediately after availability and before focus hook | `useSettingsResourceAttempt()` returning the attempt-completed Boolean |

No other original function node is changed. The complete adapted owner, all 100 compiler memo slots and two full local metadata predicates occur exactly once in the used constructor. The generator authenticates the original full function and the two original IIFEs, constructs only these two replacements, compares canonical ASTs, and verifies exact generated client/contract bytes. Ten raw witnesses bind focus/reset/child/primitive/metadata call boundaries. No standalone recovered core is copied or imported from unmerged work.

`createSettingsModalOwner(capabilities)` returns the component accepting `{section,focusSettingId,onSectionChange,onClose}`. `useVisibleSections` is a required availability hook; its original address/permission/feature providers are not acquired or implemented. The source UI selects a matching section or the first visible metadata ID (and preserves the inert `trading` fallback literal for an empty list). Synthetic denied/unknown requests do not establish authentication or availability parity.

`useSettingsResourceAttempt` exactly matches the hook returned by #1911's `createSettingsResourceContent`; it is attempt-completed, not a new resource-readiness guarantee. `Loading` also matches #1911. The original content/scroll branch naturally remains inside the full parent and is credited as already recovered, without a new source-count claim for that region.

Focus must use #1920's **`useTransientSettingId(focusSettingId)` and `FocusContext.Provider`** directly. The latter receives `{value,children}`. Do not pass the higher-level `FocusProvider({settingId,children})` here: it would run the transient-ID hook a second time and use the wrong props. `SearchResults({query,visibleSections})` matches #1898; `SectionContent({section,onRequestClose})` matches #1952. Those source units, #1872 fields and #1839 state remain external credited ports. No field or protected child is reconstructed here.

Other capabilities are React JSX/compiler/state/effect/ID/ref, translation/key translation, `definitionsForSection` read-only resettable metadata, `resetSection(section)`, dialog/tabs/button primitives and icons. `resetSection` is only a callback port, not a persistence implementation. The original confirmation clears after that callback succeeds; a throw leaves confirmation open. Tab selection clears confirmation before forwarding selection. Reset availability uses strict-false metadata and disappears during nonblank search; no new policy is invented. Dialog callbacks close only on falsy changes; explicit header and Done callbacks retain their original behavior.

Search keeps raw controlled input but sends trimmed text to results with the visible metadata IDs. The native scroll owner resets on resolved section or blank/nonblank mode changes, not every term change. The original section-keyed parent controls child remount; no added focus, clear-button focus return, cancellation, query or staleness policy is introduced. Supplied hooks must obey React rules at their unconditional call sites. Their internal hook layouts, subscriptions and provider behavior are external and unqualified.

From `app/` with existing pinned dependencies:

```sh
node scripts/original-settings-modal-owner.mjs
node --test tests/original_settings_modal_owner.test.mjs tests/original_source.test.mjs
PUMP_SETTINGS_MODAL_OUTPUT=/your/isolated/output node --test tests/original_settings_modal_owner_browser.test.mjs
```

Tests supply only safe feed/privacy metadata, inert denied/unknown section selections, read-only results/section/loading ports and synthetic reset callbacks. Native browser typing/scroll and actual React rendering qualify the owner under those explicit ports; diagnostic primitive CSS is not original pixels or generic modal/focus-trap parity. No actual cookies/storage/sessions/credentials/user/account/preferences, address/permission/flag/provider acquisition, trading/admin controls or live requests are involved. No API/full-app/native/provider/security/completion claim. Original materials retain their authorship.
