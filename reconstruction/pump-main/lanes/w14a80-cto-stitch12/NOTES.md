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

0-B folds (byte-identical or M-neutral): cd_holder_dest,
ev_auth_deref, ev_reset_m, ev_ts_map, n_amt_ge/amtmax/amtmin/atok/checked/ensmap/flip0/ge1/lamvar/letr/match0/tnmap, p_289.
Negative-size genes are all expensive in X: cu_match -8 (-6), lf_pr_dl -8 (-9), n_ensmatch -24 (-10), n_mapamt_ens -24
(-11), ev_hr_curve -8 (-14), lf_ea -16 (-17), e_ql_ref -72 (-27), ev_ts_prepool -56 (-88).

X + structural -B probes (0d04cf4): `validate(..,a.sharing_config.key)` / `let sk=a.sharing_config.key` -272 B (M -446),
`&a.sharing_config.key()` inline 2,075, dropping the `Ok::<_,Error>((..))?` tuple wrapper collapses (1,830); `&{sk}` / `&hk.0`
fold. C0 + crl_kd 27,368 / 2,222 (+2 at -32 B), C0 + crl_kd + hkmut 27,400 / 2,209, + p_colnat + wl_ts_clockvar 27,392 / 2,216; hoisting `let cr=..` out of the
`shared` expression (crh*) collapses (M ~1,915): the copy must stay inside the `&&` operand block.

## 5. Main 95a64ba (#3409 w14a82 holder-arg, 0.66986, M 2,236, 3,204 slots)

Shift map: best pure -8 is now **+5 (wallet body 0x5cb0) / +4 (native arm 0x5938-0x5ac8)**, best pure +8 +1 (entry
0x180/0x1a0), best pair +6.

| variant | bytes | M | note |
| --- | ---: | ---: | --- |
| main (m0, fresh) | 27,400 | 2,236 | 3,204 slots |
| **wn** (`!a.current_creator.is_writable`) | 27,392 | **2,238** | +2 at -8 B |
| sm (sharing `if let`) / rP (pool_authority `rent_epoch:x.rent_epoch`) | 27,392 | 2,237 | +1 at -8 B each |
| wn+sm / wn+rP | 27,384 | 2,234 | not additive |
| C0 (wn+sm+rP) | 27,376 | 2,236 | the 0d04cf4 +4 is gone |
| su_to_st | 27,392 | 2,233 | no longer free |
| wn + su_to_st | 27,384 | 2,236 | |
| hkmut | 27,432 | 2,236 | free +32 |
| p_colnat | 27,408 | 2,235 | |
| crl / crl_L | 27,472 | 2,238 / 2,239 | |
| X = C0 + crl_L | 27,448 | 2,239 | +3 at +48 B |
| X + su_to_st | 27,440 | 2,236 | |
| crl_L + wn + su_to_st + amp_inline | 27,440 | 2,234 | |
| n_andthen / n_ensmatch / n_mapamt_ens (native arm) | 27,376 | 2,229 / 2,229 / 2,228 | -24 B; the +4 pure zone does not survive the codegen change |
| r_inl | 27,384 | 2,220 | |
| n_andthen + p_colnat / n_ensmatch + p_colnat | 27,384 | 2,232 | |

Pairs at 27,400 (all <= main): wn + nf_pre_ev 2,236 (3,214 slots), wn + cu_unwrapcur 2,236 (3,215), wn + p_colnat 2,235,
sm/rP + nf_pre_ev / cu_unwrapcur 2,235 (3,203-3,204 slots: one token short of a slot-tiebreak win), sm/rP + p_colnat 2,234,
wn + ev_cb_local 2,233, wn + n_mapamt 2,231, wn + hkmut + amp_inline + su_to_st 2,231, wn + wl_ts_clockvar + sm/rP 2,231
(3,373-3,381 slots), wn + g_w_clock_local + sm 2,231, wn + rr5D 2,221, C0 + hkmut + su_to_st 2,220 (3,009 slots).

