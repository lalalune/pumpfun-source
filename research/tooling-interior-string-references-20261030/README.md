# References inside printable rodata runs

The deep-disassembly report previously recognized an `lddw` string reference
only when its address exactly matched the start of an extracted printable run.
Retained captures contain type-8 relocated pointers into those runs. Ignoring
these pointers omitted most printable-data references from the window report.

For example, Mayhem instruction `0x36c8` contains
`1802000098d00a000000000000000000`, pointing to `0xad098`, four bytes
inside the run at `0xad094`. The remaining printable bytes are `true`.
Instruction `0x36e0` points to `0xad050`, 150 bytes inside the run at
`0xacfba`, whose remaining bytes are `false`. Both sites have type-8
relocations. The old report omitted both.

## Correction and limits

Sorted run starts are computed once. Each lookup uses a binary search for the
preceding run and checks its exclusive end, then returns up to 120 bytes from
the referenced position. This adds O(log R) lookup per immediate for R runs;
it does not scan every string for every instruction. Existing exact-start
references keep their content and schema.

These are **printable-run suffix previews**, not recovered Rust string lengths.
An interior suffix may be shorter than four bytes even though the extracted
run has at least four. No preview crosses the run's end or includes an adjacent
nonprintable byte. Adjacent literals can share a printable run; these observations
do not identify the historical compiler's pooling or linking decisions.
The [Rust Reference](https://doc.rust-lang.org/reference/type-layout.html#str-layout)
describes `str` as UTF-8 slice data, so an ASCII-run boundary alone does not
establish the semantic slice boundary. No runtime use, callee, ownership,
equivalence or security claim is made.

This change leaves extraction, address keys, relocation interpretation, captures
and historical reports intact. Open PR #1258 separately changes string-map keys
from file offsets to virtual addresses. This lookup operates on the supplied
keys without translating them, and a shifted-key control verifies compatibility.
The actual four captures are identity-mapped. It does not implement #1258's fix.

## Reproduction

Run from the repository root with Python 3.12:

```sh
python -B research/tooling-interior-string-references-20261030/test_verify.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
PYTHONHASHSEED=1 PYTHONUTF8=1 python -B scripts/deep_disassembly.py --program mayhem --output /tmp/string-references-after
python -B /tmp/string-references-after/verify.py
```

Use a fresh output directory. Baseline commit:
`094a06f18df738d41e77070c1a009e135671ac1a`. Before the correction, all four
real CLI count regressions failed; boundary controls also reported the absent
new helper. Afterward, both test methods pass (including four real CLI runs and
their generated packet verifiers), root tooling passes ten tests, and all nine
captures verify on CPython 3.12.14. The suite runs in evidence CI.

| Capture | Before | Added interior references | After |
| --- | ---: | ---: | ---: |
| Pump | 114 | 2368 | 2482 |
| Pump AMM | 135 | 1635 | 1770 |
| Pump Fees | 79 | 1084 | 1163 |
| Mayhem | 29 | 865 | 894 |

Every added real reference has a type-8 relocation and its preview matches the
captured bytes. All previous exact-start references remain present. A separate
before/after Mayhem CLI comparison preserves every other window field and the
contents of all nine other artifacts (gzip compared after decompression).
Only window references, the README explanation and resulting manifest change;
the existing gzip timestamp behavior is outside this correction.
