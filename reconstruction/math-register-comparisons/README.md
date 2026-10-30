# Unsigned register comparisons in math reports

The archived `scripts/deep_section_analysis.py` recognizes unsigned JGT/JGE/JLT/JLE
after add/sub/mul only when the comparison uses an immediate. Their register forms
are omitted. This successor verifies the archived analyzer and ELF reader SHA-256
before executing them and replaces the one comparison predicate in memory. Root
scripts, captures, prior packages and every unrelated heuristic remain unchanged.

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
