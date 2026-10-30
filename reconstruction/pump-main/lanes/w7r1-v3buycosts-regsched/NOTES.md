# Lane w7r1-v3buycosts-regsched: `trade::v3_buy_costs` (original 0x80df8, 2,120 B)

Angle: register-allocation and scheduling residuals. I built an llc oracle on our IR and searched IR permutations
that reach the original register assignment. Base: origin/main a418dd3 (1027 normalized / 276 raw; v3_buy_costs
2,136 B, ratio 0.920, 9 '-' lines on the one-function oracle). **No source change in this lane.** While this lane
ran, the sibling lane w7r1-v3buycosts-blockorder reached a normalized match (PR #2272, labeled-block break so that
both add3 errors leave through one Err arm). The last scan here confirms that mechanism independently from the IR
side.

## Oracle

`oracle/` (diagnostic only, never used for proposals): `capture_full.py` (lane-local `--emit=llvm-ir` build),
`mkone.py` (one-function module), `irexp.py` (edit + llc + diff vs `win.py orig`), plus new:

* `mut.py`: mutation generator and scorer. Classes are `commute` (commutative operands, uadd args), `icmpswap`,
  `invert` (predicate inversion with a successor swap, or xor-inverted branches), `move` (non-adjacent in-block moves),
  `phiord`, `phiinc`, `alloca`, `ltdel`, `esplit` (empty and ZST-marker edge blocks) and `bmove`. Each result
  carries a signature for the sret class: `E2/3` is the original (entry spill, two r3 reloads) and `e0/3` is the base
  (r6 split).
* `singles.py`: every single mutation. `beam.py`: beam search, which `SRET=1` constrains to the original sret class.
* `edits/`: hand edits. `flaggen.py` re-encodes the post flag, `errtail.py` / `errtail_sub.py` merge error tails,
  `sem.py` / `sem2.py` are equivalent arithmetic and test forms, `selflag.py` is a select-like mayhem flag, and
  `p08flip.py` flips the post-flag polarity of w6r2's both-outer-mayhem IR.

## Results (ledger rows a3588d4d, ea8fb72a, f9fb50d4, e555e157, b110c3bc, 9a401495, a8f10cea)

| Mechanism (IR level) | Result |
| --- | --- |
| 1,326 single permutations (commute, icmp swap, inversion, xor-inversion, phi order and incoming order, 626 in-block moves, lifetime deletions, edge blocks, block moves) | Only 4 flip the sret to the original class: xor-inverted is_mayhem branch (-34, 2096 B), commuted first uadd (-39), xor-inverted second null test (-51), bb4 lifetime deletion (-51). Each one reassigns the front. |
| Beam search (width 8-12, depth 3-4) from base, from the 4 flips and from the best flag variant, constrained to the original sret class | Plateaus at 27 / 18 '-' lines. |
| 66 alloca-order swaps | All stay in the r6 class. |
| Post-None flag as i8/i32/i64 phi + icmp eq/ne 0 (both polarities), pointer re-test, select-like mayhem flag | Every non-i1 encoding gives the original sret. 1-for-Some + `ne` is the closest at -19 (front: flag in r9 instead of r3, spill-slot order, expect_failed block placement). 1-for-None gives -48. Weights 1:3..11:9 on the i1 flag branch never flip it. |
| p08 (both-outer-mayhem) with flipped flag polarity | Front at -20, but the sret goes back to r6. |
| Equivalent arithmetic: i128 high-word try_from check, or.cond as two branches / swapped, add+icmp in place of uadd, usub.with.overflow, no `!range`, no `tail`, no call attrs | The late forms never flip the sret (-9 to -63). Front is_mayhem tests that lose the zero heuristic (trunc, xor, ult 1, sle 0) flip it, but reassign the front (-34..-36). |
| greedy llc knobs (diagnostic) | None reaches the original. csr-first-time-cost and priority knobs are inert. |
| All five error tails merged into one sret-store block (ret / .sink) | 2096 / 2104 B, front reassigned. |
| **Subsets of merged error tails** | **{add3#1 Err, add3#2 Err} and {add3#1, add3#2, 375/pre_fee} give 0 diff at 2120 B.** Adding the 371 or gross tail costs 1-2 lines. Any subset without add3#1 keeps the r6 split. Four or five merged tails reassign the front. |

## Key insight

The sret split is not decided by BPI panic leaks alone; that was the earlier waves' local model. It is decided by
the set of sret use blocks that greedy sees. Every edit that changes the front's MIR shape (flag encoding, mayhem
test, bb4) flips the sret, and it reassigns the front too, because the sret competes for r6-r9 there. The only edit
that changes nothing else is giving add3#1 and add3#2 one shared Err arm, which removes one sret use block from the
late region before RA. This is what #2272 does at the source level. The original therefore propagated both add3
errors through one Err arm.

## Next ideas

* Apply the same check to the other RA-tie windows: count sret / return-place use blocks at RA (`-print-before=greedy`)
  and merge error arms in the IR oracle before trying spellings.
* Blind spots to watch for: in-block instruction order and phi order never mattered here; use-block structure did.
