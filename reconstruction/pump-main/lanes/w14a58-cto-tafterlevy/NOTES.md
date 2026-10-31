# w14a58-cto-tafterlevy: size-complement pairing of su_tafter / c_ammp with the le_vy1 validate closure

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 6330811 (0.65698, M 2,193), 2e1379d (0.65728, M 2,194; #3369 sh_iflet, #3372 wallet `!is_writable`),
fc628cf (0.65758, M 2,195; #3378, #3379) and 39eb377 (0.66477, M 2,219; #3361 landed tafter6 + amm_present, #3386 fee edge).
Ledger: approach `tafterlevy`, keys `0x22a10-w14-{6330811,2e1379d,fc628cf,39eb377}-tafterlevy-*-v1` (the r6 pair rows were
first recorded under 2e1379d keys by mistake at 18:47 and re-recorded under fc628cf; the fc628cf rows are the right ones).

Oracle: w14a21/w14a42's raw-IR capture + `opt -O3` + `llc` (`tools/capvar.sh`, `rx.py`, `q.py`), repointed at this lane.
`m` (no edit) reproduces main on both bases (`eq_main: true`, 0.65698 / 0.65728 at 27,400). `M` = exact matched original
instructions (`tools/mr.py`); ratio = 2M/(n_orig+n_cand), so at 27,400 B main needs M >= 2,195 to be beaten on 2e1379d.
Genes are in `e/hb.py` (w14a21 `v7c`, w14a42 `ny`/`le`/`sh_iflet`/`ny_*`, plus this lane's `tafter`, `tafter6`, `ammp`
and the `in_*` closure merges); `e/mk.py name a+b+c` composes them, `e/pool.py` adds the genes47 / size-knob / knob8 /
stitch11 libraries.

Genes:
- `tafter` = w14a38 su_tafter: `}else{let r=(false,Some(args.0),true);target=st.creator;r}` in the sharing tuple tree.
- `tafter6` = w14a38 f6: the same with `target=a.bonding_curve.creator`.
- `ammp` = w14a38 s_amm_present: `let amm_present=!..data_is_empty();let amm_frozen=amm_present&&..`.
- `le_vy1` = w14a21 validate as an immediately-called closure (`v7c`) + `let new=new;` at the non-holder arm (`ny`) +
  306 `let Some(t)=new else{..}` (`le`). `le_v7c` = v7c + le.

## Result 1: the two leads do not compose (main 6330811, 0.65698, M 2,193)

| name | spec | bytes | ratio | M | jM |
| --- | --- | ---: | ---: | ---: | ---: |
| m | main | 27,400 | 0.65698 | 2,193 | 2,225 |
| t_sh | tafter + sh_iflet | 27,352 | 0.65877 | 2,197 | 2,226 |
| tafter | su_tafter | 27,360 | 0.65867 | 2,197 | 2,225 |
| tafter6 | f6 | 27,368 | 0.65857 | 2,197 | 2,225 |
| ca_sh | c_ammp + sh_iflet | 27,368 | 0.65827 | 2,196 | 2,227 |
| c_ammp | tafter + ammp | 27,376 | 0.65788 | 2,195 | 2,226 |
| h0 | tafter6 + ammp | 27,384 | 0.65748 | 2,194 | 2,226 |
| tafter_a_b2 / tafter6_a_b2 | tafter + ammp + v7c+ny+le+sh_iflet | 27,424 | 0.65579 | 2,190 | 2,232 |
| tafter_b2 | tafter + v7c+ny+le+sh_iflet | 27,408 | 0.65538 | 2,188 | 2,231 |
| n_b2 | v7c+ny+le+sh_iflet (w14a42's best) | 27,432 | 0.65479 | 2,187 | 2,231 |
| tafter_le_vy1 | tafter + le_vy1 | 27,408 | 0.64640 | 2,158 | 2,200 |
| le_vy1 | | 27,432 | 0.64581 | 2,157 | 2,200 |
| tafter_vy1 | tafter + v7c+ny | 27,408 | 0.64520 | 2,154 | 2,275 |
| tafter_a2 | tafter + v7c+le+sh_iflet | 27,376 | 0.60902 | 2,032 | 2,151 |
| tafter_le_v7c | tafter + v7c+le | 27,384 | 0.60803 | 2,029 | 2,150 |

- `tafter6_*` and `tafter_*` composites are token-identical whenever the closure is present.
- The sizes are roughly additive (-40 B + 32 B = 27,392 / 27,408), the matches are not: tafter's +4 in orig 0x1800-0x1c00
  falls to +2 under the closure, and without `ny` (le_v7c, a2) tafter flips the TCF/sweep register assignment
  (orig 0x2c00-0x3800 -101 M).

## Result 2: merging the two in the non-holder arm (6330811)

| name | form | bytes | M |
| --- | --- | ---: | ---: |
| T_ny_c / T_ny_t (+le, +le+sh) | tafter, closure, `let new=new;` at the closure start / before `let target` | 27,408-27,416 | 2,126-2,127 |
| T_ny_r (+sh) | tafter, closure, `let new=&new;` + `*new` let-else | 27,376-27,384 | 2,029-2,032 |
| T_ny_h (le, b2) | tafter, closure, copy in the holder arm | 27,360-27,368 | 2,008 |
| Io_* / It_* / Itn2_* | the whole `(collect_old,sharing_update,skip)` tree moved inside the closure (orig form / tafter / tafter + a trailing copy) | 27,960-28,072 | 1,298-1,357 |
| Itn1_* | tree inside, non-holder arm `let new=new;let r=(false,Some(new),true);` | 27,656-27,696 | 1,413-1,453 |
| I6_* | tree inside, f6 | 27,656-27,664 | 1,291-1,318 |

Moving the tree into the closure makes the closure return a 4-field tuple through memory: +260..+670 B, -840 M.
No placement of the copy beats the plain composite.

## Result 3: on main 2e1379d (sh_iflet landed) the lead is unchanged and the closure is still a net loss

| name | bytes | ratio | M | jM |
| --- | ---: | ---: | ---: | ---: |
| m | 27,400 | 0.65728 | 2,194 | 2,227 |
| tafter | 27,360 | 0.65897 | 2,198 | 2,227 |
| tafter6 | 27,368 | 0.65887 | 2,198 | 2,227 |
| c_ammp | 27,376 | 0.65847 | 2,197 | 2,228 |
| h0 | 27,384 | 0.65808 | 2,196 | 2,228 |
| ammp | 27,416 | 0.65648 | 2,192 | 2,228 |
| tafter_le_vy1 (= tafter6_le_vy1) | 27,416 | 0.65588 | 2,190 | 2,232 |
| le_vy1 | 27,440 | 0.65529 | 2,189 | 2,232 |
| tafter_a_le_vy1 | 27,432 | 0.65539 | 2,189 | 2,233 |
| le_v7c | 27,432 | 0.65000 | 2,171 | 2,290 |
| tafter_le_v7c / tafter_a_le_v7c | 27,384 / 27,400 | 0.60833 / 0.60785 | 2,030 / 2,029 | |

Exact matches per 0x400 of the original, minus main (`tools/exact.py`, 2e1379d):

| orig region | tafter | c_ammp | h0 | le_vy1 | tafter_le_vy1 | tafter_a_le_vy1 | tafter_le_v7c |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0x0400 | 0 | +1 | 0 | +4 | +4 | +4 | +2 |
| 0x0800 | +1 | +1 | +1 | +10 | +10 | +10 | +9 |
| 0x0c00 | 0 | 0 | 0 | +3 | +3 | +3 | -24 |
| 0x1000 | 0 | 0 | 0 | -5 | -5 | -5 | -5 |
| 0x1400 | -1 | -1 | -1 | -1 | -2 | -2 | -2 |
| 0x1800 | +4 | +4 | +4 | 0 | +2 | +2 | -4 |
| 0x1c00-0x2000 | 0 | 0 | 0 | -2 | -2 | -1 | -12 |
| 0x2400-0x3c00 | 0 | +1 | +1 | -9 | -9 | -8 | -114 |
| 0x4000-0x5400 | 0 | 0 | 0 | -1 | -1 | -1 | 0 |
| 0x5800-0x6800 | 0 | -3 | -3 | -4 | -4 | -7 | -12 |
| total | +4 | +3 | +2 | -5 | -4 | -5 | -164 |

The closure still sheds ~9 M of spill colour in orig 0x2400-0x3c00 and 4 in 0x5800, which tafter does not repay.

## Result 4: size-repay screen on the tafter base (main 2e1379d; tafter = 27,360 B, M 2,198)

103 genes (all 37 applicable stitch11 genes, the size-knob catalog `K.*`, knob8 `k8.*` and the first genes47 `g.*`) were
stacked on su_tafter. 64 are token-identical to it. Every size-adding gene costs at least 3 M; tafter needs +40 B for at most 3 M.

| gene on tafter | bytes | M (Δ) |
| --- | ---: | ---: |
| s.cu_iflet (curve fee `if let`, landed later as #3379) | -8 | 2,198 (0) |
| k8.wl_writ_eq (`is_writable==false`, also in #3379) | +8 | 2,195 (-3) |
| K.wl_ts_clockvar / K.g_w_clock_local | +16 | 2,195 (-3) |
| s.ev_nf_let | +24 | 2,192 (-6) |
| s.n_mapamt, s.ev_cb_local | +8 | 2,190 (-8) |
| K.cu_replace, g.c_hr_cb | +8 | 2,184 (-14) |
| k8.wl_ixlit | +32 | 2,181 (-17) |
| s.ev_mint_key, s.ev_nf_unw | +16 / +24 | 2,168 / 2,169 |
| s.pu_own (the only gene landing tafter at 27,400) | +40 | 2,067 (-131) |

## Result 5: main fc628cf (0.65758, M 2,195): pairs and the h0_cu near miss

`cuunw` = revert of #3379's curve fee if-let (`curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);`, +8 B).

| name | spec | bytes | M |
| --- | --- | ---: | ---: |
| m | main | 27,400 | 2,195 |
| tafter / tafter6 | | 27,360 / 27,368 | 2,199 / 2,199 |
| t6_cu | tafter6 + cuunw | 27,376 | 2,197 |
| c_ammp / ca_cu | tafter + ammp (+ cuunw) | 27,376 / 27,384 | 2,197 / 2,197 |
| h0 / **h0_cu** | tafter6 + ammp (+ cuunw) | 27,384 / **27,392** | 2,196 / **2,197** |
| ca_nf | c_ammp + ev_nf_let | 27,400 | 2,195 (tie, = stitch11 ca_nflet) |
| ca_ck_cu, h0_ck, h0_lc, t6_nf_cu, t_nf_ck, J.K.wl_ts_clockvar+wlnot | | 27,400 | 2,192-2,194 |
| h0_cu + s.n_mapamt / s.ev_cb_local / K.cu_replace | | 27,400 | 2,192 / 2,191 / 2,185 |

h0_cu is 8 B short with 2 M to spare: one +8 B change costing at most 1 M lands it above main
(M 2,196 at 27,400 = 0.65788). `tools/s11/shift.py` on h0_cu: a pure +8 is free (0) anywhere in the validate block
(cand 0x490-0x5d0) and +1 at the entry (0x180/0x1a0) or in the wallet tail (0x61f8-0x62c8); elsewhere it costs 1-11.

Validate and entry spellings on h0_cu (all 27,392 B unless noted, none adds size without loss):
- token-identical (M 2,197): ny, v_cbnot, v_frev, v_fsplit (`!(1..=max).contains`), v_hdis, v_hkclone, v_hrne, v_hsplit,
  v_icref, v_newne, v_newsome, v_tmatch, v_zero, v_zeroeq, en_own, en_qany, tr_cb, tr_hr, tr_okq, tr_sk;
- worse: v_icrev 2,190, v_hrnot 2,184, le 2,182, en_qnat 2,190, v_feeiflet (+8 B) 2,109, v_icsplit 1,868,
  en_qref 2,051 (-216 B), en_mintref 1,901 (+248 B), en_hk1/en_hk2 1,848.

Wider gene screen on h0_cu (40 knob8 / size-knob genes before main moved): 29 token-identical, the rest -1..-5 M;
size-adding ones K.wl_ts_clockvar / K.g_w_clock_local +16 B at -3 M. No +8 B change at <= 1 M was found.

## Result 6: main 39eb377 (0.66477, M 2,219) carries the tafter6 + amm_present lead; the closure still loses

#3361 (w14a53 stitch11) landed this lane's h0 pair (tafter6 + ammp) with a pump_fees owner re-read as the size repay, and #3386
then added the fee-Some edge block. Re-test of the closure on that main:

| name | spec | bytes | M | jM |
| --- | --- | ---: | ---: | ---: |
| m | main 39eb377 | 27,400 | 2,219 | 2,250 |
| tst | `target=st.creator` in the tafter tuple (revert f6) | 27,392 | 2,219 | 2,250 |
| noammp | revert amm_present | 27,384 | 2,217 | 2,249 |
| le_vy1 (= tst_le_vy1) | v7c+ny+le | 27,440 | 2,211 | 2,254 |
| na_le_vy1 (= na_tst_le_vy1) | noammp + le_vy1 | 27,424 | 2,212 | 2,253 |
| vy1 / tst_vy1 / na_vy1 | v7c+ny | 27,424-27,440 | 2,207-2,208 | 2,328 |
| le_v7c | v7c+le | 27,416 | 2,012 | 2,130 |

Per 0x400 of the original, le_vy1 minus main: 0x400 +4, 0x800 +9, 0xc00 +3, 0x1000 -5, 0x1400 -1, 0x1800 -2, 0x2000 -2,
0x2400 -2, 0x2800 -2, 0x2c00 +1, 0x3800 -2, 0x3c00 -4, 0x4800 -1, 0x5400 -1, 0x5800 -3, 0x5c00 -1, 0x6000 +1 (total -8).
The closure's validate gain (+16) is stable across five mains, and so are its losses: -5 in the fee errors (0x1000) and
~-19 of spill colour spread over 0x1400-0x5c00. `tst` is a new free -8 B knob on 39eb377 (token-identical matches).

## Conclusion

- The size-complement pairing of the two validate-head leads is a dead end: sizes add, matches do not (best composite on any
  main is 2-9 M below main at its size). The closure needs about +9 M from somewhere else to pay for its own colour losses
  before any size pairing helps.
- The tafter half of the pairing was worth it on its own and is now on main (#3361).
- Leftover free knobs on 39eb377: `tst` (-8 B, 0 M). Free +8 positions (shift oracle on h0_cu, fc628cf): validate block and
  entry; any faithful +8 there pairs with `tst`.
