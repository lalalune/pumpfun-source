# Original Settings decimal draft input

The complete `124884.eo` React renderer was a required `NumberInput` port in #1872's source-adapted `ed` field dispatcher. This supplies that full input owner, its actual decimal grammar and local frame dependency. Three complete original AST regions occur exactly once inside the used constructor; four authenticated raw witnesses bind the actual dispatcher number branch, supplied props, value/setter and mounted-state boundaries. Captures are parsed as data, never evaluated.

`createSettingsDecimalInput({jsx,jsxs,useMemoCache,useState})` returns the original component accepting `{value,onCommit,min,step,unit,label,isDisabled}`. All values and the commit callback are explicit supplied capabilities. This implements neither descriptor/value acquisition nor persistence, protected controls, account/trading/admin data or providers. The actual external #1872 dispatcher converts numeric-kind values with the original `typeof number ? value : Number(value)` and passes the callback/metadata unchanged. Existing #1839 state and #1920 Row remain external. The frame style shared with #1872 is an exact local dependency, not a new helper claim or duplicate dispatcher.

The draft starts null, so display uses `String(value)`. Focus snapshots that controlled value; accepted edits retain a local draft while immediate positive finite numeric values commit. Commas normalize to dots, only the original decimal grammar is admitted, and length is at most 12 UTF-16 code units. Empty, dot and zero can remain drafts without committing. Optional minimum uses `Math.max` after the raw positivity/finite test; no new min validation, maximum, precision, rounding or step policy is added. `step` remains an attribute on `type="text"`.

Parent-controlled updates remain masked by an active draft. Blur clears it and displays the latest controlled value. A commit callback error propagates after draft state was enqueued; there is no new rollback/catch. Native disabled blocks interaction; the handler itself adds no disabled guard. Malformed supplied values/minimums retain original stringification/Math.max behavior rather than invented sanitization.

From `app/` with existing dependencies:

```sh
node scripts/original-settings-decimal-input.mjs
node --test tests/original_settings_decimal_input.test.mjs tests/original_source.test.mjs
PUMP_SETTINGS_DECIMAL_OUTPUT=/your/isolated/output node --test tests/original_settings_decimal_input_browser.test.mjs
```

Only synthetic numeric props and callback state are used. Diagnostic browser CSS and read-only host labels do not establish original pixels, preference effects, native/global Settings integration, provider/API/full-app compatibility or security/completion acceptance. No actual cookies/storage/sessions/credentials/user/account data or live service request is involved. Original materials retain their authorship.
