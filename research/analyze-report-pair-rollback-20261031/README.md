# A failed second report leaves the first one regenerated

`scripts/analyze.py` regenerates two reports from the same read-only evidence:
`evidence/binary-analysis.json` and `evidence/interface-inventory.json`. Both
are admitted before anything is written, then staged, then replaced one by one:

```python
for temporary, path in staged:
    os.replace(temporary, path)
```

If the second replace fails — a full disk, a permission change, an interrupted
run — the first report is already from the new run while the second is still
from the previous one. The pair is tracked evidence: the binary layout and the
interface inventory are read together, and nothing in either file lets a reader
detect that they describe different regenerations.

## Change

Every prior file's bytes are captured immediately before its replace, and any
exception after the first replacement restores what this call changed:

```python
for temporary, path in staged:
    prior[path] = path.read_bytes() if path.is_file() else None
    os.replace(temporary, path)
    replaced.append(path)
except BaseException:
    for path in replaced:
        data = prior[path]
        if data is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(data)
    raise
```

Destination admission, staging names, the umask-derived mode, the UTF-8 LF
content and successful publication are unchanged.

## Tests

`tests/test_analyze_report_pair_rollback.py` (contract-tests discovery):

- a normal call publishes both reports and leaves no staging file;
- a failed second replace restores the first report's prior bytes;
- a failed second replace removes a first publication that had no prior file.

```
$ python -B -m unittest tests.test_analyze_report_pair_rollback
base 963d1eefb: FAILED (failures=2)   # b'new binary\n' != b'old binary\n'
change:         Ran 3 tests ... OK

$ python -B scripts/test_analyze_publication.py
OK
```

## Limits

This narrows the window in which a partially published pair exists; it does not
make two filesystem renames atomic. The restore is a plain write to a path this
call already owned, so it preserves the file's mode. It adds no analysis
behavior, changes no report content, and touches no capture.
