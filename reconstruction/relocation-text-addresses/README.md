# Text relocation address translation

This opt-in successor completes the `.text` side of the address-space correction
in [PR #1241](https://github.com/lalalune/pumpfun-source/pull/1241).
The archived `analyze_relocations` uses section virtual addresses for data targets,
but still classifies text with `elf.lo/hi` (file offsets), skips `.text` in its
section loop, and reads relocated LDDW operands using the virtual address as a file
index. A text section at address `0x1000`, file offset `0x20`, is consequently
reported as unknown. A relocation at address `0x20` is incorrectly called text.

`reviewed().analyze_relocations(elf)` uses section addresses for all target labels
and translates text addresses with `file_offset + address - section_address` before
reading LDDW operands. An incomplete instruction at the end of `.text` is not
resolved using bytes from the following section. Reports preserve relocation
addresses as virtual addresses.

The adapter checks the exact archived analyzer and ELF reader SHA-256 before any
source execution, then applies three unique, bounded substitutions in memory.
It changes no root script, capture, prior evidence package or relocation type
labels. Five tests cover both directions of a non-identity mapping, false file
offset attribution, section-bound reads, source drift and exact equality of the
complete reports for all nine retained captures.

From the repository root:

```bash
python3 -B reconstruction/relocation-text-addresses/test_analyze.py
python3 -B reconstruction/relocation-text-addresses/analyze.py --program pump --output work/pump-relocations-translated.json
python3 scripts/test_tooling.py
python3 scripts/verify_evidence.py
```

Use a new output filename. CLI reports bind the binary, archived sources and
adapter by SHA-256. The callable accepts the archived analyzer's parsed-section
interface; synthetic mappings test that interface directly. The CLI deliberately
retains the archived capture reader, whose broader non-identity ELF parsing is
outside this correction. The current captures have identical text addresses and
file offsets, so their reports are unchanged. This is static reporting fidelity,
not a general ELF validation, relocation execution or source-equivalence proof.
Only the reviewed LF source bytes are admitted; no Windows qualification is made.
