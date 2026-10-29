# Keep Mayhem Retry keyboard focus through an unavailable read

On the maintained `/mayhem` page, Tab from Sort reaches **Retry local adapter**.
Pressing Enter starts the real local GET. The previous loading branch removes
the focused button, so focus falls to `BODY` and stays there when the existing
503 response recreates Retry. The corrected baseline reproduced that failure
with product source unchanged from `630a074126a13d4133514d599129c6ac9a3179bc`.

The fix keeps loading and unavailable content in one section with stable child
positions. Once Retry is shown, it remains mounted during the read. A guarded
`aria-disabled` state prevents repeated activation while preserving keyboard
focus; it does not use native `disabled` or move focus imperatively. If the user
tabs back to Sort while waiting, response completion leaves focus there.

This is a reproduced defect in the maintained reconstruction, not a recovered
original Retry interaction. The existing local API still returns
`503 MAYHEM_DATA_UNAVAILABLE`; no market response, API origin, query, sorting,
auth, data adapter, captured source, SDK or feature ledger changes.

## Actual before and after

| Measurement | Result |
| --- | --- |
| First harness `8849efb800d2561da53ebfc7f8c95361bc0c5e47` | Actual 503; `BUTTON → BODY → BODY`; final focus assertion failed. Its later absolute two-request assumption was never reached. |
| Corrected harness `6b67098b77693aff008e92355984e661162d1e10` | Two initial development request events plus one retry; delta-one assertion passed, then the same focus assertion failed. Product source remained unchanged. |
| Candidate `1d4ea15abe6ca67232edbe67a33888fdfd9e9f83` | **12/12 passed in 23.5s**: the unchanged corrected before/after flow, two new actual 503 busy/no-steal cases and nine retained controls. |

The three new cases continue the actual localhost GET and assert its 503/error
code; they do not fulfill or replace its response. They use keyboard Tab/Enter
and Shift+Tab after initially focusing the native Sort control. The extra
cases assert `aria-disabled`, native `disabled === false`, exactly one retry
despite two more Enter presses, and no focus theft after moving to Sort.
Nonlocal requests and mutation methods are blocked in these new cases.

Some retained controls deliberately use labelled synthetic rows. Their success
does not qualify live market data, native API compatibility, full Mayhem
completion or original visual parity. The new focus story uses Chromium at
1280×800 in development mode; this is not a screen-reader, other-engine or
production-build result.

`VALIDATION.json` binds exact measured commits, source hashes, command and
headless checks. The two negative JSON attachments, both raw failure logs and
before/fixed PNGs are retained here. Full negative traces remain privately
preserved with their hashes recorded. The passing line reporter retained its
explicit screenshot and raw log, but no separate positive focus JSON/trace;
positive focus values are asserted by the passing tests rather than claimed as
an independently retained attachment. All raw logs use deterministic gzip, with
both compressed and decompressed hashes in `MANIFEST.json`.

## Reproduce

With the repository's pinned dependencies already installed:

```sh
cd app/packages/frontend
corepack pnpm exec playwright test --config playwright.mayhem-retry.config.ts
```

This starts the ordinary local Next development server on 3010; it must be free.
Expected: 12 passed. For the focused before case, use a separate checkout of
the base commit, copy this PR's `tests/mayhem-retry.flow.ts`, and copy
`baseline-playwright-config.txt` from this packet to
`app/packages/frontend/playwright.mayhem-retry.config.ts`. Run the same command.
Expected: the final `toBeFocused` assertion fails after an actual 503; the
retry-delta assertion immediately before it passes. This reconstructs the
corrected measured harness; the initial harness is retained as earlier evidence,
not silently relabelled.

Headless checks at the candidate code commit all passed:

```sh
cd app
corepack pnpm test:mayhem
corepack pnpm --filter @pump-reconstruction/frontend typecheck
python3 scripts/verify-evidence.py
corepack pnpm check:progress
cd ..
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

Results: 5 Mayhem model tests, frontend typecheck, 698 captured objects/npm/SDK
integrity, progress consistency plus 9 tests, 9 repository captures and 10 tooling
tests. Later packet-only commits preserve all candidate code and harness bytes;
their exact public tree mapping is recorded separately during publication.

Live overlap review inspected 347 open PRs and main
`604917c16410d67d9b981305e28e160a93728f50`. Its screener component is byte-identical
to the tested base. Related #1307 changes integer validation in the API routes;
#1499 changes a backend per-coin trader board. Neither changes this component.
Competing Explore navigation #1547 remains untouched; our private Explore
candidate is not part of this PR.
