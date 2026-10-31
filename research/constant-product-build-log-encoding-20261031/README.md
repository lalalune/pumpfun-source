# The constant-product build log is not written as UTF-8 LF

`scripts/pump_build_constant_product.py` retains the compiler output next to
the object it produces:

```python
(args.output / 'build.log').write_text(result.stdout + result.stderr, encoding='utf-8')
```

With `newline=None`, Python translates `\n` to the host line separator on
write. The compiler emits multi-line diagnostics, so the same build retained a
different `build.log` on Windows than on the Linux CI.

## Change

```python
(args.output / 'build.log').write_text(result.stdout + result.stderr,
                                       encoding='utf-8', newline='\n')
```

The compiler invocation, the source and compiler snapshots, the object read and
every exit status are unchanged.

## Tests

`tests/test_constant_product_build_log_encoding.py` requires every `write_text`
in the script to pin `encoding="utf-8"` and `newline="\n"`, and exactly one such
writer to remain. It runs under the contract-tests discovery
(`python -B -m unittest discover -s tests -v`).

```
$ python -B -m unittest tests.test_constant_product_build_log_encoding
base ecea7021f: FAILED (failures=1)
change:         Ran 1 test ... OK
```

## Limits

This changes only the bytes of the retained build log. It adds no build
behavior, changes no capture or prior receipt, and does not alter the object the
script produces.
