# buyv2-sibling-transplant

Targets (programs/pump/src/buy_v2.rs):
- `0x13f630` `buy_v2::buy_exact_quote_in_handler` (line 545), original 20,184 B
- `0x13b9b8` `buy_v2::buy_handler` (line 179), original 15,480 B

## Result 1: restore the prior-swarm exact-quote handler (attempt 8ed0a8a6)

The 2026-10-29 swarm's `exactquote-reordering` lane worked from a base tree whose ELF is
`bbb925b7` (eq ratio 0.98742). That source was never merged; main's handler had regressed to
0.694. The tree survives in git as `5e49b8cd6:research/pump-swap-partial-recovery-20261029/snapshots/v2-best-exactquote/source.tar.gz`.
Its `buy_v2.rs` is line-aligned with main, so lines 545..end were transplanted onto main
(the handler body plus the `pay_from_user*` / `move_curve_tokens` wrappers at 1052-1055).

| metric | main d2cb88d | this branch |
| --- | --- | --- |
| eq handler bytes / ratio | 20,096 / 0.69433 | 20,176 / 0.97341 |
| eq masked (regs,br,call,stack) | 0.9176 | 0.9742 |
| buy_handler | 15,424 / 0.66526 | unchanged |
| official | 1019 / 188 | 1019 / 188, no gains, no losses |
| unstripped sha256 | 04fdafc0 | 8cff4778 |

Mechanism differences restored: `let (base_token_program,base_mint)` bound at entry,
`NO_EXACT_FEE` const with `if !native{...}` admission, whitelist test written
`a.global.whitelist_pda==a.user.key()`, `(quote,pf,cf,computed,bps,bps)` tuple order,
`creator!=default` fee arms, local wrappers for curve/user transfers, and TradeEvent field order.

