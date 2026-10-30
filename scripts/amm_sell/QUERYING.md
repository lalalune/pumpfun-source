## Querying attempt history

The `best` query (also used by `summary`) ranks only the current
`SCORE_VERSION`; its existing eligibility and within-version ordering are retained.
To inspect a known historical metric,
use `attempts.py best --score-version 2`. Unversioned records remain available
through `grep` and `seen` but are not mixed into current rankings. `approaches`
reports its distance minima separately per version. These queries do not rewrite
the ledger, cached results, or the builder's `BEST.json`.

Read-only queries need only Python; the `note` writer retains its existing POSIX
locking requirement. Run the query regressions with
`python -I -B scripts/amm_sell/test_attempt_queries.py`.
