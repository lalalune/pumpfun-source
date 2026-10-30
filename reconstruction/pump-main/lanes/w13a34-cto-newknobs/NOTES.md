# w13a34-cto-newknobs: new size knobs outside the frame/validate regions

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Continues w13a11-cto-stitch-7 (#3008) and
w13a10-cto-pfclimb-6 (#3010), whose shared next idea was new ±8/±16 B knobs from data flow in regions the frame and
validate lanes do not touch.

## Method

- 46 new semantics-preserving spellings (`tools/knobs.py`, dict `K`), each a list of exact `(old, new)` replacements
  with equal newline counts, so every `line!()` site keeps its line. Regions: AdminCtoEvent field sources (curve
  read-back vs locals, values bound before the pool CPI), the `admin_cto_pool` and `admin_cto_sharing_config` CPI
  argument forms (accounts struct or program clone bound first, args read early), pool-authority signer seeds,
  Clock/Rent call sites (execute event, wallet event, sweep rent), the `pool_updated` / msg tail and the curve update
  block (`mem::replace` forms). Also 54 genes from the w13a10 `genes13.py` library that still apply, as re-screens.
- Each knob was scored with the w13a23 raw-IR oracle (`capvar.sh` + `rx.py`: identity build emitting pre-opt IR, then
  SDK `opt -O3` and `llc` as fastbuild; `eq_main` was true for both base captures, so the oracle equals the build).
  `tools/run2.sh` pipelines it: captures on 2 build workspaces, `rx` in the background.
- `tools/catalog.py` merged every result into `$SWARM/w11/sizeknobs-cto.json` (bases `m06e6bb8` and `m8cf3c5f`;
  the catalog now has 95 knobs). `tools/pair.py` lists size-balanced 2- and 3-knob sets from a screen file.
- Ledger rows: approach `size-knob-screen`, keys `0x22a10-w13-<main7>-newknobs-<knob>-v1`.

## Screen on main 06e6bb829 (0.57669, 27,400 B)

Full table: `screen-06e6bb8.jsonl`. Only one knob raised the ratio, and it changes the size.

| knob | Δbytes | ratio | Δratio |
| --- | ---: | ---: | ---: |
| `ev_reset_shared` (event `sharing_config_reset:shared`) | -128 | 0.57988 | **+0.00319** |
| 15 knobs, among them `ev_auth_deref`, `ev_ts_map`, `pool_prog_let`, `pu_match`, `sig_arr`, `rent_checked`, `wl_cr_deref`, `tail_a_ctx` | 0 | 0.57669 | 0 (same ratio) |
| `pool_args_pre` (pool CPI args `(target,curve.is_holder_reward,fee)` bound before `pool_updated`) | +8 | 0.57661 | -0.00008 |
| `pu_len`, `g_old_fee_first` | 0 | 0.57639 | -0.00030 |
| `pu_amm_key` (`a.pool.owner==a.pump_amm.key`), `sh_fees_key` (`a.sharing_config.owner==a.pump_fees.key`) | 0 | 0.57631 | -0.00038 |
| `ev_hr_curve` | -8 | 0.57618 | -0.00051 |
| `wl_ts_clockvar` / `g_w_clock_local` | +24 | 0.57613 | -0.00056 |
| `cu_replace` (`old_creator=mem::replace(&mut curve.creator,target)`) | 0 | 0.57609 | -0.00060 |
| `g_rent_named` / `g_rent_ref` / `g_s7_rentlocal` | -16 | 0.57597 | -0.00072 |
| `ev_nf_pre` | +24 | 0.57583 | -0.00086 |
| `pool_hr_local` | +32 | 0.57515 | -0.00154 |
| `ev_cb_pre` | +24 | 0.57494 | -0.00175 |
| `pu_amm_keyfn` | +80 | 0.57425 | -0.00244 |
| `cu_fee_replace` | -8 | 0.57378 | -0.00291 |
| `ev_ts_clockvar` | 0 | 0.57370 | -0.00299 |
| `g_s7_dborrow` | -80 | 0.57366 | -0.00303 |
| `sh_prog_let` / `cu_typed` | -32 | 0.5734 / 0.5722 | -0.003 / -0.004 |
| `ev_mint_key`, `ev_newfee_unwrap`, `rent_map` | +16..+24 | | -0.006..-0.010 |
| `pool_accs_let`, `sh_accs_let`, `sig_mint_acct`, `ev_*_pre` (auth/bc/nc), `ev_ts_prepool` | | | -0.02..-0.11 |
| `pool_tgt_curve`, `ev_nc_target`, `ev_ts_presig` | | | about -0.22 |

No size-balanced set reached a gain: the only +128 B fillers (`pu_amm_keyfn`+`wl_ts_clockvar`+`ev_nf_pre`, -0.0039 in
sum) cost more than `ev_reset_shared` gives.

## Re-screen on main 8cf3c5f8a (0.62043; main moved 3 times during the lane)

| knob | Δbytes | ratio | Δratio |
| --- | ---: | ---: | ---: |
| `g_old_fee_first` | 0 | 0.62043 | 0 |
| `pool_args_pre` | +8 | 0.62034 | -0.00009 |
| `pu_len` | 0 | 0.62013 | -0.00030 |
| `pu_amm_key`, `sh_fees_key` | 0 | 0.62004 | -0.00039 |
| `cu_replace`, `g_canedit_first`, `g_s7_destrev` | 0 | 0.61983 | -0.00060 |
| `ev_ts_clockvar` | 0 | 0.61744 | -0.00299 |
| `cu_fee_replace` | -8 | 0.61753 | -0.00290 |
| `ev_reset_shared` | -112 | 0.60402 | **-0.01641** |

## Findings

1. **Tail knobs are local and stable across mains.** Every zero-size or ±8 B knob in the post-update tail and curve
   block has the same Δratio to within 0.00001 on both mains (for example `cu_replace` -0.00060/-0.00060, `pu_len`
   -0.00030/-0.00030, `ev_ts_clockvar` -0.00299/-0.00299, `pool_args_pre` -0.00008/-0.00009). They do not perturb
   register allocation upstream, so their catalog deltas can be reused on later mains without re-measuring.
   All of them are ≤ 0: the tail's data flow (event sources, CPI argument order, Clock call placement) already
   matches the original as closely as these spellings can.
2. **`pool_args_pre` is the near-neutral +8 B filler that w13a10 could not find** ("No ratio-neutral +8 B companion"):
   -0.00008 on 06e6bb8 and -0.00009 on 8cf3c5f. Pair it with any -8 B gain elsewhere to land at 27,400 B for a
   0.00009 cost.
3. **`ev_reset_shared` is a global register-allocation lever, not a local one.** `sharing_config_reset:shared`
   instead of `sharing_update.is_some()` ends `sharing_update`'s liveness at the sharing CPI and saves 112-128 B.
   Every register assignment in the function shifts. It flipped from +0.0032 (06e6bb8) to -0.0164 (8cf3c5f) once the
   clone-layout PRs landed. Re-screen it on each main as a frame-lane lever, not as a size knob.
4. Spellings that move pure reads (keys, curve fields, Clock) ahead of the pool CPI cost 0.065-0.11. The original
   reads them after the CPI, as main already does.

## Pairs on 8cf3c5f (`pairs-8cf3c5f.jsonl`)

| set | bytes | ratio |
| --- | ---: | ---: |
| `z_sh_flat` + `pool_args_pre` | 27,400 | 0.62043 (= main, 3,311 slots vs 3,305) |
| `z_sh_flat_owner_first` + `pool_args_pre` | 27,384 | 0.61732 |
| `z_sfo_deref` + `pool_args_pre` | 27,384 | 0.61732 |

On this main the owner-first `shared` spellings are -24 B, not -8 B, and lose 0.003. `z_sh_flat` is -8 B and
ratio-neutral, so its pair with `pool_args_pre` lands exactly at main's ratio with no gain.

## Next ideas

- Use `pool_args_pre` (+8, about -0.0001) as the filler for any -8 B gain another lane finds.
- Re-screen `ev_reset_shared` (-112..-128 B) on each new main together with the frame lanes' ±128 B levers: its sign
  depends on the frame (+0.0032 on 06e6bb8, -0.0164 on 8cf3c5f).
- The tail region (event, pool CPI, Clock, curve stores) looks exhausted for spellings: 46 new knobs and 54
  re-screens found no zero-size gain on two mains. Remaining admin_cto distance is upstream (frame, clone layout,
  validate RPO), where the frame lanes work.
