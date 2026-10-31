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

## 3. ebe5387 (#3495): screen in progress

(see the next commit)
