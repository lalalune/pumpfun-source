# w14a109-cto-stitch13: integrator lane for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a80-cto-stitch12 (#3411). Ledger approach `stitch13`, keys `0x22a10-w14-<main7>-stitch13-<variant>-v1`.

Oracle (experiment only): `tools/scr.py <specfile> [workers]` = stitch12's gene library (`genes.py`, `genes_s11b.py` on the
stitch12 branch) + `tools/genes_s13.py` (w14a89 t-family, the #3137 size-knob catalog as `K_*` genes), applied to a crate
copy; the pre-opt IR is captured with w14a88's `capraw.py` and scored with `rx.py` (opt -O3 + llc, ~35-100 s per variant
on the shared machine, `eq_main` true on the unedited capture of every main used). M = matched masked tokens against the
original (difflib, as `mcount.py`). Every run records a ledger row.

Main moved three times during this lane (963d1ee -> 13fe453 #3480 -> ebe5387 #3495), so the screens are per base.

## 1. 963d1ee (M 2,244, 3,123 slots): the rest of the stitch12 single screen

| gene | dB | M | dM | note |
| --- | ---: | ---: | ---: | --- |
| ev_auth_deref, r_getdot, n_amt_ge, n_flip0, n_checked, n_amtmin, n_lamvar, v_tmatch, v_hkclone, v_issome_if, v_fee_range, v_fee_lt1, v_cbnot, v_zero_ne, v_fee_gt, v_mayhem_req, su_hold, su_ns | 0 | 2,244 | 0 | byte-identical to main |
| n_amtmax | 0 | 2,244 | 0 | one slot differs (0x5a10), same M |
| t1 / t4 / t5 (w14a89 tree `new.is_none()` spellings) | -24 | 2,243 | -1 | |
| t1 + crl_L | +48 | 2,246 | +2 | |
| t1 + crl_L + vol334_back | +40 | 2,244 | 0 | |
| tai_pa / n_ensiflet / v_tletelse | 0 | 2,229 | -15 | |
| v_tswap / q_swap | 0 | 2,237 | -7 | |
| n_mapamt(_flip/_and/_us/_m) | +8 | 2,237 | -7 | |
| ev_cb_local | +8 | 2,235 | -9 | |
| n_ensmatch / n_andthen / n_mapamt_ens | -24 | 2,233-2,234 | -10/-11 | |
| tai_tv / tai_gl / tai_mi | -8 / -24 / 0 | 2,213 / 2,203 / 2,166 | | |
| v_tokor / q_arr / r_letrent / v_tcontains / n_tq | -96 / +88 / -32 / -200 / 0 | 2,102 / 2,101 / 1,953 / 1,658 / 1,298 | | |

Junk bound on t1 (`junkgreedy.py`, 3 pure +8 insertions): 2,245 @ 27,400 (+1 over main), all at the entry
(0x140-0x190), so a faithful +24 B fill for t1 is worth at most +1.

## 2. 13fe453 (#3480, M 2,245, 3,123 slots): knob prices

| gene | dB | M | dM |
| --- | ---: | ---: | ---: |
| vol334_back (drop the #3430 validate `read_volatile` placeholder) | -8 | 2,244 | -1 |
| t1 | -24 | 2,244 | -1 |
| crl_kd | -8 | 2,243 | -2 |
| rP_back / p_colnat / su_to_st | +8 / +8 / -8 | 2,242 | -3 |
| wl_writ_eq / cu_unwrapcur | +8 | 2,241 | -4 |
| sm_iflet (#3480 reverted it) | -8 | 2,240 | -5 |
| cu_match / ur9l / amp_inline / n_mapamt / nf_back | -8 / -8 / -16 / +8 / -24 | 2,239-2,237 | -6..-8 |
| ur3o / hkmut / ev_cb_local / ev_mint_key | -8 / +32 / -8 / +16 | 2,235 / 2,232 / 2,220 / 2,214 | |
| p_feecfg (`st.fee_configurable==false` at 334) / p_dc_empty | +8 | 2,201 / 2,194 | -44 / -51 |
| ur9d, ur3d, p_dc_frozen, p_docoin, p_coinpres, p_elseif, p_skip, p_289 | 0 | 2,245 | 0 |

Junk bound on vol334_back (one pure +8): 2,245 @ 27,400 = main, at the entry 0x190 or anywhere in the validate error
blocks 0x6e8-0x758. So the 334 placeholder is exactly a junk slot: a faithful +8 B change that is junk-neutral there would
remove it at no M cost. No +8 B gene in the library is (best -3).

## 3. ebe5387 (#3495, M 2,247, 3,123 slots): single + pair screen (131 rows)

`eq_main` true on the unedited capture. Junk bound on t1 here: 2,248 @ 27,400 (+1 over main) with two pure +8 at the
entry (0x140-0x190) and one neutral +8, so a faithful +24 B t1 fill is worth at most +1 M.

| dB | dM | genes |
| ---: | ---: | --- |
| 0 | 0 | byte-identical to main: K_st_ql_first, K_pool_prog_let, K_wl_ts_map, K_pu_match, K_sig_arr, K_wl_cr_deref, K_g_s7_tokzero, K_g_s7_tokamtne, r_getdot, n_amt_ge, n_flip0, n_checked, n_amtmin, n_lamvar, v_tmatch, v_hkclone, v_issome_if, v_fee_range, v_fee_lt1, v_cbnot, v_zero_ne, v_fee_gt, v_mayhem_req, su_hold, su_ns, x_hr_curve, x_cb_curve, r_lamvar, r_ifsub, r_rentref, n_atok, n_ge1, n_letr, n_ensmap, n_tnmap, n_match0, p_dc_frozen, p_docoin, p_coinpres, p_elseif, p_skip, p_289, p_shared, p_cb, p_co, p_pool, p_amp, e_rs, ev_auth_deref, ev_ts_map |
| +0 | +0 | n_amtmax |
| -24 | -1 | t1 |
| -8 | -1 | vol334_back |
| +0 | -1 | K_sh_fees_key, cs_old_fee_first, en_feesl |
| +0 | -2 | K_g_canedit_first, vol334_back+rP_back |
| -32 | -3 | t1+vol334_back |
| -8 | -3 | su_to_st |
| +0 | -3 | vol334_back+wl_writ_eq, vol334_back+cu_unwrapcur |
| +8 | -3 | p_colnat |
| +0 | -4 | vol334_back+p_colnat |
| +8 | -4 | cu_unwrapcur |
| +0 | -5 | su_to_st+cu_unwrapcur |
| -8 | -6 | cu_match |
| +0 | -6 | su_to_st+p_colnat |
| +0 | -7 | v_tswap, q_swap |
| +8 | -7 | n_mapamt, n_mapamt_flip, n_mapamt_and, n_mapamt_us, n_mapamt_m, n_eq0first, n_okamt |
| -24 | -8 | ev_nf_inline |
| +0 | -8 | vol334_back+n_mapamt |
| -24 | -10 | n_ensmatch, n_andthen |
| +0 | -10 | ev_ts_clockvar, cu_fee_first |
| -24 | -11 | n_mapamt_ens |
| +0 | -11 | e_ql_wl1 |
| -32 | -12 | K_cu_typed |
| -8 | -15 | K_cu_fee_replace |
| +0 | -15 | n_ensiflet, v_tletelse, tai_pa |
| +8 | -15 | nf_old |
| +24 | -15 | e_cb |
| +64 | -17 | K_w_ev_creator_first |
| +8 | -18 | cu_iflet_old |
| +0 | -19 | K_prep_match |
| -8 | -25 | ev_cb_local |
| -16 | -27 | r_inl |
| +0 | -28 | ev_nf_unwrap |
| -8 | -31 | tai_tv |
| +16 | -31 | ev_mint_key |
| -24 | -41 | tai_gl |
| +8 | -44 | p_feecfg |
| -80 | -46 | K_s_old_borrow |
| +8 | -51 | p_dc_empty |
| +0 | -78 | tai_mi |
| -64 | -121 | ev_ts_prepool |
| -24 | -126 | K_sh_accs_let |
| -96 | -143 | v_tokor |
| +88 | -144 | q_arr |
| -216 | -150 | e_ql_ref |
| -168 | -254 | t1+en_dlen |
| -88 | -254 | en_dlen_gt, en_dlen |
| -112 | -257 | K_ev_reset_shared |
| -592 | -282 | K_ev_ts_presig |
| -32 | -291 | r_letrent |
| +64 | -373 | e_nc |
| +64 | -376 | e_bk |
| +64 | -388 | e_au |
| +40 | -471 | K_g_s7_destscope |
| -184 | -523 | x_cr_curve |
| +272 | -532 | K_w_create_rev |
| +64 | -553 | K_sig_mint_acct |
| -200 | -586 | v_tcontains |
| +8 | -798 | p_296b |
| +8 | -817 | p_296a |
| +80 | -944 | ev_nc_target |
| +0 | -947 | n_tq |
| -27160 | -2238 | n_then |
| | | compile/apply errors: ev_hr_local |

Entry spellings for the t1 fill: `data_len()!=0` / `>0` drop the borrow check (-88 B, -254); `&FEES==owner` -1 at 0 B;
`*owner==FEES` is byte-identical (w14a77). n_then emits a 240 B execute (outlined body), an artifact.

## 4. Result

No landable change: best zero-loss measurement is main ebe5387 (0.67316 / 3,123 @ 27,400).

- The prices of the library genes are stable across 963d1ee, 13fe453 and ebe5387: about 50 fold to main's bytes, no single
  gene gains, the cheapest knobs are vol334_back (-8 B / -1), t1 (-24 B / -1), su_to_st (-8 / -3), p_colnat (+8 / -3).
- Pairs are not better than additive: vol334_back + every +8 B gene loses 2-8 (the 334 placeholder sits on a pure-junk slot,
  and no faithful +8 B gene is junk-neutral there); su_to_st + p_colnat / cu_unwrapcur -6 / -5; t1 + vol334_back -3.
- So a placeholder-removal or t1 repay needs a new faithful spelling that changes codegen, not a library knob.
- Not run (machine load reached ~120 at 23:30-00:50 and captures stopped finishing): X_st_rP, X_st_wle, the 0 B -1 pairs
  (K_sh_fees_key + cs_old_fee_first, en_feesl + cs_old_fee_first), t1 + three +8 B genes, and the rr*/lf*/evo*/tl*/sw*
  families (all losses on older mains in stitch11/12).
- Harvest (ledger + PRs, three passes): the only zero-loss leads above main were landed by their own lanes (#3480 q7,
  #3495 cs_blk). The rest are IR-only (brhead h289 irglue +4 at -8 B, irorder +18; raprio/curvestorereg RA forces;
  tag660 dup) or below main.
- Ledger: approach `stitch13`, keys `0x22a10-w14-{963d1ee,13fe453,ebe5387}-stitch13-<name>-v1`. `0x22a10-w14-963d1ee-stitch13-T_t3-v1`
  is a false compile-failed (busy workspace); t3 was the same as t1 in w14a89.
