# Lane w3-sellv3-oracle (wave 3)

Target: `0x14a8a8` `trade::sell` (sell_v3), 6032 B. Base: origin/main 665499915 (1022 normalized / 276 raw).
On base, sell is 6040 B with ratio 0.98707 (rename-aware residual: the prologue `-0x358` lea plus the
helper-result `tag==2` re-check). This lane has no source change: the result is an IR-level map of what
the original needs.

## Oracles (scripts/)

- `capture_ir.py` (from v3trade-amm-idioms; `XFLAGS` env adds rustc flags) + `slim.py` + `oracle.py`
  (llc -O3 +store-imm,+jmp-ext pic, compare with `win.py orig`). On base IR it reproduces the build exactly
  (734 vs 735 insns, ratio 0.9871).
- `ired.py slim.ll SYM edit.py [X>Y block moves]`: apply a python edit to the post-opt function, then oracle.
  `MODEDIT=` edits the whole module, for example to change a callee declaration.
- `preor.py pre.ll edit.py`: **pre-opt oracle**. Capture with `XFLAGS=-Cno-prepopulate-passes`, edit the
  unoptimized sell IR, run `opt -passes='default<O3>'` (10 s) and then llc. On s06 it reproduces the rustc
  build exactly (diff 96, ratio 0.8747), so the in-tree LLVM pipeline is `default<O3>`. This lets you test
  MIR-shape hypotheses at the IR level before searching for a source spelling.
- `t.sh <trial> <edits.py> [cap]`: makes a variant from the worktree, builds it, scores it and runs
  target_metric. With `cap`, it also captures IR and runs the oracle.

## Results (IR level)

Post-opt base IR (helper `emit_sell_cpi(..)?; Ok(())`):
1. Dropping the `icmp eq %tag, 2` re-check alone gives jne and an r8/r9 swap (87 slots). This equals the
   helper-as-tail form.
2. Adding the Clock `?` error block (bb107) right after the event block bb108, before the LLVM-inlined emit
   blocks, gives the original `jeq Ok,+1; ja Err`. Only the r8/r9 swap is left (82).
3. Adding the return-block phis in tag-first order (`%_0.sroa.0.0` i64 before the ptr phi) **fixes the
   r8/r9 swap**: 4 slots, which is only the `-0x358` lea placement (ratio 0.9973, 734/734).

Two IR families reach that 4-slot state:
- **A, helper as tail expression** (`emit_sell_cpi(&ctx,&event)`): needs (i) tag-first ret phis and
  (ii) a non-chain block directly after the event block at ISel. The clock-error block, the ret block or the
  bb58 join all work. Other blocks give 9 to 182 slots.
- **B, inline `emit_cpi!(event)`** (s06): needs (i) tag-first ret phis and (ii) lifetime markers on
  `authority_info`, `inner_data`, the chain iterator temp `_184` and the invoke result `_200`. MIR opts
  remove their StorageLive/Dead. Without the markers, StackColoring cannot merge them, and the 32-byte
  `_4.i` lands at -0x28 instead of -0x100. That is the "frame top" problem found by the earlier lanes; it
  is not about alloca order (moving `%_386` changes nothing).

Why the order is wrong at all: LLVM inlining splices the callee blocks right after the call block. The
original therefore has the emit blocks in rustc first-reference order (after the clock-error block), and the
helper locals at the frame top with full-span lifetime markers. That is what MIR inlining would produce, but
the 1.79 MIR inliner still applies the cost threshold (100) to `#[inline(always)]`, so the emit helper is
LLVM-inlined (`.i` blocks).

### Ret phi order mechanism
The phis are created in the first SROA run (PromoteMem2Reg). SROA pops allocas from the back of the entry
block, and PromoteMem2Reg removes fast-path allocas by swapping in the last list element. Moving `%_0` to the
top of the entry block in pre-opt IR flips sell to tag-first (s06: 96 -> 18 slots, the same as the
post-opt phi swap). `refund_pool_authority` is tag-first only because its `amount` argument is spilled
after `_0` (removing the spill flips it back). Spilling `amount` or `min_sol_output` in sell does **not**
flip it. rustc always allocates `_0` below all non-argument locals, so no direct source lever has been found.
Position scan (`ir-edits/p_r0k.py`, K = number of allocas `_0` is moved up): K<=19 gives ptr-first and K>=20 tag-first.
The flip happens once `_0` is processed after `%_39`, the 24-byte error `Source{file,line}` temp of an early
`require!`/`error!` site that is memcpy'd into the AnchorError. The phi order therefore depends on the count
and kind of early error-site temporaries: a source lever would change how many such temps sit at the bottom
of the alloca list (the earliest MIR locals).

### Prologue lea (`-0x358` before the r3/r7 GEPs)
Unchanged by: GEP order, GEPs before the load, an explicit sret alloca for prepare_bonding_curve,
extractvalue placement, or a split entry block (CodeGenPrepare re-merges it). Every `-pre-RA-sched` variant
also places it late. The original's other prepare_bonding_curve call sites vary (exact/sell_v2: early;
buy: late) with identical entry IR, so the cause is elsewhere in the entry DAG.

## Source trials (all 1022/276, no gains or losses)
| trial | form | bytes | ratio |
|---|---|---|---|
| s06 | inline `emit_cpi!(event)` | 6032 | 0.8747 |
| tail | helper as tail expr | 6024 | 0.8875 |
| h4 | if-let helper as tail | 6024 | 0.8589 (+phi swap: 44, ok block after err) |
| ba | inline expansion, `let infos=[authority_info]` | 6032 | 0.8283 (markers still missing) |
| bb | inline expansion, `let r=invoke_signed(..)` | 5904 | 0.8554 |
| bc | inline expansion, `.iter().copied()` | 6008 | 0.5720 |

Ledger ids: 591ae388, 804cc186, d7e67cb1, eb423d0f, e886ef3a, 1a126ad2, 7520ae6c, fa00fe7f.

## Next ideas
- Family B: find a spelling that keeps StorageLive/Dead on the moved emit locals (for example, the account
  info array or the data Vec built in a nested block, or moves the MIR CopyProp/GVN cannot unify), and check
  each candidate with `preor.py` first.
- Ret phi order: use the pre-opt oracle to find which promotable non-fast-path alloca sits at the end of the
  SROA list in sell. Removing that one (for example, a temp the original did not have) together with a spilled
  argument should flip the order.
- The lea: compare the entry-block SelectionDAG of the original's early-lea callers (sell_v2 0x1445a8, exact
  0x148a60) with buy's late-lea caller.
