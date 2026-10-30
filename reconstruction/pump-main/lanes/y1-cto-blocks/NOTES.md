# y1-cto-blocks: local permutation search on admin_cto::execute (0x22a10)

Base: main dce6faf97 (program sources equal to 0bcf7223c). Baseline score:
`pump-main-swarm/y-baseline/0bcf7223c/score.json` (1032 normalized / 347 raw).

Driver: `genes.py` (line-count-preserving, semantically equivalent source permutations;
no error!/require! site changes line) and `run.py` (2 workers, 1 cargo job each, builds
with fastbuild.py, scores target_metric.py + score.py, records each variant in the ledger
under approach `blocks`, keys `0x22a10-dce6faf97-blocks-<mech>-v1`). 53 builds in total.

## Result (committed)

Three permutations together:

- `t-store-hr-cb-swap`: store `curve.is_cashback_coin` before `curve.is_holder_reward`
- `s-token-frozen-first`: in sweep's token path read `token_frozen` before `token_raw_amount`
- `s-old-before-bump`: in sweep, `let old=current_creator.key()` before `let bump` (the
  region2of6 lane found the same order earlier, measured on its own base)

| | main | this branch |
| --- | ---: | ---: |
| admin_cto size (orig 27400) | 27344 | **27400** |
| admin_cto ratio | 0.37637 | 0.36459 |
| calls (internal, syscall) | 154, 3 | 154, 3 |
| score.py normalized | 1032 | 1032 |
| score.py raw | 347 | **1032** (+685) |
| losses / raw losses | | 0 / 0 |

Candidate sha256 prefix 1e79f0ddcbde. The store swap by itself is enough for the
original size and the +685 raw: every function after admin_cto moves back to its
original address. Open PRs #2509, #2524 and #2528 reach the same size by other mechanisms.

## Single-gene measurements on main (ratio, size)

Ratio up: v-none-check-is-some 0.37983 (27448), t-store-creator-hr-swap 0.37757,
s-token-frozen-first / s-old-before-bump / t-store-perm-HBC / t-store-perm-BHC 0.37667.
Original size 27400: t-store-hr-cb-swap 0.36399, t-store-perm-BCH 0.36339,
t-ev-new-locals 0.32534. Byte-identical: about 15 genes (operand order of
side-effect-free &&, ==, require! spelling, >0 vs !=0, if/else polarity of empty
arms). Each combination with v-none-check-is-some moves size away from 27400
(best ratio 0.38432 at 27448).
