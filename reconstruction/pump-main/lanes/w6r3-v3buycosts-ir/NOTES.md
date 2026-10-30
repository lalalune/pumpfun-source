# w6r3-v3buycosts-ir: `trade::v3_buy_costs` (0x80df8)

Base: origin/main 6484b2837 (1027/1035 normalized, 293 raw).

## Result: the target is already solved by open PR #2272. This lane verified it on the current main.

Before writing a new IR-oracle loop, the ledger showed that open PR #2272
(`swarm/w7r1-v3buycosts-blockorder`) reached a normalized match on a418dd3. That PR joins
both `add3` Err arms through a labeled block, then applies one `?`. Siblings #2286 and #2290
reproduced it. This lane applied the same two-line `trade_v3.rs` change to 6484b28:

| | base 6484b28 | + #2272 source |
| --- | --- | --- |
| 0x80df8 bytes (orig 2,120) | 2,136 | **2,120** |
| ratio / slots_diff | 0.920 / 19-21 | **1.000 / 0** |
| official normalized / raw | 1027 / 293 | **1028 / 293** |
| gains / losses | | gain `0x80df8`; 0 normalized, 0 raw losses |
| unstripped sha256 | | `2ef4591161dc00f70fa7402b9a2b83607dcd2c404a6aa0e8f4fbcd3c6473ee64` |

`git merge-tree origin/main origin/swarm/w7r1-v3buycosts-blockorder` is clean, and GitHub reports
#2272 as MERGEABLE (not draft). **Action: merge #2272.** This branch does not carry the source
change, so the gain is not duplicated.

## Raw residual (analysis)

The candidate `v3_buy_costs` sits at 0x89b60, not 0x80df8: unmatched windows earlier in `.text`
still shift it. Comparing raw bytes slot by slot at the two addresses gives 30 differing slots:
16 `lddw` (section pointers) and 14 pc-relative `call` (17 calls in all; the other 3 have equal
immediates). All 30 depend on addresses. No instruction, register or stack-offset byte differs. Raw for this
window therefore depends only on layout and needs no further source work here.

Ledger: `0x80df8-main-6484b28-labeled-block-add3-pair-join-rebase-verify-v1` (attempt 5284dbde).
