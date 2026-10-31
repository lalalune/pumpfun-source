# Buyback recipient differential: fresh output admission

## Defect

`scripts/pump_buyback_recipient_differential.py` guards its destination with
`assert not args.output.exists()`. `Path.exists()` follows symlinks, so a
dangling symlink at `--output` is "not there", and the later
`args.output.write_text(...)` then follows the link. The receipt is published at
the link target, the requested path stays a dangling link, and the run exits 0 —
the "fresh output path" rule never applied to the file that was written.

Reproduced on `52c0b087c` with the captured original as both binaries:

```
ln -s "$tmp/escape dir/escaped-report.json" "$tmp/report.json"
python -B scripts/pump_buyback_recipient_differential.py \
  --candidate evidence/original/pump/deployed.so --output "$tmp/report.json"
# exit 0, {"cases": 42, "mismatches": []}
# "$tmp/escape dir/escaped-report.json"  304,628 bytes
# "$tmp/report.json"                     still a dangling symlink
```

## Change

* Admission uses `os.path.lexists(args.output)`, which counts a dangling link as
  an existing destination, and fails with `Use a fresh output path` before any
  fixture or VM work.
* The receipt is created with `args.output.open('x', encoding='utf-8',
  newline='\n')`. `O_EXCL` refuses a symlink or file that appears between the
  check and the write instead of following it, and the UTF-8/LF pin is kept.
* `scripts/test_pump_receipt_encoding.py` now recognises both pinned shapes
  (`write_text` and an exclusive `open`) and still requires the same five
  writers, so the guard keeps covering this script.

After:

```
python -B scripts/pump_buyback_recipient_differential.py \
  --candidate evidence/original/pump/deployed.so --output "$tmp/report.json"
# Use a fresh output path
# exit 1; "$tmp/escape dir/" empty; the symlink is untouched

python -B scripts/pump_buyback_recipient_differential.py \
  --candidate evidence/original/pump/deployed.so --output "$tmp/nested/report.json"
# {"cases": 42, "mismatches": []}
# exit 0; the full report is at the requested path
```

## Tests

`tests/test_buyback_recipient_output_admission.py` (new):

* `test_dangling_output_symlink_is_refused_before_the_run` — fails on the base
  script (exit 0, report at the link target), passes after.
* `test_existing_output_file_is_refused_unchanged` — control, passes on both.
* `test_fresh_output_still_publishes_the_full_report` — control, runs the real
  42-case differential into a new nested directory, passes on both.

Also passing: `tests/test_pump_buyback_external_candidate.py` (3 tests),
`scripts/test_pump_receipt_encoding.py` (1 test), `scripts/test_tooling.py`
(228 tests) and `scripts/verify_evidence.py` (9 captures).

## Limits

The receipt write is still neither staged nor fsynced; the report is a derived
artifact rather than a captured input, so this change fixes admission and
follow-through, not durability. No differential result changes: the guard fires
before any work, and the fresh control reports the same 42 cases with zero
mismatches.

Source commit for this report: `52c0b087c`. Environment: macOS arm64, Python
3.14.3, solders 0.27.1.
