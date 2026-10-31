# w14a64-cto-shiftpair: size-shift oracle pairs for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a53-cto-stitch11 (#3361) section 3. Ledger approach `shiftpair`, keys `0x22a10-w14-<main7>-shiftpair-<name>-v1`.
Tools (`tools/`, experiment only): `shift.py`/`rx.py`/`fnbin.py`/`segdiff.py`/`splice.py` (from w14a53),
`mcount.py` (w14a55), `cls.py` (w14a47), `shiftk.py` (w14a31), and new `jwhy.py <fn.bin> [+pos] [-pos]`: applies the pure
shift.py edit(s) and lists exactly which jumps / instructions change matched status (explains a shift-map entry).
`run.py <spec> [workers]` + `genes.py` (stitch11 library plus this lane's genes); run with `SRCBASE=<pristine main crate>`.

## 1. Shift map on main 2e1379d (M 2,194 at 27,400)

- Pure -8: best cand 0x16e8 (+5 M; the `stxdw [r10-0x8d8],r8` holder spill in the post-validate join). `jwhy.py`: only 2 of
  the 5 are jump distances (0x7d0->0x5708, 0x8b0->0x5830, both validate edges to the shared error tail at 0x5708/0x5830);
  the other 3 are local re-alignments that need that exact spill gone (RA, not a size knob). Any -8 in 0x800-0x1c00: +2.
- Pure +8: best entry block 0x180/0x1a0 (+1; the local `jne r0` at 0x178->0x1a0). 0x400-0x1c00: +1; 0x2000+: negative.
- Pairs (top-40 and a 256 B grid): +0x180/-0x16e8 +6, +0x54c0/-0x5a20 +4 (0x6d8->0x5708, 0x54b8->0x5830, 0x6370->0x5830),
  +0x2480/-0x5b20 +3.
- On the -8 lead `cu_iflet2` (curve fee `if let Some(f)=fee{..}`, 27,392 B, M 2,193) a pure +8 anywhere in cand
  0x5930-0x5af8 (sweep native arm: Rent / saturating_sub / ensure_rent_exempt / transfer_native) gives M 2,198 (main+4);
  0x5400-0x6100 gives +3.

## 2. Landed #3379 (main 0d945ea -> fc628cf): `cu_iflet2` + `wl_writ_eq`

`cu_iflet2` (-8 B, M -1) + `wl_writ_eq` (+8 B in the wallet head, the cu_iflet2 shift map's +8 zone): same M, slots 3192 -> 3183.

## 3. Polarity knob screen on fc628cf (`!x` -> `x==false`, every site)

`wl_writ_eq` is a pure block-order +8 knob, so every `!` site was screened (main M 2,195):

| gene | site | bytes | M |
| --- | --- | ---: | ---: |
| p_colnat | wallet `if collection_native==false\|\|coin_present` | +8 | 2,192 |
| p_feecfg | validate `st.fee_configurable==false` | +8 | 2,175 |
| p_dc_empty | wallet do_collect `data_is_empty()==false` | +8 | 2,145 |
| p_ammfz | sweep amm_frozen `data_is_empty()==false` | +16 | 2,192 |
| p_296a / p_296b | validate 296 | 0 | collapse (0.42) |
| p_dc_frozen, p_docoin, p_coinpres, p_elseif, p_skip, p_289, p_shared, p_cb, p_co, p_pool | | 0 | = main (p_289 1 raw loss) |

shift.py on p_colnat (27,408 B, M 2,192): a pure -8 anywhere in cand 0x3e00-0x5400 (the CPI AccountInfo clone run, no
calls between 0x3c80 and 0x4a20) or at 0x2600 gives M 2,198 = main +3.

## 4. p_colnat + CPI literal -8 moves (fc628cf, main 0.65758 / 3,192 slots)

Literals numbered in source order (1 TCF ctx pump_amm, 2 TCF coin vault ATA, 3 TCF vault ATA, 4 TCF program, 5 sharing
pool_authority, 6 authority, 7 global, 8 mint, 9 sharing program). `swK` swaps the lamports/data fields, `urK<f>` replaces a
re-read `a.<acct>.<f>` with `x.<f>`.

| pair | bytes | ratio | slots |
| --- | ---: | ---: | ---: |
| **p_colnat + ur5r** (pool_authority `rent_epoch:x.rent_epoch`) | 27,400 | **0.65848** | 3,229 |
| p_colnat + ur9l (sharing program `lamports:x.lamports.clone()`) | 27,400 | 0.65818 | 3,220 |
| p_colnat + ur3o (vault ATA `owner:x.owner`) | 27,400 | 0.65728 | 3,229 |
| p_colnat + sw3 | 27,400 | 0.62792 | |
| p_colnat + ur3d / ur9d / sw1 / sw2 / sw4..sw9 | 27,408 (0 B moves) | 0.6407-0.65658 | |

The 0.65848 pair was not landed: main moved to 304b03a (#3361 su_tafter) first, and after the merge it measured
0.65788 / 3,263 (= main ratio, more slots). #3361 also reverted #3379's two lines (stitch11's merge kept its side).

## 5. Main 304b03a (M 2,196): singles and pairs

Shift map: the validate-region -8 bonus is gone. Best pure pair +3 (+8 at entry 0x180 or 0x2060-0x24e0, -8 in the wallet
body 0x5cb0-0x62c0). Singles (M at size):

| gene | bytes | M | gene | bytes | M |
| --- | ---: | ---: | --- | ---: | ---: |
| cu_iflet2 | -8 | **2,197** | wl_writ_eq | +8 | 2,195 |
| ur5r | -8 | 2,196 | n_okamt / n_eq0first | +8 | 2,192 |
| ur9l | -8 | 2,195 | p_colnat | +8 | 2,196 |
| ur3o | -8 | 2,192 | w_cpfirst | +8 | 2,163 |
| ur9o | -16 | (0.65838 with p_amp) | e_ql_wl1 | +24 | 2,184 |
| w_bump_a, w_cc_and2, w_ccswap, w_dcif, w_docoinif, w_evfee_first | 0 | = main | e_sh_rev / e_ql_nat1 / w_cconly | 0 | 2,189-2,190 |

Pairs: **cu_iflet2 + p_colnat 0.65818 / 3,261 at 27,400 (M 2,197, 0 losses, differential 363/0)**; cu_iflet2 + ur5r +
p_colnat + wl_writ_eq 0.65818; cu_iflet2 + wl_writ_eq 0.65758; cu_iflet2 + n_okamt / n_eq0first 0.65698; ur5r + p_colnat 0.65788 (tie).
Not landed: before the PR went up, main moved to 39eb377 (#3386 w14a66 feeedge 0.66477), which contains cu_iflet2 itself.
`ur9o` (dropping the pump_fees owner re-read #3361 added) is -16 B at +0.0005: that is stitch11's su_tafter repay, left to it.

## 6. Main 39eb377 (M 2,219, 0.66477 / 3,230)

Shift map: best pure pair +4 (+8 at cand 0x54c0, the error edge after `call ..; ldxdw r8,[r10-0x878]` where the original
has `ldxdw r1; mov r9,r1` (RA), with -8 in the wallet body 0x5cb0-0x62c0, where ours spills the do_collect flag to
[r10-0x938] and the original keeps it in r8: RA again). On ur5r (27,392 B) the best +8 is cand 0x2468-0x24e8 or 0x54b8 (+2);
on p_colnat (27,408) the best -8 is in the native arm 0x5938-0x5ac8 (+2).

| trial | bytes | M | ratio |
| --- | ---: | ---: | ---: |
| main | 27,400 | 2,219 | 0.66477 |
| ur5r / p_colnat (singles) | -8 / +8 | 2,219 / 2,219 | |
| p_colnat + ur5r, wl_writ_eq + ur5r | 27,400 | 2,219 (tie; slots 3,269 / 3,230) | 0.66477 |
| p_colnat + ur9l, wl_writ_eq + ur9l | 27,400 | 2,218 | 0.66447 |
| p_colnat + ur3o / n_okamt + ur5r / p_colnat + wl_writ_eq + ur5r + ur9l | 27,400 | 2,213 / 2,214 / 2,216 | |
| p_colnat + n_andthen / n_ensmatch (native arm now -16) | 27,384 | 2,217 | |
| + wl_writ_eq | 27,392 | (not additive: wl_writ_eq 0 B there) | 0.66337 |
| p_colnat + n_atok/n_flip0/n_ge1/n_letr/n_match0/r_getdot2/r_ifsub/r_lamvar/r_rentref | 27,408 | 2,219 (0 B, identical) | |
| p_colnat + n_ensiflet / n_eq0first / n_mapamt / r_inl / r_letrent2 / n_tq | +8/+16/+16/-16/-32/+8 | 2,206 / 2,215 / 2,215 / 2,198 / 1,938 / 1,315 | |
| ur5r + sweep-head spellings (sh_af_if, sh_af_eqf, sh_rq_ne, sh_rq_let, p_amp, p_elseif2) | 27,392 | 2,219 (0 B) | |
| ur5r + sh_dest_ne / sh_dest_deref / sh_elseif_amp | 27,392 / 27,312 / 27,312 | 2,217 / 2,210 / 1,712 | |

## 7. Position -> best real knob -> M cost (39eb377)

| zone (cand) | pure value | real knobs found | real cost |
| --- | --- | --- | --- |
| +8 entry 0x180 / 0x2060-0x24e8 | +1 (+2 on ur5r) | p_feecfg (+8, M -20 on fc628cf); e_ql_wl1 +24; none at +8 that is free | >= 6 M |
| +8 error edge 0x54c0 | +1 alone, +4 with wallet -8 | none (orig byte is an RA `mov r9,r1`) | n/a |
| -8 wallet body 0x5cb0-0x62c0 | +2 | none: every wallet-body spelling is 0 B (do_collect spill is RA) | n/a |
| -8 native arm 0x5938-0x5ac8 | +2 on p_colnat | n_andthen/n_ensmatch are -16 (M -2); all other native spellings 0 B | -2 M at -16 |
| -8 CPI clone run 0x3e00-0x5400 | 0 | ur5r free, ur9l -1, ur3o -6, swK 0 B | 0 |
| +8 wallet head/gate | 0 | p_colnat free, wl_writ_eq free (-1 on 304b03a) | 0 |

Mechanism worth reusing: `if x==false` is a pure +8 B block-order knob versus `if !x` at some sites (wl_writ_eq,
p_colnat); `!= true` / `== true` forms are byte-identical. CPI literal re-read removals (`a.<acct>.<f>` -> `x.<f>`) are
-8 B (ur5r, ur9l, ur3o) or -16 B (ur9o) and often free.

## 8. Main 0d04cf4 (#3393 w14a72: ur9o + wl_writ_eq repay, 0.66507 / 3,228, M 2,220)

| trial | bytes | M | ratio / slots |
| --- | ---: | ---: | --- |
| wl_writ_not2 (back to `!is_writable`) / p_colnat / ur5r singles | -8 / +8 / -8 | 2,220 / 2,220 / 2,218 | |
| wl_writ_not2 + p_colnat | 27,400 | 2,220 (tie) | 0.66507 / 3,271 |
| wl_writ_not2 + cu_unwrapcur, ur5r + cu_unwrapcur | 27,400 | 2,219 | 0.66477 |
| p_colnat + ur5r / ur9l / ur3o | 27,400 | 2,218 / 2,217 / 2,217 | 0.66447-0.66417 |
| wl_writ_not2 + n_okamt / n_eq0first, ur5r + n_okamt | 27,400 | 2,215 | 0.66357 |

The free +-8 stock (p_colnat, wl_writ_eq/not, ur5r, cu_iflet2/unwrapcur) only ties on 39eb377 and 0d04cf4: the pure
shift value is now in zones (error-edge RA `mov`, wallet do_collect spill, native-arm join) with no source size knob.
