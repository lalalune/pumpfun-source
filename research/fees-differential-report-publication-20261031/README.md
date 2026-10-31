# Pump Fees receipts publish atomically

Problem: eight bounded Pump Fees differential runners
(`fees_donation_create_differential.py`, `fees_deprecated_differential.py`,
`fees_error_messages_differential.py`, `fees_sharing_create_differential.py`,
`fees_external_codec_differential.py`, `fees_social_claim_differential.py`,
`fees_initialize_differential.py`, `fees_sharing_update_differential.py`) read
the captured Pump Fees image, the shared Pump/AMM images, the captured config
snapshot and the dependency ELFs, then truncated `--output` with `write_text`
at their last step. `--output evidence/original/pump_fees/deployed.so`
destroyed the captured image; `--output scripts/fees_deprecated_differential.py`
replaced the runner with its own report, and the same run could no longer
import its own module. Sibling Fees runners (`fees_admin_differential.py`,
`fees_admin_transfer_differential.py`, `fees_config_differential.py`,
`fees_extend_differential.py`, `fees_upsert_differential.py`,
`fees_buyback_differential.py`, `fees_social_create_differential.py`) already
admit their destination.

Fix: admit the destination with `scripts/pump_differential_output.py:
PumpReport`, built immediately after `parse_args`, before any image is pinned
or a case runs. The eight runners read only inputs `PumpReport` already
protects; `fees_error_messages_differential.py` additionally declares its
optional `--baseline` image as an extra input. Publication stages the bytes,
fsyncs and replaces, so a failed write never truncates a prior receipt.
Receipt bytes are unchanged — no script hash is embedded.

Reproduction (base revision `52c0b087c`), on a scratch copy:

```
cp -R scripts evidence research /tmp/fees-scratch/
python -B /tmp/fees-scratch/scripts/fees_deprecated_differential.py \
  --candidate /tmp/fees-scratch/evidence/original/pump_fees/deployed.so \
  --output /tmp/fees-scratch/evidence/original/pump_fees/deployed.so
# base: exit 0, the captured image is now the receipt
# proposed: exit 1, ValueError: report output aliases an input
```

## Evidence

- New test `tests/test_fees_differential_report_publication.py`: 32 failing
  subtests in 5 tests at base, 5 tests OK after.
- Behaviour unchanged: base and proposed receipts are byte-identical —
  donation_create 356 cases, deprecated 80, error_messages 2, sharing_create
  116, external_codec 9, social_claim 347, initialize 180, sharing_update 417;
  no mismatches.
- `scripts/test_tooling.py` 228 tests OK, `scripts/verify_evidence.py` verifies
  9 captures.

## Limits

The controls prove admission and publication on synthetic local fixtures; they
do not re-run the full Fees corpora and make no byte-identity claim about the
rebuilt program. The control runs cost ~20s in total (sharing_update dominates
at ~13s). macOS arm64, Python 3.14.3.
