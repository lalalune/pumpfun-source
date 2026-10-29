# Lane llvm-ir-inverse (AMM sell cashback)

Approach: get the optimized LLVM IR rustc feeds codegen, reproduce codegen exactly with the SDK llc,
then permute basic blocks of `fn cashback` to find IR layouts that give the original machine code.

## Exact llc reproduction
Diagnostic build with `--extra-root-flags "-C save-temps --emit=llvm-bc,link"`; the `*-cgu.0.rcgu.bc` file is the
codegen input. `llc -O3 -mattr=+store-imm,+jmp-ext -relocation-model=pic -function-sections -data-sections
-trap-unreachable -no-trap-after-noreturn -filetype=obj` reproduces rustc's whole `.o` byte for byte
(`-no-trap-after-noreturn` is required). `opt -passes=instnamer` keeps it identical (it gives stable block names).
`tools/reduce.py` makes a module where only cashback is defined (other functions become declares, aliases dropped):
the cashback section is still identical, and llc takes about 0.15 s. `tools/prep.sh SLOT NAME` does all of this.
`tools/irscore.py OBJ` scores an unlinked object against the original window (call and lddw immediates masked,
callee names compared separately).

## Results
- Diff 1 (borrow test): any block between bb37 (try_borrow_data) and bb121 (success) at ISel gives the original
  `jeq r2,r3,+1; ja +201`. The owner_ne source (`if *owner != crate::ID { return err!(..) }` on line 444) does exactly
  this: the inlined line-444 error blocks end up between them in the IR.
- Diff 2 (ATA): same mechanism at bb59 (ATA data_is_empty), whose layout successor must be neither bb65 (create)
  nor bb68 (try_from_unchecked). Scanning every block Y inserted after bb59 (owner_ne IR): only bb83 (the
  create-branch error join) gives size 9024 with all 80 callees in order and **5 slot diffs**. Those 5 slots are
  jumps into a duplicated `ldxdw r6,[r10-1304]; ja ret` tail: the original keeps the final copy (0x2330), while
  llc keeps the copy at 0x16c8. So BranchFolder tail merging picks a different block to keep.
- The reorder lane's else-if variant (e0dfd) differs from the original in IR content (spill slots), not only in
  block order, so permutation can't fix it.

## Dead ends
- Putting the error block bb120 right after bb37: gives jeq to success with the error path falling through (wrong form).
- Moving bb83/bb84 to the end without a block between bb59 and bb68: still >= 68 distance.
