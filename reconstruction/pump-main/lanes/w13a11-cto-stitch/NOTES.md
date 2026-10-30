# Lane w13a11-cto-stitch (wave 13)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: integrator/stitcher. Collect unlanded admin_cto source genes from w12/w13 lanes, combine compatible
edits on latest main at exactly 27,400 B, and land zero-loss composites through `land.py`.
Base: main 3912c47ac (programs/ identical on origin/main 5d597ce7a): 27,400 B, ratio 0.48772, slots 3,273.

Tooling (not in git, `~/.cache/.../lanes/w13a11-cto-stitch/tools`): w12a04-cto-k4size's `genes.py`/`run.py`
(queue runner, fastbuild + target_metric, two builds max) with `genes13.py` adding w12a07-cto-sweepthread's
source genes. Every gene keeps the newline count, so every error/require site keeps its `line!()`.

## Composite 1 (#2885, landed 085e5dffb): skip flag + vsigner + bump-first + reset early

| metric | main 3912c47ac | this lane | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,400 | **27,400** | 27,400 |
| ratio | 0.48772 | **0.48922** | 1 |
| slots_diff (positional) | 3,273 | 3,303 | 0 |
| calls | 154+3 | 154+3 | 154+3 |
| normalized / raw | 1034 / 1034 | 1034 / 1034 | 1035 |
| losses (norm / raw) | | 0 / 0 | |
| runtime differential | | 363/363 | |

Unstripped sha256 `4fc952ce8efbf4aa8d30036222f6d7c0a94363a6cb1739a09ccfdc50b975354a`.

Genes (source of each):
- `st_skip` (w12a07-cto-sweepthread `skiptree`): the sharing tree yields a `skip` flag as a phi of constants
  (`false` only in the shared+holder arm) and the sweep gate is `(!skip).then(..)`; the original gates the sweep
  on such a flag.
- `st_vsig` (w12a07 `vsig`): `let vsigner:&[&[&[u8]];1]=&[vaultseeds];` once, shared by both sweep transfers.
  These two alone: 27,440 / 0.49065 (+40 B).
- `st_bo` (w12a07 `bumpold`): `let bump=..;let old=..;` order: -32 B (27,408 / 0.48944).
- `h_reset_early` (w12a04-cto-k4size step 4): `let reset=sharing_update.is_some();` before the pool signer
  seeds, used by the event: alone on main 27,392 / 0.48869; here it takes the composite to 27,400.

## Compose / conflict table (measured on main 3912c47ac; bytes / ratio)

| variant | bytes | ratio | note |
| --- | ---: | ---: | --- |
| main | 27,400 | 0.48772 | |
| h_reset_early | 27,392 | 0.48869 | |
| h_ev_cb_global (event `is_cashback_coin` from the curve) | 27,384 | 0.48906 | |
| w_cp_inline (wallet `coin_present` bound inside `do_coin`) | 27,416 | 0.48997 | calls 155+3 |
| st_skip + st_vsig | 27,440 | 0.49065 | |
| + st_bo | 27,408 | 0.48944 | |
| + st_bo + h_reset_early | **27,400** | **0.48922** | composes: landed candidate |
| + st_rl + st_bo | 27,392 | 0.48929 | |
| + st_rl + st_bo + h_reset_early + h_fee_iflet | 27,400 | 0.48742 | fee_iflet conflicts with reset here |
| h_ev_cb_global + w_cp_inline | **27,400** | **0.49041** | composes (155+3 calls), but not with the skip family (A8 27,432 / 0.48892) |
| skip+vsig + h_ev_cb_global | 27,456 | 0.49140 | |
| skip+vsig + h_ev_cb_global + reset | 27,448 | 0.49147 | best ratio seen, 48 B over |
| A4 = skip+vsig+bo + evcb + reset | 27,416 | 0.49027 | |
| A1 = A4 + st_rref (`let rent=&Rent::get()?`) | 27,400 | 0.49011 | st_rl gives the same bytes |
| skip+vsig + st_rref | 27,424 | 0.49049 | |
| skip+vsig+bo + reset + st_rref | 27,384 | 0.48996 | |
| A5/A7 (skip family + w_cp_inline) | 27,416-27,440 | 0.489 | w_cp_inline conflicts with the skip family |

## Composite 2 (#2892, merged 4394685): + Result gate + event cashback from the curve + Rent ref, minus reset

