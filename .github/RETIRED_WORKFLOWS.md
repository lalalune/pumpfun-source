# Retired research verification workflows

The following workflows were removed because every verifier they invoke is absent
from the maintained tree. They ran on every push and pull request and failed with
Python exit code 2 before performing any verification.

| Workflow | Removed research packages |
| --- | --- |
| Verify independent AMM event replay | `research/amm-event-capture-independent-replay`, `research/amm-current-event-capture-20261027` |
| Verify AMM pool preparation boundaries | `research/amm-pool-preparation-boundaries` |
| Verify Pump AMM migration composition | `research/pump-amm-migration-composition` |

The workflow definitions are preserved in Git history at base commit
`665499915f9caedcd38921d415a90f0606686398`. No evidence or verifier is deleted
by this change. Removing these jobs does **not** establish that event replay,
pool boundaries, or migration composition passes. Those checks are unavailable
until their complete, authenticated packages and dependencies are restored or
replaced by maintained verification with equivalent coverage.

Observed failed runs on the fork at `92b5f5802272d390ddf743bf3364802a7f9920a7`:

- [Event replay](https://github.com/Oz-0s/pumpfun-source/actions/runs/40903218269)
- [Pool preparation](https://github.com/Oz-0s/pumpfun-source/actions/runs/40903218643)
- [Migration composition](https://github.com/Oz-0s/pumpfun-source/actions/runs/40903218484)

The retained root checks can still be run independently:

```sh
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

These check retained capture integrity and tooling; they are not substitutes for
the retired runtime suites. The separate `verify.yml` historical matrix also
references removed research/repro inputs and needs its own audit. This change
does not claim that the entire repository CI is green. Maintained targeted
workflows are unchanged; no failure is converted into a successful or skipped
verification result.
