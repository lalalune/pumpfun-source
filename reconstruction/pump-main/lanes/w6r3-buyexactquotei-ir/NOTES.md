# w6r3-buyexactquotei-ir: 0x13f630 buy_exact_quote_in normalized match on main 6484b28

Target: `0x13f630` `pump_recovered::buy_exact_quote_in_v2` (handler `buy_v2::buy_exact_quote_in_handler`), 20,184 B.

| | base origin/main 6484b28 | this branch |
| --- | --- | --- |
| target bytes | 20,216 | 20,184 (original size) |
| target ratio | 0.99635 | 1.0 (slots_diff 0, normalized equal) |
| official normalized / raw | 1027 / 293 | 1028 / 293 |
| gains / losses | | `0x13f630` / none (raw losses none) |
| unstripped sha256 | | `7ec420ec6bb52548ebfe84516da1d75dae00e1af3333b66809ae81f681a0a5d0` |

## Mechanism

Port of PR #2269 (w7r1-buyexactquoteinh-regsched, built on #2240's program-fn form) onto
current main, which since gained the pinned `ordered.ld` link order (#2251) and other merges.
The diff applied cleanly and needed no `ordered.ld` regeneration (the handler is a local item):

1. `buy_exact_quote_in_handler` is `#[inline(always)]` and the program fn
   `pump_recovered::buy_exact_quote_in_v2` is `#[inline(never)]` (the original window is the program fn).
2. The Complete-if and `prepare_bonding_curve(..)?` are inline in the handler tail, with
   `drop(ev)` after `emit_cpi!(ev)` (TradeEvent not live across Complete/prepare).
3. `partial` is passed by reference (`&partial`, `*partial`): the program-fn local gets an alloca
   that survives early SROA and is removed in the post-inline SROA before `shareholders.i`, so
   PromoteMem2Reg yields the original [cap, ptr, len] phi order and the `mov r7,2` copy is
   scheduled first, as in the original.

No runtime behaviour change (by-ref vs by-value bool, inlining attributes, scope of `ev`).

Raw: the window is not raw-equal; all 179 differing slots are internal `call` displacements (130)
and section-pointer `lddw` (49), i.e. layout of other still-unmatched windows.

Ledger: attempt `98e2a07cab034f83bd247895341e29f4` (dedupe `0x13f630-main-6484b28-pr2269-port-v1`).
