# Lane buyv2-hillclimb

Targets (programs/pump/src/buy_v2.rs):

- `0x13b9b8` `buy_v2::buy_handler`: original 15,480 B.
- `0x13f630` `buy_v2::buy_exact_quote_in_handler`: original 20,184 B.

## Step 1: seed from the prior frozen-best source (attempt 32763981e8cd40ec904be7e3db7907e9)

Main's `buy_handler` had drifted away from the prior swarm's frozen-best spelling
(the source the `buyv2-bruteforce` lane was measured on). Restoring frozen-best's
`buy_v2.rs` (local `pay_from_user*` / `move_curve_tokens` wrappers, bound
`base_token_program`/`base_mint`, `a.*` field paths in fee validation, `gross`
naming, `Ok((0,0,0,0))` whitelist arm) recovers its codegen on current main:

| target | before (main d2cb88d) | after |
| --- | --- | --- |
| 0x13b9b8 bytes | 15,424 | 15,464 (orig 15,480) |
| 0x13b9b8 ratio | 0.66526 | 0.94354 |
| 0x13f630 | 20,096 / 0.69433 | unchanged |
| official | 1019 / 188 | 1019 / 188, no gains, no losses |

Unstripped sha256: 728936d2cbfb4dc441107bc1c4f9080e7fe65695f5e4891280c38f35387a2030.

Engine (outside git): `~/.cache/pumpfun-reconstruction/lanes/buyv2-hillclimb/engine/`.

## Step 2: gene engine, exact-quote tail transplant (attempt b075029ac7144a69bc72d2b71f4c4786)

The engine (`engine/genes.py`) renders buy_v2.rs from a genome of tail idioms per handler
(wrapper vs direct transfer/payment calls, bound `system_program`/`base_*`, cashback branch
order, payment amount spelling, `uva` binding, snapshot order, TradeEvent/CompleteEvent field
order, `ix_name` conversion). The identity genome rebuilds the seed byte for byte (728936d2).

Giving `buy_exact_quote_in_handler` the frozen-best buy_handler tail:

| target | before | after |
| --- | --- | --- |
| 0x13f630 bytes (orig 20,184) | 20,096 | 20,112 |
| 0x13f630 ratio | 0.69433 | 0.92620 |
| 0x13b9b8 | 15,464 / 0.94354 | unchanged |
| official | 1019 / 188 | 1019 / 188, no gains, no losses |

Control (attempt 5ea82e879a9a413284b20f33c83db29c): buy_handler with the main-style direct
tail falls to 0.70098, so the tail spelling was the dominant residual in both handlers.
Unstripped sha256: 9316184ec66730c5b450fc95349b3ca49664d1135a3e3ed6a2155aa750608d68.

## Step 3: climb generation 1 + compose with buyv2-sibling-transplant (PR #1218)

- Gen 1 single-gene flips: buy_handler snapshot order `SNAP_A` (reserves, then creator,
  quote_mint) raises 0x13b9b8 from 0.94354 to 0.94776 at 15,464 B.
- The sibling lane restored the prior-swarm exact-quote handler (0.97341, 20,176 B). The
  engine now uses that section as its exact-quote base; its genome encoding renders a
  file whose build reproduces 0.97341. Composed build `sib-render`: eq 0.97341 / 20,176 B,
  bh 0.94776 / 15,464 B, official 1019/188, no gains, no losses,
  sha256 0aa51f4ef6081904323e2c5e6466da079c03a6b6a7a109d80243484f8fcf1e69.
