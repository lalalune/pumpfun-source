# Pump v3 and creator-setter receipts publish atomically

Problem: four bounded Pump differential runners
(`pump_create_control_differential.py`, `pump_set_creator_differential.py`,
`pump_v3_configured_fee_differential.py`,
`pump_v3_token_extensions_differential.py`) read the captured Pump image, the
shared Mayhem/Pump Fees images, the captured config snapshot, the signed v3
curve transaction and the dependency ELFs, then truncated `--output` at their
last step. `--output evidence/original/pump/deployed.so` destroyed the
captured image; `--output scripts/pump_set_creator_differential.py` replaced
the runner with its own report, and the same run could no longer import it.
Sibling runners (Pump create/extend, Pump state/migration, the Mayhem
validators and the AMM family) already admit their destination.

Fix: admit the destination with `scripts/pump_differential_output.py:
PumpReport`, built immediately after `parse_args`, before any image is pinned
or a case runs. The create-control runner declares the Mayhem image and the
`token_metadata` dependency ELF; the v3 pair declares
`pump_trade_fixture.REPORT_INPUTS` (the signed v3 curve fixture plus the
pump/pump_fees/dependency captures and ELFs); the creator-setter runner reads
only inputs `PumpReport` already protects. Publication stages the bytes,
fsyncs and replaces, so a failed write never truncates a prior receipt.

Reproduction (base revision `52c0b087c`), on a scratch copy:

```
cp -R scripts evidence research /tmp/pv3-scratch/
python -B /tmp/pv3-scratch/scripts/pump_set_creator_differential.py \
  --candidate /tmp/pv3-scratch/evidence/original/pump/deployed.so \
  --output /tmp/pv3-scratch/evidence/original/pump/deployed.so
# base: exit 0, the captured image is now the receipt
# proposed: exit 1, ValueError: report output aliases an input
```

## Evidence

- New test `tests/test_pump_v3_report_publication.py`: 18 failing subtests in
  6 tests at base, 6 tests OK after.
- Behaviour unchanged once embedded source hashes are ignored
  (`script_sha256`, `provenance`, `harness_sha256`): create_control 85 cases,
  set_creator 509, v3_configured_fee 372, v3_token_extensions 126; no
  mismatches.
- `scripts/test_tooling.py` 228 tests OK, `scripts/verify_evidence.py` verifies
  9 captures.

## Limits

The controls prove admission and publication on synthetic local fixtures; they
do not re-run the full v3 corpora and make no byte-identity claim about the
rebuilt program. The control runs cost ~26s in total (v3_configured_fee
dominates at ~11s). macOS arm64, Python 3.14.3.
