# w14a53-cto-stitch11: integrator lane for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Ledger approach `stitch11`, keys `0x22a10-w14-<main7>-stitch11-<variant>-v1`. Tools: `genes.py` (stitch10 library plus
new genes at the end), `run.py <spec> [workers]` (measure.sh queue; per-base `results-<main7>.jsonl`, keeps `fn.bin`),
`tools/fnbin.py` (extract the admin_cto bytes of a .so), `tools/segdiff.py` + `tools/splice.py` (from w14a38).

Note: the 14 `0x22a10-w14-0fbf8da-stitch11-df_*-v1` ledger rows marked compile-failed were fastbuild workspace-lock
failures caused by this lane (BlockingIOError), not compile errors. `run.py` now re-queues on that error.

## 1. Near-tie panel (w14a26 stitch10 list) on main 0fbf8da (0.65578, 3,280 slots)

| variant | ratio | bytes | note |
| --- | ---: | ---: | --- |
| main (m0, fresh measure.sh) | 0.65578 | 27,400 | reproduces the baseline |
| cs_swap3, c_ce_cr, n_hk_direct, cmp_pool_rev, cmp_fees_rev, sh_iflet+cu_unwrapcur | 0.65548 | 27,400 | one quantum below main |
| pu_amm_key | 0.65508 | 27,400 | |
| pre_cb_match, pre_cb_not | 0.65578 | 27,400 | tie, distinct sha |
| v_hr_ne | 0.65578 | 27,400 | tie, 1 raw loss |
| sh_iflet | 0.65558 | 27,392 | |
| cu_match (w14a27 t41) | 0.65528 | 27,392 | |
| pu_own (owner-first pool gate) | 0.65059 | 27,408 | |
| w14a27 d4 (token arm `.and_then`) | 0.65528 | 27,368 | |
| w14a27 s_frozen_first alone | 0.62257 | 27,448 | |
| **d4 + s_frozen_first** | **0.65648** | 27,392 | +0.0007 at -8 B |
| **wl_writ_not** (`!a.current_creator.is_writable`, revert of wl_writ_eq) | **0.65618** | 27,392 | +0.0004 at -8 B |
| wl_writ_not + cu_unwrapcur / + ev_cb_local | 0.65548 / 0.65458 | 27,400 | repay loses |

## 2. Main d371f97 (0.65638): the d4 + s_frozen_first lead and +8 B repays

| variant | ratio | bytes | slots |
| --- | ---: | ---: | ---: |
| d4 + s_frozen_first (`d4ff`) | 0.65708 | 27,392 | |
| wl_writ_not | 0.65678 | 27,392 | |
| d4ff + wl_writ_not | 0.65628 | 27,384 | (not additive) |
| sh_iflet | 0.65618 | 27,392 | |
| **d4ff + cu_unwrapcur** | **0.65698** | **27,400** | 3,193, 0 losses |
| d4ff + n_cb_fwd / cu_replace / c_hr_cb | 0.65488 / 0.65428 / 0.65428 | 27,400 | |
| d4ff + wl_writ_not + wl_ts_clockvar | 0.65518 | 27,400 | 3,355 |
| d4ff + wl_ts_clockvar + sh_iflet | 0.65518 | 27,400 | |
| wl_writ_not + n_cb_fwd / cu_replace / c_hr_cb / clockvar+sh_iflet / cu_unwrapcur / ev_cb_local | 0.65428 / 0.65339 / 0.65428 / 0.65488 / 0.65548 / 0.65458 | 27,400 | |

Singles on d371f97 (size probes): cu_unwrapcur 0.65538 @27,408; ev_cb_local 0.65449 @27,408; lf_pr_dl 0.65548 @27,400;
r_getdot, n_amt_ge, cd_holder_dest, ev_reset_m, sh_nonefirst = main (0 B); r_letrent 0.65208 @27,384; sw_ifskip 0.51932 @27,416;
ev_nf_unw 0.6483 @27,424; lf_au_dl 0.63642 @27,416; lf_ea 0.65338 @27,376; lf_mi 0.63811 @27,400; lf_gl 0.63943 @27,440;
pargs_hr_local 0.6479 @27,432; ev_nf_let 0.65459 @27,424; ev_hr_curve 0.65348 @27,392; wl_ts_clockvar 0.65588 @27,416.

