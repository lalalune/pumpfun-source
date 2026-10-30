# x1-cto-sweep-exit-nonconst-tag (round 1): admin_cto::execute (0x22a10)

The idea was to feed the sweep's exit merge a Result tag that JumpThreading cannot fold, so the
sweep tail is placed before the post-sweep join as in the original.

Base: main 8b5fd9d81. Scoring baseline: 1852a872e (`x-baseline/1852a872e/score.json`, 1032/337).

## Results (score.py vs baseline; target_metric.py for 0x22a10)

| tag | variant | size B | ratio | norm | raw | losses |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| main | main 8b5fd9d81 | 27,344 | 0.37637 | 1032 | 347 | 0 |
| a | tail expression, both arms `transfer_*(..).map(\|()\|amount)` | 27,368 | 0.3762 | 1032 | 347 | 0 |
| b | `swept=(shared&&holder).then(\|\|sweep(..)).transpose()?.unwrap_or(0)` | 27,240 | 0.3765 | 1032 | 347 | 0 |
| c | `swept_r` bound without `?`, `swept=swept_r?` after pool seeds (line 745) | 27,672 | 0.36429 | 1032 | 347 | 0 |
| d | arms swapped (`if !native`) | byte-identical to main | | | | |
| e | native arm passthrough only; token arm keeps `?` + `Ok(amount)` | **27,400** | 0.37448 | 1032 | **1032** | 0 |
| f | token arm passthrough only | 27,368 | 0.3762 | 1032 | 347 | 0 |
| **g** | **e + b** (committed) | **27,400** | **0.39784** | 1032 | **1032** | 0 |

With (e) and (g), admin_cto::execute is exactly the original 27,400 B, so every later function lands
at its original address. That gives +685 raw windows against the shared baseline, with zero normalized or raw losses.

## Why native-only

In the original, the native arm (Rent::get, ensure_rent_exempt, transfer_native) and the token arm
(create_idempotent, transfer_vault_tokens) are cold blocks at the end of the function (orig
0x28380-0x28b00). The native arm returns through the shared `jne r7,2` merge at 0x26670, so its
tag is not threaded. The token arm's Ok path jumps past that merge (`ja -0x492` to 0x26678), so it
is threaded. Passing transfer_native's Result through (`.map(|()|amount)`) reproduces that split.
Variants (a), (c), (e) and (g) all move the 784-insn sweep tail before the merge (about 255 of the
original 0x24d0-0x3c38 slots matched, against 2 on main).

## Current main (33df3bfd0)

Main has since reached 27,400 B through #2524 (account lifetimes, 1033/1033). Rebased onto it, (g)
gives 27,416 B and ratio 0.43816 (new main: 0.3601). The ratio is higher, but the function is
16 B too long, so raw falls to 347. To be acceptable on current main, the mechanism needs a
companion change that removes 16 B.
