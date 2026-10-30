# Root function-body admission transition

This packet records the three existing root-tool hash transitions for explicit
virtual and physical `.text` body bounds. The root Python script set is unchanged.
Original captures, immutable checkpoint inputs and historical receipts/packages
are not edited. Older receipts keep identifying the tool hashes they originally
ran; no historical result is transferred to this revised reader. The raw inventory
already includes the current helper hash in newly generated receipts.

Run from the repository root:

```sh
python -B tests/test_function_body_file_ranges.py
python -O -B tests/test_function_body_file_ranges.py
python -B scripts/test_pump_quote_control_function_match.py
python -B scripts/test_pump_window_inventory.py
python -E -X utf8 scripts/verify_evidence.py
python -E -X utf8 scripts/test_tooling.py
```

`transition.json` records base commit and base/proposed SHA-256 values for every
changed root script. The regression mutates independent bytearray copies of the
actual retained Pump ELF's `.text` file offset while keeping its section headers
readable. A declared 176-byte selected function formerly returned eight bytes or
zero bytes instead of rejecting the file extent. The positive control reads all
1,035 actual selected windows and checks their exact captured bytes. Virtual range
checks also remain active with optimized Python. No masking policy is changed.

Local Windows results: the new seven-test suite passes normally and with `-O`;
15 existing matcher tests and four inventory tests pass; nine captures verify.
The root tooling suite cannot collect because the official Windows solders 0.27.1
wheel lacks `FeatureSet`. A real LLVM objdump is unavailable, so no complete
objdump-backed CLI run is claimed. No mocked objdump, source rebuild, runtime
execution, score improvement, full ELF verification or equivalence/security claim.