d4ff + cu_unwrapcur is exactly what w14a50-cto-frozenrepay landed independently as #3358 (main 6330811, 0.65698,
byte-identical fn). This lane's copy was never pushed.

## 3. Size-shift oracle (w14a31 `shift.py`, copied to `tools/`)

`tools/shift.py <fn.bin>` inserts a junk 8 B slot at each block start (+8) or deletes one unmatched insn (-8), fixes the
crossing jumps and scores M. It isolates the pure jump-distance part of a size knob.
- On d4ff (d371f97, M 2,193 at 27,392): a pure +8 anywhere in cand 0x5930-0x5ca8 (sweep native arm, ensure_rent_exempt /
  transfer_native, and the inlined wallet head: executable / owner memcmp / token_frozen) is **+4 M**; elsewhere <= +1.
  The real +8 knobs tried are all in the tail (curve update / event), which explains why they cost 2-4 M.
- On main 6330811 (M 2,193 at 27,400): best pure -8 is cand **0x16e8 (+5 M)**, a spill store in the validate/flag block
  (`stxdw [r10-0x8d8], r8`, orig ~0x24188); best +8 is at the entry block 0x180/0x1a0 (+1 M); best pair +0x180/-0x16e8 is
  **+6 M** (~+0.0018). So any faithful -8 B inside the validate result/flag block costing <= 4 M, plus +8 B in the entry
  block, would beat main.

## 4. Main 6330811 (#3358, 0.65698, M 2,193, Lo 3,339 / Lc 3,337 tokens)

`tools/mcount.py <fn.bin>...` prints M (matched rx tokens), token counts and ratio. At 27,400 B a candidate beats main only
with **M >= 2,194** (0.65728). Every "tie" below is M 2,193; every -8 B "gain" below is pure size (same or lower M, one token
fewer).

