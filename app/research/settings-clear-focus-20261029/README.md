# Continue typing after clearing the Settings filter

On base `04be15f61e66d27282e2af3d581de984389eac90` (app tree
`e3d6d8cd07df4f561a4fd058dad29d22de451bfc`), activating Clear settings search
removes its focused button. Focus falls to `BODY`, so continued typing does not
reach the search input even though Settings stays open.

The selected baseline cases cover desktop mouse activation and mobile-width
keyboard activation (Tab to Clear, then Enter). All five subsequent trusted
`g/r/o/u/p` keydowns target `BODY`; the search remains empty. The corresponding
native `type=search` controls clear through their actual browser cancel affordance
or Escape, retain input focus and accept the same typing. No synthetic DOM key
dispatch or `fill()` is used for the continued-typing assertion: `fill()` would
refocus the input and conceal the defect.

The product fix adds a ref to the existing search input and focuses it from the
existing Clear callback. The input stays mounted while the Clear button disappears.
No route, filtering/model, preference, API, global shortcut or other modal logic
changes. This is an authored local UI repair, not recovered original-site parity.

## Actual qualification

The frozen spec/controller before and after have identical declared inputs
except `settings-control.tsx`. `before/` contains two actual workflow failures;
`after/` contains four passes across mouse/keyboard activation at 1280×900 and
390×844. Each native control also passes. After the fix, the trusted letter events
target `INPUT`, its value becomes `group`, the matching Group chats row appears,
and the exact URL/hash and open dialog are preserved. Errors and external
requests are zero.

The combined regression attempt on port 3027 reports **23 pass, one failure and
one not run**. The unchanged service-boundary test hardcodes origin 3010 and
classifies normal 3027 page/CSS/font GETs as unexpected. Its raw failure remains
in `controls/`. No origin assertion, mask or test was modified. The same owned
server was stopped and restarted on the required port 3010 with identical source;
only that failed boundary and the last unrun resize control were run there.
Both pass in `origin-controls/`.

The union is **25 unique passing browser cases**: four new Clear workflows,
16 unchanged Settings cases and five unchanged Create-link cases. The four new
cases repeat in the combined batch to capture screenshots and add no extra unique
coverage. A single clean 25-case batch is not claimed. Strict frontend typechecking,
21 source-contract/privacy tests, 10 Settings model tests and evidence verification
(698 captures, npm integrity, unchanged SDK sources) pass.

## Reproduce

The existing frontend configuration uses canonical loopback port 3010, which the
service-boundary test requires:

```sh
cd app/packages/frontend
corepack pnpm exec playwright test \
  settings-clear-focus.spec.ts settings.spec.ts create-external-links.spec.ts --workers=1
corepack pnpm exec tsc --noEmit --incremental false
```

For an existing separately started server, a temporary config can import the
maintained Playwright config, retain its accepted-clickwrap state, disable
`webServer`, and set that server's `baseURL`. The actual runs use one worker and
finite failure limits, with full Playwright traces disabled to bound disk use.
`run.mjs` is the exact historical controller with its disclosed workspace paths;
the checked-in specs are the portable reproducer. Non-loopback browser requests
are blocked, and captured JavaScript is not executed.

Additional executed commands from the repository root:

```sh
cd app
node --test tests/settings-contract.test.mjs tests/original_privacy_external_links.test.mjs
node packages/backend/node_modules/tsx/dist/cli.mjs --test tests/settings_model.test.ts
cd ..
python3 app/scripts/verify-evidence.py
```

`MANIFEST.json` authenticates the retained evidence files; `QUALIFICATION.json`
lists source hashes and the exact coverage union. Saved records are finite test
evidence, not an independent browser attestation or a new execution.

## Limits and preservation

An execution-transport disconnect initially prevented process creation for the
broader checks. One connection check recovered; the owned server was stopped
cleanly, and the never-started checks ran after one restart with unchanged source.
`transport-incident.json` distinguishes that orchestration event from tests.

This covers Chromium mouse/keyboard behavior at two viewport widths, not OS
touch/IME, other engines, original flag availability or backend compatibility.
The separate open #1304 composing-Escape and #1490 backdrop work is not copied or
qualified by this source change. Original captures, SDK/dependencies, earlier
packets, shared menus/styles and the paused backend prototype remain unchanged.
