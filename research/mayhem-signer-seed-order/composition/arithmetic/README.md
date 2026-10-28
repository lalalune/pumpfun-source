# Trace Legacy Sell price arithmetic through native lowering

The subsequent [ordinary source-order control](guard/README.md) moves price
before `checked_mul`. It restores both the original seven-callee prefix and
nonzero overflow branch direction, with repeated complete outputs. A separate
Option projection does not do so. Error-block placement and the full handler
remain unmatched; the earlier overflow evidence below is retained unchanged.

The original O0082 calculates price before testing a retained low-bit flag.
The selected PR #330 source's `checked_mul` form tests its overflow flag first;
its selected machine instructions also divide the tolerance product before
calculating price. Reusing PR #327's existing `overflowing-product` source form
restores price-before-guard ordering. Combining it with PR #393's late inline
signer seeds preserves that property. **Neither control recovers a complete
handler or adds an original function match.**

This packet extends the preceding block-placement investigation. It retains
six actual native SDK v1.54 root compilations: two baseline diagnostics, two
overflow controls with diagnostics, and two controls repeated without those
diagnostic flags. Both complete symbols ELFs and ordinary stripped ELFs repeat
for each source control. Both baseline diagnostics reproduce their complete
parent outputs. These six runs reuse 104 pinned dependency artifacts and are
not fresh dependency builds. Compiler commands, environments, source maps,
tool/dependency hashes, raw stderr and linker captures remain available.

A **seventh successful build** executes the public `rebuild.py` in a new
directory with fresh dependencies. Its 163 compiler commands (85 target
commands) reproduce both complete late-overflow outputs. The separate launch,
logs, compiler records and linker captures are retained under
`rebuild-validation/`; the identical ELF bytes reuse the control artifacts.
Equality of every dependency archive is not claimed.

## Source provenance

All 67 source inputs start from the PR #330 packet at
`ea2b4e13db1c4e3d81836a4bdacbf312697d74d1`. The two replacements are the already
retained PR #327 `overflowing-product` control at
`a600dd2617cf9d062b0a602204fb8419e9e8c108`:

```rust
let (scaled,overflow)=reference.overflowing_mul(tolerance_bps as u128);
// The existing price calculation remains between these statements.
let delta=if overflow{return Err(MayhemError::MathOverflow);}else{scaled}/10_000;
```

The early control's complete `pump_interface.rs` and `state.rs` equal that
upstream control byte for byte; only PR #330's `buy_v2.rs` differs across their
67-file source maps. The native early control reproduces the upstream control's
complete normalized Legacy Sell body, relocation pattern and ordered callee
identities. This is not raw body or whole compiler-output identity across hosts.
The late control additionally applies the exact retained inline CPI source
region from the parent packet. Only `pump_interface.rs` changes from each PR
#330 early/late parent; line counts and the CPI error macro location are held.

## Actual IR and machine observations

The CodeGen Prepare dump explicitly links the multiplication-overflow tuple,
extracted flag, branch, price multiply/divide and tolerance quotient by SSA
values. The `checked_mul` guard precedes price calculation and carries branch
profile metadata. In both `overflowing_mul` controls, the price calculation
precedes the same tuple's overflow guard; that guard lacks profile metadata.
This does not establish profile metadata as the sole cause of final layout.

Baseline IR after `expand-large-div-rem`, `sbf-check-and-opt-ir` and
`codegenprepare` is retained. The baseline's machine call sequence has the
tolerance divide before the price multiply already at `finalize-isel`.
All **83 resolved callee identities** are identical across the five actual
dumps: after instruction selection, before/after machine sinking, and
before/after machine scheduling. Those later two passes therefore do not
introduce the observed callee-order difference in this build. Other passes
intervene between CodeGen Prepare and finalized instruction selection; this
packet does not attribute the change to an unobserved individual transform.
The retained `Before SBF ISel` machine dump is empty, not usable input LLVM IR.

