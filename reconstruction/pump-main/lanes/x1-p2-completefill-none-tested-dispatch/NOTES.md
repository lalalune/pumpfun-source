# x1-p2-completefill-none-tested-dispatch (round 1)

Target: swap_hop 0x5b3b0. Stacked on `x1-p2-buy-fees-whole-netquote-completefill`
(d2c0935be = 6936bc3f8 fees-whole + merge of main 1852a872e), which keeps the TradeFees
from complete_fill whole in the Some payload.

Mechanism: the `complete_fill(..)?` dispatch in `multi_hop_curve_swap.rs` changes from
`if let Some((f,quote,post)) = .. { .. } else { .. }` to `match .. { None => .., Some(..) => .. }`.
The line count stays the same, so line!() immediates do not move.

Effect at original +0x2a98..+0x2c50: rustc/LLVM now emits `jeq r3,0,+0x1b` (None out of line)
with the Some copies as fall-through, followed by `ja`, the closure-error block and the None block.
That is the original's layout. The base emitted `jeq r3,1` with None plus the error block placed
before Some.

| build | swap_hop bytes | ratio | normalized | raw | losses |
|---|---|---|---|---|---|
| base d2c0935be | 18,584 | 0.92654 | 1032 | 347 | 0/0 |
| (a) match None-first | 18,584 | **0.93048** | 1032 | 347 | 0/0 |
| (b) let fill; match fill | 18,552 | 0.89365 | 1032 | 337 | 0/0 (drops 10 raw gains) |
| (c) let fill; is_none/unwrap | 18,560 | 0.89346 | 1032 | 337 | 0/0 (drops 10 raw gains) |

Baseline: x-baseline/1852a872e/score.json (normalized 1032, raw 337).

Residual in this region: the branch offsets (`ja -0x74` vs `-0x76`, `jeq r3,2,-0x77` vs `-0x200`)
come from the shared error-exit placement and from the `ldxdw r2,[r10-0xb28]; add64 r2,8`
placement before the `call 0x2ab1d` compare block (orig +0x29f0). Both are outside this mechanism.
Introducing a `let fill` binding is harmful: it changes the size of the whole function, not only this block.
