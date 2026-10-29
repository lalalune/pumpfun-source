# Settings identifier search text

The captured `124884.eb` search/results consumer indexes translated label,
description, search terms, section label and `definition.id.replace(/[.]/g, " ")`.
The local mapped Settings search omits that last operand. Thus the visible
external-link row matches `external links`, but its captured identifier words
`privacy confirmExternalLinks` produce no result. The same omission affects
other already-mapped identifiers such as `notifications browserPush`.

This correction adds only the identifier text to the native search document.
It does not add definitions or controls, infer any preference/account value,
change token-AND matching/order, normalize periods in the query, or change
Unicode/case/locale policy. Literal dotted queries retain their prior behavior.
Open #1188 separately changes compatibility-normalization order in the same
file; that work is credited as distinct and is neither copied nor superseded.
An integration may touch that file while combining the independent operands.

`SOURCE.json` and its verifier authenticate the original raw factory, complete
filter/results caller and actual identifier operand without evaluating captured
code. The native check locates the operand inside the actual used definition
filter/search document and permits only the source parameter-name adaptation
from `e` to `setting`. This is an operation/caller attribution, not whole
Settings, original visibility/translation/provider or search equivalence.

Run from `app/` using the existing pinned dependencies:

```sh
node scripts/original-settings-id-search.mjs
node packages/backend/node_modules/tsx/dist/cli.mjs --test tests/settings_model.test.ts tests/settings_identifier_search.test.ts
```

The finite browser method attaches to an independently started local Next
server. From `app/packages/frontend/`, start the normal development command on
an owned loopback port, then run:

```sh
PUMP_SETTINGS_BASE=http://127.0.0.1:3027 \
PUMP_SETTINGS_OUTPUT=/your/isolated/phase-output \
node node_modules/@playwright/test/cli.js test --config playwright.settings-id.config.ts
```

The method uses the actual Settings page and native search input at 390px and
1280px. Standard label/accent search and unknown/dotted-query negative controls
precede the identifier assertion; focus and normal dismissal follow it. It
never fulfills JSON or activates a setting control. Its accepted-clickwrap state
is an explicit existing synthetic fixture in a fresh browser context. Requests
are restricted to its owned same-origin GET/HEAD pages/assets. There is no real
user-cookie/session/credential acquisition, preference mutation, permission
request, tenant/backend authentication claim, pixel/native parity or completion
claim. Original captured materials retain their authorship.

The [frozen qualification](validation/README.md) retains the final same-method
two-width causal failure → pass, the separate first method-setup failure,
24 passing candidate model/shared-source tests, and the later config typecheck
failure/correction with byte-identical TypeScript-erased JavaScript. Actual
browser heads remain separately bound; no replay is relabeled to a newer head.
