# Mayhem validator receipts publish atomically

Problem: the six Mayhem validators (`mayhem_validate_admin`,
`_fee_recipient`, `_quote_withdraw`, `_sweeps`, `_extend`, `_withdraw`) read
the captured Mayhem image, the captured dependency ELFs and the program sources
they hash into the receipt, then truncated `--output` with `write_text` as their
last step. `--output evidence/original/mayhem/deployed.so` destroyed the
captured image; `--output scripts/mayhem_validate_admin.py` replaced the module
with its own report, so the same run's later import raised `NameError: name
'null' is not defined`.

Fix: admit the destination with the same publisher the Pump runners use,
`scripts/pump_differential_output.py: PumpReport`, built before the first case
runs and declared with the Mayhem inputs (`REPORT_INPUTS`: the captured image
and `programs/mayhem/{Cargo.toml,Cargo.lock,src/lib.rs}`). `PumpReport` also
protects the candidate, the executing script, every loaded module's source and
the captured dependency ELFs. Publication stages the bytes, fsyncs and replaces,
so a failure never truncates a prior receipt. Receipt bytes are unchanged: the
same UTF-8, compact-separator JSON with one trailing newline.

Reproduction (base revision `52c0b087c`), on a scratch copy so nothing real is
lost:

```
cp -R evidence programs scripts /tmp/mayhem-scratch/   # keep the real captures
python -B /tmp/mayhem-scratch/scripts/mayhem_validate_extend.py \
  --candidate /tmp/mayhem-scratch/evidence/original/mayhem/deployed.so \
  --output /tmp/mayhem-scratch/evidence/original/mayhem/deployed.so
# base: exit 0, the captured image is now the report
# proposed: exit 1, ValueError: report output aliases an input
```

## Evidence

- New test `tests/test_mayhem_validate_report_publication.py`: 24 failing
  subtests in 5 tests at base, 5 tests OK after.
- Behaviour unchanged: base and proposed scripts produce an identical `cases`
  array for the same candidate (admin 1051, fee_recipient 306, quote_withdraw
  329, sweeps 692, extend 301, withdraw 274; no mismatches).
- `scripts/test_tooling.py` OK, `scripts/verify_evidence.py` verifies 9
  captures.

## Limits

The controls prove admission and publication on synthetic local fixtures; they
do not re-run the full Mayhem validation corpus and make no byte-identity claim
about the rebuilt program.

`scripts/test_mayhem_report_encoding.py` already fails on the base revision
(its threshold counts pinned `write_text` calls); PR #3165 makes that guard
recognise the admitted publication shape. macOS arm64, Python 3.14.3.
