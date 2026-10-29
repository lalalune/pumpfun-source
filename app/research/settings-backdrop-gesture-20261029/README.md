# Preserve Settings during a selection drag

On base `9f9d94c56f7bbedb6c3e45a9e95c287321313621` (app tree
`e3d6d8cd07df4f561a4fd058dad29d22de451bfc`), dragging from the Settings search
input onto its backdrop closes the modal and discards the filter. The browser
retargets the resulting click to `DIALOG`; the existing click handler treats
that target alone as an outside click.

The same trusted mouse sequence reproduces this at 1280×900 and 390×844. Both
records contain `pointerdown INPUT`, `pointerup DIALOG`, then `click DIALOG`,
with `isTrusted: true`. A plain native dialog with `closedby="any"` retains
the same drag. A separate actual outside click closes that reference, establishing
that this browser supports native light dismissal rather than ignoring the
attribute. This is a browser control, not a claim about the original site's
implementation or other engines.

Only `settings-control.tsx` changes in product source. A ref records whether
the press begins outside the dialog. Dismissal requires that origin and an
outside release/click position, and pointer cancellation clears the pending
press. Geometry distinguishes an inside endpoint even when pointer capture or
click retargeting reports the dialog. Routing, Cancel, focus restoration,
keyboard handlers and native `showModal`/`close` setup remain in their existing code.
No native `closedby` attribute or new browser capability requirement is added
to the product.

## Executed proof

`before-corrected/` and `after/` contain source inputs, raw reports and actual
pointer observations. Their frozen spec/runner are identical; the only changed
declared input is Settings product source. The baseline has two actual Settings
assertion failures after successful native controls. The candidate passes all
six mouse cases: inside→outside drag, outside→inside drag and intentional
backdrop dismissal at both widths. The checks preserve filter/URL state on a
drag and focus/query/hash behavior on dismissal. All recorded inputs are trusted;
page errors, console errors and external requests are zero.

An additional real Chromium CDP `touchStart`→`touchCancel` produces trusted
touch pointer events, preserves the dialog/filter and permits a later normal
outside click. This is cancellation/recovery evidence, not operating-system
touchscreen compatibility. The 16 unchanged Settings tests and five unchanged
Create external-link tests pass. Together these are **28 unique browser cases**.
Two repeated inside-drag cases supply after screenshots and add no unique
coverage. The raw control report is in `regressions/`; visual repeats are in
`after-visual/`.

Strict frontend typechecking, 21 source-contract/privacy tests, 10 Settings
model tests and app evidence verification (698 captures, npm integrity,
unchanged SDK sources) pass. `UNCHANGED-FUNCTIONS.json` records TypeScript AST
text equality of `select`, `trapFocus` and `navigateTabs` against the base.
Ordinary Escape controls pass. The base's composing-Escape problem remains the
separate open #1304; no IME repair or platform equivalence is claimed here.

## Reproduce

With the existing pinned dependencies and installed Chromium, the maintained
frontend configuration starts its loopback test server:

```sh
cd app/packages/frontend
corepack pnpm exec playwright test \
  settings-backdrop.spec.ts settings-pointer-cancel.spec.ts \
  settings.spec.ts create-external-links.spec.ts --workers=1
corepack pnpm exec tsc --noEmit --incremental false
```

For a separately running loopback server, use a temporary configuration that
imports `playwright.config.ts`, retains its accepted-clickwrap state, disables
`webServer`, and sets that server's `baseURL`. The actual run used port 3010,
one worker, finite failure limits, failure screenshots and full Playwright
traces disabled to bound disk use. `run.mjs` is the exact historical controller
with its disclosed workspace/output paths; it is retained as an execution
record. The specs above are the portable reproducer. It never executes captured
JavaScript and blocks non-loopback browser requests.

From the repository root, the additional executed checks are:

```sh
cd app
node --test tests/settings-contract.test.mjs tests/original_privacy_external_links.test.mjs
node packages/backend/node_modules/tsx/dist/cli.mjs --test tests/settings_model.test.ts
cd ..
python3 app/scripts/verify-evidence.py
```

`MANIFEST.json` binds the saved evidence bytes. These saved reports are finite
test evidence, not an independent browser attestation or a fresh rerun.

## Setup limits and preservation

The initial native-reference cleanup used a visible-only locator after the
native dialog had closed. Both attempts timed out before exercising the actual
Settings drag. `before/` preserves those raw blocked outcomes. Changing only
that locator to include hidden elements allowed the same baseline to reach the
actual defect. A first model command could not resolve `tsx` at the app root;
using the existing pinned backend executable ran all ten tests without an
installation. Both logs remain retained.

Original captures, SDK/dependencies, prior packets, footer/privacy integration,
global styles, shared menus, shell handlers and unrelated settings code remain
unchanged. This fixes an authored local UI interaction; it does not establish
original frontend parity, current server availability, auth behavior or security
acceptance.
