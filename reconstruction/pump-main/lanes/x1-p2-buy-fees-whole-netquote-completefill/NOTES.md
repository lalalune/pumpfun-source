# x1-p2-buy-fees-whole-netquote-completefill

Target: swap_hop, window 0x5b3b0 (18,584 B).
Base: 5e9a02804 (swarm/w9r1-swaphop-asm p2, read-only), merged with main 1852a872e.

## Mechanism
In the buy arm of swap_hop (programs/pump/src/multi_hop_curve_swap.rs), keep the TradeFees
returned by `net_quote_for_budget` whole (`let (_, nf) = ...; sub3(trade_amount, nf.protocol_fee, nf.creator_fee)`),
and carry a whole TradeFees through the reserves-if tuple: `(base,q,nf,None)`,
`(reserves,q,nf,None)`, `Some((f,quote,post)) => (reserves,quote,f,Some(post))`.
The buy arm returns that `fees` value directly instead of rebuilding
`TradeFees{pf,cf,p_rate,c_rate}`. The sell arm is unchanged. Edits stay within existing lines,
so line!() values and layout-pad balance are unchanged.

## Metrics (score.py vs shared baseline 1852a872e: normalized 1032, raw 337)
| build | swap_hop bytes | ratio | normalized | raw | losses |
|---|---|---|---|---|---|
| p2 base 5e9a028 (unmerged) | 18,520 | 0.89006 | 1031 | 337 | 0x1489f8 (stale base) |
| (a) both whole, unmerged | 18,584 | 0.92654 | 1031 | 347 | 0x1489f8 (inherited) |
| **(a) both whole + merge main** | **18,584** | **0.92654** | **1032** | **347** | **none** |
| (b) net_quote whole only | 18,520 | 0.89006 | 1032 | 337 | none (byte-identical to base) |
| (c) complete_fill whole only (M7) | 18,552 | 0.88972 | 1032 | 337 | none |
| (a) + bind `base_mint` once | 18,584 | 0.92654 | 1032 | 347 | none (no change) |

Raw gains (+10): 0x29518 0x296f0 0x32530 0x3b598 0x3b738 0x3cd50 0x47d00 0x524f0 0x54c90 0x54db8
(these come from the +64 B size fix, which shifts later code back to the original addresses).
Calls 107/1 match the original. 1047 differing slots remain (target_metric slots_diff).

## Residual
Neither half works alone. Both halves are needed so that the TradeFees phi gets its own
slots, which restores the two original 4-insn copy blocks.
The largest remaining pattern is a spill-slot swap of [r10-0xaa8] and [r10-0xab0] (31 and 32 sites):
the original spills r8 (first at o+0x420, `stxdw [r10-0xaa8], r8`) to -0xaa8 and r9 (h, arg-r4 +0x10) to -0xab0.
Ours is the reverse. Binding `base_mint` once does not change it.

Note: reconstruction/harness/win.py `show` crashes on this toolchain's objdump (it parses the
hex label line as decimal slot index); diffs were taken with a direct llvm-objdump + difflib compare.
