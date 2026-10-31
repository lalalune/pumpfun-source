# Creator-fee recipient credit limits in native models

Base: `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`.

The ordinary native distribution model reports success when a recipient credit
exceeds u64. The companion alias model wraps the balance. Actual signed
`distribute_creator_fees` execution from the retained Pump capture returns the
runtime `ArithmeticOverflow` error instead.

Check each recipient credit after its source debit, in transfer order. The
ordinary model distinguishes runtime ArithmeticOverflow from custom error codes;
the alias model checks its updated per-key balance so repeated recipients and
vault self-transfers retain their behavior. Query-only minimum calculations,
zero credits, debit insufficiency and earlier admission errors are unchanged.

## Repeat

With the repository Python dependencies and host Rust on PATH:

```sh
python3 -B tests/test_creator_distribution_credit_captured.py --probe
python3 -B tests/test_creator_distribution_credit_captured.py
python3 -B tests/test_creator_fee_distribution_captured.py
python3 -B tests/test_distribution_alias_captured.py
```

Run the same probe against base and fixed model sources. It freshly compiles both
native hosts, supplies the same starting inputs to their existing APIs and to
signed LiteSVM transactions, and compares errors, balances, events and return
data. The original image is hash-checked before execution. No live transaction
or deployed program is changed.

The 80-case probe contains 44 ordinary/query cases and 36 alias cases. Before,
9 cases in each family differ; after, all 80 agree. Controls cover credit
boundaries, zero/rounded-zero amounts, repeated and distinct recipients, a vault
self-transfer, read-only recipients, prior invalid-share/account/config errors,
and insufficient source balance. Raw outcomes and source fingerprints are in
`before.json`, `after.json` and `results.json`.

The modified Rust files are host-only recovered models, not part of the SBF
crate. Near-u64 balances here are synthetic local runtime inputs; this makes no
claim about their reachability on a live cluster. This finite correction does
not establish full account admission, token-route coverage, program source
identity, whole-program equivalence or a security finding.
