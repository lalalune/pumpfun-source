# w10r1-swaphop-region1of4: 0x5b3b0 multi_hop_curve::swap_hop, region 1 of 4 (bytes 0x0..0x1226)

Base: origin/main e61baa928 (fresh build 1032/347, zero losses). swap_hop 18,584 B (= original), ratio 0.85352, slots_diff 1023.

## Region census (difflib alignment, matched original instructions per quarter)
| region | base | IR oracle `gep_up` |
|---|---:|---:|
| 1 [0x0,0x1226) | 563/574 | **573/574** |
| 2 [0x1226,0x244c) | 431/571 | 452/571 |
| 3 [0x244c,0x3672) | 416/572 | 424/572 |
| 4 [0x3672,0x4898) | 542/570 | 550/570 |
| ratio | 0.85352 | **0.87407** |

## Region 1 residual: no region-1 statement causes it
Region 1's statements (prepare_curve through the buyback recipient check) already compile to
the original instructions. The 11 unmatched instructions are:
- 3 jump offsets whose targets lie in regions 2 and 3;
- 8 accesses to one swapped pair of spill slots, -0xaa8 and -0xab0: the flag&2 value plus the `[h+0]` pointer, against the bonding-curve data pointer `h.val`.
  The same pair is swapped through the whole function (about 40 slots). The `tools/swapsim.py` swap alone gives 0.85352 -> 0.86445.

Mechanism: StackSlotColoring gives the lowest free spill frame index (FI) to the interval with the highest weight, where weight is the
sum of the block frequencies of its references. Pre-coloring weights, from llc `-print-machine-bfi` and the MIR:
the flag&2 slot is 0.087891 and the curve-pointer slot is 0.088132. The curve pointer wins only because of a re-spill
that only the candidate has, in region 2 (bb80, cand 0x17d0 `stxdw [r10-0xaa8], r9`, freq 0.00069). Without that re-spill
the order flips to the original's.

## Cause of the re-spill (region 2, just past this region's statements)
buy_fee_market_cap's curve argument `%_136 = gep %h.val, 8` (Account<BondingCurve> -> &BondingCurve) sits at the call.
The original computes it (`ldxdw r6,[slot]; add64 r6,8`) between the two Rc decrements that drop the
fee_config AccountInfo temporary. llc oracle: moving that single GEP above the fee_config clone
reproduces this placement after MachineSink. Region 1 then matches (1 jump residual), and every region improves (table above).

## Source spellings tried
| trial | result | ledger |
|---|---|---|
| `let c: &BondingCurve = &h.bonding_curve;` (complete_fill gets `&h.bonding_curve`) | byte-identical: MIR rebuilds `&(*box).0` at the call, so the early deref is dead | 356cef63 |

Known dead ends (ledger): c-deref-once/twice (still &Account), fee-config-len-after-cap (changes call order),
fee-config-ai-bind.

## Next ideas (for the region-2 owner or a stitcher)
Find an ordinary spelling whose `&BondingCurve` for the cap call is a value produced before the
fee_config clone and that the MIR does not rebuild at the call site. Examples: a plain helper taking
`(fee_config, curve: &BondingCurve, mint)` and returning `(len, cap)`, which LLVM rather than the MIR inliner inlines;
or a binding that a call before `fee_config_len` consumes by value.
Target signature: `gep h.val,8` dominating the fee_config `AccountInfo::clone`.

Tools (outside git): ~/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-region1of4/tools/{rd.py,rbin.py,sscw.py,swapsim.py,variant.sh}
and orc.py/extract.py/capir.py copied from w7r1-swaphop-regsched. Ledger: 02357b01 (oracle), 356cef63.
