# Lane w10r1-admincto-stitch (wave 10, round 1)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`). Angle: stitcher/integrator.
Collect the admin_cto edits of the w10 region lanes, the other admin_cto lanes and the x/y lanes, combine
compatible edits, build, score, keep the best composite.
Builds and scratch: `~/.cache/pumpfun-reconstruction/lanes/w10r1-admincto-stitch/` (tools/ there: token-level
3-way merge `merge3.py`, gene sweep driver `gs.py` reusing the hillclimb lane's gene library, call-sequence aligner
`calls.py`, llc oracle `orc.py`, branch-weight sweep `bsweep.py`).

## Current result (base: origin/main bf0b20087, which includes #2524 at 27,400 B)

| metric | main bf0b200 | this branch | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 | 27,400 |
| slots_diff | 3,297 | 3,297 | 0 |
| ratio | 0.36010 | **0.36099** | 1 |
| calls | 154+3 | 154+3 | 154+3 |
| official normalized / raw | 1033 / 1033 | 1033 / 1033 | |
| gains / losses (norm, raw) | | 0 / 0, 0 / 0 | |

Change: the curve-store block writes `is_holder_reward` before `creator` (gene `curve_swap_754_755` of the
hillclimb lane's library, re-applied on the new main). Same stores, same values, no error site moves.

## Stitch log

1. Old main 917ee615 (27,344 B, 0.37637): rebased onto #2509 (ql_before_shared, 27,400 B, 0.358). Composites with
   region2of6 t6, region6of6 do_collect, #2416 validate take(), cpi with_signer and to_ifexpr: every pair moved the
   size off 27,400 (27,144..27,552). Size effects are not additive. Best ratio: to_ifexpr + region6 (0.39036 at 27,440).
2. #2524 merged (27,400 B, 3,297 slots). The lane edits re-applied on it: r6 27,528 / 0.37448, r2 27,408 / 0.36064,
   toif 27,464, ql_before_shared 27,472, with_signer 27,472, r2+r6 27,584, cpi+r6 27,560: all off size (686 raw losses).
3. Single-gene sweep on the new main (knob library): curve_swap_754_755 27,400 / 3,297 / 0.36099 (kept),
   ev_clock_first 27,400 / 3,297 / 0.3571; the others move the size.

## Analysis (llc oracle on main's post-opt IR)

- Call-sequence alignment (`calls.py`): orig = [validate+410][sweep head][sweep tail: amm 660, transfer_creator_fees,
  Rent::get][post-sweep: sharing_config, pool, event][native/token/wallet]; ours places the post-sweep before the sweep tail.
- Branch-weight sweep over all 144 conditional branches (2000:1 each way, greedy 6 rounds): most layout-sensitive are the
  sweep.exit Result re-check, wallet `executable` test, 306 let-else None test, sweep amm `token_frozen` Ok test,
  Rent::get tag test; 6 rounds reach 0.4917 (27,424 B). IR-only, not a proposal.
