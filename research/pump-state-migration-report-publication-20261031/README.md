# Pump state and migration receipts publish atomically

Problem: six bounded Pump differential runners
(`pump_holder_distribution_differential.py`, `pump_idl_authority_differential.py`,
`pump_incentives_admin_differential.py`, `pump_volume_sync_differential.py`,
`pump_migrate_differential.py`, `pump_migrate_v2_differential.py`) read the
captured Pump/AMM images, the captured config snapshot, the saved migration
transaction and the dependency ELFs, then truncated `--output` with
`write_bytes` at their last step. `--output evidence/original/pump/deployed.so`
destroyed the captured image; `--output scripts/pump_migrate_differential.py`
replaced the runner with its own report. Sibling runners
(`pump_minimum_fee_differential.py`, `pump_create_differential.py`,
`pump_claim_panic_differential.py`, the AMM family) already admit their
destination.

Fix: admit the destination with `scripts/pump_differential_output.py:
PumpReport`, built before the first case runs. The migration pair declares the
saved transaction its probe replays
(`research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json`)
as an extra input; the other four read only inputs `PumpReport` already
protects. Publication stages the bytes, fsyncs and replaces, so a failed write
never truncates a prior receipt. Receipt bytes are unchanged.

Reproduction (base revision `52c0b087c`), on a scratch copy:

```
cp -R scripts evidence research /tmp/psm-scratch/
python -B /tmp/psm-scratch/scripts/pump_volume_sync_differential.py \
  --candidate /tmp/psm-scratch/evidence/original/pump/deployed.so \
  --output /tmp/psm-scratch/evidence/original/pump/deployed.so
# base: exit 0, the captured image is now the receipt
# proposed: exit 1, ValueError: report output aliases an input
```

## Evidence

- New test `tests/test_pump_state_report_publication.py`: 20 failing subtests
  in 5 tests at base, 5 tests OK after.
- Behaviour unchanged: base and proposed receipts are identical once
  `script_sha256` is ignored — holder_distribution 649 cases, idl_authority
  171, incentives_admin 299, volume_sync 341, migrate 228, migrate_v2 827; no
  mismatches.
- `scripts/test_tooling.py` 228 tests OK, `scripts/verify_evidence.py` verifies
  9 captures.

## Limits

The controls prove admission and publication on synthetic local fixtures; they
do not re-run the full state/migration corpora and make no byte-identity claim
about the rebuilt program. The control runs cost ~68s in total (migrate_v2
dominates at ~29s). macOS arm64, Python 3.14.3.
