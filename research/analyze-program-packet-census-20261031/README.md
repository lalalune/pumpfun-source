# Census the analyze_program packet directory

Problem: `analyze_program.py` embeds the same packet verifier as
`deep_disassembly.py`, `deep_section_analysis.py` and
`bytecode_signatures.py`, but missed the directory census check those three
gained in PR #3036. Adding any unlisted file, directory or dangling symlink to a
generated packet still printed `All checks passed.`.

Fix: insert the sibling's two-line check at the top of the generated `main()`,
and add `analyze_program` to the census test's generator map so every case
covers it.

Reproduction at base `8cf3c5f8a7912b36ced352e49ac8538ff864a4c2`:

```
python -B scripts/analyze_program.py --program mayhem --output /tmp/packet
echo unreviewed > /tmp/packet/stale.txt
python -I -B /tmp/packet/verify.py   # All checks passed. (exit 0)
```

After the change the same verifier exits 1 with
`FAIL: packet directory entry set mismatch` and leaves the packet untouched.

Limits: existing packets are not regenerated; the check applies to new output.
macOS arm64, Python 3.14.3.

## Active wrapper qualification

The maintained output-retention wrapper now accepts the reviewed current
analyzer and ELF-reader LF/CRLF forms, plus their imported packet-publication
helper. Its real-capture, failed-input, retention and helper-drift tests pass.
The missing-capture control reaches the analyzer rather than failing during a
missing helper import. This refresh changes the executable wrapper only; no
historical packet is regenerated or rewritten.
