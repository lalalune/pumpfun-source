# x2-hop-none-first-plus-8b (round 2)

Target: 0x5b3b0 `multi_hop_curve::swap_hop`. Base: origin/swarm/x1-integrator 678c7ea0b
(programs identical to main c8dcbbcf7: 0.98907, 127 slots, 18,584 B).

## Result

| build | change (on base) | bytes | ratio | slots | norm / raw vs 1852a872e baseline | raw losses vs main build |
|---|---|---|---|---|---|---|
| base | - | 18,584 | 0.98907 | 127 | 1033 / 1033 | - |
| x1-integrator t1 | complete_fill `match` None-first | 18,576 | 0.98054 | - | 1033 / 337 | 696 |
| v1 | t1 + `let mut trade_amount=amount; if buy {trade_amount=post_fee?;}` | 18,576 | 0.9075 | - | 1033 / 337 | 696 |
| v2 | t1 + `match buy as u8 {1=>post_fee?, _=>amount}` | 18,568 | 0.9077 | - | 1033 / 337 | 696 |
| v3 | t1 + trade_amount and adapter_difference moved inside the buy arm | 18,576 | 0.9836 | - | 1033 / 337 | 696 |
| v4 | v3 without None-first | 18,584 | 0.99213 | 89 | 1033 / 1033, 0 losses | 0 |
| **v5** | **v3 + reserves if flipped to `if base > reserves {complete path} else {(base,q,nf,None)}`** | **18,584** | **0.99913** | **18** | **1033 / 1033, 0 losses** | **0** |
| v6 | v5 + `let global=&*a.global` hoisted and passed to complete_fill | byte-identical to v5 | | | | |

Committed: v5 (unstripped sha256 prefix 345e98ab0e).

## Mechanism

1. `trade_amount = post_fee_amount(..)?` and `adapter_difference = amount.checked_sub(..)..?` are now
   computed inside the buy arm of the `(fees, ..) = if buy {..}` (the sell arm never used
   trade_amount). There is no longer an `else {amount}` block that creates the join before
   post_fee_amount's successors. This alone reproduces the IR-oracle moves bb259-after-bb39 and
   bb262-after-bb43 from w10r1-swaphop-hillclimb: orig +0x18f8 `jeq r1,2,+1; ja` and +0x1a18 `jne r1,0`
   (v4: 0.99213/89).
2. complete_fill `match .. { None => .., Some(..) => .. }` fixes orig +0x2b50 `jeq r3,0,+0x1b`
   (-8 B on its own).
3. Flipping the reserves `if` to gt-first makes MIR RPO codegen the complete path (and
   complete_fill's Err block) after the raw_output carry test. That restores orig +0x28a0
   `jne r1,0,+1; ja +6` with the Overflow-closure block inline: the +8 B companion that None-first needed.

## Residual (18 slots)

The only remaining difference is the placement of `ldxdw r2,[r10-0xb28]; add64 r2,8` (the `&a.global`
complete_fill argument). The original puts it right after the whitelist memcmp test at +0x29f8; ours
puts it just before the call. Hoisting a `global` binding is byte-identical (v6). Lane
x2-hop-global-binding-into-complete-fill owns this site.

Ledger keys: `0x5b3b0-x1int-678c7ea0b-*`, `0x5b3b0-x2nf8b-v5-*`.
