# Arithmetic right shifts in math-window reports

`analyze_math_patterns` counted 64-bit logical left/right shifts but omitted
both arithmetic-right-shift forms (`0xc7`, `0xcf`) from its `shifts` field.
The correction includes those two opcodes in the existing 64-bit category.
It does not expand the analyzer to 32-bit operations or change its heuristics.

Primary source: anza-xyz/sbpf commit
`f754c707f99779a756978f87c9afd25eeeb3d92e`,
[opcode definitions](https://github.com/anza-xyz/sbpf/blob/f754c707f99779a756978f87c9afd25eeeb3d92e/src/ebpf.rs#L352-L377).
Both ARSH64 operand forms are explicitly arithmetic shifts. The four previously
counted LSH64/RSH64 forms remain included.

## Retained evidence

Base: `094a06f18df738d41e77070c1a009e135671ac1a`. `evidence.json` records
the baseline helper hash, original capture hashes, original logical-shift totals
and hashes of the complete math reports with only `shifts` removed. These report
receipts check that this correction changes no other fields, window selection,
order, classification or ranking. They do not freeze the whole helper source.
A future intentional math-report change will require reviewing these receipts.

| Capture | Shifts before | Added ARSH64 | Shifts after | Affected windows |
| --- | ---: | ---: | ---: | ---: |
| Pump | 1895 | 44 | 1939 | 12 |
| Pump AMM | 1435 | 43 | 1478 | 11 |
| Pump Fees | 863 | 38 | 901 | 9 |
| Mayhem | 566 | 29 | 595 | 9 |

For example, Mayhem window `0xaa680` reported 85 shifts while omitting four
ARSH64 instructions. The corrected count is 89. Totals apply to the existing
selected math windows, not the entire text section. All 154 omitted operations
are identified by independently walking logical instructions in the tests.

## Validation

Run from the repository root with Python 3.12:

```sh
python -B research/tooling-arithmetic-shift-counts-20261030/test_verify.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
PYTHONUTF8=1 python -B scripts/deep_section_analysis.py --program mayhem --output /tmp/math-shifts-after
python -B /tmp/math-shifts-after/verify.py
```

Use a fresh output directory. The same focused suite fails six subcases on the
baseline (four real captures and both ARSH64 operand controls), then passes both
test methods after the fix. Existing logical shifts, 32-bit shifts and unrelated
operations have controls. Root tooling passes ten tests and nine captures verify
on CPython 3.12.14. The evidence CI suite runs the focused tests.

Before/after Mayhem CLI packets both pass their generated verifiers. Only the
nine affected `shifts` fields and the resulting manifest hash change; all other
files are byte-identical. Historical packets and captures are unchanged.

Open PR #1618 separately handles register-comparison overflow candidates in a
source-bound successor. It does not correct these shift counts. Its pinned
adapter's source admission would require its own reviewed transition if combined
with changes to the archived helper. This correction makes no runtime,
overflow-protection, reconstruction-equivalence or security claim.
