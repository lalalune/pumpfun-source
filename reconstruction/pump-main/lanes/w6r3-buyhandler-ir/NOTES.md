# w6r3-buyhandler-ir: 0x13b9b8 `buy_v2::buy_handler`

Base: origin/main 6484b2837 (1027/1035 normalized, 293 raw; target 15512 B vs 15480 B, ratio 0.97998).

## Result

The normalized match from PR #2225 (lane w7r1-buyhandler-inline, built on 6edd839) still holds
on current main, which since gained the pinned sibling link order (`link/ordered.ld`, raw 276 -> 293).
This branch cherry-picks that PR's two commits (fa924dda0, 8b8ebe781) unchanged onto 6484b2837
and re-verifies them. No IR-oracle work was needed: the IR-level residuals the lane was
spun up for were already solved by #2225.

| metric | 6484b2837 | this branch |
| --- | --- | --- |
| 0x13b9b8 normalized | false | **true** |
| target bytes (orig 15480) | 15512 | 15480 |
| ratio / slots_diff | 0.97998 / - | 1.0 / 0 |
| calls (orig 90) | 90 | 90 |
| official normalized / raw | 1027 / 293 | **1028 / 293** |
| gains / losses / raw losses | - | [0x13b9b8] / none / none |
| unstripped sha256 | - | 70d96eb8aaeba80280ad644d198532a60c7f070836e04a984694dfc6a9aaa0ff |

Built twice (working-tree apply and the committed cherry-picks): same sha256.
The matching symbol is `pump_recovered::pump_recovered::buy_v2` (candidate 0x144f30); the window
is not raw because of global placement (call/lddw displacements), not function content.

## Behaviour

No runtime change: `complete_and_prepare`'s body is copied inline verbatim, `drop(ev)` after
`emit_cpi!` only ends a borrow-free value early, the TradeEvent literal reorders side-effect-free
field selects, and the fee tuple swap only renames the binding order (`(cf,pf,..)`).

Ledger: ab71d9bdec2a4a8c9038bdaa8172bbb9 (`0x13b9b8-main-6484b28-port-pr2225-v1`).

Merge note: this branch and #2225 carry identical source; merge one of them only.
