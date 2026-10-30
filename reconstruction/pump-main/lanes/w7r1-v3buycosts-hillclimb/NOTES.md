# Lane w7r1-v3buycosts-hillclimb: `trade::v3_buy_costs` (original 0x80df8, 2,120 B)

Base: origin/main 2162b3b00 (official 1027 normalized / 276 raw; v3_buy_costs 2,136 B, ratio 0.920, 17/17 calls,
function sha256[:16] d73adf73aff7ddce). **No source change proposed.** The target was matched (normalized) during this
run by the sibling lane w7r1-v3buycosts-blockorder (PR #2272, add3 pair in a labeled block with `break`), so the lane
stopped at that point.

## Method

`tools/mutgen.py` is a spelling grammar for the function body with 7 dimensions (front buyback/post_buyback, the
line-371 total_buyback check, `first` add3, `second` add3, the line-375 net check + pre_fee, the gross-up tail,
statement order). It renders lines 365..377 so both `error!()` sites stay on 371/375 and no other line moves.
`tools/hc.py` builds each configuration with fastbuild.py (2 parallel builds, shared slots) and measures 0x80df8 with
target_metric's `measure_window`; `tools/ledger_rec.py` records every configuration in the ledger
(`0x80df8-main-2162b3b-hc-<config>-v1`, approach `mutation-hillclimb`).

## Results (79 configurations, 46 distinct function bodies)

* All 47 one-dimension neighbours of the base were built, plus 27 pairwise combinations of the best non-identical
  singles. **The base is a strict local optimum**: no neighbour or pair improves ratio, size or slots.
* 29 configurations are byte-identical to the base function: all front spellings (if-let, map_or, map/unwrap_or,
  unwrap_or_default, destructuring, tuple, closure, nested `fn` with #[inline] / no attr / #[inline(always)],
  `is_mayhem>0`), let-else / match / if-let / overflowing_add / ok_or(()).map_err for line 371, match for 375,
  map_or(Ok(0)) for second, let-else / closure / tuple-inline gross-up tail.
* Best non-identical: N1 (`?` then separate `pre_fee_amount(..)?`) and N12 (Result bound then `?`) 2,136 B 0.916;
  B1/B4 (match for second) 2,144 B 0.914; N3 (gross_up_quote helper) 2,128 B 0.914.
* Size 2,120 B was reached only with wrong layout: O1 (both add3 before total_buyback) 152 slots, A1+N1 209 slots.
* Explicit `match` instead of `?` on an add3 result (A1, B5) costs a lot (2,176 B 0.741): it restructures error edges.
* Nested `#[inline(never)]` helpers (FWx, FBx) outline code (13/16 calls).

## Insight

The single-statement spelling space of this body collapses to a few IR shapes and none flips the sret tie. The fix
found by the blockorder lane (grouping both add3 calls in one labeled block so their error tails merge before `?`)
is a cross-statement control-flow restructuring that this grammar did not contain: a hill-climb over local spellings
cannot reach it. Future mutation grammars should include block-grouping operators (labeled blocks, shared `?` over
grouped Results, closures returning Result over several statements), not only per-statement rewrites.
