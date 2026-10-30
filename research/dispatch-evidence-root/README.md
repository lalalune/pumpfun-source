# Proposed dispatch evidence-root asset transition

`scripts/recover_dispatch.py` now passes the caller's evidence root to
`program_names(root)`. Partial evidence checkouts and their archived selectors
previously selected programs from the tool's own checkout instead.

`transition.json` proposed this single script change for maintainer review under
`scripts/README.md`'s frozen-set convention. It binds the exact base and changed
script, the unchanged direct Python script-name set (275 files), and the retained
Fees/AMM capture bytes. Historical packages and their source pins remain intact.

The change landed in #2173 as `1526951b5497ab5d035941bdd2c1286b0b281e17`
(`landedRevision`). The verifier checks only Git history, not the working tree:
the base binds the proposal as above; the landed commit's parent holds the
before script, the landed commit holds the after script, `recover_dispatch.py`
is the only direct `scripts/*.py` file it changes, its direct script-name set
equals its parent's, and the Fees/AMM captures are unchanged. Later edits to
`scripts/` therefore do not invalidate this record.

In a shallow checkout, first run
`git fetch origin abfda9f14a99e03785e57afbb1e4018b1785219f 1526951b5497ab5d035941bdd2c1286b0b281e17 105fa5b17000189da759ac5215fe3fa7b751a861`
(base, landed commit and its parent).
Run `python -I -B research/dispatch-evidence-root/verify.py`, then
`python -I -B tests/test_dispatch_root.py`. This checks the proposed asset
transition and local dispatch behavior; it establishes no checkpoint acceptance,
reconstruction equivalence, source-build provenance or security clearance.
