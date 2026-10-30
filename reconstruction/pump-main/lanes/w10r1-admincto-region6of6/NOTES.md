# Lane w10r1-admincto-region6of6 (wave 10, round 1)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`).
Angle: region split, region 6 of 6 = original window offsets `0x5930..0x6b18` (4,584 B).
Base: origin/main 917ee615f (1032 normalized / 347 raw). Builds: `~/.cache/pumpfun-reconstruction/lanes/w10r1-admincto-region6of6/`.

## Region 6 map (original offsets, IR block names from the llc oracle on main's IR)

| orig | source | IR block |
| --- | --- | --- |
| 0x5930 | tail of an `error!` From conversion | |
| 0x5970-0x5b28 | sweep native path, 663-664: `Rent::get` min balance, `lamports`, `ensure_rent_exempt`, `transfer_native` | bb83.i141, bb30.i, bb87.i |
| 0x5b40-0x5cb8 | wallet 557-560: native-mint memcmp, coin `data_is_empty`, source `data_is_empty`, coin `token_frozen` | bb60.i/bb57.i, bb13.i, bb19.i93, bb20.i83, bb73.i84 |
| 0x5cc0-0x5e68 | wallet 561 ATA `create_idempotent` + dispatch on r6 (collect) / r8 (coin CPI) | bb24.i, bb82.i |
| 0x5e70-0x60f0 | sweep token path 719: holder ATA `create_idempotent`, `transfer_vault_tokens` | bb43.i132, bb44.i133, bb103.i135 |
| 0x60f8-0x6118 | wallet native path glue (r6=1, r8=0) | bb19.thread.i |
| 0x6120-0x62e0 | wallet 563-564 `collect`, `Clock::get` + its error From | bb29.i85, bb84.i, bb31.i, bb85.i |
| 0x6300-0x6358 | wallet 559 source `token_frozen` (placed out of line) | bb16.i |
| 0x63b8-0x6858 | CollectCreatorFeeEvent emit! + emit_cpi! | bb86.i |
| 0x6878-0x6a40 | wallet 568 `collect_coin_creator_fee` CPI | bb46.i |
| 0x6a48-0x6b18 | invoke_signed error From + Rc drops | |

## Finding: the original wallet computes two decision flags as phis of constants

Original registers: r6 = "collect" flag, r8 = "coin CPI" flag. The source-empty path sets both to 0, the
native path sets r6=1/r8=0, the source `token_frozen` block sets r6 = !frozen, the coin `token_frozen` block
sets r8 = !frozen, and after the ATA call the original tests `and r6,1` / `and r8,1`. Main kept
`source_frozen`/`source_present`/`coin_frozen` as phis and recomputed `native||(present&&!frozen)` after the ATA,
which made MachineBlockPlacement put the source `token_frozen` inline and the coin `token_frozen` + wallet ATA
after the sweep ATA.

Source (t02): `let do_collect=collection_native||(!source.data_is_empty()&&!token_frozen(source)?);`
`let do_coin=coin_present&&!token_frozen(coin)?;` before the ATA, `if do_collect{..}`, `if do_coin{..}`.
Same behaviour (the original evaluates the same calls in the same order). Region-6 block order now equals the original's.

| metric | main 917ee61 | t02 | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,344 | **27,376** | 27,400 |
| win ratio (target_metric) | 0.37637 | 0.36895 | 1 |
| region-6 ratio (difflib, normalized, call-anchored) | 0.4763 | **0.5914** | 1 |
| calls | 154+3 | 154+3 | 154+3 |
| official normalized / raw | 1032 / 347 | 1032 / 347 | |
| gains / losses | | 0 / 0 | |

t01 (rejected): binding the flags as `&&` of the old bools gives and-of-phis, 27,536 B.

## Remaining region-6 residuals

- Sweep Ok edges: the original sends the sweep's Ok results (amount 0, after transfer) into the shared sweep.exit
  join (`0x3c58`, tag re-check); ours threads them straight to the post-sweep block (0x2478) and errors to 0x2460.
  Cross-region (sweep.exit is in region 3).
- Register choice: original keeps the error payload in r9 and do_coin in r8; ours uses r6 and spills do_coin.
  Probably global allocation pressure from the other regions.
