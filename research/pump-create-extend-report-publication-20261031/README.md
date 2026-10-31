# Pump create/extend receipts publish atomically

Problem: four Pump create/extend differential runners
(`pump_create_quote_differential.py`, `pump_create_v2_differential.py`,
`pump_create_mayhem_differential.py`, `pump_extend_differential.py`) read the
captured Pump and Mayhem images, the captured config snapshot and the
dependency ELFs, then truncated `--output` with `write_bytes` at their last
step. `--output evidence/original/pump/deployed.so` destroyed the captured
image; `--output scripts/pump_extend_differential.py` replaced the runner with
its own report. Their admitted siblings `pump_create_differential.py` and
`pump_global_init_differential.py` already publish through
`scripts/pump_differential_output.py: PumpReport`.

Fix: admit the destination with `PumpReport`, built before the first case and
before `pin_program`, declaring `evidence/original/mayhem/deployed.so` for the
three create runners (and both `--candidate-pump` / `--candidate-mayhem` paths
for `create_mayhem`). Publication stages the bytes, fsyncs and replaces, so a
failed write never truncates a prior receipt. Receipt bytes are unchanged: the
same indented JSON gzipped with `mtime=0`.

Reproduction (base revision `52c0b087c`), on a scratch copy:

```
cp -R scripts evidence research /tmp/pce-scratch/
python -B /tmp/pce-scratch/scripts/pump_extend_differential.py \
  --candidate /tmp/pce-scratch/evidence/original/pump/deployed.so \
  --output /tmp/pce-scratch/evidence/original/pump/deployed.so
# base: exit 0, the captured image is now the gzip receipt
# proposed: exit 1, ValueError: report output aliases an input
```

## Evidence

- New test `tests/test_pump_create_extend_report_publication.py`: 15 failing
  subtests in 4 of 5 tests at base, 5 tests OK after.
- Behaviour unchanged: base and proposed gzip receipts are identical once
  `script_sha256` is ignored — create_quote 297 cases, create_v2 110, extend
  308, create_mayhem 17; no mismatches.
- `scripts/test_tooling.py` 228 tests OK, `scripts/verify_evidence.py` verifies
  9 captures. The three output-parent suites report 9 tests OK plus the same 2
  `setUpClass` errors the base revision produces (missing local build inputs).

## Limits

The controls prove admission and publication on synthetic local fixtures; they
do not re-run every corpus case against every candidate class and make no
byte-identity claim about the rebuilt program. macOS arm64, Python 3.14.3.
