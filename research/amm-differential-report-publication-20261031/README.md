# AMM differential receipts publish atomically

Problem: eight AMM differential runners
(`pump_amm_{boost_burn,cashback,create,creator_reassignment_cto,creator_reassignment,incentives,migration_create,transfer_creator}_differential.py`)
read the captured `pump_amm` image, the captured dependency ELFs, the captured
trade/migration fixtures and the `programs/pump-amm` source tree, then
truncated `--output` with `write_text` as their last step.
`--output evidence/original/pump_amm/deployed.so` destroyed the captured image;
`--output scripts/pump_amm_create_differential.py` replaced the runner with its
own report, so the same run's later import failed. The family's already-admitted
siblings publish through `scripts/pump_differential_output.py: PumpReport`.

Fix: admit the destination with `PumpReport`, built before the first case runs
and before `pin_program` moves the candidate out of the way, with
`AMM_REPORT_INPUTS` (new constant in `pump_amm_reusable_harness.py`) naming the
three captured fixtures and the AMM source tree. `PumpReport` already protects
the captured images, dependency ELFs, candidate, executing script and every
loaded module's source. Publication stages the bytes, fsyncs and replaces, so a
failed write never truncates a prior receipt. Receipt bytes are unchanged.

Reproduction (base revision `52c0b087c`), on a scratch copy:

```
cp -R scripts evidence programs research /tmp/amm-scratch/
python -B /tmp/amm-scratch/scripts/pump_amm_create_differential.py \
  --candidate /tmp/amm-scratch/evidence/original/pump_amm/deployed.so \
  --output /tmp/amm-scratch/evidence/original/pump_amm/deployed.so
# base: exit 0, the captured image is now the report
# proposed: exit 1, ValueError: report output aliases an input
```

## Evidence

- New test `tests/test_amm_differential_report_publication.py`: 32 failing
  subtests in 5 tests at base, 5 tests OK after. Per runner it refuses the
  captured image, the candidate, a captured fixture and the executing script,
  leaving each byte-identical, and still publishes a fresh nested receipt.
- Behaviour unchanged: base and proposed reports are identical once the script
  hashes that necessarily change are ignored (create 246, migration_create 37,
  transfer_creator 267, creator_reassignment 327, cashback 146, boost_burn 506,
  creator_reassignment_cto 159, incentives `sync`; no mismatches).
- `scripts/test_tooling.py` 228 tests OK, `scripts/verify_evidence.py` verifies
  9 captures, `scripts/test_amm_harness_content_cache.py` OK, and the existing
  AMM publication/pinned-candidate suites (14 tests) still pass.

## Limits

The controls prove admission and publication on synthetic local fixtures; they
do not re-run the full AMM differential corpus and make no byte-identity claim
about the rebuilt program. macOS arm64, Python 3.14.3.
