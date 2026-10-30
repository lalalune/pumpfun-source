# x1-p2-post-fill-global-before-curve-stores

Target: swap_hop (0x5b3b0). Base: origin/main e61baa928, where #2403's &Context swap_hop is already merged.

Change: in the `if let Some(post)=post_fill.as_ref()` branch, bind `let global: &Global = &a.global;`
before the `post_complete_base_out`/`post_complete_quote_in` stores and pass `global` to `accrue_fees`.
The `a.global` Box load (`ldxdw r1,[r10-0xa48]; ldxdw r3,[r1]`) now comes before the two curve stores,
as it does in the original at 0x5d8f8. The binding sits on the existing `if let` line, so line numbers are unchanged.

| build | swap_hop ratio | bytes | slots_diff | normalized / raw | losses vs control |
|---|---|---|---|---|---|
| control (e61baa928) | 0.85352 | 18584 | 1023 | 1032 / 347 | - |
| v1 let-global binding (kept) | 0.85439 | 18584 | 1023 | 1032 / 347 | none / none |
| v2 #[inline(always)] apply_post_fill helper | 0.85439 | byte-identical to v1 | | | |
| v3 v1 + `let bc=&mut h.bonding_curve` | 0.85439 | byte-identical to v1 | | | |
| v4 one global binding hoisted before both accrue_fees | 0.81741 | 18576 | | 1032 / 337 | 10 raw losses (rejected) |

The local residual at this site is the original's re-spill `stxdw [r10-0xab0], r1` of the reloaded curve pointer,
between the two stores, plus frame-wide spill-slot offsets. Neither source binding order reproduces that re-spill.
