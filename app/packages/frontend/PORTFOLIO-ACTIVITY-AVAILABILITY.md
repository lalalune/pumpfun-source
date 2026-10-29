# Public activity inspection without a successful balance read

A valid public address with an unsupported token-account response previously lost
the **Read public Pump record** control. The panel was nested inside
`PortfolioResult`, which only renders after every holdings read succeeds. The
existing record reader only needs the public address, `getGenesisHash`, and
`getAccountInfo`; successful SOL/SPL/Token-2022 balances are not its prerequisite.

The panel now renders below the holdings status for a canonical committed URL
address. The existing pure address validator rejects empty and malformed inputs.
The target is displayed explicitly; editing an unsubmitted draft does not retarget
it. The address/refresh key resets the existing panel and aborts its pending work
on refresh or navigation. Reads remain explicit. The holdings controller, form,
page key, API, SDK, record reader and record controller are unchanged.

This is a correctness fix to the documented reconstruction. The existing SDK
evidence at `app/research/wallet-program-record-20261029/SOURCE.json` remains prior
work. The pending-draft/navigation behavior in open PR #1349 is a separate scope;
this patch does not change its sites. No original server implementation, current
rewards, eligibility, ownership, authentication, positions or signing is inferred.

## Before and after

Base product: `04be15f61e66d27282e2af3d581de984389eac90`.
The corrected test-only baseline `8d97e6bc1090610e1cb1032dae7e70509a25d240`
reaches the documented holdings error, confirms zero automatic record reads,
then fails because the record button is absent. The earlier broad `role=alert`
selector instead matched Next's route announcer as well as the error; that setup
failure is retained separately and is not the defect proof.

Product fix: `d2d372d0f25f669f7ddfc3dd65de22faf0335cc3`.
Test-only follow-up: `db13adf08eae30fd57854b651c963b9e4c1bf2fe`.
The first candidate batch passes six new cases, then fails on an over-specific
total holdings-request count: the trace includes an initial aborted request, its
replacement, and the explicit retry. The test now measures exactly one request
added by Retry. The product code did not change. Only that failed case and the
fourteen unrun cases were resumed: 14 pass, one existing guard skips. Across both
runs, **20 unique cases pass and one explicitly skips**, out of 21 discovered.

The seven new cases cover pending/failed holdings, empty/invalid addresses,
committed address versus draft, navigation and late completion, and refresh
invalidation without automatic record reads. Six existing Portfolio cases and
seven runnable record cases also pass. The existing SDK-loaded route guard needs
its separate no-RPC test flag and is skipped here; these controlled-response
browser cases do not establish configured production/mainnet success.

Additional checks: frontend TypeScript; 11 existing address/response/record checks
(including the real local HTTP handler/SDK-reader flow); application evidence
(698 objects, npm integrity, unchanged SDK sources); progress plus nine tests;
and the root nine-capture/ten-tooling checks. The first Node attempt lacked a
sparse-excluded tracked evidence JSON. Its exact HEAD bytes were restored before
the passing rerun. No evidence was regenerated or acceptance rule changed.

From `app/`, using the pinned pnpm 10.24 workspace:

```sh
pnpm --filter @pump-reconstruction/frontend exec playwright test --config playwright.portfolio-activity.config.ts --max-failures=1
pnpm --filter @pump-reconstruction/frontend typecheck
node --test tests/wallet_program_record.test.mjs tests/portfolio_response_boundary.test.mjs tests/portfolio-address-boundary.test.mjs
python3 scripts/verify-evidence.py
pnpm check:progress
```

The isolated browser config uses port 3010 and an empty `SOLANA_RPC_URL`. It does
not install a test route or change production configuration. No live wallet,
private key, external balance response or transaction is used.

[`visual/portfolio-activity-20261029`](visual/portfolio-activity-20261029) contains
compressed complete logs, failure contexts, explicitly partial call excerpts with
full private-trace hashes, before/after screenshots, tested source bindings and a
SHA-256 manifest. The desktop screenshots are 1280 pixels wide; the mobile
after-image is 320 pixels wide. No full application suite, production build,
upstream visual equivalence or feature milestone increase is claimed here.
