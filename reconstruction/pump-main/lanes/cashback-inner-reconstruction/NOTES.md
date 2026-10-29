# Lane cashback-inner-reconstruction

Target: original window `0x6cd78` (8,544 B), `legacy_sell::process_cashback_inner`
(`programs/pump/src/sell.rs:19`).

## Metrics (target_metric.py / score.py)

| build | cand bytes | ratio | callees in orig order | official normalized / raw | gains / losses |
| --- | ---: | ---: | --- | --- | --- |
| baseline d2cb88d | 8,816 | 0.7354 | no (line-85 error inlined, to_string inlined) | 1019 / 188 | - |
| step 1 (inline check, keyif) | 8,584 | 0.7611 | yes, all 58 | 1019 / 188 | none / none |
| step 2 (named bump array) | 8,584 | 0.8031 | yes, all 58 | 1019 / 188 | none / none |

## Mechanism

1. The original calls `Account::try_from_unchecked`, not `try_from`, after `transfer_native`
   (callee window resolves to `try_from_unchecked`). Diagnostic ratio is unchanged by this alone.
2. The existing-account check is inline in the `else` branch, not a nested `check_existing`
   function. With the nested function LLVM inlines `ToString::to_string` at the line-85 site
   (the original keeps it as a call) and adds a Result re-test (`== 2`) after the helper's error
   merge, which the original does not have. `#[inline(always)]` on the helper fixes the
   `to_string` call but keeps the re-test.
3. With the check inlined, the else head was laid out first. Cause (found with diagnostic
   LLVM flags in an experiment copy only): BPF `analyzeBranch` cannot analyze conditional
   branches, so a block ending in a conditional branch that falls through is glued to its
   layout successor. In the inline version the empty error-return merge block that sat between
   the `data_is_empty` branch block and the else head is removed by early tail duplication, so
   the branch falls through into the else head. The original shows `jne r0,0,+1; ja else`,
   i.e. unglued. `-disable-early-taildup` reproduced the original order (ratio 0.7605).
4. A source change that achieves it: write the line-33 key check as
   `if key != expected { return err!(...) }` together with the `if len < 8 || disc != ... { return err!(...) }`
   discriminator check. All 58 callees then appear in original order.

5. `let bump_seed = [bump];` declared before the seeds slice (instead of the `&[bump]` temporary inside it)
   puts the bump byte directly below the seeds array (orig -0x1e9) and aligns the stack-frame offsets
   of the early locals with the original. Ratio 0.7611 -> 0.8031.

## Remaining residuals

- 40 B (5 slots) larger. `user` (r4) is spilled to the stack in the candidate; the original keeps it in r7 for the whole function, so the argument spill slots are shifted by 8.
- Register allocation and spills differ in the `CpiContext::new(system_program.clone(), Transfer{from: user.clone(), to: uva.clone()})`
  clone sequence (orig +0xc68..0xdb0), plus the first instruction (`mov r6, r2` vs `mov r7, r2`).

Ledger attempt ids: 92dba45b (try_from_unchecked), b02ee191/143f1c62 (inline else), b7fe3455 (inline(always)),
1adf199b (early-taildup diagnostic), ada66214 (keyif), efa2b36a (named bump array); sweep rows for 0x6cd78 by lane cashback-inner-reconstruction.

## Round 2

PR #1234 merged step 1 only (0.7611). Branch merged with origin/main (1020 normalized, which includes the
coordinate-archaeology Location realign of the `copy_from_slice` lines). Step 2 (named bump array) re-applied on top:

| build | cand bytes | ratio | official normalized / raw | gains / losses vs d2cb88d |
| --- | ---: | ---: | --- | --- |
| origin/main 60bdd8a | 8,584 | 0.7611 | 1020 / 188 | 0x14f4e0 / none |
| round 2 t00 (bump_seed) | 8,584 | 0.8031 | 1020 / 188 | 0x14f4e0 / none |
<<<<<<< HEAD
| round 2 sg2 (&Signer user + pub(crate) wrapper) | 8,536 | 0.9858 | 1020 / 188 | 0x14f4e0 / none |

