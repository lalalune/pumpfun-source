# Recompare retained Pump outcomes before admission

Base: `90300f9d2efe3ef014b116172251a41bfb104d78`. Observed 2026-10-31.

The serial and parallel Pump corpus validators checked each retained `match` or empty difference list, but accepted a receipt whose actual original/candidate fields contradicted that success claim. A real 93-case administrative report was generated with the captured Pump program used on both sides. Changing only candidate error, balance, or account bytes still admitted all 93 cases. Removing the error field from both sides also passed.

The shared admission helper now checks the fields each of the 41 generic suite producers actually promises to compare. Missing fields and unequal outcomes are rejected before a successful aggregate is published. Normalized panic/Anchor messages and event logs are retained when the producer compares them; incidental log lines, diagnostic source coordinates and compute counts remain outside the equality contracts. The three specialized receipt protocols retain their existing gates.

`reproduce.py` executes the real administrative producer, preserves its receipt, and passes independent changed copies to the production parallel validation function. It does not fabricate a build receipt or replace VM execution. Run against a base checkout and the fixed checkout, choosing a fresh evidence directory for each:

```sh
python research/runtime-retained-outcome-comparison-20261031/reproduce.py --repo /path/to/checkout --output /tmp/fresh-receipt-proof
```

Both producer executions produced the identical receipt hash recorded in `results.json`: 93 cases and no differences. Before the fix, all four inconsistent copies were admitted. Afterwards, all four are rejected; the unchanged control and an incidental-diagnostics control remain admitted.

Validation: the existing CI command `python -B tests/test_pump_retained_receipt_contract.py` passes 15 tests, including five new tests using a real producer receipt. Serial retention passes 10 tests, parallel publication passes 8, all 9 evidence captures verify, and the 242-test tooling suite passes. Existing synthetic publication/count fixtures were updated to include the fields their scenarios promise. No binary, retained capture or historical packet was changed. This proof does not claim a fresh execution of the full 44-suite corpus.

All **41 generic producers** were also run with four workers against the captured original on both sides. Every producer exited successfully and all **9,910 cases** passed the new field contracts in 172.685 seconds. `results.json` retains each receipt hash, actual count, elapsed time and admission result. This validates the full changed contract map; it is still not a full 44-suite aggregate build/run. The retained diagnostic driver and receipts are available in the contribution research session.

Review hardening: the direct-field table also requires the producers' nested
return/inner metadata, signed transaction identity, event log payloads and
normalized panic/Anchor diagnostics. Claim-panic receipts must retain exactly
one complete panic and the producer's expected message. Recursive comparison
preserves JSON types, rejecting a boolean replaced with an equal Python integer
or an integer replaced with an equal float. The regression suite generates real
creator, minimum-distribution, fee-sweep, schedule and claim-panic receipts;
changes are receipt-admission controls, not additional successful VM cases.
The historical results above describe the initial contribution; they do not
certify the later hardened consumer.
