# Preserve the next GO search draft after a delayed submit

The maintained GO archive accepts a search, then synchronizes the input when
the URL query commits. Before this fix, that synchronization overwrote text
typed after submitting but before the actual RSC response arrived. The same
component already protects drafts typed after Reset; normal submissions had no
corresponding ownership record.

On unchanged main `604917c16410d67d9b981305e28e160a93728f50`, submit
`  Follow  `, hold the genuine localhost `/go?q=Follow&_rsc=…` GET, and type
`next archive draft`. Continuing the unchanged response commits `q=Follow` and
causes the actual local archive GET to return 200. The input incorrectly becomes
`Follow`. Both 1280px and 375px measurements fail at that final draft assertion;
the earlier navigation and archive-status assertions pass.

The fix records the submitted raw draft and normalized query. On that matching
own-query commit, a functional state update preserves a newer input value. An
unchanged draft still normalizes to the committed query. Reset and real
`popstate` clear the submission record so URL/history synchronization retains
its existing meaning. The correction changes no query builder, cursor, filter,
sort, task positioning, archive loader, API response or data.

## Actual measurements

| Revision | Result |
| --- | --- |
| Baseline harness `536911f27939640ad6f1dfe81c4bbcff42bcf7bb` | **2 failed**: pending draft `next archive draft` became `Follow` after real RSC commit and actual archive 200, at 1280px and 375px. Product source identical to main. |
| Candidate code `891add9f5488083c0a4d6dd8df0d8b77b1be2072` | **14 passed in 36.7s**: the byte-identical two-width before/after flow, one normalization/history control, and eleven unchanged GO cases. |

The two target cases block nonlocal requests and mutation methods, hold only
the actual RSC GET, then call `route.continue()`. They never fulfill a request
or substitute a body. They independently await and assert the real
`/api/go-bounties?q=Follow` 200 and wait until the read settles before recording
the input. The four before/fixed JSON records retain actual URLs, drafts,
status and empty forbidden-request lists. Desktop before/fixed PNGs are also
retained; private full negative traces remain hash-bound in `VALIDATION.json`.

The additional control proves a changed submitted query still trims unchanged
input, and unsent text gives way to genuine Back/Forward URL state and reload.
Retained controls cover search/refresh/history, filters/sorting/cursors,
validation, failure/malformed data, stale responses, details/Escape/focus,
viewports, navigation boundaries, pending selections and delayed Reset.
Some retained controls intentionally replace error/malformed responses; those
are distinct from the new genuine-response cases.

The raw candidate log includes a shared SearchDialog hydration diagnostic
during query/history activity. This component and its dependencies are
unchanged here, and the existing shared-hydration work remains separate. All
14 selected tests pass, but this packet makes no whole-app console-clean claim.

## Source and data boundary

This fixes a reproduced defect in the reconstruction's mounted archive UI;
it does not claim a captured original interaction or a live GO service. The
existing verifier reads the first-party `/go` capture as data and extracts its
25 direct archived bounties. Its object remains unchanged:

`app/evidence/web/objects/e66810e11f481135`, 1030034 bytes,
SHA-256 `8037ac8c628063897531326090f1a4d3cbf8ed0051f4f6e9f88c821f4fee9ece`.

No captured JavaScript is evaluated. No source capture, SDK, authentication,
wallet, submissions, funding, payout, backend, dependency, feature ledger or
compatibility/milestone count changes. Original visual/interaction parity,
other engines, screen readers and a production build are unqualified here.

Live ownership review excluded clipboard #1255, Explore #1547 and tabs #1328.
Related GO #1344 changes cursor validation (its component edits are at the
cursor helper/read), and #1469 changes task positioning in `go-data.ts`. This
PR preserves those separate concerns and changes only normal-submit draft
ownership in `go-explorer.tsx`.

## Reproduce

With pinned dependencies available and port 3010 free:

```sh
cd app/packages/frontend
corepack pnpm exec playwright test --config playwright.go-submit.config.ts
```

Expected: 14 passed. To reproduce the baseline, use a separate checkout of the
base commit, copy this PR's `tests/go-pending-submit.flow.ts`, and copy this
packet's `baseline-playwright-config.txt` to
`app/packages/frontend/playwright.go-submit.config.ts`. Run the same command.
Expected: 2 final draft assertions fail, after actual archive 200 responses.
The current flow is byte-identical to the measured baseline flow; only the
candidate config's test selection expands. Next command/environment/origin are
unchanged. Full private baseline traces are preserved, not overwritten.

Headless checks at the frozen candidate passed:

```sh
cd app
corepack pnpm test:go
corepack pnpm --filter @pump-reconstruction/frontend typecheck
python3 scripts/verify-evidence.py
corepack pnpm check:progress
cd ..
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

Results: 8 GO model tests, frontend typecheck, 698 captured objects/npm/unchanged
SDK sources, progress consistency plus 9 tests, 9 root captures and 10 tooling
tests. `VALIDATION.json` pins source and measured commits; `MANIFEST.json`
authenticates all packet bytes and both compressed/raw log hashes. Later
packet-only commits preserve the measured source/harness. Publication records
the exact tested-local/public Git tree mapping separately.
