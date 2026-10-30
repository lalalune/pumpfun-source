# Lane w10r1-admincto-hillclimb (wave 10, round 1)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`). Angle: automated
mutation hill-climb. Base: origin/main 917ee615f (1032/1035 normalized, 347 raw).

## Tooling

- `hc.py`: applies ordered gene sets (exact, line-count-preserving substitutions; every error-site
  line stays put) to `admin_cto.rs`, builds each variant in a cloned crate copy with two lane work dirs
  (the machine-wide 10-slot lock still applies), then runs `target_metric.py` and `score.py --baseline`
  against the lane's fresh main build. Fitness: equal call counts, then |bytes - 27400|, then slots_diff,
  then ratio; zero normalized and raw losses required. Every variant is recorded in the ledger
  (approach `mutation-hillclimb`, dedupe key `0x22a10-main-917ee615-hc-<variant sha>-v1`).
- `genes1.py`: round-1 genes (63): prologue order, `shared` spelling, holder/cashback forms,
  validate signature, sharing_update/collect_old forms, wallet/sweep signatures and gates, sweep
  internals, post-sweep CPI/curve-store/event forms.

## Round 1 on 917ee615f (superseded)

`ql_before_shared` (quote_locked before shared) reached 27,400 B and raw 347 -> 1032 (PR #2509 first version).
Main then merged #2524, which reaches 27,400 B by another route with fewer differing slots (3,297), and #2529
(1033/1033). The branch was reset onto main 1b1f71122 and the climb restarted there.

## Current result (main 1b1f71122)

| metric | main 1b1f71122 | this branch | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 | 27,400 |
| slots_diff | 3,297 | 3,297 | 0 |
| ratio | 0.36010 | **0.36129** | 1 |
| calls | 154+3 | 154+3 | 154+3 |
| official normalized / raw | 1033 / 1033 | 1033 / 1033 | |
| gains / losses | | 0 / 0 (raw 0 / 0) | |

Genes `curve_swap_754_755` (the curve-store block writes `is_holder_reward` before `creator`) and
`sweep_frozen_first` (the sweep's token branch reads `token_frozen` before `token_raw_amount`; both
deserialize the same account, so the error behaviour is unchanged). Each alone keeps 27,400 B and
slots 3,297 (0.36099 / 0.36040); together 0.36129. Unstripped sha256 8870aeed02e9c179...
