# w10r1-swaphop-stitch: 0x5b3b0 multi_hop_curve::swap_hop (stitcher)

Base: origin/main 43daa2043, fresh build 1032/347, swap_hop 18,584 B (= original), ratio 0.85352, slots_diff 1023, calls 107/1.

## Composite 1 (this branch)
Two compatible mechanisms from other lanes, both in the buy arm of swap_hop (programs/pump/src/multi_hop_curve_swap.rs):
- x1 fees-whole (swarm/x1-p2-buy-fees-whole-netquote-completefill 6936bc3f8): post_fill is the 4th element of the
  reserves-if tuple and the TradeFees from net_quote_for_budget / complete_fill stay whole through it.
- region3 le-first (w10r1-swaphop-region3of4, ledger 0x5b3b0-fw581362-r3-reserves-if-le-first-v1):
  `if base <= reserves {(base,q,nf,None)} else {over-reserves}`.
Edits stay inside existing lines, so line!() values and layout-pad balance are unchanged.

| build | bytes | ratio | slots_diff | official | losses |
|---|---:|---:|---:|---|---|
| main 43daa2043 | 18,584 | 0.85352 | 1023 | 1032/347 | - |
| x1 fees-whole alone | 18,584 | 0.92654 | 1047 | 1032/347 | 0/0 |
| **x1 + le-first** | **18,584** | **0.92654** | **1017** | **1032/347** | **0/0** |

x1 alone has the higher ratio but more differing slots than main (1047 > 1023), so it is not adoptable under the
size, slots, ratio order. le-first only moves the overflow closure block and brings the slots below main.

## Composite 2: + fee_inputs helper (after #2558 merged composite 1)
y1-hop-llvm h1a: `let (fee_config_len, cap) = match fee_inputs(c,&a.fee_config,&h.base_mint) {..}` with a nested
`#[inline(always)] fn fee_inputs(curve:&BondingCurve, fee_config:&Account<FeeConfig>, mint:&Mint) -> Result<(usize,u128)>`.
The `&BondingCurve` argument is now an SSA value formed before the fee_config AccountInfo clone (the region-1 lane's
GEP-placement target), and the -0xaa8/-0xab0 spill-slot swap disappears. On main 43daa2043 alone this was -16 B (y1);
on the x1 + le-first base it keeps 18,584 B. Region 1 now matches completely (574/574).

| build | bytes | ratio | slots_diff | unmatched orig insns (4 regions) | losses |
|---|---:|---:|---:|---|---|
| x1 + le (#2558) | 18,584 | 0.92654 | 1017 | 11/71/64/22 | 0/0 |
| x1 + le + d1 (match complete_fill + bind adapter_difference) | 18,584 | 0.93441 | 930 | 11/69/48/22 | 0/0 |
| **x1 + le + fee_inputs** | **18,584** | **0.96371** | **874** | 0/29/44/10 | 0/0 |
| x1 + le + d1 + fee_inputs | 18,584 | 0.97158 | 925 | 0/27/28/10 | 0/0 |

The last row has the highest ratio and the fewest unmatched instructions, but more differing slots; the branch head
follows the size, slots, ratio order and keeps the 874-slot row.

## Trials
See the ledger (lane w10r1-swaphop-stitch, keys 0x5b3b0-main-43daa2043-stitch-*).
