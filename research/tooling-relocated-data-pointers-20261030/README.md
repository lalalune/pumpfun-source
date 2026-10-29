# Relocated data pointer attribution

The data-layout scanner read legacy relocated data slots as plain 64-bit
addresses. Original `.data.rel.ro` captures encode type-8 targets in the upper
32 bits, so the report omitted most text pointers. The correction applies only
to type-8 data slots for SBPF V0, V1 and V2. Ordinary raw pointers, other
relocation types, V3/V4 and unknown versions retain their existing behavior.

The primary source is anza-xyz/sbpf commit
`f754c707f99779a756978f87c9afd25eeeb3d92e`:

- [Loader selection](https://github.com/anza-xyz/sbpf/blob/f754c707f99779a756978f87c9afd25eeeb3d92e/src/elf.rs#L448-L458)
- [Strict-header versions](https://github.com/anza-xyz/sbpf/blob/f754c707f99779a756978f87c9afd25eeeb3d92e/src/program.rs#L87-L94)
- [Legacy data relocation](https://github.com/anza-xyz/sbpf/blob/f754c707f99779a756978f87c9afd25eeeb3d92e/src/elf.rs#L1111-L1125)

`points_to` remains an image-relative target used for static classification;
it is not the rebased VM address. Resolved records retain `raw_value` and
`relocation_type` for provenance. No capture is modified. Pointer-like values
are not proof of a vtable, runtime reachability or program equivalence.
Section address reporting and other analysis layers are outside this change.

## Reproduction

Run from the repository root with Python 3.12:

```sh
python -B research/tooling-relocated-data-pointers-20261030/test_pointer_analysis.py
python scripts/test_tooling.py
python scripts/verify_evidence.py
python scripts/deep_section_analysis.py --program pump_amm --output /tmp/data-pointers-after
python /tmp/data-pointers-after/verify.py
```

Use a fresh output directory. The focused tests run in the evidence CI suite.
`evidence.json` records the exact baseline commit, baseline script hash,
tested script and original-capture hashes, and observed counts. Script hashes
record the tested transition; the tests authenticate original capture inputs
and replay the pointer assertions against current code. They do not freeze
later unrelated helper changes. Historical packages remain unchanged.

Against baseline `094a06f18df738d41e77070c1a009e135671ac1a`, the two initial
regressions failed seven subcases (four originals and V0/V1/V2 controls).
After the fix, all controls pass. Original `.data.rel.ro` pointer counts:

| Capture | Before | After |
| --- | ---: | ---: |
| Pump | 1 | 163 |
| Pump AMM | 1 | 157 |
| Pump Fees | 0 | 111 |
| Mayhem | 0 | 67 |

All non-pointer data-layout fields remained identical across the four captures.
Before/after Pump AMM CLI packages passed their generated verifiers. Analysis
layers 2 through 5 were unchanged. Validation is offline static analysis only.
