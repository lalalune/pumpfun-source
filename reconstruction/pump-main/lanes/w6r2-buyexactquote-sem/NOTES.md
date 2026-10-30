# Lane w6r2-buyexactquote-sem (wave 6, round 2)

Target `0x1489f8` `trade::buy_exact_quote` (v3), original 7856 B. Base origin/main a7135a6a6 (1027 normalized / 276 raw):
7872 B, ratio 0.85100 (llc masked 0.9675), 66/66 calls.

**Best (r6): ratio 0.98950, 7856 B (the original's size), 952/952 insns, 66/66 calls; only 10 stack-offset slots differ.
Official 1027 / 293 on origin/main e3f3be8bb, no gains or losses.** Steps: y2 0.95643 (`68659d27`), z3 0.96537 (`8d5be622`),
u2 0.97218 (`4bb7f0f6`), pb_b2 0.97428 (`3ed56f74`), r6 0.98950 (`2f3cb468`).

## Mechanism

1. Block-level diff: after the non-whitelist `tokens_for_quote(curve,net)?` the original loads the payload word `[8]`
   before the tag branch (like the whitelist call) and both error edges tail-merge into one block. Ours loads it in each
   successor. llc oracle (hoist that load): 0.8510 -> 0.8813.
2. Why: LLVM SROA types the TradeFees slice that overlaps the `Err` Box pointer as `ptr`. In the base the `ptrtoint`
   lands at the definition of the MIR-SROA fragment `_539` (inner `net_fees`), InstCombine sinks it to the head of the
   `Ok` block once the empty forwarding block is gone, and that leading `ptrtoint` blocks SimplifyCFG's common-load hoist.
3. Raw-IR oracle (`--emit llvm-ir -C no-prepopulate-passes`, then `opt -O3` reproduces the base byte for byte): LLVM
   SROA pops allocas LIFO, i.e. lowest MIR local first. Splitting `fees` (_68) and the outer `net_fees` (_70) **after**
   `_85` / `_539` / `_525` gives 0.9543 (and fixes the r6/r9 rotation that wave 6 round 1 attributed to the lifetime-only
   error block). Moving only one of them: 0.69.
4. Source lever: make both locals address-taken until LLVM inlining. A plain helper that contains a call is not
   cross-crate-inlinable, so the MIR inliner leaves it alone and LLVM inlines it after the body's first SROA run:
   * `net_quote(curve,&fees,budget)` wraps `net_quote_for_budget(&curve.creator,fees.protocol_fee_bps,fees.creator_fee_bps,budget)`
   * `net_costs(a,&quote_fee,net,&net_fees)` wraps the two identical non-cross `v3_buy_costs(..,net_fees.protocol_fee,net_fees.creator_fee,None)` calls.
   Either alone: 0.6941. Both: 0.95643. Leaf helpers (`fee_bps(&fees)`) are MIR-inlined and change nothing.
   No runtime change: the wrappers forward the same values.

5. Same lever for `costs` (z3): both `add(costs.0,costs.1)` sites go through a plain helper `cost_total(&costs)`, so the
   `v3_buy_costs` payload word `[16]` is loaded once above the tag branch as in the original (0.95643 -> 0.96537).
   One site alone: 0.9544 / 0.9497.
6. Prologue lea (u2): llc oracle shows that unmarking the final `fees` (the `&fees` passed to `v3_emit_buy`) and giving it an
   entry lifetime.start moves the prologue lea early as in the original (wave-4 sell_v3 mechanism). Source: the event tail
   goes through a plain helper `emit_exact_quote(.., fees: TradeFees, .., post: Option<PostComplete>, ..)` that takes both by
   value and borrows them for `v3_emit_buy`; `fees`/`post` become SSA in MIR, CopyProp drops their markers, and the LLVM
   inliner adds entry markers. fees only: 0.96747; fees and post: 0.97218.

7. v3_pool_before argument loads (pb_b2): call it from a block that first binds `base_reserves=a.associated_base_bonding_curve.amount`;
   the loads are then scheduled as in the original (0.97428). The same binding at function scope changes nothing; of the six
   orders for binding all three arguments, only b,r,m matches.
8. v3_pool_before `?` branch shape (r6): BPF cannot reverse a branch after ISel, so the polarity comes from the IR block order.
   Oracle: put the post/costs join block after the v3_pool_before Ok block -> 0.9947. Source: split the post-complete logic into
   `let estimate=if cond{v3_pool_before..?; estimate_post_complete(..)?}else{None};` followed by
   `let (post,costs)=match estimate{Some(mut post)=>fit_post_complete(..)?,None=>(None,costs)};`. The join is now created after
   the Ok block: 7856 B, 0.98950.

All helpers are appended at the end of `trade_v3.rs` (no line moves) and forward the same values (no runtime change).

## Residual (r6): stack colouring only

frameoracle (`w4-frame-oracle`) on r6: two group mismatches, no other differences:
* `fees10` (the 32-byte `fees` that `v3_emit_buy` borrows) sits in our 64-byte group at 0x40 (formatter.i, formatter.i184, post23).
  The original puts it in the 48-byte group at 0x160 (bufs, the estimate payload).
* So `_301` (the v3_execute_buy result, 24 B) joins our 0x160 group. The original puts it at 0x90, because it overlaps fees10.
  Fixing fees10 fixes both.
* StackColoring sorts by size, so the 64-byte group gets the first chance at fees10. In the original fees10 therefore overlaps a
  member of the 0x40 group. The formatters are nested inside the bufs, which share 0x160 with fees10, so the member has to be
  `post23` (`Some(mut post)` around fit_post_complete). The 0x160 estimate payload must also be dead by then. Ours: fees10's first
  use is the store at the merge, after post23 ends (LifetimeStartOnFirstUse).
* Tried without success: deferred `let trade_fees;` assigned in each arm (db*, 0.42-0.79), `&fees` / `&post` variants of the emit
  helper (u3 0.9874, k1 0.9785), an execute wrapper (k2), `if let` / rebinding for the fit (e1 0.9806, e2 0.9853), llc oracles that
  move fees10's start marker (0.77-0.987), and `-stackcoloring-lifetime-start-on-first-use=false` (0.756).
* llc oracle: ending the estimate payload right after its copy into post23 sends `_301` back to 0x90 (0.9947, 5 slots, fees10
  only). Extending any single marked alloca's lifetime.end to the exit (46 tried) never gives exact.

## Trials (keys `0x1489f8-main-a7135a6-*-v1`)

| trial | mechanism | bytes | ratio | result |
| --- | --- | ---: | ---: | --- |
| base | a7135a6 | 7872 | 0.8510 | |
| a01/a02 | `q=..?` whole / `let (net,net_fees)=q` | | = base | |
| a03/a04 | `TradeFees{..net_fees}` in tuple | 7768 | 0.7649 | |
| c01 | `ref net_fees` + `*net_fees` | 7856 | 0.7941 | = oracle "net_fees32 split first" |
| c02/c05/c06 | rename / clone / shadow | | = base | |
| e01/e02/e04 | `let mut fees` reassigned in arm | 7768 | 0.6931 | |
| f01-f04 | fn-scope deferred locals for the arm | | = base | CopyProp unifies them |
| h01/h02 | tokens expression inline in the tuple | | = base | |
| h01 (w6r1) | nested inline(always) split | 7864 | 0.7979 | |
| n01/n02 | outer tuple with the whole `(u64,TradeFees)` | 7896 | 0.6957 | |
| s1-s3 | `(fees,)=(..?,)`, late destructure of `split` | | = base | |
| t1-t3 | field-wise rebuilt TradeFees | 7776-7792 | 0.64 | |
| v1/v2 | cross arm reads net_fees bps | 7784 | 0.7261 | |
| w01-w03 | no wrapper / named `quoted?` | | 0.69-0.74 | |
| x1-x3 | leaf `&TradeFees` helpers | | = base | MIR-inlined |
| y1 / y3 | one plain wrapper | 7792 | 0.6941 | |
| **y2** | both plain wrappers | 7864 | **0.95643** | kept |
| z1 / z2 | `cost_total(&costs)` at one site | 7880 / 7888 | 0.9544 / 0.9497 | |
| **z3** | `cost_total(&costs)` at both sites | 7872 | **0.96537** | kept |
| u1 | `emit_exact_quote(fees by value, &post)` | 7872 | 0.96747 | |
| **u2** | `emit_exact_quote(fees, post by value)` | 7864 | **0.97218** | kept |
| pb_* | pre-bind the v3_pool_before args (6 orders) | 7864 | 0.970-0.974 | |
| **pb_b2** | block-scoped `base_reserves` for v3_pool_before | 7864 | **0.97428** | kept |
| q1-q4 | `!cond` / `&&` / `||` spellings of the post split | | = or 0.49-0.55 | |
| r2/r3 | match on bool / `let mut split` | | = / 0.9396 | |
| **r6** | estimate Option first, then match for the fit | **7856** | **0.98950** | kept |
| u3/k1/k2 | emit/execute helper variants | | 0.79-0.987 | |
| db* | deferred `trade_fees` per arm | | 0.42-0.79 | |
| e1/e2 | `if let` / rebinding for the fit | | 0.9806 / 0.9853 | |

Oracles: hoist8 0.8813; hoist8 + lifetime.end(_86) removal 0.9343; alloca order k1 (trio first) 0.9161; fees+net_fees last 0.9543.
