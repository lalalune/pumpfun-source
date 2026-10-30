# Unsigned register comparisons in math reports

The archived `scripts/deep_section_analysis.py` recognizes unsigned JGT/JGE/JLT/JLE
after add/sub/mul only when the comparison uses an immediate. Their register forms
are omitted. This successor verifies the archived analyzer and ELF reader SHA-256
before executing them and replaces the one comparison predicate in memory. Root
scripts, captures, prior packages and every unrelated heuristic remain unchanged.

Source binding re-reviewed at `f09c728c8520`: `scripts/deep_section_analysis.py`
`9940b20f…` (after #1254, #1284, #1294, #1448, #1453, #1606, #1648, #1731,
#1795, #1806, #1813, #1831, #1842, #1991, #2182, #2209, #2351, #2482 and the LF-output commit 11c5d73b) and
`scripts/window_elf_reader.py` `5a57f329…` (after #2075 and #2388). Within
`analyze_math_patterns` those changes only add the 64-bit `0xc7`/`0xcf` shifts
to the shift count and sort windows by arithmetic density; the replaced
comparison predicate is unchanged and every count below was recomputed on
the current bytes.

Base: `094a06f18df738d41e77070c1a009e135671ac1a`. Pump file offset `0xd278`
contains `1f810000000000003d61070000000000` (`sub64 r1, r8; jge r1, r6, +7`).
The regression counts zero candidates with the archived predicate and one with
the successor. Across the existing math-intensive windows:

| Capture | Candidates before → after | Windows with candidates before → after |
| --- | ---: | ---: |
| Pump | 158 → 310 | 89 → 144 |
| PumpSwap | 121 → 196 | 63 → 101 |
| Fees | 119 → 187 | 74 → 98 |
| Mayhem | 92 → 293 | 36 → 74 |

An independent opcode-field census in the tests checks each of the 496 added
observations and confirms unrelated window fields remain identical. These are
static candidates, not proof of overflow protection, error handling, runtime
coverage or source equivalence. The five-arithmetic-op window threshold and all
other archived heuristics are retained. Only the exact reviewed LF sources are
accepted; this package makes no Windows checkout qualification claim.

Run from the repository root, using new output filenames:

```bash
python3 -B reconstruction/math-register-comparisons/test_analyze.py
python3 -B reconstruction/math-register-comparisons/analyze.py --program pump --archived --output work/math-archived.json
python3 -B reconstruction/math-register-comparisons/analyze.py --program pump --output work/math-corrected.json
python3 scripts/test_tooling.py
python3 scripts/verify_evidence.py
```

Each UTF-8 report binds its binary, archived sources and adapter by SHA-256.
Existing report files are refused, and source drift fails before execution.

The source binding was reviewed again with the combined #2546/#2548 analyzer
(`4b3c5cb204f8a287b5337e14932468c47713f0a0a38f274e1e46fec1e905f8c2`).
It rejects truncated or misaligned relocation tables and uses the section's
virtual address for strings that reach its end. The comparison predicate and
all three relocation substitutions remain unchanged. The six math and five
relocation successor tests pass against these combined bytes. The reader pin
remains `5a57f32949f983fc6f9ddf40916cd04bfcd2a73b6a16cc0e9d5d6872180dac32`.

The source binding was reviewed again with the #2625 analyzer
(`2c1c81602986cb0d988446923a6add9e10f4cffa6189737fa1cf1497345ce09b`).
It binds immediate comparisons to the destination register and recovers real IDL
discriminators from the dispatch tables. The replaced comparison predicate and
the three relocation substitutions remain unchanged, and the six math and five
relocation successor tests pass against these bytes, including the captured
Pump pair at file offset `0xd278` and every `overflow_checks` total recorded
above. The reader pin remains
`5a57f32949f983fc6f9ddf40916cd04bfcd2a73b6a16cc0e9d5d6872180dac32`.
