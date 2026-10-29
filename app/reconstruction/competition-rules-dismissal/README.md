# Competition Rules outside-press dismissal

The existing native Rules dialog traps focus and closes through Escape/Close,
but an ordinary complete press on its backdrop leaves it open. The captured
Rules controller enables outside dismissal through the actual responsive-dialog
default. This fix adds `closedby="any"` to this caller's existing native dialog.
It uses the browser's light-dismiss behavior, preserving native pointer-origin
checks, cancellation, focus return and the existing scroll-lock cleanup.

The source-only verifier binds the complete retained `590407` Rules controller
and its actual `439587.v/s` call. The named `396623.Root` re-export reaches
`524684.DrawerRoot`, which defaults `disablePointerDismissal=false` and forwards
it to the actual `660315.Root` in that same physical factory. The used backdrop
attaches the store ref. The actual outside-press predicate excludes non-left
presses, and its `385676.f` hook selects intentional click dismissal and guards
inside-start/outside-release. All witness hashes/ranges/origin contexts are in
`contract.json`; captured bundles/factories are never evaluated.

Existing source-reader/comparator infrastructure is reused unchanged. Credit
PR #1717 for the generic named-re-export/optional-registration graph diagnostics
and #1665 for the separate Search caller's native light-dismiss evidence. This
unit independently binds the competition Rules caller and actual propagation;
it does not copy or alter either generic/Search unit or claim their recovery.

This is a local browser mapping of the observed dismissal policy. It does not
reconstruct BaseUI Drawer/FloatingUI, unknown providers, swipe, nested-modal or
all touch-device behavior. Browser support for native dialog light dismissal
is required for this outside-click action; existing Escape/Close remain. No
rules copy, financial/eligibility logic, data adapter, backend, auth, key gate,
fixtures/captures or global ledger changes are made to implement the fix.

From `app`:

```sh
node scripts/verify-competition-rules-dismissal.mjs --check
node --experimental-strip-types --test tests/competition-rules-dismissal.test.mjs tests/competition-rules.test.mjs tests/original_source.test.mjs
pnpm -r typecheck
python3 scripts/verify-evidence.py
# Reserve a Next slot; fixtures own and close Next + loopback Fastify:
PUMP_RULES_PORT=3027 PUMP_RULES_PHASE=fixed node packages/frontend/node_modules/@playwright/test/cli.js test --config tests/browser/rules-dismiss.playwright.config.mts
```

The frozen browser method uses the existing native competition handler and
checked-in synthetic `solana-autumn-arena` seed through actual Next HTTP, with
the ordinary key gate active. It never fulfills JSON. The child environment
constructs a public synthetic key from a fixed prefix and `"A".repeat(49)` and
reads no parent credential. Success is bounded local functionality, not original
API/provider/visual parity or milestone completion. Exact before/after revision
bindings and raw observations are retained in the separate qualification packet.
