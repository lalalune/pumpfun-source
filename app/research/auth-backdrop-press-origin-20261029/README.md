# Auth chooser: preserve an aborted button press

On base `604917c16410d67d9b981305e28e160a93728f50`, pressing the existing
**Disconnect and forget address** button and moving outside before releasing
closed the chooser. The button's own action was not activated. Trusted browser
events showed `BUTTON` pointerdown, `DIALOG` pointerup/click, then a closed auth
dialog and an unsubscribed synthetic provider listener. `off` means listener
unsubscribe, not a Wallet Standard disconnect call.

The same native `dialog[closedby=any]` button gesture retained the dialog with
zero button activations. A separate real outside click closed the native
control, proving that light dismissal was supported in this Chromium runtime.
Both desktop and mobile product cases failed after their native controls
passed. The identical two-case driver passes after the correction.

Only AuthControl's pointer-origin guard changes: remember whether pointerdown
began on the backdrop outside the bounds, require an outside release/click,
and clear that state on pointer cancellation and closure. This keeps the
existing outside-click dismissal and prevents an aborted inside press from
being treated as a complete outside click. The approach follows the separate
Settings-only fix in #1490; no shared modal framework is introduced.

`RESULT.json` binds the exact tested source, unchanged child controller/panel,
test files, lockfile and raw receipts. Submission-check main `094a06f1` had the
same app tree as the tested base. The final finite product batch passes **18**
cases: the two target gestures, complete outside dismissal/focus/URL, inside
and reverse gestures, actual Cancel activation/late approval, trusted touch
cancel, and twelve existing auth/public-wallet controls. **Seven** explicit
synthetic-adapter cases are skipped because their test route is not mounted.
The existing 28 Node controller/model tests, frontend typecheck, AST-only
public-wallet witnesses (3 factories/6 fragments), and 698-object app evidence
verification pass. These are finite local results, not original auth or native
wallet compatibility.

The raw before/after JSON reports, trusted event records, full finite-batch
report and test logs are retained here. Before screenshots show the unexpected
closed chooser. Full traces and an earlier falsified CODE text-selection probe
remain private. Text selection generated pointercancel and already worked;
this fix is justified by the actual enabled-button click sequence. An initial
missing-tsconfig setup failure of that earlier probe is retained privately and
is not counted as a product failure. The two button failures include the
runner's expected max-failures stop notice, explicitly recorded in RESULT.

Run the normal affected browser tests from `app/packages/frontend`:

```sh
node node_modules/@playwright/test/cli.js test tests/auth-button-backdrop.spec.ts tests/auth.spec.ts tests/public-wallet.spec.ts
```

That uses the maintained Playwright server configuration on port 3010. The
recorded run instead reused an explicitly assigned Next server on 3027.
`browser-config.ts` preserves that path/port-only test configuration: stage it
as `app/packages/frontend/playwright.auth-button.config.ts`, start Next on
3027, then run `playwright test --config=playwright.auth-button.config.ts`.
The baseline two-case driver is preserved separately as `baseline-driver.ts`;
stage it under its original test filename on the base and select the two
`aborted public disconnect-button press` tests to repeat the failure.
All protocol data is synthetic; HTTP is restricted to same-origin GET/HEAD.
No real wallet extension, credentials, signatures or production calls are used.

```sh
# From app/packages/backend:
node node_modules/tsx/dist/cli.mjs --test ../../tests/auth_interface.test.ts ../../tests/public_wallet.test.ts
# From app/packages/frontend, with Next-generated route types available:
node node_modules/typescript/bin/tsc --noEmit --incremental false
# From app:
node scripts/original-contracts/public-wallet/verify.mjs --check
python3 scripts/verify-evidence.py
# From repository root:
python3 app/research/auth-backdrop-press-origin-20261029/verify.py
```

The packet verifier checks retained results and current source hashes without
replaying browser actions. No auth/controller, public-wallet child focus
(#1361), connect-result handling (#1452), prepaint (#1401), or public overview
(#1350) change is included. Captured protocol witnesses do not establish
original backdrop behavior. Authentication, signing, server compatibility,
other browser engines and visual parity remain unavailable or unqualified.
