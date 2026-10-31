# Reject malformed supplied diagnostic outcomes

At `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`, the diagnostic auditor only examines
rows whose `original` and `candidate` values are both objects. A supplied
non-null string or array in either role makes the whole row disappear from
the audit, even while the other role retains its actual logs. A malformed
receipt can therefore turn a known diagnostic mismatch into a successful
audit of fewer cases.

This follows [PR #2868](https://github.com/lalalune/pumpfun-source/pull/2868),
which checks for a missing log source after both outcome objects exist. Before
that existing check, reject a supplied non-null, non-object counterpart when
the opposite role has a recognized log source. The error names the affected
row and role. Diagnostic extraction, filtering and publication remain unchanged.

The distinction from missing or null outcomes matters. Current producers can
intentionally retain original-only calibration records, and
`pump_extend_differential.py` writes `candidate: null` when no candidate is
supplied. Their existing exclusion remains. Dictionaries without log sources
and cases with both log sources absent or empty also retain their behavior.
This is not a general receipt-schema or complete-case-coverage validator.

## Actual CLI evidence

The probe reads the unchanged 50-case receipt
`research/handler-closure-multihop-mayhem-20261029/receipts/multi_hop_three_curve_cu14.json.gz`,
SHA-256 `1b9212cf8107193430d77f1f48773f172ff94c77fe4cbad985945201ea338a8c`.
The intact report gives 50 log-bearing cases and zero mismatches. A consumer-only
negative control replaces one candidate outcome with another complete genuine
outcome from that receipt, retaining its authentic error payload. It gives 50
cases and one mismatch. It is explicitly not new paired runtime evidence.

Replacing either outcome in that mismatching row with a string or array then
gives exit 0, 49 cases and zero mismatches on the base auditor. The fixed auditor
rejects all four variants before publication, for both plain and gzip inputs.
The 32-scenario probe also checks the intact and genuine-mismatch controls,
existing missing-log rejection, original-only calibration, absent/null outcomes,
unrelated metadata and optional empty/absent logs. All complete and optional
control diagnostics are identical before and after. Inputs remain unchanged and
no staging files remain.

Additionally, exact audit outputs for 41 authentic retained producer receipts
remain identical across 9,906 log-bearing cases. These include the nine
`earned_cashback` and two `legacy_cashback` original-only calibration records.
The corpus measurements describe saved evidence only; no VM is executed.

## Repeat

```sh
python -B research/runtime-diagnostic-pair-admission-20261101/probe.py \
  --repo . --revision 9120883a957d7d9b2cab6140f66fb5bc9e6774d5 \
  --output <fresh-before-directory>
python -B research/runtime-diagnostic-pair-admission-20261101/probe.py \
  --repo . --output <fresh-after-directory>
python -B tests/test_diagnostic_pair_admission.py
python -B scripts/test_pump_diagnostic_audit_coverage.py
python -B scripts/test_pump_diagnostic_audit.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
```

The four new regression methods run the 32 CLI scenarios under normal and
optimized Python. `results.json` records the exact source identities and bounded
before/after results. No historical receipt or captured input is edited, and no
new program behavior, signature coverage or source equivalence is claimed.
