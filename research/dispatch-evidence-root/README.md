# Proposed dispatch evidence-root asset transition

`scripts/recover_dispatch.py` now passes the caller's evidence root to
`program_names(root)`. Partial evidence checkouts and their archived selectors
previously selected programs from the tool's own checkout instead.

`transition.json` proposes this single script change for maintainer review under
`scripts/README.md`'s frozen-set convention. It binds the exact base and changed
script, the unchanged direct Python script-name set (275 files), and the retained
Fees/AMM capture bytes. Historical packages and their source pins remain intact.

The verifier reads the base commit from Git. In a shallow checkout, first run
`git fetch origin abfda9f14a99e03785e57afbb1e4018b1785219f`.
Run `python -I -B research/dispatch-evidence-root/verify.py`, then
`python -I -B tests/test_dispatch_root.py`. This checks the proposed asset
transition and local dispatch behavior; it establishes no checkpoint acceptance,
reconstruction equivalence, source-build provenance or security clearance.
