# SBPF stack and register provenance gap audit

Baseline: upstream `2b9914e2ae2d1342ab135a9860c68c1ca9b42084`.

The maintained tools intentionally stop before register provenance:

- `stack_access.py` inventories only loads/stores whose encoded base register
  is literally `r10`. It does not follow `mov rN, r10`, pointer arithmetic,
  pointer spills/reloads, CFG joins, calls, or liveness.
- `control_flow.py` supplies admitted legacy-SBPF block boundaries, successors,
  reachability, calls, and cycles, but it has no value domain or fixed point.
- `residual_analysis.py` compares instruction fields and provides conservative,
  explicitly heuristic block correspondence. A `dst`/`src` difference is not
  explained as a register copy, stack alias, live-range difference, or
  spill/reload relationship.
- `instruction_stream.py`, `elf_symbols.py`, and `score.py` already provide the
  logical LDDW-aware decoder, admitted symbol ranges, and official
  normalization. A new tool should reuse them unchanged.

Historical `cto-assembly-introspection` scripts answered bounded, one-off guard
questions with backward demand and direct-r10 reaching definitions. Their own
handoff records an invalid first CFG pass, cross-call alias limits, and several
relationships that remained unknown. They consume local disassembly text and
are not maintained paired-ELF analyzers.

The historical frame and StackSlotColoring lanes are also not substitutes:
they align masked instruction text, consume private LLVM/MIR debug logs, infer
candidate virtual-register identities, or simulate compiler spill colouring.
Those experiments are useful compiler evidence, but they do not conservatively
prove stack aliases in arbitrary admitted SBPF binaries.

The missing maintained capability is therefore a bounded CFG fixed point over
decoded machine instructions that separates proven constants and stack
pointers from potential/unknown values, models calls and overlapping memory,
computes liveness, and layers paired diagnostics on the existing residual block
mapping. It must never promote a conflicting join or unknown base to a proven
stack access.

Overlap review: open PR #4056 adds execution fuzzing under
`reconstruction/verification/pump-admin-cto-fuzzer/`; current source-shim PRs
contain Pump Main research notes/source experiments. None supplies or modifies
the maintained harness capability described above.
