# Mayhem receipt guard: cover the PumpReport writers

## Defect

`scripts/test_mayhem_report_encoding.py` asserted

```python
self.assertGreater(checked, 10)
```

over the `write_text` receipts it found in `mayhem_*.py`. That was true when
the guard was added (commit `1aae96df4`), but most of the family has since moved
to the shared `PumpReport` publisher, whose bytes are composed by the caller and
published with `write`. On a clean detach of `52c0b087c`:

```
$ python -B scripts/test_mayhem_report_encoding.py
FAIL: test_every_report_writer_pins_utf8_and_lf
AssertionError: 8 not greater than 10
```

The command is a step in `.github/workflows/verify.yml`, so main's verification
is red on it. The count went stale; the invariant it was standing in for —
every Mayhem report writer pins its bytes — is still worth enforcing.

Current inventory of `mayhem_*.py` scripts that take `--output`:

| shape | scripts |
|---|---|
| pinned `write_text` (8 receipts) | `mayhem_burn_sequence` (2), `mayhem_validate_admin`, `_extend`, `_fee_recipient`, `_quote_withdraw`, `_sweeps`, `_withdraw` |
| `PumpReport` | `mayhem_buy_differential`, `_buy_v2`, `_initialize_state`, `_pump_swap`, `_sell`, `_sell_v2` |

## Change

* `takes_output(tree)` — recognises the `--output` argument.
* `pinned_writes(tree)` — the `write_text` receipts, still checked per call for
  `encoding='utf-8'` and `newline='\n'`.
* `publishes_through_pump_report(tree, source)` — recognises the
  `PumpReport` import, construction and `write` call.

Every script that takes `--output` must match one of the two shapes, so an
unpinned `write_text` or a plain `open(..., 'wb')` writer still fails, and the
family-size assertion now counts report writers rather than bare receipts while
still requiring more than ten.

## Result

```
$ python -B scripts/test_mayhem_report_encoding.py
OK (1 test)      # 13 --output writers: 8 pinned receipts, 6 PumpReport writers
```

## Tests

`tests/test_mayhem_report_encoding_guard.py` (new) drives the guard against
synthetic `mayhem_*.py` files with `SCRIPTS` redirected to a temporary root:

* pinned and `PumpReport` writers pass (twelve files),
* an unpinned `write_text` fails on `encoding`,
* a plain `open(..., 'wb')` writer fails and is named,
* six files fail the family-size assertion,
* each helper recognises its shape and rejects the others.

## Limits

This is a guard, not a writer: no report bytes change. The `PumpReport` shape is
recognised statically, so a writer that imports the publisher but composes
unpinned bytes would still pass; the `write_text` shape keeps its per-call
keyword check.

Pre-existing, unrelated: three `test_mayhem*` tests fail on a clean `52c0b087c`
detach as well (pinned-image replacement, virtual-params `setUpClass`, sell
limit).

Source commit for this report: `52c0b087c`. Environment: macOS arm64, Python
3.14.3.
