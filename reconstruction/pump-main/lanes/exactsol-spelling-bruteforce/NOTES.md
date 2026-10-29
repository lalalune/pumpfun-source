# exactsol-spelling-bruteforce

Target: `0x14f4e0` `pump_recovered::buy_exact_sol_in` (programs/pump/src/buy.rs, 13,224 B).

## Result: normalized match, zero losses

| metric | main d2cb88d | this branch |
|---|---|---|
| target slots_diff | 2 (0x1f58/0x1f60) | 0 |
| target ratio | 0.99938 | 1.0 |
| target bytes | 13224 | 13224 |
| official normalized / raw | 1019 / 188 | 1020 / 188 |
| gains / losses | - | [0x14f4e0] / [] |
| unstripped sha256 | 04fdafc0... | 43896614c48b0942490c55827d29b0b11b99c8994259ccdc9ebefe4873afe058 |

## Mechanism

The partial-fill arm computed `let total=quote.checked_add(protocol_fee).ok_or(Overflow)?.checked_add(creator_fee).ok_or(Overflow)?;`
on its own line and then `require_gte!(spendable_sol_in,total,TooMuchSolRequired)`.
The original passes the whole checked-add chain directly as the second macro argument, the same
style lib.rs:660-667 uses for the legacy `buy` TooMuchSolRequired site. `require_gte!` expands its
arguments twice (comparison and `with_values((a,b))`), so the error edge re-evaluates the chain;
LLVM CSEs the arithmetic but the error block's extraction/PHI order changes, giving the original's
tag-before-pointer load order after `Error::with_values`. Line 117 becomes a `// layout-pad`, so all
other Source lines are unchanged (133 and 143 sites stay put).

## Trials (ledger keys `0x14f4e0-main-d2cb88d-bruteforce-<variant>-v1`, attempts 1179-1194)

Byte-identical to main (canonicalized away): hand-if-return, arm-tail-ifelse, nested-if-flag,
quote-two-steps, fees-tuple, match-bool, arm-ret-tuple-ok.
Distinct but worse: cond-swap (12984 B), total-two-steps (13280 B, +1 call), cf-swap (13208 B),
total-closure / total-closure-andthen (~12980 B), amount-direct (13208 B), let-mut-reassign
(13224 B, 341 slots), arm-closure-try (closure outlined, 7 losses).
Match: total-inline-require (attempt 2f7682f221ab466c9ecbce775544d79a).

Generator and runner (not in git): `~/.cache/pumpfun-reconstruction/lanes/exactsol-spelling-bruteforce/{gen.py,run.sh,batch.sh}`.