Both overflow controls have the first three multiply helpers before the first
divide already in finalized instruction selection. The 83-call diagnostic
sequence predates later tail merging and is not the final 51-call sequence.
Machine block numbers are stage-local. No cross-stage block-ID identity, CFG
equivalence or dynamic execution trace is inferred.

The first exploratory parser missed scheduler SlotIndex prefixes (`1232B`)
and incorrectly reported zero calls there. That failed report is retained
under `failed/`. The verifier accepts actual SlotIndex prefixes, rejects
unparsed call encodings and binds each MIR target to the retained ELF.

## Final executable witnesses and limits

Offsets below are bytes relative to the bound Legacy Sell body. The verifier
decodes the actual low-bit AND and conditional branch, the `10^15` literal,
the `10,000` divisor and their normalized complete direct-callee identities.
These are bounded syntactic witnesses, not a symbolic execution proof of the
original flag's full provenance.

| Source | Price multiply | Price divide | Low-bit mask / branch | Branch target | Tolerance divide |
| --- | ---: | ---: | --- | ---: | ---: |
| Original O0082 | 528 | 568 | 592 / `JNE r9, 0` | 1960 | 640 |
| PR #330 checked baseline | 680 | 720 | 512 / `JNE r3, 0` | 1864 | 552 |
| Overflow, early seeds | 504 | 544 | 552 / `JEQ r8, 0` | 928 | 976 |
| Overflow, late inline seeds | 512 | 552 | 560 / `JEQ r6, 0` | 936 | 984 |

The overflow variants branch on zero and place the error-handling calls before
the tolerance divide in file order. The original uses a nonzero branch to a
later block. Restoring one arithmetic ordering property does not restore that
branch layout or the handler.

| Source | Body bytes | Bump-load offset | Diagnostic aligned slots | Ordered callee correspondence |
| --- | ---: | ---: | ---: | ---: |
| Original | 12,992 | 6,296 | — | 51/51 |
| Checked baseline | 12,864 | 2,368 | 599 | 50/51 |
| Checked, late inline seeds | 12,848 | 6,136 | 954 | 45/51 |
| Overflow, early seeds | 12,896 | 2,400 | 621 | 46/51 |
| Overflow, late inline seeds | 12,912 | 6,200 | 985 | 46/51 |

Alignment and ordered-callee correspondence are file-layout diagnostics, not
recovered instructions, an optimization objective or behavioral qualification.
The source controls retain exactly **432 normalized / 77 raw-local / 431
injective** matches and **4,314 positive internal immediate-call observations**.
Legacy Buy, BuyV2 and SellV2 keep their full baseline normalized shapes and
ordered callees. All four original business bodies remain unmatched. Imports
are identified by names; complete local callee normalization does not close
raw, recursive or referenced-data identity.

Original capture `a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`
contains a 775,416-byte ELF and 1,992-byte allocation suffix. It is only a
comparison input. Compiler outputs here are raw linked ELFs and ordinary
stripped ELFs; they are not padded allocation images or rewritten binaries.
No target execution, runtime equivalence, selected-source promotion, security,
historical-source or whole-original identity is claimed. Main was reviewed
through `58dd857b3cbe61b35e21e22290b5284ed23893af`; later sweep/allocator
contexts remain separate from this pinned trade source.

The parent verifier includes this check. Standalone replay needs only Python's
standard library and does not invoke a compiler, Git, network or VM:

```sh
python3 -I -B research/mayhem-signer-seed-order/composition/arithmetic/verify.py
```

The retained `recorded-*.py` files preserve the actual producer/acquisition
scripts and their workspace locators. Use them as receipts, not as portable
commands to overwrite a populated workspace.

For an explicit full offline rebuild, use this directory's `rebuild.py` with
`--variant overflow-early` or `--variant overflow-late`, a new `--output`
directory and the parent's `--sdk`, `--target-sysroot`, `--vendor`, `--msvc`,
`--windows-sdk` and `--kit-version` arguments. It uses the supplied pinned tools
and vendor inputs, downloads nothing and never runs the target. Only
`overflow-late` has the fresh full-build receipt in this increment.
