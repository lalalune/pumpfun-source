# w6r1-swaphop-ir: 0x5b3b0 multi_hop_curve::swap_hop (IR-oracle loop)

Base: origin/main 099b0dd (programs/pump identical at a56331f), 1027/1035 normalized, 276 raw.
Target base: ratio 0.7063, 18,328 B (orig 18,584), segdist opregs/exact 785/912, 106/107 calls.

## Method
rustc LLVM IR captured from a scratch crate copy (`--emit=llvm-ir`, hooked through
`fastbuild.run_compiler`; scratch only), swap_hop extracted, `llc` from the SDK reproduces the
fastbuild bytes (18,328 B). IR edits are scored by the w4-swaphop oracle (exactish/opregs) and the
call-anchored segment distance; then a Rust spelling is searched for.

## Results
| trial | change | bytes | ratio | segdist | official |
|---|---|---:|---:|---:|---|
| base | origin/main | 18,328 | 0.7063 | 785/912 | 1027/276 |
| e1 (IR) | move `%_940 = sub nuw` (sell_transfer_fee) into a new sell-tail block between the transfer_quote_out merge and the accrue join | 18,400 | exactish 0.7437->0.7708 | | |
| e2 (IR) | same block, empty | identical to base (block folded) | | | |
| **s1** | line 692 keeps the checked_sub check as a statement; the sell arm's tuple element is `net - output` | **18,400** | **0.7308** | **547/685** | 1027/276, no losses |
| f1 | `a.fee_config.to_account_info().data_len()` (orig clones fee_config: 107/107 calls) | 18,440 | 0.6853 | 820/965 | no losses |
| s1c | s1 + f1 | 18,456 | 0.7143 | 574/731 | no losses |
| s2 | s1 + seeds from `h.base_mint.to_account_info().key.as_ref()` inline (sibling lane w6r1-swaphop-sem's F2 mechanism: the clone's drop follows the seed stores, orig 0x15a0-0x1680) | 18,400 | 0.7414 | 501/657 | no losses |
| s3 | s2 + f1 | 18,456 | 0.7244 | 543/701 | no losses |
| s4 | s2 + buy arm: line 571 check as statement, tuple element `amount - trade_amount` (orig 0x2d20 sub in the buy tail) | 18,376 | 0.7419 | 511/654 | no losses |
| s5 | s4 + `if last { transfer_base_out(..) }` (orig 0x2d08 tests only `last`; `mhc_transfer_base_out` returns Ok for 0 itself) | 18,360 | 0.7422 | 509/652 | no losses |
| **s7** | s5 + post_fill as the arms' 6th tuple element (orig buy tail stores the post_fill pieces at the arm end, 0x2d28-0x2d60) | **18,432** | **0.7504** | **492/630** | 1027/276, no losses |

### Mechanism (s1)
The original has a sell-arm tail block (orig 0x2438: `sub64 r8, r1` = net - output, post_fill
tag 0) that the transfer_quote_out Ok edge and the not-last edge both reach before falling into
the accrue join (0x2458). In main, sell_transfer_fee is computed at line 692 before
transfer_input, so the arm-end block holds nothing, SimplifyCFG folds it into the join, and MBP
places the 590 error and complete_fill where the original has the sell tail (the w4 "MBP
frequency" residual at orig 0x23f8/0x28c8). Putting the subtraction in the arm's result tuple
keeps the block; the overflow check (ok_or_else closure, line 692) stays where the original has
it (right after post_fee_amount, orig 0x1cd0). overflow-checks are on, but the dominating check
removes the panic edge (no new callee).

## Why branch weights never moved swap_hop blocks
BPF's `analyzeBranch` cannot analyze conditional branches, so MachineBlockPlacement keeps every
block that ends in a conditional branch chained to its IR-order successor; only chains ending in
an unconditional jump are reordered. `!prof` 1:1000 / 1000:1 on the mayhem test changes nothing;
moving the 599 block after complete_fill in IR makes the mayhem test fall through into 599 as in
the original. The lever is MIR/IR block order (and which blocks exist), not branch polarity.
The arm-tail results above are this effect: a non-empty arm-end block survives SimplifyCFG and
becomes the fallthrough the original has.

## Landing reconciliation (on main 2bad4a9, after sibling #2183)
The merge 8d7fd3c93 kept this lane's spelling and dropped #2183's `fee_config.to_account_info()`
clone, which the original makes (107/107 calls): 0.75038 but 106/107 calls. Reconciled to the
union (this lane's arm tails / post_fill tuple / `if last` + #2183's fee_config clone, `reserves`
binding and scoped whitelist key): 0x5b3b0 ratio 0.72528 (main) -> 0.7332, 18,544 B, calls
107/107 (same multiset as main and orig); official 1027/276, compare_scores vs main: no losses.
`if last` alone: orig tests the stack slot [r10-0xa88] written once at entry (0x5b480) before
raw_output exists (0x2d08); `mhc_transfer_base_out` returns Ok for 0 itself.
