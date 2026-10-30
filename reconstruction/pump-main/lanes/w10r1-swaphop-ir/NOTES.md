# w10r1-swaphop-ir: 0x5b3b0 multi_hop_curve::swap_hop (IR oracle)

## Round 1 (base x1-p2 on main 37f32a4f2)
Source found by the llc oracle: `match complete_fill(..)? {Some=>..,None=>..}` (0.93048) and
`let global = &*a.global;` bound first in the line-599 `allowed` block (0.93747, 18,584 B, 0 losses).
The stitch lane (#2558, #2574) has since merged an equivalent composite, so main now carries the
global-first spelling. This branch is notes-only on top of main b19d43e59.

## Round 2 (main b19d43e59: 18,584 B, ratio 0.97551, 1033/1033)
The oracle (`tools/orc.py`, llc on the extracted post-opt swap_hop) reproduces the build exactly.
`tools/irclimb.py` hill-climbs IR edits (block moves, within-block instruction moves, icmp/br polarity).

| oracle edit on main IR | bytes | ratio |
|---|---:|---:|
| none (main) | 18,584 | 0.97551 |
| complete_fill tag `icmp eq 0` (= source `match complete_fill(..)? {Some,None}`, built: identical) | 18,576 | 0.97048 |
| + None-arm JumpThreading block `bb73.thread50` moved after the uadd join | **18,584** | **0.98207** |
| climb alone: bb274 (complete_fill Err) after join + bb275 moved +2 | 18,584 | 0.98164 |

No single polarity flip or within-block instruction move improves at equal size.
The None thread block placement decides whether the raw_output overflow closure block (orig 0x28b0)
is laid out right after the checked_add, as in the original. JumpThreading always inserts the thread
block before bb73, so a source spelling has to change what is threaded.

Rejected source spellings (main base): explicit `match complete_fill(..) {Ok(Some),Ok(None),Err}` in
three arm orders (18,536 B); raw_output via map_or / if let / None-first match / map.unwrap_or on s1
(18,576 B); post_out as a fifth tuple element (18,664-18,672 B).

## Remaining residual (after the 0.98207 oracle)
post_fee_amount and get_fees `?` polarity (0x18f8, 0x1a18), get_fees argument schedule (0x19a8),
599 error result load order (0x23f8), complete_fill `global+8` arg placement (0x29f8), the
13-instruction adapter_difference/post_fill copy block placement (0x2d10 vs 0x2e38), polarity at 0x3e00.

Ledger: 8f7a8860, 5d99494c, 11cf2079, d550791e, 80093646, 67cd80dc, 7e82a1d1, de93c880, ff326106.
