# w10r1-swaphop-region4of4: 0x5b3b0 multi_hop_curve::swap_hop, region 4 of 4

Region 4 = original window offsets 0x3670..0x4898 (the last quarter): tail of the trade-event CPI,
native_buyback, `complete = true` + CompleteEvent route, the `post_fill` test, post_complete_buy_event +
PostCompleteBuyEvent route, and the HopOutput build.

## Result (on main bf0b20087)

| build | bytes | ratio | slots_diff | slots per region | official | losses |
|---|---:|---:|---:|---|---|---|
| main bf0b20087 | 18,584 | 0.97551 | 672 | 0/41/388/243 | 1033/1033 | - |
| `for post in post_fill` alone | 18,576 | 0.97442 | - | - | 1033/337 | 696 raw (size -8) |
| adapter_difference bind alone | 18,592 | 0.9823 | - | - | - | size +8 |
| **both (this branch)** | **18,584** | **0.98907** | **127** | **0/41/86/0** | **1033/1033** | **0/0** |

Unstripped sha256 89f8069932c243ff522a9e28025fc9ce0b39348566ea73e60aeeb4bace6f0368. `regen.sh` reproduces ordered.ld.
Regions 1 and 4 are now equal slot for slot; the 127 remaining slots are in regions 2 and 3.

## Mechanism 1: `for post in post_fill` (region 4)

The original tests the post_fill tag with `jeq r1, 0 -> HopOutput` and lets the post event fall through. Ours
had `jne r1,0,+1; ja HopOutput`. BPF `analyzeBranch` cannot analyze conditional branches, so the shape is fixed at
ISel by the IR block order and branch polarity:

- if-let gives `icmp eq tag,1; br Some, None`, with the CompleteEvent invoke's Err block (bb350) between the test and
  the Some block (rustc creates both `?` targets together, Ok first), so neither successor is next: `jcc; ja`.
- IR oracle (llc on saved IR): either moving the Some block right after the test (e1), or `icmp eq tag,0; br None, Some`
  with the base block order (e2), gives the original `jeq` form. A `match` gives the polarity but creates the None
  block first, which moves the 129-instruction post-event Ok block (rejected).
- `for post in post_fill` (Option's IntoIterator) is byte-identical to oracle e2. Nine other spellings of the
  test are in the ledger (if let &/as_ref/ref, match both orders, is_none/is_some + unwrap, into_iter().next(), {post_fill},
  identity, map(|p| p)); none of them gives this shape.

On its own this removes the `ja` (-8 B). On the old main (d12329aa2) the original's other region-4 difference was a
re-spill `stxdw [r10-0xab0], r3` in the completion block. That re-spill appears once the curve deref is formed
before the fee_config clone (the region-1 gep_up oracle, now on main as `fee_inputs`). So region 4 is complete, but
the function is 8 B short.

## Mechanism 2: bind `adapter_difference` (w9r1 d1 half, region 2/3)

`let adapter_difference = amount.checked_sub(trade_amount).ok_or_else(..)?;` at line 571, used in the buy-arm tuple
in place of `amount - trade_amount`. On main alone it adds 8 B (stitch lane: 18,592 B, 696 raw losses). Together with
mechanism 1 the size goes back to the original 18,584 B, and the whole function drops from 672 to 127 differing slots.
Both edits stay on existing lines (line!() values and layout-pad lines unchanged).

## Before main moved (d12329aa2, 0.85352/1023) — kept for history

- region 4 residual was 28 orig-only instructions, 170 slots: aa8/ab0 spill-slot swap (region-1 cause), the missing
  re-spill (+0x3978) and the jne/ja (+0x3e00), which together shifted 140 slots; r6/r9 load swap at +0x4548; post_fill-piece
  spill slots (b30/b10/b08/ac8/ad0 vs b40/b38/b30/b28/a98).
- IR oracle e3 = gep_up + polarity: region 4 left with only spill-slot numbers and jump offsets (0.8747).

## Tools (scratch, under ~/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-region4of4/tools)
capir.py/orc.py (from w7r1-swaphop-regsched), orc2.py (per-region counts), irblk.py (IR block move/renumber),
dd.py (normalized orig-vs-cand instruction diff over an offset range, .o or .so), trial.sh/batch.sh.

## Ledger
Keys `0x5b3b0-main-d12329aa2-r4-*` and `0x5b3b0-main-bf0b20087-r4-*` (lane w10r1-swaphop-region4of4).
