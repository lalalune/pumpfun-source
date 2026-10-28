# crank-derive findings (window 147944 crank_donation_fee_pda; re-derive from the original disassembly)

## 21:25 ROOT CAUSE of the v08 residual (IR-level proof)
- v08 (crank-b's best, reconstructed on w584: 15976B/1950i masked 0.9641) differs from the original ONLY because LLVM GVN
  merged the rent AccountInfo `key` load of the infos clone (`rent.clone()` in invoke's account_infos) with the SyncNative
  meta's `rent.key()` load. The merged key pointer stays live across TokenInstruction::pack in a callee-saved register
  (r8), which pushes the rent info ptr out of r6 and permutes the whole 12352..14080 region.
- Proof: llc (platform-tools v1.44 llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext on rustc's --emit=llvm-ir
  module reproduces rustc's crank exactly). Editing ONLY that IR (fresh `load ptr, ptr %_17` for infos[1].key) gives a
  crank body IDENTICAL to original 147944 (raw: regs, stack offsets, branch offsets all equal).
- Why GVN can merge in v08: helper param `rent: &AccountInfo<'info>` is noalias+readonly; after inlining, the scope
  metadata proves pack() and the heap stores cannot clobber rent.key. The original's source must not give that scope
  (rent reached through another indirection / aggregate / closure), while the rent info ptr is still loaded at the call
  site before Rent::get ([accts+656] at 6904). Testing source forms now.

## 21:13 SOURCE MATCH (independent; duplicate of crank-brute-g01, same sha e77815918e6e...8f1f6d0c)
- a3: v08 + helper `rent: &UncheckedAccount<'info>` (call site `&ctx.accounts.rent`, infos `rent.to_account_info()`):
  measure vs native w584 gained_normalized [147944], lost_normalized [], raw crank identical (ocmp raw 1.0000 span 0).
  fndiff's only 3 lines are lddw string previews (native rodata layout), as for create-g01.
- a4 (equivalent form, same sha): helper `sync_native_excess(donation: &AccountInfo, accounts: &mut CrankDonationFeePda)`
  whose first statement is `let rent: &AccountInfo<'info> = accounts.rent.as_ref();` (ata = &mut accounts.donation_fee_pda_ata).
- a1 (by-value struct NativeSync{donation, ata, rent} destructured in the helper) is WORSE: masked 0.8682 span 291
  (aggregate argument changes the caller-side codegen), so the "rent via an indirection" fix must keep the plain
  per-account parameters.
- Harvest: RR/shared/harvest/crank-derive-g01 (marked duplicate confirmation; canonical = crank-brute-g01).
- Lane tools left for reuse (RR/lanes/crank-derive/tools): mkvar.py (spec -> variant tree), run.sh (nbuild + score),
  score.py (masked/raw/depth/calls), ocmp.py (raw compare of .o/.so crank vs original), irexp.py (edit crank IR in a
  rustc --emit=llvm-ir module, llc it in ~1.6 s, score). Lane stopped per DIRECTIVES 21:08.
