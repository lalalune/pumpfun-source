# Indirect call decoding

The deep disassembler previously rendered opcode `0x8d` as an unknown raw
instruction. On the retained Mayhem capture at `0x638`, bytes
`8d00000002000000` produced `raw_0x8d r0,r0,0,2` instead of `callx r2`.
This instruction is a register-indirect call, not a direct target or syscall.

The decoder now reports the mnemonic and `indirect_call_register` in its
structured API. It does not invent a target address or change direct-call
counts, fingerprints, CFG edges, historical packets or original captures.

## Source and scope

Primary source: anza-xyz/sbpf commit
`f754c707f99779a756978f87c9afd25eeeb3d92e`,
[disassembler.rs line 297](https://github.com/anza-xyz/sbpf/blob/f754c707f99779a756978f87c9afd25eeeb3d92e/src/disassembler.rs#L297)
and [program.rs](https://github.com/anza-xyz/sbpf/blob/f754c707f99779a756978f87c9afd25eeeb3d92e/src/program.rs#L67-L102).
V0/V1 select the immediate register number, V2 selects the source nibble,
and V3/V4 select the destination nibble. Missing or unknown version information
and invalid register fields retain raw decoding. Unlike the reference formatter's
byte cast, invalid V0/V1 immediates are not truncated into a plausible register.
This is static presentation only, not validation or execution of newer SBPF.

All four real captures have flags zero. Tests inspect every logical instruction
and recover 144 Pump, 123 AMM, 121 Fees and 93 Mayhem indirect calls. Separate
controls distinguish all supported operand locations and unknown/invalid inputs.
No claim is made about runtime callee identity, program equivalence or security.

## Reproduction

Run from the repository root using Python 3.12:

```sh
python -B research/tooling-indirect-call-decoding-20261030/test_verify.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
PYTHONHASHSEED=1 PYTHONUTF8=1 python -B scripts/deep_disassembly.py --program mayhem --output /tmp/indirect-calls-after
python -B /tmp/indirect-calls-after/verify.py
```

Use a fresh output directory. Before the correction, on base
`094a06f18df738d41e77070c1a009e135671ac1a`, the same focused tests failed
nine subcases: four real captures and five known-version controls. Afterward,
four tests pass, root tooling passes ten tests and all nine captures verify.
Both before/after Mayhem CLI packet verifiers pass. With the same hash seed,
ten packet files are byte-identical; decompressed disassembly differs only in
93 callx mnemonics. Its compressed file and manifest consequently change.
The existing gzip timestamp behavior is outside this correction.

Open PRs #1502 and #1639 cover separate roadmap diagnostics, not this decoder.
This focused correction can accompany the existing deep-disassembly call fix;
it does not add another reporting schema or a replacement diagnostic pipeline.
