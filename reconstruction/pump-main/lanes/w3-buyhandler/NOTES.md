# w3-buyhandler (wave 3)

Target: `0x13b9b8` `buy_v2::buy_handler` (original 15,480 B). Base: origin/main 66549991
(1022 normalized / 276 raw), buy_handler 0.95334 / 15,488 B.

Method: llc IR oracle. `llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext` on rustc's
optimized IR reproduces the built buy_handler exactly (0 differing instructions), so IR edits can be
scored against the original in ~7 s (lane-cache tool `llcor.py`, from buyv2-sibling-transplant).
Distance = masked instruction diff (call/lddw immediates and branch offsets masked).

## Results

| step | buy bytes / ratio | llc dist | official |
| --- | --- | --- | --- |
| main 66549991 | 15,488 / 0.95334 | 72 | 1022 / 276 |
| `let whitelisted=a.global.whitelist_pda==a.user.key();` bound before the fee tuple (f24ce58f) | 15,488 / 0.95597 | 67 | 1022 / 276, no gains/losses |
| + `if _size != 0 { unsafe { core::hint::unreachable_unchecked() } }` in v2 `ensure_rent_exempt` (c948be9c) | 15,512 / 0.97629 | 52 | 1022 / 276, no gains/losses |
| + `complete_and_prepare` ends `prepare_bonding_curve(..)?;Ok(())` (3a49f3ef) | 15,512 / 0.97682 | 50 | 1022 / 276, no gains/losses |

The second step also moves the siblings: exact-quote handler 0x13f630 0.97829 -> 0.99351 (20,216 B; 0.99392 after the third step)
and sell_v2 0x144508 0.95152 -> 0.96294 (13,968 B). The callee window 0x3b598 stays normalized.

### Why the `_size` hint works

All three original callers of the v2 `ensure_rent_exempt` pass a literal `0` in r2 and reuse that zero
for a later `None` spill. In one crate the callee never reads `_size`, so LLVM DeadArgElim
(`RemoveDeadArgumentsFromCallers`, which also applies to non-local exact definitions) rewrites every
call-site argument to `poison` and the `mov r2,0` disappears. The prior swarm got the original shape
from a separate path crate, which is out of bounds here (Cargo.lock). The `unreachable_unchecked`
branch leaves a use of `_size` in IR (an assume-style condition that emits no code), so DAE keeps the
argument, while the callee's own code still folds `minimum_balance(0)` and stays byte-equal after
masking. It states a true invariant (every caller passes 0). Reviewer note: it is `unsafe`; it is
ordinary Rust, but if the coordinator prefers, drop this commit and keep the binding change alone.

The binding was hillclimb's (#1207) improvement, lost when #1310 transplanted the handler. On main
it fixes the -0x408 vs -0x1d0 snapshot-slot hunk.

## Oracle findings (llc on rustc's optimized IR, masked diff vs original)

On the best IR (t8, dist 50), three block moves together give dist 21:

1. **Checked-add overflow placement** (orig: add1, add2, ovf2 adjacent, ovf1 far). Fixed when the
   trade_fees `?` Err block (`bb214`) sits after the second checked-add block (`bb218`) or after
   `bb217`, and before the cmp block `bb222`. A permutation sweep of the six blocks (720 orders,
   `an/perm-results.txt` in the lane cache) shows the rule: add1 must be directly followed by add2
   in IR (BPF `analyzeBranch` cannot analyze conditional branches, so MachineBlockPlacement
   pre-merges a block that falls through with its IR-next block), and neither add2 nor ovf1 may be
   directly followed by cmp. rustc creates the `?` switch targets (Continue, then Break) when it
   codegens the switch after trade_fees, so with any `?`/`match`/`if let` on the trade_fees
   Result the Err block lands before add1. An LLVM-inlined helper holding the add chain (t4) gets
   the layout right, but the helper's `Result` adds tag retests after the closure calls. Not solved
   at source level.
2. **Complete `if` branch sense** (orig `jeq r1,0; ja`): the CompleteEvent CPI Err drop chain
   (`bb24.i..`) must sit between the if-test block and the then-block `bb1.i`.
3. **Terminal `jne r8,2`**: the TradeEvent CPI Err chain (`bb281..`) must come after the ret block.
   The caller tail-call form `complete_and_prepare(ctx,timestamp)` (t1) gives the original's
   structure here: no tag retest on the CompleteEvent CPI Err path, and one shared ev drop chain.
   It then also needs the prepare test to keep the Ok block (`mov r8,2`) with the Err edge going
   direct (oracle k1, 61 -> 55). rustc creates the Ok arm first for `?`/`match`. Only `if let Err`
   creates the Err arm first, and that leaves a `drop_in_place<Result<(),Error>>` call on the Ok
   path (t6/t11/t14-t16, about 0.81).
4. **quote_mint snapshot copy** (all three v2 handlers): 4 interleaved ascending i64 load/store
   pairs in IR reproduce the original (52 -> 44). i256 or `<4 x i64>` copies and alignment changes
   do not. Spellings tried (`new_from_array(to_bytes())`, `{c.quote_mint}`) are byte-identical.

Remaining after those: zero-mov phi-copy order for the whitelisted fee tuple, two spill-slot swaps
(-0x750/-0x790 and -0x7d0/-0x7d8), and the CompleteEvent CPI Err tag retest (item 3).
