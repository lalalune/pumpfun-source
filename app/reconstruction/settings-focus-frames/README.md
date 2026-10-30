# Original Settings focus, row and section frames

This closes the safe read-only frame capabilities left explicit by the existing Settings reconstruction: the complete grouped `165228` focus context, reader, transient-focus hook and provider; `379288.s` full row; and `379288.X` full section/header display. It provides editable, consumable original renderers and their actual focus/scroll lifecycle, not another field-ID or timer helper.

The generator authenticates the one captured grouped `[379288,165228]` physical factory and exact `124884` caller context. Seven complete AST regions occur exactly once inside the used exported constructor. Nine raw witnesses bind dependencies and actual Settings `h(H) → context.Provider(value)` plus real row/section output sites. Captures are parsed as data and never evaluated. Original authorship is preserved.

`createSettingsFocusFrames(capabilities)` returns `FocusContext`, `useFocusSettingId`, `useTransientSettingId`, `FocusProvider`, `Row`, and `Section`. Supply actual JSX, React compiler memo/hook/context capabilities, the original class combiner as an explicit `classNames` port, and `window: {setTimeout,clearTimeout}`. No global window property is patched. The complete exported `FocusProvider` wraps its children with the transient hook value. The actual SettingsModal separately calls that same hook and passes its value to that same context; it is not falsely described as literally rendering the exported wrapper.

`Row` preserves every original slot: title, description, note, control and children, optional ID/dense/class metadata, ref, focus marker and highlight classes. A matching defined setting ID scrolls into view with `{block:"center",behavior:"smooth"}` when the focused boolean changes. This changes visual position, not keyboard focus, and does not implement a parent focus trap. `Section` preserves its optional header/description, child divider wrapper and test ID. Supplied content may be read-only nodes; no preference control or value is acquired here.

The original focus state is one-shot: it starts true once, returns a truthy target until the native 2500ms timeout, and cleans up the prior timer when target changes or component unmounts. A target change before expiry restarts the timer; a target change after expiry **does not reset state to true**. A fresh mount initializes again. Falsey targets return null and schedule no timer. These source quirks are preserved, not replaced with a new highlight policy.

Attribution: #1839 state, #1872 choice/field, #1898 results and #1911 resource/content branches already bind their callers with these explicit frame/focus ports. None of their source is copied, imported as an unmerged runtime dependency, retallied or superseded. Prior native Settings focus/clear/filter/viewport fixes and generic shell/search/modal primitives remain unchanged. This unit does not claim the native local Settings page adopts the original frames.

Run from `app/`, using the existing pinned dependencies:

```sh
node scripts/original-settings-focus-frames.mjs
node --test tests/original_settings_focus_frames.test.mjs tests/original_source.test.mjs
PUMP_SETTINGS_FOCUS_OUTPUT=/your/isolated/output node --test tests/original_settings_focus_frames_browser.test.mjs
```

The source and complete finite method are frozen before final qualification. Node tests use actual React SSR with a timer port that would throw if SSR tried to acquire a timer. The browser method uses actual React/compiler, native smooth-scroll and a native 2500ms clock, at 390px/1280px. Its timer capability records and forwards calls, without fake clocks, global overrides or scroll spies. It checks native centered geometry, no repeated scroll/timer on unrelated rerender, target change, preserved keyboard focus, actual timeout/no-reset behavior, fresh mount, cleanup across an elapsed timeout window and falsey target behavior. The authored readonly host has no original provider or real preference state.

No actual cookies, storage, sessions, credentials, user/profile data, tenant/service request, preference mutation, wallet/admin/trading or protected availability path is acquired or implemented. No whole original Settings/global mount, original class-combiner/CSS/visual/native/API parity, completion or security acceptance is qualified. Screenshots show authored fixture styles, not the original product theme.
