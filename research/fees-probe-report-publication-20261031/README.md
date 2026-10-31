# Pump Fees probe receipts publish atomically

Problem: two bounded Pump Fees runners — `fees_donation_crank_probe.py` and
`validate_fee_handlers.py` — read the captured Pump Fees image, the donation
relay and SPL dependency ELFs, the shared AMM fixture and the saved
fee-selector receipts, then truncated `--output` with `write_text` at their
last step. `--output research/imported-lab/analysis/pump_fun/
amm-v2-trade-fixture.json` destroyed a tracked fixture;
`--output scripts/fees_donation_crank_probe.py` replaced the runner with its
own report, and the same run could no longer import it. Sibling Fees runners
(`fees_admin_differential.py`, `fees_config_differential.py`,
`fees_validate_all.py`, the eight fees differentials) already admit their
destination.

Fix: admit the destination with `scripts/pump_differential_output.py:
PumpReport`, built immediately after `parse_args`. The crank probe declares
the donation relay ELF and the shared AMM fixture; `validate_fee_handlers.py`
declares the two saved selector receipts. Publication stages the bytes,
fsyncs and replaces, so a failed write never truncates a prior receipt.
Receipt bytes are unchanged — no script hash is embedded.

Reproduction (base revision `52c0b087c`), on a scratch copy:

```
cp -R scripts evidence research /tmp/fprobe-scratch/
python -B /tmp/fprobe-scratch/scripts/fees_donation_crank_probe.py \
  --candidate /tmp/fprobe-scratch/evidence/original/pump_fees/deployed.so \
  --output /tmp/fprobe-scratch/research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json
# base: exit 0, the tracked fixture is now the receipt
# proposed: exit 1, ValueError: report output aliases an input
```

## Evidence

- New test `tests/test_fees_probe_report_publication.py`: 9 failing subtests
  in 6 tests at base, 6 tests OK after.
- Behaviour unchanged: base and proposed receipts are byte-identical —
  crank probe 357 cases, validate_fee_handlers 10838 cases; no mismatches.
- `scripts/test_tooling.py` 228 tests OK, `scripts/verify_evidence.py` verifies
  9 captures.

## Limits

The controls prove admission and publication on synthetic local fixtures; they
do not re-run the full probe corpora and make no byte-identity claim about the
rebuilt program. The control runs cost ~4s in total. macOS arm64, Python
3.14.3.
