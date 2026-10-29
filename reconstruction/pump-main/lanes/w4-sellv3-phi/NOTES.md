# w4-sellv3-phi: sell_v3 (0x14a8a8) normalized match

Target `0x14a8a8` `trade::sell` (sell_v3). Base origin/main 630a074 (1023 normalized / 277 raw).

| | slots_diff | ratio | bytes | official | gains | losses | unstripped sha256 |
|---|---:|---:|---:|---|---|---|---|
| before (630a074) | 6 | 0.99728 | 6032 | 1023 / 277 | | | 1c66d0a9acff |
| after (t03) | 0 | 1.0 (normalized_equal) | 6032 | 1024 / 277 | 0x14a8a8 | none | d0f2111fe7f8 |

## Source change
`programs/pump/src/trade_v3.rs`: sell_body builds the event through a plain (no inline attribute)
`fn sell_event(curve, global, volume, user, mint, amount, quote, fees: TradeFees, buyback_fee,
quote_transfer_fee, timestamp) -> TradeEvent` that forwards to `trade_event(.., false, .., &fees, .., "sell", timestamp)`.
It takes `fees` by value instead of sell_body borrowing it. The helper is written on the same line as `quote_is_native`,
so no Source line moves.

## Mechanism (found with the llc IR oracle)
1. The last residual was the prologue sret `lea` for `prepare_bonding_curve` (`mov r1,r10; add r1,-0x358`), scheduled
   after the argument ADDs. BPF uses the `list-ilp` pre-RA scheduler. The FI `MOV_rr` (depth 0) and the arg
   `ADD_ri`s tie on reg pressure, so ILP falls to BURRSort, which puts the leaf FI node last. The original's
   order comes from ILP's critical-path check, `|depth spread| > MaxReorderWindow (6)`. The ADDs' depth is the number
   of chain nodes ahead of the `ctx.accounts` load plus a small constant.
   - `llc -max-sched-reorder=0` makes base early. `-disable-sched-critical-path` makes the explicit-sret IR and
     sell_v2 (which matches early in the original) late again.
2. The entry chain nodes are `lifetime.start`s. The LLVM inliner adds them when it inlines `sell_body` into `sell`, one
   per surviving `sell_body` alloca that has no markers. Base has 3 (`_184` chain iter, `inner_data`,
   `authority_info`; all from the emit_cpi! expansion). sell_v2 has 4 (`creator`) and an early lea.
   IR oracle: adding one more entry lifetime.start before the load gives an exact llc match (734/734). Unmarking
   `fees`, `_20`, `_21`, `_34`, `_79`, `_204`, `_207`, `ix_data`, `buf`, or `_200` also gives exact. Unmarking other
   allocas changes stack coloring.
3. Source: with `fees` moved by value instead of borrowed, `fees` is SSA in MIR. CopyProp merges the `?` binding `val`
   into it and drops its StorageLive/Dead. The pointer is still passed to the LLVM-inlined helper, so the alloca survives
   SROA and gets the 4th entry lifetime.start.
   - `#[inline(always)]` / `#[inline]` helpers are MIR-inlined, and the parameter becomes a marked 32-byte copy (frame +16, 6080 B).
   - `#[inline(never)]` keeps a call (5992 B).

## Attempts (ledger)
- d204a146 analysis (entry chain depth decides the lea)
- a44d34f0 t01 named error local: byte-identical
- ccfdd307 t02/t04 inline(always)/inline helper: MIR-inlined, worse
- 486e4c8f t05 inline(never): worse
- 0b0e4e3c t03 plain helper: normalized match, 1024/277, no losses

## Tools (scripts/)
`irx.py` (llc a slimmed post-opt function and compare it to the original, `LLCX` for extra llc flags), `unmark.py` (oracle edit:
strip one alloca's markers and add an entry lifetime.start), `d1.py` (add N dummy entry lifetime.starts), `liveout.py`,
`callsites.py` (list every call site of a function in an objdump, e.g. prepare_bonding_curve callers in the original),
`pre.sh`/`unm.py` (pre-opt IR, then list sell_body allocas with no markers), `post.sh`, `capture_mir.py`.
The same lever (one more unmarked surviving alloca in an inlined body) should apply to `buy_exact_quote` (0x1489f8), whose
original lea is also early while our build's is late.
