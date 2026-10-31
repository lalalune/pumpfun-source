# Fees aggregate: bind retained outcomes

At base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`, `fees_validate_all.py` accepts a row's `match: true` or empty difference list without checking the retained semantic outcomes. In a real producer receipt, `set_authority-0` rejects with error 6001 and `set_authority-1` succeeds. Replacing the first row's candidate outcome with the independently executed second outcome, while retaining its original flags, makes the base aggregate CLI publish `mismatches: []` despite original error 6001 versus candidate success.

The fix applies each of the 18 producers' comparison contracts to their retained payloads before publishing. It preserves their excluded raw log/compute fields. Donation crank, social creation and buyback compare only the event log lines that those producers compare. Existing count, summary-failure, output preservation and image checks remain in place. This completes the intended row checks introduced in [PR 3239](https://github.com/lalalune/pumpfun-source/pull/3239).

A fresh unmodified aggregate invocation executed all 18 actual SBF suites against the captured Fees image: 17,331 cases, exit 0, no mismatches. Its 99,064,962 raw bytes were losslessly compressed for external session retention; raw/compressed hashes and per-suite counts are in `provenance.json`. The public `bounded-receipts.json.gz` contains the first two authentic cases per suite (36 total), with outcomes unchanged. This is a bounded extract, not a new runtime execution or whole-handler coverage claim.

Both the full corpus and bounded extract were then replayed through the exact aggregate CLI. Small child adapters only return these retained receipts; they do not simulate or claim SBF execution. The unchanged control passes on base and fix. The incompatible genuine administrative outcome is accepted and published by base; the fix rejects it before replacing the prior aggregate. No outcome is fabricated for this reproduction.

Reproduce the bounded before/after consumer workflow with new output names:

```sh
python -B research/runtime-fees-retained-outcomes-20261101/replay.py --repo . --corpus research/runtime-fees-retained-outcomes-20261101/bounded-receipts.json.gz --revision 9120883a957d7d9b2cab6140f66fb5bc9e6774d5 --output /tmp/fees-before.json
python -B research/runtime-fees-retained-outcomes-20261101/replay.py --repo . --corpus research/runtime-fees-retained-outcomes-20261101/bounded-receipts.json.gz --output /tmp/fees-after.json
python -B tests/test_fees_retained_outcomes.py
```

To regenerate a full authentic runtime corpus, run the real producer and then supply that output to the same replay script:

```sh
python -B scripts/fees_validate_all.py --candidate evidence/original/pump_fees/deployed.so --output /tmp/fees-fresh.json
python -B research/runtime-fees-retained-outcomes-20261101/replay.py --repo . --corpus /tmp/fees-fresh.json --output /tmp/fees-fresh-replay.json
```

Validation: four new methods (including actual CLI replay and all 112 declared semantic fields), five existing receipt-integrity methods, 13 output/timeout/frozen-checkout/image-pinning methods, three optimized-mode checks, 250 tooling tests and nine capture seals pass. Existing bookkeeping fixtures now retain authentic matching outcome rows so their publication tests still reach publication. Their file-size limit admits each child receipt and continues to fail only at aggregate publication.

Scope: consumer admission of contradictory retained evidence. Deliberate receipt corruption is distinguished from a spontaneous producer failure. Hashes identify the retained corpus; this is not cryptographic receipt authentication, candidate equivalence, production build evidence, or an on-chain finding. Original captures and historical packets are unchanged.
