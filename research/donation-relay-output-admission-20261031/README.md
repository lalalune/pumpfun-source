# Donation-relay report can replace the binary it describes

`scripts/donation_relay_differential.py` runs each case against two independent
LiteSVM instances, one loaded with the captured relay binary and one with the
candidate, and writes its report last:

```python
Path(output).parent.mkdir(parents=True, exist_ok=True)
Path(output).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
```

Nothing compares `--output` with the inputs the oracle reads: the candidate ELF,
the captured relay binary (`ORIGINAL`, pinned by `ORIGINAL_SHA`), the captured
`spl_token` and `associated_token` images, the reserved-IDL record and the AMM
fixture. A destination that names one of them is written over that input after
every case has run.

## Reproduction on the base revision

With the tracked dependency images staged at the ignored
`repro/donation-relay/local-validation-proposal` paths, and a copy of the
captured relay as the candidate:

```sh
python -B scripts/donation_relay_differential.py \
  --candidate /tmp/dr-cand.so --group business_rejection --output /tmp/dr-cand.so
```

Base revision `53abf28b`:

```
{"group": "business_rejection", "case_count": 3, "differential_matched": 3,
 "mismatched_cases": [], ...}
exit 0
/tmp/dr-cand.so: 2442 bytes of JSON, sha256 a9f27d2f...6159e
sha256 before: 367f07a6...68563 (the captured relay bytes)
```

The run reports a matched differential and leaves a candidate that has become
the report. A destination that merely lives elsewhere behaves normally
(`--output /tmp/report.json` still exits 0 with `differential_matched 3`), so the
defect is the missing admission, not the oracle.

## Change

```python
def protect_output(output, inputs):
    """Refuse a report destination that aliases an input the oracle consumes. ..."""
    destination = Path(output)
    for value in inputs:
        source = Path(value)
        if destination.resolve() == source.resolve() or (
                destination.exists() and source.exists() and os.path.samefile(destination, source)):
            raise ValueError('report output aliases an input: ' + str(source))
```

`main` calls it with the candidate, `ORIGINAL`, `SPL_TOKEN`, `ASSOCIATED`, `IDL`,
`AMM_FIXTURE` and this script, before `execute` loads any fixture or runs a case.
`samefile` covers a hard link or a symlink to an input, which a string compare
alone would miss.

The sibling Pump, AMM, Fees and Mayhem differentials already admit their report
destinations (`PumpReport`, `protect_report_output`, `protect_inputs`); the relay
differential had no such check. Refusing up front is the smallest change that
preserves the oracle: it keeps the report payload, the paired comparison, the
effect checks and the mismatch exit status untouched.

## Tests

`tests/test_donation_relay_output_admission.py`, run by the contract-tests
discovery (`python -B -m unittest discover -s tests -v`):

- candidate destination: exit != 0, `report output aliases an input`, no fixture
  lookup, candidate bytes unchanged;
- captured relay destination: exercised through `protect_output` directly,
  because a CLI run that failed to refuse would overwrite the tracked capture the
  test reads;
- hard link and symlink destinations: refused, candidate unchanged;
- unrelated destination: not refused.

On base `53abf28b` the file reports `FAILED (failures=2, errors=1)` (both CLI
alias cases exit 0; `protect_output` does not exist). With the change:

```sh
python -B -m unittest tests.test_donation_relay_output_admission -v
# Ran 4 tests ... OK
```

## Limits

This admits where the report may be written. It adds no execution, selector or
signature coverage, changes no capture, suite or prior receipt, and does not
alter the differential's comparison or report payload. Replacing a prior report
at an unrelated path is unchanged.
