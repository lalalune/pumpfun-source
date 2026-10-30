# Lane w13a47-cto-stitch9 (wave 13)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: integrator/stitcher. Re-run the cheap scans on the current main, re-screen the open near-miss genes, compose at 27,400 B.

## Step 1 — %1 composite on main 6ff770f7a (0.62403)

`pool_args_pre` (w13a34, +8 B) + `u_sand` (w13a30 genes30, -8 B):
- the pool CPI arguments are bound right after `pool_updated`: `let pargs=(target,a.bonding_curve.is_holder_reward,fee);`
  and passed as `pargs.0,pargs.1,pargs.2` (the curve's holder flag is read before the pool test, as the original reads
  the holder value from a slot instead of at the CPI);
- `shared` as one `&&` chain instead of `if ..{..}else{false}`.

| metric | main 6ff770f7a | this composite |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| ratio | 0.62403 | **0.62672** |
| slots_diff | 3,325 | 3,305 |
| normalized / raw | 1034 / 1034 | 1034 / 1034 |
| gains / losses | | 0 / 0 |
| runtime differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | `ee08c486f68867d36eec196c4a08650493ad502af58d170ef614fed301cd2e51` |

`pool_args_pre` alone is 27,408 / 0.62663 on 6ff770f (it was -0.00009 on 8cf3c5f): its sign flipped once #3155 moved the
entry copy of `new`. Partners at -8 B on 6ff770f: `u_sand` 0.62672, `e_reset` 0.62552, `s_su_iflet` 0.62552,
`cu_fee_replace` 0.62313; `e_reset_late` keeps 27,408.

## Scans on main 52c0b087c (0.62103), all llc oracle on a capture (oracle = build, 0.62103)

- `segscan.py scan` (w13a30): 228 single AccountInfo clone field-segment moves over 19 clones, both pump_amm clones of the
  transfer CPI included (they load from the same `%364`). None above main at any size; 19 byte-identical; best +8 B
  0.61585, best +16 B 0.60168. Clone field orders are a local optimum.
- `fieldscan.py --pairs 6` (w13a21; w13a29 next idea 1): 55 singles + 288 pairs, none above main (best pair 0.62043).
- `mkscan3.py` (w13a35, 892 IR edits): best 0.62283 at 27,400 = branch weight 1:2000 on the Rc `clone` exit / `inc_strong`
  blocks of one clone; no source form (same finding as w13a35).

## Gene screens on 52c0b087c (target_metric; main 0.62103)

