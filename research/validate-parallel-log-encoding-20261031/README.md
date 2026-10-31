# Retained validator logs are not written as UTF-8 LF

`scripts/pump_validate_parallel.py` keeps one `<suite>.log` per executed suite in
the retained evidence directory:

```python
(retained / (name + '.log')).write_text(completed.stdout, encoding='utf-8')
```

With `newline=None`, Python translates `\n` to the host line separator on write.
The compiler output contains newlines, so the same suite run retained different
log bytes on Windows than on the Linux CI. Every other text artifact this driver
publishes is a report payload written binary and staged; the logs were the one
unpinned writer.

## Change

```python
(retained / (name + '.log')).write_text(completed.stdout, encoding='utf-8',
                                        newline='\n')
```

The suite command, sharding, timeout handling, retained failure outputs, the
report payload and the exit status are unchanged.

## Tests

`tests/test_validate_parallel_log_encoding.py` requires every `write_text` in the
driver to pin `encoding="utf-8"` and `newline="\n"`, and exactly one such writer
to remain. It runs under the contract-tests discovery
(`python -B -m unittest discover -s tests -v`).

```
$ python -B -m unittest tests.test_validate_parallel_log_encoding
base ecea7021f: FAILED (failures=1)
change:         Ran 1 test ... OK

$ python -B scripts/test_pump_validate_parallel.py
OK
```

## Limits

This changes only the bytes of the retained suite logs. It adds no suite,
sharding or timeout behavior, changes no capture, suite or prior receipt, and
does not alter the report payload or its digests.