Composition with lane `buyv2-hillclimb` (#1207, frozen-best buy_handler): the whole snapshot
buy_v2.rs on main gives buy 0.94354 / 15,464 and eq 0.97341 / 20,176, 1019/188, no losses
(sha 3fcb1c4b, attempt 40cfd39c).

Remaining gap to the snapshot's own 0.98742 (and frozen-best buy 0.96177): the snapshot tree
also used the `pump-native-payments` path crate, which main removed. Re-adding it changes
Cargo.toml/Cargo.lock, so it is out of bounds (attempt dc8d8c16, compile-failed in a main copy).

## Result 2: sibling field order for `shareholders` (attempts 004c3e14, 3d77b725; on main 60bdd8a7)

Result 1 merged as #1218. Main 60bdd8a7 then also had #1207 (hillclimb buy_handler 0.94776)
and #1191 (buy_exact_sol_in matched, 1020/188).

`buy_handler` has no residual at the mayhem `buyback_fee_basis_points` branch, but the
exact-quote handler did (orig 0x1436c0: `jne r0,0,+2` where ours emitted `jeq r0,0,+1; ja +2`).
The siblings differ in where `shareholders` sits in the TradeEvent literal. Moving eq's
`shareholders` after the two buyback fields, as in buy_handler, removes that residual. A
one-instruction `mov r7,2` scheduling move appears near the shareholders unwrap (orig
0x1430d0), and the function gets 8 B smaller.

| eq metric (main 60bdd8a7) | before | after |
| --- | --- | --- |
| bytes / ratio | 20,176 / 0.97341 | 20,168 / 0.97361 |
| masked ratio (regs,br,call,stack) | 0.9742 | 0.9744 |
| buy_handler | 15,464 / 0.94776 | unchanged |
| official | 1020 / 188 | 1020 / 188, no gains, no losses vs main |
| unstripped sha256 | 8262164b | 65826a7c |

Flipping the arms instead (`if !c.is_mayhem_mode{..}else{0}`) gives a byte-identical ELF
(a3b03e53).

## Residual analysis (base: main + snapshot buy_v2.rs, sha 3fcb1c4b)

With registers, branch offsets, call immediates, stack offsets and rodata pointers masked,
eq has 13 residual hunks and buy_handler has 20. Most of them occur in both handlers:

1. **`_size` spill around `ensure_rent_exempt`** (orig eq 0x142b48/0x142be8/0x142c40, buy
   0x13dcd0..0x13ddc0). The original passes `_size = 0` in r2 and reuses that zero as the
   spilled `None` dst operand. In one crate, LLVM DeadArgElim finds the unused `_size`
   (exact definition) and poisons the call-site argument, so no `mov r2,0` is emitted. In the
   snapshot tree, `ensure_rent_exempt_v2` lives in the separate `pump-native-payments` crate,
   so callers see only a declaration, and the residual is gone in both handlers (bbb925b7: eq
   9 hunks, buy 16). Restoring the crate needs Cargo.toml/Cargo.lock changes, which are out of
   bounds. I found no ordinary in-crate spelling that keeps a call-site argument alive while
   leaving the callee's own bytes unchanged.
2. **Terminal `?` on `prepare_bonding_curve`** (orig `jne r7,2,ret`, ours `jeq r7,2,+1; ja ret`).
   At ISel, the IR block after the prepare call is the shared Err path that drops `ev`
   (String/Vec), so ISel emits jeq-to-ok plus an unconditional jump. BPF `analyzeBranch` cannot
   reverse conditional branches later. `drop(ev)` just before prepare removes this residual but
   moves the prepare block ahead of the CompleteEvent block (attempt 7b8f072f). `drop(ev)`
   right after `emit_cpi!` changes nothing in eq (f08bf076).
3. **Stack-slot group A** (orig -0x100, ours -0x28: the unwrap_failed error at function entry,
   the post_fee Result, and the prepare Result). Dumping frame objects after PEI shows that A's
   24-byte members were colored into the 32-byte CompleteEvent seeds slot (frame index 9, the
   top of the frame). That pushes the TradeEvent bump to -0x38 (orig -0x28) and the outer
   seeds slice to -0x118 (orig -0x160). In the original, A merged into a 48-byte slot at -0x100.
4. **quote_mint snapshot copy order** (orig copies ascending, ours descending, in both
   handlers). Both snapshots are `llvm.memcpy` in IR. Respelling the copy gives a
   byte-identical ELF (bac1ba16, 7a48bc8d). The ascending, interleaved ld/st pairs suggest the
   original copy came from chained scalar loads and stores, not a memcpy intrinsic.

Experiment-only tooling (outside git, under the lane's cache dir): `scripts/sdiff.py` (masked
structural diff), `scripts/callseq.py` (call-name sequence diff), `scripts/frame.py` (stack
offset census), and `scripts/fastbuild_ir.py` + `irwrap.py`, which emit optimized IR and
`-print-after=prologepilog` frame objects for one function without changing the target
bytes (verified: identical eq function bytes).

## Result 3 (round 2): CompleteEvent emission + prepare in an `#[inline(always)]` helper (attempt 83bd6497)

Tooling: `scripts/llcor.py` (lane cache) runs the SDK `llc` on rustc's emitted optimized IR
(reproduces the built function exactly), optionally moving IR blocks or allocas, and diffs the
function against the original with call/lddw immediates and branch offsets masked.
`scripts/lifeexp.py` inserts lifetime markers into the IR; `scripts/scmerge.py` turns
`-print-before/after=stack-coloring` dumps into a slot-merge map.

Root cause of the stack residual (item 3 above), in both handlers: the `emit_cpi!` temporaries
of the CompleteEvent CPI (`_647` from_iter iterator 48 B, `inner_data`, `authority_info`, the
invoke Result) have **no lifetime markers** in IR, so StackColoring never merges anything into
the 48-byte iterator slot at -0x100. Group A (post_fee Result, TradeEvent ix_data, unwrap temp)
then merges into the 32-byte CompleteEvent seeds slot at -0x28. Adding helper-scoped markers to
just those four allocas in IR removes every stack hunk (llc oracle dist 40 -> 27). LLVM's
inliner inserts exactly such markers for a callee's marker-less allocas, so in the original the
CompleteEvent emission was inside an inlined function. Matched precedents: legacy
`buy_exact_sol_in` (`#[inline]` body, iterator temps `_459.i` have markers) and sell_v3's
`#[inline(always)] emit_sell_cpi`.

| variant (both handlers) | eq bytes / ratio | buy bytes / ratio |
| --- | --- | --- |
| PR head before (shareholders order) | 20,168 / 0.97361 | 15,464 / 0.94776 |
| helper = `emit_cpi!` only, `?` in caller (4489cf56) | 20,200 / 0.97201 | 15,496 / 0.9457 |
| helper = Complete if-block, caller `?` then prepare (b6418523) | 20,192 / 0.97221 | 15,488 / 0.94595 |
| helper = then-body only (4aa11725) | byte-identical to emit_cpi-only | |
| **helper = Complete if-block + `prepare_bonding_curve`, caller `helper(ctx,ts)?; Ok(())` (83bd6497)** | **20,192 / 0.97829** | **15,488 / 0.95334** |
| same, helper call as tail expression (0bb5e918) | 20,136 / 0.97562 | 15,432 / 0.944 |

Official 1020/188, no gains or losses vs main. Unstripped sha256
86b0298046ab3f1968902467de019482e99391e57b745c0025c7d5e5db32edef.

Remaining eq residuals (oracle on the new IR): quote_mint copy order, the `ensure_rent_exempt`
r2=0 spill (needs a cross-crate callee), one `mov r7,2` schedule, the Complete `if` branch
sense (orig `jeq r1,0; ja`), and the terminal `jne r7,2`. Moving the helper's CPI-error drop
chain after the Ok return block in IR fixes the terminal branch (oracle 36 -> 32).

Other round-2 trials: `size.min(0)` to keep the ensure_rent_exempt arg alive (byte-identical:
MIR-inlined), `if let Err(e)=prepare(..)` (eq 0.797), `drop(ev)` after prepare (identical),
`if r.is_err(){return r;}` (outlines drop_in_place<TradeEvent>, both ~0.80).
