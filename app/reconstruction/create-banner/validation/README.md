# Banner workflow qualification

Runtime/source commit: **e2eb54c388b60ec359accfec7e130d4c6a2efa4a**.
The following receipt-only additions preserve those tested runtime files exactly.

`checks.json` binds the executed inputs, commands/results, artifact byte counts and
SHA-256 hashes. The isolated temporary Playwright config is retained as text;
place it beside `packages/frontend/playwright.config.ts` when repeating, and use
an available serial port. Commands run with the app's pinned pnpm 10.24.0 and
already provisioned dependencies, without installation. No captured code runs.

Before: restore the exact pinned base **form** bytes (`git show ef400863:app/packages/frontend/src/app/create-coin-form.tsx`), leaving new unreferenced modules on disk; run the new keyboard-picker case. The expected failure is the missing Add banner summary. Restore the candidate form before the candidate run. This is an entrypoint-controlled baseline, not a separately rebuilt complete checkout.

After, from `packages/frontend`:

```
CREATE_BANNER_PHASE=candidate-responsive corepack pnpm exec playwright test \
  --config playwright.create-banner.tmp.ts --max-failures=1 \
  tests/create-banner.spec.ts tests/create.spec.ts \
  tests/create-video.spec.ts tests/create-external-links.spec.ts
```

All **25 cases pass**: seven banner cases and 18 retained Create/video/external-link
cases. The new open-panel assertion checks document width at 320/375/390/768/1440;
a non-3:1 actual decoded PNG remains admitted. Keyboard chooser, failed replacements,
main-image/metadata separation, readiness feedback, cancellation, replacement,
reset/unmount URL release and reload are exercised. One pending-decoder test uses
an explicitly synthetic stalled-image port; it is not real-codec success proof.

Focused model/source tests, frontend types, 698-object/npm/31-SDK integrity,
progress plus nine progress tests, and required root nine-capture/ten-tooling
checks pass. Exact source/tree admission is preserved in the root check record
referenced by the PR. Full production/workspace/browser checks are not claimed.

The before screenshot and local after screenshots are actual browser outputs.
They are not original-production reference comparisons. Full-page captures retain
the shared fixed navigation's placement; no whole-page occlusion or pixel-parity
claim is made. Raw failed/intermediate runs are retained privately, with their
honest counts and corrections recorded in `checks.json`. They are not relabelled
as final passes.

No banners enter token metadata or SDK parameters. No file is resized, persisted,
uploaded or published. There is no URI, wallet connection, signing, RPC or launch.

Raw logs are losslessly gzip-compressed, preserving terminal whitespace. For example, `gzip -dc browser-final.log.gz` displays the unmodified final browser log; both compressed and decoded hashes are bound by the receipt.
