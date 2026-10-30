# Exact declared outcomes for an archived runtime cohort

The immutable `pump-multihop-sell-fees-20261029/correspondence.py` checks a
declared numeric error using substring membership. The expected 6063 therefore
also accepts a native-shaped `InstructionErrorCustom(16063)` or
`InstructionErrorCustom(60630)`. Replacing that error in all three roles of the
retained `truncated_fee_config` case, and updating the output receipt and packet
manifest, leaves every existing runtime correspondence check passing. The gate
still returns 16 case triples, 48 verified signatures and zero structured/log
mismatches, despite the incorrect declared error code and unchanged raw log
reporting Error Number 6063.

The current successor lives at
`reconstruction/verification/retained_multihop_outcomes.py`. It source-binds the
unaltered historical checkers and runs the complete existing correspondence,
then requires exact qualified native error values for all three roles of every
case. No regular-expression substring test is used. It also checks the complete
packet manifest and genuine archived candidate-image identities.

## This is archived runtime consistency, not current-source acceptance

The whole historical `verify.py` is not a valid current-main acceptance gate:
both maintained source files have changed, and its external fixture path was
removed. This successor does not run that whole historical verifier or silently
restore those sources. It imports its read-only manifest/decoding utilities and
the original complete runtime correspondence function, with exact source hashes.

An owned temporary filesystem view holds the real captured evidence inputs and
the exact small archived fixture already retained in this packet. The source-
pinned input map and existing correspondence verify all byte joins. Nothing is
restored into the repository; no compiler, producer, LiteSVM, live transaction or
network runs. Deleted experiments and stopped lanes are not resumed.

The JSON result explicitly declares `current_source_acceptance: false`.
The preserved checks still cover the 16 triples, 48 actual signed wires,
source-owned fixture prestates, 48 captured-loader records, all loaded-program
hashes, raw metadata joins, structured parity and ordered non-compute logs,
73 input records and nine output files. This remains finite consistency rather
than independent execution attestation or an independently observed post-state.

## Repeatable evidence

With the pinned root requirements installed, from the repository root:

```
python -I -B -X utf8 reconstruction/verification/retained_multihop_outcomes.py --repo-root .
python -I -B -X utf8 tests/test_retained_multihop_outcomes.py
python -E -B -X utf8 scripts/verify_evidence.py
python -E -B -X utf8 scripts/test_tooling.py
```

The five-test suite executes the real current CLI and the unchanged original
correspondence. Fresh clean evidence passes. Both coherently resealed error-code
mutations pass the original complete correspondence and fail the current CLI at
`exact declared outcome: truncated_fee_config`. A corrupted actual transaction
signature still fails the original signature gate before the new outcome check.
A changed historical checker is rejected before execution by its source binding.
Actual optimized Python subprocesses also call both public verification APIs;
each raises `ValueError` before reading or accepting archived evidence.
All mutations stay in owned temporary packet copies; original files are intact.

Only the runtime cohort is qualified here. No fresh source build, score gain,
whole-program equivalence, new behavioral case or security acceptance is claimed.
The original packet and its source/build/runtime evidence remain byte-identical.
