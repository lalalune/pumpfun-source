# Lane v3trade-coordinates

Targets: V3 trade handlers in `programs/pump/src/trade_v3.rs`.

## Coordinate archaeology

`coords.py window` vs `coords.py fn` on baseline d2cb88d: every Source{file,line} site in all
three windows already sits on its original line (buy 801/802/842; sell 1126/1127/1148;
buy_exact_quote 881/882/891/926/1001/993/935/971). Line placement is not the residual; slot
offsets differ (code shape before each site), e.g. buy_v3 first site at slot 1208 vs 1144,
buy_exact_quote 891 at 1752 vs 2296.

## Trial t01: port `sell-inline-quote-options` (e38 packet) onto main

Mechanism: `TradeFees` passed by reference into `trade_event`/`v3_emit_buy` (instead of a
4-tuple), inline `if is_sol{None}else{Some(..)}` quote-account args at each payment call,
`init_volume_user` helper, `emit_sell_cpi` helper, `v3_buy_costs` unconditional
`protocol_fee_split` + inline `pre_fee_amount`. The multi_hop_curve_swap hunk was re-applied by
hand (main had split the `Clock::get()` timestamp out).

| window | before (d2cb88d) | after t01 |
|---|---|---|
| 0x14a8a8 sell | 6056 B, ratio 0.443 | 6040 B, ratio 0.950 |
| 0x147ba0 buy | 3800 B, ratio 0.544 | 3712 B, ratio 0.645 |
| 0x1489f8 buy_exact_quote | 7800 B, ratio 0.303 | 7656 B, ratio 0.313 |

Official: normalized 1019, raw 188, gains [], losses []. unstripped sha256
a64a2f8ad78f5d3e2aa71c577f2b57c6b46a1f7b54fde1340b58ba3ea47bb61b. Ledger a45227c77891401a8631b2571d4cc63b.

## Trial b04: buy_v3 guard with scoped user key (adopted)

`let mut excess=0; let amount={let user_key=a.user.key(); if mayhem {if partial_fill{amount.min(real)}else{amount}} else if user_key!=a.global.whitelist_pda && amount>real {excess=amount-real;real} else {same clip}};`

The e38 `event-fees-volume-guard` shape (b01, ratio 0.706) bound the key at function scope, so
it got its own 32-byte stack slot and shifted every frame offset by 0x20. The original stores
the key in the -0xa8 temporary area that later calls reuse, i.e. the key is short-lived. Scoping
it inside the block expression lets stack coloring reuse the slot: frame offsets now match.

| window | t01 | b04 |
|---|---|---|
| 0x147ba0 buy | 3712 B, 0.645 | 3728 B, 0.849 |

Official 1019/188, no gains or losses. unstripped sha256 8336a2200d8502bf8dded3bd2286032a9255112ec466c7b3fd30ae08c3a0e009.
Rejected this round (ledger): single if/else-if chain (b02, b05), mutable-amount chain (b03),
precomputed `whitelisted` bool in either operand order (b07-b09), sell tail-expression
`emit_sell_cpi(..)` (t02: structurally closer but r8/r9 swap, 0.860), user/source quote Option
locals (s03-s05).

Remaining buy_v3 residuals: the original loads `a.global` before the key copy and shares one
partial-fill min clip between the mayhem path and the not-crossing path; the epilogue store/exit
is placed once at the end (ours duplicates it in the middle).
