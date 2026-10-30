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

## Result so far

| metric | main 917ee615f | this branch | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,344 | **27,400** | 27,400 |
| ratio | 0.37637 | 0.35800 | 1 |
| slots_diff (equal size only) | n/a | 3,361 | 0 |
| calls | 154+3 | 154+3 | 154+3 |
| official normalized / raw | 1032 / 347 | **1032 / 1032** | |
| gains / losses (norm, raw) | | 0 / 0, **685** / 0 | |

Mechanism (gene `ql_before_shared`): `quote_locked` (`global_quote(bonding_curve.quote_mint, &global)`)
is computed before `shared` instead of after it. The function reaches the original size exactly, so
`.text` has the original length and every later function sits at its original address: 685 windows
become raw matches (all 1,032 normalized windows are now raw). Ratio falls 0.376 -> 0.358, which
the size-first ranking accepts.
