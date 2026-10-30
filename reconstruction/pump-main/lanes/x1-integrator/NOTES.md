# x1-integrator (round 1)

Base: origin/main c8dcbbcf7. Its fresh build scores normalized 1033, raw 1033 against the shared
1852a872e baseline (gain 0x1e7c0, 696 raw gains, 0 losses), sha 89f8069932c2. On this main:

| window | main c8dcbbcf7 |
|---|---|
| 0x1e7c0 create_v2::execute | 1.0, normalized and raw equal (#2529) |
| 0x5b3b0 swap_hop | 0.98907, 127 slots, 18,584 B (#2611) |
| 0x22a10 admin_cto::execute | 0.3601, 27,400 B (#2524) |

Main moved past every verified round-1 branch, so this branch merges none of them. Every port
below has 0 losses against the shared baseline but loses raw windows against current main, so all
were dropped:

| trial | admin_cto / swap_hop | vs main |
|---|---|---|
| x1-sroa-debug-requeue-trace | already matched on main (#2529) | n/a |
| x1-p2-* swap_hop branches (fees-whole, cap-qm09, post-fill-global) | already on main or superseded by the 0.98907 source | n/a |
| completefill None-first `match` | swap_hop 18,576 B, 0.98054 | 696 raw losses |
| cashback late eval (`!holder&&cashback` at the curve store) | admin_cto 27,280 B, **0.39604** | 686 raw losses |
| sweep g (transpose gate + native passthrough) | admin_cto 27,416 B, **0.43816** | 686 raw losses |
| sweep g + cashback | 27,304 B, 0.31032 | 686 raw losses |
| sweep e only (passthrough, if-gate kept) | 27,416 B, 0.38934 | 686 raw losses |
| sweep b only (transpose gate) | 27,384 B, 0.3602 | 686 raw losses |

Sizes do not add up: on main, b is -16 B and e is +16 B, but b+e (g) is +16 B, and g+cashback is -96 B.
Both admin_cto levers raise the ratio but break the exact 27,400 B size, so each needs a size-neutral companion.

Ledger keys: `0x5b3b0-main-c8dcbbcf7-x1int-*`, `0x22a10-main-c8dcbbcf7-x1int-*`.
Tool: ~/.cache/pumpfun-reconstruction/lanes/x1-integrator/tools/trial.sh (scores against both the shared baseline and the main build).
