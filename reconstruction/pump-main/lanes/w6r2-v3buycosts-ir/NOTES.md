# Lane w6r2-v3buycosts-ir: `trade::v3_buy_costs` (original 0x80df8, 2,120 B)

Base: origin/main a7135a6a6 (1027 normalized / 276 raw). **The source is unchanged.** This PR holds analysis and
oracle tools only. The target is still 2,136 B, ratio 0.920, with a 9/11-line residual against the one-function
llc oracle: the sret pointer is split into r6 where the original spills it everywhere and reloads it into r3.

## New findings

1. **Branch hints from source never survive on this toolchain.** A `-Cno-prepopulate-passes` capture
   (`capture_noopt.py`) shows that `checked_add` really does emit `llvm.expect.i1(%overflow, false)` through core's
   `unlikely!`. rustc 1.79 routes every intrinsic result through a temporary alloca (zext/store/load), and
   LowerExpectIntrinsic runs before SROA, so the hint is dropped. Only a MIR `Assert` gives `!prof`. Any surviving
   checked-op hint would also make the error paths colder, the wrong direction for the line-375 leak. So the
   wave-4 "needs a weight" rule cannot come from source, and the residual must be structural.
2. **Code-neutral structure does move the sret split.** Lifetime markers on the ZST alloca (from the LLVM-inlined
   `protocol_fee_split`) keep otherwise-empty MBBs alive until RA. Deleting only `bb4`'s `lifetime.start` (second
   split, mayhem && Some) gives the original's spill-everywhere and r3 reloads at 2,120 B. The cost is a different
   front allocation (-51/+51).
3. **Exhaustive code-neutral scan, with no result.** Every single, pair and triple drawn from {35 marker deletions,
   43 lifetime-only edge-split blocks} was tried: 76,076 triples plus all singles and pairs. Nothing beats the base
   9/11 except layout-only jlt/ja to jge folds. Marker or empty-block structure alone cannot reach the original.
4. **The front and the sret split are coupled.** Three results show it:
   * In source, guarding both splits outside (`if is_mayhem!=0{0}else{split(..,false).0}`, p08) gives a late
     region and sret RA that match the original exactly: entry spill, r3 at both tails, no duplicate block. The
     front changes, though: 2,112 B, 0.873.
   * Inverting the post-None flag phi in the base IR (`flipbase`) also fixes the sret, and also turns the front
     into the p08 shape.
   * Inverting p08's flag back to the original polarity fixes the front almost entirely (2,128 B, -20/+21) but
     brings the r6 split back.
   So far, every change that fixes one side breaks the other.

## Source trials (all 1027/276, no gains or losses)

| trial | mechanism | result |
| --- | --- | --- |
| p01/p02 | `protocol_fee_split` `#[inline]` / no attribute | byte-identical |
| p03/p04 | unconditional second split on `post fee or 0` | 2,096 B 0.743 |
| p05 | both splits via one local closure | identical |
| p06 | `is_mayhem!=0` bound once | identical |
| p07 | outer mayhem guard on the second split only | 2,160 B 0.449 |
| p08/p10 | outer mayhem guard on both splits | 2,112 B 0.873 (sret correct, front wrong) |
| p09 | outer guard on the first split only | 2,136 B 0.872 |
| g_* (10) | outer-guard family × second-arm spellings (`gen_outer_mayhem.py`) | 2,056-2,136 B, at most 0.873 |
| p11/p12 | `protocol_fee_split` single-exit if/else, negated guard | identical IR |

## Next ideas

* Search source shapes that give the *original-polarity* (isNone) flag together with the p08-style CFG, where
  the mayhem path tests `post` itself instead of inheriting a phi.
* A MIR-level oracle (`llc -start-before=greedy` on edited `.mir`) to isolate which interference in the front
  decides the split. It can find a target property, not a spelling.
* Otherwise, treat 0x80df8 as blocked.

Tools: `lscan.py` (marker deletions), `escan.py`/`escan_lib.py` (lifetime-only edge splits), `mscan.py`
(mixed combos), `capture_noopt.py`. They are used together with `../w4-v3costs/oracle/{mkone,irexp,fn.sh}`.