### Mechanism (round 2): ArgumentPromotion strips noalias from `user`

- IR oracle: `-C save-temps -Zfewer-names=yes` in an experiment copy, then
  `llc -O3 -mtriple=sbf -mattr=+store-imm,+jmp-ext -relocation-model=pic -function-sections -data-sections`
  on the optimized cgu bitcode reproduces rustc's bytes exactly (`$OUT/tools/oracle.py`, ~13 s per trial).
  `opt -passes='default<O3>'` on the `no-opt.bc` also reproduces it.
- `-print-changed -filter-print-funcs` shows the post-inline EarlyCSE (MemorySSA) merging the
  `AccountInfo::clone` key load of `user` with the entry `user.key()` load. It is legal because `user` is
  `noalias readonly` (constant memory to MemorySSA), so no cap/limit flag stops it. The original reloads the
  key from `user` at the clone, which then keeps `user` (not the key pointer) live and fixes the spill layout.
- Removing only `noalias` from the `user` parameter in no-opt IR gives 8,536 B, normalized dist 16, ratio 0.9858.
- Source that produces exactly that: `user: &Signer<'info>` in `process_cashback_inner` (and the wrapper), with
  `from: user.to_account_info()`, and the wrapper `pub(crate)` instead of `pub`. With `pub` + `#[inline(always)]`
  the inner fn is reachable cross-crate and gets external hidden linkage. `pub(crate)` makes it internal, so the O3
  ArgumentPromotion pass promotes the `&Signer` to its only loaded field (the `&AccountInfo`). The promoted parameter
  carries no `noalias`/`readonly`, so the CSE no longer happens. The caller loads `ctx.accounts.user.info` exactly
  like the original (`ldxdw r4, [r3 + 0x3d8]`). `&Signer` without `pub(crate)` is not promoted and loses `sell` 0x152888.

Remaining (dist 16): the else-branch `try_borrow_data()?` test (orig `jeq Ok, +1; ja err`, ours `jne err`) and one
tail `ja` block placement near +0x2150.

### Final step (round 2): owner check as `if ... { return err!(...) }` -> normalized match

| build | cand bytes | ratio | official normalized / raw | gains / losses vs d2cb88d |
| --- | ---: | ---: | --- | --- |
| round 2 o1t | 8,544 | 1.0000 (normalized_equal) | 1021 / 188 | 0x6cd78, 0x14f4e0 / none |

- IR oracle sweep (`tools/reorder.py`): moving almost any block (26 of 105) to sit right after the
  `try_borrow_data` test block gives distance 0. Moving it after the Ok successor does not. So the original's CFG equals ours. Only the
  LLVM block order differs. When the Ok successor is the next IR block, ISel inverts the branch (`jne err`). When it is not,
  ISel emits `jeq ok; ja err`. BPF cannot analyze conditional branches, so block placement never rewrites it.
- Writing the existing-account owner check as
  `if user_volume_accumulator.owner != &crate::ID { return err!(PumpError::InvalidCashbackAccumulator); }`
  (same line, same error) changes the order in which rustc creates the LLVM blocks. That is enough: 0x6cd78 normalized-equal.
  `*owner != crate::ID` is byte-identical. `require!(*owner == crate::ID)` is unchanged.
- Also adopted `Account::try_from` (checked) per callgraph-census row
  `0x6cd78-main-60bdd8a-checked-try-from-callee-identity-v1`. Normalized output is unchanged because the callee is masked.
- unstripped sha256 af5b9f02e925a4e32f675de12306d2d5fb50e9463248d7587b1c7ba6ba2e10cc. Raw-equal is still false (whole-ELF addresses).
=======
>>>>>>> origin/main
