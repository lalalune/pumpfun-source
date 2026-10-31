# A malformed `suites` member escapes both log audits unannounced

`scripts/pump_diagnostic_audit.py` is the shared paired-log oracle: the
differential scripts call `audit({'suite': rows})` in-process, and the CLI reads
a retained receipt and audits `report['suites']`.

```python
def audit(suites):
    mismatches, coverage = [], Counter()
    ...
    for name, suite in suites.items():
```

`suites.items()` is the first use. A receipt whose `suites` member is a list —
an edited file, a wrong-field copy, a producer that wrote the wrong shape —
reaches it and fails with `AttributeError: 'list' object has no attribute
'items'`, naming neither the receipt nor the member.

`scripts/pump_strict_ordered_logs.py` walks `report['suites']` with a walker that
accepts lists, so the same receipt is refused there with an unrelated message,
`Report pair/log coverage differs`, which suggests missing pairs rather than a
malformed member.

## Reproduction on the base revision

```sh
printf '{"suites": []}' > "$T/report.json"
python -B scripts/pump_diagnostic_audit.py --report "$T/report.json" --output "$T/audit.json"
```

Base revision `963d1eefb`:

```
Traceback (most recent call last):
  ...
  File "scripts/pump_diagnostic_audit.py", line 129, in audit
    for name, suite in suites.items():
AttributeError: 'list' object has no attribute 'items'
```

## Change

```python
def audit(suites):
    """Audit available pairs, rejecting a log source present on only one side."""
    if not isinstance(suites, dict):
        raise ValueError('report suites must be a mapping')
```

and, in the strict ordered-log audit, before its walk:

```python
require(isinstance(report['suites'],dict),'Report suites must be a mapping')
```

Pair discovery, log comparison, coverage counts, mismatch payloads and exit
statuses are unchanged, and a well-formed receipt audits exactly as before.

## Tests

`tests/test_audit_suite_shape.py`:

- `diagnostic.audit` refuses a list and a string, and still audits a
  well-formed one-case receipt;
- the diagnostic CLI names the malformed report instead of printing a traceback;
- `ordered.audit` refuses the same receipt with `Report suites must be a mapping`.

```
$ python -B -m unittest tests.test_audit_suite_shape
base 963d1eefb: FAILED (failures=2, errors=1)
change:         Ran 3 tests ... OK
```

## Limits

This changes which error names a malformed receipt. It adds no pair, no
comparison and no case, and does not alter any valid receipt's audit or exit
status.