w13a10-cto-pfclimb (#2888) found the same skip/vsigner/bump-first family independently with the Result-valued
gate `swept=if !skip{sweep(..)}else{Ok(0)}?;` (-8 B) as the size companion instead of `reset`.

| variant (on main 3912c47ac; S = skip+vsig+bo) | bytes | ratio | note |
| --- | ---: | ---: | --- |
| S + gate_res (= #2888) | 27,400 | 0.48951 | |
| S + gate_res + evcb + reset | 27,408 | 0.49034 | |
| **C1 = S + gate_res + evcb + st_rref** | **27,400** | **0.49071** | this PR, 0 losses, 363/363 |
| S + gate_res + evcb + reset + rref + fee_iflet | 27,392 | 0.48899 | |
| S + gate_res + reset + fee_iflet | 27,408 | 0.48705 | fee_iflet hurts with the skip family |

Composite 2 versus main 085e5dffb: drop `reset` (event reads `sharing_update.is_some()` again), add the Result
gate, `is_cashback_coin:a.bonding_curve.is_cashback_coin` in the event (`h_ev_cb_global`, w12a04 H-table:
27,384 / 0.48906 alone on H2) and `let rent=&Rent::get()?;` in the sweep native arm (`rent_ref`,
w12a14-cto-hillclimb). 27,400 B / **0.49071** / slots 3,313, 1034/1034, zero losses, unstripped sha256
`48d5a9c99d2fd34f...`, differential 363/363.

## Composite 3: borrowed argument copy and cached sharing flag

This candidate moves the `CtoState` binding out of the inner tuple scope and
borrows `new` as `let args=&(new,);`. The shared non-holder arm uses `args.0`,
which equals the same immutable `Copy` value previously read directly. It also
caches `sharing_update.is_some()` before the pool signer seeds for use in the event.

Compared with the verified #2906 baseline, this composite returns the cashback
boolean operands and the independent curve-field access order to their earlier
forms. The event still reads the updated holder and cashback fields from the
curve. These changes preserve values, validation and CPI order; all 24 macro
sites retain their original line numbers.

A fresh identity build was compared against main
`e9e426998ed4c214223879cb54bb2e3384f25449`, whose full Pump source inventory
matches the verified #2906 build (`d44d67269eb5ab2aaa962a2497a6552bb53254a6bb33bd0015f5d8103b62a4c0`).

| Measure | #2906 baseline | Composite 3 |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| Sequence diagnostic ratio | 0.49131 | 0.49431 |
| Differing normalized instruction slots | 3,280 | 3,306 |
| Raw / normalized matched windows | 1,034 / 1,034 | 1,034 / 1,034 |

The sequence ratio improves while the positional mismatch count increases.
The official 1,035-window inventory has no missing or resized windows and no
lost raw or normalized matches. This partial-window improvement does not
increase the matched-window completion percentage or establish whole-ELF identity.

All 363 signed admin_cto differential cases matched the captured program with
genuine dependency CPIs. This is bounded runtime evidence, not all-input proof.

Source inventory: `976a6bf25dd46c867047081de1bc0a0ff758ff0e3dc0a7192d200f7ce1d1e430`.
Unstripped ELF: `46ba0c60c7b4dd11f7a67f01b81ff7e305b700dd2e1f459fccd07ddca58b3d2c`.
Runtime ELF: `95f21f881dbf6c3be67819735a291eceaa934314b4e43b2427cda21228420302`.

## Later composite: cashback field and sharing reset

Relative to the verified #2927 source, the event reads cashback from the curve
field assigned earlier in the same call, and computes the reset flag directly
from immutable `sharing_update` instead of caching it. The emitted values are
unchanged: there is no intervening curve-field write/reload or mutation of the
sharing option. Validation and CPI order, and all 24 macro call-site line
numbers, are unchanged.

The reviewed branch includes main
`b720cf9267d2ef8ea1e73a36b78f53260e03839e`, whose full Pump source inventory
matches the verified #2927 build:
`6ec93b9004c2374f087c98d93a6d5bc3c211ef133999b84a0e995b8b080a3761`.

| Measure | #2927 baseline | Candidate |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| Sequence diagnostic ratio | 0.51228 | 0.51348 |
| Differing normalized 8-byte slots | 3,334 | 3,334 |
| Raw / normalized matched windows | 1,034 / 1,034 | 1,034 / 1,034 |

A fresh identity build and official score preserve every existing raw and
normalized match across the 1,035-window inventory, with no missing or resized
windows. This remains a partial-window sequence improvement; the matched-window
completion percentage is unchanged and whole-ELF identity is not established.

All 363 signed admin_cto differential cases matched the captured program with
genuine dependency CPIs. This is bounded runtime evidence, not all-input proof.

Source inventory: `e3c9b449d89df914be23f8ba7f42027ae27a6f25e1b6fa25f938f0bc1dae6275`.
Unstripped ELF: `620d90b0b2e33a2f422cbb6755437804dc3a30d9a125f2e298d39cd3da9ca9fc`.
Runtime ELF: `1559324ef78658e3d6130754196ebbc17ec77df89d868c7b5b669c1f7b159666`.