| genes | bytes | ratio |
| --- | ---: | ---: |
| `o_ab_late` (w13a19) | 27,384 | 0.62122 |
| `s_rent_local` | 27,384 | 0.61882 |
| `o_ab_late`+`s_rent_local` | 27,368 | 0.6205 |
| + `ph` (abr_ph) | 27,400 | 0.61923 |
| `k2` (w13a24-3) | 27,360 | 0.57293 |
| `k2`+`pool_args_pre` | 27,368 | 0.57344 |
| `w_tf_prog2` (w13a09, literal clone let) / `+ph` | 27,368 / 27,400 | 0.61661 / 0.61714 |
| `w_tf_prog_tti` | 27,384 | 0.60473 |
| `s_su_iflet` / `+pool_args_pre` | 27,392 / 27,400 | 0.62082 / **0.62193** |
| `t_cus` | 27,384 | 0.62152 (landed by #3155) |
| `o_ab_late`+`t_cus`+`wl_ts_clockvar`+`pool_args_pre` | 27,400 | **0.62223** |
| `e_reset`, `u_sand` | 27,392 | 0.62082 |
| `c_fee_unwrap` / `e_cb_local` / `ph` / `pool_args_pre` | 27,408 / 27,416 / 27,432 / 27,408 | 0.61884 / 0.61905 / 0.61976 / 0.62094 |

Main moved to 6ff770f (#3155, which also carries `t_cus`) before these were proposed; see step 1.

## Tools (`tools/`)

- `genes47.py`: gene library keyed on 52c0b08/6ff770f (w13a30 genes30 + w13a34 knobs + w13a19/w13a24/w13a09 leads +
  `pap_*` variants). Every gene keeps the newline count.
- `run47.py <queue> <results.jsonl> 2`: background runner (rsync crate copy, fastbuild, target_metric).
- `rec47.py`: ledger recorder. `cap.sh`: capture build -> trimmed `mod.ll` for the llc oracles.

Ledger: approach `stitch-composite`, keys `0x22a10-w13-<main7>-stitch9-<variant>-v1`; scans
`0x22a10-w13-52c0b08-stitch9-{segscan-singles,fieldscan-pairs6,mkscan3}-v1`.

## Step 2 (wave 14 continuation) — %2 composite on main 53abf28b1 (0.62672)

Single-gene screen of 92 catalog genes + 25 genes rebased on 53abf28 (pool args, `shared` chain, Ok tuple orders,
event locals). Positive singles: `n_cb_rev` (`let cashback=!holder&&st.cashback;`, same as `n_cb_if`) 27,392 / 0.62772,
`s_rent_local` (`let rent=Rent::get()?;let min=rent.minimum_balance(0);`) 27,384 / 0.62691.
Composite with the +24 B `ev_nf_pre` (`let nf=a.bonding_curve.creator_fee_bps;` before `pool_updated`, event reads `nf`):

| metric | main 53abf28b1 | this composite |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| ratio | 0.62672 | **0.62882** |
| slots_diff | 3,305 | 3,288 |
| normalized / raw | 1034 / 1034 | 1034 / 1034 |
| gains / losses | | 0 / 0 |
| runtime differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | `74617479b7688b5d16aac7af7476282b513f68aff900bca0ac07c600d10a0080` |

`ev_cb_pre` (`let cbc=a.bonding_curve.is_cashback_coin;`) as the +24 B partner ties (0.62882, different bytes).
Other pairs: `n_cb_rev`+`c_fee_unwrap` 0.62732, `+e_cb_local+s_su_iflet` 0.62762, `+s_rent_local+wl_ts_clockvar+c_fee_unwrap` 0.62762,
`+x_ata_rev` 0.62493, `+wl_ts_clockvar+e_reset/s_su_iflet` 0.62672. Keys `0x22a10-w13-53abf28-stitch9-<name>-v1`.

## Step 3 — %3 on main 23322b07c (0.62882): `pool_updated` empty-test first

`let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;` (gene `pu_rev`, same as w13a30's `p_empty_first`, which was
-0.0006 on 53abf28 and turned positive once #3200 landed).

| metric | main 23322b07c | this change |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| ratio | 0.62882 | **0.63062** |
| slots_diff | 3,288 | 3,288 |
| normalized / raw | 1034 / 1034 | 1034 / 1034 |
| gains / losses | | 0 / 0 |
| runtime differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | `c38b85038579b0d7c5d275864e06fecf16c635868434919b3378ba9f4fa73752` |

Same-screen dead ends on 23322b0 (bytes / ratio): `v_hr_rev` 26,576 / 0.519, `v_he_b` 27,360 / 0.613, `v_he_c` 27,392 / 0.524,
`v_tsh_rev` 0.62672, `co_rev` 27,392 / 0.577, `x_dcoin_rev` 27,376 / 0.604, `w_af_rev` 27,424 / 0.461, `v_hold_eq` 27,352 / 0.514,
`x_hold_eq`/`x_hold_ml` 27,232 / 0.570, `pre_sk_args`/`pre_sk_first` 27,192 / 0.622, `pre_args_late` 27,208 / 0.572,
`pre_cb_late` 27,328 / 0.569; byte-neutral: `v_hr_ne`, `v_he_a`, `v_he_d`, `v_f_rev`, `v_cbv_rev`, `pre_cb_mid/sk/hopt/match/not`,
`sc_auth_*` (sharing CPI authority literal; fieldscan R3160 was +0.0006 on 53abf28 but is neutral on 23322b0).

