# Token-program constant detector

`scripts/bytecode_signatures.py::detect_token_transfer_patterns` looks for an
`lddw` immediate equal to 3, 7 or 12 and labels it `spl_token_instruction`.
Those values are SPL Token instruction-data bytes, not code immediates. The
detector returns zero rows for all four originals.

The program address is a 32-byte constant assembled by four consecutive `lddw`
loads. In the captures each chunk is followed by a store, so the four `lddw`
instructions are consecutive in the `lddw` sequence but not adjacent bytes.
This packet hash-checks the archived helper and detects exactly the SPL Token
and Token-2022 program constants. It does not rewrite the archived script and
does not claim that a transfer or CPI occurred.

```sh
python3 -B research/tooling-token-program-constant-detector-20261029/test_verify.py
python3 -B research/tooling-token-program-constant-detector-20261029/verify.py --repo .
python3 -B scripts/verify_evidence.py
python3 -B scripts/test_tooling.py
```

## Real corpus before/after

| program | windows | old rows | new rows | old windows | new windows | Tokenkeg | Tokenz |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pump | 1,035 | 0 | 4 | 0 | 4 | 3 | 1 |
| pump_amm | 785 | 0 | 2 | 0 | 2 | 1 | 1 |
| pump_fees | 585 | 0 | 3 | 0 | 3 | 3 | 0 |
| mayhem | 441 | 0 | 20 | 0 | 10 | 16 | 4 |
| total | 2,846 | 0 | 29 | 0 | 19 | 23 | 6 |

The raw oracle independently walks every window's complete `lddw` sequence and
requires the same 29 rows. A synthetic four-chunk Tokenkeg sequence is detected;
three chunks, a wrong fourth chunk, and four `lddw` constants equal to 3 are not.

## Method and limits

`inputs.json` binds the reviewed script and four original `.text` images.
`observations.json.gz` is regenerated from those bytes; `coverage-delta.json`
records the tooling totals. These rows are token-program constant loads in
static code. They do not prove a token transfer, a CPI, runtime reachability,
source provenance, whole-program equality or security clearance. The archived
`bytecode_signatures.py` and its reports remain unchanged.
