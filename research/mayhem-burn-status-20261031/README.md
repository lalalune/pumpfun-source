# Mayhem burn-sequence receipt status

`scripts/mayhem_burn_sequence.py` describes "three two-step offline burn
sequences" but never checked that it ran any. At base
`5889e795eba64e85e613b4409921323bfecec414`, a fixture manifest with an empty
`eligible_families` list produced `{"case_count": 0, "mismatches": []}`, wrote
`comparison.json`, and exited 0; a run whose cases differ also printed the
mismatch list and exited 0, because `main()` had no return value.

`results.json` records the empty-manifest run before and after. The fix refuses
a manifest that selects no family before creating the output directory, and ends
with `raise SystemExit(bool(out['mismatches']))`, the same exit convention as
`scripts/mayhem_buy_differential.py:48`.

`tests/test_mayhem_burn_sequence_status.py` drives `main()` in-process with
`run()` stubbed to the smallest receipt row it inspects: no VM executes and no
case is claimed. It covers the empty manifest (refused, no output directory),
matching receipts (exit 0) and differing receipts (exit 1). All three fail on
the base script, which exits normally in each case, and pass in 0.08s on the
proposed script.

The companion `scripts/verify_mayhem_burn_sequence.py` is untouched and still
requires `case_count == 3`; because it pins `runner_sha256`, any previously
generated local receipt for this runner must be regenerated. No receipt is
tracked in the repository, so no committed package is affected.

Required checks on the proposed tree: `python3 -E -X utf8 scripts/test_tooling.py`
(217 pass) and `python3 -E -X utf8 scripts/verify_evidence.py` (nine captures
verified). macOS arm64, Python 3.14.3. No fixture, capture or comparison field
changes; the three-sequence scope claim is unchanged and remains unexercised
here.

## Review qualification

The empty-family regression now invokes the actual CLI with a missing candidate
and checks that refusal occurs before candidate access or output creation. The
two status-branch unit tests still substitute receipt rows; they do not execute
a VM.

An independent review also reran the three historical eligible families from
commit `69a61eec1` using the actual VM entrypoint. A captured-image self-comparison
completed all 12 signed transactions with no mismatches and exit 0. The retained
historical reconstructed candidate completed the same transactions, with only
second-burn source-location log differences in all three cases. This runner now
exits 1 for those raw differences, while `verify_mayhem_burn_sequence.py` still
accepts them under its explicit log-normalization policy. The raw runner status
must not be described as the independent verifier's semantic acceptance status.
The historical inputs were recovered only for review; no old package or binary
is added to the repository by this change.