| variant | ratio | bytes | M | note |
| --- | ---: | ---: | ---: | --- |
| cu_iflet2 (`if let Some(f)=fee{..}`, revert of #3358's repay) | 0.65708 | 27,392 | 2,193 | size only |
| wl_writ_not / sh_iflet | 0.65678 | 27,392 | 2,192 | |
| w14a38 `su_tafter + s_amm_present` (ca) | 0.65788 | 27,376 | **2,195** | +2 M at -24 B |
| ca + ev_nf_let (+24) | 0.65698 | 27,400 | 2,193 | tie |
| cu_iflet2 + n_mapamt (native arm `..map(\|()\|amount)}else{Ok(amount)}`, +8) and 4 spellings of it | 0.65698 | 27,400 | 2,193 | tie (3,195 slots) |
| wl_writ_not + n_mapamt | 0.65698 | 27,400 | | tie (3,199 slots) |
| cu_iflet2 + wl_writ_not + sh_iflet + ev_nf_let | 0.65698 | 27,400 | | tie (3,197 slots) |
| sh_iflet + n_mapamt | 0.65668 | 27,400 | | |
| n_hk_direct, c_ce_cr, cmp_pool_rev, cmp_fees_rev | 0.65668 | 27,400 | | one quantum below |
| pre_cb_match, pre_cb_not, wl_owner_eqsys | 0.65698 | 27,400 | | distinct-sha ties |
| v_hr_ne | 0.65698 | 27,400 | | tie, 1 raw loss |
| pu_amm_key | 0.65628 | 27,400 | | |
| ev_cb_local | 0.65538 | 27,408 | | |
| n_ensiflet / n_ensmatch / n_andthen / n_tq | 0.65249 / 0.65458@27,376 / 0.65458@27,376 / 0.37957 | | | |
| n_flip0, wl_exec_true, wl_writ_netrue, wl_owner_deref, wl_frozen_true, n_checked, n_amtmin, n_amtmax, n_lamvar | = main | | | byte-identical folds |
| wl_ts_clockvar (+16) with any -8 / -16 partner | 0.65488-0.65598 | | | +80 slots: loses |

## 5. The w14a38 su_tafter lead on 6330811 and its size repay

`su_tafter` (shared non-holder arm `else{let r=(false,Some(args.0),true);target=st.creator;r}`) alone is **M 2,197 at
27,360 B** (0.65867, +4 M at -40 B). `s_amm_present` alone is +16 B, M 2,190. Together (`ca`) M 2,195 at 27,376 B.
`tools/shift.py` on su_tafter: no pure +8 position is worth more than +1 M, so the repay must be codegen-neutral, and
every real +8..+24 B knob costs 3-6 M in su's context:

| su_tafter + | bytes | M | ratio |
| --- | ---: | ---: | ---: |
| (alone) | 27,360 | 2,197 | 0.65867 |
| nf_pre_ev (`let nf` just before the event, +8) | 27,368 | 2,194 | 0.65767 |
| wl_ts_clockvar (+16) | 27,376 | 2,194 | 0.65758 |
| ev_nf_let (+24) | 27,384 | 2,193 | 0.65718 |
| n_mapamt / ev_cb_local (+8) | 27,368 | 2,191 | 0.65677 |
| n_cb_fwd | 27,368 | 2,192 | 0.65707 |
| c_hr_cb / cu_replace / f_iflet / e_mint_key / x_cp_inline / x_dcol_rev | | | 0.632-0.655 |
| s_amm_present + nf_pre_ev (`ca_nfev`) | 27,384 | 2,195 | 0.65778 |
| s_amm_present + ev_nf_let / nf_post_a / nf_blk | 27,400 | 2,193 | 0.65698 (tie) |
| ca_nfev + wl_ts_clockvar | 27,400 | | 0.65668 |
| ca_nfev + n_mapamt + ev_cb_local (+ pre_cb_match / pre_cb_not / wl_owner_eqsys) | 27,400 / 27,392 | | 0.65348-0.65398 |
| ca_nfev + clockvar + {map+ci, map+wl, cb+ci, cb+sh, map+hr_curve} | 27,400 | | 0.65219-0.65578 |
| su + ev_nf_let + clockvar / su + nf_pre_ev + map + cb + clockvar / su + ev_nf_let + map + cb | 27,400 | | 0.65608 / 0.65309 / 0.65339 |

Validate spellings (6330811): v_tmatch, v_hkclone, v_issome_if, v_fee_range fold to main's bytes; v_tletelse 0.65249;
v_tokor 0.61751 @27,264.

Tie-composite lottery on 6330811 (stopped when #3369 landed): pairs/triples of the distinct-sha ties
(ci_mapamt `cm`, wl_owner_eqsys `oe`, pre_cb_match `pm`, pre_cb_not `pn`) all stay at 0.65698 (3,193-3,195 slots);
each tie + a one-quantum-below gene (n_hk_direct, c_ce_cr, cmp_pool_rev, cmp_fees_rev) is 0.65668. The ties do not add.

## 6. Main c3e5b51 (#3369, 0.65698 / 3,182 slots) panel

| variant | ratio | bytes | slots |
| --- | ---: | ---: | ---: |
| su_tafter | 0.65867 | 27,360 | (M 2,197) |
| su_r2 (su_tafter with `target=a.bonding_curve.creator`) | 0.65857 | 27,368 | (M 2,197: a free +8 B over su_tafter) |
| su_tafter + {v_zero_ne, v_mayhem_req, v_fee_gt, v_cbnot, su_hold, su_ns} | 0.65867 | 27,360 | folds |
| su_tafter + sh_crkey / v_tswap / q_swap | 0.65687 / 0.65657 / 0.65657 | 27,360 | |
| ca / ca_nfev / su_nfev / su_clk | 0.65788 / 0.65778 / 0.65767 / 0.65758 | 27,376 / 27,384 / 27,368 / 27,376 | |
| cu_iflet2 | 0.65708 | 27,392 | |
| pre_cb_match, pre_cb_not, wl_owner_eqsys, v_zero_ne, v_mayhem_req, v_fee_gt, v_cbnot | 0.65698 | 27,400 | 3,182 (ties) |
| ci_mapamt / w_mapamt / ca_nflet | 0.65698 | 27,400 | 3,184 / 3,196 / 3,222 |
| n_hk_direct, cmp_pool_rev, cmp_fees_rev, c_ce_cr | 0.65668 | 27,400 | 3,182 |
| sh_crkey / v_tswap / q_swap | 0.65518 / 0.65488 / 0.65488 | 27,400 | |
| nf_pre_ev / ev_cb_local / n_mapamt | 0.65628 / 0.65538 / 0.65508 | 27,408 | |
| v_feeiflet / sh_ownfirst / q_arr / v_tcontains / su_new | 0.63082 / 0.63223 / 0.6273 / 0.50699 / 0.47932 | | |

## 7. Main 2e1379d (#3372, 0.65728, M 2,194, 3,192 slots): su_tafter repay with re-read knobs

#3369/#3372 (w14a55, w14a43) landed "re-read" knobs: one field of an `x`-bound AccountInfo literal read through the
account path (`rent_epoch:a.pool_authority.rent_epoch`, `data:a.pump_fees.data.clone()`), +8 B each at ~0 M.
`genes.py` `rr<k><F>` generates all of them (k = literal index in source order: 0 TCF CpiContext pump_amm, 1
coin_creator_vault_ata, 2 vault ATA, 3 TCF program, 4 sharing pool_authority, 5 authority, 6 mint, 7 pump_fees program;
F in KLDORSWE). All 56 applied on top of su_r2 (M 2,198 at 27,368):

| outcome | genes |
| --- | --- |
| folds (byte-identical to su_r2, 27,368) | 0K 0L 0O 1L 2K 3K 3L 3O 4L 4O 5L 5R 5S 5W 5E 6L 6R 6S 6W 6E 7L |
| +8 B | 5D (M 2,194), 7K (2,192) |
| +16 B | 7O (2,193), 7E (2,192), 7R (2,190), 7S/7W (2,188), 3D (2,189) |
| +32 B | 3S (2,190), 3R (2,186) |
| big losses (M 2,037-2,170) | 0D 0R 0S 0W 0E 1K 1D 1O 1R 1S 1W 1E 2L 2R 2S 2W 2E 4K 4D 4S 4W 4E 5K 5O 6K 6D 6O |

Other su variants on 2e1379d (main M 2,194):

| variant | bytes | M | ratio |
| --- | ---: | ---: | ---: |
| su_tafter | 27,360 | 2,198 | 0.65897 |
| su_r2 | 27,368 | 2,198 | 0.65887 |
| su_r2 + x_hr_curve / x_cb_curve (curve re-reads in the tuple block) | 27,368 | 2,198 | folds |
| su_r2 + x_cr_curve | 27,168 | 1,694 | collapse |
| su_r2 + s_amm_present | 27,384 | 2,196 | 0.65808 |
| su_r2 + s_amm_present + nf_pre_ev | 27,392 | 2,195 | 0.65768 |
| ... + wl_writ_eq (+ x_hr_curve / x_cb_curve / pre_cb_match / pre_cb_not) | 27,400 | 2,193 | 0.65698 (3,226 slots) |
| ... + n_mapamt / ev_cb_local / n_cb_fwd / lf_pr_dl | 27,400 / 27,400 / 27,400 / 27,384 | 2,191 / 2,189 / 2,190 / 2,192 | |
| su_r2 + s_amm_present + wl_ts_clockvar | 27,400 | 2,193 | 0.65698 (3,379 slots) |
| su_r2 + rr5D | 27,376 | 2,194 | |

So su_tafter's +4 M survives every landing since d371f97, but every faithful +8 B found costs 1-2 M in its context;
the best full-size composites tie main at M 2,193, one token short.

## 8. Mains 0d945ea (#3378, 0.65758, M 2,195) and fc628cf (#3379, 0.65758 / 3,183 slots)

On 0d945ea, `su_r2 + s_amm_present + rr7O` (sharing pump_fees literal `owner:a.pump_fees.owner`) was **0.65788 at 27,400 B,
M 2,196, 0 losses** (one token above main), but #3379 landed one minute later (w14a64 curve fee if-let + wallet
`is_writable==false` size pair) and on fc628cf the same composite only ties (0.65758, 3,224 slots vs main 3,183).
Every other repay of su_r2 on fc628cf (M 2,199 at 27,368):

| su_r2 + | bytes | M | ratio |
| --- | ---: | ---: | ---: |
| s_amm_present + rr7O (+ pre_cb_match / pre_cb_not / x_hr_curve) | 27,400 | 2,195 | 0.65758 (tie, 3,224 slots) |
| s_amm_present + rr7E / rr5D + nf_pre_ev | 27,400 | 2,194 | 0.65728 |
| s_amm_present + rr7R / rr7S / rr7W | 27,400 | 2,192 / 2,190 / 2,190 | |
| rr7O | 27,384 | 2,194 | 0.65748 |
| rr7O + rr5D / rr7K / rr7E / rr7R | 27,392 / 27,392 / 27,384 / 27,384 | 2,195 / 2,193 / 2,186 / 2,191 | |
| rr5D + rr7E | 27,392 | 2,194 | |
| rr7O + {clockvar, nf_pre_ev+rr5D, cu_unwrapcur+rr5D, nf_pre_ev+cu_unwrapcur, rr3D} | 27,400 | 2,188-2,192 | |
| su_tafter + s_amm_present + rr7O | 27,392 | 2,195 | |

On 0d945ea: su 0.65927 @27,360 (M 2,199), su_r2 0.65917 @27,368, su_r2+amp+nf_pre_ev 0.65798 @27,392 (M 2,196),
+ wl_writ_eq 0.65728, su_r2+amp+clockvar 0.65728, +rr5D 0.65758 (tie), +rr7K 0.65698, su_r2+amp+rr7E 0.65758 (tie),
pre_cb_match / pre_cb_not 0.65758 (3,192 = main's slots), wl_owner_eqsys 0.63182 (no longer a tie), cu_iflet2 0.65738 @27,392.

## 9. Landing candidate on fc628cf: su_r2 + s_amm_present + rr7O with #3379's size pair reverted

M is scored against the original, not against main, so the 0d945ea composite is still one token above fc628cf's main.
On fc628cf, `su_r2 + s_amm_present + rr7O + cu_unwrapcur + wl_writ_not` (the four genes plus undoing #3379's
cu-if-let / is_writable==false pair) measures **0.65788, 3,223 slots, 27,400 B, 1034/1034, 0 losses** (main 0.65758 / 3,183),
unstripped sha c688d0cac740df27, 363-case differential: 0 mismatches. Changes:
- shared non-holder arm `else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}` (w14a38's su_tafter, curve read);
- sweep `let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=amm_present&&token_frozen(..)?;` (w14a38);
- sharing CPI pump_fees literal `owner:a.pump_fees.owner` (re-read, +16 B here);
- curve `creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps)` and wallet `!a.current_creator.is_writable` (pre-#3379 forms).

**Landed as #3361 (land.py merge 304b03a82): 0.65758/3,183 -> 0.65788/3,223, 0 losses, differential 363/0.**

## 10. Main 304b03a (#3361, 0.65788, M 2,196, 3,223 slots), branch -2

| variant | ratio | bytes | slots | M |
| --- | ---: | ---: | ---: | ---: |
| cu_iflet2 (curve fee `if let`) | 0.65828 | 27,392 | | **2,197** (+1 M at -8 B) |
| cu_iflet2 + rr5D | 0.65788 | 27,400 | 3,222 | 2,196 (tie) |
| #3379's pair (cu_iflet2 + wl_writ_eq) | 0.65758 | 27,400 | 3,224 | 2,195 |
| wl_writ_eq | 0.65748 | 27,408 | | 2,195 |
| pre_cb_match, pre_cb_not, x_hr_curve, x_cb_curve | 0.65788 | 27,400 | 3,223 | ties |
| rr7R / rr7E | 0.65698 / 0.65548 | 27,400 | | 2,193 / 2,188 |
| rr7K / rr5D | 0.65658 / 0.65718 | 27,408 | | 2,192 / 2,194 |
| su_to_st (target from st again) + wl_writ_eq / + rr5D | 0.65758 / 0.65728 | 27,400 | 3,220 / 3,213 | |
| amp_inline + {clockvar, rr5D+nf_pre_ev, ev_nf_let+cu_iflet2} | 0.65638-0.65668 | 27,400 | | |

cu_iflet2 + X on 304b03a (44 of 69 built before #3386 landed): best at 27,400 B are **cu_iflet2 + nf_pre_ev** and
cu_iflet2 + rr5D (+ pre_cb_match / pre_cb_not), 0.65788 with **3,222 slots** (main 3,223: a slot-tiebreak win, overtaken by
#3386 before it could land). cu_iflet2 + lf_pr_dl is -32 B at M 2,197 (0.65857 @27,368). rr0K/0L/0O/1L/2K/3K/3L/3O fold.
cu_iflet2 + rr7K 0.65728; + n_mapamt (3 spellings) / ev_cb_local 0.65698; + rr3E/3S/3W +32 B (M 2,192-2,194).

## 11. Main 39eb377 (#3386 w14a66 fee-Some edge, 0.66477, M 2,219, 3,230 slots)

| variant | ratio | bytes | slots | M |
| --- | ---: | ---: | ---: | ---: |
| lf_pr_dl (sharing program clone with Rc locals; undoes the 3 pump_fees re-reads) | 0.66537 | 27,376 | | **2,220** |
| su_to_st (`target=st.creator` in the su arm) | 0.66487 | 27,392 | | 2,219 |
| pre_cb_match, pre_cb_not, x_hr_curve, x_cb_curve | 0.66477 | 27,400 | 3,230 | ties |
| v_hr_ne | 0.66477 | 27,400 | 3,230 | tie, 1 raw loss |
| su_to_st + rr5D | 0.66447 | 27,400 | 3,220 | 2,218 |
| n_hk_direct, c_ce_cr, cmp_pool_rev, cmp_fees_rev | 0.66447 | 27,400 | 3,230 | 2,218 |
| cu_unwrapcur / rr5D / nf_pre_ev | 0.66437 | 27,408 | | 2,218 |
| amp_inline | 0.66437 | 27,384 | | 2,217 |
| su_to_st + wl_writ_eq / wl_writ_eq | 0.66417 @27,400 / 0.66407 @27,408 | | | 2,217 |
| rr7R / rr7K / n_mapamt / ev_cb_local / rr7E | 0.66387 / 0.66377 / 0.66347 / 0.66347 / 0.66237 | | | |
| amp_inline + clockvar / + ev_nf_let + cu_unwrapcur | 0.66327 / 0.66277 | | | |
| wl_owner_eqsys | 0.63871 | 27,400 | 3,185 | |

Zero-size library re-screen on 39eb377 (67 of 70 genes from the stitch10 tie list, `z_*`): 54 tie at 0.66477 / 3,230
slots (byte-identical or same slots), the rest 0.66387-0.66447. lf_pr_dl + su_to_st 0.66517 @27,368. No slot-tiebreak win.

## 12. Main 0d04cf4 (#3393 w14a72, 0.66507, M 2,220, 3,228 slots): final panel

su_to_st and wl_writ_not are -8 B at the same M (0.66517 @27,392). pre_cb_match / pre_cb_not / x_hr_curve tie (3,228).
wl_writ_not + nf_pre_ev / + rr5D 0.66477 (M 2,219); rr7O 0.66427 @27,416; su_to_st + rr5D / nf_pre_ev / cu_unwrapcur
0.66417; cu_unwrapcur / rr5D / nf_pre_ev 0.66407 @27,408; lf_pr_dl now loses (0.66337 @27,392, M 2,214). Lane stopped here
(time box).