**Use for other lanes:** on 95a64ba, `wn` is a +2 M / -8 B knob and `sm`, `rP` are +1 M / -8 B. Any source lead that
costs +8 B (for example a validate-layout or Err306-placement source form, w14a78/w14a87 oracles: M +15..+28 at +8 B)
should be paired with `wn` first; a +16 B lead with `wn` + `sm` or `wn` + `rP` (both -2 jointly, so price them).

## 6. Landing candidate on 95a64ba: `ev_nf_let` + `wn` + `sm` (0.66986 -> 0.67166)

The 95a64ba single screen found **ev_nf_let** (`let nf=a.bonding_curve.creator_fee_bps;` before `pool_updated`, event field
`new_creator_fee_bps:nf`) at **+16 B, M 2,240 (+4)** (nf_blk / nf_post_a, the same read placed elsewhere, give the same).
It is repaid with the two -8 B knobs that are positive on this main:

1. `ev_nf_let`: event new fee read once into `nf` right after the curve block (+16 B);
2. `wn`: wallet `if !a.current_creator.is_writable{return ..}` (was `==false`, -8 B);
3. `sm`: sharing CPI `if let Some(val)=sharing_update{..}` (was `match .. None=>{}`, -8 B).

| | main 95a64ba | this PR |
| --- | ---: | ---: |
| ratio | 0.66986 | **0.67166** |
| M | 2,236 | 2,242 |
| slots_diff | 3,204 | 3,215 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034/1034 | 1034/1034, no gains or losses |

Differential: 363 cases, 0 mismatches. Ledger key `0x22a10-w14-ecea702-stitch12-nfl_wn_sm-v1` (built on 95a64ba source;
the key took the baseline sha current at run start).
Same ratio with more slots: ev_nf_let + wn + rP (3,223), + ev_reset_early (3,215), nf_blk / nf_post_a + wn + sm (3,215).
Below: ev_nf_let + sm + rP 0.67136, + wn + cu_match 0.67136, + cu_match + ev_reset_early 0.67106, + wn + su_to_st 0.67076.
Off size: ev_nf_let + C0 0.67206 @27,392 (M 2,243), + wn + amp_inline 0.67176 @27,392 (M 2,242).

## 7. Main ecea702 (#3430 w14a88: wn + validate volatile placeholder, 0.67076, M 2,239, 3,123 slots)

#3430 landed `wn` itself (repaid with a +8 B volatile read), so the section 6 composite became ev_nf_let + sm + one more -8:

| ev_nf_let + | bytes | M | slots |
| --- | ---: | ---: | ---: |
| **sm + rP** | 27,400 | **2,244** (0.67226) | 3,123 |
| rP + ev_reset_early / nf_blk + sm + rP / nf_post_a + sm + rP | 27,400 | 2,244 | 3,123 |
| sm + cu_match / rP + cu_match / cu_match + ev_reset_early | 27,400 | 2,243 | 3,123 |
| amp_inline | 27,400 | 2,243 | 3,142 |
| sm (alone, +8) / nothing (+16) | 27,408 / 27,416 | 2,241 / 2,240 | |
| sm + su_to_st | 27,400 | 2,240 | 3,211 |

ev_nf_let + sm + rP measured 0.67226 / 3,123 / 27,400, 1034/1034, 0 losses, differential 363/0 (unstripped sha
c3ea5d9310d855ee). Before this lane could land it, **w14a86-cto-t1vaultname landed the identical function as #3437**
(963d1ee: same fn.bin bytes), so this lane has no landing of its own.

## 8. Main 963d1ee (#3437, 0.67226, M 2,244, 3,123 slots)

Shift map: best pure -8 is 0, best pure +8 +1 (entry 0x180/0x1a0), best pair +1. Size-pair levers are now worth at most one
token; further gains must come from codegen changes like ev_nf_let (+4 real at +16 B on 95a64ba).
