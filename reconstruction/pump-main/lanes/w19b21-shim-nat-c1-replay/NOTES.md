# w19b21-shim-nat-c1-replay: C1 is decided outside C1 (admin_cto 0x22a10)

Work in progress. llc oracle numbers on captures, nothing landed yet.

## Headline (main 8815a7763, M 3065)

Main without its three C1 trap weights (`aicl`/`aicd` back to `aic`, capture `u8815`) is M 3016 @27392 B, and its first-round C1 colours are already the original's (all pointers, `data.prog`, `fl.prog`).
On that base **two sticky forces outside C1**, `%1729=r0` (piece of `%81`, votes V2, V5, J1, def orig 0xb08) and `%1743=r3` (piece of `%78`, the cashback bool at orig 0xd80), give:

- **M 3153 (0.9443) @27384 B, all3 3309**
- **C1 451/458 exact, 458/458 all3, frame-masked 458**: every tile register and spill slot right, only -0x948/-0x950/-0x958 swapped.

## Why

1. First round: the C1 cascade is deterministic in size and use count (`tools/sim1.py` replays the real log for all 139 first-round C1 events).
   Before 8815a7763 it was one "rotation" away: `key.admin` evicted `writ.pool` from r2. A 2% weight on `key.admin` (`RAPRIO_WEIGHT`) gave the original's first-round colours, M +65 to +88.
2. Second round: lam.fees r0, key.fees r5, data.fees r7 land right on their own. `lam.pool` must get r8 (ours r6), which pushes owner.fees to r6 and so on. r8 is blocked at lam.pool's second dequeue (seq about 1460) by the flag piece
   (`%79` split, `Split for $r8 in 49 bundles`, the piece runs through V..C1 tile 6).
3. In the original that flag piece has been evicted by then. The eviction comes from V: `%17`'s split product (E3, V1, V2, J1; orig r8, ours r0) has no free register once r0 is busy in V2-J1 and evicts the flag piece (lightest).
   r0 is busy because `%81`'s piece holds it in V2, V5, J1 (ours r7).

So C1's naming prize is priced in V2/V5/J1's second-round registers.

## Lever: one branch weight on the fee range test (main 1f7ca411c)

`llc` screen of every conditional branch (`tools/brscreen.py`, 1,184 cells, scored by M and the C1 tile metric). Only one branch moves C1: `bb55.i`, `f==0||f>st.max_fee`, `p(ok)` anywhere from 0.02 to 0.48 against the default 0.5.
On main without the C1 trap weights and the repay reads:

| p(ok) | M | bytes | C1 tiles exact / 278 |
|---:|---:|---:|---:|
| 0.5 (default) | 3,016 | 27,392 | 179 |
| 0.02 | 3,105 | 27,400 | 267 |
| 0.1 | 3,128 | 27,408 | 267 |
| 0.2 - 0.45 | 3,144 | 27,416 | 267 |
| 0.25 - 0.45, repay reads kept | 3,181 | 27,464 | 278 |

Source form: `if unsafe{expect_p(f==0||f>st.max_fee,true,P)}{..}` reproduces the IR cell (capture signature equal in M and bytes).

## Result: with the original's plan flags, C1 needs no weight at all

w19b25's natural V1..J2 (#4195, M 3,217 with the three C1 trap weights) minus those weights: **M 3,303 (0.98922) at 27,400 B, C1 458/458, all3 3,334.** The fee weight above was a stand-in for that V shape, so it is dropped too.
What is left: E3 one inverted branch (`jne r8,0,0x900` as `jeq`+`ja`, +8 B), the S2 native arm's amount registers plus the last repay read, and jump offsets that follow from those.
