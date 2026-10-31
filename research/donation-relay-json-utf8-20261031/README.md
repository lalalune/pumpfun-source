# The relay differential reads its JSON inputs with the platform default encoding

`scripts/donation_relay_differential.py` reads the relay IDL and the imported AMM
fixture inside `prepare()`:

```python
cap = json.loads(AMM_FIXTURE.read_text())['accounts']['quote_mint']
...
ix = next(i for i in json.loads(IDL.read_text())['instructions'] if i['name'] == name)
```

Both files carry documentation text. On an ASCII-locale host — `LANG` unset,
the CI default for a fresh shell — `read_text()` decodes with US-ASCII and the
fixture build aborts before any case runs. The pump IDL consumers were pinned to
UTF-8 earlier for exactly this reason; these two literals were not covered.

## Reproduction on the base revision

A driver imports the module, points `IDL` and `AMM_FIXTURE` at files with one
UTF-8 arrow, and calls `prepare()`:

```sh
LC_ALL=C LANG=C PYTHONUTF8=0 PYTHONCOERCECLOCALE=0 python3 -c '<driver>'
UnicodeDecodeError: 'ascii' codec can't decode byte 0xe2 in position 16: ordinal not in range(128)
```

## Change

```python
json.loads(AMM_FIXTURE.read_text(encoding='utf-8'))
json.loads(IDL.read_text(encoding='utf-8'))
```

Case preparation, instruction construction, both VM runs, the comparison and the
receipt payload are unchanged.

## Tests

`tests/test_donation_relay_json_reads.py` drives `prepare()` in a subprocess with
the C locale and a non-ASCII IDL and AMM fixture, for an ordinary and a native
donation. It runs under the contract-tests discovery.

```
$ python -B -m unittest tests.test_donation_relay_json_reads
base 963d1eefb: FAILED (failures=2)   # UnicodeDecodeError for both reads
change:         Ran 2 tests ... OK
```

## Limits

This changes only how the two inputs are decoded. It adds no case, no run and no
comparison, and changes no capture or prior receipt.
