# Diagnostic audit cannot publish into a new output root

`scripts/pump_diagnostic_audit.py` audits the paired logs already retained in a
differential receipt and publishes the result as a fresh receipt. It stages that
receipt with `tempfile.NamedTemporaryFile(dir=args.output.parent, ...)` and then
publishes it without replacement.

Nothing creates `args.output.parent`. When the caller names an output root that
does not exist yet — the normal case for a new evidence directory — the staging
call raises `FileNotFoundError` and the audit publishes nothing.

## Reproduction on the base revision

A one-case report with a differing panic message and a fresh nested destination:

```sh
python -B scripts/pump_diagnostic_audit.py --report "$T/report.json" \
  --output "$T/fresh/nested/audit.json"
```

Base revision `53abf28b`:

```
FileNotFoundError: [Errno 2] No such file or directory:
  '<temp>/fresh/nested/.audit.json.adzglp4c'
```

Exit status 1, and `<temp>/fresh` is never created. The same report with a
destination whose parent already exists publishes normally (`{"log_bearing_cases":
1, "mismatches": 1}`, exit 1), so the failure is the missing parent, not the
audit.

## Change

```python
result['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
# Stage beside the destination; a fresh destination root is the caller's to
# name, so its parent must exist before the staged file can be created.
args.output.parent.mkdir(parents=True, exist_ok=True)
```

This is the same line, in the same position relative to staging, that the two
sibling audit CLIs already run: `scripts/pump_strict_ordered_logs.py` before its
`NamedTemporaryFile`, and `scripts/pump_data_order.py` before
`publish_certificate`. The directory is created only after the report has parsed
and produced at least one log-bearing case, so an unusable report still creates
nothing.

Nothing else changes: the report parsing, log-pair admission, panic/anchor/
comparand comparison, no-replace publication, source-report re-read discipline,
staging cleanup and mismatch exit status all stay as they are.

## Tests

Two cases are added to `scripts/test_pump_diagnostic_audit_publication.py`, which
`verify.yml` already runs directly:

- `test_fresh_output_parent_is_created` — a matched one-case report publishes into
  `<temp>/fresh/nested`; the receipt carries the source-report digest, the report
  is unchanged, and the output root holds only `audit.json`.
- `test_fresh_output_parent_still_reports_mismatches` — a panic-message difference
  publishes into `<temp>/fresh`, exits 1 and records both panic strings.

On the base revision both cases fail with the `FileNotFoundError` above; with the
change all twelve cases in the file pass.

```sh
python -B scripts/test_pump_diagnostic_audit_publication.py
```

## Limits

This fixes where the audit may write, not what it audits. It adds no new
execution, signature or selector coverage, changes no captures, suites or prior
receipts, and does not alter the receipt payload or its digests. The
treated-bytes admission rules of the audit itself are unchanged.
