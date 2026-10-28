# Ordinary source order restores the initial arithmetic call sequence

Moving the price statement before `checked_mul` restores two bounded original
properties without adding a hint: the first **seven resolved callee identities**
equal O0082's prefix, and the overflow branch is again a nonzero branch after
price division. Both complete compiler outputs repeat without diagnostic flags.
The original error-block placement and complete handler still do not match.

The parent overflow-tuple form fixes price-before-guard ordering but emits a
zero branch over error handling. This follow-up separates ordinary source
ordering from an Option conversion. Each control changes only the inline price
helper in the exact 67-input PR #330/late-seed source context. No branch hints,
inline assembly, padding, no-op arithmetic or binary rewriting are introduced.

The positive ordering control swaps just these two statements:

```rust
let price=vs*1_000_000_000_000_000u128/vt;
let scaled=reference.checked_mul(tolerance_bps as u128);
```

Its next statement remains `scaled.ok_or(MayhemError::MathOverflow)?/10_000`.
In actual CodeGen Prepare IR, price multiplication/division now precedes the
overflow intrinsic and its guard. The guard has profile metadata. Final native
instructions nevertheless put the two overflow multiply helpers ahead of the
price multiply, as in the original. Source statement order, LLVM IR file order
and machine instruction order are distinct observations.

The negative control retains `overflowing_mul` but replaces the explicit error
branch with `(!overflow).then_some(scaled).ok_or(MayhemError::MathOverflow)?`.
Its CodeGen Prepare guard still lacks profile metadata, and the final branch
still skips error handling when the low bit is zero. This ordinary Option
conversion alone does not reproduce the checked-price-first arrangement. These
observations do not isolate profile metadata as the sole causal difference.

## Final executable evidence

The verifier uses the entry wrapper to bind the complete handler and resolves
local callees through their complete normalized windows and relocation patterns.
The first seven are two validation helpers, three multiply helpers and two
division helpers. Equality here is of these callee identities; it does not mean
equal caller instructions, arguments, raw callees, data or dynamic execution.

| Source | First seven call offsets | Mask / branch | Branch target | Body bytes | Bump read |
| --- | --- | --- | ---: | ---: | ---: |
| Original O0082 | 80, 192, 328, 384, 528, 568, 640 | 592 / `JNE r9, 0` | 1960 | 12,992 | 6,296 |
| Checked, price first, late seeds | 80, 192, 328, 384, 512, 552, 624 | 576 / `JNE r7, 0` | 952 | 12,912 | 6,200 |
| Overflow with Option projection | First seven identities differ | 560 / `JEQ r7, 0` | 936 | 12,904 | 6,192 |

The checked control's taken branch reaches `mov r7, 2` at 952, then an
unconditional jump to 1032, where error construction starts. The verifier checks
those bytes and that jump target. This still differs from the original's shared
error-block layout. The normalized slot diagnostic is 995 (Option control 980),
and ordered-callee correspondence is 46/51 (Option control 45/51); neither is
a complete match or a reason to promote a selected source.

Both controls preserve the exact **432 normalized / 77 raw-local / 431
injective** match sets and **4,314 positive internal-call observations**.
The other three trade handlers retain their complete normalized shapes and
ordered callees; all four original business bodies remain unmatched.

Three actual root compilations reuse the same pinned compiler and 104 dependency
artifacts: two source controls with actual CodeGen Prepare/finalized-isel dumps,
then the checked control repeated without diagnostics. Commands, exact source
maps and transforms, logs, linker captures and both complete outputs are retained.
The checked repeat equals the full symbols ELF and full ordinary stripped ELF,
including nonallocated bytes. Each initial MIR dump resolves 83 calls, preceding
the later tail merging that yields 51 final handler calls.

A fourth successful build executes the public recipe with fresh dependencies
and a new target directory. Its 163 compiler commands (85 target) reproduce
both complete checked-price-first outputs. Separate launch, logs, compiler
records and linker captures are retained in `rebuild-validation/`; identical
ELFs reuse the control artifacts. Complete dependency-archive identity is not
claimed. This fresh-build receipt applies to the checked control, not the
Option control.

The original captured allocation image is comparison-only. No target is run.
No behavioral, CFG, historical-source, recursive/data or whole-original identity
is claimed. Sweep and allocator compositions remain separate.

Replay is offline and included in the parent verifier:

```sh
python3 -I -B research/mayhem-signer-seed-order/composition/arithmetic/guard/verify.py
```

The parent's explicit `rebuild.py` accepts `--variant checked-price-first-late`
and `--variant option-projection-late` with the same pinned tool/vendor arguments
and a new output directory. It does not download inputs or execute the target.
