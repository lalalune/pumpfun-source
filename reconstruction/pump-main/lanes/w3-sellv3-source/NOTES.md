# Lane w3-sellv3-source (wave 3)

Target: `0x14a8a8` trade_v3 `sell` (sell_v3), 6032 B. Base: origin/main 665499915 (1022 normalized / 276 raw).

## Result (s04)

| | base 665499915 | s04 |
|---|---|---|
| cand bytes | 6040 | 6032 (= original) |
| ratio | 0.98707 | 0.99728 |
| slots_diff | n/a (size differs) | 6 |
| differing insns (normalized, aligned) | 14 | 4 |
| official normalized / raw | 1022 / 276 | 1022 / 276, gains [], losses [] |
| unstripped sha256 | aaf06331 (capture) / 86ed3f6a | e25ede25cf5021fa1ad10d151523e88856f86cc25f532831ee2923dcea1f3eeb |

Source change (`programs/pump/src/trade_v3.rs`, no lines moved):
- `pub fn sell(..)->Result<()> {sell_body(ctx,amount,min_sol_output)} #[inline(always)] fn sell_body(..)->Result<()> {` (same line as before).
- `emit_cpi!(event);` directly in the body instead of the `emit_sell_cpi(&ctx,&event)?` helper (helper deleted, its five lines left blank).

Ledger: 90948f27ff8a4e8b9cca26749966f28b (s04), c778c900716d (s03), 3a6c9be2 (s01), 3aba039f (s02).

Remaining residual: the `mov r1,r10; add r1,-0x358` sret lea for `prepare_bonding_curve` is scheduled after the
two argument GEPs (original: before them). Same residual exists in buy_exact_quote; buy_v3's original has it late.

## Mechanism

Three IR properties were needed (found with an llc oracle on the slim module, then an opt+llc oracle on
pre-optimisation IR, see below):

1. No `tag==2` re-check of the `From<ProgramError>` result: inline `emit_cpi!` returns the converted error
   straight through `?` in the handler body.
2. The `Clock::get()?` error block (bb107) right after the event block in IR order, before the emit blocks: also
   comes from inline `emit_cpi!` (rustc's first-reference block order).
3. In the return block the i64 tag phi must precede the ptr phi. Otherwise greedy RA swaps r8 (accounts) and r9
   (return tag) globally. (1)+(2) alone = the old r08/s06 "r8/r9 swap".

(3) is decided in the first (early) SROA: `PromoteMem2Reg` inserts each new phi at the block start, so the alloca
promoted later gets the earlier phi. SROA pops its worklist LIFO, i.e. in alloca *creation* order, and `_0` (the
return place) is created first, so `_0.sroa.0` (i64) is promoted before `_0.sroa.N` (ptr) and its phi ends up
second. The swap only happens when trivially-promotable allocas earlier in the PromotableAllocas list are removed
by `RemoveFromAllocasList` (swap-with-last) and pull the ptr partition forward; for sell that needs ~40 such
allocas, so with `_0` as the merge slot it never happens. Moving `_0`'s alloca to the top of the entry block in
pre-opt IR flips the order (opt -O3 + llc reproduces). In source: the `#[inline(always)]` body is LLVM-inlined
(post-opt names carry `.i` and `sell_body...exit`), so the merged return values reach `sell` through the
inlined callee and the final return-block phis come out tag-first. With the inline emit the frame also comes out like the original (key temp at -0x100,
seeds at -0x28); without the wrapper the inline-emit frame merges the key temp into the seeds slot at -0x28.

## Oracles (in ~/.cache/pumpfun-reconstruction/lanes/w3-sellv3-source/tools)
- `capture_ir.py` / `slim.py` / `irx.py`: post-opt IR → llc → compare (0.4 s per trial on the slim module).
- `capture_pre.py`: build with `-C no-prepopulate-passes --emit=llvm-bc`; `opt -passes='default<O3>'` on that
  bitcode reproduces the fastbuild sell function exactly (`preopt.py`, ~13 s). `phiorder.py` runs only SROA.
- `perm.py`: permutes the tail chunk order; `cmp.py --swap/--mask`: rename/frame-aware diff.

## Rejected
- s01: inline `emit_cpi!` alone (= r08): r8/r9 swap + key temp merged at -0x28, 94 slots.
- s02: helper taking `TradeEvent` by value + `?`: frame +0x60, recheck stays.
- s03: wrapper + body but keeping the helper `?`: byte-identical sell to base.

## Prologue lea (remaining 4 insns) - IR oracle result, no source yet
On the s04 post-opt IR, llc gives a full match (0 diff) when the `prepare_bonding_curve` result is written through
an explicit sret alloca whose `lifetime.start` is at function entry, before the `ctx.accounts` load (ledger
f23eefd0). No effect: a dummy early lifetime.start, a direct call stored into an alloca, all -pre-RA-sched variants
and -disable-sched-* flags, misched, GEP order, tail/noalias/readonly attrs. A source form must keep the
prepare_bonding_curve window (0x3cd50) matching, so changing its return type is not free. buy_exact_quote shares
the residual; buy_v3's original has the lea late.
