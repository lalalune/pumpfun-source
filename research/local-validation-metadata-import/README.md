# Proposed asset transition: keep capture metadata independent of VM imports

`scripts/test_tooling.py` imports `local_validation` to check captured-program
address selection. That helper uses only pathlib/JSON, but import-time LiteSVM
loading makes this metadata workflow fail before executing any test when the
native VM dependency is unavailable. On Windows the pinned solders 0.27.1 wheel
is installed but lacks the `FeatureSet` export required by `solders.litesvm`.

Move all six runtime imports into `main()`, before any VM work or output. The
actual smoke-test entry point still requires the real dependencies and fails
when unavailable. Do not substitute a VM, skip runtime validation or change the
program-address selection, transactions, evidence or matching rules.

The new subprocess regression runs with `-I -S`, reads all four actual retained
capture receipts and verifies their selected addresses without site packages.
Before: one failure and one passing negative control. After: both pass, also
under `python -O`. Calling `main()` without solders remains a hard failure.

The required tooling suite now executes 40 tests; its independent interface-root
regression still raises three errors, already addressed by separate PR #2102.
No passing full suite is claimed. All nine capture integrity checks pass.

This is a proposed one-script asset transition under current on-chain tooling
scope. `transition.json` binds base and proposed source bytes. No script is
added/removed, immutable checkpoint re-sealed, or original capture changed.
No compiler, VM execution, new byte match or security acceptance is established.
