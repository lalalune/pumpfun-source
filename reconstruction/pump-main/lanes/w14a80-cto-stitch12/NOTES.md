# w14a80-cto-stitch12: integrator lane for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a53-cto-stitch11-2 (#3396) and w14a64-cto-shiftpair-2 (#3394). Ledger approach `stitch12`, keys
`0x22a10-w14-<main7>-stitch12-<variant>-v1`.

Tools (experiment only): `genes.py` (stitch11-2 library `genes_s11b.py` + shiftpair genes + this lane's genes at the end),
`run.py <spec> [workers]` (measure.sh queue, per-base `results-<main7>.jsonl`, keeps `fn.bin`), `q.sh` (sequential spec
queue), `tools/summ.py <prefix> [base_bytes base_M]` (exact M per result row), `tools/dis.py` (minimal sBPF disassembler for
fn.bin / `orig`), `tools/ops.py` (difflib opcode listing: where a candidate has extra tokens), plus `shift.py`, `shiftk.py`,
`jwhy.py`, `mcount.py`, `rx.py`, `segdiff.py` from the two parent lanes.

M = matched masked rx tokens against the original (`mcount.py`). At 27,400 B a candidate beats main 0d04cf4 (M 2,220,
0.66507) only with M >= 2,221 (0.66537).

## 1. Shift map on main 0d04cf4 (M 2,220 at 27,400)

`shift.py`: best pure +8 is +1 (entry 0x180/0x1a0, or 0x6200-0x62d0); best pure -8 is +2 (wallet body 0x5cb0-0x62c0, the
do_collect spill); best pair +3. Unchanged from shiftpair-2 section 8: the pure-size value is small.

## 2. Free knob stock on 0d04cf4 (measure.sh, exact M)

| variant | bytes | M | note |
| --- | ---: | ---: | --- |
| main (m0, fresh) | 27,400 | 2,220 | reproduces the baseline (3,228 slots) |
| wl_writ_not2 + su_to_st (`wn_st`) | 27,384 | 2,220 | the two free -8 B stack (-16 B, 0 M) |
| C0 = wl `!` + sharing `if let` + pool_authority `rent_epoch:x.rent_epoch` (w14a72) | 27,376 | **2,224** | +4 at -24 B |
| crl (w14a77: `{let cr=a.bonding_curve.creator;a.sharing_config.key()==cr}`) | 27,472 | 2,222 | +2 at +72 B |
| **crl_L** (`{let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}`) | 27,472 | **2,223** | +3 at +72 B |
| crl_sk / crl_ref / crl_eq | 27,472 | 2,222 | |
| crl_kd / crl_kdL (`*a.sharing_config.key`) | 27,392 | 2,218 / 2,214 | |
| crl + wn_st + amp_inline | 27,440 | 2,224 | |
| crl_L + wn_st + amp_inline | 27,440 | 2,225 | |
| **X = C0 + crl_L** | 27,448 | **2,227** | **+7 M at +48 B** (the best off-size composite found) |
| C0 + crl | 27,448 | 2,226 | |
| X + su_to_st / C0 + crl + su_to_st | 27,440 | 2,226 / 2,225 | |
| C0 + p_colnat | 27,384 | 2,221 | |
| C0 + hkmut (free +32 on main) | 27,408 | 2,211 | hkmut costs 13 on C0 |

The crl / crl_L gain is the 8-instruction creator copy at cand 0x80-0xc0. It lines up with the original's 4-word copy runs at
orig 0x100-0x198 (holder_key = hk.0 and the sharing-key copy). `shiftk.py` on X: a pure -48 B in validate (cand 0x9d0-0x1f50)
is worth +1..+2 more (M 2,228-2,229). So **X lands as soon as any faithful -48 B costs <= 6 M in X's context.**

## 3. Repays of X to 27,400 (measure.sh)

| X + | bytes | M |
| --- | ---: | ---: |
| su_to_st + amp_inline + n_andthen / n_ensmatch | 27,400 | 2,217 |
| n_andthen + amp_inline + ur9l | 27,400 | 2,216 |
| sh_prog_let + su_to_st + ur9l | 27,400 | 2,216 (3,035 slots) |
| sh_prog_let + amp_inline | 27,400 | 2,215 |
| n_andthen + amp_inline + ur3o | 27,400 | 2,212 |
| g_s7_dborrow (`*a.holder_creator_vault.key!=dest`, -80) + hkmut | 27,400 | 2,200 |
| singles: amp_inline -16 (-7), n_andthen -24 (-10), sh_prog_let -32 (-12), g_s7_dborrow -80 (-14) | | |

## 4. Single-gene screen on X (160 genes of the library that apply and change the source)

See section 2 of the summary table in SUMMARY.json. 0-B folds (byte-identical or M-neutral): cd_holder_dest,
ev_auth_deref, ev_reset_m, ev_ts_map, n_amt_ge/amtmax/amtmin/atok/checked/ensmap/flip0/ge1/lamvar/letr/match0/tnmap, p_289.
Negative-size genes are all expensive in X: cu_match -8 (-6), lf_pr_dl -8 (-9), n_ensmatch -24 (-10), n_mapamt_ens -24
(-11), ev_hr_curve -8 (-14), lf_ea -16 (-17), e_ql_ref -72 (-27), ev_ts_prepool -56 (-88).
