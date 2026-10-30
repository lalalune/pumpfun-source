# Window D: Admin CTO reconstruction

Target: Pump Main `admin_cto::execute` at original `0x22a10` (27,400 bytes).

## Fresh baseline

The lane started from `origin/main` at
`75b6547f66d097cb36e3a3f1ad60643d0c5fd848`. The official identity recipe
(v1.44 macOS rustc with the pinned Linux `sbpf-solana-solana` target libraries)
reproduced the maintained baseline:

- Admin CTO: 27,344 bytes, diagnostic ratio 0.37637.
- Direct calls: 154 internal calls and 3 external/syscall calls, matching the
  captured window census.
- Whole-program scorer: 1,027 / 1,035 normalized and 276 / 1,035 raw.
- Unstripped ELF SHA-256:
  `c2531dc00a48a5a38d937a635b81a78fed54186e50f6e17ce9006ec016568850`.
- Stripped ELF SHA-256:
  `d0d414e8a710885c16e233205e696e811c3e90587a6147425cb293cc812b034a`.
- Captured original SHA-256:
  `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`.

The exact rustc SHA-256 was
`1f26338cc2cabd0a6057dcbd0528bba262b23ca1296d357a55304ee31d1d9e5a`.

## Accepted source change

The maintained caller initialized `swept` to zero before the optional holder
sweep, then overwrote it only on the `shared && holder` branch. Expressing the
same control flow as definite assignment removes the preinitialized mutable
local:

```rust
let swept;
// source-coordinate padding
if shared && holder {
    swept = sweep(&ctx, &holder_key)?;
} else {
    swept = 0;
}
```

This is behavior-preserving, but it changes the MIR local lifetime and the
optimized control-flow layout. The first opcode-shape difference from the
baseline candidate is at target-relative `+0x21b0`: the baseline retains a
conditional result-tag branch followed by a long jump, while the new build
uses the direct jump and eliminates 13 instructions overall. The direct-callee
multiset remains identical (154 internal calls, 3 external/syscall calls, 37
unique internal callees).

Official identity results:

| Metric | Baseline | Definite assignment |
|---|---:|---:|
| Admin CTO bytes | 27,344 | 27,240 |
| Diagnostic ratio | 0.37637 | 0.37650 |
| Normalized membership | 1,027 | 1,027 |
| Raw membership | 276 | 276 |
| Normalized gains / losses | - | 0 / 0 |
| Raw gains / losses | - | 0 / 0 |

Final pre-rebase artifact hashes:

- Unstripped:
  `edcd31807b37224f8083fef3677fd2d9388e276852dcbf07aa060394309abc25`.
- Stripped:
  `dbd210997adefe64d0ad28e094c2ab96e2d24e4368e28a4c1ec5310fea0041d9`.

## Rejected and byte-identical source experiments

Every source experiment used a real identity build and a complete scorer pass.
The live attempt ledger contains the exact artifacts and results.

- Applying `?` after a conditional `Result<u64>`, assigning the branch value
  directly, and an explicit `Ok` / `Err` match all compiled byte-identically to
  the accepted definite-assignment form.
- Returning branch-local `Ok(amount)` values from the native/token sweep also
  compiled byte-identically. It did not recover the original shared result
  join.
- Expressing the native test as `!=` plus `match` compiled byte-identically.
- Reversing the native-mint equality operands reduced the ratio to 0.37560.
- Binding the quote-mint value and calling `PartialEq::eq` by reference reduced
  the ratio to 0.22206.

All variants above retained 1,027 normalized and 276 raw memberships, but the
two diagnostic regressions were rejected.

## Remaining IR gap

A fresh optimized LLVM IR capture still contains separate
`sweep.exit.thread`, `sweep.exit.thread335`, and `sweep.exit` blocks. Successful
sweep paths feed a separate `swept` phi; the accepted change does not claim to
recover the original unthreaded result join.

As a diagnostic only, compiling the root crate with
`-Cllvm-args=-jump-threading-threshold=0` raised the target ratio to 0.39820 and
produced a 27,424-byte target. It also changed the target call census to 154/5
and caused 271 normalized and 85 raw membership losses (756/191 overall), so it
is not an acceptance candidate and no compiler flag is part of the source
change. Its unstripped SHA-256 was
`d771f728913630aa34700c06d6664f08a909cc326b0ef8614746a34c826ee5a0`.
This independently reproduces the historical finding that LLVM jump threading
is a real residual source of the codegen gap.

## Offline differential qualification

`scripts/pump_admin_cto_differential.py` executed 363 signed LiteSVM cases
against the captured original and the independently rebuilt stripped candidate.
The cases cover creator reassignment, old-creator collection, holder sweeping,
native and token quote paths, Token-2022 admission, PDA and authority failures,
destination token-account validation, creator-fee boundaries, malformed and
frozen accounts, rent/resize boundaries, failed CPIs, events, errors, and state
transitions.

Result: 363 / 363 matched for error, before/after account state, events, inner
instructions, and return data. This finite corpus is evidence for the changed
control-flow representation; it is not a claim of exhaustive behavioral
identity. The report SHA-256 was
`32b2b5b38f45b48ac4933e530b5eae55baaec8219c2d26ba7bb106955b365b74`.

## Final upstream rebase

Immediately before publication the branch was rebased onto `origin/main` at
`a7135a6a64c446166895f7e3ea4ca84ac1a9b848`. An independent clean build of
that exact upstream SHA reproduced the same baseline target metrics and the
same 1,027 normalized / 276 raw membership. A separate clean build of the
rebased candidate reproduced the same 27,240-byte target, 0.37650 ratio, 154/3
call census, and zero normalized or raw gains/losses versus the fresh upstream
build.

Final upstream artifacts:

- Baseline unstripped:
  `31ec6381b4e7b4a7fb4c2a27820e65df8919196e9af15e3f398d55c5bbc88d58`.
- Baseline stripped:
  `1b04b8d4cf9ba6fda52d25d7781cb3ceb2d0cc359dd10e09d1672a97053b1455`.
- Candidate unstripped:
  `e4d630ca738f861e872cd78b9426babf147694e823899ee06aed53e4449c96d8`.
- Candidate stripped:
  `02abf4644b2de6fc2155886fcb6dd781cc3a585fe81a2f415fe4e6d82ad40ba1`.

The final candidate repeated all 363 offline comparisons with zero mismatches;
the final report SHA-256 was
`b50174d3b8d396d2015c63571d8a4e5251efd0615e1c2849ecb7e2bf8291eb19`.
